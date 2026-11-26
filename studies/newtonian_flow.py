"""
Part 1's Newtonian mechanics of spatial flow (docs/part1/mechanics/newtonian.md), by the page's own procedure: each
step the particle is carried with its space (u dt) and moves through it (w dt), and w then changes by the difference
in the flow, u2 - u3, added as plain vectors. the flow is Part 1's, straight in at the escape speed sqrt(2GM/r)

  apple   Newton's apple, at rest 11 m above the Earth's surface, falling 10 m, at steps of 1 s down to 0.0001 s;
          the landing (1 m up) is placed between the last two steps by linear interpolation, so the time isn't
          rounded to a whole number of steps. against Newtonian gravity, by small steps of a = -GM/r^2
  orbit   an orbit of the Earth from apogee at 20,000 km with the Newtonian ellipse's speed there (perigee 7,000 km),
          three times round: the flow procedure (solid, its second-order form, steps of 0.5 s) against Newtonian
          gravity (dashed); the page's claim is that the procedure is Newton's gravity for any w, not only for a
          straight drop. the first-order form at 0.1 and 0.05 s shows its error: perigee creeps out, by half as much
          at half the step

writes logs/newtonianFlow/newtonianFlow_<datetime>/: summary.log, and csvs and viewer files for both examples

run: python3 studies/newtonian_flow.py      (a minute or so; then: python3 scripts/publish_run.py logs/newtonianFlow/newtonianFlow_<datetime>)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import Body, SpecialFlowCalculator, NewtonianCalculator, Particle
from engine.logger import LOG_DIR
from engine.constants import *
from part1_examples import write, follow, COLOURS
from two_body_escapes import writeViewerFiles

EARTH = [Body(ME)]
GM = G*ME


class NewtonianFlow(SpecialFlowCalculator):
  """the page's procedure, with the change in the flow added to w as a plain vector: order 1 is the page's steps as
  they stand; order 2 takes the same steps half way, then the whole step at the middle's rates"""

  keepLight = False   #with plain addition light's speed through space isn't c, and isn't held there

  def __init__(self, bodies, order=1):
    super().__init__(bodies, order=order, step='velocity')

  def addSI(self, u, v):
    return u + v

  def describe(self):
    return "Part 1's Newtonian flow procedure (order %d, plain addition)" % self.order


def drop(calc, dt, flow):
  """the apple from 11 m, until it is 1 m up: the landing time, u, w and v there (interpolated between steps)"""
  p = Particle()
  p.pos = np.array([0.0, REARTH + 11.0])
  if flow:
    calc.initPV(p, np.array([0.0, 0.0]))
  else:
    p.v = np.array([0.0, 0.0])
  before = None
  while p.pos[1] > REARTH + 1.0:
    before = (p.t, p.pos[1], p.v[1], p.u[1] if flow else 0.0, p.w[1] if flow else 0.0)
    calc.move(p, dt)
  after = (p.t, p.pos[1], p.v[1], p.u[1] if flow else 0.0, p.w[1] if flow else 0.0)
  f = (before[1] - (REARTH + 1.0))/(before[1] - after[1])
  return [b + f*(a - b) for a, b in zip(after, before)]


