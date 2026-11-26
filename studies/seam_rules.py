"""
where a seam can go, and where the crossing rule works

  placement  the potential flow's seam is where the two bodies' S are equal, S_0 = S_1 + c (engine/two_centre.py
             offsets): the constant c puts it through the saddle, where g is 0. but each region's time T = t + S_k/c^2
             is continuous across the seam for any c, so any c gives a valid slicing. the seam is moved by changing c
             (in units of S at the saddle), and light crossing it is run against GR, as in studies/seam_crossing.py.
             also: where the seam then crosses the line between the bodies

  interface  the crossing rule (MetricCalculator.crossSeam: momentum along the boundary kept, energy kept) away from
             any seam: one body, the model's time (its flow, space curved) inside a boundary and GR's own time
             (harmonic, no flow) outside. the two times differ by S(x)/c^2, so they meet without a jump only on a
             level set of S - a circle round the body. a circle (where they meet, up to a constant) and a straight
             line (where they don't) are tried, light crossing them run against GR

run: python3 studies/seam_rules.py     (a few minutes; prints, and writes logs/modelChecks/seamRules_<datetime>/summary.log)
"""
import math
import os
import sys
import time
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import Body, Particle, SpecialFlowCalculator
from engine.metric import MetricCalculator, FlowSpacetime, PostNewtonian, Spacetime
from engine.logger import LOG_DIR
from engine.constants import MS, C
import seam_crossing as sc

D, HALF = sc.D, sc.HALF
SHIFTS = (-0.3, -0.1, 0.0, 0.1, 0.3)        #c, in units of S at the saddle
RAYS = [('30,000 km off the line', (-HALF, 3e7), (1, 0)), ('100,000 km off', (-HALF, 1e8), (1, 0)),
        ('at 45 degrees', (-HALF/math.sqrt(2), -HALF/math.sqrt(2) + 5e7), (1, 1))]


def shifted(shift):
  calc = SpecialFlowCalculator(sc.BODIES(), 2)
  field = calc.rayField()
  saddle = field.saddle(0, 1)
  field.offsets[1] += shift*field.action(saddle, 0)
  return calc, field


def seamOnAxis(field):
  """where the seam crosses the line between the bodies (x, m from the middle)"""
  lo, hi = -D/2*0.999, D/2*0.999
  for _ in range(60):
    mid = (lo + hi)/2
    if field.region(np.array([mid, 0.0])) == 0:
      lo = mid
    else:
      hi = mid
  return (lo + hi)/2


def placementRun(job):
  shift, start, direction = job
  calc, field = shifted(shift)
  S = FlowSpacetime(calc, transverse='flow')
  return job, light(MetricCalculator(S), start, direction)


def light(calc, start, direction, dt=sc.DT_LIGHT, reach=1.2*HALF, centre=np.zeros(2)):
  p = Particle()
  p.pos = np.array(start, dtype=float)
  calc.initLight(p, np.array(direction, dtype=float)/np.linalg.norm(direction))
  pts, dirs, turns = [p.pos.copy()], [p.v/np.linalg.norm(p.v)], []
  before = calc.sideOf(p)
  started = time.time()
  while np.linalg.norm(p.pos - centre) < reach and len(pts) < 200000 and time.time() - started < 600:
    old = p.v/np.linalg.norm(p.v)
    calc.move(p, dt)
    pts.append(p.pos.copy())
    dirs.append(p.v/np.linalg.norm(p.v))
    if getattr(p, 'region', None) is not None and p.region != before:
      turns.append(math.acos(max(-1.0, min(1.0, old @ dirs[-1]))))
      before = p.region
  return np.array(pts), np.array(dirs), turns, time.time() - started >= 600


