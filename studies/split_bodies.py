"""
the bodies taken one at a time (engine/split.py): each body's own one-body flow, its changes to a particle applied one
after the other. the tests the other rules had (studies/multi_body_rules.py, multi_body_clocks.py, multi_body_pn.py),
each run in the split model:

  one       one body: the split model against the flow model - an orbit round the Earth, light past the Sun
  newton    g from a particle let go from rest, the Sun 1 AU away: at the Earth's surface and the Moon's distance;
            and the Earth moving at 29.8 km/s, the Sun at rest
  clocks    over a day, a clock on the equator and one in GPS orbit, the Sun at rest 1 AU away: the model's rate in
            GR's static time (dT/dt = 1 + v . sum u_k/c^2) less GR's; and light pulses from a clock at noon to one at
            dusk, against GR's ratio of their rates
  matter    the step's own first-order term: a particle at rest at the Moon's distance, against Newton, by D (if it
            changes with D it moves the Moon against the Earth); and what the interval's own paths (geodesics) would give
  jupiter   light past Jupiter, the Sun 5.2 AU away: the bending with both less each alone (GR: 0 to first order)
  lunar     radar from the Earth's surface to a mirror at the Moon's distance, by the mirror's angle from the Sun (D),
            the round trip less the Earth's alone (as multi_body_pn.py's lunar, with the split model's light) - along
            the straight line, and checked by light run in the model. the mirror sits on a circle in the model's
            coordinates (the bodies are at rest, so nothing orbits); the matter section shows the steps would not move
            the Moon off it
the light tests run with each light rule (engine/split.py: 'interval' and 'static')

writes logs/multiBody/splitBodies_<datetime>/summary.log

run: python3 studies/split_bodies.py
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, SpecialFlowCalculator, NewtonianCalculator, Particle
from engine.split import SplitFlowCalculator
from engine.logger import LOG_DIR
from engine.constants import *
from multi_body_rules import released, SUN_EARTH, DMOON
from multi_body_clocks import ground, gps, potential, pulse, SIDEREAL_DAY
from multi_body_pn import radar, NODES, WEIGHTS, MJ, RJ, DJ

UAS = 180/math.pi*3600e6


def one():
  lines = ['one: one body, the split model against the flow model']
  ends = []
  for cls in (SpecialFlowCalculator, SplitFlowCalculator):
    calc = cls([Body(ME)])
    p = Particle()
    p.pos = np.array([7e6, 0.0])
    calc.initPV(p, np.array([0.0, 8000.0]))
    for _ in range(20000):
      calc.move(p, 0.5)
    ends.append((p.pos, p.pt))
  lines.append('  an orbit round the Earth, 10,000 s: the positions differ by %.1e m, the proper times by %.1e s'
               % (np.linalg.norm(ends[0][0] - ends[1][0]), abs(ends[0][1] - ends[1][1])))
  b = 2*6.957e8
  sun = [Body(MS, DJ - b, 0.0)]
  bends = [bend(SpecialFlowCalculator(sun), 0.0)] + [bend(SplitFlowCalculator(sun, l), 0.0) for l in ('interval', 'static')]
  lines.append('  light past the Sun at 2 R_sun: the flow model %.6f, split with each light rule %.6f and %.6f arcsec'
               ' (GR 4GM/bc^2: %.6f)' % tuple([x*UAS/1e6 for x in bends] + [4*G*MS/(b*C*C)*UAS/1e6]))
  return lines


def newton():
  lines = ['newton: g from a particle let go from rest for 0.01 s, against Newton\'s, the Sun 1 AU to the left']
  worst = {}
  for title, pos in (('surface, facing the Sun', (-REARTH, 0.0)), ('surface, at the side', (0.0, REARTH)),
                     ('surface, away from the Sun', (REARTH, 0.0)), ('the Moon\'s distance, at the side', (0.0, DMOON)),
                     ('the Moon\'s distance, away', (DMOON, 0.0))):
    g = released(SplitFlowCalculator(SUN_EARTH), pos)
    n = NewtonianCalculator(SUN_EARTH).gravity(np.array(pos))
    worst[title] = np.linalg.norm(g - n)
    lines.append('  %-34s error %.1e m/s^2 (g %.4g)' % (title, worst[title], np.linalg.norm(n)))
  #the Earth moving up at its orbital speed, the Sun at rest: g in the Earth's frame
  moving = [Body(MS, -AU, 0.0), Body(ME, velocity=(0.0, 29.8e3))]
  for title, pos in (('moving Earth, surface facing the Sun', (-REARTH, 0.0)), ('moving Earth, surface ahead', (0.0, REARTH))):
    p = Particle()
    p.pos = np.array(pos)
    calc = SplitFlowCalculator(moving)
    calc.initPV(p, np.array([0.0, 29.8e3]))
    for _ in range(100):
      calc.move(p, 1e-4)
    g = (p.v - np.array([0.0, 29.8e3]))/0.01
    n = NewtonianCalculator(SUN_EARTH).gravity(np.array(pos))
    worst[title] = np.linalg.norm(g - n)
    lines.append('  %-34s error %.1e m/s^2' % (title, worst[title]))
  return lines, worst


def clockResiduals(calc, clock):
  """over a day: the model's rate in GR's static time less GR's, steady part out; and the time kept, as in
  multi_body_clocks.residuals"""
  ts = np.linspace(0.0, 86400.0, 2001)
  diff = []
  for t in ts:
    x, v = clock(t)
    model = calc.rate(x, v)/(1 + v @ calc.flow(x)/C**2)
    diff.append(model - (1 - (potential(x) + (v @ v)/2)/C**2))
  diff = np.array(diff) - np.mean(diff)
  kept = np.concatenate([[0.0], np.cumsum((diff[1:] + diff[:-1])/2*np.diff(ts))])
  kept = kept - np.polyval(np.polyfit(ts, kept, 1), ts)
  return (diff.max() - diff.min())/2, (kept.max() - kept.min())/2


def clocks():
  lines = ['clocks: over a day, the rate in GR\'s static time less GR\'s (steady part out), the Sun at rest 1 AU away']
  calc = SplitFlowCalculator(SUN_EARTH)
  found = {}
  for title, clock in (('equator', ground), ('GPS', gps)):
    swing, kept = clockResiduals(calc, clock)
    found[title] = swing
    lines.append('  %-8s rate swing %.1e, time swing %.1e s' % (title, swing, kept))
  noon, dusk = ground(0.0)[0], ground(SIDEREAL_DAY/4)[0]
  gr = (1 - potential(dusk)/C**2)/(1 - potential(noon)/C**2) - 1
  for light in ('interval', 'static'):
    calc = SplitFlowCalculator(SUN_EARTH, light)
    t1, t2 = pulse(calc, noon, dusk, 0.0), pulse(calc, noon, dusk, 1.0)
    rate = lambda x: calc.rate(x, np.array([0.0, 0.0]))
    ratio = (t2 - t1)*rate(dusk)/rate(noon) - 1
    found['signals ' + light] = ratio - gr
    lines.append('  light rule %-10r pulses 1 s apart from a clock at noon to one at dusk: the second counts %.4e'
                 ' (GR %.4e; %+.1e)' % (light, ratio, gr, ratio - gr))
  return lines, found


def bend(calc, b, half=10*AU, fraction=0.002):
  """light leaving (DJ + b, -half) straight up, run to y = +half: its turn (radians, towards -x positive)"""
  p = Particle()
  p.pos = np.array([DJ + b, -half])
  calc.initLight(p, np.array([0.0, 1.0])) if isinstance(calc, SplitFlowCalculator) else None
  if not isinstance(calc, SplitFlowCalculator):
    u = calc.flow(p.pos)
    calc.initPV(p, np.array([0.0, u[1] + math.sqrt(C*C - u[0]**2)]))
  while p.pos[1] < half:
    calc.move(p, calc.stepSize(p, fraction, 0.01*AU/C))
  return math.atan2(-p.v[0], p.v[1])


def jupiter(light):
  lines = ['jupiter, light rule %r: light passing Jupiter on the side away from the Sun (5.2 AU off), 10 AU either side: the bending'
           ' with both, less each alone (GR: 0 to first order in G)' % light,
           '  %10s %16s %16s %16s' % ('b (R_J)', 'Jupiter (uas)', 'both - each', 'of Jupiter\'s')]
  sun, jup = Body(MS, 0.0, 0.0), Body(MJ, DJ, 0.0)
  found = {}
  for radii in (1, 10, 100, 1000):
    b = radii*RJ
    both = bend(SplitFlowCalculator([sun, jup], light), b)
    s = bend(SplitFlowCalculator([sun], light), b)
    j = bend(SplitFlowCalculator([jup], light), b)
    found[radii] = (both - s - j)*UAS
    lines.append('  %10d %16.2f %16.3f %15.2f%%' % (radii, j*UAS, found[radii], (both - s - j)/j*100))
  return lines, found


def roundTrip(calc, a, b, pieces=400):
  """light's round trip a -> b -> a along the straight line, in the model's time: 1/s(n) + 1/s(-n) along it"""
  span = np.linalg.norm(b - a)
  n = (b - a)/span
  edges = np.concatenate([[0.0], np.geomspace(1.0, span, pieces)])
  total = 0.0
  for lo, hi in zip(edges[:-1], edges[1:]):
    for x, wt in zip(NODES, WEIGHTS):
      pos = a + ((lo + hi)/2 + (hi - lo)/2*x)*n
      total += wt*(hi - lo)/2*(1/calc.lightSpeed(pos, n) + 1/calc.lightSpeed(pos, -n))
  return total


def stepAccel(calc, x, v, h=2.0):
  """the step's acceleration at x, v: centred, a step forward and one back"""
  ends = []
  for dt in (h, -h):
    p = Particle()
    p.pos = x.copy()
    calc.initPV(p, v.copy())
    calc.move(p, dt)
    ends.append(p.v)
  return (ends[0] - ends[1])/(2*h)


