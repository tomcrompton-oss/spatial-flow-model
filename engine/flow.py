"""
the flow model: bodies, a particle, and the calculators that move it

  Calculator              the flow of space u and newtonian gravity g round the bodies, relativistic velocity
                          addition, and the orbital / hyperbolic sim loops; moves nothing itself
  NewtonianCalculator     plain newtonian gravity
  SpecialFlowCalculator   the flow model: the particle moves at v = w + u, where w is its velocity relative to the
                          flowing space; order=1 is the original step (NewSpecialFlowCalculator), order=2 the
                          second-order step (SecondOrderSpecialFlowCalculator), the default

the flow's direction is Calculator.direction (see flowDirection): with more than one body it is by default the
eikonal flow, which has no curl, so space moving with it falls at exactly g - for two bodies worked out exactly
(engine/two_centre.py), for more from tables of its paths (engine/eikonal.py)

a gravitational wave (engine/waves.py, Calculator.wave) adds its own flow, which changes with time: flow takes the
time, and the steps pass it (the flow is otherwise steady)

the calculators that were in flow2.py and are no longer used are in legacy/legacy_calculators.py
"""
import math
import time
import numpy as np
from engine.constants import *
from engine.vectors import length


EIKONAL = ('eikonal', 'eikonal-exact')   #the directions with no curl: the ray tables, and the exact two-body solution
RAY_TABLES = {}   #the ray tables built so far (engine/eikonal.py), by bodies: they never change once built


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

  def __init__(self, bodies=None, direction=None, wave=None):
    """
    Args:
      bodies (list of Body): the masses; default one black solar mass at (0,0); [] for none (a wave alone)
      direction: which way the flow points (its magnitude is always the same) - see flowDirection; 'eikonal-exact'
                 only for two bodies. by default 'eikonal-exact' for two bodies, 'eikonal' for more, and along g
                 (straight in or out) for one; 'g' sets along g for any number
      wave: a gravitational wave whose flow is added (engine/waves.py PlaneWave), or None
    """
    if bodies is None:
      bodies = [Body()]
    elif isinstance(bodies, Body):
      bodies = [bodies]
    elif not isinstance(bodies, (list, tuple)):
      raise TypeError('pass a list of Body objects, e.g. [Body(m)], not ' + repr(bodies))
    self.bodies = list(bodies)
    self.GM = G*sum(b.mass for b in self.bodies) #total, used by the log
    if direction == 'eikonal-exact' and len(self.bodies) != 2:
      raise ValueError("the 'eikonal-exact' flow is for two bodies (%d given): use 'eikonal' (the ray tables)"
                       % len(self.bodies))
    if direction is None and len(self.bodies) > 1:
      direction = 'eikonal-exact' if len(self.bodies) == 2 else 'eikonal'
    self.direction = direction   #None (one body): along g (see flowDirection); can be set at any time
    self.rays = None             #the zero-energy paths for the eikonal directions (engine/eikonal.py or
                                 #engine/two_centre.py), made when needed
    self.wave = wave             #a gravitational wave adding its flow (engine/waves.py), or None
    self.log = None #set by the sims so warnings go to the log

  def warn(self, message):
    if self.log is not None:
      self.log.print('WARNING:', message)
    else:
      print('WARNING:', message)

  def flow(self, pos, region=None, t=0.0):
    """
    velocity of space (u) at pos, at time t (which only a gravitational wave's flow depends on)
      magnitude: square root of the sum of the squares of the flow to each body, sqrt(2GM/d)
      direction: set by self.direction (see flowDirection) - by default, for more than one body, down the eikonal
                 flow's zero-energy paths; along g (towards black bodies and away from white ones, weighted by each
                 body's GM/d^2) when it is None or 'g'
    region: for a direction with a seam ('eikonal', 'eikonal-exact'), the side of it to take the flow from (see region)
    plus self.wave's flow, if there is one
    """
    if self.wave is not None:
      wave = self.wave.flow(pos, t)
      if not self.bodies:
        return wave
      return self.bodiesFlow(pos, region) + wave
    return self.bodiesFlow(pos, region)

  def bodiesFlow(self, pos, region=None):
    """the bodies' flow at pos (see flow)"""
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
    if self.direction is not None:
      g = self.flowDirection(pos, region)

    gsize = length(g)
    if gsize == 0:
      self.warn('g=0 at %s, the flow has no direction - using u=0' % pos)
      return np.array([0.0, 0.0])
    return math.sqrt(U2) * g/gsize

  def flowDirection(self, pos, region=None):
    """
    which way the flow points at pos (any length; flow scales it to the flow's magnitude), by self.direction:
      None or 'g'  along g - towards black bodies and away from white ones, weighted by GM/d^2 (the default for one
                   body, where it is straight in or out)
      'nearest'    towards the nearest body (away from it if it is white)
      'centre'     towards the bodies' centre of mass
      'eikonal'    down the zero-energy newtonian path from the nearest body through pos (engine/eikonal.py): no
                   curl, so space moving with the flow falls at exactly g; a seam where the bodies' regions meet.
                   region picks the side of the seam (None: the side pos is on); along g past the table. the
                   default for three or more bodies
      'eikonal-exact'  the same flow for exactly two bodies, worked out exactly rather than from tables
                   (engine/two_centre.py: the zero-energy paths separate in elliptic coordinates); everywhere. the
                   default for two bodies
      (x, y)       that way everywhere
      a function   of pos, returning the direction there
    """
    direction = self.direction
    if direction in EIKONAL:
      found = self.rayField().direction(pos, region)
      if found is not None:
        return found
    if direction is None or direction == 'g' or direction in EIKONAL:
      g = np.array([0.0, 0.0])
      for b in self.bodies:
        r = pos - b.pos
        d = length(r)
        g = g + (-1 if b.black else 1)*(b.GM/d**2)*(r/d)
      return g
    if direction == 'nearest':
      b = min(self.bodies, key=lambda b: length(pos - b.pos))
      return (b.pos - pos) if b.black else (pos - b.pos)
    if direction == 'centre':
      centre = sum(b.mass*b.pos for b in self.bodies)/sum(b.mass for b in self.bodies)
      return centre - pos
    if callable(direction):
      return np.asarray(direction(pos), dtype=float)
    return np.asarray(direction, dtype=float)

  def rayField(self):
    """
    the zero-energy paths out of each body: for direction 'eikonal' the tables (engine/eikonal.py), built the first
    time for these bodies (a few seconds) and shared by every calculator with them; for 'eikonal-exact' the exact
    two-body solution (engine/two_centre.py)
    """
    key = [(b.mass, b.x, b.y, b.black) for b in self.bodies] + [self.direction]
    if self.rays is None or self.rays[0] != key:
      if self.direction == 'eikonal-exact':
        from engine.two_centre import TwoCentreField
        self.rays = (key, TwoCentreField(self.bodies))
      else:
        tables = RAY_TABLES.get(str(key))
        if tables is None:
          from engine.eikonal import RayField
          tables = RAY_TABLES[str(key)] = RayField(self.bodies)
        self.rays = (key, tables)
    return self.rays[1]

  def region(self, pos):
    """which side of the flow's seam pos is on (the nearest body's index), or None if the flow has no seam"""
    if self.direction not in EIKONAL:
      return None
    return self.rayField().region(pos)

  def crossSeam(self, p, before):   #(p.t is the step's end)
    """
    after a step that started in region before: if the particle has crossed the seam, w takes the jump in the flow
    there, added relativistically (as each step adds the flow's change) - u old side - u new side - so the jump does
    not kick it: v is kept to first order in u/c, and light stays at |w| = c
    """
    after = self.region(p.pos)
    if after == before:
      return
    u = self.flow(p.pos, after, p.t)
    p.w = self.addSI(p.w, p.u - u)
    p.u = u
    p.v = p.w + p.u

  def describeDirection(self):
    """the flow's direction in words, for logs"""
    d = self.direction
    if d is None or d == 'g':
      return 'along g'
    if d == 'eikonal':
      return 'down zero-energy paths from the nearest body (no curl; seam where the regions meet)'
    if d == 'eikonal-exact':
      return ('down zero-energy paths from the nearest body (no curl; seam where the regions meet), exact two-body'
              ' solution in elliptic coordinates')
    if d in ('nearest', 'centre'):
      return {'nearest': 'towards the nearest body', 'centre': 'towards the centre of mass'}[d]
    if callable(d):
      return getattr(d, '__name__', 'a function of position')
    return 'fixed, along (%g, %g)' % tuple(d)

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
    """the distance from pos to the nearest body (infinite with none)"""
    return min((length(pos - b.pos) for b in self.bodies), default=float('inf'))

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

  def __init__(self, bodies=None, order=2, direction=None, wave=None):
    super().__init__(bodies, direction, wave)
    if order not in (1, 2):
      raise ValueError('order is 1 or 2, not %r' % order)
    self.order = order
    self.runspeed = 60000 if order == 1 else 25000

  def __repr__(self):
    return '<flow.SpecialFlowCalculator object, order %d>' % self.order

  def initPV(self, p, v):
    """start moving at v"""
    p.v = v
    p.u = self.flow(p.pos, None, p.t)
    p.w = p.v - p.u

  def initPW(self, p, w):
    """start moving at w relative to the local space"""
    p.w = w
    p.u = self.flow(p.pos, None, p.t)
    p.v = p.w + p.u

  def initPFreefall(self, p):
    """moving with the flow (v = u, w = 0): a fall from rest at infinity, for a black body"""
    p.u = self.flow(p.pos, None, p.t)
    p.v = p.u
    p.w = np.array([0.0, 0.0])

  def initPAgainstFlow(self, p):
    """
    thrown against the flow at twice its speed (v = -2u, w = v - u = -3u), as astroDescend falls into a white body
    (NewSpecialWhiteFlowCalculator's initPFreefall)
    """
    p.u = self.flow(p.pos, None, p.t)
    p.v = -2*p.u
    p.w = p.v - p.u

  def move(self, p, dt):
    if self.order == 1:
      self.moveFirstOrder(p, dt)
    else:
      self.moveSecondOrder(p, dt)

  def moveFirstOrder(self, p, dt):
    #the flow where space moves to, and where the particle moves to - from the side of any seam the step starts on,
    #both at the step's end (the difference is the flow's change across space; its change in time comes in with u3)
    side = self.region(p.pos)
    end = p.t + dt
    u2 = self.flow(p.pos + p.u*dt, side, end)
    p.pos = p.pos + p.v*dt
    p.d += length(p.v*dt)
    u3 = self.flow(p.pos, side, end)

    #the difference changes w (this gives the rotation)
    p.w = self.addSI(p.w, u2 - u3)
    p.u = u3
    p.v = p.w + p.u
    p.t = end
    self.crossSeam(p, side)

    s = 1 - (length(p.w)**2)/C**2
    if s > 0.0:
      p.pt += dt*math.sqrt(s)

  def moveSecondOrder(self, p, dt):
    light = abs(length(p.w) - C) < 1e-9*C

    #half a step the first-order way, to the middle of the step - all from the side of any seam the step starts on
    side = self.region(p.pos)
    middle, end = p.t + dt/2, p.t + dt
    xm = p.pos + p.v*dt/2
    um = self.flow(xm, side, middle)
    wm = self.addSI(p.w, self.flow(p.pos + p.u*dt/2, side, middle) - um)
    vm = wm + um

    #the whole step from the start, at the middle's rates: the flow difference across the middle point (a centred
    #difference, at the middle's time), its relativistic change worked out at the middle w
    dw = self.flow(xm - wm*dt/2, side, middle) - self.flow(xm + wm*dt/2, side, middle)
    p.w = p.w + (self.addSI(wm, dw) - wm)
    if light:
      p.w = p.w*C/length(p.w)
    p.pos = p.pos + vm*dt
    p.d += length(vm*dt)
    p.u = self.flow(p.pos, side, end)
    p.v = p.w + p.u
    p.t = end
    self.crossSeam(p, side)

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
