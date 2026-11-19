"""
the lapse and curved space (engine/metric.py FlowSpacetime: lambda of gravity in the clocks, space curved to match,
kappa = lambda - GR at first order for one body, studies/metric_checks.py) on the two tests that ruled out the
eikonal flow with the bodies at rest (studies/multi_body_pn.py):

  lunar    radar from the Earth's surface to a mirror at the Moon's distance and back, the Sun 1 AU away, by the
           mirror's angle from the Sun (D): the round trip less the Earth's alone, as a range at the Earth's clock -
           its cos D part, against lunar laser ranging's (2.8 +- 4.1) mm. light along the straight line, at the
           speeds |s n - u|_gamma = N c either way (its bending changes the trip only at second order)
  jupiter  light passing Jupiter (the Sun 5.2 AU away), 10 AU either side: the bending with both, less the Sun's alone
           and Jupiter's alone (GR: 0 to first order in G), against VLBI's 10 microarcseconds

each for the eikonal flow at lambda = 0 (the flow model), 0.5 and 1 (no flow left: all of gravity in the clocks and
the curved space); the eikonal flow with the clocks left alone (N = 1) and space curved across it (FlowSpacetime
transverse: GR's static metric sliced by free fall, to first order); the same with space decided by the flow alone,
(|u|^2 delta - u u)/c^2 (transverse 'flow'), on the eikonal, vector and along-g flows, with the last two flat for
comparison; and GR's first post-Newtonian metric of the
bodies at rest (engine/metric.py PostNewtonian)

run: python3 studies/lapse_two_bodies.py [test ...]     (default both; prints, and writes
     logs/modelChecks/lapseTwoBodies_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, Config, SpecialFlowCalculator
from engine.metric import MetricCalculator, FlowSpacetime, PostNewtonian
from engine.logger import LOG_DIR
from engine.vectors import length
from engine.constants import *
from multi_body_pn import NODES, WEIGHTS, DMOON, MJ, RJ, DJ

SHARES = (0.0, 0.5, 1.0)
MODELS = (['eikonal, lambda %g' % s for s in SHARES] + ['eikonal, N = 1, transverse space']
          + ['%s, N = 1, space from u' % f for f in ('eikonal', 'vectors', 'along g')]
          + ['vectors, flat', 'along g, flat', 'GR (first post-Newtonian)'])
FLOWS = {'eikonal': {}, 'vectors': {'combine': 'vectors'}, 'along g': {'direction': 'g'}}


def spacetime(model, bodies):
  if model.startswith('GR'):
    return PostNewtonian(bodies)
  name = model.split(',')[0]
  rule = dict(FLOWS[name])
  if name == 'eikonal' and len(bodies) == 2:
    rule['direction'] = 'eikonal-exact'
  flow = SpecialFlowCalculator(bodies, 2, **rule)
  if 'flat' in model:
    return FlowSpacetime(flow)
  if 'space from u' in model:
    return FlowSpacetime(flow, transverse='flow')
  if 'transverse' in model:
    return FlowSpacetime(flow, transverse=True)
  share = float(model.split('lambda ')[1])
  return FlowSpacetime(flow, share=share, curve=share)


def speeds(S, x, n):
  """light's coordinate speeds along n and against it at x: the roots of |s n - u|^2_gamma = N^2 c^2"""
  a, u = S.lapseOffset(x, 0.0), S.flow(x, 0.0)
  h = S.space(x, 0.0)
  g = np.eye(2) if h is None else np.eye(2) + h
  N = 1 + a
  A, B, D = n @ g @ n, n @ g @ u, u @ g @ u - N*N*C*C
  root = math.sqrt(B*B - A*D)
  return (B + root)/A, (-B + root)/A


