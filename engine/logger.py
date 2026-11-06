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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   #the project folder
LOG_DIR = os.path.join(ROOT, 'logs')                #study logs
TEST_LOG_DIR = os.path.join(ROOT, 'tests', 'logs')   #regression test logs, kept apart from the studies'


def studyFolder(studyName):
  """the folder a study's logs go in: its name up to the first '_'"""
  return studyName.split('_')[0] or studyName


class OrbitStats:
  """
  the closest and farthest points (from the origin) since the last orbit ended, and a record of each orbit;
  an orbit ends when Calculator.orbitalSim sees the particle cross +y
  """

  def __init__(self, gm=G*MS):
    self.GM = gm     #for the predicted period and precession; Log.start / logBodies set it from the calculator
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
    d = np.linalg.norm(p.pos)
    if d > self.max:
      self.max, self.maxpos = d, p.pos.copy()
    if d < self.min:
      self.min, self.minpos = d, p.pos.copy()
    return d

  def endOrbit(self):
    """record the orbit just ended; returns the angles of its periapsis and apoapsis"""
    self.orbit += 1
    sma = (self.min + self.max)/2
    e = 1 - 2/(self.max/self.min + 1)
    minP = math.pi - math.acos(self.minpos[1]/self.min)   #total precession
    maxP = math.acos(self.maxpos[1]/self.max)
    self.periods.append(self.period)
    self.periapsis.append(self.min)
    self.apoapsis.append(self.max)
    self.semiMajorAxis.append(sma)
    self.eccentricity.append(e)
    self.periapsisAngle.append(minP)
    if len(self.periapsisAngle) > 1:
      self.periapsisPrecession.append(self.periapsisAngle[-1] - self.periapsisAngle[-2])
    self.apoapsisAngle.append(maxP)
    if len(self.apoapsisAngle) > 1:
      self.apoapsisPrecession.append(self.apoapsisAngle[-1] - self.apoapsisAngle[-2])
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
    self.predictedPrecession = (24*math.pi**3)*(self.calcSMA**2)/(self.predictedPeriod**2 * C**2 * (1 - self.calcEccentricity**2))
    if n > 1:
      self.calcPPrecession = sum(self.periapsisPrecession)/n
      self.calcAPrecession = sum(self.apoapsisPrecession)/n
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

  def start(self, maxn, p, calc, dt):
    self.starttime = time.time()
    self.startpos = p.pos
    self.print('Starting estimated duration:', "{:.2f}".format(maxn/calc.runspeed), 'seconds (',
               "{:.2}".format(maxn/(calc.runspeed*3600)), ') hours')
    self.print('calc: ', calc)
    self.print('dt: ', dt)
    self.logBodies(calc)

  def logBodies(self, calc):
    """one line per body - the csv viewer reads these back to draw the bodies and their flow"""
    bodies = getattr(calc, 'bodies', [])
    if bodies:
      self.stats.GM = calc.GM   #the predictions use the calculator's bodies, not one solar mass
    self.print('bodies:', len(bodies))
    for i, b in enumerate(bodies):
      self.print('body %d: mass %.6e kg (%.6g MS)  x %.6e m  y %.6e m  %s'
                 % (i+1, b.mass, b.mass/MS, b.x, b.y, 'black' if b.black else 'white'))

  def updatePosition(self, p, dt):
    """after each step: track the orbit statistics, and write a csv row when one is due"""
    self.t += dt
    d = self.stats.track(p, dt)
    if self.csvFile and (self.freq == 0 or round(self.t/dt) % round(self.freq/dt) == 0):
      self.writeRow(p, d)

  def writeRow(self, p, d=None):
    self.csvWriter.writerow([self.t, p.pt, np.linalg.norm(p.pos) if d is None else d, p.pos[0], p.pos[1], p.v[0], p.v[1]])

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

  def finishOrbit(self):
    if self.csvFile:
      self.csvFile.flush()
    self.print()
    self.print('Simulation complete: ', time.time() - self.starttime, 'seconds (', (time.time() - self.starttime)/3600, ' hours)')
    self.print('sim time:', self.t)
    self.print()
    s = self.stats
    if s.orbit == 0:
      self.print('No orbits completed')
      return
    if not s.summary():
      self.print('Only warmup orbit completed')
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
    else:
      accuracy = lambda calc: 100 - 100*abs((s.predictedPrecession - calc)/s.predictedPrecession)
      self.print('calc periapsis precession:', s.calcPPrecession, '   accuracy=', accuracy(s.calcPPrecession), '%')
      self.print('calc apoapsis precession:', s.calcAPrecession, '   accuracy=', accuracy(s.calcAPrecession), '%')

  def finishHyperbolic(self, p):
    if self.csvFile:
      self.csvFile.flush()
    s = self.stats
    self.print('finish hyperbolic:', time.time() - self.starttime, 'seconds (', (time.time() - self.starttime)/3600, ' hours)')
    self.print('sim time:', self.t)
    self.print('closest distance:', s.min, ' ', s.min/AU, 'AU')
    self.print('Angle:', 4*s.GM/(C**2*s.min))
    self.print(p.v)
    self.print(p.v[0])
    speed = math.sqrt(p.v[0]**2 + p.v[1]**2)
    self.print(speed)
    self.print('Calc angle:', math.acos(p.v[0]/speed))
    w = math.sqrt(p.w[0]**2 + p.w[1]**2)
    self.print('Calc angle:', math.acos(p.w[0]/w) if w > 0 else 'none (w = 0)')
    self.print('')
