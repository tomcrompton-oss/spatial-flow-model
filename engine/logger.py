"""
logging a run: Log writes the .log text and the .csv of positions; OrbitStats keeps the orbit statistics
(closest and farthest points, each orbit's period, apsides and precession) that Log reports at the end

files go in logs/<folder>/<study name>_<datetime>.log / .csv: a folder per kind of study, the study name up to its
first '_' (lightPastSun_20pct -> lightPastSun/, sim_closeOrbits -> sim/); tests/ write theirs to tests/logs/ instead
"""
import math
import os
import csv
import time
from datetime import datetime
import numpy as np
from engine.constants import *
from engine.vectors import length
from engine.exact import grPrecessionExact, kerrPrecessionExact

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   #the project folder
LOG_DIR = os.path.join(ROOT, 'logs')                #study logs
TEST_LOG_DIR = os.path.join(ROOT, 'tests', 'logs')   #regression test logs, kept apart from the studies'


def studyFolder(studyName):
  """the folder a study's logs go in: its name up to the first '_'"""
  return studyName.split('_')[0] or studyName


class OrbitStats:
  """
  the closest and farthest points (from the bodies' centre of mass) since the last orbit ended, the closest over the
  whole run, and a record of each orbit; an orbit ends when engine/run.py's OrbitCounter says so
  """

  def __init__(self, gm=G*MS):
    self.GM = gm     #for the predicted period and precession; Log.start / logBodies set it from the calculator
    self.centre = np.array([0.0, 0.0])   #the bodies' centre of mass, which distances are from (logBodies sets it)
    self.closest, self.closestPos = float('inf'), None
    self.spin = 0.0     #a rotating hole's a/M (logBodies sets it): its orbits compare with exact Kerr
    self.sense = None   #+1 going round anticlockwise, -1 clockwise (from the first step)
    #every periapsis and apoapsis as it happens - a turning point in the distance - as (distance, angle); unlike
    #each orbit's closest and farthest points these stay right when the apsides move fast round the orbit
    self.periapsides, self.apoapsides, self.recent = [], [], []
    self.orbit = 0   #orbits ended so far (the first is a warmup part orbit)
    self.period = 0.0
    self.resetExtremes()
    self.max, self.min = 1.0, 1000*AU   #as before the first orbit: the start counts as the first farthest point
    self.periods, self.periapsis, self.apoapsis, self.semiMajorAxis, self.eccentricity = [], [], [], [], []
    self.periapsisAngle, self.periapsisPrecession, self.apoapsisAngle, self.apoapsisPrecession = [], [], [], []
    #worked out by summary()
    self.calcPeriod = self.calcPeriapsis = self.calcApoapsis = self.calcSMA = self.calcEccentricity = 0.0
    self.predictedPeriod = self.predictedPrecession = 0.0
    self.calcPPrecession = self.calcAPrecession = 0.0

  def resetExtremes(self):
    self.max, self.maxpos = 0.0, np.array([0.0, 0.0])
    self.min, self.minpos = 10000*AU, np.array([0.0, 0.0])

  def track(self, p, dt):
    """after each step: the time into this orbit and the extremes of the distance"""
    self.period += dt
    rel = p.pos - self.centre
    if self.sense is None:
      self.sense = 1.0 if rel[0]*p.v[1] - rel[1]*p.v[0] >= 0 else -1.0
    d = length(rel)
    if d < self.closest:
      self.closest, self.closestPos = d, p.pos.copy()
    if d > self.max:
      self.max, self.maxpos = d, p.pos.copy()
    if d < self.min:
      self.min, self.minpos = d, p.pos.copy()
    self.recent = (self.recent + [(d, rel)])[-3:]
    if len(self.recent) == 3:
      (d0, _), (d1, r1), (d2, _) = self.recent
      if d1 < d0 and d1 <= d2:
        self.periapsides.append((d1, math.atan2(r1[1], r1[0])))
      elif d1 > d0 and d1 >= d2:
        self.apoapsides.append((d1, math.atan2(r1[1], r1[0])))
    return d

  def endOrbit(self):
    """record the orbit just ended; returns the angles of its periapsis and apoapsis"""
    self.orbit += 1
    sma = (self.min + self.max)/2
    e = 1 - 2/(self.max/self.min + 1)
    #the apsides' angles round the centre, and their changes from the last orbit's: a step of less than half a turn,
    #in the direction the orbit goes, so the precession is positive when the apsides move on the way the orbit goes
    minP, maxP = (math.atan2(*(pos - self.centre)[::-1]) for pos in (self.minpos, self.maxpos))
    turn = lambda new, old: self.sense*((new - old + math.pi) % (2*math.pi) - math.pi)
    self.periods.append(self.period)
    self.periapsis.append(self.min)
    self.apoapsis.append(self.max)
    self.semiMajorAxis.append(sma)
    self.eccentricity.append(e)
    self.periapsisAngle.append(minP)
    if len(self.periapsisAngle) > 1:
      self.periapsisPrecession.append(turn(self.periapsisAngle[-1], self.periapsisAngle[-2]))
    self.apoapsisAngle.append(maxP)
    if len(self.apoapsisAngle) > 1:
      self.apoapsisPrecession.append(turn(self.apoapsisAngle[-1], self.apoapsisAngle[-2]))
    self.period = 0
    return minP, maxP

  def summary(self):
    """average the whole orbits (dropping the warmup) and the predictions; False if there are none"""
    if self.orbit < 2:
      return False
    del self.periods[0], self.periapsis[0], self.apoapsis[0], self.eccentricity[0]
    self.orbit -= 1
    n = self.orbit
    self.calcPeriod = sum(self.periods)/n
    self.calcPeriapsis = sum(self.periapsis)/n
    self.calcApoapsis = sum(self.apoapsis)/n
    self.calcSMA = (self.calcPeriapsis + self.calcApoapsis)/2
    self.predictedPeriod = 2*math.pi*math.sqrt(self.calcSMA**3/self.GM)
    self.calcEccentricity = sum(self.eccentricity)/n
    if n > 1:
      self.calcPPrecession = sum(self.periapsisPrecession)/n
      self.calcAPrecession = sum(self.apoapsisPrecession)/n
    if len(self.periapsides) >= 2 and len(self.apoapsides) >= 2:
      #better: from each periapsis and apoapsis as it happened
      turn = lambda new, old: self.sense*((new - old + math.pi) % (2*math.pi) - math.pi)
      mean = lambda xs: sum(xs)/len(xs)
      self.calcPeriapsis = mean([d for d, _ in self.periapsides])
      self.calcApoapsis = mean([d for d, _ in self.apoapsides])
      self.calcSMA = (self.calcPeriapsis + self.calcApoapsis)/2
      self.calcEccentricity = (self.calcApoapsis - self.calcPeriapsis)/(self.calcApoapsis + self.calcPeriapsis)
      self.calcPPrecession = mean([turn(b, a) for (_, a), (_, b) in zip(self.periapsides, self.periapsides[1:])])
      self.calcAPrecession = mean([turn(b, a) for (_, a), (_, b) in zip(self.apoapsides, self.apoapsides[1:])])
    self.predictedPeriod = 2*math.pi*math.sqrt(self.calcSMA**3/self.GM)
    self.predictedPrecession = (24*math.pi**3)*(self.calcSMA**2)/(self.predictedPeriod**2 * C**2 * (1 - self.calcEccentricity**2))
    return True


