"""
the White Holes page (docs/part1/white-holes.md): the Black Holes page's fall, into a white hole instead - space
flowing out of the hole at the escape speed, u = sqrt(2GM/r) outward, decelerating (g = GM/r^2, still inward) - checked
against exact general relativity

the hole is the Black Holes page's: 4 million solar masses (rs = 1.18e10 m, rs/c = 39.4 s), the observer who stays put
at START = 20 rs (holding still against the outflow, moving in through it at u: clock at sqrt(1 - rs/r) = 0.975 of the
flow's time, as for the black hole)

  fall     falling from rest at infinity, against the outflow (initPAgainstFlow: w = -2u/(1 + u^2/c^2), so a
           stationary observer sees it pass at the escape speed), passing the observer at t = 0. its proper time is a
           black hole fall's, but in the white hole's time it only creeps towards the horizon, its clock slowing to a
           stop. it sends light straight out at the same proper times as the black hole's traveller (every 4 minutes,
           and at 2, 1.5, 1.2, 1.05 and 1.01 rs), and the light reaches START at the same times after t = 0. x against
           t, followed to t = END
  flashes  the same fall in space (x, y): at 3, 1.5 and 1.1 rs light in 12 directions, followed for 0.4 rs/c, over
           the outflow (u, and g pointing in) - the light's circle carried out with the space, the ray sent straight
           in holding nearly still near the horizon

exact general relativity in the white hole's time (outgoing Gullstrand-Painleve time, t_s - f(r), f the black hole's
GP less Schwarzschild time): the fall is at T = tau - 2 (f(r) - f(START)) after proper time tau, and light straight
out climbs at dr/dT = c(1 + sqrt(rs/r))

writes logs/whiteHoles/whiteHoles_<datetime>/: a csv and log for each path, whiteHoles_fall.full.json and
whiteHoles_flashes.full.json (with the outflow as its backgrounds file), and summary.log

run: python3 studies/white_holes.py      (then: python3 scripts/publish_run.py logs/whiteHoles/whiteHoles_<datetime>)
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

MASS = 4e6*MS
RS = schwarzschildRadius(MASS)
GM = G*MASS
START = 20*RS
END = 4000.0             #the fall is followed to this time (s)
STEP = 1e-3              #each step moves about this fraction of the distance to the hole
EVERY = 20               #steps between csv rows
COLOURS = {'object': '#2a78d6', 'ray': '#eb6834'}
CALC = SpecialFlowCalculator([Body(MASS, black=False)], 2)
COLUMNS = ['t', 'pt', 'pos_x', 'pos_y', 'v_x', 'v_y']
X_T = lambda colour, style='solid': {'pos_x / t': [colour, style, colour]}
DESCRIPTION = ('Space flowing out of a white hole of 4 million solar masses at the escape speed, u = sqrt(2GM/r): at'
               ' the speed of light at the Schwarzschild radius (1.18e10 m), slower further out. It slows as it goes,'
               ' so its acceleration g (dark arrows) points back in, at GM/r^2: a white hole attracts, as a black hole'
               ' does.')


# --- exact general relativity, in the white hole's time ------------------------------------------------------------

def fallR(tau):
  """where a fall from rest at infinity, at START at proper time 0, is after proper time tau"""
  return (START**1.5 - 1.5*math.sqrt(2*GM)*tau)**(2/3)

def gpLessSchwarzschild(r):
  """the black hole's Gullstrand-Painleve less Schwarzschild time at r (outside the horizon); the white hole's is minus it"""
  s = math.sqrt(r/RS)
  return RS/C*(2*s + math.log((s - 1)/(s + 1)))

def fallT(tau):
  """the white hole's time when the fall has taken proper time tau (0 at START)"""
  return tau - 2*(gpLessSchwarzschild(fallR(tau)) - gpLessSchwarzschild(START))

