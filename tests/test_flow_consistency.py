"""
checks that the flow from Calculator.flow is consistent with gravity, where there is more than one body

a piece of space at point A moves at the flow u(A); if it then accelerates at g it reaches point B moving at
the flow there, u(B) - as it does for a single body, where u is the speed of a fall from rest at infinity.
each path starts at A with velocity u(A), is integrated (RK4) under Calculator.gravity for a short time, and
the velocity it arrives with is compared with u(B) in size and direction

each scenario runs with three flow directions (Calculator.direction):
  'g'              along the net g: the speed always matches, but off the line through the bodies the direction is
                   1-27 degrees out, since that flow has curl - kept as the case the eikonal flows fix, and expected
                   to fail
  'eikonal'        down zero-energy paths from the nearest body, from the ray tables (engine/eikonal.py)
  'eikonal-exact'  the same, worked out exactly for two bodies (engine/two_centre.py)
the eikonal flows have no curl, so space at u accelerating at g stays at u - except across their seam, where the
flow's direction jumps by design: paths that end on the other side of it from A are left out (and logged)

each scenario writes tests/logs/flowtest/flowtest_<scenario>_<direction>_<datetime>.log (bodies and results) and
.csv (the paths, with the travelled velocity v and the calculated flow u at each point) for the viewer

run: python3 tests/test_flow_consistency.py      (-v lists every scenario)
"""
import csv
import math
import unittest
import numpy as np
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
from engine.flow import Body, Calculator
from engine.logger import Log, TEST_LOG_DIR
from engine.constants import *
from engine.integrate import rk4Gravity

MAX_SPEED_ERROR = 1.0   #% difference allowed between |v| at B and |u(B)|
MAX_ANGLE_ERROR = 1.0   #degrees allowed between v at B and u(B)
TRAVEL = 0.2            #each path covers about this fraction of A's distance to the nearest body
STEPS = 2000            #RK4 steps per path
CSV_ROWS = 20           #points written to the csv along each path
MIN_DISTANCE = 0.1*AU   #A points closer than this to a body are left out

SEP = 0.5*AU            #bodies at (-SEP, 0) and (+SEP, 0), 1 AU apart

#A points in AU: hand picked, then a grid over the bodies
POINTS = [(0, 0.5), (0, -1), (1, 0), (-1.2, 0.3), (0.3, 0.2), (2, 2), (-0.2, -0.4), (0.8, 0.6), (5, 0), (0, 3)]
POINTS += [(float(x), float(y)) for y in np.arange(-1.5, 1.51, 0.5) for x in np.arange(-2, 2.01, 0.5)]
POINTS = list(dict.fromkeys(POINTS))   #without repeats

DIRECTIONS = ['g', 'eikonal', 'eikonal-exact']

SCENARIOS = [
  ('twoBlackHoles', [Body(MS, -SEP, 0), Body(MS, SEP, 0)]),
  ('twoWhiteHoles', [Body(MS, -SEP, 0, black=False), Body(MS, SEP, 0, black=False)]),
  ('whiteAndBlackHole', [Body(MS, -SEP, 0, black=False), Body(MS, SEP, 0)]),
]


