"""
the examples in Part 1 of the write-up (docs/archive/part1/), each run in the flow model so the website can show it in the
browser viewer:

  apple     Newton's apple: at rest 11 m above the Earth's surface (v = 0, so w = -u: moving up through space at
            the escape speed), it falls 10 m; against Newtonian gravity (dashed). height and time, not x and y
  regions   light crossing regions of space that flow downwards ever faster (u = (0, -k x), up to 0.8c), by the
            write-up's original procedure (each step: move with space, then through it, then w changes by the
            difference in the flow): with that change added as plain vectors (dashed) the light keeps going straight
            (and |w| passes c); added relativistically (solid) its path curves; and the true geodesic of this flow's
            metric (dotted: studies/grav_wave_across.py's Geodesic) keeps w and is carried down with the space. this
            flow has curl, which is why the three differ (with no curl the model's step is the geodesic)
  bending   light passing a 1 solar mass hole at impact parameters of 4-30 Schwarzschild radii, in the flow model
            (solid) and under Newtonian gravity at c (dashed), which bends it about half as much
  orbit     an orbit between 20 and 60 Schwarzschild radii, six times round: the flow model's precesses, about 20
            degrees an orbit; the Newtonian ellipse (dashed) stays closed
  radar     a radar echo past a hole: light from an 'Earth' 150 Schwarzschild radii on one side to a mirror 60 on the
            other and back, x against time: the two legs take different times (the clocks the model runs on are
            Gullstrand-Painleve time), and the round trip shows the Shapiro delay

writes logs/part1/part1_<datetime>/: a csv and log for each path, and a viewer file per example
(part1_<example>.full.json), with the steady flow written as a background frame for the browser viewer

run: python3 studies/part1_examples.py      (then: python3 scripts/publish_run.py logs/part1/part1_<datetime>)
"""
import csv
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Calculator, SpecialFlowCalculator, NewtonianCalculator, Particle
from engine.logger import Log, LOG_DIR
from engine.constants import *
from engine.exact import schwarzschildRadius
from two_body_escapes import writeViewerFiles

RS = schwarzschildRadius(MS)
HOLE = [Body(MS)]
COLOURS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#8a5cd8', '#e34948']


