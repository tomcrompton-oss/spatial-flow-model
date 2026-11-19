"""
check 1, conserved quantities: does each model keep the energy and angular momentum its symmetries say it should, in
its own forms (engine/flow.py Calculator.conserved; the split model's in engine/split.py, Newton's in NewtonianCalculator)?
GR keeps them for a particle in any steady field (E), any field the same turned about a point (L), and fields steady
in a turning frame (the Jacobi constant J = E - Omega L) - whatever the bodies

  one      one body, an orbit from 200 to 600 Schwarzschild radii: E and L. every model is the one-body flow here,
           so this is the steps' own floor
  pair     a body of 1 solar mass and one of 0.1, at rest 2e7 m apart (the heavier's flow at the lighter 0.012 c), a
           particle going round the lighter from 2e5 to 3e5 m (0.027 c): E
  around   1 and 0.5 solar masses at rest 1e6 m apart, a particle going round both from 1.5e7 to 2.5e7 m - through the
           eikonal flow's seam twice an orbit: E
  turning  the 'pair' bodies going round each other on circles, the eikonal flow turning with them (combine
           'turning'), a particle round the lighter: J

each run is made at three step fractions (each step moves at most that fraction of the distance to the nearest body),
and the numbers are taken to zero step by the quadratic through the three - the flow step is first order close to a
body (the to-do), so its own drift comes out and what is left is the model's. for each quantity:
  drift   its change per orbit, from the slope through its values at each periapsis (the same place on the orbit, so
          its swing round the orbit drops out)
  swing   its largest less its smallest value over the run
both as fractions of its start, and in '1PN units': that fraction over eps = the larger of v^2/c^2 and the potential
sum GM/dc^2 at the start - GR's first corrections to the energy are about eps of it, so a quantity that isn't kept at
that order swings by about 1 of these, and one that is kept by far less

the flow models take the momentum step (engine/flow.py's default); 'along g (velocity step)' is the old one, which
isn't the metric's path where the flow has curl

run: python3 studies/conserved_quantities.py [case ...]     (default all; CQ_MODELS='a,b' runs just those models;
     prints, and writes
     logs/modelChecks/conserved_<datetime>/summary.log)
"""
import io
import contextlib
import math
import os
import sys
import time
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, Config, SpecialFlowCalculator, NewtonianCalculator
from engine.split import SplitFlowCalculator
from engine.turning import TurningRayField, carriedJacobi
from engine.logger import LOG_DIR
from engine.vectors import length
from engine.constants import *

FRACTIONS = (4e-4, 2e-4, 1e-4)
RS = 2*G*MS/C**2

#the models: name -> how to make its calculator for the bodies
SPLIT = ('lorentz', 'local', 'freefall', 'carried', 'heavier', 'heavier-only', 'heavier-centre')
MODELS = {
  'Newton': lambda bodies: NewtonianCalculator(bodies),
  'vectors': lambda bodies: SpecialFlowCalculator(bodies, 2, combine='vectors'),
  'along g': lambda bodies: SpecialFlowCalculator(bodies, 2, direction='g'),
  'along g (velocity step)': lambda bodies: SpecialFlowCalculator(bodies, 2, direction='g', step='velocity'),
  'eikonal': lambda bodies: SpecialFlowCalculator(bodies, 2, direction='eikonal-exact'),
  'split galilean': lambda bodies: SplitFlowCalculator(bodies, 'interval', 'galilean'),
}
for _boost in SPLIT:
  MODELS['split ' + _boost] = (lambda boost: lambda bodies: SplitFlowCalculator(bodies, 'static', boost))(_boost)


def ellipse(gm, centre, rp, ra, side=1.0):
  """a particle at periapsis rp from centre (on the +x side, or -x with side -1), going anticlockwise to apoapsis ra"""
  a = (rp + ra)/2
  return centre + np.array([side*rp, 0.0]), np.array([0.0, side*math.sqrt(gm*(2/rp - 1/a))]), 2*math.pi*math.sqrt(a**3/gm)


def one():
  bodies = [Body(MS)]
  x, v, period = ellipse(G*MS, np.zeros(2), 200*RS, 600*RS)
  return bodies, x, v, period, lambda t: bodies[0].pos, 6


def pair():
  D = 2e7
  bodies = [Body(MS), Body(0.1*MS, D, 0.0)]
  x, v, period = ellipse(0.1*G*MS, bodies[1].pos, 2e5, 3e5)
  return bodies, x, v, period, lambda t: bodies[1].pos, 6


def around():
  D, m = 1e6, 0.5
  bodies = [Body(MS, -D*m/(1 + m), 0.0), Body(m*MS, D/(1 + m), 0.0)]
  x, v, period = ellipse(1.5*G*MS, np.zeros(2), 1.5e7, 2.5e7, side=-1.0)
  return bodies, x, v, period, lambda t: np.zeros(2), 5


def turningBodies():
  D, m = 2e7, 0.1
  omega = math.sqrt(G*(1 + m)*MS/D**3)
  return [Body(MS, -D*m/(1 + m), 0.0, circling=omega), Body(m*MS, D/(1 + m), 0.0, circling=omega)], omega, D


def turning():
  bodies, omega, D = turningBodies()
  B = bodies[1]
  x, v, period = ellipse(0.1*G*MS, B.pos, 2e5, 3e5)
  return bodies, x, v + omega*np.array([-B.pos[1], B.pos[0]]), period, lambda t: B.at(t), 6


CASES = {'one': (one, ['Newton', 'one body']), 'pair': (pair, list(MODELS)), 'around': (around, list(MODELS)),
         'turning': (turning, ['turning'])}


