"""
the rotating-hole river model (engine/kerr.py's KerrFlowCalculator, second order, adaptive steps) against exact
Kerr, in the hole's equatorial plane (engine/exact.py), for a 4e6 MS hole (all sizes in M = GM/c^2):

1. light bending, passing with the spin and against it, at impact parameters from 100 M in to 12 M, for spins 0 to
   0.99: the bend against Kerr's exact bend at the light's impact parameter L/E, and what leaving the twist out does
2. orbits from 40 M, going round with the spin and against it: the periapsis precession against Kerr's exact
   precession for the orbit's own periapsis and apoapsis, and against a non-rotating hole's

writes logs/kerrComparison/kerrComparison_<datetime>.log

run: python3 studies/kerr_comparison.py      (about 2 minutes)
"""
import math
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, Config
from engine.kerr import KerrFlowCalculator
from engine.logger import Log
from engine.constants import *
from engine.exact import kerrDeflectionExact, kerrImpactParameter, kerrPrecessionExact, grPrecessionExact
from studies.compare_second_order import apsis

MASS = 4e6*MS
FRACTION = 3e-4    #the step fraction for every run
START = 1e4        #light starts and ends this far out (M)


def adaptive(fraction=None):
  config = Config()
  config.dt, config.stepFraction = 1e9, fraction or FRACTION
  return config


def lightBend(spin, b0, twist=1.0, fraction=None, start=START):
  """
  light from (-START, b0) M along +x to x = +START M: passing above (b0 > 0) it goes round clockwise - against a
  positive spin. returns its bend towards the hole and its impact parameter L/E as it starts
  """
  calc = KerrFlowCalculator([Body(MASS, spin=spin)], order=2, twist=twist)
  p = Particle()
  p.pos = np.array([-start*calc.M, b0*calc.M])
  calc.initPW(p, np.array([C, 0.0]))
  b = kerrImpactParameter(p.pos, p.w, p.u, calc.a)
  for dt in calc.steps(p, adaptive(fraction), 2*start*calc.M/C):
    calc.move(p, dt)
  angle = math.atan2(p.w[1], p.w[0])
  return (-angle if b0 > 0 else angle), b


def orbitPrecession(spin, prograde, rStart=40, speed=0.13, orbits=5, twist=1.0, fraction=None):
  """
  an equatorial orbit from rStart M on the +y axis moving across at speed (of c) - round with the spin or against
  it. returns the precession (rad per orbit, in its own direction) at periapsis and at apoapsis, and its mean
  periapsis and apoapsis r (m)
  """
  calc = KerrFlowCalculator([Body(MASS, spin=spin)], order=2, twist=twist)
  a = calc.a
  p = Particle()
  p.pos = np.array([0.0, math.sqrt((rStart*calc.M)**2 + a*a)])   #flat distance R for r = rStart
  calc.initPV(p, np.array([(-1.0 if prograde else 1.0)*speed*C, 0.0]))   #-x from the top is anticlockwise
  last, peris, apos = [], [], []
  turned, prev = 0.0, math.atan2(p.pos[1], p.pos[0])
  while turned < 2*math.pi*(orbits + 0.5):
    calc.move(p, calc.stepSize(p, fraction or FRACTION))
    if not np.all(np.isfinite(p.pos)):
      return None   #it fell in
    angle = math.atan2(p.pos[1], p.pos[0])
    turned += abs((angle - prev + math.pi) % (2*math.pi) - math.pi)
    prev = angle
    last = (last + [(p.t, np.linalg.norm(p.pos), p.pos.copy())])[-3:]
    if len(last) == 3:
      (_, x0, _), (_, x1, _), (_, x2, _) = last
      for found, store in ((x1 < x0 and x1 <= x2, peris), (x1 > x0 and x1 >= x2, apos)):
        if found:
          store.append(apsis([q[0] for q in last], [q[1] for q in last], [q[2] for q in last]))
  sense = 1.0 if p.pos[0]*p.v[1] - p.pos[1]*p.v[0] > 0 else -1.0
  precession = lambda pts: sense*float(np.mean(np.diff(np.unwrap([math.atan2(q[2][1], q[2][0]) for q in pts]))))
  toR = lambda R: math.sqrt(R*R - a*a)   #flat distance R to r
  return precession(peris), precession(apos), toR(np.mean([q[1] for q in peris])), toR(np.mean([q[1] for q in apos]))


def light(log):
  log.print('1. light from %g M to %g M past the hole; positive b goes against the spin' % (START, START))
  log.print()
  log.print('  %6s %8s %14s %16s %18s %8s' % ('spin', 'b0 (M)', 'exact bend', 'vs exact - 1', 'no twist: vs - 1', 'time s'))
  for spin in (0.0, 0.5, 0.9, 0.99):
    for b0 in (100, -100, 30, -30, 12, -12):
      t0 = time.time()
      bend, b = lightBend(spin, b0)
      exact = kerrDeflectionExact(b, MASS, spin)
      without = '%18.3e' % (lightBend(spin, b0, 0.0)[0]/exact - 1) if spin else '%18s' % '-'
      log.print('  %6g %8g %14.8f %16.3e %s %8.1f' % (spin, b0, exact, bend/exact - 1, without, time.time() - t0))
  log.print()


def orbits(log):
  log.print('2. orbits from 40 M at 0.13 c, 5 orbits: precession against exact Kerr for their own apsides')
  log.print()
  log.print('  %6s %-11s %12s %12s %14s %14s %18s %8s' % ('spin', 'direction', 'peri r (M)', 'apo r (M)', 'exact Kerr', 'vs exact - 1',
                                                         'non-rotating hole', 'time s'))
  M = G*MASS/C**2
  for spin in (0.5, 0.9):
    for prograde in (True, False):
      t0 = time.time()
      pp, pa, rp, ra = orbitPrecession(spin, prograde)
      exact = kerrPrecessionExact(rp, ra, MASS, spin, prograde)
      log.print('  %6g %-11s %12.4f %12.4f %14.8f %14.3e %18.8f %8.1f' % (spin, 'with spin' if prograde else 'against', rp/M, ra/M, exact,
                                                                     pp/exact - 1, grPrecessionExact(rp, ra, MASS), time.time() - t0))
  log.print()
  log.print('  without the twist the orbits are different ones (the start is the same, the river not): for spin 0.9')
  for prograde in (True, False):
    result = orbitPrecession(0.9, prograde, twist=0.0)
    if result is None:
      log.print('    %-10s it falls into the hole' % ('with spin' if prograde else 'against'))
    else:
      pp, pa, rp, ra = result
      log.print('    %-10s precession vs exact Kerr for its apsides - 1: %+.3e' % ('with spin' if prograde else 'against',
                                                                               pp/kerrPrecessionExact(rp, ra, MASS, 0.9, prograde) - 1))
  log.print()


if __name__ == '__main__':
  log = Log('kerrComparison', True, False)
  log.print('the rotating-hole river model (KerrFlowCalculator, second order, adaptive steps, fraction %g) against exact Kerr' % FRACTION)
  log.print()
  light(log)
  orbits(log)
  log.close()
