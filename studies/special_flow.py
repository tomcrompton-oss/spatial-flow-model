"""
Part 1's special-relativistic mechanics of spatial flow (docs/part1/mechanics/special-relativistic.md): light crossing
regions of space that flow downwards ever faster (u = (0, -k x), up to 0.8c), by the page's procedure. the change in
the flow added to w as a plain vector (dashed) leaves the light going straight, but lets |w| pass c; added
relativistically (solid), |w| stays at c and the path curves - Thomas precession (Wigner rotation)

the same example as studies/part1_examples.py's regions, without its third path (the flow's geodesic, which differs
because this flow has curl - for a later page)

writes logs/specialFlow/specialFlow_<datetime>/: summary.log, csvs and the viewer files (special_regions.full.json)

run: python3 studies/special_flow.py      (seconds; then: python3 scripts/publish_run.py logs/specialFlow/specialFlow_<datetime>)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import Particle
from engine.logger import LOG_DIR
from engine.constants import *
from part1_examples import write, follow, COLOURS, Shear
from two_body_escapes import writeViewerFiles


def main():
  folder = os.path.join(LOG_DIR, 'specialFlow', 'specialFlow_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  made, lines = [], []
  for relativistic, style in ((False, 'dashed'), (True, 'solid')):
    calc = Shear(relativistic)
    p = Particle()
    p.pos = np.array([0.0, 0.0])
    calc.initPW(p, np.array([C, 0.0]))
    rows = follow(calc, p, lambda p: p.pos[0] >= Shear.WIDTH or p.t > 30, lambda p: 1e-3, every=20)
    name = 'regions_' + ('relativistic' if relativistic else 'plain')
    t, x, y, vx, vy = rows[-1]
    lines.append('%s: crossed %.0f m in %.3f s, w turned %.2f degrees, v (%.4fc, %.4fc), |w| %.6fc'
                 % (name, x, t, math.degrees(math.atan2(p.w[1], p.w[0])), vx/C, vy/C, np.linalg.norm(p.w)/C))
    print(lines[-1], flush=True)
    made.append((write(folder, name, calc, rows, ['t', 'pos_x', 'pos_y', 'v_x', 'v_y'],
                       ['light from (0, 0) along +x through u = (0, -k x), k = 0.8c over %g m; the change in the flow'
                        ' added %s' % (Shear.WIDTH, 'relativistically' if relativistic else 'as plain vectors'),
                        lines[-1]]), COLOURS[1], style))
  writeViewerFiles(folder, 'special_regions', made, preferences={'showFlow': True, 'showBodies': False},
                   frames=Shear(True))
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)
  return folder


if __name__ == '__main__':
  main()