class Log:
  """
  a run's .log (print) and .csv (updatePosition writes a row every freq seconds, every step if freq is 0);
  the orbit statistics are in self.stats, and read through the log too (log.orbit, log.calcPeriod, log.min ...)
  """

  def __init__(self, studyName='log', writeToFile=False, writeToCsv=False, logDir=None):
    self.studyName = studyName
    self.file = None
    self.csvFile = None
    self.csvWriter = None
    self.t = 0.0          #time since the start of the run
    self.freq = 0         #seconds between csv rows; 0 for every step
    self.nextRow = None   #when the next csv row is due
    self.starttime = time.time()
    self.startpos = None
    self.stats = OrbitStats()
    if logDir is None:
      logDir = os.path.join(LOG_DIR, studyFolder(studyName))
    basename = os.path.join(logDir, studyName + '_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    if writeToFile or writeToCsv:
      os.makedirs(logDir, exist_ok=True)
    if writeToFile:
      self.file = open(basename + '.log', 'w')
    if writeToCsv:
      self.csvFile = open(basename + '.csv', 'w', newline='')
      self.csvWriter = csv.writer(self.csvFile)
      self.csvWriter.writerow(['t', 'pt', 'd', 'pos_x', 'pos_y', 'v_x', 'v_y'])

  def __getattr__(self, name):
    #the orbit statistics, as attributes of the log (only called for names the log itself doesn't have)
    if name != 'stats' and 'stats' in self.__dict__:
      return getattr(self.stats, name)
    raise AttributeError(name)

  def close(self):
    """close the .log and .csv files"""
    for f in (self.file, self.csvFile):
      if f:
        f.close()

  def print(self, *args, **kwargs):
    """print to screen, and to the log file if writing to file"""
    print(*args, **kwargs)
    if self.file:
      print(*args, file=self.file, **kwargs)
      self.file.flush()

  def start(self, maxn, p, calc, config):
    """the start of a sim: its estimated duration (maxn steps; 0 if not known), calculator, steps and bodies"""
    self.starttime = time.time()
    self.startpos = p.pos
    if maxn:
      self.print('Starting estimated duration:', "{:.2f}".format(maxn/calc.runspeed), 'seconds (',
                 "{:.2}".format(maxn/(calc.runspeed*3600)), ') hours')
    self.print('calc: ', calc)
    self.logSteps(config)
    self.logBodies(calc)

  def logSteps(self, config):
    """the step size: dt, and the step fraction if the steps are adaptive (then dt is the longest step)"""
    dt = getattr(config, 'dt', config)   #a Config, or older callers' dt
    self.print('dt: ', dt)
    fraction = getattr(config, 'stepFraction', None)
    if fraction:
      self.print('step fraction: %g  (adaptive steps, at most dt)' % fraction)

  def logBodies(self, calc):
    """one line per body - the csv viewer reads these back to draw the bodies and their flow"""
    bodies = getattr(calc, 'bodies', [])
    if bodies:
      self.stats.GM = calc.GM   #the predictions use the calculator's bodies, not one solar mass
      self.stats.centre = sum(b.mass*b.pos for b in bodies)/sum(b.mass for b in bodies)
      if len(bodies) == 1:
        self.stats.spin = getattr(bodies[0], 'spin', 0.0)
    self.print('bodies:', len(bodies))
    for i, b in enumerate(bodies):
      self.print('body %d: mass %.6e kg (%.6g MS)  x %.6e m  y %.6e m  %s%s%s'
                 % (i+1, b.mass, b.mass/MS, b.x, b.y, 'black' if b.black else 'white',
                    '  spin %.10g' % b.spin if getattr(b, 'spin', 0) else '',
                    '  velocity %.6e %.6e m/s' % tuple(b.velocity) if getattr(b, 'moving', False) else ''))
    if getattr(calc, 'direction', None) is not None or getattr(calc, 'combine', 'squares') != 'squares':
      self.print('flow direction:', calc.describeDirection())
    if getattr(calc, 'moving', False):
      self.print('moving bodies:', 'each carries its flow (the space round it moves with it)' if calc.carried
                 else 'each takes its flow pattern along, the space not moving with it')
    if getattr(calc, 'wave', None) is not None:
      self.print('gravitational wave:', calc.wave.describe())

  def updatePosition(self, p, dt):
    """
    after each step: track the orbit statistics, and write a csv row when one is due - every freq seconds, at the
    step nearest the time (with fixed steps, freq a whole number of them, that is exactly every freq seconds);
    returns whether it wrote a row
    """
    self.t += dt
    d = self.stats.track(p, dt)
    if not self.csvFile:
      return False
    if self.freq == 0:
      self.writeRow(p, d)
      return True
    if self.nextRow is None:
      self.nextRow = self.freq
    if self.t < self.nextRow - dt/2:
      return False
    self.writeRow(p, d)
    while self.nextRow <= self.t + dt/2:
      self.nextRow += self.freq
    return True

  def writeRow(self, p, d=None):
    self.csvWriter.writerow([self.t, p.pt, length(p.pos) if d is None else d, p.pos[0], p.pos[1], p.v[0], p.v[1]])

  def logOrbit(self):
    s = self.stats
    minpos, maxpos, mn, mx = s.minpos, s.maxpos, s.min, s.max
    minP, maxP = s.endOrbit()
    self.print("orbit ", self.t/DAY, "days", "min:", mn, "max:", mx)
    #the same in full, for csv_viewer.py: when the orbit ended, and where its periapsis and apoapsis were
    self.print('orbit %d: t %r s  periapsis %r m at (%r, %r)  apoapsis %r m at (%r, %r)'
               % tuple([s.orbit] + [float(v) for v in (self.t, mn, minpos[0], minpos[1], mx, maxpos[0], maxpos[1])]))
    self.print(minP, maxP)
    s.resetExtremes()

  def finish(self, p):
    """
    the end of a run: how long it took, the closest approach, and - if there were whole orbits - their period,
    apsides and precession (against GR's leading term and its exact value for these apsides); if not, the angles
    the particle (and its velocity relative to the flow) ended up going at, as for a flyby
    """
    if self.csvFile:
      self.csvFile.flush()
    s = self.stats
    self.print()
    self.print('Simulation complete: ', time.time() - self.starttime, 'seconds (', (time.time() - self.starttime)/3600, ' hours)')
    self.print('sim time:', self.t)
    self.print('closest distance:', s.closest, ' ', s.closest/AU, 'AU')
    self.print()
    if s.orbit == 0:
      self.print('No orbits completed')
    elif s.orbit == 1:
      self.print('Only warmup orbit completed')
    if s.orbit < 2 or not s.summary():
      self.finishFlyby(p)
      return
    self.print('orbits:', s.orbit, ' average period', s.calcPeriod/DAY, ' days          predicted period:', s.predictedPeriod/DAY, ' days')
    self.print()
    self.print('calculated')
    self.print('  Periapsis:\t', s.calcPeriapsis, "\t", "{:0.2}".format(s.calcPeriapsis/AU), 'AU')
    self.print('  Apoapsis:\t', s.calcApoapsis, "\t", "{:0.2}".format(s.calcApoapsis/AU), 'AU')
    self.print('  semi-major:\t', s.calcSMA, "\t", "{:0.2}".format(s.calcSMA/AU), 'AU')
    self.print('  eccentricity:\t', s.calcEccentricity)
    self.print()
    self.print('predicted precession: ', s.predictedPrecession)
    if s.orbit == 1:
      self.print('Need >1 orbits to calculte precession')
      return
    accuracy = lambda calc, predicted: 100 - 100*abs((predicted - calc)/predicted)
    self.print('calc periapsis precession:', s.calcPPrecession, '   accuracy=', accuracy(s.calcPPrecession, s.predictedPrecession), '%')
    self.print('calc apoapsis precession:', s.calcAPrecession, '   accuracy=', accuracy(s.calcAPrecession, s.predictedPrecession), '%')
    if s.spin:
      #a rotating hole: the distances here are the river model's flat R; Kerr's r = sqrt(R^2 - a^2)
      a = s.spin*s.GM/C**2
      rp, ra = (math.sqrt(R*R - a*a) for R in (s.calcPeriapsis, s.calcApoapsis))
      prograde = s.sense*s.spin > 0
      exact = kerrPrecessionExact(rp, ra, s.GM/G, s.spin, prograde)
      label = 'Kerr exact precession (%s the spin) for these apsides:' % ('with' if prograde else 'against')
    else:
      exact = grPrecessionExact(s.calcPeriapsis, s.calcApoapsis, s.GM/G)
      label = 'GR exact precession for these apsides:'
    self.print(label, exact, '   periapsis accuracy=', accuracy(s.calcPPrecession, exact),
               '%   apoapsis accuracy=', accuracy(s.calcAPrecession, exact), '%')

  def finishFlyby(self, p):
    """the end of a run with no whole orbits: the predicted bend for the closest approach, and the final angles"""
    s = self.stats
    self.print('Angle:', 4*s.GM/(C**2*s.closest))
    self.print(p.v)
    self.print(p.v[0])
    speed = math.sqrt(p.v[0]**2 + p.v[1]**2)
    self.print(speed)
    self.print('Calc angle:', math.acos(p.v[0]/speed) if speed > 0 else 'none (v = 0)')
    w = math.sqrt(p.w[0]**2 + p.w[1]**2)
    self.print('Calc angle:', math.acos(p.w[0]/w) if w > 0 else 'none (w = 0)')
    self.print('')
