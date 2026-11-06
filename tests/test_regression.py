"""
quick regression tests: the engine against exact results and against numbers from earlier runs, so a change can be
checked in well under a minute. files they write go in a folder in tests/logs/, apart from the studies' logs, and
are removed afterwards (set KEEP_TEST_LOGS=1 to keep them)

run: python3 -m unittest discover tests        (or: python3 tests/test_regression.py -v)
"""
import csv
import math
import os
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.constants import *
from engine.flow import Body, Particle, Config, MinDistance, NewtonianCalculator, SpecialFlowCalculator, makeCalculator, calculatorName
from engine.logger import Log, TEST_LOG_DIR
from engine.exact import fallTime, rayTime, grPrecession, orbitPeriod, schwarzschildRadius


def read(path):
  with open(path) as f:
    return f.read()


def scratch(test):
  """a fresh folder in tests/logs for a test's files, removed when it ends (KEEP_TEST_LOGS=1 keeps it)"""
  os.makedirs(TEST_LOG_DIR, exist_ok=True)
  folder = tempfile.mkdtemp(prefix='regression_', dir=TEST_LOG_DIR)
  if not os.environ.get('KEEP_TEST_LOGS'):
    test.addCleanup(shutil.rmtree, folder, True)
  return folder

HOLE = 4000000*MS         #the black / white hole of the descent studies
START = 1.025*AU          #where the descents start
RS = schwarzschildRadius(HOLE)
STOP = 11816508000.0      #where the descent studies stop: just outside RS, which the white-hole descent only creeps towards
MAX_STEPS = 1000000       #no test runs on for ever


def fall(order, dt, black=True):
  """the descent studies: freefall into a black hole (with the flow), or thrown into a white one (against it)"""
  calc = SpecialFlowCalculator([Body(HOLE, black=black)], order=order)
  p = Particle()
  p.pos = np.array([0.0, START])
  (calc.initPFreefall if black else calc.initPAgainstFlow)(p)
  for _ in range(MAX_STEPS):
    if np.linalg.norm(p.pos) < STOP:
      return p
    calc.move(p, dt)
  raise AssertionError('the descent did not reach %g m' % STOP)


def ray(order, dt):
  """light sent straight out from 4 rs to START; returns its flight time, interpolated across the last step"""
  calc = SpecialFlowCalculator([Body(HOLE)], order=order)
  p = Particle()
  p.pos = np.array([0.0, 4*RS])
  calc.initPW(p, np.array([0.0, C]))
  n, prev = 0, p.pos[1]
  while p.pos[1] < START:
    prev = p.pos[1]
    calc.move(p, dt)
    n += 1
    if n > MAX_STEPS:
      raise AssertionError('the light ray did not get out')
  return (n - 1)*dt + dt*(START - prev)/(p.pos[1] - prev)