def jacobian(b, x):
  """d u_i/d x_j of body b's flow at x"""
  r = x - b.pos
  d = np.linalg.norm(r)
  n, s = r/d, math.sqrt(2*b.GM/d)
  return s/(2*d)*np.outer(n, n) - s*(np.eye(2) - np.outer(n, n))/d


def geodesicAccel(calc, x, v):
  """
  the acceleration on the interval's own paths, bodies at rest: from L = -c sqrt(Q), Q = c^2 - v^2 + 2 v . U - S,
  U = sum u_k, S = sum u_k^2
  """
  us = [calc.bodyFlow(b, x) for b in calc.bodies]
  Js = [jacobian(b, x) for b in calc.bodies]
  U, S = sum(us), sum(u @ u for u in us)
  Q = C*C - v @ v + 2*v @ U - S
  w = v - U
  vU = sum(J @ v for J in Js)
  rhs = vU - sum(J.T @ v for J in Js) + sum(J.T @ u for J, u in zip(Js, us)) \
        + w*(2*v @ vU - sum(2*u @ (J @ v) for J, u in zip(Js, us)))/(2*Q)
  return np.linalg.solve(np.eye(2) + np.outer(w, w)/Q, rhs)


def matter():
  lines = ['matter: a particle at rest at the Moon\'s distance, the Sun 1 AU to the left: the acceleration less Newton\'s,'
           ' by D - the model\'s step, and the interval\'s own paths',
           '  %8s %26s %26s' % ('D (deg)', 'step (m/s^2)', 'interval\'s paths (m/s^2)')]
  calc = SplitFlowCalculator(SUN_EARTH)
  found = []
  for D in (0, 90, 180, 270):
    x = DMOON*np.array([-math.cos(math.radians(D)), math.sin(math.radians(D))])
    v = np.array([0.0, 0.0])
    n = NewtonianCalculator(SUN_EARTH).gravity(x)
    step, path = stepAccel(calc, x, v) - n, geodesicAccel(calc, x, v) - n
    found.append((step, path))
    lines.append('  %8d %26s %26s' % (D, np.array2string(step, precision=3), np.array2string(path, precision=3)))
  spread = lambda k: (max(f[k][0] for f in found) - min(f[k][0] for f in found))/2
  lines.append('  towards the Sun, half the spread by D: the step %.1e, the interval\'s paths %.1e m/s^2 (the Moon\'s'
               ' orbit moves by about that over omega^2 = %.1e: %.2f m and %.1f m)'
               % (spread(0), spread(1), (2*math.pi/(27.32*DAY))**2, spread(0)/(2*math.pi/(27.32*DAY))**2,
                  spread(1)/(2*math.pi/(27.32*DAY))**2))
  return lines, {'step': spread(0), 'paths': spread(1)}


