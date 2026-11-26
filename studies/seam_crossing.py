"""
paths crossing the seam of the potential flow (two bodies at rest, engine/two_centre.py's exact flow), against
general relativity: with space curved across the flow (FlowSpacetime transverse 'flow') the model is GR's first
post-Newtonian metric re-sliced in time, T = t + S(x)/c^2, with the same spatial coordinates - so a path's shape in
space must be GR's, crossing the seam or not; only how fast it is traced in T differs. a kink at the seam would show
at the size of u/c (here up to 0.8%), against the model's own error of order (u/c)^4

each path starts at the same place in the model and in GR (engine/metric.py PostNewtonian), with the same direction
of coordinate velocity (light), or GR's coordinate velocity v_t and the model's v_T = v_t / (1 - u . v_t / c^2)
(dT/dt = 1 + grad S . v/c^2, grad S = -u). measured: the largest distance from the model's path to GR's, and the
largest angle between their directions, and the change of the model's direction across the crossing step

the crossing rule is tried three ways (MetricCalculator.crossSeam):
  rule      the engine's: the momentum along the seam kept, the momentum across changed to keep the energy H
  keep p    the canonical momentum p kept as it is (only the flow changes)
  keep v    the coordinate velocity v kept (the momentum set from v in the new region)
and, for flat space (the flow model of Part 2), the engine's rule

run: python3 studies/seam_crossing.py     (a few minutes; prints, and writes
     logs/modelChecks/seamCrossing_<datetime>/summary.log)
"""
import math
import os
import sys
import time
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, SpecialFlowCalculator
from engine.metric import MetricCalculator, FlowSpacetime, PostNewtonian
from engine.logger import LOG_DIR
from engine.constants import MS, C, G

D = 2e8                 #m between two bodies of a solar mass each: the flow at the seam's middle is 0.8% of c
HALF = 5e8              #paths run from x = -HALF to +HALF (or the like, turned)
DT_LIGHT = 2e-3         #s: 600 km a step
BODIES = lambda: [Body(MS, -D/2, 0.0), Body(MS, D/2, 0.0)]


def spacetime(kind):
  if kind == 'GR':
    return PostNewtonian(BODIES())
  calc = SpecialFlowCalculator(BODIES(), 2)
  return FlowSpacetime(calc, transverse=False if kind == 'flat' else 'flow')


class KeepP(MetricCalculator):
  def crossSeam(self, p, before):
    after = self.region(p.pos, p.t)
    if after != before:
      p.region = after
      self.keep(p)


class KeepV(MetricCalculator):
  def crossSeam(self, p, before):
    after = self.region(p.pos, p.t)
    if after != before:
      v = p.v.copy()
      p.region = after
      if p.light:
        self.initLight(p, v/np.linalg.norm(v))
      else:
        self.initPV(p, v)


RULES = {'rule': MetricCalculator, 'keep p': KeepP, 'keep v': KeepV}


def run(job):
  """one path: its points and directions, and the turn of its direction across each crossing step"""
  kind, rule, start, direction, speed = job
  S = spacetime(kind)
  calc = (MetricCalculator if kind == 'GR' else RULES[rule])(S)
  p = Particle()
  p.pos = np.array(start, dtype=float)
  n = np.array(direction, dtype=float)/np.linalg.norm(direction)
  if speed is None:
    calc.initLight(p, n)
    dt = DT_LIGHT
  else:
    v = speed*n
    if kind != 'GR':
      u = S.flow(p.pos, 0.0, S.region(p.pos, 0.0))
      v = v/(1 - (u @ v)/C**2)
    calc.initPV(p, v)
    dt = DT_LIGHT*C/speed
  pts, dirs, turns = [p.pos.copy()], [p.v/np.linalg.norm(p.v)], []
  before = calc.sideOf(p)
  started = time.time()
  while np.linalg.norm(p.pos) < 1.2*HALF and len(pts) < 200000 and time.time() - started < 600:
    old = p.v/np.linalg.norm(p.v)
    calc.move(p, dt)
    pts.append(p.pos.copy())
    dirs.append(p.v/np.linalg.norm(p.v))
    if getattr(p, 'region', None) is not None and p.region != before:
      turns.append(math.acos(max(-1.0, min(1.0, old @ dirs[-1]))))
      before = p.region
  return job, (np.array(pts), np.array(dirs), turns, len(pts) >= 200000 or time.time() - started >= 600)


