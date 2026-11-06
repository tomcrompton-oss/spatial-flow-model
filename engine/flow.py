"""
the flow model: bodies, a particle, and the calculators that move it

  Calculator              the flow of space u and newtonian gravity g round the bodies, relativistic velocity
                          addition, and the orbital / hyperbolic sim loops; moves nothing itself
  NewtonianCalculator     plain newtonian gravity
  SpecialFlowCalculator   the flow model: the particle moves at v = w + u, where w is its velocity relative to the
                          flowing space; order=1 is the original step (NewSpecialFlowCalculator), order=2 the
                          second-order step (SecondOrderSpecialFlowCalculator), the default

the calculators that were in flow2.py and are no longer used are in legacy/legacy_calculators.py
"""
import math
import time
import numpy as np
from engine.constants import *
from engine.vectors import length


class Config:
  """
  a sim's steps: a fixed dt, or (stepFraction set) adaptive steps - each moves at most stepFraction of the distance
  to the nearest body (see Calculator.stepSize), and none is longer than dt
  """
  dt = 0.0
  stepFraction = None


class Condition:
  """a sim's end: check(p) is True while the sim should carry on"""
  def __init__(self, limit):
    self.limit = limit


class Duration(Condition):
  def check(self, p):
    return p.t <= self.limit


class ProperDuration(Condition):
  def check(self, p):
    return p.pt <= self.limit


class MinDistance(Condition):
  def check(self, p):
    return length(p.pos) >= self.limit


class MaxDistance(Condition):
  def check(self, p):
    return length(p.pos) <= self.limit


class MaxDistanceAndBelow(Condition):
  def check(self, p):
    return not (length(p.pos) > self.limit and p.pos[1] < 0)


class Particle:
  def __init__(self):
    self.pos = np.array([0.0, 0.0])
    self.v = np.array([0.0, 0.0])
    self.u = np.array([0.0, 0.0])   #velocity of local space
    self.w = np.array([0.0, 0.0])   #local velocity relative to space
    self.pt = 0.0   #proper time
    self.t = 0.0    #coord time
    self.d = 0.0    #distance travelled


class Body:
  """
  a mass that space flows into (black) or out of (white)
  Args:
    mass (float): mass in kg
    x, y (float): position in m
    black (bool): True - space flows in, False - space flows out (white)
    spin (float): a/M for a rotating hole (KerrFlowCalculator only), -1 to 1, positive anticlockwise
  """
  def __init__(self, mass=MS, x=0.0, y=0.0, black=True, spin=0.0):
    self.mass = mass
    self.pos = np.array([float(x), float(y)])
    self.black = black
    self.spin = spin   #a/M, -1 to 1, positive anticlockwise: used by engine/kerr.py's KerrFlowCalculator
    self.GM = G*mass

  @property
  def x(self):
    return self.pos[0]

  @property
  def y(self):
    return self.pos[1]