def travel(calc, a, region=None):
  """
  follow space from A: start at u(A) (from the given side of the seam, if the flow has one), accelerate at g
  returns B, the velocity there, and CSV_ROWS + 1 samples (t, pos, v) along the way
  """
  pos = np.array(a, dtype=float)
  v = calc.flow(pos, region)
  nearest = min(np.linalg.norm(pos - b.pos) for b in calc.bodies)
  dt = TRAVEL*nearest/np.linalg.norm(v)/STEPS
  samples = [(0.0, pos, v)]
  for i in range(STEPS):
    pos, v = rk4Gravity(calc, pos, v, dt)
    if (i + 1) % (STEPS//CSV_ROWS) == 0:
      samples.append(((i + 1)*dt, pos, v))
  return pos, v, samples


def compare(calc, a, region=None):
  """speed error (%) and angle error (degrees) between the travelled velocity and u(B)"""
  b, v, samples = travel(calc, a, region)
  u = calc.flow(b)
  speedError = 100*abs(np.linalg.norm(v) - np.linalg.norm(u))/np.linalg.norm(u)
  cos = np.dot(v, u)/(np.linalg.norm(v)*np.linalg.norm(u))
  angleError = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
  return b, v, u, speedError, angleError, samples


class FlowTests(unittest.TestCase):

  def checkScenario(self, name, bodies, direction):
    calc = Calculator(bodies, direction)
    log = Log('flowtest_%s_%s' % (name, direction), True, False, os.path.join(TEST_LOG_DIR, 'flowtest'))   #apart from the studies' logs
    calc.log = log
    log.logBodies(calc)
    log.print('flow test: start at A with u(A), accelerate at g; v at B should equal u(B)')
    log.print('limits: speed %g%%, angle %g degrees' % (MAX_SPEED_ERROR, MAX_ANGLE_ERROR))
    log.print()
    log.print('  %-14s %-18s %12s %12s %9s %9s' % ('A (AU)', 'B (AU)', '|v| km/s', '|u(B)| km/s', 'speed %', 'angle deg'))

    with open(log.file.name[:-4] + '.csv', 'w', newline='') as f:
      out = csv.writer(f)
      out.writerow(['elapsed', 'pos_x', 'pos_y', 'v_x', 'v_y', 'u_x', 'u_y'])
      failed = 0
      tested = 0
      crossed = 0
      for p in POINTS:
        a = np.array(p, dtype=float)*AU
        if min(np.linalg.norm(a - body.pos) for body in bodies) < MIN_DISTANCE:
          continue
        if np.linalg.norm(calc.flow(a)) == 0:
          log.print('  %-14s no flow at A (g=0), left out' % ('(%g, %g)' % p))
          continue
        side = calc.region(a)   #on the seam itself either side will do, but the same one throughout
        b, v, u, speedError, angleError, samples = compare(calc, a, side)
        if side != calc.region(b):
          crossed += 1
          log.print('  %-14s %-18s crosses the seam, left out' % ('(%g, %g)' % p, '(%.4g, %.4g)' % (b[0]/AU, b[1]/AU)))
          continue
        tested += 1
        ok = speedError <= MAX_SPEED_ERROR and angleError <= MAX_ANGLE_ERROR
        failed += not ok
        log.print('  %-14s %-18s %12.4f %12.4f %9.4f %9.4f  %s' % ('(%g, %g)' % p, '(%.4g, %.4g)' % (b[0]/AU, b[1]/AU),
                  np.linalg.norm(v)/1000, np.linalg.norm(u)/1000, speedError, angleError, 'ok' if ok else 'FAIL'))
        for t, pos, vel in samples:
          flow = calc.flow(pos)
          out.writerow([t, pos[0], pos[1], vel[0], vel[1], flow[0], flow[1]])
        out.writerow([''] * 7)   #an empty row ends the path
        with self.subTest(scenario=name, A=p):
          self.assertLessEqual(speedError, MAX_SPEED_ERROR, 'speed at B is %.3f%% from |u(B)|' % speedError)
          self.assertLessEqual(angleError, MAX_ANGLE_ERROR, 'direction at B is %.3f degrees from u(B)' % angleError)
    log.print()
    log.print('%s, %s: %d of %d paths passed%s' % (name, direction, tested - failed, tested,
                                                    ', %d crossed the seam' % crossed if crossed else ''))
    log.close()


def makeTest(scenario, direction):
  test = lambda self: self.checkScenario(*SCENARIOS[scenario], direction)
  return unittest.expectedFailure(test) if direction == 'g' else test   #the flow along g has curl (see above)


for i, (name, _) in enumerate(SCENARIOS):
  for direction in DIRECTIONS:
    setattr(FlowTests, 'test%s%s_%s' % (name[0].upper(), name[1:], direction.replace('-', '_')), makeTest(i, direction))


if __name__ == '__main__':
  unittest.main()