def compare(model, gr):
  """the largest distance from the model's points to GR's path, and the largest angle between directions there - over
  the stretch both cover (a model point past either end of GR's path is left out)"""
  (mp, md, _, _), (gp, gd, _, _) = model, gr
  worst, angle = 0.0, 0.0
  for x, d in zip(mp[::5], md[::5]):
    k = int(np.argmin(np.sum((gp - x)**2, axis=1)))
    if k == 0 or k == len(gp) - 1:
      continue
    a, b = k - 1, k + 1
    seg = gp[b] - gp[a]
    t = np.clip((x - gp[a]) @ seg/(seg @ seg), 0, 1) if seg @ seg > 0 else 0.0
    worst = max(worst, float(np.linalg.norm(x - (gp[a] + t*seg))))
    angle = max(angle, math.acos(max(-1.0, min(1.0, float(d @ gd[k])))))
  return worst, angle


PATHS = [   #(label, start, direction, speed: None for light)
  ('light across the middle, 30,000 km off the line', (-HALF, 3e7), (1, 0), None),
  ('light across, 100,000 km off the line', (-HALF, 1e8), (1, 0), None),
  ('light across, 300,000 km off the line', (-HALF, 3e8), (1, 0), None),
  ('light at 45 degrees to the seam', (-HALF/math.sqrt(2), -HALF/math.sqrt(2) + 5e7), (1, 1), None),
  ('light along the seam, 1,000 km beside it', (-1e6, -HALF), (0, 1), None),
  ('light crossing near a body, 20,000 km out', (-HALF, 2e7 + 0.0), (1, 0.08), None),
  ('a particle at 3,000 km/s, across the middle', (-2e8, 5e7), (1, 0), 3e6),
  ('a particle at 3,000 km/s that stays on one side (the comparison\'s own noise)', (-5e7, -3e8), (0, 1), 3e6),
  ('a particle at 10,000 km/s, across, 20,000 km off the line', (-3e8, 2e7), (1, 0), 1e7),
]


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'seamCrossing_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  jobs = []
  for label, start, direction, speed in PATHS:
    for kind, rule in (('GR', 'rule'), ('curved', 'rule'), ('curved', 'keep p'), ('curved', 'keep v'), ('flat', 'rule')):
      jobs.append((kind, rule, start, direction, speed))
  lines = ['paths crossing the seam between two solar masses %.0e m apart, at rest: the model with space curved (GR'
           ' re-sliced) and flat, each crossing rule, against GR (PostNewtonian). distance: the largest from the'
           ' model\'s path to GR\'s; angle: the largest between their directions; turn: the model\'s change of'
           ' direction across each crossing step' % D]
  with Pool(8) as pool:
    results = {}
    for job, out in pool.imap_unordered(run, jobs):
      results[job] = out
      print('done', job[0], job[1], job[2], 'hung' if out[3] else '', flush=True)
  for label, start, direction, speed in PATHS:
    gr = results[('GR', 'rule', start, direction, speed)]
    lines.append('%s (GR: %d crossings)' % (label, len(gr[2])))
    for kind, rule in (('curved', 'rule'), ('curved', 'keep p'), ('curved', 'keep v'), ('flat', 'rule')):
      m = results[(kind, rule, start, direction, speed)]
      dist, ang = compare(m, gr)
      lines.append('  %-7s %-7s distance %.3e m   angle %.3e rad   crossings %d, turn there %s%s'
                   % (kind, rule, dist, ang, len(m[2]), ', '.join('%.2e' % t for t in m[2]) or '-',
                      '   (stopped by its limit)' if m[3] else ''))
  print('\n'.join(lines), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
