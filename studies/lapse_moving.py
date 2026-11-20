"""
the lapse and curved space with the bodies moving: the turning flow (the Sun and the Earth going round each other,
the eikonal flow turning with them, studies/turning_eikonal.py) along engine/metric.py's family - lambda of gravity
in the clocks, space curved to match (kappa = lambda), and lambda of GR's moving-body terms (its vector potential and
its lapse's psi), so that lambda = 1 is GR's first post-Newtonian metric of the same bodies; and with the clocks left
alone (N = 1) and space curved across the flow, by 2 Phi/c^2 or by the flow's own |u|^2/c^2 (FlowSpacetime transverse
True or 'flow'; the turning flow's |u|^2 is not 2 Phi, so the two differ):

  sun      light passing the Sun, 0.5 AU either side (inside the turning flow's Sun region, where its paths' energy
           J squeezes space): the bending at 2, 10 and 50 solar radii, less the same family's bending with the Sun
           alone (so the flow's part of light's coordinate direction at the ends, which is as large as the bending
           at 0.5 AU, drops out), against the same for GR's metric (Cassini: 2.3 x 10^-5 of the bending)

radar to a mirror held at a fixed distance in the turning frame is not a fair test here: in GR's coordinates such a
mirror is Lorentz-contracted by the Earth's 30 km/s (a cos 2D term of about v^2 r/4c^2 = 0.93 m), where the turning
flow carries the Earth's space with it. lunar ranging with moving bodies needs the Moon's own orbit, fitted as
studies/de_sitter.py does

run: python3 studies/lapse_moving.py     (prints, and writes
     logs/modelChecks/lapseMoving_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, SpecialFlowCalculator
from engine.metric import MetricCalculator, FlowSpacetime, PostNewtonian
from engine.logger import LOG_DIR
from engine.vectors import length
from engine.constants import *
from turning_eikonal import bodies, OMEGA

SHARES = (0.0, 0.5, 1.0)
MODELS = (['turning, lambda %g' % s for s in SHARES] + ['turning, N = 1, transverse space',
          'turning, N = 1, space from u', 'turning, N = 1, from its body', 'GR (first post-Newtonian)'])


def mode(model):
  return 'source' if 'from its body' in model else 'flow' if 'space from u' in model else True


def spacetime(model, alone=False):
  """the model's spacetime, or (alone) the same family's with the Sun alone, at rest where it is at t = 0"""
  if alone:
    sun = [Body(MS, *bodies()[0].pos)]
    if model.startswith('GR'):
      return PostNewtonian(sun)
    if 'N = 1' in model:
      return FlowSpacetime(SpecialFlowCalculator(sun, 2), transverse=mode(model))
    share = float(model.split('lambda ')[1])
    return FlowSpacetime(SpecialFlowCalculator(sun, 2), share=share, curve=share)
  if model.startswith('GR'):
    return PostNewtonian(bodies())
  if 'N = 1' in model:
    return FlowSpacetime(SpecialFlowCalculator(bodies(), 2, combine='turning'), transverse=mode(model))
  share = float(model.split('lambda ')[1])
  return FlowSpacetime(SpecialFlowCalculator(bodies(), 2, combine='turning'), share=share, curve=share)


def bend(S, b, half=0.5*AU, fraction=0.001):
  """light from the Sun's place + (b, -half) along +y to y = +half, run in the spacetime: its turn towards the Sun"""
  calc = MetricCalculator(S)
  centre = S.bodies[0].at(0.0)
  p = Particle()
  p.pos = centre + np.array([b, -half])
  calc.initLight(p, np.array([0.0, 1.0]))
  while p.pos[1] < centre[1] + half:
    calc.move(p, calc.stepSize(p, fraction, 0.002*AU/C))
  return math.atan2(-p.v[0], p.v[1])


def sun(job):
  model, radii, alone = job
  return job, bend(spacetime(model, alone), radii*RSUN)


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'lapseMoving_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  mas = 180/math.pi*3600e3
  radii = (2, 10, 50)
  with Pool(8) as pool:
    found = dict(pool.map(sun, [(m, r, alone) for m in MODELS for r in radii for alone in (False, True)]))
  extra = {(m, r): found[(m, r, False)] - found[(m, r, True)] for m in MODELS for r in radii}
  gr = {r: extra[(MODELS[-1], r)] for r in radii}
  lines = ['sun: light passing the Sun, 0.5 AU either side, the Sun and the Earth going round each other: the bending'
           ' less the same family\'s with the Sun alone, against GR\'s the same way (Cassini: 2.3e-5 of the bending,'
           ' %.4f mas at 2 R_sun)' % (2.3e-5*found[(MODELS[-1], 2, True)]*mas)]
  for m in MODELS:
    lines.append('  %-32s %s' % (m, '   '.join('%d R_sun: %+.4f mas (GR\'s %+.4f)' % (r, extra[(m, r)]*mas, gr[r]*mas)
                                                for r in radii)))
  print('\n'.join(lines), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
