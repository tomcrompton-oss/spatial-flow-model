"""
the bodies moved by the carried flow (engine/carried.py CarriedBodies: each body a test particle in the carried flow
of the others, its own left out), flat space or space curved across the flow relative to its body:

  binary     two bodies of 2 solar masses in all, a = 1e8 m, e = 0.3, for 12 orbits (studies/binary_pulsar.py's): the
             periastron advance against GR's 3 (GMn)^(2/3)/(c^2 (1 - e^2)) per 2 pi, exact for any mass ratio, taken
             to zero step from 2000 and 4000 steps an orbit; and the centre of mass's acceleration (GR: none)
  nordtvedt  a pair of 0.01 solar masses each, 1e7 m apart, let fall from rest 1e10 m from the Sun for 40 of its
             orbits, against a single body of their mass at their centre (studies/split_more.py's): how much faster
             the pair falls, in units of g E/Mc^2 - Nordtvedt's eta (GR 0, lunar laser ranging 10^-4). the carried
             flow's tides are Newton's only approximately, so both are run at c and at c x 1000 and the difference
             taken (the Sun held still)

run: python3 studies/carried_bodies.py [test ...] [--flat | --curved]     (default both tests, both spaces; prints,
     and writes logs/modelChecks/carriedBodies_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.logger import LOG_DIR
from engine.constants import *

MTOTAL, A, E, ORBITS, STEPS = 2*MS, 1e8, 0.3, 12, 2000
RATIOS = (1.0, 0.1, 0.01)


def setC(scale):
  """c times scale, everywhere it is used (in this process: a pool's workers set it for each job). from c itself,
  not the module's current value, so it doesn't compound from one job to the next"""
  c = 299792458.0
  for name in list(sys.modules):
    m = sys.modules[name]
    if (name.startswith('engine.') or name == '__main__') and hasattr(m, 'C'):
      m.C = c*scale
  globals()['C'] = c*scale


def binaryRun(job):
  ratio, curved, steps = job
  from engine.carried import CarriedBodies
  setC(1.0)
  m1 = MTOTAL/(1 + ratio)
  m2 = MTOTAL - m1
  rp = A*(1 - E)
  vrel = math.sqrt(G*MTOTAL*(1 + E)/rp)
  sim = CarriedBodies([m1, m2], [[m2/MTOTAL*rp, 0.0], [-m1/MTOTAL*rp, 0.0]],
                      [[0.0, m2/MTOTAL*vrel], [0.0, -m1/MTOTAL*vrel]], transverse='source' if curved else False)
  period = 2*math.pi*math.sqrt(A**3/(G*MTOTAL))
  dt = period/steps
  seps, centre, times = [], [], []
  while sim.t < (ORBITS + 0.5)*period:
    sim.step(dt)
    x = sim.places()
    rel = x[0] - x[1]
    seps.append((sim.t, math.sqrt(rel @ rel), math.atan2(rel[1], rel[0])))
    centre.append((m1*x[0] + m2*x[1])/MTOTAL)
    times.append(sim.t)
  peri = []
  for i in range(1, len(seps) - 1):
    if seps[i][1] < seps[i - 1][1] and seps[i][1] <= seps[i + 1][1]:
      (t0, r0, a0), (t1, r1, a1), (t2, r2, a2) = seps[i - 1], seps[i], seps[i + 1]
      f = 0.5*(r0 - r2)/(r0 - 2*r1 + r2)
      da = math.remainder(a2 - a0, 2*math.pi)/2
      peri.append((t1 + f*dt, a1 + f*da))
  n = np.arange(len(peri))
  k = np.polyfit(n, np.unwrap([p[1] for p in peri]), 1)[0]
  P = np.polyfit(n, [p[0] for p in peri], 1)[0]
  accel = 2*np.polyfit(np.array(times), np.array(centre), 2)[0]
  return job, (k, P, accel)


def binary(pool, spaces):
  lines = ['binary: 2 solar masses in all, a = %.0e m, e = %.1f, %d orbits; the periastron advance against GR\'s'
           ' (exact for any mass ratio), to zero step from %d and %d steps an orbit; the centre of mass\'s'
           ' acceleration (GR none)' % (A, E, ORBITS, STEPS, 2*STEPS)]
  found = dict(pool.map(binaryRun, [(r, c, s) for c in spaces for r in RATIOS for s in (STEPS, 2*STEPS)]))
  for c in spaces:
    for r in RATIOS:
      (k1, P1, _), (k2, P2, acc) = found[(r, c, STEPS)], found[(r, c, 2*STEPS)]
      k, P = (4*k2 - k1)/3, (4*P2 - P1)/3
      gr = 3*(G*MTOTAL*2*math.pi/P)**(2/3)/(C*C*(1 - E*E))*2*math.pi
      lines.append('  %-7s m2/m1 %-5g advance / GR\'s %.5f (steps: %.5f, %.5f)   centre of mass accelerating at %.3g m/s^2'
                   % ('curved' if c else 'flat', r, k/gr, k1/gr, k2/gr, math.sqrt(acc @ acc)))
  return lines


def fallRun(job):
  """the centre of mass of the movers (the pair, or the single body) after T, the Sun a body too"""
  which, curved, dt, scale = job
  from engine.carried import CarriedBodies
  setC(scale)
  D, m, r = 1e10, 0.01*MS, 1e7
  vorb = math.sqrt(G*2*m/r)/2
  centre = np.array([D, 0.0])
  from engine.flow import Body
  if which == 'pair':
    masses, xs, vs = [m, m], [centre + [0.0, r/2], centre - [0.0, r/2]], [[vorb, 0.0], [-vorb, 0.0]]
  else:
    masses, xs, vs = [2*m], [centre], [[0.0, 0.0]]
  #the Sun held still (as studies/split_more.py): moved, it would sit in the pair's flow 1e10 m out, where one of the
  #pair's rivers with the other's tide is no flow at all (the tide's expansion about one of them, at 1000 times their
  #separation)
  sim = CarriedBodies(masses, xs, vs, transverse='source' if curved else False, fixed=[Body(MS)])
  P = 2*math.pi*r/(2*vorb)
  T = 40*P
  while sim.t < T - 1e-9:
    sim.step(min(dt, T - sim.t))
  x = sim.places()
  return job, sum(mi*xi for mi, xi in zip(masses, x))/sum(masses)


def nordtvedt(pool, spaces):
  D, m, r = 1e10, 0.01*MS, 1e7
  vorb = math.sqrt(G*2*m/r)/2
  P = 2*math.pi*r/(2*vorb)
  T = 40*P
  binding = G*m*m/(2*r)/(2*m*C*C)
  g = G*MS/D**2
  lines = ['nordtvedt: a pair of 0.01 solar masses each, %.0e m apart (E/Mc^2 = %.2e), let fall from rest %.0e m from'
           ' the Sun for 40 of its orbits, against a single body of their mass; less the same at c x 1000' % (r, binding, D)]
  dts = (P/200, P/400)
  found = dict(pool.map(fallRun, [(w, c, dt, s) for c in spaces for w in ('pair', 'single') for dt in dts
                                  for s in (1.0, 1e3)]))
  for c in spaces:
    acc = {}
    for dt in dts:
      gap = {s: found[('pair', c, dt, s)] - found[('single', c, dt, s)] for s in (1.0, 1e3)}
      acc[dt] = 2*(gap[1.0] - gap[1e3])/T**2
    a = (4*acc[dts[1]] - acc[dts[0]])/3
    eta = a[0]/(g*binding)   #falling faster towards the Sun (-x) is eta < 0... as split_more: eta = -faster
    lines.append('  %-7s the pair falls faster by %+.3e m/s^2 (steps: %+.3e, %+.3e): eta = %+.3f (GR 0)'
                 % ('curved' if c else 'flat', -a[0], -acc[dts[0]][0], -acc[dts[1]][0], eta))
  return lines


TESTS = {'binary': binary, 'nordtvedt': nordtvedt}


def main():
  args = [a for a in sys.argv[1:] if not a.startswith('--')]
  spaces = [False] if '--flat' in sys.argv else [True] if '--curved' in sys.argv else [False, True]
  names = args or list(TESTS)
  folder = os.path.join(LOG_DIR, 'modelChecks', 'carriedBodies_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = []
  with Pool(8) as pool:
    for name in names:
      out = TESTS[name](pool, spaces)
      print('\n'.join(out), flush=True)
      lines += out
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
