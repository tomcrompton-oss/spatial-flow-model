"""
the flow model (second-order SpecialFlowCalculator, adaptive steps) against exact general relativity
(engine/exact.py), to settle two leftovers:

1. light past the Sun bent by about 4.45e-5 (of 4GM/c^2 b) more than GR, whatever the step: it is u/c at the start
   (4.44e-5 at 10 AU, falling as 1/sqrt(start distance)), because light started b off the axis along it, where the
   flow runs along it, has GR's impact parameter cL/E = b/(1 + u/c). against GR's exact bending at that impact
   parameter the model agrees to parts in 10^7, second-order term included
2. close orbits precessed about 1.5% more than 6 pi GM/c^2 a(1 - e^2): that formula is only GR's leading term (the
   next adds 1.2% at 196 Schwarzschild radii) and a, e were the orbit's nominal ones, not its own. against GR's
   exact precession for the orbit's measured periapsis and apoapsis the model agrees to parts in 10^4, closer as
   the steps get smaller

writes logs/grComparison/grComparison_<datetime>.log

run: python3 studies/gr_comparison.py      (about a minute)
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
from engine.exact import grDeflectionExact, grPrecessionExact, grPrecession, impactParameter, orbitPeriod, schwarzschildRadius
from studies.compare_step_size import orbit
from studies.compare_second_order import precession, PERIHELION

FRACTION = 0.0003   #the step fraction for every run


def adaptive(dt, fraction=FRACTION):
  config = Config()
  config.dt, config.stepFraction = dt, fraction
  return config


def lightBend(start, b):
  """light from (-start, b) along +x to x = +start: its bend (from w) and GR's impact parameter as it starts"""
  calc = SpecialFlowCalculator([Body(MS)], order=2)
  p = Particle()
  p.pos = np.array([-start, b])
  calc.initPW(p, np.array([C, 0.0]))
  bGR = impactParameter(p.pos, p.w, p.u)
  for dt in calc.steps(p, adaptive(1e9), 2*start/C):
    calc.move(p, dt)
  return math.atan2(-p.w[1], p.w[0]), bGR


def light(log):
  log.print('1. light past the Sun, from -D to +D at b off the axis')
  log.print('   bend against GR exact at b, and at the light\'s own impact parameter bGR = cL/E; u/c at the start for scale')
  log.print()
  log.print('  %8s %8s %16s %16s %14s %8s' % ('D (AU)', 'b/RSUN', 'vs GR(b) - 1', 'vs GR(bGR) - 1', 'u(D)/c', 'time s'))
  for b in (RSUN, 0.2*RSUN, 0.025*RSUN):
    for D in (1, 10, 100, 1000):
      t0 = time.time()
      bend, bGR = lightBend(D*AU, b)
      log.print('  %8g %8g %16.4e %16.4e %14.4e %8.1f' % (D, b/RSUN, bend/grDeflectionExact(b) - 1, bend/grDeflectionExact(bGR) - 1,
                                                       math.sqrt(2*G*MS/(D*AU))/C, time.time() - t0))
  log.print()


def orbits(log):
  log.print('2. Mercury\'s orbit shrunk by a scale, 6 orbits: precession against GR exact for the orbit\'s own (mean)')
  log.print('   periapsis and apoapsis, and against the leading term 6 pi GM/c^2 a(1 - e^2) with the nominal a and e')
  log.print()
  log.print('  %8s %8s %14s %14s %16s %16s %8s' % ('scale', 'a/rs', 'peri prec', 'GR exact', 'vs GR exact - 1', 'vs leading - 1', 'time s'))
  e = (MERCURY_MAX - PERIHELION)/(MERCURY_MAX + PERIHELION)
  for scale in (1e3, 1e4, 1e5, 3e5):
    r, v = MERCURY_MAX/scale, MERCURY_SPEED_AT_MAX*math.sqrt(scale)
    a = (MERCURY_MAX + PERIHELION)/2/scale
    period = orbitPeriod(a)
    t0 = time.time()
    peris, apos, n, wall = orbit(r, v, 7.5*period, adaptive(period/20))
    rp, ra = np.mean([d for d, _ in peris]), np.mean([d for d, _ in apos])
    measured, exact = precession(peris), grPrecessionExact(rp, ra)
    log.print('  %8g %8.0f %14.6e %14.6e %16.3e %16.3e %8.1f' % (scale, a/schwarzschildRadius(MS), measured, exact, measured/exact - 1,
                                                          measured/grPrecession(a, e) - 1, time.time() - t0))
  log.print()


if __name__ == '__main__':
  log = Log('grComparison', True, False)
  log.print('the flow model (second order, adaptive steps, fraction %g) against exact general relativity' % FRACTION)
  log.print()
  light(log)
  orbits(log)
  log.close()