def write(folder, name, calc, rows, columns, notes):
  """a csv of rows (with columns) and its log (calc's bodies, then notes); returns the csv's path"""
  log = Log(name, True, False, folder)
  log.logBodies(calc)
  for line in notes:
    log.print(line)
  path = log.file.name[:-4] + '.csv'
  log.close()
  with open(path, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(columns)
    for row in rows:
      out.writerow(['%.12g' % v for v in row])
  return path


def follow(calc, p, done, step, every=1):
  """move p by step(p) until done(p); the rows (t, x, y, vx, vy) every few steps, and the last"""
  rows = [(p.t, *p.pos, *p.v)]
  n = 0
  while not done(p):
    calc.move(p, step(p))
    n += 1
    if n % every == 0:
      rows.append((p.t, *p.pos, *p.v))
  if rows[-1][0] != p.t:
    rows.append((p.t, *p.pos, *p.v))
  return rows


def apple(folder):
  """Newton's apple: 11 m up, at rest, falling 10 m"""
  made, lines = [], []
  earth = [Body(ME)]
  for name, calc, style in (('apple_flow', SpecialFlowCalculator(earth, 2), 'solid'),
                            ('apple_newton', NewtonianCalculator(earth), 'dashed')):
    p = Particle()
    p.pos = np.array([0.0, REARTH + 11.0])
    if isinstance(calc, SpecialFlowCalculator):
      calc.initPV(p, np.array([0.0, 0.0]))   #v = 0: w = -u, up through space at the escape speed
    rows = follow(calc, p, lambda p: p.pos[1] <= REARTH + 1.0, lambda p: 1e-4, every=100)
    rows = [(t, y - REARTH, vy) for t, x, y, vx, vy in rows]
    t, h, v = rows[-1]
    lines.append('%s: fell 10 m in %.4f s, at %.4f m/s' % (name, t, -v))
    made.append((write(folder, name, calc, rows, ['t', 'height', 'v_y'],
                       ['the apple, at rest 11 m up, falls 10 m (steps of 1e-4 s)', lines[-1]]),
                  COLOURS[0] if style == 'solid' else COLOURS[1], style))
  writeViewerFiles(folder, 'part1_apple', made, selection=(('t', 'height'),),
                   styles=lambda colour, style='solid': {'t / height': [colour, style, colour]},
                   preferences={'equalAspect': False, 'showBodies': False, 'showSchwarzschild': False, 'showFlow': False})
  return lines


class Shear(SpecialFlowCalculator):
  """space flowing downwards ever faster to the right: u = (0, -k x) for x between 0 and WIDTH, still elsewhere"""
  WIDTH = 1e9
  K = 0.8*C/WIDTH

  def __init__(self, relativistic):
    super().__init__([], 1)
    self.relativistic = relativistic

  def flow(self, pos, region=None, t=0.0):
    x = min(max(pos[0], 0.0), self.WIDTH)
    return np.array([0.0, -self.K*x])

  def addSI(self, u, v):
    return super().addSI(u, v) if self.relativistic else u + v

  def describe(self):
    return 'relativistic' if self.relativistic else 'plain'


def regions(folder):
  """light crossing regions of space flowing ever faster downwards, by the original first-order procedure"""
  made, lines = [], []
  for relativistic, style in ((False, 'dashed'), (True, 'solid')):
    calc = Shear(relativistic)
    p = Particle()
    p.pos = np.array([0.0, 0.0])
    calc.initPW(p, np.array([C, 0.0]))
    rows = follow(calc, p, lambda p: p.pos[0] >= Shear.WIDTH or p.t > 30, lambda p: 1e-3, every=20)
    name = 'regions_' + ('relativistic' if relativistic else 'plain')
    t, x, y, vx, vy = rows[-1]
    turned = math.degrees(math.atan2(p.w[1], p.w[0]))
    lines.append('%s: crossed %.0f m in %.3f s, w turned %.2f degrees, v (%.4fc, %.4fc), |w| %.6fc'
                 % (name, x, t, turned, vx/C, vy/C, np.linalg.norm(p.w)/C))
    made.append((write(folder, name, calc, rows, ['t', 'pos_x', 'pos_y', 'v_x', 'v_y'],
                       ['light from (0, 0) along +x through u = (0, -k x), k = 0.8c over %g m; the change in the flow'
                        ' added %s' % (Shear.WIDTH, 'relativistically' if relativistic else 'as plain vectors'),
                        lines[-1]]), COLOURS[1], style))
  from grav_wave_across import Geodesic
  shear = Shear(True)
  geodesic = Geodesic(type('ShearFlow', (), {'flow': lambda self, pos, t: shear.flow(pos)})())
  p = Particle()
  geodesic.initPW(p, np.array([C, 0.0]))
  rows = follow(geodesic, p, lambda p: p.pos[0] >= Shear.WIDTH or p.t > 30, lambda p: 1e-3, every=20)
  t, x, y, vx, vy = rows[-1]
  lines.append('regions_geodesic: crossed %.0f m in %.3f s, w turned %.2f degrees, v (%.4fc, %.4fc), |w| %.6fc'
               % (x, t, math.degrees(math.atan2(p.w[1], p.w[0])), vx/C, vy/C, np.linalg.norm(p.w)/C))
  made.append((write(folder, 'regions_geodesic', shear, rows, ['t', 'pos_x', 'pos_y', 'v_x', 'v_y'],
                     ['light from (0, 0) along +x through the same flow: the true geodesic of its metric,'
                      ' ds^2 = -c^2 dt^2 + |dx - u dt|^2', lines[-1]]), COLOURS[1], 'dotted'))
  writeViewerFiles(folder, 'part1_regions', made, preferences={'showFlow': True, 'showBodies': False},
                   frames=Shear(True))
  return lines


def bending(folder):
  """light past a hole at several impact parameters: the flow model and Newtonian gravity at c"""
  made, lines = [], []
  for k, b in enumerate((4, 6, 10, 20, 30)):
    for name, calc, style in (('flow', SpecialFlowCalculator(HOLE, 2), 'solid'), ('newton', NewtonianCalculator(HOLE), 'dashed')):
      p = Particle()
      p.pos = np.array([-150*RS, b*RS])
      if isinstance(calc, SpecialFlowCalculator):
        calc.initPW(p, np.array([C, 0.0]))
      else:
        p.v = np.array([C, 0.0])
      rows = follow(calc, p, lambda p: np.linalg.norm(p.pos) > 160*RS and p.pos[0] > 0,
                    lambda p: 0.002*np.linalg.norm(p.pos)/C, every=10)
      bend = -math.degrees(math.atan2(p.v[1], p.v[0]))
      lines.append('b = %d rs, %s: bent %.2f degrees' % (b, name, bend))
      made.append((write(folder, 'bend%d_%s' % (b, name), calc, rows, ['t', 'pos_x', 'pos_y', 'v_x', 'v_y'],
                         ['light from x = -150 rs at y = %d rs along +x: %s' % (b, 'the flow model' if name == 'flow' else
                          'Newtonian gravity, starting at c'), lines[-1]]), COLOURS[k], style))
  writeViewerFiles(folder, 'part1_bending', made, preferences={'showFlow': True}, frames=SpecialFlowCalculator(HOLE, 2))
  return lines


def orbit(folder):
  """an orbit between 20 and 60 rs, six times round"""
  made, lines = [], []
  rp, ra = 20*RS, 60*RS
  a = (rp + ra)/2
  speed = math.sqrt(G*MS*(2/ra - 1/a))   #the Newtonian ellipse's speed at apoapsis
  period = 2*math.pi*math.sqrt(a**3/(G*MS))
  for name, calc, style in (('orbit_flow', SpecialFlowCalculator(HOLE, 2), 'solid'), ('orbit_newton', NewtonianCalculator(HOLE), 'dashed')):
    p = Particle()
    p.pos = np.array([ra, 0.0])
    if isinstance(calc, SpecialFlowCalculator):
      calc.initPV(p, np.array([0.0, speed]))
    else:
      p.v = np.array([0.0, speed])
    turned = [0.0, math.atan2(p.pos[1], p.pos[0])]

    def done(p):
      angle = math.atan2(p.pos[1], p.pos[0])
      step = (angle - turned[1] + math.pi) % (2*math.pi) - math.pi
      turned[0] += step
      turned[1] = angle
      return turned[0] >= 6*2*math.pi
    rows = follow(calc, p, done, lambda p: 0.0005*np.linalg.norm(p.pos)/max(np.linalg.norm(p.v), np.linalg.norm(p.u)), every=20)
    lines.append('%s: six times round in %.4f s (Newtonian period %.4f s)' % (name, rows[-1][0], period))
    made.append((write(folder, name, calc, rows, ['t', 'pos_x', 'pos_y', 'v_x', 'v_y'],
                       ['an orbit from apoapsis at 60 rs with the Newtonian ellipse\'s speed there (periapsis 20 rs): %s'
                        % ('the flow model' if 'flow' in name else 'Newtonian gravity'), lines[-1]]),
                  COLOURS[0], style))
  writeViewerFiles(folder, 'part1_orbit', made, preferences={'showFlow': True}, frames=SpecialFlowCalculator(HOLE, 2))
  return lines


def radar(folder):
  """a radar echo past a hole: out from 'Earth' at x = -150 rs to a mirror at x = +60 rs, and back"""
  made, lines = [], []
  calc = SpecialFlowCalculator(HOLE, 2)
  b = 15*RS
  earth, mirror = -150*RS, 60*RS
  p = Particle()
  p.pos = np.array([earth, b])
  calc.initPW(p, np.array([C, 0.0]))
  step = lambda p: 0.001*np.linalg.norm(p.pos)/C
  out = follow(calc, p, lambda p: p.pos[0] >= mirror, step, every=10)
  there = p.t
  p.w = -p.w   #the mirror sends it straight back (its w reversed, as a mirror at rest in its space would)
  p.v = p.w + p.u
  back = follow(calc, p, lambda p: p.pos[0] <= earth, step, every=10)
  f = lambda r: RS/C*(2*math.sqrt(r/RS) + math.log((math.sqrt(r/RS) - 1)/(math.sqrt(r/RS) + 1)))
  offset = f(math.hypot(earth, b)) - f(math.hypot(mirror, b))
  flat = (mirror - earth)/C
  lines.append('out %.6f s, back %.6f s (flat space: %.6f s each way); out - back %.6f s; the clock offset between'
               ' the ends, 2 x %.6f s = %.6f s; round trip %.6f s, %.6f s more than flat space'
               % (there, p.t - there, flat, 2*there - p.t, offset, 2*offset, p.t, p.t - 2*flat))
  made.append((write(folder, 'radar', calc, out + back[1:], ['t', 'pos_x', 'pos_y', 'v_x', 'v_y'],
                     ['light from x = -150 rs (y = 15 rs) to a mirror at x = +60 rs and back', lines[-1]]),
               COLOURS[3], 'solid'))
  writeViewerFiles(folder, 'part1_radar', made, selection=(('pos_x', 't'),),
                   styles=lambda colour, style='solid': {'pos_x / t': [colour, style, colour]},
                   preferences={'equalAspect': False, 'showBodies': False, 'showSchwarzschild': False, 'showFlow': False})
  return lines


def main():
  folder = os.path.join(LOG_DIR, 'part1', 'part1_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = []
  for example in (apple, regions, bending, orbit, radar):
    found = example(folder)
    lines += found + ['']
    print('\n'.join(found), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  return folder


if __name__ == '__main__':
  main()