def calculator(model, bodies):
  if model == 'one body':
    return SpecialFlowCalculator(bodies, 2)
  if model == 'turning':
    #the turning frame's tables at this pair's scale (the defaults are for the Solar System: paths from 150 km out)
    calc = SpecialFlowCalculator(bodies, 2, combine='turning')
    _, omega, D = turningBodies()
    calc.jacobi = carriedJacobi(bodies, omega)
    key = [(b.mass, b.x, b.y, b.black) for b in bodies] + [None, 'turning', calc.omega, calc.jacobi]
    calc.rays = (key, TurningRayField(bodies, calc.omega, calc.jacobi, minR=1e-6*D, maxR=3*D))
    return calc
  return MODELS[model](bodies)


def run(job):
  """one model, one case, one step fraction: the quantities at each periapsis, their range, and eps"""
  case, model, fraction = job
  bodies, x, v, period, centre, orbits = CASES[case][0]()
  calc = calculator(model, bodies)
  p = Particle()
  p.pos = x
  if hasattr(calc, 'initPV'):
    calc.initPV(p, v)
  else:
    p.v = v
  config = Config()
  config.dt, config.stepFraction = period/100, fraction
  q0 = calc.conserved(p)
  eps = max((p.v @ p.v)/C**2, sum(b.GM/length(p.pos - b.at(0.0)) for b in bodies)/C**2)
  low, high = dict(q0), dict(q0)
  peri, recent = {name: [] for name in q0}, []
  start, n, stopped = time.time(), 0, None
  r0 = length(p.pos - centre(0.0))
  cap = int(8*orbits*2*math.pi/fraction)   #about 3 times what a run should take
  with contextlib.redirect_stdout(io.StringIO()):
    for dt in calc.steps(p, config, orbits*period):
      calc.move(p, dt)
      n += 1
      r = length(p.pos - centre(p.t))
      if n >= cap or not r0/10 < r < 10*r0:
        stopped = 'after %d steps, %.3g of the way, at %.3g of the starting distance' % (n, p.t/(orbits*period), r/r0)
        break
      q = calc.conserved(p)
      for name, value in q.items():
        low[name], high[name] = min(low[name], value), max(high[name], value)
      recent = (recent + [(length(p.pos - centre(p.t)), q)])[-3:]
      if len(recent) == 3 and recent[1][0] < recent[0][0] and recent[1][0] <= recent[2][0]:
        for name, value in recent[1][1].items():
          peri[name].append(value)
      if not np.all(np.isfinite(p.pos)):
        break
  return job, {'q0': q0, 'low': low, 'high': high, 'peri': peri, 'eps': eps, 'steps': n, 'wall': time.time() - start,
               'stopped': stopped}


def summarise(results, case, model):
  """drift and swing, at each fraction and taken to zero step"""
  runs = [results[(case, model, f)] for f in FRACTIONS]
  out = {}
  for name in runs[0]['q0']:
    scale = abs(runs[0]['q0'][name])
    drifts, swings = [], []
    for r in runs:
      values = r['peri'][name]
      drifts.append(np.polyfit(np.arange(len(values)), values, 1)[0]/scale if len(values) >= 2 else math.nan)
      swings.append((r['high'][name] - r['low'][name])/scale)
    zero = lambda ys: np.polyfit(FRACTIONS, ys, 2)[-1]
    out[name] = (drifts, zero(drifts), swings, zero(swings))
  return out, runs[0]['eps'], len(runs[-1]['peri'][next(iter(runs[0]['q0']))]), sum(r['wall'] for r in runs)


def main():
  cases = sys.argv[1:] or list(CASES)
  folder = os.path.join(LOG_DIR, 'modelChecks', 'conserved_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  only = [m for m in os.environ.get('CQ_MODELS', '').split(',') if m]   #CQ_MODELS='one body,eikonal': just those
  if only:
    CASES.update({case: (CASES[case][0], [m for m in CASES[case][1] if m in only]) for case in cases})
  jobs = [(case, model, f) for case in cases for model in CASES[case][1] for f in FRACTIONS]
  jobs.sort(key=lambda j: (not j[1].startswith('split'), j[2]))   #the slowest first
  results = {}
  with Pool(8) as pool:
    for job, result in pool.imap_unordered(run, jobs):
      results[job] = result
      print('%d/%d %s %s %g: %d steps, %.0f s%s' % (len(results), len(jobs), job[0], job[1], job[2], result['steps'],
            result['wall'], ', STOPPED ' + result['stopped'] if result['stopped'] else ''), flush=True)
  lines = ['conserved quantities: each model\'s own forms (per unit mass, E and J less the rest energy). drift: the '
           'change per orbit (from the periapsides); swing: largest less smallest over the run; both as fractions of '
           'the start, at step fractions %s and taken to zero step (0:), and in 1PN units (/eps)' %
           ', '.join('%g' % f for f in FRACTIONS)]
  for case in cases:
    lines.append('')
    lines.append('== %s' % case)
    for model in CASES[case][1]:
      stops = [results[(case, model, f)]['stopped'] for f in FRACTIONS if results[(case, model, f)]['stopped']]
      if stops:
        lines.append('  %-22s stopped early: %s' % (model, '; '.join(stops)))
        continue
      out, eps, orbits, wall = summarise(results, case, model)
      for name, (drifts, drift0, swings, swing0) in out.items():
        lines.append('  %-22s %s  drift/orbit %s  0: %+.2e (%+.2e eps)   swing %s  0: %.2e (%.2e eps)'
                     '   [eps %.1e, %d periapsides, %.0f s]'
                     % (model, name, ' '.join('%+.2e' % d for d in drifts), drift0, drift0/eps,
                        ' '.join('%.2e' % s for s in swings), swing0, swing0/eps, eps, orbits, wall))
  print('\n'.join(lines))
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
