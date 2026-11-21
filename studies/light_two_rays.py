"""
light past Jupiter as VLBI measures it: the angle between two rays arriving at one observer - one passing Jupiter at
b, one at a reference distance - against GR's. the angle at one place and time is the same in any slicing of time
and any frame's coordinates, so it can be compared for flows whose space moves far from the bodies (the turning flow:
25-40 km/s at 10 AU), where a ray's direction through the coordinates can't: re-slicing time by the flow's potential
turns that by u/c (and the cross term - both bodies less each alone - needs a flow that can be run for one body)

each ray leaves a fixed emitter H before Jupiter (y = -H) and is shot - its starting direction found by the secant
method - to reach the observer H beyond it (y = +H, x = Jupiter's + the reference distance), the light passing Jupiter
as it is at (X_J, 0). the observer moves with the space there (the flow models' free fall: N = 1): in a flow model it
measures each ray's direction as w = v - u, light's velocity through that space, and the angle between them with
space's metric gamma; in GR it moves at the model's u through GR's static frame (where angles are the coordinates',
the space being conformally flat to first order), so GR's directions are aberrated exactly (special relativity) by
that velocity

cases: Jupiter at rest, the eikonal flow (flat, and space from u relative to its body) and GR, the Sun and Jupiter at
rest about their centre of mass; Jupiter on its orbit, the turning flow (the eikonal flow in the frame turning with
them: one potential), and the carried flow (each region its own potential), against GR with the same bodies moving

run: python3 studies/light_two_rays.py [H in AU]     (default 2; prints, and writes
     logs/modelChecks/lightTwoRays_<datetime>/summary.log)
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
from engine.constants import *
from multi_body_pn import MJ, RJ, DJ

UAS = 180/math.pi*3600e6
H = (float(sys.argv[1]) if len(sys.argv) > 1 else 2.0)*AU
NEAR = (1, 10)          #the near rays' distances from Jupiter (R_J)
REFERENCE = 100         #the reference ray's
MU = MJ/(MS + MJ)
W = math.sqrt(G*(MS + MJ)/DJ**3)
XJ = (1 - MU)*DJ        #Jupiter from the centre of mass (and from the Sun, for the carried flow's setup)
T0 = H/C                #the light passes Jupiter then, Jupiter at (XJ, 0)

#each case: its spacetimes, and the label of the GR it is compared with
CASES = {
  'eikonal, flat, at rest': 'GR, at rest',
  'eikonal, space from u, at rest': 'GR, at rest',
  'turning, flat, on its orbit': 'GR, on its orbit',
  'turning, space from u, on its orbit': 'GR, on its orbit',
  'carried, flat, on its orbit': 'GR, carried setup',
  'carried, space from u, on its orbit': 'GR, carried setup',
}


def bodies(case):
  if 'carried' in case:
    #the Sun held at the origin and Jupiter circling it (engine/carried.py's flows: a body held still has no region
    #falling with it, but the Sun's is the one region the light doesn't pass through)
    a = -W*T0
    return [Body(MS), Body(MJ, XJ*math.cos(a), XJ*math.sin(a), circling=W)]
  if 'at rest' in case:
    return [Body(MS, -MU*DJ, 0.0), Body(MJ, XJ, 0.0)]
  a = -W*T0
  return [Body(MS, -MU*DJ*math.cos(a), -MU*DJ*math.sin(a), circling=W),
          Body(MJ, XJ*math.cos(a), XJ*math.sin(a), circling=W)]


def spacetime(case):
  B = bodies(case)
  if case.startswith('GR'):
    return PostNewtonian(B)
  if case.startswith('carried'):
    from engine.carried import CarriedSpacetime
    return CarriedSpacetime(B, transverse='source' if 'space from u' in case else False)
  flow = (SpecialFlowCalculator(B, 2, combine='turning') if case.startswith('turning')
          else SpecialFlowCalculator(B, 2, direction='eikonal-exact'))
  return FlowSpacetime(flow, transverse='source') if 'space from u' in case else FlowSpacetime(flow)


def observer():
  return np.array([XJ + REFERENCE*RJ, H])


def emitter(b):
  """the emitter for the ray passing Jupiter at about b: the straight line from it to the observer crosses y = 0
  there"""
  return np.array([2*(XJ + b) - observer()[0], -H])


def trace(S, start, angle, fraction=0.002):
  """light from start (at t = 0), its velocity through the coordinates at angle from +y: where it crosses y = H, and
  its velocity and the time there"""
  calc = MetricCalculator(S)
  p = Particle()
  p.pos = np.array(start, float)
  calc.initLight(p, np.array([-math.sin(angle), math.cos(angle)]))
  while True:
    before = (p.pos.copy(), p.t)
    calc.move(p, min(calc.stepSize(p, fraction, 0.01*AU/C), max((H - p.pos[1])/C, 1.0)))
    if p.pos[1] >= H:
      s = (H - before[0][1])/(p.pos[1] - before[0][1])
      return before[0] + s*(p.pos - before[0]), p.v.copy(), before[1] + s*(p.t - before[1]), calc.sideOf(p)


def shoot(S, b):
  """the ray from b's emitter that reaches the observer: its velocity, time and region there"""
  start, target = emitter(b), observer()[0]
  d = observer() - start
  guess = math.atan2(-d[0], d[1])
  angles, misses = [guess, guess + 1e-6], []
  for a in angles:
    misses.append(trace(S, start, a)[0][0] - target)
  for _ in range(12):
    a = angles[-1] - misses[-1]*(angles[-1] - angles[-2])/(misses[-1] - misses[-2])
    x, v, t, side = trace(S, start, a)
    angles.append(a)
    misses.append(x[0] - target)
    if abs(misses[-1]) < 0.05:
      return v, t, side, misses[-1]
  return v, t, side, misses[-1]


