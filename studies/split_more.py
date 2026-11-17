"""
four more tests of the split model (engine/split.py, 'static' light, 'freefall' frames):

  jupiter    light past a moving Jupiter (Jupiter alone, moving along the light's way at v): GR's bending is
             4GM/(c^2 b) (1 - v . k/c), k the light's direction - the velocity-dependent part VLBI saw past Jupiter
             (Fomalont & Kopeikin 2003). v up to 0.01 c so the factor shows
  decay      orbital decay: the binary of studies/binary_pulsar.py (equal masses), its period from periastron to
             periastron over the run, against GR's loss to gravitational waves (Peters 1964)
  desitter   de Sitter precession: the Moon (on an orbit of eccentricity 0.12, so its perigee is well defined) round
             the Earth on its orbit round the Sun, for a year, in the model and in GR (studies/lunar_orbit.py's EIH
             equations), from the same start: the turning of the Moon's perigee, model less GR. GR has the Moon's
             orbit turning at 19.2 mas a year more than Newton from falling round the Sun; if the model lacks it the
             difference is that. GR run in a frame turning at the de Sitter rate calibrates it
  nordtvedt  the Nordtvedt effect: a pair of bodies orbiting each other (their binding energy -E) let fall from rest
             towards the Sun, against a single test particle let go at the same place; both run in the model, and
             again with c a thousand times larger to take out Newton's tides. GR: they fall together. Nordtvedt's eta:
             the pair's gravitational mass over its inertial, less 1, is eta U/Mc^2, U = -E its binding energy (so a
             pair falling faster has eta < 0). lunar laser ranging: eta = (-0.2 +- 1.1) x 10^-4

run: python3 studies/split_more.py [test ...]      (default all four; prints, and writes
     logs/multiBody/splitMore_<tests>_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
import engine.split as split
import engine.flow as flow
from engine.flow import Body, Particle
from engine.split import SplitFlowCalculator, Boost
from engine.logger import LOG_DIR
from engine.constants import *
import binary_pulsar as bp
import lunar_orbit as lo
from multi_body_pn import MJ, RJ, DJ

MODEL = ('static', 'freefall')


def jupiter():
  lines = ['jupiter: light past Jupiter alone, 10 R_J off, Jupiter moving at v along the light\'s way; the bending against'
           ' GR\'s 4GM/(c^2 b) (1 - v . k/c)']
  b = 10*RJ
  half = 2*AU
  def bend(v):
    calc = SplitFlowCalculator([Body(MJ, DJ, 0.0, velocity=(0.0, v))], *MODEL)
    p = Particle()
    p.pos = np.array([DJ + b, -half])
    calc.initLight(p, np.array([0.0, 1.0]))
    while p.pos[1] < half:
      calc.move(p, calc.stepSize(p, 0.002, 0.005*AU/C))
    return math.atan2(-p.v[0], p.v[1])
  still = bend(0.0)
  found = {}
  for v in (13.1e3, 0.001*C, -0.001*C, 0.01*C):
    ratio = bend(v)/still
    found[v] = ratio/(1 - v/C)
    lines.append('  v = %+10.4g m/s: bending over Jupiter\'s at rest %.7f; GR\'s 1 - v/c %.7f; model over GR %.7f'
                 % (v, ratio, 1 - v/C, found[v]))
  return lines, found


def decay():
  lines = ['decay: the equal-mass binary of studies/binary_pulsar.py, its period from periastron to periastron over'
           ' %d orbits, against GR\'s loss to gravitational waves' % bp.ORBITS]
  m = bp.MTOTAL/2
  found = {}
  for steps in (bp.STEPS, 2*bp.STEPS):
    peri, centre, times = bp.run(1.0, 'freefall', steps)
    t = np.array([q[0] for q in peri])
    n = np.arange(len(t))
    c2, c1, c0 = np.polyfit(n, t, 2)   #t = c0 + P n + (Pdot P/2) n^2
    P = c1
    found[steps] = 2*c2/P
    lines.append('  %d steps an orbit: period %.4f s, its change %+.3e s/s' % (steps, P, found[steps]))
  e = bp.E
  fe = (1 + 73/24*e*e + 37/96*e**4)/(1 - e*e)**3.5
  gr = -192*math.pi/5*G**(5/3)/C**5*(P/(2*math.pi))**(-5/3)*fe*m*m*bp.MTOTAL**(-1/3)
  lines.append('  GR (Peters): %.3e s/s; the model\'s, extrapolated to zero step, %+.3e s/s'
               % (gr, (4*found[2*bp.STEPS] - found[bp.STEPS])/3))
  found['gr'] = gr
  return lines, found


def lrl(rel, vrel, gm):
  """the direction of the perigee: the Laplace-Runge-Lenz vector's angle"""
  r = np.linalg.norm(rel)
  e = ((vrel @ vrel) - gm/r)*rel/gm - (rel @ vrel)*vrel/gm
  return math.atan2(e[1], e[0]), np.linalg.norm(e)


