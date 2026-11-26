"""
the crossing rule with a body moving: does the boundary have to be where the two times agree?

with bodies at rest (studies/seam_rules.py) the rule worked across any boundary, even one where the two times differ,
since nothing then depends on time. with a body moving, the time a light ray carries across a boundary matters: the
engine keeps it (p.t unchanged), so if the two sides' times differ there, the ray comes out at the wrong moment, and
meets the body where it isn't.

one body moving at V = 0.1 c (to make the effect large; both sides are the same first post-Newtonian GR, so the
comparison is exact to that order): GR's harmonic time t outside a boundary (engine/metric.py PostNewtonian), and the
same spacetime re-sliced by the body's flow carried at its velocity inside it (SlicedPN: t = T + (phi - phi_0)/c^2,
phi = V . d - 2 sqrt(2 GM r)). the boundaries, each moving with the body:

  level set   a curve where phi = phi_0: the two times agree all along it
  circle      a circle round the body: phi, and so the times, differ along it
and a circle held fixed in space (the times differ, and the boundary doesn't move with the body). light passing the
body, crossing the boundary twice, against GR all the way

run: python3 studies/seam_moving.py     (a few minutes; prints, and writes logs/modelChecks/seamMoving_<datetime>/summary.log)
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
from engine.flow import Body, Particle
from engine.metric import MetricCalculator, PostNewtonian, SlicedPN, Spacetime
from engine.logger import LOG_DIR
from engine.constants import MS, C, G
import seam_crossing as sc

V = 0.1*C
R = 1e8                 #the boundary's size (m)
BODY = lambda: Body(MS, 0.0, 0.0, velocity=(0.0, V))
HALF = 5e8


class Sliced(SlicedPN):
  """SlicedPN with phi less a constant, so its time is GR's on the level set phi = phi_0"""

  def __init__(self, bodies, phi0):
    super().__init__(bodies, around=0)
    self.phi0 = phi0

  def potential(self, x, t):
    phi, grad, rate = super().potential(x, t)
    return phi - self.phi0, grad, rate


class Joined(Spacetime):
  timedSeams = True

  def __init__(self, shape):
    body = BODY()
    self.bodies = [body]
    self.shape = shape
    self.phi0 = V*0.0 - 2*math.sqrt(2*body.GM*R)          #phi on the level set through (R, 0) from the body
    self.inner = Sliced([body], self.phi0)
    self.outer = PostNewtonian([body])
    self.static, self.centre = False, None

  def region(self, x, t):
    b = self.bodies[0]
    d = x - b.at(t)
    if self.shape == 'level set':
      inside = V*d[1] - 2*math.sqrt(2*b.GM*np.linalg.norm(d)) > self.phi0
    elif self.shape == 'circle':
      inside = d @ d < R*R
    else:
      inside = x @ x < R*R                                   #held fixed in space
    return 0 if inside else 1

  def seamVelocity(self, x, t=0.0):
    return np.zeros(2) if self.shape == 'fixed circle' else np.array([0.0, V])

  def parts(self, x, t, region=None):
    if region is None:
      region = self.region(x, t)
    return (self.inner if region == 0 else self.outer).parts(x, t, None)

  def lapseOffset(self, x, t):
    return self.parts(x, t)[0]

  def flow(self, x, t, region=None):
    return self.parts(x, t, region)[1]

  def space(self, x, t, region=None):
    S = self.inner if (self.region(x, t) if region is None else region) == 0 else self.outer
    return S.pieces(x, t)[1] if S is self.inner else S.space(x, t)


def light(job):
  shape, y0 = job
  S = PostNewtonian([BODY()]) if shape == 'GR' else Joined(shape)
  calc = MetricCalculator(S)
  p = Particle()
  p.pos = np.array([-HALF, y0])
  calc.initLight(p, np.array([1.0, 0.0]))
  pts, dirs, turns, before = [p.pos.copy()], [p.v/np.linalg.norm(p.v)], [], calc.sideOf(p)
  started = time.time()
  while p.pos[0] < HALF and len(pts) < 100000 and time.time() - started < 900:
    old = p.v/np.linalg.norm(p.v)
    calc.move(p, 2e-3)
    pts.append(p.pos.copy())
    dirs.append(p.v/np.linalg.norm(p.v))
    if getattr(p, 'region', None) is not None and p.region != before:
      turns.append(math.acos(max(-1.0, min(1.0, old @ dirs[-1]))))
      before = p.region
  return job, (np.array(pts), np.array(dirs), turns, time.time() - started >= 900)


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'seamMoving_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  passing = HALF/C*V          #the body moves this far while the light reaches it
  offsets = (passing + 3e7, passing + 6e7)
  shapes = ('GR', 'level set', 'circle', 'fixed circle')
  with Pool(8) as pool:
    out = dict(pool.map(light, [(s, y) for s in shapes for y in offsets]))
  lines = ['one body moving at %.2f c: GR\'s time outside a boundary, the same spacetime re-sliced by the body\'s carried'
           ' flow inside; light passing it, against GR all the way' % (V/C)]
  for y in offsets:
    lines.append('light passing about %.0f km from the body' % ((y - passing)/1e3))
    for s in shapes[1:]:
      m = out[(s, y)]
      dist, ang = sc.compare(m, out[('GR', y)])
      lines.append('  %-12s crossings %d, turns there %s;  distance from GR %.2e m, angle %.2e rad%s'
                   % (s, len(m[2]), ', '.join('%.1e' % t for t in m[2]) or '-', dist, ang, '  (hung)' if m[3] else ''))
  print('\n'.join(lines), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