class Calculator:
  runspeed = 30000   #rough steps per second, for the log's estimate of how long a run takes

  def __init__(self, bodies=None):
    """
    Args:
      bodies (list of Body): the masses; default one black solar mass at (0,0)
    """
    if bodies is None:
      bodies = [Body()]
    elif isinstance(bodies, Body):
      bodies = [bodies]
    elif not isinstance(bodies, (list, tuple)):
      raise TypeError('pass a list of Body objects, e.g. [Body(m)], not ' + repr(bodies))
    self.bodies = list(bodies)
    self.GM = G*sum(b.mass for b in self.bodies) #total, used by the log
    self.log = None #set by the sims so warnings go to the log

  def warn(self, message):
    if self.log is not None:
      self.log.print('WARNING:', message)
    else:
      print('WARNING:', message)

  def flow(self, pos):
    """
    velocity of space (u) at pos
      magnitude: square root of the sum of the squares of the flow to each body, sqrt(2GM/d)
      direction: towards black bodies and away from white ones, weighted by each body's GM/d^2
    """
    U2 = 0.0                    #the square of the flow's magnitude
    g = np.array([0.0, 0.0])    #its direction
    for b in self.bodies:
      r = pos - b.pos
      d = length(r)
      U2 += 2*b.GM/d            #the square of the flow to this body
      pull = b.GM/d**2 * r/d
      if b.black:
        g -= pull               #towards the body
      else:
        g += pull               #away from the body

    gsize = length(g)
    if gsize == 0:
      self.warn('g=0 at %s, the flow has no direction - using u=0' % pos)
      return np.array([0.0, 0.0])
    return math.sqrt(U2) * g/gsize

  def gravity(self, pos):
    """newtonian acceleration at pos: the sum of each body's pull"""
    g = np.array([0.0, 0.0])
    for b in self.bodies:
      r = pos - b.pos
      d = length(r)
      g = g + -(b.GM/d**2) * (r/d)
    return g

  def add(self, u, v):
    """
    relativistic addition of two velocities
    Args:
      u (float): the first velocity as a fraction of c
      v (float): the second velocity as a fraction of c
    Returns:
      w (float): the sum of the two velocities as a fraction of c
    """
    if np.dot(v, v) == 0:
      return u.copy()

    upar = v * np.dot(u, v) / np.dot(v, v)
    uper = u - upar

    wpar = (upar + v) / (1 + np.dot(v, upar))
    x = 1 - np.dot(v, v)
    #using fp numbers it is possible to get a negative number here
    if x < 0:
      v = v / length(v)
      L = 0
    else:
      L = math.sqrt(x)

    wper = (L * uper) / (1 + np.dot(v, upar))
    return wpar + wper

  def addSI(self, u, v):
    """
    relativistic addition of two velocities
    Args:
      u (float): the first velocity in m/s
      v (float): the second velocity in m/s
    Returns:
      w (float): the sum of the two velocities in m/s
    """
    return self.add(u/C, v/C)*C

  def move(self, p, dt):
    raise NotImplementedError('Calculator only gives the flow and gravity; use a calculator that moves particles')

  def nearest(self, pos):
    """the distance from pos to the nearest body"""
    return min(length(pos - b.pos) for b in self.bodies)

  def stepSize(self, p, fraction, dtMax=None):
    """
    an adaptive step: long enough to move fraction of the distance to the nearest body, at the fastest of the
    particle's speed v, the flow u and its speed relative to the flow w (a step looks at the flow that far away), and
    no longer than dtMax. close in, and moving fast, the steps are short; far out and slow, they are long - so the
    error in each step is about the same everywhere
    """
    speed = max(length(p.v), length(p.u), length(p.w))
    dt = fraction*self.nearest(p.pos)/speed if speed > 0 else float('inf')
    return min(dt, dtMax) if dtMax else dt

  def steps(self, p, config, duration=None):
    """
    the length of each step in turn: config.dt every time, or adaptive steps if config.stepFraction is set (dt is
    then the longest step); with a duration, the steps stop when it is reached
    """
    if config.stepFraction is None:
      if duration is None:
        while True:
          yield config.dt
      for n in range(int(duration/config.dt)):
        yield config.dt
      return
    t = 0.0
    while duration is None or t < duration:
      dt = self.stepSize(p, config.stepFraction, config.dt or None)
      if duration is not None:
        dt = min(dt, duration - t)
      t += dt
      yield dt

  def run(self, p, config, log, ends, progress=None):
    """
    run p until the first of ends - [('time', s)], [('orbits', 20), ('min', rs)] ... (see engine/run.py) - with the
    steps config sets (fixed dt or adaptive), logging it as it goes; orbits are counted and logged whenever they
    happen. returns why it stopped and the number of steps
    """
    from engine.run import simulate
    return simulate(self, p, config, log, ends, progress)

  def orbitalSim(self, p, config, log):
    """a run for config.durationDays (as the orbit studies have always run)"""
    return self.run(p, config, log, [('time', config.durationDays*DAY)])

  def hyperbolicSim(self, p, config, log):
    """a run until config.condition stops it (as the descent and light studies have always run)"""
    return self.run(p, config, log, [('condition', config.condition)])


class NewtonianCalculator(Calculator):
  runspeed = 200000

  def move(self, p, dt):
    g = self.gravity(p.pos)
    p.v = p.v + g*dt
    p.pos = p.pos + p.v*dt
    p.pt += dt
    p.t += dt


