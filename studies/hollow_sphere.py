"""
the Hollow Sphere page (docs/part2/hollow-sphere.md): something falling from rest far away straight through a hollow
shell (mass M, radius R) and out the other side, along the x axis, in four flows that each move space inside at the
surface's escape speed u_R = sqrt(2GM/R) (so clocks held still inside run at sqrt(1 - rs/R), as in general relativity)
and differ only in direction along the line:

  A  inside, space carries on as it came in (+x, the faller's way)
  B  inside, it flows as on the far side (-x, against the faller)
  C  towards the centre from both sides
  D  out from the centre both ways

outside, space falls in at sqrt(2GM/|x|), as round a single body. each is run two ways:

  smooth    the shell SHELL thick, the flow changing linearly across it (and, for C and D, across CENTRE round the
            centre), followed by the flow calculator's momentum step - the paths of ds^2 = -c^2 dt^2 + (dx - u dt)^2.
            something moving with the space is carried into wherever the flow meets itself head on, and stalls there
  boundary  the flow jumps at the shell (and the centre), and at each jump the faller changes reference frame: it
            lands on the boundary, keeps its velocity relative to the boundary (which is at rest), and carries on in
            the space on the other side - w' = (v_b - u')/(1 - v_b u'/c^2), v_b = (w + u)/(1 + w u/c^2) its velocity
            relative to the boundary, u and u' the flow either side. each side's flow is used only on its own side,
            so no step straddles a jump

measured, against exact general relativity (the fall from rest far away to the shell, and the climb back out, each
fallTime; across the inside 2R sqrt(1 - rs/R)/u_R, space inside the shell flat): where the faller stops, if it does;
its proper time to the shell, across the inside, from the shell out to +START, and in all; and the flow's time.
the flow model's prediction across the inside is 2R/u_R in every option (the faller passes the shell at the escape
speed, across a diameter that observers held still inside measure as 2R/sqrt(1 - u_R^2/c^2) in flat flowing space) -
longer than general relativity's by 1/sqrt(1 - rs/R), which curved space removes

writes logs/hollowSphere/hollowSphere_<datetime>/: summary.log, a csv for each run, and two viewer files (x against t):
hollowSphere_smooth.full.json and hollowSphere_boundary.full.json

run: python3 studies/hollow_sphere.py
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))                     #studies/, for the helpers
import numpy as np
from engine.flow import Body, SpecialFlowCalculator, Particle
from engine.logger import LOG_DIR
from engine.constants import *
from engine.exact import schwarzschildRadius, fallTime
from part1_examples import write
from two_body_escapes import writeViewerFiles

MASS = MS
RS = schwarzschildRadius(MASS)
R = 10*RS                 #the shell's radius: space inside moves at sqrt(0.1) c = 0.316c
SHELL = 1e-3*R            #its thickness, smooth
CENTRE = 1e-3*R           #C and D turn round across this, either side of the centre, smooth
START = 6*R               #the faller passes -START moving with the flow (as having fallen from rest far away), followed to +START
STEP = 1e-4               #steps move about this fraction of the distance to the nearest feature
EVERY = 200              #steps between csv rows (the steps are fine; the viewer needs far fewer)
HOLD = 0.0066             #a stalled faller is drawn held where it stopped until this time (s), for the viewer
GM = G*MASS
UR = math.sqrt(2*GM/R)
OPTIONS = {'A': (1, 1), 'B': (-1, -1), 'C': (1, -1), 'D': (-1, 1)}   #the flow inside, left half and right half (x u_R)
COLOURS = {'A': '#2a78d6', 'B': '#e34948', 'C': '#1baf7a', 'D': '#eda100'}
COLUMNS = ['t', 'pt', 'pos_x', 'pos_y', 'v_x', 'v_y']
X_T = lambda colour, style='solid': {'pos_x / t': [colour, style, colour]}


def outside(x):
  """the flow outside the shell, in towards it (extended past R for the boundary mode's own side)"""
  return -math.copysign(1, x)*math.sqrt(2*GM/abs(x))


class ShellFlow(SpecialFlowCalculator):
  """the flow along the x axis round and through the shell, smooth, or in zones the faller crosses one at a time"""

  def __init__(self, option, smooth=True):
    super().__init__([Body(MASS)], order=2)
    self.halves = OPTIONS[option]
    self.smooth = smooth
    self.split = self.halves[0] != self.halves[1]
    self.bounds = [-R, 0.0, R] if self.split else [-R, R]     #the boundary mode's jumps
    self.zone = 0                                             #which zone the faller is in (boundary mode)

  def inside(self, x):
    return UR*self.halves[0 if x < 0 else 1]

  def zoneFlow(self, zone, x):
    """the flow of zone (0, the left outside, to len(bounds), the right outside), at x, wherever x is"""
    if zone == 0:
      return outside(-abs(x))
    if zone == len(self.bounds):
      return outside(abs(x))
    middle = (self.bounds[zone - 1] + self.bounds[zone])/2
    return self.inside(middle)

  def along(self, x):
    """u along x"""
    if not self.smooth:
      return self.zoneFlow(self.zone, x)
    a = abs(x)
    if a >= R + SHELL:
      return outside(x)
    if a <= CENTRE and self.split:                                       #C, D: turning round across the centre
      return self.inside(CENTRE)*x/CENTRE
    inner = self.inside(x)
    if a <= R:
      return inner
    f = (a - R)/SHELL                                                     #across the shell
    return (1 - f)*inner + f*outside(math.copysign(R + SHELL, x))

  def flow(self, pos, region=None, t=0.0):
    return np.array([self.along(float(pos[0])), 0.0])

  def cross(self, p):
    """at a boundary (boundary mode): into the next zone, keeping the velocity relative to the boundary"""
    u, w = self.zoneFlow(self.zone, float(p.pos[0])), float(p.w[0])
    vb = (w + u)/(1 + w*u/C**2)                                           #relative to the boundary, at rest
    self.zone += 1
    u2 = self.zoneFlow(self.zone, float(p.pos[0]))
    w2 = (vb - u2)/(1 - vb*u2/C**2)
    p.w = np.array([w2, 0.0])
    p.u = np.array([u2, 0.0])
    p.v = p.w + p.u


def stepAt(x, v):
  """a step moving about STEP of the distance to the nearest place the flow changes"""
  near = min(abs(abs(x) - R), abs(abs(x) - R - SHELL), abs(x))
  return STEP*max(near, 0.5*SHELL)/max(abs(v), 1e-3*UR)


def fall(option, smooth=True):
  """from -START to +START, or until it stalls: rows, (proper time, flow time, v, w) at each mark, steps, and how
  it ended"""
  calc = ShellFlow(option, smooth)
  p = Particle()
  p.pos = np.array([-START, 0.0])
  calc.initPFreefall(p)
  rows, marks, steps = [(p.t, p.pt, *p.pos, *p.v)], {}, 0
  targets = sorted(set([-R, R, START] + ([] if smooth else calc.bounds)))
  slow, why, furthest = 0, 'reached +START', -START
  while p.pos[0] < START - 1e-9*R:
    x = float(p.pos[0])
    nxt = next(T for T in targets if T > x + 1e-9*R)
    dt = stepAt(x, p.v[0])
    if p.v[0] > 0 and x + p.v[0]*dt > nxt:                               #land on the next mark
      dt = (nxt - x)/p.v[0]
    calc.move(p, dt)
    steps += 1
    if not np.all(np.isfinite(p.pos)):
      why = 'failed: the position stopped being a number at x = %.7f R' % (x/R)
      break
    if abs(p.pos[0] - nxt) < 1e-7*R:
      p.pos = np.array([nxt, 0.0])
      if nxt not in marks:
        marks[nxt] = (p.pt, p.t, float(p.v[0]), float(p.w[0]))
      if not smooth and nxt in calc.bounds:
        calc.cross(p)
        p.pos = np.array([nxt + 1e-9*R, 0.0])    #just past it (the step's differences are scaled by the distance to the centre)
        rows.append((p.t, p.pt, *p.pos, *p.v))
    if steps % EVERY == 0:
      rows.append((p.t, p.pt, *p.pos, *p.v))
    #stalled: creeping to a stop
    if p.pos[0] > furthest + 1e-9*R:
      furthest, slow = float(p.pos[0]), 0
    else:
      slow += 1
    if slow > 2000 or (steps > 200 and p.v[0] < 1e-6*UR):
      why = 'stalled at x = %.7f R, moving at %.1e c, with w %.4f c' % (p.pos[0]/R, p.v[0]/C, p.w[0]/C)
      break
  if np.all(np.isfinite(p.pos)):
    rows.append((p.t, p.pt, *p.pos, *p.v))
  if why.startswith('stalled'):
    #held where it stopped, for the viewer: at rest there (its clock running at the flow's rate, w = 0), to HOLD
    t, pt, x = p.t, p.pt, float(p.pos[0])
    rows += [(T, pt + (T - t), x, 0.0, 0.0, 0.0) for T in np.linspace(t, max(HOLD, t), 20)[1:]]
  return rows, marks, steps, why


def csvRows(path):
  import csv
  with open(path) as f:
    return [[float(v) for v in row] for row in list(csv.reader(f))[1:] if row]


def main():
  folder = os.path.join(LOG_DIR, 'hollowSphere', 'hollowSphere_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  fallIn = fallTime(GM, START, R)
  model = 2*R/UR
  gr = 2*R*math.sqrt(1 - RS/R)/UR
  lines = ['a hollow shell of %g solar mass, radius %g m = %g rs; space inside at u_R = %.6f c' % (MASS/MS, R, R/RS, UR/C),
           'the faller from rest far away, from -%g R to +%g R' % (START/R, START/R),
           'exact GR: in to the shell %.9f s, across the inside %.9f s, out again %.9f s, in all %.9f s (proper time)'
           % (fallIn, gr, fallIn, 2*fallIn + gr),
           'the flow model across the inside: 2R/u_R = %.9f s, %.4f%% longer than GR' % (model, 100*(model/gr - 1))]
  views = {}
  for smooth in (True, False):
    lines += ['', 'the shell smooth (%g m thick): the flow\'s own paths' % SHELL if smooth else
              'the flow jumping at the shell (and centre), crossed by changing reference frame']
    made = []
    for option in OPTIONS:
      rows, marks, steps, why = fall(option, smooth)
      out = ['  %s  %s; %d steps' % (option, why, steps)]
      if -R in marks:
        out.append('     in to the shell: proper time %.9f s (exact %.9f, - 1 %.1e)' % (marks[-R][0], fallIn,
                                                                                         marks[-R][0]/fallIn - 1))
      if -R in marks and R in marks:
        inside = marks[R][0] - marks[-R][0]
        out.append('     across the inside: proper time %.9f s (the model\'s 2R/u_R - 1 %.1e; GR - 1 %.2e), flow time %.9f s'
                   % (inside, inside/model - 1, inside/gr - 1, marks[R][1] - marks[-R][1]))
      if R in marks and START in marks:
        outLeg = marks[START][0] - marks[R][0]
        total = marks[START][0]
        out.append('     out from the shell: proper time %.9f s (exact %.9f, - 1 %.1e)' % (outLeg, fallIn, outLeg/fallIn - 1))
        out.append('     the whole trip: proper time %.9f s (GR %.9f, - 1 %.2e; the model with 2R/u_R inside, - 1 %.1e),'
                   ' flow time %.6f s' % (total, 2*fallIn + gr, total/(2*fallIn + gr) - 1,
                                         total/(2*fallIn + model) - 1, marks[START][1]))
      lines += out
      print('\n'.join(out), flush=True)
      made.append((write(folder, 'fall%s_%s' % (option, 'smooth' if smooth else 'boundary'), ShellFlow(option, smooth),
                         rows, COLUMNS, ['option %s: falling from rest far away through a hollow shell' % option] + out),
                   COLOURS[option], 'solid'))
    views['smooth' if smooth else 'boundary'] = made
  for name, made in views.items():
    #the shell's walls, as lines at x = -R and +R through the run
    end = max(max(r[0] for r in csvRows(path)) for path, *_ in made)
    for side in (-1, 1):
      made.append((write(folder, 'wall%s_%s' % ('L' if side < 0 else 'R', name), ShellFlow('A'),
                         [(t, t, side*R, 0.0, 0.0, 0.0) for t in (0.0, end)], COLUMNS, ['the shell\'s wall at x = %+g R' % side]),
                   '#b8b8b8', 'solid'))
    writeViewerFiles(folder, 'hollowSphere_' + name, made, selection=(('pos_x', 't'),), styles=X_T,
                     preferences={'equalAspect': False, 'showBodies': False, 'showSchwarzschild': False,
                                  'showFlow': False, 'showPathLegend': False})
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines[:4]))
  print('written to', folder)


if __name__ == '__main__':
  main()