class Engine(unittest.TestCase):

  def testBlackHoleFallTime(self):
    """a fall from rest at infinity takes (2/3)(a^1.5 - d^1.5)/sqrt(2GM), at either order"""
    for order, dt, tolerance in ((1, 0.1, 1e-4), (2, 1.0, 1e-5)):
      with self.subTest(order=order):
        p = fall(order, dt)
        exact = fallTime(G*HOLE, START, np.linalg.norm(p.pos))
        self.assertLess(abs(p.t - exact)/exact, tolerance)
        self.assertAlmostEqual(np.linalg.norm(p.w), 0.0)   #moving with the flow, so no time dilation
        self.assertAlmostEqual(p.pt, p.t, places=6)

  def testWhiteHoleDescentUnchanged(self):
    """the white-hole descent (astroDescend, first order, dt = 0.01 s) gives what it did before the refactoring"""
    p = fall(1, 0.01, black=False)
    self.assertAlmostEqual(p.t, 2227.2, places=6)
    self.assertAlmostEqual(p.pt, 444.8164739365552, places=6)

  def testLightLeavingABlackHole(self):
    """light climbs at c - u: the flight time matches the exact integral, much more closely at second order"""
    exact = rayTime(RS, 4*RS, START)
    self.assertLess(abs(ray(1, 1.0) - exact)/exact, 5e-4)
    self.assertLess(abs(ray(2, 1.0) - exact)/exact, 1e-6)

  def testSecondOrderOrbit(self):
    """Mercury at 1/10 scale, dt = 10 s: the second-order orbit holds steady and precesses about as GR says"""
    from studies.compare_second_order import orbit, growth, precession, PERIHELION
    r, v = MERCURY_MAX/10, MERCURY_SPEED_AT_MAX*math.sqrt(10)
    a, e = (MERCURY_MAX + PERIHELION)/20, (MERCURY_MAX - PERIHELION)/(MERCURY_MAX + PERIHELION)
    peris, apos, _, _, _ = orbit(SpecialFlowCalculator([Body(MS)], order=2), r, v, 10, 12*DAY)
    self.assertGreaterEqual(len(apos), 3)
    self.assertLess(abs(growth(apos)), 10e3)    #m per orbit (first order: about 29,000 km)
    pp, pa = precession(peris), precession(apos)
    self.assertAlmostEqual(pp/pa, 1, delta=0.01)   #periapsis and apoapsis agree
    self.assertAlmostEqual(pp/grPrecession(a, e), 1, delta=0.1)

  def testNewtonianOrbitAndLog(self):
    """a newtonian orbit through Calculator.orbitalSim: the period, the log's statistics and its files"""
    folder = scratch(self)
    log = Log('regressionOrbit', True, True, folder)
    log.freq = 3600
    calc = NewtonianCalculator([Body(MS)])
    p = Particle()
    p.pos = np.array([0.0, MERCURY_MAX/10])
    p.v = np.array([MERCURY_SPEED_AT_MAX*math.sqrt(10), 0.0])
    config = Config()
    config.dt, config.durationDays = 10, 12
    with open(os.devnull, 'w') as quiet:
      stdout, sys.stdout = sys.stdout, quiet
      try:
        calc.orbitalSim(p, config, log)
      finally:
        sys.stdout = stdout
    self.assertGreaterEqual(log.orbit, 3)
    exact = orbitPeriod((log.calcPeriapsis + log.calcApoapsis)/2)
    self.assertAlmostEqual(log.calcPeriod/exact, 1, delta=1e-3)
    self.assertAlmostEqual(log.calcApoapsis/(MERCURY_MAX/10), 1, delta=1e-3)
    log.close()
    text = read(log.file.name)
    self.assertIn('study type: orbit', text)
    self.assertIn('orbit 2: t ', text)
    rows = list(csv.reader(read(log.csvFile.name).splitlines()))
    self.assertEqual(rows[0], ['t', 'pt', 'd', 'pos_x', 'pos_y', 'v_x', 'v_y'])
    self.assertAlmostEqual(float(rows[1][0]), 3600.0)

  def testAdaptiveLightPastTheSun(self):
    """adaptive steps: light from 10 AU to 10 AU grazing the Sun at 0.2 RSUN bends as in the 12-hour fixed-step runs"""
    dis, b = 10*AU, 0.2*RSUN
    calc = SpecialFlowCalculator([Body(MS)], order=2)
    p = Particle()
    p.pos = np.array([-dis, b])
    calc.initPW(p, np.array([C, 0.0]))
    config = Config()
    config.dt, config.stepFraction = 10.0, 0.001
    n = 0
    for dt in calc.steps(p, config, 2*dis/C):
      calc.move(p, dt)
      n += 1
    self.assertLess(n, 30000)   #about 20,000 steps, where fixed steps of 0.1 s take 100,000 and are less accurate
    bend = math.atan2(-p.w[1], p.w[0])
    self.assertAlmostEqual(bend/(4*G*MS/(C**2*b)), 1.0000755, delta=5e-6)
    self.assertAlmostEqual(p.t, 2*dis/C, delta=1e-6)   #the steps stop exactly at the duration

  def testCsvRowsWithAdaptiveSteps(self):
    """with uneven steps the csv rows come at the steps nearest each interval"""
    log = Log('regressionRows', False, True, scratch(self))
    log.freq = 100.0
    p = Particle()
    for dt in [7.0, 13.0, 29.0, 41.0, 3.0, 50.0, 11.0, 60.0]:
      log.updatePosition(p, dt)
    log.close()
    rows = [float(r[0]) for r in list(csv.reader(read(log.csvFile.name).splitlines()))[1:]]
    self.assertEqual(rows, [90.0, 214.0])   #steps end at 7, 20, 49, 90, 93, 143, 154, 214: nearest 100 and 200 s

  def testCalculatorNames(self):
    """names old and new, as in logs and sim configs, make the right calculator"""
    for name, order in (('NewSpecialFlowCalculator', 1), ('SecondOrderSpecialFlowCalculator', 2),
                        ('SpecialFlowCalculator, second order', 2), ('calc:  <flow.SpecialFlowCalculator object, order 1>', 1)):
      calc = makeCalculator(name, [Body(MS)])
      self.assertIsInstance(calc, SpecialFlowCalculator)
      self.assertEqual(calc.order, order)
    self.assertIsInstance(makeCalculator('NewtonianCalculator', [Body(MS)]), NewtonianCalculator)
    self.assertIsNone(calculatorName('NoSuchCalculator'))


