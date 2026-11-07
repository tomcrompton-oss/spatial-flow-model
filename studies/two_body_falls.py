"""
falls into two black holes of one solar mass each, 1 AU apart (the holes of studies/two_body_escapes.py), under
newtonian gravity alone (the combined g of both, RK4)

30 paths starting 10 AU from the origin (the centre of mass), equally spaced in angle (the first on the +x axis),
each moving at the flow speed there - |u| from Calculator.flow, for both holes, the escape speed - straight towards
the origin; each runs until it comes within 1.5 Schwarzschild radii of a hole, gets back out past 10 AU, or reaches
the step limit

writes logs/twoBodyFalls/twoBodyFalls_<datetime>/: a csv (the 30 paths, an empty row ending each) and a log (the
bodies, and where and when each path ended), and twoBodyFalls.full.json (with its .prefs.json and .config.json) to
open it in the viewer

run: python3 studies/two_body_falls.py      (then: python3 viewer/csv_viewer.py logs/twoBodyFalls/twoBodyFalls_<datetime>/twoBodyFalls.full.json)
"""
import csv
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Calculator
from engine.logger import Log, LOG_DIR
from engine.constants import *
from engine.integrate import rk4Gravity
from studies.two_body_escapes import BODIES, START, REACH, STEP, EVERY, writeViewerFiles

PATHS = 30            #starting points round the 10 AU circle
MAX_STEPS = 200000    #paths stop after this many steps
COLOUR = '#1baf7a'


def fall(calc, angle, near):
  """
  one path from REACH at angle (radians), at |u| towards the origin, under g; it stops within near (m) of a body,
  back out past REACH, or at MAX_STEPS. returns the rows (t, pos, v) every EVERY steps, why it stopped and the steps
  """
  pos = REACH*np.array([math.cos(angle), math.sin(angle)])
  v = -np.linalg.norm(calc.flow(pos))*pos/REACH
  t = 0.0
  rows = [(t, pos, v)]
  for i in range(1, MAX_STEPS + 1):
    nearest = min(np.linalg.norm(pos - b.pos) for b in calc.bodies)
    dt = STEP*nearest/np.linalg.norm(v)
    pos, v = rk4Gravity(calc, pos, v, dt)
    t += dt
    reason = None
    for n, b in enumerate(calc.bodies):
      if np.linalg.norm(pos - b.pos) < near:
        reason = 'reached body %d' % (n + 1)
    if np.linalg.norm(pos) > REACH:
      reason = 'back out past %g AU' % (REACH/AU)
    if reason or i % EVERY == 0:
      rows.append((t, pos, v))
    if reason:
      return rows, reason, i
  return rows, 'step limit', MAX_STEPS


def main():
  folder = os.path.join(LOG_DIR, 'twoBodyFalls', 'twoBodyFalls_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  calc = Calculator(BODIES)
  near = START*2*G*BODIES[0].mass/C**2
  log = Log('falls', True, False, folder)
  calc.log = log
  log.logBodies(calc)
  log.print('%d paths from %g AU, at the flow speed |u| there, straight towards the centre of mass, under newtonian g'
            % (PATHS, REACH/AU))
  log.print('stop: within %g m (%g Schwarzschild radii) of a body, back out past %g AU, or the step limit' % (near, START, REACH/AU))
  log.print()
  log.print('  %6s %8s %-20s %-22s %12s %12s' % ('angle', 'steps', 'end (AU)', 'stopped', 'days', '|v| km/s'))
  ends = {}
  path = log.file.name[:-4] + '.csv'
  with open(path, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'pos_x', 'pos_y', 'v_x', 'v_y'])
    for n in range(PATHS):
      angle = 2*math.pi*n/PATHS
      rows, reason, steps = fall(calc, angle, near)
      t, pos, v = rows[-1]
      ends[reason] = ends.get(reason, 0) + 1
      log.print('  %6.0f %8d %-20s %-22s %12.2f %12.4g' % (math.degrees(angle), steps, '(%.4f, %.4f)' % (pos[0]/AU, pos[1]/AU),
                                                          reason, t/DAY, np.linalg.norm(v)/1000))
      for t, pos, vel in rows:
        out.writerow([t, pos[0], pos[1], vel[0], vel[1]])
      out.writerow([''] * 5)   #an empty row ends the path
  log.print()
  for reason, count in sorted(ends.items()):
    log.print('%d %s' % (count, reason))
  log.close()
  print(', '.join('%d %s' % (count, reason) for reason, count in sorted(ends.items())))
  writeViewerFiles(folder, 'twoBodyFalls', [(path, COLOUR)])
  return folder


if __name__ == '__main__':
  main()