class Joined(Spacetime):
  """one body: the model's time (flow, space curved across it) inside the boundary, GR's own (harmonic) outside"""

  def __init__(self, shape, R):
    body = Body(MS, 0.0, 0.0)
    self.bodies = [body]
    self.inner = FlowSpacetime(SpecialFlowCalculator([body], 2), transverse='flow')
    self.outer = PostNewtonian([body])
    self.shape, self.R = shape, R
    self.centre = None

  def region(self, x, t):
    inside = x @ x < self.R**2 if self.shape == 'circle' else x[0] > self.R
    return 0 if inside else 1

  def parts(self, x, t, region):
    if region is None:
      region = self.region(x, t)
    return (self.inner if region == 0 else self.outer).parts(x, t, None)

  def lapseOffset(self, x, t):
    return self.parts(x, t, None)[0]

  def flow(self, x, t, region=None):
    return self.parts(x, t, region)[1]

  def space(self, x, t, region=None):
    S = self.inner if (self.region(x, t) if region is None else region) == 0 else self.outer
    return S.space(x, t, None)


class BoundaryNormal(Joined):
  """the same, with the crossing rule told the boundary's own normal (rather than the flow's jump's direction)"""

  def seamNormal(self, x, t):
    if self.shape == 'circle':
      return x/np.linalg.norm(x)
    return np.array([1.0, 0.0])


INTERFACES = [   #(label, shape, boundary, start, direction)
  ('a circle of radius 100,000 km (the times meet), light passing 50,000 km from the body', 'circle', 1e8,
   (-HALF, 5e7), (1, 0)),
  ('the same circle, light passing 20,000 km from the body', 'circle', 1e8, (-HALF, 2e7), (1, 0)),
  ('a straight line 50,000 km from the body (the times don\'t meet), light crossing it 50,000 km off the axis',
   'line', 5e7, (-HALF, 5e7), (1, 0)),
]


def interfaceRun(job):
  label, shape, R, start, direction, which = job
  if which == 'GR':
    calc = MetricCalculator(PostNewtonian([Body(MS, 0.0, 0.0)]))
  else:
    calc = MetricCalculator((BoundaryNormal if which == 'normal' else Joined)(shape, R))
  return job, light(calc, start, direction)


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'seamRules_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = ['placement: the seam moved by changing the constant between the two bodies\' S (in units of S at the saddle);'
           ' light crossing it, the model with space curved against GR (as studies/seam_crossing.py)']
  _, field = shifted(0.0)
  grRuns = [('GR', 'rule', start, direction, None) for _, start, direction in RAYS]
  with Pool(8) as pool:
    grs = dict(pool.map(sc.run, grRuns))
    found = dict(pool.map(placementRun, [(s, start, d) for s in SHIFTS for _, start, d in RAYS]))
    for s in SHIFTS:
      _, f = shifted(s)
      lines.append('  shift %+.1f: the seam crosses the line between the bodies %+.0f km from the middle' %
                   (s, seamOnAxis(f)/1e3))
      for label, start, d in RAYS:
        m = found[(s, start, d)]
        dist, ang = sc.compare(m, grs[('GR', 'rule', start, d, None)])
        lines.append('    light %-24s distance from GR %.2e m   angle %.2e rad   turn at the seam %s%s'
                     % (label, dist, ang, ', '.join('%.1e' % t for t in m[2]) or '-', '  (hung)' if m[3] else ''))
    print('\n'.join(lines), flush=True)
    lines.append('')
    lines.append('interface: one body, the model\'s time inside a boundary, GR\'s own outside; light crossing it, against'
                 ' GR all the way; the rule using the flow\'s jump as the normal (the engine\'s), and the boundary\'s own')
    jobs = [(label, shape, R, start, d, which) for label, shape, R, start, d in INTERFACES
            for which in ('GR', 'jump', 'normal')]
    out = dict(pool.map(interfaceRun, jobs))
  for label, shape, R, start, d in INTERFACES:
    gr = out[(label, shape, R, start, d, 'GR')]
    lines.append('  ' + label)
    for which in ('jump', 'normal'):
      m = out[(label, shape, R, start, d, which)]
      dist, ang = sc.compare(m, gr)
      lines.append('    normal from the %-8s distance from GR %.2e m   angle %.2e rad   turns at the boundary %s'
                   % ('flow\'s jump' if which == 'jump' else 'boundary', dist, ang,
                      ', '.join('%.1e' % t for t in m[2]) or '-'))
  print('\n'.join(lines[lines.index('') + 1:]), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