def ray(job):
  case, b = job
  return job, shoot(spacetime(case), b*RJ)


def signedAngle(a, b, g=None):
  """the angle from direction a to direction b, measured with the metric g (2 x 2; flat if None)"""
  g = np.eye(2) if g is None else g
  return math.atan2(math.sqrt(np.linalg.det(g))*(a[0]*b[1] - a[1]*b[0]), a @ g @ b)


def aberrate(n, beta):
  """the direction of light going along unit n (in a frame) seen by an observer moving at beta (v/c) through it"""
  b2 = beta @ beta
  g = 1/math.sqrt(1 - b2)
  nb = n @ beta
  m = n + ((g - 1)*nb/b2 - g)*beta if b2 > 0 else n
  return m/(g*(1 - nb))


def measured(case, rays):
  """the angle from the reference ray to each near ray, at the observer, in the model and in GR (uas)"""
  S = spacetime(case)
  out = {}
  for b in NEAR:
    vRef, tRef, sideRef, _ = rays[(case, REFERENCE)]
    v, t, side, _ = rays[(case, b)]
    x = observer()
    u = S.flow(x, tRef, sideRef)
    h = S.space(x, tRef, sideRef)
    g = np.eye(2) if h is None else np.eye(2) + h
    model = signedAngle(vRef - u, v - S.flow(x, t, side), g)
    gr = CASES[case]
    gv, gRef = rays[(gr, b)][0], rays[(gr, REFERENCE)][0]
    beta = u/C
    grAngle = signedAngle(aberrate(gRef/np.linalg.norm(gRef), beta), aberrate(gv/np.linalg.norm(gv), beta))
    out[b] = (model*UAS, grAngle*UAS)
  return out


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'lightTwoRays_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  cases = list(CASES) + sorted(set(CASES.values()))
  jobs = [(c, b) for c in cases for b in NEAR + (REFERENCE,)]
  with Pool(8) as pool:
    rays = dict(pool.map(ray, jobs))
  lines = ['light past Jupiter, the Sun 5.2 AU away: the angle at one observer between a ray passing Jupiter at b and'
           ' one at %d R_J, the emitters and the observer %.1f AU either side; the model\'s against GR\'s for the same'
           ' observer (moving with the model\'s space there); VLBI to 10 uas' % (REFERENCE, H/AU)]
  worst = max(abs(r[3]) for r in rays.values())
  lines.append('  the rays reach the observer to %.2f m' % worst)
  for case in CASES:
    m = measured(case, rays)
    lines.append('  %-38s %s' % (case, '   '.join('%d R_J: %+.2f uas off GR (GR %.1f)' % (b, m[b][0] - m[b][1], m[b][1])
                                                for b in NEAR)))
  print('\n'.join(lines), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