def apple(folder, say):
  say('the apple, 11 m up, at rest, falling 10 m (landing interpolated between the last two steps)')
  say('%-10s %12s %16s %16s %16s' % ('dt (s)', 'time (s)', 'u (m/s)', 'w (m/s)', 'v (m/s)'))
  for dt in (1.0, 0.1, 0.01, 0.001, 0.0001):
    t, y, v, u, w = drop(NewtonianFlow(EARTH), dt, True)
    say('%-10g %12.6f %16.4f %16.4f %16.6f' % (dt, t, u, w, v))
  t, y, v, u, w = drop(NewtonianCalculator(EARTH), 1e-5, False)
  g = GM/(REARTH + 11.0)**2
  say('Newtonian gravity (steps of 1e-5 s): %.6f s, %.6f m/s; g at 11 m up %.4f m/s^2, sqrt(2d/g) %.6f s, g t %.6f m/s'
      % (t, v, g, math.sqrt(20/g), g*math.sqrt(20/g)))
  made = []
  for name, calc, style in (('apple_flow', NewtonianFlow(EARTH), 'solid'), ('apple_newton', NewtonianCalculator(EARTH), 'dashed')):
    p = Particle()
    p.pos = np.array([0.0, REARTH + 11.0])
    if style == 'solid':
      calc.initPV(p, np.array([0.0, 0.0]))
    rows = follow(calc, p, lambda p: p.pos[1] <= REARTH + 1.0, lambda p: 1e-4, every=100)
    rows = [(t, y - REARTH, vy) for t, x, y, vx, vy in rows]
    made.append((write(folder, name, calc, rows, ['t', 'height', 'v_y'],
                       ['the apple, at rest 11 m up, falls 10 m (steps of 1e-4 s)']),
                 COLOURS[0] if style == 'solid' else COLOURS[1], style))
  writeViewerFiles(folder, 'newtonian_apple', made, selection=(('t', 'height'),),
                   styles=lambda colour, style='solid': {'t / height': [colour, style, colour]},
                   preferences={'equalAspect': False, 'showBodies': False, 'showSchwarzschild': False, 'showFlow': False})


def orbit(folder, say):
  rp, ra = 7.0e6, 2.0e7
  a = (rp + ra)/2
  speed = math.sqrt(GM*(2/ra - 1/a))
  period = 2*math.pi*math.sqrt(a**3/GM)
  say('')
  say('an orbit of the Earth from apogee 20,000 km at %.2f m/s (the Newtonian ellipse: perigee 7,000 km, period %.2f s),'
      ' three times round' % (speed, period))

  def run(calc, dt, every=None):
    p = Particle()
    p.pos = np.array([ra, 0.0])
    if isinstance(calc, NewtonianFlow):
      calc.initPV(p, np.array([0.0, speed]))
    else:
      p.v = np.array([0.0, speed])
    rs = []
    rows = follow(calc, p, lambda p: rs.append(np.linalg.norm(p.pos)) or p.t >= 3*period, lambda p: dt, every=every or 1)
    r = np.array(rs)
    peri = [r[i] for i in range(1, len(r) - 1) if r[i] < r[i - 1] and r[i] <= r[i + 1]]
    return rows, peri

  for dt in (0.1, 0.05):
    rows, peri = run(NewtonianFlow(EARTH, 1), dt)
    say('the procedure, first order, steps of %g s: perigees %s km' % (dt, ', '.join('%.4f' % (x/1e3) for x in peri)))
  made = []
  for name, calc, dt, style in (('orbit_flow', NewtonianFlow(EARTH, 2), 0.5, 'solid'),
                                ('orbit_newton', NewtonianCalculator(EARTH), 0.05, 'dashed')):
    rows, peri = run(calc, dt, int(20/dt))
    say('%s (steps of %g s): perigees %s km' % (calc.describe() if style == 'solid' else 'Newtonian gravity', dt,
        ', '.join('%.4f' % (x/1e3) for x in peri)))
    made.append((write(folder, name, calc, rows, ['t', 'pos_x', 'pos_y', 'v_x', 'v_y'],
                       ['an Earth orbit from apogee 20,000 km, perigee 7,000 km: %s'
                        % (calc.describe() if style == 'solid' else 'Newtonian gravity')]),
                  COLOURS[0] if style == 'solid' else COLOURS[1], style))
  calc = NewtonianFlow(EARTH)
  p = Particle()
  p.pos = np.array([ra, 0.0])
  calc.initPV(p, np.array([0.0, speed]))
  say('at apogee: v = (%.1f, %.1f) m/s, u = (%.1f, %.1f) m/s, w = (%.1f, %.1f) m/s' % (*p.v, *p.u, *p.w))
  writeViewerFiles(folder, 'newtonian_orbit', made, preferences={'showFlow': True, 'showSchwarzschild': False},
                   frames=NewtonianFlow(EARTH))


def main():
  folder = os.path.join(LOG_DIR, 'newtonianFlow', 'newtonianFlow_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = []
  def say(s):
    lines.append(s)
    print(s, flush=True)
  apple(folder, say)
  orbit(folder, say)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
