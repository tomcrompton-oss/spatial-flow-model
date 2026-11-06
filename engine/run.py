"""
running a sim: one loop for every kind of run. it stops at the first of its end conditions, and counts orbits as
they happen, so the same run can be an orbit, a flyby or a fall - the log records whatever happened

end conditions, as (kind, value):
  ('time', s)              elapsed (coordinate) time
  ('properTime', s)        the particle's proper time
  ('min', m)               closer than m to any body
  ('max', m)               farther than m from every body
  ('orbits', n)            n whole orbits (after the first part orbit, see OrbitCounter)
  ('condition', c)         an older flow.Condition: the run goes on while c.check(p) is True
"""
import math
import numpy as np
from engine.vectors import length

KINDS = ('time', 'properTime', 'min', 'max', 'orbits', 'condition')


class OrbitCounter:
  """
  counts orbits by the angle turned round the bodies' centre of mass, in the direction the particle starts going
  round. the first orbit ends after three quarters of a turn - a quarter turn short of the start, so the orbits'
  boundaries fall between the start and the far side, not on an apsis for an orbit started at one - and each one
  after that a whole turn later. for a single body at the origin, started on the +y axis, the boundaries are where
  the particle crosses the -x axis, as Calculator.orbitalSim used to count orbits (crossing y = 0 upwards)
  """
  FIRST = 1.5*math.pi   #turned at the end of the first orbit

  def __init__(self, calc, p):
    masses = sum(b.mass for b in calc.bodies)
    self.centre = sum(b.mass*b.pos for b in calc.bodies)/masses
    r = p.pos - self.centre
    sense = r[0]*p.v[1] - r[1]*p.v[0]   #anticlockwise if positive
    self.sense = 1.0 if sense >= 0 else -1.0
    self.angle = math.atan2(r[1], r[0])
    self.turned = 0.0   #in the starting direction
    self.orbits = 0     #boundaries passed (the first is the end of the part orbit)

  def step(self, pos):
    """after each step: True if an orbit has just ended"""
    r = pos - self.centre
    angle = math.atan2(r[1], r[0])
    change = (angle - self.angle + math.pi) % (2*math.pi) - math.pi   #the smallest turn between the two
    self.angle = angle
    self.turned += self.sense*change
    if self.turned >= self.FIRST + 2*math.pi*self.orbits:
      self.orbits += 1
      return True
    return False

  def turnsTo(self, n):
    """the angle turned at the end of n whole orbits"""
    return self.FIRST + 2*math.pi*n


class Ending:
  """a run's end conditions: whether one is reached, which, and roughly how far through the run is"""

  def __init__(self, ends, calc, p, counter):
    self.ends = [(kind, value) for kind, value in ends]
    for kind, _ in self.ends:
      if kind not in KINDS:
        raise ValueError('unknown end condition %r - one of %s' % (kind, ', '.join(KINDS)))
    if not self.ends:
      raise ValueError('a run needs an end condition')
    self.calc, self.counter = calc, counter
    self.d0 = calc.nearest(p.pos)

  def timeLimit(self):
    """the elapsed time the run stops at, if that is one of its ends (the steps then stop exactly there)"""
    times = [value for kind, value in self.ends if kind == 'time']
    return min(times) if times else None

  def before(self, p):
    """before a step: a reason to stop now (the older conditions are checked before each step)"""
    for kind, value in self.ends:
      if kind == 'condition' and not value.check(p):
        return 'the condition was met'
    return None

  def after(self, t, p):
    """after a step: a reason to stop, or None"""
    if not np.all(np.isfinite(p.pos)):
      return 'position is not finite'
    for kind, value in self.ends:
      if kind == 'time' and t >= value*(1 - 1e-12):
        return 'elapsed time reached'
      if kind == 'properTime' and p.pt >= value:
        return 'proper time reached'
      if kind == 'min' and self.calc.nearest(p.pos) < value:
        return 'reached %g m from a body' % value
      if kind == 'max' and self.calc.nearest(p.pos) > value:
        return '%g m from every body' % value
      if kind == 'orbits' and self.counter.orbits >= value + 1:   #+1 for the part orbit at the start
        return '%d orbits' % value
    return None

  def progress(self, t, p):
    """roughly how far through the run is, 0 to 1: the furthest on of its end conditions"""
    fractions = []
    for kind, value in self.ends:
      if kind == 'time':
        fractions.append(t/value)
      elif kind == 'properTime':
        fractions.append(p.pt/value)
      elif kind == 'orbits':
        fractions.append(self.counter.turned/self.counter.turnsTo(value))
      elif kind in ('min', 'max'):
        d = self.calc.nearest(p.pos)
        if value != self.d0:
          fractions.append((self.d0 - d)/(self.d0 - value) if kind == 'min' else (d - self.d0)/(value - self.d0))
    return min(max(fractions + [0.0]), 0.999)


def simulate(calc, p, config, log, ends, progress=None):
  """
  run p with calc from now until the first of ends (see the module notes): steps as config says (fixed dt, or
  adaptive with config.stepFraction), a csv row at the start, every log.freq seconds and at the end, a log line for
  each orbit, and the log's summary at the end. progress(ending, t, p) is called after each step, if given (it can
  ask ending.progress(t, p) how far on the run is, when it wants to).
  returns why it stopped and the number of steps
  """
  calc.log = log
  counter = OrbitCounter(calc, p)
  ending = Ending(ends, calc, p, counter)
  duration = ending.timeLimit()
  fixed = config.stepFraction is None
  log.start(int(duration/config.dt) if fixed and duration else 0, p, calc, config)
  if log.csvFile:
    log.writeRow(p)   #the start
  t, n, reason, wrote = 0.0, 0, None, True
  for dt in calc.steps(p, config, duration):
    reason = ending.before(p)
    if reason:
      break
    calc.move(p, dt)
    t += dt
    n += 1
    wrote = log.updatePosition(p, dt)
    if counter.step(p.pos):
      log.logOrbit()
    reason = ending.after(t, p)
    if progress:
      progress(ending, t, p)
    if reason:
      break
  else:
    reason = reason or 'elapsed time reached'
  if log.csvFile and not wrote:
    log.writeRow(p)   #the end, unless the last step wrote it
  log.print()
  log.print('stopped:', reason, 'after', n, 'steps')
  log.finish(p)
  return reason, n
