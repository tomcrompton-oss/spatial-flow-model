"""
the flow step on the particle's momentum (engine/flow.py SpecialFlowCalculator step='momentum') against the velocity
step (order 2) it would replace - each test at a few step sizes, with how the error falls as the step halves (2 for
first order, 4 for second) and the time taken:

  close     an orbit from 200 to 600 Schwarzschild radii, 3 orbits: E and L, which GR keeps
  falls     into a black hole with the flow, and from rest far away into a white one, to just outside the horizon
            (tests/test_regression.py's): proper time against the exact fall time
  light     light sent straight out from 4 rs to 1 AU: its flight time against the exact integral
  mercury   Mercury's orbit at 1/10 scale (weak field, 30 days): the precession against exact GR's for its apsides
  curl      the flow along g round two bodies, which has curl, for a day from the eikonal study's start: the end point
            against the metric's own path (engine/geodesic.py's fourth-order steps at a tenth of the step), and the
            energy E, which the metric's paths keep (the flow is steady)

run: python3 studies/momentum_step.py [test ...]     (default all; prints, and writes
     logs/modelChecks/momentumStep_<datetime>/summary.log)
"""
import math
import os
import sys
import time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, Config, SpecialFlowCalculator
from engine.geodesic import GeodesicCalculator
from engine.exact import fallTime, rayTime, grPrecessionExact, schwarzschildRadius
from engine.logger import LOG_DIR
from engine.vectors import length
from engine.constants import *

STEPS = ('velocity', 'momentum')
RS = 2*G*MS/C**2


def calc(step, bodies, **kwargs):
  return SpecialFlowCalculator(bodies, 2, step=step, **kwargs)


def timed(f):
  start = time.time()
  out = f()
  return out, time.time() - start


def close(step, fraction):
  """the close orbit's E and L changes, as fractions"""
  c = calc(step, [Body(MS)])
  rp, ra = 200*RS, 600*RS
  a = (rp + ra)/2
  p = Particle()
  p.pos = np.array([rp, 0.0])
  c.initPV(p, np.array([0.0, math.sqrt(G*MS*(2/rp - 1/a))]))
  q0 = c.conserved(p)
  period = 2*math.pi*math.sqrt(a**3/(G*MS))
  config = Config()
  config.dt, config.stepFraction = period, fraction
  for dt in c.steps(p, config, 3*period):
    c.move(p, dt)
  q = c.conserved(p)
  return max(abs(q[n]/q0[n] - 1) for n in q0)


HOLE = 4000000*MS
START, STOP = 1.025*AU, 11816508000.0


def falls(step, dt):
  """the larger of the black and white falls' proper-time errors"""
  errs = []
  for black in (True, False):
    c = calc(step, [Body(HOLE, black=black)])
    p = Particle()
    p.pos = np.array([0.0, START])
    (c.initPFreefall if black else c.initPAgainstFlow)(p)
    while length(p.pos) >= STOP:
      c.move(p, dt)
    errs.append(abs(p.pt/fallTime(G*HOLE, START, length(p.pos)) - 1))
  return max(errs)


def light(step, dt):
  """light out from 4 rs to START: the flight time's error"""
  rs = schwarzschildRadius(HOLE)
  c = calc(step, [Body(HOLE)])
  p = Particle()
  p.pos = np.array([0.0, 4*rs])
  c.initPW(p, np.array([0.0, C]))
  n, prev = 0, p.pos[1]
  while p.pos[1] < START:
    prev = p.pos[1]
    c.move(p, dt)
    n += 1
  t = (n - 1)*dt + dt*(START - prev)/(p.pos[1] - prev)
  return abs(t/rayTime(rs, 4*rs, START) - 1)


def mercury(step, dt):
  """Mercury at 1/10 scale for 30 days: the precession's error against exact GR for its apsides"""
  from studies.compare_second_order import orbit, precession
  r, v = MERCURY_MAX/10, MERCURY_SPEED_AT_MAX*math.sqrt(10)
  peris, apos, _, _, _ = orbit(calc(step, [Body(MS)]), r, v, dt, 30*DAY)
  exact = grPrecessionExact(np.mean([d for d, _ in peris]), np.mean([d for d, _ in apos]), MS)
  return abs(precession(peris)/exact - 1)


CURL_BODIES = lambda: [Body(MS, -AU/2, 0.0), Body(MS, AU/2, 0.0)]
CURL_START = (np.array([0.0, 0.3*AU]), np.array([30e3, 0.0]))


def curlRun(c, dt, span=5*DAY):
  p = Particle()
  p.pos = CURL_START[0].copy()
  c.initPV(p, CURL_START[1])
  e0 = c.conserved(p)['E']
  for _ in range(int(round(span/dt))):
    c.move(p, dt)
  return p.pos, c.conserved(p)['E']/e0 - 1


CURL_TRUTH = {}


def curl(step, dt):
  """the flow along g (curl): the end point's distance from the metric's own path, and E's change"""
  if 'x' not in CURL_TRUTH:
    CURL_TRUTH['x'] = curlRun(GeodesicCalculator(CURL_BODIES(), direction='g'), 60.0)[0]
  x, dE = curlRun(calc(step, CURL_BODIES(), direction='g'), dt)
  return length(x - CURL_TRUTH['x']), dE


TESTS = {
  'close': (close, (1e-3, 5e-4, 2.5e-4), 'step fraction', 'largest |change| of E, L (fraction)'),
  'falls': (falls, (1.0, 0.5, 0.25), 'dt (s)', 'proper time error (fraction), worse of black and white'),
  'light': (light, (4.0, 2.0, 1.0), 'dt (s)', 'flight time error (fraction)'),
  'mercury': (mercury, (100.0, 50.0, 25.0), 'dt (s)', 'precession error (fraction)'),
  'curl': (curl, (1200.0, 600.0, 300.0), 'dt (s)', 'end point from the metric\'s path (m); E change (fraction)'),
}


def main():
  chosen = sys.argv[1:] or list(TESTS)
  folder = os.path.join(LOG_DIR, 'modelChecks', 'momentumStep_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = ['the momentum step against the velocity step (order 2): errors at each step, the factor each halving '
           'cuts them by (2 first order, 4 second), and the time taken']
  for name in chosen:
    f, sizes, label, what = TESTS[name]
    lines.append('')
    lines.append('== %s: %s at %s %s' % (name, what, label, ', '.join('%g' % s for s in sizes)))
    for step in STEPS:
      runs = [timed(lambda s=s: f(step, s)) for s in sizes]
      errs = [r[0] for r in runs]
      first = [e[0] if isinstance(e, tuple) else e for e in errs]
      text = '  %-9s %s' % (step, '  '.join(('%.2e' % e) if not isinstance(e, tuple) else '%.2e m, E %+.1e' % e
                                            for e in errs))
      text += '   halving cuts by %s' % ', '.join('%.1f' % (a/b) if b else '-' for a, b in zip(first, first[1:]))
      text += '   %.1f s' % sum(r[1] for r in runs)
      lines.append(text)
      print(lines[-1], flush=True)
  print('\n'.join(lines))
  with open(os.path.join(folder, 'summary.log'), 'w') as fh:
    fh.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
