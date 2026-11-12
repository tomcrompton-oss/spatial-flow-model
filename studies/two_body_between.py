"""
a particle travelling from one hole to the other, with the flow of space pointing different ways - the flow's
magnitude is as always (sqrt of the sum of 2GM/d over the bodies), only its direction is set (Calculator.direction)

the two holes of studies/two_body_escapes.py (one solar mass each, at x = -0.5 AU and +0.5 AU); the particle starts
2 Schwarzschild radii from the left hole's centre, on the line between them, moving at W (relative to the space it
is in, w) straight at the right hole, and moves the flow model's way (SpecialFlowCalculator, second order) until it
is 2 Schwarzschild radii from the right hole, falls back into the left one's horizon, is 10 AU from the centre of
mass, or reaches the step limit. W = 0.95c is just over what it takes to get out with the flow along g (0.943c)

the flow points
  left      to the left (-x) everywhere
  down      from top to bottom (-y) everywhere
  nearest   towards the nearest body - flipping half way
  centre    towards the centre of mass - the reverse of nearest, between the holes
  g         (for comparison, in the log only) along g - on the line between the holes the same as nearest
  eikonal, eikonal-exact   (in the log only) down the eikonal flow's zero-energy paths, from tables and exact (the
            default for two bodies) - on the line between the holes the same as nearest too

writes logs/twoBodyBetween/twoBodyBetween_<datetime>/: a csv and log for each, a comparison (comparison.log), and
twoBodyBetween.full.json to open them in the viewer (whose flow background is always along g), and
twoBodyBetweenTimes.full.json: x against coordinate and proper time for the three that stay on the line between

run: python3 studies/two_body_between.py      (then: python3 viewer/csv_viewer.py logs/twoBodyBetween/twoBodyBetween_<datetime>/twoBodyBetween.full.json)
"""
import csv
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import SpecialFlowCalculator, Particle
from engine.logger import Log, LOG_DIR
from engine.constants import *
from engine.vectors import length
from two_body_escapes import BODIES, REACH, writeViewerFiles

W = 0.95*C            #the starting speed relative to space
START = 2             #start and finish this many Schwarzschild radii from a hole's centre
STEP = 0.0005         #each step moves about this fraction of the distance to the nearest hole
EVERY = 20            #steps between csv rows
MAX_STEPS = 2000000

DIRECTIONS = [   #(name, Calculator.direction, colour)
  ('left', (-1.0, 0.0), '#2a78d6'),
  ('down', (0.0, -1.0), '#eb6834'),
  ('nearest', 'nearest', '#1baf7a'),
  ('centre', 'centre', '#8a5cd8'),
  ('g', 'g', None),
  ('eikonal', 'eikonal', None),
  ('exact', 'eikonal-exact', None),
]


def travel(calc):
  """the run from the left hole towards the right: the rows (t, pt, pos, v, w, u), why it stopped, the steps"""
  left, right = calc.bodies
  rs = 2*G*left.mass/C**2
  p = Particle()
  p.pos = left.pos + np.array([START*rs, 0.0])
  calc.initPW(p, W*(right.pos - left.pos)/length(right.pos - left.pos))
  row = lambda: (p.t, p.pt, p.pos.copy(), p.v.copy(), p.w.copy(), p.u.copy())
  rows = [row()]
  for i in range(1, MAX_STEPS + 1):
    calc.move(p, calc.stepSize(p, STEP))
    reason = None
    if not np.all(np.isfinite(p.pos)):
      return rows, 'not a number', i
    if length(p.pos - right.pos) < START*rs:
      reason = 'arrived'
    elif length(p.pos - left.pos) < rs:
      reason = 'fell back'
    elif length(p.pos) > REACH:
      reason = '%g AU out' % (REACH/AU)
    if reason or i % EVERY == 0:
      rows.append(row())
    if reason:
      return rows, reason, i
  return rows, 'step limit', MAX_STEPS


def run(folder, name, direction):
  """one direction: its csv and log in folder; returns the csv's path and a summary"""
  calc = SpecialFlowCalculator(BODIES, 2, direction)
  log = Log(name, True, False, folder)
  calc.log = log
  log.logBodies(calc)
  log.print('from %g Schwarzschild radii from body 1 at |w| = %gc towards body 2, the flow model (second order),'
            ' steps of %g of the distance to the nearest body' % (START, W/C, STEP))
  rows, reason, steps = travel(calc)
  path = log.file.name[:-4] + '.csv'
  with open(path, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'proper_t', 'pos_x', 'pos_y', 'v_x', 'v_y', 'w_x', 'w_y', 'u_x', 'u_y'])
    for t, pt, pos, v, w, u in rows:
      out.writerow([t, pt, pos[0], pos[1], v[0], v[1], w[0], w[1], u[0], u[1]])
  t, pt, pos, v, w, u = rows[-1]
  speeds = [length(v)/C for _, _, _, v, _, _ in rows]
  middle = min(rows, key=lambda r: abs(r[2][0]))   #the row nearest the middle (x = 0)
  summary = {'name': name, 'direction': calc.describeDirection(), 'reason': reason, 'steps': steps, 't': t, 'pt': pt,
             'end': pos/AU, 'v': length(v)/C, 'w': length(w)/C, 'vmax': max(speeds), 'vmin': min(speeds),
             'vmid': length(middle[3])/C, 'wmid': length(middle[4])/C, 'drift': max(abs(r[2][1]) for r in rows)/AU}
  log.print('stopped: %s after %d steps, t %.2f s, proper time %.2f s, at (%.4f, %.4f) AU, |v| %.4fc, |w| %.4fc'
            % (reason, steps, t, pt, pos[0]/AU, pos[1]/AU, summary['v'], summary['w']))
  log.close()
  return path, summary


def main():
  folder = os.path.join(LOG_DIR, 'twoBodyBetween', 'twoBodyBetween_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  made, summaries = [], []
  for name, direction, colour in DIRECTIONS:
    path, summary = run(folder, name, direction)
    summaries.append(summary)
    if colour:
      made.append((path, colour))
  head = '%-8s %-28s %-9s %9s %10s %10s %8s %8s %8s %8s %8s %10s' % (
    'flow', 'direction', 'stopped', 'steps', 't (s)', 'proper (s)', '|v| mid', '|w| mid', '|v| end', '|w| end',
    '|v| max', 'off axis')
  lines = ['particle from 2 Schwarzschild radii from the left hole at |w| = %gc towards the right one' % (W/C), '', head]
  for s in summaries:
    lines.append('%-8s %-28s %-9s %9d %10.2f %10.2f %7.4fc %7.4fc %7.4fc %7.4fc %7.4fc %7.3g AU' % (
      s['name'], s['direction'][:28], s['reason'], s['steps'], s['t'], s['pt'], s['vmid'], s['wmid'], s['v'], s['w'],
      s['vmax'], s['drift']))
  with open(os.path.join(folder, 'comparison.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines))
  writeViewerFiles(folder, 'twoBodyBetween', made)
  #the three along the line between the holes lie on top of each other there: x against the time taken instead,
  #coordinate time solid, proper time dashed
  writeViewerFiles(folder, 'twoBodyBetweenTimes', [m for m in made if 'down' not in os.path.basename(m[0])],
                   [('pos_x', 't'), ('pos_x', 'proper_t')],
                   lambda colour: {'pos_x / t': [colour, 'solid', colour], 'pos_x / proper_t': [colour, 'dashed', colour]},
                   {'equalAspect': False, 'showBodies': False})
  return folder


if __name__ == '__main__':
  main()
