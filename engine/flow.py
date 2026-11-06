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


class Config:
  dt = 0.0


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
    return np.linalg.norm(p.pos) >= self.limit


class MaxDistance(Condition):
  def check(self, p):
    return np.linalg.norm(p.pos) <= self.limit


class MaxDistanceAndBelow(Condition):
  def check(self, p):
    return not (np.linalg.norm(p.pos) > self.limit and p.pos[1] < 0)


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
  """
  def __init__(self, mass=MS, x=0.0, y=0.0, black=True):
    self.mass = mass
    self.pos = np.array([float(x), float(y)])
    self.black = black
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
    #magnitude of flow
    U = 0.0
    for b in self.bodies:
      d = np.linalg.norm(pos - b.pos)
      U = U + 2*b.GM/d   #square of the flow to this body
    U = math.sqrt(U)

    #direction of flow
    g = np.array([0.0, 0.0])
    for b in self.bodies:
      r = pos - b.pos
      d = np.linalg.norm(r)
      g_mag = b.GM/d**2
      if b.black:
        g -= g_mag * r/d   #towards the body
      else:
        g += g_mag * r/d   #away from the body

    gsize = np.linalg.norm(g)
    if gsize == 0:
      self.warn('g=0 at %s, the flow has no direction - using u=0' % pos)
      return np.array([0.0, 0.0])
    return U * g/gsize

  def gravity(self, pos):
    """newtonian acceleration at pos: the sum of each body's pull"""
    g = np.array([0.0, 0.0])
    for b in self.bodies:
      r = pos - b.pos
      d = np.linalg.norm(r)
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
    x = 1 - np.linalg.norm(v)**2
    #using fp numbers it is possible to get a negative number here
    if x < 0:
      v = v / np.linalg.norm(v)
      L = 0
    else:
      L = math.sqrt(1 - np.linalg.norm(v)**2)

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

  def orbitalSim(self, p, config, log):
    """
    run an orbital simulation
    """
    dt = config.dt
    maxn = int((config.durationDays*DAY)/dt)
    self.log = log

    log.print('study type: orbit')   #the viewer splits orbit runs into their orbits
    log.start(maxn, p, self, dt)

    for n in range(maxn):
      oldpos = p.pos.copy()
      self.move(p, dt)
      log.updatePosition(p, dt)
      if oldpos[1] < 0 and p.pos[1] >= 0:
        log.logOrbit()   #orbit completed
    log.finishOrbit()

  def hyperbolicSim(self, p, config, log):
    """
    run a hyperbolic simulation
    """
    dt = config.dt
    self.log = log

    log.print('study type: hyperbolic')
    log.start(config.condition.limit, p, self, dt)

    while config.condition.check(p):
      self.move(p, dt)
      log.updatePosition(p, dt)

    log.finishHyperbolic(p)
    log.print(p.pos)
    log.print(p.v)


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
    p.d += np.linalg.norm(p.v*dt)
    u3 = self.flow(p.pos)

    #the difference changes w (this gives the rotation)
    p.w = self.addSI(p.w, u2 - u3)
    p.u = u3
    p.v = p.w + p.u

    p.t += dt
    s = 1 - (np.linalg.norm(p.w)**2)/C**2
    if s > 0.0:
      p.pt += dt*math.sqrt(s)

  def moveSecondOrder(self, p, dt):
    light = abs(np.linalg.norm(p.w) - C) < 1e-9*C

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
      p.w = p.w*C/np.linalg.norm(p.w)
    p.pos = p.pos + vm*dt
    p.d += np.linalg.norm(vm*dt)
    p.u = self.flow(p.pos)
    p.v = p.w + p.u

    p.t += dt
    s = 1 - (np.linalg.norm(wm)**2)/C**2
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
  if 'SpecialFlowCalculator' in text:
    return 'SpecialFlowCalculator, first order' if 'order 1' in text else 'SpecialFlowCalculator, second order'
  return 'NewtonianCalculator' if 'NewtonianCalculator' in text else None


def makeCalculator(name, bodies):
  """a calculator by CALCULATORS name (or an old name)"""
  key = calculatorName(name)
  if key is None:
    raise ValueError('unknown calculator %r - one of %s' % (name, ', '.join(CALCULATORS)))
  cls, kwargs = CALCULATORS[key]
  return cls(bodies, **kwargs)
