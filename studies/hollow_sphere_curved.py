"""
the Curved Space page (docs/part2/curved-space.md): the hollow shell of studies/hollow_sphere.py in the model with
curved space (engine/metric.py), N = 1.
inside, space is shortened along the line by a^2 = 1 - rs/R and flows at sqrt(rs/R)/a (coordinate speed), so that
observers held still inside see flat space (diameter 2R) and clocks at sqrt(1 - rs/R): general relativity's inside.
outside, the one-body flow, flat. the shell (SHELL thick) and, for C and D, the centre, change smoothly.
the faller: from rest far away (moving with the space), along x. measured: where it stalls, and the proper time
across the inside, against general relativity's 2R sqrt(1 - rs/R)/u_R; and the same with space flat (studies/hollow_sphere.py's flat flow,
in this engine). the faller isn't taken across the boundaries here (it stalls where the flow meets itself, as in
hollow_sphere.py's smooth runs): option A, which crosses the inside first, gives the crossing time

run: python3 studies/hollow_sphere_curved.py      (prints; a few minutes)
"""
import math, sys, time
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
import numpy as np
from engine.constants import *
from engine.flow import Body, Particle
from engine.metric import Spacetime, MetricCalculator
from engine.exact import schwarzschildRadius, fallTime

M = MS
RS = schwarzschildRadius(M)
GM = G*M
R = 10*RS
SHELL = 0.05*R
CENTRE = 0.05*R
START = 50*R
A2 = 1 - RS/R
UIN = math.sqrt(RS/R)*C/math.sqrt(A2)       #the flow inside, in coordinates
UR = math.sqrt(2*GM/R)
OPT = {'A': lambda x: 1.0, 'B': lambda x: -1.0, 'C': lambda x: -math.copysign(1, x), 'D': lambda x: math.copysign(1, x)}


class Shell(Spacetime):
  def __init__(self, option, curved=True):
    self.bodies = [Body(M)]
    self.dirn = OPT[option]
    self.curved = curved

  def mix(self, x):
    """0 inside, 1 outside, linear across the shell"""
    return min(max((abs(x) - R)/SHELL, 0.0), 1.0)

  def along(self, x):
    out = -math.copysign(1, x)*math.sqrt(2*GM/max(abs(x), R + SHELL))
    d = self.dirn(x)
    if self.dirn(-1) != self.dirn(1) and abs(x) < CENTRE:
      d = self.dirn(CENTRE)*x/CENTRE
    inner = d*(UIN if self.curved else UR)
    f = self.mix(x)
    return (1 - f)*inner + f*out

  def flow(self, x, t, region=None):
    return np.array([self.along(float(x[0])), 0.0])

  def space(self, x, t, region=None):
    if not self.curved:
      return None
    f = self.mix(float(x[0]))
    return np.array([[(1 - f)*(A2 - 1), 0.0], [0.0, 0.0]])


def run(option, curved=True, limit=120):
  st = Shell(option, curved)
  calc = MetricCalculator(st)
  p = Particle()
  p.pos = np.array([-START, 0.0])
  calc.initPV(p, st.flow(p.pos, 0.0))                 #moving with the space
  marks, furthest, still, t0 = {}, -START, 0, time.time()
  targets = [-R, R, START]
  while p.pos[0] < START and time.time() - t0 < limit:
    x = float(p.pos[0])
    near = min(abs(abs(x) - R), abs(abs(x) - R - SHELL), abs(x))
    dt = 1e-3*max(near, 0.02*SHELL)/C
    nxt = next(T for T in targets if T > x + 1e-9*R)
    if p.v[0] > 0 and x + p.v[0]*dt > nxt:
      dt = (nxt - x)/p.v[0]
    calc.move(p, dt)
    if abs(p.pos[0] - nxt) < 1e-6*R and nxt not in marks:
      marks[nxt] = (p.pt, p.t)
    if p.pos[0] > furthest + 1e-7*R:
      furthest, still = float(p.pos[0]), 0
    else:
      still += 1
    if still > 3000:
      break
  where = 'reached +START' if p.pos[0] >= START else 'stalled at x = %.5f R (v %.1e c)' % (p.pos[0]/R, p.v[0]/C)
  inside = marks[R][0] - marks[-R][0] if (R in marks and -R in marks) else None
  return where, marks, inside


gr = 2*R*math.sqrt(1 - RS/R)/UR
flat = 2*R/UR
print('shell at 10 rs; inside crossing: GR %.9f s, the flat flow model %.9f s' % (gr, flat))
print('fall to -R exact %.6f s' % fallTime(GM, START, R))
for curved in (True, False):
  print('curved space inside' if curved else 'flat (the flow model as it is)')
  for option in 'ABCD':
    where, marks, inside = run(option, curved)
    extra = '' if inside is None else '; inside %.9f s (GR - 1: %.2e)' % (inside, inside/gr - 1)
    reach = '' if -R not in marks else '; -R at proper time %.6f' % marks[-R][0]
    print('  %s: %s%s%s' % (option, where, reach, extra), flush=True)