def lightTime(r0, r1):
  """light straight out of a white hole from r0 to r1, dr/dT = c(1 + sqrt(rs/r)): (2 rs/c)[s^2/2 - s + ln(s + 1)]"""
  F = lambda r: (lambda s: s*s/2 - s + math.log(s + 1))(math.sqrt(r/RS))
  return 2*RS/C*(F(r1) - F(r0))

def blackLightTime(r0, r1):
  """the same for a black hole, dr/dT = c(1 - sqrt(rs/r)), for the comparison"""
  F = lambda r: (lambda s: s*s/2 + s + math.log(abs(s - 1)))(math.sqrt(r/RS))
  return 2*RS/C*(F(r1) - F(r0))


# --- the simulation ------------------------------------------------------------------------------------------------

def row(p):
  return (p.t, p.pt, *p.pos, *p.v)

def dtAt(p):
  return STEP*np.linalg.norm(p.pos)/C

def ray(t, pos, w, duration=None):
  """light from pos at time t moving at w relative to space: out to START, or for duration; returns (rows, end, r)"""
  p = Particle()
  p.pos, p.t = pos.copy(), t
  CALC.initPW(p, w)
  rows, steps, end = [row(p)], 0, None if duration is None else t + duration
  while True:
    r = np.linalg.norm(p.pos)
    if (end is None and r >= START) or (end is not None and p.t >= end - 1e-9):
      break
    dt = dtAt(p) if end is None else min(dtAt(p), end - p.t)
    if end is None and np.linalg.norm(p.pos + p.v*dt) > START:   #land on START
      dt = (START - r)/max(np.dot(p.v, p.pos)/r, 1e-30)
    CALC.move(p, dt)
    steps += 1
    if steps % EVERY == 0:
      rows.append(row(p))
  if rows[-1][0] != p.t:
    rows.append(row(p))
  return rows, p.t, np.linalg.norm(p.pos)

def falling(p, until, emitAt, onEmit, rows):
  """move p until until(p), landing exactly on each proper time in emitAt for onEmit(p)"""
  pending = sorted(emitAt)
  steps = 0
  while not until(p):
    dt = dtAt(p)
    if pending:
      rate = math.sqrt(max(1 - (p.w @ p.w)/C**2, 1e-30))
      dt = min(dt, (pending[0] - p.pt)/rate)
    if dt > 0:
      CALC.move(p, dt)
      steps += 1
      if steps % EVERY == 0:
        rows.append(row(p))
    while pending and p.pt >= pending[0] - 1e-6:
      rows.append(row(p))
      onEmit(p)
      pending.pop(0)
  rows.append(row(p))


