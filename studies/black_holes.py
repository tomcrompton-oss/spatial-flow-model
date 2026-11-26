"""
the Black Holes page (docs/part1/black-holes.md): an observer falling into a black hole, and a probe that goes close
to one and comes back, each sending light back out to an observer who stays put, checked against exact general
relativity

the hole is 4 million solar masses, about the size of Sagittarius A* at the centre of our galaxy (Schwarzschild radius
rs = 1.18e10 m, rs/c = 39.4 s). the observer who stays put holds still against the flow at START = 20 rs (their
clock runs at sqrt(1 - rs/r) = 0.975 of the flow's time; one further out sees the same gaps between arrivals, since the
flow is steady, a constant time later)

  fall     falling from rest at infinity (moving with the flow, w = 0), passing the observer at t = 0 and falling
           through the horizon to the centre (stopped at 0.05 rs), sending light straight out every 4 minutes of its
           own time and at 2, 1.5, 1.2, 1.05, 1.01, 0.9 and 0.5 rs. x against t: a spacetime diagram, with the
           hole and its horizon drawn by the viewer as lines
  flashes  the same fall in space (x, y): at 3, 1.5, 1 and 0.6 rs it sends light out in 12 directions, followed for
           0.4 rs/c, over the flow - the light's circle is carried in with the space, and from the horizon in all of it
           goes inward
  probe    the astronaut of the write-up's Part 2: falls the same way from START to 1.5625 rs (where space flows in at
           0.8c), holds still there against the flow (w = 0.8c outward, clock at 0.6) for as long by its clock as the
           fall took, then climbs back out ballistically at the escape speed (0.8c added relativistically to the
           0.8c of the flow: w = 0.976c); a light signal straight out every 5 minutes of its own time

each emission is compared with exact general relativity (in Gullstrand-Painleve time, the flow's time): where and
when it was sent, and when it reaches START

writes logs/blackHoles/blackHoles_<datetime>/: a csv and log for each path, a viewer file per example
(blackHoles_<example>.full.json), and summary.log; flashes has the steady flow as its backgrounds file

run: python3 studies/black_holes.py      (then: python3 scripts/publish_run.py logs/blackHoles/blackHoles_<datetime>)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
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
CENTRE = 0.05*RS         #where a path into the hole is stopped
STEP = 1e-3              #each step moves about this fraction of the distance to the hole
EVERY = 20               #steps between csv rows
HOVER = RS/0.64          #where space flows in at 0.8c
COLOURS = {'object': '#2a78d6', 'ray': '#eb6834', 'inside': '#8a5cd8'}
CALC = SpecialFlowCalculator([Body(MASS)], 2)
X_T = lambda colour, style='solid': {'pos_x / t': [colour, style, colour]}
COLUMNS = ['t', 'pt', 'pos_x', 'pos_y', 'v_x', 'v_y']


# --- exact general relativity, in Gullstrand-Painleve time (the flow's) ------------------------------------------

def fallR(tau, r0=START):
  """where a fall from rest at infinity, at r0 at time 0, is after proper time tau"""
  return (r0**1.5 - 1.5*math.sqrt(2*GM)*tau)**(2/3)

def climbR(tau, r0=HOVER):
  """where the ballistic climb at the escape speed from r0 is after proper time tau (the fall reversed)"""
  return (r0**1.5 + 1.5*math.sqrt(2*GM)*tau)**(2/3)

def gpLessSchwarzschild(r):
  """Gullstrand-Painleve less Schwarzschild time at r (outside the horizon)"""
  s = math.sqrt(r/RS)
  return RS/C*(2*s + math.log((s - 1)/(s + 1)))

def lightTime(r0, r1):
  """light straight out from r0 to r1, dr/dt = c(1 - sqrt(rs/r)): (2 rs/c)[s^2/2 + s + ln|s - 1|], s = sqrt(r/rs).
  inside the horizon it goes inward, so r1 < r0 there"""
  F = lambda r: (lambda s: s*s/2 + s + math.log(abs(s - 1)))(math.sqrt(r/RS))
  return 2*RS/C*(F(r1) - F(r0))


# --- the simulation ------------------------------------------------------------------------------------------------

def row(p):
  return (p.t, p.pt, *p.pos, *p.v)

def dtAt(p):
  return STEP*np.linalg.norm(p.pos)/C

def ray(folder, n, t, pos, w, duration=None):
  """light from pos at time t moving at w relative to space: straight out until START (or the centre), or for
  duration; returns (csv path, time it ends, r it ends at)"""
  p = Particle()
  p.pos, p.t = pos.copy(), t
  CALC.initPW(p, w)
  rows, steps, end = [row(p)], 0, None if duration is None else t + duration
  while True:
    r = np.linalg.norm(p.pos)
    if (end is None and r >= START) or r < CENTRE or (end is not None and p.t >= end - 1e-9):
      break
    dt = dtAt(p) if end is None else min(dtAt(p), end - p.t)
    if end is None and r < START and np.linalg.norm(p.pos + p.v*dt) > START:   #land on START
      dt = (START - r)/max(np.dot(p.v, p.pos)/r, 1e-30)
    CALC.move(p, dt)
    steps += 1
    if steps % EVERY == 0:
      rows.append(row(p))
  if rows[-1][0] != p.t:
    rows.append(row(p))
  r = np.linalg.norm(p.pos)
  return rows, p.t, r


def falling(p, until, emitAt, onEmit, rows):
  """move p (falling or climbing) until until(p), landing exactly on each proper time in emitAt for onEmit(p)"""
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
  lines = []
  made = []
  T = fallTime(GM, START, 0.0)
  inner = [2, 1.5, 1.2, 1.05, 1.01, 0.9, 0.5]
  emitAt = [240.0*k for k in range(1, int(fallTime(GM, START, RS)/240) + 1)] + [fallTime(GM, START, r*RS) for r in inner]
  emissions = []
  p = Particle()
  p.pos = np.array([START, 0.0])
  CALC.initPFreefall(p)
  rows = [row(p)]
  falling(p, lambda p: np.linalg.norm(p.pos) < CENTRE, emitAt, lambda p: emissions.append((p.t, p.pt, p.pos.copy())), rows)
  lines.append('fall: from rest at infinity, passing START = 20 rs at t = 0; the horizon at proper time %.2f s (exact),'
               ' %.2f s more to the centre; reached %.3f rs at t %.3f s, proper time %.3f s (exact to there %.3f s)'
               % (fallTime(GM, START, RS), fallTime(GM, RS, 0), np.linalg.norm(p.pos)/RS, p.t, p.pt,
                  fallTime(GM, START, np.linalg.norm(p.pos))))
  made.append((write(folder, 'fall', CALC, rows, COLUMNS, ['falling from rest at infinity, from 20 rs (t = 0) into the'
                     ' hole, moving with the flow (w = 0)', lines[-1]]), COLOURS['object'], 'solid'))
  lines.append('  %-3s %10s %10s %10s %12s %12s %12s %12s' % ('ray', 'sent pt', 'r (rs)', 'exact r', 'back at t',
               'exact', 'gap', 'ratio - 1'))
  last = None
  for n, (t, pt, pos) in enumerate(emissions, 1):
    r = np.linalg.norm(pos)
    rays, end, rEnd = ray(folder, n, t, pos, C*pos/r)
    exactR = fallR(pt)
    inside = r < RS
    if inside:
      exact = t + lightTime(r, rEnd)
      note = 'reaches %.3f rs at t %.3f s (exact %.3f s): it never comes out' % (rEnd/RS, end, exact)
      lines.append('  %-3d %10.3f %10.5f %10.5f   inside: %s' % (n, pt, r/RS, exactR/RS, note))
    else:
      exact = t + lightTime(r, START)
      gap = '' if last is None else '%.3f' % (end - last)
      lines.append('  %-3d %10.3f %10.5f %10.5f %12.3f %12.3f %12s %12.2e' % (n, pt, r/RS, exactR/RS, end, exact, gap,
                   (end - t)/(exact - t) - 1))
      last = end
    made.append((write(folder, 'fallray%d' % n, CALC, rays, COLUMNS,
                       ['light sent straight out at t %g s from %.4f rs by the falling observer' % (t, r/RS), lines[-1]]),
                 COLOURS['inside' if inside else 'ray'], 'solid'))
  writeViewerFiles(folder, 'blackHoles_fall', made, selection=(('pos_x', 't'),), styles=X_T,
                   preferences={'equalAspect': False, 'showBodies': True, 'showSchwarzschild': True, 'showFlow': False,
                                'showPathLegend': False})
  return lines


def flashes(folder):
  lines = []
  made = []
  p = Particle()
  p.pos = np.array([4*RS, 0.0])
  p.t = p.pt = fallTime(GM, START, 4*RS)
  CALC.initPFreefall(p)
  rows = [row(p)]
  at = [3, 1.5, 1.0, 0.6]
  emissions = []
  falling(p, lambda p: np.linalg.norm(p.pos) < CENTRE, [fallTime(GM, START, r*RS) for r in at],
          lambda p: emissions.append((p.t, p.pos.copy())), rows)
  made.append((write(folder, 'flashfall', CALC, rows, COLUMNS, ['falling from rest at infinity, from 4 rs in']),
               COLOURS['object'], 'solid'))
  span = 0.4*RS/C
  for n, (t, pos) in enumerate(emissions):
    r = np.linalg.norm(pos)
    outward = 0
    for k in range(12):
      a = 2*math.pi*k/12
      rays, end, rEnd = ray(folder, k, t, pos, C*np.array([math.cos(a), math.sin(a)]), duration=span)
      outward += rEnd > r
      made.append((write(folder, 'flash%d_%02d' % (n, k), CALC, rays, COLUMNS,
                         ['light from %.2f rs at t %g s, at %d degrees' % (r/RS, t, 30*k)]),
                   COLOURS['inside' if r <= RS else 'ray'], 'solid'))
    lines.append('flash at %.2f rs (space flowing in at %.3fc): %d of 12 rays further out after %.2f s' %
                 (r/RS, math.sqrt(RS/r), outward, span))
  writeViewerFiles(folder, 'blackHoles_flashes', made, preferences={'showFlow': True, 'showPathLegend': False,
                   'showSchwarzschild': True}, frames=CALC,
                   background=('the flow into the hole', 'Space flowing in towards a black hole of 4 million solar'
                               ' masses at the escape speed, u = sqrt(2GM/r), reaching the speed of light at the'
                               ' Schwarzschild radius (1.18e10 m) and faster inside it; g is the acceleration of'
                               ' space falling with it, GM/r^2, inward.'))
  return lines


def probe(folder):
  lines, made = [], []
  Td = fallTime(GM, START, HOVER)
  interval = 300.0
  emissions = []
  emit = lambda leg: (lambda p: emissions.append((leg, p.t, p.pt, p.pos.copy())))
  p = Particle()
  p.pos = np.array([START, 0.0])
  CALC.initPFreefall(p)
  rows = [row(p)]
  grid = [interval*k for k in range(1, int(3*Td/interval) + 2)]
  falling(p, lambda p: p.pt >= Td - 1e-6, [g for g in grid if g < Td] + [Td], lambda p: p.pt < Td - 1e-6 and emit('down')(p), rows)
  landed, rLand = p.t, np.linalg.norm(p.pos)
  #holding still against the flow: v = 0, w = -u, its clock at sqrt(1 - u^2/c^2)
  p.pos = p.pos*HOVER/np.linalg.norm(p.pos)
  CALC.initPV(p, np.zeros(2))
  rate = math.sqrt(1 - (p.u @ p.u)/C**2)
  hold = [g for g in grid if Td <= g < 2*Td]
  dt, steps = 20.0, 0
  while p.pt < 2*Td - 1e-9:
    step = min(dt, (2*Td - p.pt)/rate, ((hold[0] - p.pt)/rate) if hold else dt)
    p.t += step
    p.pt += step*rate
    steps += 1
    if hold and p.pt >= hold[0] - 1e-6:
      rows.append(row(p))
      emit('held')(p)
      hold.pop(0)
    elif steps % 5 == 0:
      rows.append(row(p))
  rows.append(row(p))
  launched = p.t
  u = CALC.flow(p.pos)
  CALC.initPW(p, CALC.addSI(-u, -u))
  lines.append('probe: fell from 20 rs to %.4f rs (exact %.4f) in %.3f s (exact %.3f s) by its clock and the flow\'s;'
               ' held at %.4f rs for %.3f s of its clock (%.3f s of the flow\'s: its clock at %.4f); launched at w = %.5fc'
               ' outward (v = %.5fc)' % (rLand/RS, HOVER/RS, landed, Td, HOVER/RS, Td, launched - landed, rate,
                                         np.linalg.norm(p.w)/C, np.dot(p.v, p.pos)/np.linalg.norm(p.pos)/C))
  falling(p, lambda p: np.linalg.norm(p.pos) >= START, [g for g in grid if g >= 2*Td], emit('up'), rows)
  rTop = np.linalg.norm(p.pos)
  climbExact = fallTime(GM, rTop, HOVER) + 2*(gpLessSchwarzschild(rTop) - gpLessSchwarzschild(HOVER))
  lines.append('  climbed back to %.4f rs: %.3f s by its clock (exact %.3f s; the fall took %.3f s), %.3f s of the'
               ' flow\'s time (exact %.3f s); back at t %.3f s, its clock %.3f s'
               % (rTop/RS, p.pt - 2*Td, fallTime(GM, rTop, HOVER), Td, p.t - launched, climbExact, p.t, p.pt))
  made.append((write(folder, 'probe', CALC, rows, COLUMNS, ['the probe: down from 20 rs to 1.5625 rs, held there, and'
                     ' back out', lines[0], lines[1]]), COLOURS['object'], 'solid'))
  lines.append('  %-3s %-5s %9s %9s %9s %10s %10s %11s %11s %9s %10s' % ('ray', 'leg', 'sent pt', 'sent t', 'exact t', 'r (rs)',
               'exact r', 'back at t', 'exact', 'gap', 'ratio - 1'))
  last = None
  for n, (leg, t, pt, pos) in enumerate(emissions, 1):
    r = np.linalg.norm(pos)
    if leg == 'down':
      et, er = pt, fallR(pt)
    elif leg == 'held':
      et, er = Td + (pt - Td)/rate, HOVER
    else:
      er = climbR(pt - 2*Td)
      et = Td + Td/rate + (pt - 2*Td) + 2*(gpLessSchwarzschild(er) - gpLessSchwarzschild(HOVER))
    rays, end, _ = ray(folder, n, t, pos, C*pos/r)
    exact = et + lightTime(er, START)
    lines.append('  %-3d %-5s %9.1f %9.2f %9.2f %10.5f %10.5f %11.2f %11.2f %9s %10.2e' % (n, leg, pt, t, et, r/RS, er/RS,
                 end, exact, '' if last is None else '%.2f' % (end - last), (end - exact)/exact))
    last = end
    made.append((write(folder, 'proberay%d' % n, CALC, rays, COLUMNS, ['light sent straight out at t %g s from %.4f rs'
                       ' by the probe (%s)' % (t, r/RS, leg), lines[-1]]), COLOURS['ray'], 'solid'))
  writeViewerFiles(folder, 'blackHoles_probe', made, selection=(('pos_x', 't'),), styles=X_T,
                   preferences={'equalAspect': False, 'showBodies': True, 'showSchwarzschild': True, 'showFlow': False,
                                'showPathLegend': False})
  return lines


def main():
  folder = os.path.join(LOG_DIR, 'blackHoles', 'blackHoles_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = ['a %g solar mass hole: rs %.6e m, rs/c %.4f s; the observer who stays put at 20 rs, clock at %.5f'
           % (MASS/MS, RS, RS/C, math.sqrt(1 - RS/START)), '']
  for example in (fall, flashes, probe):
    found = example(folder)
    lines += found + ['']
    print('\n'.join(found), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)
  return folder


if __name__ == '__main__':
  main()
