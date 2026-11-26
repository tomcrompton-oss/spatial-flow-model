"""
a hunch, not for the docs: light sent straight out from just outside a black hole's horizon, in the flow model. space
falls in at u = c sqrt(rs/r), so light moving out at c through it gains on the hole at c - u, which near the horizon
is about |du/dr| (r - rs): the light's distance from the horizon grows exponentially, at the rate |du/dr| at the
horizon, c/(2 rs) - the surface gravity over c. any wave sent out from there is stretched the same way, and that
exponential stretching is what makes Hawking radiation thermal, at k T = hbar |du/dr| / (2 pi)

rays leave from rs (1 + eps), eps = 1e-1 to 1e-6, and are followed to 3 rs by the flow model (SpecialFlowCalculator,
second order), against exact general relativity's outward light, t = (2 rs/c)[s^2/2 + s + ln(s - 1)], s = sqrt(r/rs).
measured: the growth rate of ln(r - rs) while the ray is within 1% of rs of the horizon (a straight-line fit), against
c/(2 rs); and the temperature that rate gives, against Hawking's, for three holes (the rate goes as 1/M, so the run
is done once, in units of rs/c, and scaled)

writes logs/horizonPeeling/horizonPeeling_<datetime>/: a csv per ray (t in rs/c, log10 of the distance from the
horizon in rs, and exact GR's time to there), horizonPeeling.full.json (that distance against t) and summary.log

run: python3 studies/horizon_peeling.py
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import Body, SpecialFlowCalculator, Particle
from engine.logger import LOG_DIR
from engine.constants import *
from engine.exact import schwarzschildRadius
from two_body_escapes import writeViewerFiles

HBAR = 1.054571817e-34
KB = 1.380649e-23
MASS = MS                         #the run's hole; the results scale with rs
RS = schwarzschildRadius(MASS)
EPS = (1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6)
END = 3*RS
STEP = 2e-4                       #each step moves this fraction of the ray's distance from the horizon
NEAR = 1e-3                       #the fit uses the ray while it is within this many rs of the horizon
HOLES = (('supermassive (4e6 solar masses)', 4e6*MS), ('the Sun\'s mass', MS), ('microscopic (5e11 kg)', 5e11))
COLOURS = ('#b5d4f4', '#85b7eb', '#5ea0e6', '#378add', '#185fa5', '#0c447c')   #from 1e-1 (lightest) to 1e-6 rs out


def exactTime(r0, r):
  """general relativity's outward light from r0 to r (the flow model's time, Gullstrand-Painleve), in s"""
  F = lambda r: (lambda s: s*s/2 + s + math.log(s - 1))(math.sqrt(r/RS))
  return 2*RS/C*(F(r) - F(r0))


def ray(eps):
  calc = SpecialFlowCalculator([Body(MASS)], 2)
  p = Particle()
  p.pos = np.array([RS*(1 + eps), 0.0])
  calc.initPW(p, np.array([C, 0.0]))
  rows = []
  while p.pos[0] < END:
    gap = p.pos[0] - RS
    rows.append((p.t*C/RS, math.log(gap/RS), math.log((p.pos[0] - RS)/RS), p.pt))
    dt = STEP*gap/max(p.v[0], 1e-30)
    if p.pos[0] + p.v[0]*dt > END:
      dt = (END - p.pos[0])/p.v[0]
    calc.move(p, dt)
  rows.append((p.t*C/RS, math.log((p.pos[0] - RS)/RS), 0.0, p.pt))
  return rows, p.t


def main():
  folder = os.path.join(LOG_DIR, 'horizonPeeling', 'horizonPeeling_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  expected = 0.5                  #c/(2 rs), in units of c/rs
  lines = ['light straight out from just outside the horizon of a %g kg hole (rs %.4g m, rs/c %.4g s), to 3 rs'
           % (MASS, RS, RS/C), '  expected growth of ln(r - rs) near the horizon: |du/dr| = c/(2 rs) = %.4f c/rs' % expected, '']
  made, rates = [], []
  for k, eps in enumerate(EPS):
    rows, t = ray(eps)
    exact = exactTime(RS*(1 + eps), END)
    near = [(tt, lg) for tt, lg, _, _ in rows if lg < math.log(NEAR)]
    slope = np.polyfit([a for a, _ in near], [b for _, b in near], 1)[0] if len(near) > 10 else float('nan')
    rates.append(slope)
    lines.append('  from rs (1 + %g): reaches 3 rs at %.6f rs/c (exact GR %.6f, - 1 %.1e); ln(r - rs) grows at %.6f c/rs'
                 ' while within %g rs (- %.4f: %.1e)' % (eps, t*C/RS, exact*C/RS, t/exact - 1, slope, NEAR, expected,
                                                         slope/expected - 1))
    path = os.path.join(folder, 'ray_eps%g.csv' % eps)
    with open(path, 'w') as f:
      f.write('t (rs/c),log10 distance from the horizon (rs),exact GR t (rs/c)\n')
      for tt, lg, _, _ in rows[::max(1, len(rows)//400)] + [rows[-1]]:
        r = RS*(1 + math.exp(lg))
        f.write('%.8g,%.8g,%.8g\n' % (tt, lg/math.log(10), exactTime(RS*(1 + eps), r)*C/RS if r > RS*(1 + eps) else 0.0))
    with open(path[:-4] + '.log', 'w') as f:
      f.write('light straight out from rs (1 + %g), to 3 rs: t in rs/c, ln of the distance from the horizon in rs\n' % eps)
    made.append((path, COLOURS[k % len(COLOURS)], 'solid'))
  rate = float(np.nanmean(rates))      #the rays that start inside NEAR
  lines += ['', '  the growth rate, all rays: %.6f c/rs (expected %.4f)' % (rate, expected), '',
            'the temperature that rate gives, k T = hbar (rate)/(2 pi), against Hawking\'s, hbar c^3/(8 pi G M k):']
  for name, mass in HOLES:
    rs = schwarzschildRadius(mass)
    T = HBAR*(rate*C/rs)/(2*math.pi*KB)
    TH = HBAR*C**3/(8*math.pi*G*mass*KB)
    lines.append('  %-32s rate %.4g /s: T %.4g K; Hawking %.4g K (- 1 %.1e)' % (name, rate*C/rs, T, TH, T/TH - 1))
  X, Y = 't (rs/c)', 'log10 distance from the horizon (rs)'
  writeViewerFiles(folder, 'horizonPeeling', made, selection=((X, Y),),
                   styles=lambda colour, style='solid': {X + ' / ' + Y: [colour, style, colour]},
                   preferences={'equalAspect': False, 'showBodies': False, 'showSchwarzschild': False, 'showFlow': False,
                                'showPathLegend': False})
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
