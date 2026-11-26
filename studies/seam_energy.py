"""
energy across the seam: orbits round both of two solar masses 200,000 km apart (at rest), crossing the seam many
times, run by the model with space curved and flat (studies/seam_crossing.py's spacetimes), steps 0.2% of the distance
to the nearer body: the change in the energy H across each crossing step against an ordinary step's

run: python3 studies/seam_energy.py     (a few minutes; prints, and writes logs/modelChecks/seamEnergy_<datetime>/summary.log)
"""
import os
import sys
import time
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import Particle
from engine.metric import MetricCalculator
from engine.logger import LOG_DIR
import seam_crossing as sc


def orbit(job):
  kind, start, v = job
  calc = MetricCalculator(sc.spacetime(kind))
  p = Particle()
  p.pos = np.array(start, float)
  calc.initPV(p, np.array(v, float))
  E0 = calc.conserved(p)['E']
  before, steps, jumps, worst, started = calc.sideOf(p), [], [], 0.0, time.time()
  while p.t < 2e4 and time.time() - started < 900:
    e1 = calc.conserved(p)['E']
    calc.move(p, calc.stepSize(p, 0.002, 5.0))
    e2 = calc.conserved(p)['E']
    change = abs(e2 - e1)/abs(E0)
    if p.region != before:
      jumps.append(change)
      before = p.region
    else:
      steps.append(change)
    worst = max(worst, abs(e2 - E0)/abs(E0))
  return job, (len(jumps), max(jumps) if jumps else 0.0, float(np.median(steps)), max(steps), worst, p.t)


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'seamEnergy_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  jobs = [(k, (0.0, 1.5e8), (v, 0.0)) for k in ('curved', 'flat') for v in (1.4e6, 1.6e6)]
  lines = ['orbits round both bodies, crossing the seam: the energy\'s change across each crossing step, against an'
           ' ordinary step\'s (as a share of the energy)']
  with Pool(4) as pool:
    for (kind, start, v), (n, jump, typical, largest, worst, t) in pool.map(orbit, jobs):
      lines.append('  %-6s starting at %.1e m/s: %d crossings in %.0f s; across a crossing at most %.1e; an ordinary step'
                   ' typically %.1e, at most %.1e; the drift over the run %.1e' % (kind, v[0], n, t, jump, typical,
                                                                                 largest, worst))
  print('\n'.join(lines), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
