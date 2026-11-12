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
from engine.flow import Body, Calculator, Particle, Config, MinDistance, NewtonianCalculator, SpecialFlowCalculator, makeCalculator, calculatorName
from engine.logger import Log, TEST_LOG_DIR
from engine.vectors import length
from engine.exact import fallTime, rayTime, grPrecession, orbitPeriod, schwarzschildRadius, grDeflectionExact, grPrecessionExact, impactParameter


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
    self.assertIn('orbit 2: t ', text)
    self.assertIn('GR exact precession for these apsides', text)
    rows = list(csv.reader(read(log.csvFile.name).splitlines()))
    self.assertEqual(rows[0], ['t', 'pt', 'd', 'pos_x', 'pos_y', 'v_x', 'v_y'])
    self.assertAlmostEqual(float(rows[1][0]), 0.0)      #the start
    self.assertAlmostEqual(float(rows[2][0]), 3600.0)

  def testAdaptiveLightPastTheSun(self):
    """light from 10 AU to 10 AU past the Sun at 0.2 RSUN bends as GR does exactly, at its impact parameter cL/E"""
    dis, b = 10*AU, 0.2*RSUN
    calc = SpecialFlowCalculator([Body(MS)], order=2)
    p = Particle()
    p.pos = np.array([-dis, b])
    calc.initPW(p, np.array([C, 0.0]))
    bGR = impactParameter(p.pos, p.w, p.u)
    self.assertAlmostEqual(bGR/b, 1/(1 + math.sqrt(2*G*MS/dis)/C), delta=1e-9)   #b/(1 + u/c)
    config = Config()
    config.dt, config.stepFraction = 10.0, 0.001
    n = 0
    for dt in calc.steps(p, config, 2*dis/C):
      calc.move(p, dt)
      n += 1
    self.assertLess(n, 30000)   #about 20,000 steps, where fixed steps of 0.1 s take 100,000 and are less accurate
    bend = math.atan2(-p.w[1], p.w[0])
    self.assertAlmostEqual(bend/(4*G*MS/(C**2*b)), 1.0000755, delta=5e-6)   #as the 12-hour fixed-step runs
    self.assertAlmostEqual(bend/grDeflectionExact(bGR), 1, delta=1e-6)
    self.assertAlmostEqual(p.t, 2*dis/C, delta=1e-6)   #the steps stop exactly at the duration

  def testExactGR(self):
    """the exact GR integrals agree with their series where the series are good"""
    m = G*MS/C**2
    b = RSUN
    self.assertAlmostEqual(grDeflectionExact(b)/(4*m/b + 15*math.pi/4*(m/b)**2), 1, delta=1e-6)
    rp, ra = 46.0e9, 69.82e9
    p, e = 2*rp*ra/(rp + ra), (ra - rp)/(ra + rp)
    self.assertAlmostEqual(grPrecessionExact(rp, ra)/(6*math.pi*m/p + 1.5*math.pi*(18 + e*e)*(m/p)**2), 1, delta=1e-7)

  def testCloseOrbitPrecessesAsGR(self):
    """Mercury at 1/100,000 scale (196 Schwarzschild radii): precession as GR's exact value for its own apsides"""
    from studies.compare_step_size import orbit
    from studies.compare_second_order import precession, PERIHELION
    scale = 1e5
    period = orbitPeriod((MERCURY_MAX + PERIHELION)/2/scale)
    config = Config()
    config.dt, config.stepFraction = period/20, 0.001
    peris, apos, n, wall = orbit(MERCURY_MAX/scale, MERCURY_SPEED_AT_MAX*math.sqrt(scale), 4.5*period, config)
    exact = grPrecessionExact(np.mean([d for d, _ in peris]), np.mean([d for d, _ in apos]))
    self.assertAlmostEqual(precession(peris)/exact, 1, delta=2e-3)   #5e-4 at this step fraction, smaller with smaller steps

  def testKerrExact(self):
    """exact Kerr: the photon orbits and ISCOs at spin 0 and 1, and spin 0 is Schwarzschild"""
    from engine.exact import kerrPhotonOrbit, kerrISCO, kerrDeflectionExact, kerrPrecessionExact
    M = G*MS/C**2
    for spin, photon, isco in ((0, (3, 3), (6, 6)), (1, (1, 4), (1, 9))):
      self.assertAlmostEqual(kerrPhotonOrbit(MS, spin, True)/M, photon[0], places=6)
      self.assertAlmostEqual(kerrPhotonOrbit(MS, spin, False)/M, photon[1], places=6)
      self.assertAlmostEqual(kerrISCO(MS, spin, True)/M, isco[0], places=6)
      self.assertAlmostEqual(kerrISCO(MS, spin, False)/M, isco[1], places=6)
    self.assertAlmostEqual(kerrDeflectionExact(0.2*RSUN, MS, 0)/grDeflectionExact(0.2*RSUN), 1, delta=1e-12)
    rp, ra = 465229.09, 712558.12
    self.assertAlmostEqual(kerrPrecessionExact(rp, ra, MS, 0)/grPrecessionExact(rp, ra), 1, delta=1e-9)

  def testKerrRiver(self):
    """the rotating-hole river: at spin 0 it is SpecialFlowCalculator; at spin 0.9 light passing with and against the
    spin bends, and an orbit with the spin precesses, as exact Kerr says"""
    from engine.kerr import KerrFlowCalculator
    from engine.exact import kerrDeflectionExact, kerrPrecessionExact
    from studies.kerr_comparison import lightBend, orbitPrecession, MASS
    runs = []
    for calc in (SpecialFlowCalculator([Body(MS)]), KerrFlowCalculator([Body(MS)])):
      p = Particle()
      p.pos = np.array([0.0, MERCURY_MAX/1e5])
      calc.initPV(p, np.array([MERCURY_SPEED_AT_MAX*math.sqrt(1e5), 0.0]))
      for _ in range(2000):
        calc.move(p, 1e-5)
      runs.append(p.pos)
    self.assertLess(length(runs[0] - runs[1])/length(runs[0]), 1e-11)
    for b0 in (30, -30):
      bend, b = lightBend(0.9, b0, fraction=1e-3, start=3e3)
      self.assertAlmostEqual(bend/kerrDeflectionExact(b, MASS, 0.9), 1, delta=2e-4)   #6e-5; without the twist 1.6e-2
    peri, apo, rp, ra = orbitPrecession(0.9, True, orbits=2, fraction=1e-3)
    self.assertAlmostEqual(peri/kerrPrecessionExact(rp, ra, MASS, 0.9, True), 1, delta=2e-3)   #5e-4; without the twist 0.3

  def testFlowDirection(self):
    """setting the flow's direction changes only its direction: the default is the eikonal flow ('eikonal-exact' for
    two bodies, 'eikonal' for more; along g for one), a vector points that way everywhere, 'nearest' at the nearest
    body and 'centre' at the centre of mass; and a particle runs with it"""
    bodies = [Body(MS, -0.5*AU, 0.0), Body(MS, 0.5*AU, 0.0)]
    self.assertEqual(Calculator(bodies).direction, 'eikonal-exact')
    self.assertEqual(Calculator(bodies + [Body(MS, 0.0, AU)]).direction, 'eikonal')
    self.assertIsNone(Calculator([Body(MS)]).direction)
    pos = np.array([0.2*AU, 0.3*AU])
    u = Calculator(bodies, 'g').flow(pos)
    unit = lambda v: v/length(v)
    for direction, want in (((-1.0, 0.0), np.array([-1.0, 0.0])), ((0.0, -2.0), np.array([0.0, -1.0])),
                            ('nearest', unit(bodies[1].pos - pos)), ('centre', unit(-pos))):
      got = Calculator(bodies, direction).flow(pos)
      self.assertAlmostEqual(length(got)/length(u), 1.0, places=14)
      self.assertLess(length(unit(got) - want), 1e-14)
    calc = SpecialFlowCalculator(bodies, 2, 'centre')
    p = Particle()
    p.pos = np.array([-0.4*AU, 0.0])
    calc.initPW(p, np.array([0.0, 0.0]))
    for _ in range(100):
      calc.move(p, 10.0)
    self.assertGreater(p.pos[0], -0.4*AU)   #carried towards the middle, away from the nearer hole

  def testEikonalFlow(self):
    """the 'eikonal' flow has the usual magnitude and no curl, so its acceleration (u . grad) u is g even where g's
    field lines bend; space released off the half-way line falls as newtonian gravity says, and a particle dropped
    down the seam keeps to it"""
    from engine.integrate import rk4Gravity
    bodies = [Body(MS, -0.5*AU, 0.0), Body(MS, 0.5*AU, 0.0)]
    calc = SpecialFlowCalculator(bodies, 2, 'eikonal')
    newton = Calculator(bodies)
    for pos in (np.array([1.4*AU, 1.4*AU]), np.array([-0.3*AU, 0.2*AU]), np.array([-2*AU, -3*AU])):
      u = calc.flow(pos)
      self.assertAlmostEqual(length(u)/length(newton.flow(pos)), 1.0, places=14)
      h = 1e-6*AU
      a = length(u)*(calc.flow(pos + u/length(u)*h) - calc.flow(pos - u/length(u)*h))/(2*h)
      self.assertLess(length(a - newton.gravity(pos))/length(newton.gravity(pos)), 1e-4)
    #space moving with the flow from (-0.6, 1.2) AU, against newtonian gravity from the same start at v = u
    p = Particle()
    p.pos = np.array([-0.6*AU, 1.2*AU])
    calc.initPFreefall(p)
    pos, v, t = p.pos.copy(), p.v.copy(), 0.0
    while t < 2e6:   #down to 0.07 AU from the left hole; the difference falls as the step squared
      dt = min(0.004*calc.nearest(p.pos)/length(p.v), 2e6 - t)
      t += dt
      calc.move(p, dt)
      pos, v = rk4Gravity(newton, pos, v, dt)
    self.assertLess(length(p.pos - pos)/length(pos - bodies[0].pos), 1e-5)
    #dropped from rest on the half-way line it falls down it, through the middle and out the other side (newtonian
    #gravity: to y = -1 AU), crossing the seam with no kick - the line is unstable near the middle (for y^2 < 0.5
    #AU^2), so it ends a little off it
    p = Particle()
    p.pos = np.array([0.0, 1.0*AU])
    calc.initPV(p, np.array([0.0, 0.0]))
    low = p.pos[1]
    while p.v[1] <= 0:
      calc.move(p, 0.002*calc.nearest(p.pos)/max(length(p.v), length(p.u)))
      low = min(low, p.pos[1])
    self.assertLess(abs(p.pos[0]), 1e-3*AU)
    self.assertAlmostEqual(low/AU, -1.0, delta=1e-3)

  def testEikonalSeam(self):
    """for unequal masses the eikonal flow's seam goes through the potential's saddle, S is the same either side of
    it, and a particle crossing it keeps v (to first order) - light keeping |w| = c"""
    bodies = [Body(2*MS, -0.5*AU, 0.0), Body(MS, 0.5*AU, 0.0)]
    calc = SpecialFlowCalculator(bodies, 2, 'eikonal')
    field = calc.rayField()
    saddle = field.saddle(0, 1)
    self.assertAlmostEqual(saddle[0]/AU, 0.5*(math.sqrt(2) - 1)/(math.sqrt(2) + 1), places=9)   #2GM/(x+0.5)^2 = GM/(0.5-x)^2
    for y in (0.0, 0.5, 2.0, -4.0):
      lo, hi = -0.4*AU, 3*AU   #in body 0's region, and body 1's
      for _ in range(60):
        mid = (lo + hi)/2
        lo, hi = (mid, hi) if field.region(np.array([mid, y*AU])) == 0 else (lo, mid)
      seam = np.array([(lo + hi)/2, y*AU])
      self.assertLess(abs(field.action(seam, 0)/field.action(seam, 1) - 1), 1e-6)
      if y == 0.0:
        self.assertAlmostEqual(seam[0]/AU, saddle[0]/AU, delta=1e-4)
      for w in (np.array([30e3, 5e3]), np.array([C, 0.0])):
        p = Particle()
        p.pos = seam - np.array([1.0, 0.0])
        calc.initPW(p, w)
        v = p.v.copy()
        p.pos = seam + np.array([1.0, 0.0])   #now across the seam: re-side it
        calc.crossSeam(p, 0)
        if w[0] < C:
          self.assertLess(length(p.v - v)/length(v), 1e-3)   #the jump is up to 2|u| ~ 1e5 m/s: v kept to ~(u/c)^2
        else:
          self.assertAlmostEqual(length(p.w)/C, 1.0, places=12)   #light stays light

  def testEikonalExact(self):
    """the 'eikonal-exact' flow (engine/two_centre.py) is the 'eikonal' flow without tables: its acceleration is g to
    rounding, it agrees with the ray tables' direction and S, its seam goes through the saddle, and it is only for two
    bodies"""
    for masses in ((1, 1), (2, 1)):
      bodies = [Body(masses[0]*MS, -0.5*AU, 0.0), Body(masses[1]*MS, 0.5*AU, 0.0)]
      calc = SpecialFlowCalculator(bodies, 2, 'eikonal-exact')
      rays = SpecialFlowCalculator(bodies, 2, 'eikonal').rayField()
      field = calc.rayField()
      newton = Calculator(bodies)
      for pos in (np.array([1.4*AU, 1.4*AU]), np.array([-0.3*AU, 0.2*AU]), np.array([-2*AU, -3*AU]),
                  np.array([0.05*AU, 0.01*AU]), np.array([0.3*AU, 1e-9*AU]), np.array([2*AU, 0.0]),
                  np.array([-3*AU, 1e-7*AU])):   #just off the axis beyond a hole, where its path is nearly the axis
        u = calc.flow(pos)
        self.assertAlmostEqual(length(u)/length(newton.flow(pos)), 1.0, places=14)
        h = 1e-5*AU
        a = length(u)*(calc.flow(pos + u/length(u)*h, calc.region(pos)) - calc.flow(pos - u/length(u)*h, calc.region(pos)))/(2*h)
        self.assertLess(length(a - newton.gravity(pos))/length(newton.gravity(pos)), 1e-7)
        i = field.region(pos)
        self.assertEqual(i, rays.region(pos))
        self.assertLess(length(field.direction(pos) - rays.direction(pos)), 1e-6)
        self.assertLess(abs(field.action(pos, i)/rays.action(pos, i) - 1), 1e-6)
      saddle = field.saddle(0, 1)
      self.assertAlmostEqual(field.action(saddle, 0)/field.action(saddle, 1), 1.0, places=12)
      for side in (-1, 1):
        self.assertEqual(field.region(saddle + side*np.array([1e-6*AU, 0.0])), 0 if side < 0 else 1)
    with self.assertRaises(ValueError):
      Calculator([Body(), Body(MS, AU, 0.0), Body(MS, 0.0, AU)], 'eikonal-exact')

  def testGravitationalWave(self):
    """a plane wave through the plane is a flow of space (engine/waves.py): particles moving with it keep their TT
    coordinates, particles starting at rest move as geodesic deviation says, and light's round trip along an arm
    takes as long as in GR - each to first order in h; and a calculator with no bodies is the wave alone"""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'studies'))
    from engine.waves import PlaneWave
    from studies.grav_wave import roundTrip, strainMatrix, rateMatrix
    h = 1e-6
    wave = PlaneWave(plus=h, cross=0.5*h, frequency=100.0, phasePlus=0.3, phaseCross=1.1)
    calc = SpecialFlowCalculator([], 2, wave=wave)
    X0 = np.array([1e6, 4e5])
    self.assertTrue(np.array_equal(calc.flow(X0, None, 0.01), wave.flow(X0, 0.01)))
    free, rest = Particle(), Particle()
    free.pos, rest.pos = X0.copy(), X0.copy()
    calc.initPW(free, np.array([0.0, 0.0]))
    calc.initPV(rest, np.array([0.0, 0.0]))
    tt = X0 - strainMatrix(wave, 0.0) @ X0/2
    for _ in range(2000):   #one period
      calc.move(free, 5e-6)
      calc.move(rest, 5e-6)
    t = free.t
    self.assertLess(length(free.pos - (tt + strainMatrix(wave, t) @ tt/2))/(h*length(X0)), 1e-5)
    geodesic = X0 + (strainMatrix(wave, t) - strainMatrix(wave, 0.0) - rateMatrix(wave, 0.0)*t) @ X0/2
    self.assertLess(length(rest.pos - geodesic)/(h*length(X0)), 1e-4)
    arm = PlaneWave(plus=h, frequency=100.0, phasePlus=0.4)
    calc = SpecialFlowCalculator([], 2, wave=arm)
    L = 0.25*C/100.0
    T = roundTrip(calc, L, np.array([1.0, 0.0]), 0.002, steps=1000)
    want = 2*L*(1 - arm.strain(0.002)[0]/2)/C + arm.integral(0.002, 0.002 + T)[0]/2
    self.assertLess(abs(T - want)/(h*L/C), 1e-4)

  def testBackgroundFrames(self):
    """a flow that changes with time is written as frames (engine/background_frames.py): read back they give u and
    the acceleration of space, du/dt + (u . grad) u, at the frames' times, and the viewer's environment draws from
    them"""
    from engine.waves import PlaneWave
    from engine.background_frames import writeFrames, readFrames
    wave = PlaneWave(plus=1e-3, frequency=10.0)
    calc = SpecialFlowCalculator([], 2, wave=wave)
    folder = tempfile.mkdtemp()
    try:
      path = os.path.join(folder, 'frames.csv')
      writeFrames(path, calc, (-1e5, 1e5, -1e5, 1e5), np.arange(9)/80, cells=5)
      frames = readFrames(path)
      self.assertEqual((frames.times.size, frames.xs.size, frames.ys.size), (9, 5, 5))
      t, pos = 3/80, np.array([5e4, -5e4])   #a frame's time, on a grid point
      frame = frames.at(t)
      self.assertLess(length(frame.flow(pos) - wave.flow(pos, t))/length(wave.flow(pos, t)), 1e-7)
      rate = wave.rate(t)[0]
      second = -wave.plus*wave.omega**2*math.sin(wave.omega*t)
      want = np.array([(second/2 + rate**2/4)*pos[0], (-second/2 + rate**2/4)*pos[1]])
      self.assertLess(length(frame.gravity(pos) - want)/length(want), 1e-5)
      self.assertTrue(np.isnan(frame.flow(np.array([2e5, 0.0]))).all())   #outside the grid
      sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'viewer'))
      from viewer.data import Environment
      env = Environment([], [], None, path)
      self.assertTrue(env.hasField())
      self.assertFalse(Environment([], [], None, None).hasField())
    finally:
      shutil.rmtree(folder)

  def testKerrBackgrounds(self):
    """the rotating river's acceleration is u du/dR (GM/R^2 at spin 0), its twist gradient matches the twist's
    change, and a rotating hole's circles sit where r+, 2M, 0 and the special orbits are"""
    from engine.kerr import KerrFlowCalculator
    from viewer.data import Environment
    still = KerrFlowCalculator([Body(4e6*MS)])
    pos = np.array([3e10, 4e10])
    self.assertLess(length(still.gravity(pos) - Calculator([Body(4e6*MS)]).gravity(pos))/length(still.gravity(pos)), 1e-14)
    calc = KerrFlowCalculator([Body(4e6*MS, spin=0.9)])
    M = calc.M
    for R in (1.7*M, 3*M, 10*M):
      x, h = np.array([R, 0.0]), R*1e-5
      speed = lambda d: length(calc.flow(np.array([d, 0.0])))
      self.assertAlmostEqual(-length(calc.gravity(x))/(speed(R)*(speed(R + h) - speed(R - h))/(2*h)), 1, delta=1e-8)
      change = (calc.twistAt(x + [h, 0]) - calc.twistAt(x - [h, 0]))/(2*h)
      self.assertAlmostEqual(calc.twistGradient(x)/change, 1, delta=1e-8)
    env = Environment([(4e6*MS, 0.0, 0.0, True)], [0.9])
    self.assertAlmostEqual(env.ergosphere()/(math.sqrt(4 + 0.81)*M), 1, delta=1e-12)
    self.assertAlmostEqual(env.ring()/(0.9*M), 1, delta=1e-12)
    radii = {(kind, sense): R/M for kind, sense, R in env.specialOrbits()}
    self.assertAlmostEqual(radii['isco', 'with'], math.sqrt(2.32088**2 + 0.81), delta=1e-4)   #r = 2.32088 M (Bardeen et al.)
    self.assertLess(env.horizon(0), radii['photon', 'with']*M)
    flat = {kind: R/M for kind, sense, R in Environment([(4e6*MS, 0.0, 0.0, True)]).specialOrbits()}
    self.assertAlmostEqual(flat['photon'], 3, delta=1e-12)
    self.assertAlmostEqual(flat['isco'], 6, delta=1e-12)

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
    cfg = {'name': 'regressionStudy', 'calculator': 'SpecialFlowCalculator, second order',
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
    text = read(path[:-4] + '.log')
    self.assertIn('stopped: reached', text)
    self.assertIn('No orbits completed', text)

  def testOneKindOfRun(self):
    """every run counts orbits as they happen and stops at the first of its ends: an orbit given a distance end
    that it never reaches runs its orbits; a fall given an orbit end that it never reaches falls"""
    from engine.run import OrbitCounter
    import studies.run_study as run_study
    scale = 1e5
    r, v = MERCURY_MAX/scale, MERCURY_SPEED_AT_MAX*math.sqrt(scale)
    common = {'calculator': 'SpecialFlowCalculator, second order', 'bodies': [{'mass': MS, 'x': 0.0, 'y': 0.0, 'black': True}],
              'dt': 1e-4, 'stepFraction': 0.001, 'every': 1e-3, 'logDir': scratch(self)}
    with open(os.devnull, 'w') as quiet:
      stdout, sys.stdout = sys.stdout, quiet
      try:
        orbit = run_study.run(dict(common, name='regressionOrbitEnds', position=[0.0, r], velocity=[v, 0.0],
                                   end=[{'kind': 'orbits', 'value': 3}, {'kind': 'min', 'value': 1e3}]))
        fall = run_study.run(dict(common, name='regressionFallEnds', position=[0.0, r], velocity=[0.0, 0.0],
                                  end=[{'kind': 'orbits', 'value': 3}, {'kind': 'min', 'value': 2*RS/HOLE*MS}]))
      finally:
        sys.stdout = stdout
    text = read(orbit[:-4] + '.log')
    self.assertIn('stopped: 3 orbits', text)
    self.assertIn('orbit 4: t ', text)          #the part orbit, then 3 whole ones
    self.assertIn('orbits: 3', text)
    text = read(fall[:-4] + '.log')
    self.assertIn('stopped: reached', text)
    self.assertNotIn('orbit 1: t ', text)      #a straight fall turns no angle round the body


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