def roundTrip(S, a, b, pieces=400):
  """light's round trip a -> b -> a along the straight line, in the coordinates' time"""
  span = length(b - a)
  n = (b - a)/span
  edges = np.concatenate([[0.0], np.geomspace(1.0, span, pieces)])
  total = 0.0
  for lo, hi in zip(edges[:-1], edges[1:]):
    for x, wt in zip(NODES, WEIGHTS):
      s = (lo + hi)/2 + (hi - lo)/2*x
      up, down = speeds(S, a + s*n, n)
      total += wt*(hi - lo)/2*(1/up + 1/down)
  return total


def clockRate(S, x):
  """a clock at rest at x: dtau/dt = sqrt(N^2 - |u|^2_gamma/c^2)"""
  a, u = S.lapseOffset(x, 0.0), S.flow(x, 0.0)
  h = S.space(x, 0.0)
  uu = u @ u if h is None else u @ (np.eye(2) + h) @ u
  return math.sqrt((1 + a)**2 - uu/C**2)


def lunar(model):
  both = spacetime(model, [Body(MS, -AU, 0.0), Body(ME)])
  alone = spacetime(model, [Body(ME)])
  rows = []
  for D in range(0, 360, 10):
    out = np.array([-math.cos(math.radians(D)), math.sin(math.radians(D))])
    a, b = REARTH*out, DMOON*out
    extra = C*(roundTrip(both, a, b)*clockRate(both, a) - roundTrip(alone, a, b)*clockRate(alone, a))/2
    rows.append((math.radians(D), extra))
  Ds, ms = np.array([r[0] for r in rows]), np.array([r[1] for r in rows])
  return model, {'cosD': 2*np.mean(ms*np.cos(Ds)), 'mean': ms.mean(), 'swing': (ms.max() - ms.min())/2}


def bend(S, b, half=10*AU, fraction=0.002):
  calc = MetricCalculator(S)
  p = Particle()
  p.pos = np.array([DJ + b, -half])
  calc.initLight(p, np.array([0.0, 1.0]))
  while p.pos[1] < half:
    calc.move(p, calc.stepSize(p, fraction, 0.01*AU/C))
  return math.atan2(-p.v[0], p.v[1])


def jupiter(job):
  model, radii = job
  b = radii*RJ
  sun, jup = Body(MS, 0.0, 0.0), Body(MJ, DJ, 0.0)
  both, s, j = (bend(spacetime(model, bodies), b) for bodies in ([sun, jup], [sun], [jup]))
  return job, (both - s - j, j)


def main():
  chosen = sys.argv[1:] or ['lunar', 'jupiter']
  folder = os.path.join(LOG_DIR, 'modelChecks', 'lapseTwoBodies_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = []
  uas = 180/math.pi*3600e6
  with Pool(8) as pool:
    if 'lunar' in chosen:
      lines.append('lunar: radar Earth -> Moon\'s distance -> Earth, the Sun 1 AU away, less the Earth alone, as a range:'
                   ' its cos D part (lunar laser ranging (2.8 +- 4.1) mm), mean and swing over the month')
      for model, r in pool.map(lunar, MODELS):
        lines.append('  %-34s cos D %+.4f m   mean %+.4f m   swing %.4f m' % (model, r['cosD'], r['mean'], r['swing']))
      print('\n'.join(lines), flush=True)
    if 'jupiter' in chosen:
      lines.append('jupiter: light past Jupiter, the Sun 5.2 AU away: the bending with both less each alone (GR: 0 to first'
                   ' order; VLBI positions to under 10 uas)')
      jobs = [(m, r) for m in MODELS for r in (1, 10, 100)]
      found = dict(pool.map(jupiter, jobs))
      for m in MODELS:
        lines.append('  %-34s %s' % (m, '   '.join('%g R_J: %+.2f uas (of %.0f)' % (r, found[(m, r)][0]*uas,
                                                                                found[(m, r)][1]*uas)
                                                 for r in (1, 10, 100))))
      print('\n'.join(lines[-len(MODELS) - 1:]), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