def lunar(light):
  lines = ['lunar, light rule %r: radar from the Earth\'s surface to a mirror at the Moon\'s distance, the Sun 1 AU away, by the'
           ' mirror\'s angle from the Sun (D): the round trip at the Earth\'s clock less the Earth\'s alone, as a range' % light]
  alone = SplitFlowCalculator([Body(ME)], light)
  rest = np.array([0.0, 0.0])
  def extra(D, calc):
    out = np.array([-math.cos(math.radians(D)), math.sin(math.radians(D))])
    a, b = REARTH*out, DMOON*out
    return C*(roundTrip(calc, a, b)*calc.rate(a, rest) - roundTrip(alone, a, b)*alone.rate(a, rest))/2
  calc = SplitFlowCalculator(SUN_EARTH, light)
  Ds = np.radians(np.arange(0, 360, 10))
  ms = np.array([extra(math.degrees(D), calc) for D in Ds])
  cos1, cos2 = 2*np.mean(ms*np.cos(Ds)), 2*np.mean(ms*np.cos(2*Ds))
  lines.append('  mean %.3f m; its cos D part %.4f m, its cos 2D part %.4f m' % (ms.mean(), cos1, cos2))
  uS = math.sqrt(2*G*MS/AU)
  lines.append('  expected: cos D from the cross term (n . u_S)(n . u_E)/c^2 along the way, u_S int u_E dr/c^2 = %.4f m;'
               ' cos 2D from (n . u_S)^2/2c^2, D_moon u_S^2/4c^2 = %.4f m'
               % (uS*2*math.sqrt(2*G*ME)*(math.sqrt(DMOON) - math.sqrt(REARTH))/C**2, DMOON*uS*uS/(4*C*C)))
  for D in (0, 90):
    out = np.array([-math.cos(math.radians(D)), math.sin(math.radians(D))])
    a, b = REARTH*out, DMOON*out
    run = [radar(c, a, b) for c in (calc, alone)]
    metres = C*(run[0]*calc.rate(a, rest) - run[1]*alone.rate(a, rest))/2
    lines.append('  check, D = %d: light run in the model %.4f m, the straight line %.4f m' % (D, metres, extra(D, calc)))
  lines.append('  lunar laser ranging fits (2.8 +- 4.1) mm cos D (Williams, Turyshev and Boggs 2004)')
  return lines, {'cosD': cos1, 'cos2D': cos2}


def main():
  folder = os.path.join(LOG_DIR, 'multiBody', 'splitBodies_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = []
  sections = [one, newton, matter, clocks] + [lambda l=l: jupiter(l) for l in ('interval', 'static')] \
             + [lambda l=l: lunar(l) for l in ('interval', 'static')]
  for section in sections:
    out = section()
    lines += (out[0] if isinstance(out, tuple) else out) + ['']
    print('\n'.join(out[0] if isinstance(out, tuple) else out), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
