"""
the flow pointed along g, round the two holes of studies/two_body_escapes.py: does space moving with it fall at g?

for paths from 2 AU, each drawn twice: the flow line (a piece of space carried by the flow, dx/dt = u) and the
newtonian fall from the same place at the same velocity (what space must do if it falls at g). where the flow has no
curl the two are the same path (the eikonal flow: studies/two_body_falls.py); along g they part, by up to 27 degrees
in direction (tests/test_flow_consistency.py)

writes logs/twoBodyAlongG/twoBodyAlongG_<datetime>/: a csv of the flow lines and one of the falls (an empty row ending
each path), and twoBodyAlongG.full.json, the flow along g behind them

run: python3 studies/two_body_along_g.py      (then: python3 scripts/publish_run.py logs/twoBodyAlongG/twoBodyAlongG_<datetime>)
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
from studies.two_body_escapes import BODIES, STEP, writeViewerFiles

PATHS = 12
FROM = 2*AU          #where the paths start, round the holes
MAX_STEPS = 200000


def flowLine(calc, pos, near):
  """a piece of space carried by the flow from pos: dx/dt = u, by RK4, until it is within near of a body"""
  t, rows = 0.0, []
  for i in range(MAX_STEPS):
    u = calc.flow(pos)
    if i % 20 == 0:
      rows.append((t, pos, u))
    nearest = min(np.linalg.norm(pos - b.pos) for b in calc.bodies)
    if nearest < near:
      break
    dt = STEP*nearest/np.linalg.norm(u)
    k1 = u
    k2 = calc.flow(pos + k1*dt/2)
    k3 = calc.flow(pos + k2*dt/2)
    k4 = calc.flow(pos + k3*dt)
    pos = pos + (k1 + 2*k2 + 2*k3 + k4)*dt/6
    t += dt
  rows.append((t, pos, calc.flow(pos)))
  return rows


def fall(calc, pos, near):
  """newtonian, from pos at the flow's velocity there, until within near of a body"""
  v = calc.flow(pos)
  t, rows = 0.0, []
  for i in range(MAX_STEPS):
    if i % 20 == 0:
      rows.append((t, pos, v))
    nearest = min(np.linalg.norm(pos - b.pos) for b in calc.bodies)
    if nearest < near or np.linalg.norm(pos) > 1.5*FROM:
      break
    dt = STEP*nearest/np.linalg.norm(v)
    pos, v = rk4Gravity(calc, pos, v, dt)
    t += dt
  rows.append((t, pos, v))
  return rows


def writePaths(path, paths):
  with open(path, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'pos_x', 'pos_y', 'v_x', 'v_y'])
    for rows in paths:
      for t, pos, v in rows:
        out.writerow([t, pos[0], pos[1], v[0], v[1]])
      out.writerow([''] * 5)


def main():
  folder = os.path.join(LOG_DIR, 'twoBodyAlongG', 'twoBodyAlongG_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  calc = Calculator(BODIES, direction='g')
  near = 0.02*AU
  made = []
  starts = [FROM*np.array([math.cos(a), math.sin(a)]) for a in (2*math.pi*(n + 0.5)/PATHS for n in range(PATHS))]
  for name, run, colour, style in (('flowlines', flowLine, '#1baf7a', 'dashed'), ('falls', fall, '#e8590c', 'solid')):
    log = Log(name, True, False, folder)
    log.logBodies(calc)
    log.print('%d paths from %g AU: %s' % (PATHS, FROM/AU, 'flow lines of the flow along g (dx/dt = u)' if run is flowLine
                                         else 'newtonian falls, starting at the flow\'s velocity'))
    path = log.file.name[:-4] + '.csv'
    log.close()
    writePaths(path, [run(calc, start, near) for start in starts])
    made.append((path, colour, style))
  writeViewerFiles(folder, 'twoBodyAlongG', made, frames=calc,
                   styles=lambda colour, style='solid': {'pos': [colour, style, colour]})
  print('written to', folder)
  return folder


if __name__ == '__main__':
  main()