class Studies(unittest.TestCase):

  def testRunStudyFromConfig(self):
    """a study from a config (as the viewer's Sim tab runs them): estimate, run, files, and the end condition"""
    import studies.run_study as run_study
    folder = scratch(self)
    cfg = {'name': 'regressionStudy', 'type': 'hyperbolic', 'calculator': 'SpecialFlowCalculator, second order',
           'bodies': [{'mass': HOLE, 'x': 0.0, 'y': 0.0, 'black': True}], 'position': [0.0, START],
           'velocity': [0.0, -math.sqrt(2*G*HOLE/START)], 'dt': 1.0, 'every': 100.0,
           'end': {'kind': 'min', 'value': STOP}, 'logDir': folder}
    steps, seconds, how = run_study.estimate(cfg)
    self.assertAlmostEqual(steps/1202, 1, delta=0.1)   #the fall takes about 1,202 s
    with open(os.devnull, 'w') as quiet:
      stdout, sys.stdout = sys.stdout, quiet
      try:
        path = run_study.run(cfg)
      finally:
        sys.stdout = stdout
    self.assertTrue(path.startswith(folder))
    rows = list(csv.reader(read(path).splitlines()))[1:]
    self.assertAlmostEqual(float(rows[0][3 + 1]), START)            #the starting row
    self.assertLess(float(rows[-1][2]), STOP)                       #ended at the horizon
    self.assertIn('study type: hyperbolic', read(path[:-4] + '.log'))


class Viewer(unittest.TestCase):

  def testViewerReadsAStudy(self):
    """the viewer imports, and reads a study's csv"""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'viewer'))
    import csv_viewer
    folder = scratch(self)
    path = os.path.join(folder, 'regressionViewer_2026-01-01_00-00-00.csv')
    with open(path, 'w') as f:
      f.write('t,pt,d,pos_x,pos_y,v_x,v_y\n0,0,1,0,1,1,0\n1,1,1,1,0,0,-1\n')
    data = csv_viewer.Dataset(path)
    self.assertEqual(data.nrows, 2)
    self.assertEqual(csv_viewer.studyName(path), 'regressionViewer')
    self.assertIsNotNone(csv_viewer.flow)
    self.assertIsNotNone(csv_viewer.simrun)


if __name__ == '__main__':
  unittest.main()