def fall(folder):
  lines, made = [], []
  inner = [2, 1.5, 1.2, 1.05, 1.01]
  emitAt = [240.0*k for k in range(1, int(fallTime(GM, START, RS)/240) + 1)] + [fallTime(GM, START, r*RS) for r in inner]
  emissions = []
  p = Particle()
  p.pos = np.array([START, 0.0])
  CALC.initPAgainstFlow(p)
  rows = [row(p)]
  falling(p, lambda p: p.t >= END, emitAt, lambda p: emissions.append((p.t, p.pt, p.pos.copy())), rows)
  r = np.linalg.norm(p.pos)
  lines.append('fall: from rest at infinity against the outflow, passing START = 20 rs at t = 0; at t %.1f s it is at'
               ' %.6f rs, its clock at %.3f s (exact %.3f s; a black hole fall reaches the horizon at %.3f s), running'
               ' at %.2e of the white hole\'s time' % (p.t, r/RS, p.pt, fallTime(GM, START, r), fallTime(GM, START, RS),
                                                      math.sqrt(1 - (p.w @ p.w)/C**2)))
  made.append((write(folder, 'fall', CALC, rows, COLUMNS, ['falling from rest at infinity into a white hole, from 20 rs'
                     ' (t = 0), against the outflow', lines[-1]]), COLOURS['object'], 'solid'))
  lines.append('  %-3s %10s %10s %10s %10s %10s %12s %12s %12s %10s %12s' % ('ray', 'sent pt', 'r (rs)', 'exact r',
               'sent t', 'exact t', 'back at t', 'exact', 'black hole', 'gap', 'ratio - 1'))
  last = None
  for n, (t, pt, pos) in enumerate(emissions, 1):
    r = np.linalg.norm(pos)
    rays, end, rEnd = ray(t, pos, C*pos/r)
    exactR = fallR(pt)
    exactT = fallT(pt)
    exact = exactT + lightTime(exactR, START)
    black = pt + blackLightTime(exactR, START)   #the black hole's traveller's flow time is its proper time
    gap = '' if last is None else '%.3f' % (end - last)
    lines.append('  %-3d %10.3f %10.5f %10.5f %10.3f %10.3f %12.3f %12.3f %12.3f %10s %12.2e' % (n, pt, r/RS, exactR/RS,
                 t, exactT, end, exact, black, gap, (end - t)/(exact - exactT) - 1))
    last = end
    made.append((write(folder, 'fallray%d' % n, CALC, rays, COLUMNS,
                       ['light sent straight out at t %g s from %.4f rs by the falling observer' % (t, r/RS), lines[-1]]),
                 COLOURS['ray'], 'solid'))
  writeViewerFiles(folder, 'whiteHoles_fall', made, selection=(('pos_x', 't'),), styles=X_T,
                   preferences={'equalAspect': False, 'showBodies': True, 'showSchwarzschild': True, 'showFlow': False,
                                'showPathLegend': False})
  return lines


def flashes(folder):
  lines, made = [], []
  p = Particle()
  p.pos = np.array([4*RS, 0.0])
  p.pt = fallTime(GM, START, 4*RS)
  p.t = fallT(p.pt)
  CALC.initPAgainstFlow(p)
  rows = [row(p)]
  at = [3, 1.5, 1.1]
  span = 0.4*RS/C
  emissions = []
  last = fallTime(GM, START, at[-1]*RS)
  falling(p, lambda p: p.pt >= last and p.t >= emissions[-1][0] + span if emissions and len(emissions) == len(at) else False,
          [fallTime(GM, START, r*RS) for r in at], lambda p: emissions.append((p.t, p.pos.copy())), rows)
  made.append((write(folder, 'flashfall', CALC, rows, COLUMNS, ['falling from rest at infinity into a white hole, from'
                     ' 4 rs in']), COLOURS['object'], 'solid'))
  for n, (t, pos) in enumerate(emissions):
    r = np.linalg.norm(pos)
    outward = 0
    for k in range(12):
      a = 2*math.pi*k/12
      rays, end, rEnd = ray(t, pos, C*np.array([math.cos(a), math.sin(a)]), duration=span)
      outward += rEnd > r
      made.append((write(folder, 'flash%d_%02d' % (n, k), CALC, rays, COLUMNS,
                         ['light from %.2f rs at t %g s, at %d degrees' % (r/RS, t, 30*k)]), COLOURS['ray'], 'solid'))
    lines.append('flash at %.2f rs (space flowing out at %.3fc): %d of 12 rays further out after %.2f s' %
                 (r/RS, math.sqrt(RS/r), outward, span))
  writeViewerFiles(folder, 'whiteHoles_flashes', made, preferences={'showFlow': True, 'showGravity': True,
                   'showPathLegend': False, 'showSchwarzschild': True}, frames=CALC,
                   background=('the flow out of the hole', DESCRIPTION))
  return lines


def main():
  folder = os.path.join(LOG_DIR, 'whiteHoles', 'whiteHoles_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = ['a %g solar mass white hole: rs %.6e m, rs/c %.4f s; the observer who stays put at 20 rs, clock at %.5f'
           % (MASS/MS, RS, RS/C, math.sqrt(1 - RS/START)), '']
  for example in (fall, flashes):
    found = example(folder)
    lines += found + ['']
    print('\n'.join(found), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)
  return folder


if __name__ == '__main__':
  main()
