"""
escape paths from two black holes of one solar mass each, 1 AU apart (at x = -0.5 AU and +0.5 AU), under newtonian
gravity alone (the combined g of both, RK4: engine/flow_lines.py)

30 paths from each hole, equally spaced in angle (the first heading along +x); each starts 1.5 Schwarzschild radii
(1.5 x 2GM/c^2) from its hole's centre at the escape speed there - |u| from Calculator.flow, for both holes - heading
straight away from that hole, and runs until it is 10 AU from the origin (the centre of mass), comes within
1.5 Schwarzschild radii of a hole, or reaches the step limit

writes logs/twoBodyEscapes/twoBodyEscapes_<datetime>/: for each hole a csv (its 30 paths, an empty row ending each)
and a log (the bodies, and where and when each path ended), and twoBodyEscapes.full.json (with its .prefs.json and
.config.json) to open both in the viewer, coloured by the hole they leave

run: python3 studies/two_body_escapes.py      (then: python3 viewer/csv_viewer.py logs/twoBodyEscapes/twoBodyEscapes_<datetime>/twoBodyEscapes.full.json)
"""
import csv
import json
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Calculator
from engine.logger import Log, LOG_DIR
from engine.constants import *
from engine.flow_lines import line

SEP = 0.5*AU          #holes at (-SEP, 0) and (+SEP, 0)
PATHS = 30            #paths from each hole
START = 1.5           #paths start this many Schwarzschild radii from their hole's centre
REACH = 10*AU         #and stop this far from the origin
STEP = 0.002          #each step moves about this fraction of the distance to the nearest hole
EVERY = 10            #steps between csv rows

BODIES = [Body(MS, -SEP, 0.0), Body(MS, SEP, 0.0)]
COLOURS = ['#2a78d6', '#eb6834']   #paths from the left hole, and from the right


def escapes(folder, calc, i):
  """the paths from hole i: a csv and a log in folder; returns the csv's path"""
  home = BODIES[i]
  name = 'from%s' % ('Left' if i == 0 else 'Right')
  start = START*2*G*home.mass/C**2
  log = Log(name, True, False, folder)
  calc.log = log
  log.logBodies(calc)
  log.print('%d paths from body %d, starting %g m (%g Schwarzschild radii) out at the escape speed |u|, heading away'
            ' from its centre, under newtonian g' % (PATHS, i + 1, start, START))
  log.print('stop: within %g m of a body, %g AU from the origin, or the step limit' % (start, REACH/AU))
  log.print()
  log.print('  %6s %8s %-20s %-22s %12s %12s' % ('angle', 'steps', 'end (AU)', 'stopped', 'days', '|v| km/s'))
  ends = {}
  path = log.file.name[:-4] + '.csv'
  with open(path, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'pos_x', 'pos_y', 'v_x', 'v_y'])
    for n in range(PATHS):
      angle = 2*math.pi*n/PATHS
      rows, reason, steps = line(calc, home, angle, start, REACH, STEP, EVERY)
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
  print('%-10s %s' % (name, ', '.join('%d %s' % (count, reason) for reason, count in sorted(ends.items()))))
  return path


def writeViewerFiles(folder, name, made):
  """a full config for the viewer in folder: <name>.full.json naming its .prefs.json and .config.json, for the
  csvs in made, [(path, colour)]; prints how to open it"""
  results = [{'path': path, 'relative': os.path.basename(path), 'visible': True, 'straight': False, 'ends': False,
              'periapsis': False, 'apoapsis': False, 'styles': {'pos': [colour, 'solid', colour]},
              'selection': [['pos_x', 'pos_y']], 'group': None, 'hiddenOrbits': []} for path, colour in made]
  config = {'kind': 'config', 'version': 1, 'results': results, 'selected': made[0][0], 'background': None, 'timeInterval': ''}
  prefs = {'kind': 'preferences', 'version': 1, 'preferences': {'mode': 'xy', 'equalAspect': True, 'showFlow': False,
           'showTimeMarks': False, 'showMarkers': False, 'showBodies': True, 'showPathLegend': True, 'showFieldKey': True}}
  full = {'kind': 'full', 'version': 1, 'preferences': name + '.prefs.json', 'config': name + '.config.json'}
  for ext, doc in (('.config.json', config), ('.prefs.json', prefs), ('.full.json', full)):
    with open(os.path.join(folder, name + ext), 'w') as f:
      json.dump(doc, f, indent=2)
  print('open with: python3 viewer/csv_viewer.py', os.path.relpath(os.path.join(folder, name + '.full.json'), os.path.dirname(LOG_DIR)))


def main():
  folder = os.path.join(LOG_DIR, 'twoBodyEscapes', 'twoBodyEscapes_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  calc = Calculator(BODIES)
  made = [(escapes(folder, calc, i), COLOURS[i]) for i in range(len(BODIES))]
  writeViewerFiles(folder, 'twoBodyEscapes', made)
  return folder


if __name__ == '__main__':
  main()