def desitter(days=365.25, steps=(10.0, 20.0)):
  start = (np.array([0.0, -lo.DMOON]), np.array([1080.0, 0.0]))
  lines = ['desitter: the Moon (eccentricity about 0.12) round the Earth on its orbit, for %.0f days: the direction of'
           ' its perigee, the model less GR, as a rate' % days]
  lo.SPAN = days*DAY - DAY
  samples = np.arange(DAY, days*DAY - DAY, DAY/4)
  gm = G*ME
  def angles(track, setup):
    out = []
    for t in samples:
      x = track.at(t)
      h = 1.0
      v = (track.at(t + h) - track.at(t - h))/(2*h)
      out.append(lrl(x - setup.earth(t), v - setup.earthV(t), gm)[0])
    return np.unwrap(out)
  model = lo.Setup(True, False, start=start)
  runs = {}
  for dt in steps:
    calc, moon = lo.modelRun(model, dt, 'freefall')
    runs[dt] = angles(moon, model)
  modelAngles = (4*runs[steps[0]] - runs[steps[1]])/3   #steps[1] = 2 steps[0]
  gr = lo.Setup(True, True, start=start)
  dS = gr.deSitter()
  grAngles = angles(lo.grRun(gr, start), gr)
  turned = lo.Setup(True, True, turn=dS, start=start)
  turnedAngles = angles(lo.grRun(turned, start), turned)
  year = 365.25*DAY
  rate = lambda a: np.polyfit(samples, a, 1)[0]*year
  found = {'model - GR': rate(modelAngles - grAngles), 'turned - GR': rate(turnedAngles - grAngles),
           'step': rate(runs[steps[0]] - runs[steps[1]]), 'perigee': rate(grAngles)}
  mas = 180/math.pi*3600e3
  lines.append('  GR: the perigee turns %.3f rad a year (the Sun\'s tide, mostly); de Sitter\'s part 19.2 mas a year'
               % found['perigee'])
  lines.append('  the model less GR: %+.2f mas a year (its %g s and %g s steps differ by %.2f mas a year before'
               ' extrapolation)' % (found['model - GR']*mas, steps[0], steps[1], found['step']*mas))
  lines.append('  calibration: GR in a frame turning at the de Sitter rate, less GR: %+.2f mas a year'
               % (found['turned - GR']*mas))
  return lines, found


def fall(bodies, starts, T, dt, scale=1.0):
  """the bodies of starts [(mass, x, v)] moving in the Sun's flow and each other's, for T; the centre of mass at the
  end. bodies: the Sun (fixed)"""
  split.C = flow.C = C*scale
  try:
    movers = [bp.MovingBody(m, x, v) for m, x, v in starts]
    allBodies = bodies + movers
    calcs = []
    for b in movers:
      calc = SplitFlowCalculator(allBodies, *MODEL)
      calc.skip = b
      calcs.append(calc)
    t = 0.0
    while t < T - 1e-9:
      h = min(dt, T - t)
      new = []
      for b, calc in zip(movers, calcs):
        p = Particle()
        p.pos, p.t = b.x0.copy(), t
        calc.initPV(p, b.v0.copy())
        calc.move(p, h)
        new.append((p.pos, p.v))
      for b, (x, v) in zip(movers, new):
        b.set(t + h, x, v, (v - b.v0)/h)
      t += h
    M = sum(b.mass for b in movers)
    return sum(b.mass*b.x0 for b in movers)/M
  finally:
    split.C = flow.C = C


def nordtvedt():
  D = 1e10                          #from the Sun
  m = 0.01*MS                       #each of the pair
  r = 1e7                           #the pair's separation, on a circle
  vorb = math.sqrt(G*2*m/r)/2       #each one's speed round their centre
  P = 2*math.pi*r/(2*vorb)
  T = 40*P
  steps = 400                       #an orbit of the pair
  sun = [Body(MS)]
  centre = np.array([D, 0.0])
  pair = [(m, centre + [0.0, r/2], [vorb, 0.0]), (m, centre - [0.0, r/2], [-vorb, 0.0])]
  single = [(2*m, centre, [0.0, 0.0])]
  binding = G*m*m/(2*r)/(2*m*C*C)   #E/Mc^2 for the pair (kinetic + potential = -G m m/2r)
  g = G*MS/D**2
  lines = ['nordtvedt: a pair of 0.01 solar masses each, %.0e m apart (E/Mc^2 = %.2e), let fall from rest %.0e m from'
           ' the Sun for %.0f of its orbits, against a single body of the same mass let go at its centre; less the'
           ' same with c x 1000 (Newton\'s tides)' % (r, binding, D, T/P)]
  found = {}
  for dt in (P/steps, P/(2*steps)):
    gap = {}
    for scale in (1.0, 1e3):
      gap[scale] = fall(sun, pair, T, dt, scale) - fall(sun, single, T, dt, scale)
    rel = gap[1.0] - gap[1e3]
    accel = 2*rel/T**2
    found[dt] = accel
    lines.append('  %d steps an orbit: the pair less the single body, less Newton\'s: %s m after %.0f s; as an'
                 ' acceleration %s m/s^2' % (round(P/dt), np.array2string(rel, precision=3), T,
                                            np.array2string(accel, precision=3)))
  a = (4*found[P/(2*steps)] - found[P/steps])/3
  faster = -a[0]/(g*binding)   #towards the Sun is -x: how much faster the pair falls, in units of g E/Mc^2
  lines.append('  towards the Sun, extrapolated: the pair falls faster by %+.3e m/s^2 = %+.3f g E/Mc^2 (g = %.3f'
               ' m/s^2), so Nordtvedt\'s eta = %+.3f (GR 0; lunar laser ranging (-0.2 +- 1.1) x 10^-4)'
               % (-a[0], faster, g, -faster))
  found['eta'] = -faster
  return lines, found


TESTS = {'jupiter': jupiter, 'decay': decay, 'desitter': desitter, 'nordtvedt': nordtvedt}


def main():
  names = sys.argv[1:] or list(TESTS)
  folder = os.path.join(LOG_DIR, 'multiBody', 'splitMore_%s_%s' % ('-'.join(names), datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
  os.makedirs(folder, exist_ok=True)
  lines = []
  for name in names:
    out, _ = TESTS[name]()
    print('\n'.join(out), flush=True)
    lines += out + ['']
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
