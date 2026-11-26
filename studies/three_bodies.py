"""
the Multiple Bodies page (docs/part2/multiple-bodies.md): the potential flow round three bodies at rest, three black
holes of one solar mass each at the corners of an equilateral triangle 1 AU across, in the flow model (the eikonal
flow from tables of the paths, engine/eikonal.py: no curl, its speed from the three potentials added) against
Newton's gravity (RK4) from the same starts

each body has a region of the flow of its own; the three regions meet at three seams, which meet at the centre, where
g is zero. the runs cross the seams again and again:

  around2AU   a circle (for 3 solar masses at the centre) 2 AU from the centre, ten times round: three seam
              crossings an orbit
  around4AU   the same at 4 AU
  ellipse     periapsis 1.4 AU, e 0.4, round the centre
  through     from 5 AU out at 40 km/s, aimed just off the centre: through the middle of the three, across the seams
  fall        from rest 3 AU out, just off one of the seams

writes logs/threeBodies/threeBodies_<datetime>/: a csv for each run (and <name>_newton.csv), summary.log, and
threeBodies.full.json with the flow and its seams as the background (threeBodies.backgrounds.json)

run: python3 studies/three_bodies.py
"""
import math
import os
import sys
import time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import Body, Particle, SpecialFlowCalculator
from engine.logger import LOG_DIR
from engine.constants import *
from engine.integrate import rk4Gravity
from engine.vectors import length
from studies.compare_second_order import apsis
from two_body_escapes import writeViewerFiles

SIDE = AU
BODIES = [Body(MS, x=SIDE/math.sqrt(3)*math.cos(a), y=SIDE/math.sqrt(3)*math.sin(a))
          for a in (math.pi/2, math.pi/2 + 2*math.pi/3, math.pi/2 + 4*math.pi/3)]
GM3 = 3*G*MS
YEAR = 365.25*86400
STEP = 1e-3            #each step moves at most this fraction of the distance to the nearest body
EVERY = 40
MAX_STEPS = 3000000
CAPTURE = 2.0          #Schwarzschild radii
ESCAPE = 20*AU
RS = 2*G*MS/C**2
COLOURS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#6250d6']
DESCRIPTION = ('Space round three black holes of one solar mass each, at the corners of a triangle 1 AU across, '
               'flowing as a potential flow: its speed from the three potentials added, sqrt(2GM/d1 + 2GM/d2 + '
               '2GM/d3), and no swirl, running down the paths of things falling from rest far away. The grey arrows '
               'are the flow u, the dark ones g, its acceleration, which is Newton\'s gravity. Each hole has a region '
               'of its own; the dashed lines are the three seams where the regions meet, meeting at the centre, '
               'where g is zero.')


def period(r, gm):
  return 2*math.pi*math.sqrt(r**3/gm)


def tests():
  """(name, description, position, velocity or None for rest, apsides about the centre, time limit)"""
  out = []
  for r in (2, 4):
    pos = np.array([r*AU, 0.0])
    out.append(('around%dAU' % r, 'a circle (for 3 solar masses at the centre) %d AU from the centre' % r, pos,
                np.array([0.0, math.sqrt(GM3/(r*AU))]), True, 10*period(r*AU, GM3)))
  peri, e = 1.4*AU, 0.4
  out.append(('ellipse', 'periapsis 1.4 AU, e 0.4, round the centre', np.array([peri, 0.0]),
              np.array([0.0, math.sqrt(GM3*(1 + e)/peri)]), True, 8*period(peri/(1 - e), GM3)))
  out.append(('through', 'from 5 AU out at 40 km/s, aimed just off the centre, through the middle of the three',
              np.array([-5*AU, 0.03*AU]), np.array([40000.0, 0.0]), False, 1.2*YEAR))
  out.append(('fall', 'from rest 3 AU out, just off the seam below the centre', np.array([0.02*AU, -3*AU]), None,
              False, 3*YEAR))
  return out


def stopReason(pos):
  if not np.all(np.isfinite(pos)):
    return 'not finite'
  for k, b in enumerate(BODIES):
    if length(pos - b.pos) < CAPTURE*RS:
      return 'captured by hole %d' % (k + 1)
  if length(pos) > ESCAPE:
    return 'escaped'
  return None


class Apsides:
  def __init__(self):
    self.recent, self.peri = [], []

  def add(self, t, pos):
    self.recent = (self.recent + [(t, length(pos), pos.copy())])[-3:]
    if len(self.recent) == 3:
      (_, a, _), (_, b, _), (_, c, _) = self.recent
      if b < a and b <= c:
        self.peri.append(apsis([x[0] for x in self.recent], [x[1] for x in self.recent], [x[2] for x in self.recent]))

  def precession(self):
    """the mean advance of the closest approach to the centre, degrees an orbit (positive the way it goes round)"""
    if len(self.peri) < 2:
      return None
    angles = np.unwrap([math.atan2(q[1], q[0]) for _, _, q in self.peri])
    return math.degrees(np.mean(np.diff(angles)) % (2*math.pi) - 2*math.pi*(np.mean(np.diff(angles)) % (2*math.pi) > math.pi)), len(self.peri) - 1


