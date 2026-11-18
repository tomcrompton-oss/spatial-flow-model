"""
two checks of the split model (engine/split.py) that the tests of studies/split_bodies.py don't make:

  boost      the system moving: in GR a system moving steadily behaves as one at rest (local Lorentz invariance). the
             Earth (alone; with the Sun at rest; and with the Sun moving too) moving at V through the frame the split
             model's empty space is at rest in, with each of the model's boosts (engine/split.py: 'galilean' and
             'lorentz'): (1) a Moon on its orbit, run for a day in the model, against the orbit at rest seen from the
             moving Earth's frame (a Galilean shift, or a Lorentz boost: the frame each boost works in); (2) radar
             from the Earth's surface to a mirror moving with the Earth at the Moon's distance, along V and across
             it, both placed where (1) puts the Moon's orbit (Lorentz-contracted with the 'lorentz' boost): the round
             trip at the emitter's clock, as a range, less the same at rest. this is what lunar laser ranging would
             see
  causal     light against matter: the steps for matter are not the paths of light's rule (studies/split_bodies.py,
             matter), so can matter outrun light? particles at gamma 10 to 10^6 fired out of the Sun's surface
             towards Jupiter (where the two flows oppose), and past Jupiter: the least margin along the way between
             light's speed in the particle's direction (each light rule) and the particle's own (GR: 1/2 gamma^2 of
             c, at least), and how differently from light the fastest bends

run: python3 studies/split_checks.py      (prints, and writes logs/multiBody/splitChecks_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle
from engine.split import SplitFlowCalculator, Boost
from engine.logger import LOG_DIR
from engine.constants import *
from multi_body_pn import MJ, RJ, DJ

DMOON = 3.844e8
RSUN = 6.957e8


MODELS = (('interval', 'galilean'), ('static', 'lorentz'))


def moonOrbit(V, light, boost, days=1.0, dt=10.0):
  """
  the Moon on its orbit round the Earth moving at V, run for days: how far it ends from the orbit at rest, seen from
  the Earth's frame - the frame the boost works in (Galilean: x - V t at the same t; Lorentz: boosted)
  """
  V = np.array(V, dtype=float)
  r0, v0 = np.array([DMOON, 0.0]), np.array([0.0, math.sqrt(G*ME/DMOON)])
  rest = SplitFlowCalculator([Body(ME)], light, boost)
  moving = SplitFlowCalculator([Body(ME, velocity=V)], light, boost)
  p = Particle()
  if boost != 'galilean':
    f, inverse = Boost(V, 0.0, [0.0, 0.0]), Boost(-V, 0.0, [0.0, 0.0])
    p.t, p.pos = inverse.event(0.0, r0)
    moving.initPV(p, f.back(v0))
  else:
    p.pos = r0.copy()
    moving.initPV(p, v0 + V)
  for _ in range(round(days*DAY/dt)):
    moving.move(p, dt)
  if boost != 'galilean':
    T, x = f.event(p.t, p.pos)
  else:
    T, x = p.t, p.pos - V*p.t
  q = Particle()
  q.pos = r0.copy()
  rest.initPV(q, v0)
  while q.t < T - 1e-9:
    rest.move(q, min(dt, T - q.t))
  return np.linalg.norm(x - q.pos)


def leg(calc, start, end, t0, fraction=0.002):
  """light from start(t0), aimed (by secant steps on the miss) to meet end(t): its arrival time"""
  n = (end(t0) - start(t0))/np.linalg.norm(end(t0) - start(t0))
  def shoot(angle):
    p = Particle()
    p.pos, p.t = start(t0).copy(), t0
    calc.initLight(p, np.array([math.cos(angle), math.sin(angle)]))
    while (p.pos - end(p.t)) @ n < 0:
      last = (p.pos.copy(), p.t)
      gap = np.linalg.norm(end(p.t) - p.pos)
      calc.move(p, min(calc.stepSize(p, fraction), 0.2*max(gap, 1e3)/C))
    a, b = (last[0] - end(last[1])) @ n, (p.pos - end(p.t)) @ n
    f = a/(a - b)
    pos, t = last[0] + f*(p.pos - last[0]), last[1] + f*(p.t - last[1])
    off = pos - end(t)
    return n[0]*off[1] - n[1]*off[0], t
  x0 = math.atan2(n[1], n[0])
  x1 = x0 + 1e-9
  f0, t = shoot(x0)
  f1, t = shoot(x1)
  for _ in range(10):
    if f1 == f0 or abs(f1) < 1e-4:
      break
    x0, x1, f0 = x1, x1 - f1*(x1 - x0)/(f1 - f0), f1
    f1, t = shoot(x1)
  return t


def range_(bodies, V, direction, light, boost):
  """
  radar from the Earth's surface to a mirror at the Moon's distance, both moving with the Earth (at the origin at
  t = 0) at V - Lorentz-contracted along V with the 'lorentz' boost: the round trip at the emitter's clock, as a range
  """
  calc = SplitFlowCalculator(bodies, light, boost)
  V = np.array(V, dtype=float)
  def place(r):
    if boost != 'galilean' and V.any():
      f = Boost(V, 0.0, [0.0, 0.0])
      along = (r @ f.n)*f.n
      r = r - along + along/f.gamma
    return lambda t: r + V*t
  emitter, mirror = place(REARTH*direction), place(DMOON*direction)
  there = leg(calc, emitter, mirror, 0.0)
  back = leg(calc, mirror, emitter, there)
  return C*back*calc.rate(emitter(0.0), V)/2


def boost():
  lines = ['boost: the Earth moving at V through the frame the split model\'s empty space is at rest in']
  found = {}
  for light, kind in MODELS:
    for speed in (29.8e3, 370e3):
      for title, V in (('along x', (speed, 0.0)), ('along y', (0.0, speed))):
        off = moonOrbit(V, light, kind)
        found[(kind, 'moon', speed, title)] = off
        lines.append('  %-8s the Moon after a day, V = %3.0f km/s %s: %.1e m from the orbit at rest, in the Earth\'s'
                     ' frame' % (kind, speed/1e3, title, off))
  lines.append('  radar to a mirror at the Moon\'s distance moving with the Earth: the range less the same at rest'
               ' (m), the mirror along V and across it; L V^2/2c^2 for scale')
  lines.append('  %-9s %-28s %10s %14s %14s %14s' % ('boost', 'bodies', 'V (km/s)', 'along V', 'across V', 'L V^2/2c^2'))
  for light, kind in MODELS:
    for title, bodies, moves in (('none', [], ()), ('the Earth', [Body(ME)], (ME,)),
                                 ('the Earth, the Sun at rest', [Body(MS, -AU, 0.0), Body(ME)], (ME,)),
                                 ('the Earth and the Sun', [Body(MS, -AU, 0.0), Body(ME)], (ME, MS))):
      for speed in (29.8e3, 370e3):
        along, across = np.array([1.0, 0.0]), np.array([0.0, 1.0])
        V = speed*along
        movingBodies = [Body(b.mass, b.x, b.y, velocity=V) if b.mass in moves else b for b in bodies]
        if kind != 'galilean':   #a body moving with the Earth keeps its place in the Earth's frame
          for b in movingBodies:
            if b.mass in moves and b.mass != ME:
              b.pos = b.pos - (b.pos @ along)*along*(1 - 1/math.sqrt(1 - speed**2/C**2))
        still = [range_(bodies, (0.0, 0.0), d, light, kind) for d in (along, across)]
        went = [range_(movingBodies, V, d, light, kind) for d in (along, across)]
        found[(kind, title, speed)] = (went[0] - still[0], went[1] - still[1])
        lines.append('  %-9s %-28s %10.1f %14.4f %14.4f %14.4f' % (kind, title, speed/1e3, went[0] - still[0],
                                                                 went[1] - still[1], DMOON*speed**2/(2*C*C)))
  lines.append('  lunar laser ranging fits the range to millimetres; the Earth moves at 29.8 km/s round the Sun, and'
               ' at 370 km/s against the cosmic background')
  return lines, found


def causal():
  lines = ['causal: particles fired near light\'s speed: the least margin along the way, (light\'s speed in the'
           ' particle\'s direction - its speed)/c, against 1/2 gamma^2 (each light rule)']
  sun, jup = Body(MS, 0.0, 0.0), Body(MJ, DJ, 0.0)
  found = {}
  for light, kind in MODELS:
    calc = SplitFlowCalculator([sun, jup], light, kind)
    for title, start, n in (('out of the Sun towards Jupiter', np.array([RSUN, 0.0]), np.array([1.0, 0.0])),
                            ('into the Sun from Jupiter\'s side', np.array([DJ - 10*RJ, 0.0]), np.array([-1.0, 0.0])),
                            ('past Jupiter at 1 R_J', np.array([DJ + RJ, -1e11]), np.array([0.0, 1.0]))):
      for gamma in (10.0, 1e3, 1e6):
        p = Particle()
        p.pos = start.copy()
        s = calc.lightSpeed(p.pos, n)*math.sqrt(1 - 1/gamma**2)
        calc.initPV(p, s*n)
        least = float('inf')
        while np.linalg.norm(p.pos - start) < 1.5e11 and np.linalg.norm(p.pos - sun.pos) > RSUN*0.999:
          speed = np.linalg.norm(p.v)
          least = min(least, (calc.lightSpeed(p.pos, p.v/speed) - speed)/C)
          calc.move(p, calc.stepSize(p, 0.002, 0.002*AU/C))
        found[(kind, title, gamma)] = least*2*gamma**2
        lines.append('  %-9s %-34s gamma %7.0e: least margin %10.3e = %8.4f x 1/2 gamma^2'
                     % (kind, title, gamma, least, least*2*gamma**2))
  #the fastest particle and light, bent past Jupiter
  for light, kind in MODELS:
    bends = []
    for gamma in (None, 1e6):
      calc = SplitFlowCalculator([sun, jup], light, kind)
      p = Particle()
      p.pos = np.array([DJ + RJ, -1e11])
      n = np.array([0.0, 1.0])
      if gamma is None:
        calc.initLight(p, n)
      else:
        calc.initPV(p, calc.lightSpeed(p.pos, n)*math.sqrt(1 - 1/gamma**2)*n)
      while p.pos[1] < 1e11:
        calc.move(p, calc.stepSize(p, 0.002, 0.002*AU/C))
      bends.append(math.atan2(-p.v[0], p.v[1]))
    found[(kind, 'bend')] = bends
    lines.append('  %-9s past Jupiter at 1 R_J: light bends %.6f arcsec, a particle at gamma 1e6 %.6f (%.1e of it)'
                 % (kind, bends[0]*206264.8, bends[1]*206264.8, (bends[1] - bends[0])/bends[0]))
  return lines, found


def main():
  folder = os.path.join(LOG_DIR, 'multiBody', 'splitChecks_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = []
  for section in (boost, causal):
    out, _ = section()
    print('\n'.join(out), flush=True)
    lines += out + ['']
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