class SpecialFlowCalculator(Calculator):
  """
  the flow model: space flows at u (towards black bodies, away from white ones) and the particle moves at
  v = w + u, where w is its velocity relative to the space it is in. as it moves, w changes by the difference
  between the flow where space goes and the flow where the particle goes, added relativistically (addSI):
    dx/dt = w + u(x),   dw/dt = -(w . grad) u(x)
  and proper time runs at sqrt(1 - w^2/c^2)

  order=1: each step takes everything from the start of the step (NewSpecialFlowCalculator) - an error of order dt
           over a run, which shows as orbits drifting outward (about 27,000 km an orbit for Mercury at 1/10 scale,
           dt = 10 s)
  order=2: each step goes half way the first-order way, then takes the whole step at the middle's rates
           (SecondOrderSpecialFlowCalculator) - an error of order dt^2, for 5 flow evaluations a step to 2;
           light (|w| = c) is kept at exactly c. see studies/compare_second_order.py
  """

  def __init__(self, bodies=None, order=2):
    super().__init__(bodies)
    if order not in (1, 2):
      raise ValueError('order is 1 or 2, not %r' % order)
    self.order = order
    self.runspeed = 60000 if order == 1 else 25000

  def __repr__(self):
    return '<flow.SpecialFlowCalculator object, order %d>' % self.order

  def initPV(self, p, v):
    """start moving at v"""
    p.v = v
    p.u = self.flow(p.pos)
    p.w = p.v - p.u

  def initPW(self, p, w):
    """start moving at w relative to the local space"""
    p.w = w
    p.u = self.flow(p.pos)
    p.v = p.w + p.u

  def initPFreefall(self, p):
    """moving with the flow (v = u, w = 0): a fall from rest at infinity, for a black body"""
    p.u = self.flow(p.pos)
    p.v = p.u
    p.w = np.array([0.0, 0.0])

  def initPAgainstFlow(self, p):
    """
    thrown against the flow at twice its speed (v = -2u, w = v - u = -3u), as astroDescend falls into a white body
    (NewSpecialWhiteFlowCalculator's initPFreefall)
    """
    p.u = self.flow(p.pos)
    p.v = -2*p.u
    p.w = p.v - p.u

  def move(self, p, dt):
    if self.order == 1:
      self.moveFirstOrder(p, dt)
    else:
      self.moveSecondOrder(p, dt)

  def moveFirstOrder(self, p, dt):
    #the flow where space moves to, and where the particle moves to
    u2 = self.flow(p.pos + p.u*dt)
    p.pos = p.pos + p.v*dt
    p.d += length(p.v*dt)
    u3 = self.flow(p.pos)

    #the difference changes w (this gives the rotation)
    p.w = self.addSI(p.w, u2 - u3)
    p.u = u3
    p.v = p.w + p.u

    p.t += dt
    s = 1 - (length(p.w)**2)/C**2
    if s > 0.0:
      p.pt += dt*math.sqrt(s)

  def moveSecondOrder(self, p, dt):
    light = abs(length(p.w) - C) < 1e-9*C

    #half a step the first-order way, to the middle of the step
    xm = p.pos + p.v*dt/2
    um = self.flow(xm)
    wm = self.addSI(p.w, self.flow(p.pos + p.u*dt/2) - um)
    vm = wm + um

    #the whole step from the start, at the middle's rates: the flow difference across the middle point (a centred
    #difference), its relativistic change worked out at the middle w
    dw = self.flow(xm - wm*dt/2) - self.flow(xm + wm*dt/2)
    p.w = p.w + (self.addSI(wm, dw) - wm)
    if light:
      p.w = p.w*C/length(p.w)
    p.pos = p.pos + vm*dt
    p.d += length(vm*dt)
    p.u = self.flow(p.pos)
    p.v = p.w + p.u

    p.t += dt
    s = 1 - (length(wm)**2)/C**2
    if s > 0.0:
      p.pt += dt*math.sqrt(s)


#calculators by name, for studies/run_study.py and the viewer's Sim tab: name -> (class, keyword arguments)
CALCULATORS = {
  'SpecialFlowCalculator, second order': (SpecialFlowCalculator, {'order': 2}),
  'SpecialFlowCalculator, first order': (SpecialFlowCalculator, {'order': 1}),
  'NewtonianCalculator': (NewtonianCalculator, {}),
}
#names used before flow2.py became flow.py, in older logs and sim configs
OLD_NAMES = {
  'NewSpecialFlowCalculator': 'SpecialFlowCalculator, first order',
  'NewSpecialWhiteFlowCalculator': 'SpecialFlowCalculator, first order',
  'SecondOrderSpecialFlowCalculator': 'SpecialFlowCalculator, second order',
}


def calculatorName(text):
  """the CALCULATORS name for a name or a log's 'calc:' text, old or new; None if it isn't one of them"""
  for name in CALCULATORS:
    if name == text:
      return name
  for old, name in OLD_NAMES.items():
    if old in text:
      return name
  for kind in ('KerrFlowCalculator', 'SpecialFlowCalculator'):
    if kind in text:
      return kind + (', first order' if 'order 1' in text else ', second order')
  return 'NewtonianCalculator' if 'NewtonianCalculator' in text else None


def makeCalculator(name, bodies):
  """a calculator by CALCULATORS name (or an old name)"""
  key = calculatorName(name)
  if key is None:
    raise ValueError('unknown calculator %r - one of %s' % (name, ', '.join(CALCULATORS)))
  cls, kwargs = CALCULATORS[key]
  return cls(bodies, **kwargs)


#the rotating hole's calculator, in its own module (engine/kerr.py) - added here so it can be made by name
from engine.kerr import KerrFlowCalculator
CALCULATORS['KerrFlowCalculator, second order'] = (KerrFlowCalculator, {'order': 2})
CALCULATORS['KerrFlowCalculator, first order'] = (KerrFlowCalculator, {'order': 1})
