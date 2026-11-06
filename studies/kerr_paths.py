"""
paths to look at in the viewer: orbits and light past a rotating hole (KerrFlowCalculator, spin 0.9) and the same
starts past a non-rotating one, for a 4e6 MS hole (sizes in M = GM/c^2)

  orbits from 40 M at 0.13 c: going round with the spin, against it, and with no spin - 5 orbits each; with the
    spin the apsides move on about 37 degrees an orbit, against it about 74, with no spin about 50
  light from 200 M to 200 M past the hole at 12 M and 30 M: below the hole it goes round with the spin, above it
    against; and the same rays past the hole with no spin

writes logs/kerrPaths/kerrPaths_<datetime>/ - a csv and log for each path, and kerrPaths.full.json (with its
.prefs.json and .config.json) to open them all in the viewer set up to look at: colours, apsides, the horizon

run: python3 studies/kerr_paths.py      (then: python3 viewer/csv_viewer.py logs/kerrPaths/kerrPaths_<datetime>/kerrPaths.full.json)
"""
import json
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, Config
from engine.kerr import KerrFlowCalculator
from engine.logger import Log, LOG_DIR
from engine.constants import *
from engine.exact import kerrHorizon

MASS = 4e6*MS
SPIN = 0.9
FRACTION = 3e-4
LIGHT_START = 200    #light starts and ends this far out (M)


def steps():
  config = Config()
  config.dt, config.stepFraction = 1e9, FRACTION
  return config


def run(folder, name, spin, start, velocity=None, w=None, ends=(), rows=400, duration=None):
  """one path: from start (m) at velocity v through the plot, or w relative to the river (light)"""
  calc = KerrFlowCalculator([Body(MASS, spin=spin)], order=2)
  p = Particle()
  p.pos = np.array(start, dtype=float)
  if w is not None:
    calc.initPW(p, np.array(w, dtype=float))
  else:
    calc.initPV(p, np.array(velocity, dtype=float))
  log = Log(name, True, True, folder)
  log.freq = duration/rows
  log.print(name)
  reason, n = calc.run(p, steps(), log, list(ends))
  log.close()
  return log.csvFile.name, reason


def main():
  folder = os.path.join(LOG_DIR, 'kerrPaths', 'kerrPaths_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  M = G*MASS/C**2
  a = SPIN*M
  made = []   #(csv, colour, colour2, line style, periapsis / apoapsis markers)

  #orbits: from r = 40 M on the +y axis; -x from the top is anticlockwise, with the positive spin
  period = 2*math.pi*math.sqrt((30*M)**3/(G*MASS))
  for name, spin, vx, colours in (('orbit_withSpin', SPIN, -1, ('#2a78d6', '#1baf7a')), ('orbit_againstSpin', SPIN, 1, ('#e34948', '#eda100')),
                                  ('orbit_noSpin', 0.0, -1, ('#52514e', '#c3c2b7'))):
    R = math.sqrt((40*M)**2 + (spin*M)**2)   #flat distance for r = 40 M
    path, reason = run(folder, name, spin, [0.0, R], velocity=[vx*0.13*C, 0.0],
                       ends=[('orbits', 5), ('min', 2*kerrHorizon(MASS, spin))], duration=period, rows=200)
    made.append((path, colours[0], colours[1], 'solid', True))
    print('%-20s %s' % (name, reason))

  #light: from x = -200 M along +x, at 12 M and 30 M below the hole (with the spin) and above it (against)
  for b0 in (12, 30):
    for name, spin, side, colour, style in (('light%d_withSpin' % b0, SPIN, -1, '#2a78d6', 'solid'), ('light%d_againstSpin' % b0, SPIN, 1, '#e34948', 'solid'),
                                            ('light%d_noSpinBelow' % b0, 0.0, -1, '#52514e', 'dashed'), ('light%d_noSpinAbove' % b0, 0.0, 1, '#52514e', 'dashed')):
      path, reason = run(folder, name, spin, [-LIGHT_START*M, side*b0*M], w=[C, 0.0],
                         ends=[('time', 2*LIGHT_START*M/C), ('min', kerrHorizon(MASS, spin))], duration=2*LIGHT_START*M/C)
      made.append((path, colour, None, style, False))
      print('%-20s %s' % (name, reason))

  #a full config for the viewer: these files, their colours and markers, and the horizon shown
  results = [{'path': path, 'relative': os.path.basename(path), 'visible': True, 'straight': False, 'ends': False,
              'periapsis': orbit, 'apoapsis': orbit, 'styles': {'pos': [colour, style, colour2 or colour]},
              'selection': [['pos_x', 'pos_y']], 'group': None, 'hiddenOrbits': []} for path, colour, colour2, style, orbit in made]
  config = {'kind': 'config', 'version': 1, 'results': results, 'selected': made[0][0], 'background': None, 'timeInterval': ''}
  prefs = {'kind': 'preferences', 'version': 1, 'preferences': {'mode': 'xy', 'equalAspect': True, 'showSchwarzschild': True,
           'showFlow': False, 'showTimeMarks': False, 'showMarkers': True, 'showPathLegend': True, 'showFieldKey': True}}
  full = {'kind': 'full', 'version': 1, 'preferences': 'kerrPaths.prefs.json', 'config': 'kerrPaths.config.json'}
  for fname, doc in (('kerrPaths.config.json', config), ('kerrPaths.prefs.json', prefs), ('kerrPaths.full.json', full)):
    with open(os.path.join(folder, fname), 'w') as f:
      json.dump(doc, f, indent=2)
  print('open with: python3 viewer/csv_viewer.py', os.path.relpath(os.path.join(folder, 'kerrPaths.full.json'), os.path.dirname(LOG_DIR)))
  return folder


if __name__ == '__main__':
  main()
