"""
fixed against adaptive steps (Calculator.stepSize), with the second-order SpecialFlowCalculator:

1. Mercury at 1/10 scale for 12 days (eccentricity 0.21): apoapsis growth and precession against GR
2. the close orbit (1/100,000 scale, about 3 degrees of precession an orbit), 6 orbits: precession against GR
3. light from 10 AU to 10 AU passing the Sun at 0.2 RSUN: the bend against 4GM/c^2 b (the first-order run at
   dt = 0.00001 s gave 1.000076 of it, in about 12 hours)

for each: the steps taken and the time, so the accuracy can be compared for the work done

writes logs/compareStepSize/compareStepSize_<datetime>.log

run: python3 studies/compare_step_size.py      (a few minutes)
"""
import math
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, Config, SpecialFlowCalculator
from engine.logger import Log
from engine.constants import *
from engine.exact import grPrecession, orbitPeriod
from studies.compare_second_order import apsis, growth, precession, PERIHELION


def orbit(r, v, duration, config):
  """an orbit from (0, r) moving +x at v; each whole orbit's periapsis and apoapsis, the steps and the wall time"""
  calc = SpecialFlowCalculator([Body(MS)], order=2)
  p = Particle()
  p.pos = np.array([0.0, r])
  calc.initPV(p, np.array([v, 0.0]))
  last = [(0.0, np.linalg.norm(p.pos), p.pos.copy())]
  peris, apos, crossings, steps = [], [], 0, 0
  current = {'peri': None, 'apo': None}
  t0 = time.time()
  for dt in calc.steps(p, config, duration):
    old = p.pos.copy()
    calc.move(p, dt)
    steps += 1
    last = (last + [(p.t, np.linalg.norm(p.pos), p.pos.copy())])[-3:]
    if len(last) == 3:
      (_, a, _), (_, b, _), (_, c, _) = last
      if b < a and b <= c:
        current['peri'] = apsis([x[0] for x in last], [x[1] for x in last], [x[2] for x in last])
      if b > a and b >= c:
        current['apo'] = apsis([x[0] for x in last], [x[1] for x in last], [x[2] for x in last])
    if old[1] < 0 and p.pos[1] >= 0:
      crossings += 1
      if crossings > 1 and current['peri'] and current['apo']:
        for store, key in ((peris, 'peri'), (apos, 'apo')):
          _, dist, pos = current[key]
          store.append((dist, math.atan2(pos[1], pos[0])))
      current = {'peri': None, 'apo': None}
  return peris, apos, steps, time.time() - t0


def steps(dt, fraction=None):
  config = Config()
  config.dt, config.stepFraction = dt, fraction
  return config


def orbitTable(log, title, scale, orbits, fixed, adaptive):
  r, v = MERCURY_MAX/scale, MERCURY_SPEED_AT_MAX*math.sqrt(scale)
  a, e = (MERCURY_MAX + PERIHELION)/2/scale, (MERCURY_MAX - PERIHELION)/(MERCURY_MAX + PERIHELION)
  period, gr = orbitPeriod(a), grPrecession(a, e)
  log.print(title + '; GR precession %.5e rad/orbit' % gr)
  log.print()
  log.print('  %-28s %9s %8s %16s %12s %12s' % ('steps', 'steps', 'time s', 'apo growth m/orb', 'peri / GR', 'apo / GR'))
  runs = [('fixed, %g steps/orbit' % n, steps(period/n)) for n in fixed] + \
         [('adaptive, fraction %g' % f, steps(period/20, f)) for f in adaptive]   #adaptive: no step over 1/20 orbit
  for label, config in runs:
    peris, apos, n, wall = orbit(r, v, (orbits + 1.5)*period, config)
    log.print('  %-28s %9d %8.1f %16.4g %12.6f %12.6f' % (label, n, wall, growth(apos), precession(peris)/gr, precession(apos)/gr))
  log.print()


def light(log, fixed, adaptive):
  dis, b = 10*AU, 0.2*RSUN
  predicted = 4*G*MS/(C**2*b)
  log.print('3. light from %g AU to %g AU passing the Sun at 0.2 RSUN; 4GM/c^2 b = %.6e rad' % (dis/AU, dis/AU, predicted))
  log.print('   (first order, dt = 0.00001 s: bend / prediction 1.000076)')
  log.print()
  log.print('  %-28s %9s %8s %16s' % ('steps', 'steps', 'time s', 'bend / 4GM/c2b'))
  runs = [('fixed, dt %g s' % dt, steps(dt)) for dt in fixed] + [('adaptive, fraction %g' % f, steps(10.0, f)) for f in adaptive]
  for label, config in runs:
    calc = SpecialFlowCalculator([Body(MS)], order=2)
    p = Particle()
    p.pos = np.array([-dis, b])
    calc.initPW(p, np.array([C, 0.0]))
    n, t0 = 0, time.time()
    for dt in calc.steps(p, config, 2*dis/C):
      calc.move(p, dt)
      n += 1
    bend = math.atan2(-p.w[1], p.w[0])   #from w, light relative to space; towards the sun is -y
    log.print('  %-28s %9d %8.1f %16.7f' % (label, n, time.time() - t0, bend/predicted))
  log.print()


if __name__ == '__main__':
  log = Log('compareStepSize', True, False)
  log.print('fixed against adaptive steps, second-order SpecialFlowCalculator')
  log.print()
  orbitTable(log, '1. Mercury at 1/10 scale, 4 orbits', 10, 4, (1000, 2500, 25000), (0.01, 0.003, 0.001, 0.0003))
  orbitTable(log, '2. close orbit, 1/100,000 scale, 6 orbits', 1e5, 6, (1000, 5000, 50000), (0.01, 0.003, 0.001, 0.0003))
  light(log, (1.0, 0.1), (0.01, 0.001, 0.0001))
  log.close()