def runFlow(calc, pos, vel, limit, aps):
  p = Particle()
  p.pos = np.array(pos, dtype=float)
  calc.initPV(p, np.zeros(2) if vel is None else np.array(vel, dtype=float))
  v0 = p.v.copy()
  rows, reason = [(p.t, p.pt, *p.pos, *p.v)], None
  for i in range(1, MAX_STEPS + 1):
    dt = min(calc.stepSize(p, STEP), limit - p.t)
    calc.move(p, dt)
    aps.add(p.t, p.pos)
    reason = stopReason(p.pos) or ('time limit' if p.t >= limit*(1 - 1e-12) else None)
    if reason or i % EVERY == 0:
      rows.append((p.t, p.pt, *p.pos, *p.v))
    if reason:
      return rows, reason, i, v0
  return rows, 'step limit', MAX_STEPS, v0


def runNewton(calc, pos, v0, limit, aps):
  pos, v, t = np.array(pos, dtype=float), np.array(v0, dtype=float), 0.0
  rows, reason = [(t, t, *pos, *v)], None
  for i in range(1, MAX_STEPS + 1):
    speed = max(length(v), length(calc.flow(pos)))
    dt = min(STEP*calc.nearest(pos)/speed, limit - t)
    pos, v = rk4Gravity(calc, pos, v, dt)
    t += dt
    aps.add(t, pos)
    reason = stopReason(pos) or ('time limit' if t >= limit*(1 - 1e-12) else None)
    if reason or i % EVERY == 0:
      rows.append((t, t, *pos, *v))
    if reason:
      return rows, reason, i
  return rows, 'step limit', MAX_STEPS


def write(path, rows, note):
  with open(path, 'w') as f:
    f.write('t,pt,pos_x,pos_y,v_x,v_y\n')
    for r in rows:
      f.write(','.join('%.10g' % v for v in r) + '\n')
  with open(path[:-4] + '.log', 'w') as f:
    f.write('bodies: %d\n' % len(BODIES))
    for k, b in enumerate(BODIES, 1):
      f.write('body %d: mass %.6e kg (1 MS)  x %.6e m  y %.6e m  black\n' % (k, b.mass, b.x, b.y))
    f.write(note + '\n')


def main():
  folder = os.path.join(LOG_DIR, 'threeBodies', 'threeBodies_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  began = time.time()
  calc = SpecialFlowCalculator(BODIES, 2, 'eikonal')
  calc.warn = lambda m: None
  lines = ['three 1 MS holes at the corners of a triangle %g AU across; the flow %s (tables built in %.0f s)'
           % (SIDE/AU, calc.describeDirection(), time.time() - began), '']
  made = []
  for k, (name, text, pos, vel, orbit, limit) in enumerate(tests()):
    t0 = time.time()
    fa, na = Apsides(), Apsides()
    rows, reason, steps, v0 = runFlow(calc, pos, vel, limit, fa)
    nrows, nreason, nsteps = runNewton(calc, pos, v0, limit, na)
    end, nend = np.array(rows[-1][2:4]), np.array(nrows[-1][2:4])
    lines.append('%-10s %s' % (name, text))
    lines.append('  flow:   %-18s t %.4g yr  end (%.5f, %.5f) AU  (%d steps)' % (reason, rows[-1][0]/YEAR, *(end/AU), steps))
    lines.append('  newton: %-18s t %.4g yr  end (%.5f, %.5f) AU  apart %.3g AU' % (nreason, nrows[-1][0]/YEAR, *(nend/AU),
                                                                              length(end - nend)/AU))
    if orbit and fa.precession() and na.precession():
      (fp, fn), (np_, nn) = fa.precession(), na.precession()
      lines.append('  closest approach to the centre moves on: flow %.5f deg an orbit (%d orbits), newton %.5f (%d)' % (fp, fn, np_, nn))
    print('\n'.join(lines[-4 if orbit else -3:]), '(%.0f s)' % (time.time() - t0), flush=True)
    path = os.path.join(folder, name + '.csv')
    write(path, rows, 'the flow model (potential flow, second order): ' + text)
    write(path[:-4] + '_newton.csv', nrows, 'newtonian gravity (RK4): ' + text)
    made += [(path, COLOURS[k], 'solid'), (path[:-4] + '_newton.csv', COLOURS[k], 'dashed')]
  writeViewerFiles(folder, 'threeBodies', made, frames=calc, background=('the flow', DESCRIPTION),
                   preferences={'showFlow': True, 'showSeam': True, 'showPathLegend': False})
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
