"""
the four tests of general relativity in the flow model as it now stands (the second-order SpecialFlowCalculator with
adaptive steps), against exact general relativity (engine/exact.py), for docs/part1/tests/. each part can be run on
its own: python3 studies/four_tests.py bending precession orbit shapiro mercury

  bending     light past the Sun (b = 1 solar radius), and past a 1 solar-mass hole at impact parameters down by
              tens to 7 Schwarzschild radii, from 10 AU before to 10 AU after: the bend against GR's exact bending
              for the light's own impact parameter (cL/E: light started b off the axis where space flows along it
              passes a little closer, by u/c); for the Sun also Newtonian gravity at c, the Newtonian flow procedure
              (plain addition) and special relativity with Newton's gravity on the light's energy, each the
              half-size bend
  precession  Mercury's orbit scaled down 10^4, 10^5 and 3 x 10^5 times, at three step sizes: the precession
              against GR's exact precession for the orbit's own periapsis and apoapsis, the difference falling with
              the step
  orbit       an orbit between 20 and 60 Schwarzschild radii, twelve times round, for the viewer (its orbits shaded
              older to newer): about 20 degrees of precession an orbit
  shapiro     radar from the Earth (1 AU) past the Sun to Venus (0.723 AU) and back, the light passing 1 to 30 solar
              radii from the Sun's centre. each leg is aimed (by the secant method) so it arrives exactly at the
              other planet, placed where GR's exact ray with that closest approach would take it; the round trip
              against GR's exact round trip (in Schwarzschild time, which round trips share with the model's), and
              against Shapiro's weak-field formula, which in these coordinates is a constant 2 r_s/c more
  mercury     Mercury's real orbit for a century (415 orbits), its perihelion's angle orbit by orbit, for the
              viewer: the advance against GR's exact 43 arcseconds a century (the Sun alone: the other planets add
              the rest of the observed 574)

writes logs/fourTests/fourTests_<datetime>/ (checks.log and the orbit's viewer files) and, for mercury,
logs/mercuryCentury/mercuryCentury_<datetime>/ (checks.log and the century's viewer files)

run: python3 studies/four_tests.py [parts]      (bending, precession, orbit and shapiro: several minutes;
                                                mercury: about 10 minutes at the default step, more with --fine)
"""
import csv
import math
import os
import sys
import time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import Body, Particle, Config, SpecialFlowCalculator, NewtonianCalculator
from engine.logger import LOG_DIR
from engine.constants import *
from engine.exact import (grDeflectionExact, grPrecessionExact, grRayExact, shapiroDelay, impactParameter, orbitPeriod,
                          schwarzschildRadius)
from studies.compare_step_size import orbit
from studies.compare_second_order import precession, apsis, PERIHELION
from two_body_escapes import writeViewerFiles
from newtonian_flow import NewtonianFlow

RS = schwarzschildRadius(MS)
FRACTION = 3e-4            #the step: each moves at most this fraction of the distance to the Sun
MERCURY_FRACTION = 1e-4    #a century of Mercury: the step's error falls as its square, here to about 1%
SHAPIRO_FRACTION = 1e-4    #finer for radar: its delay is 10^-7 of the light's time, and the steps far out are long
ARCSEC = math.pi/(180*3600)
YEAR = 365.25*86400
BODY_LINES = 'bodies: 1\nbody 1: mass %.6e kg (1 MS)  x 0.000000e+00 m  y 0.000000e+00 m  %%s\n' % MS   #as engine/logger.py


def adaptive(dtMax, fraction=FRACTION):
  config = Config()
  config.dt, config.stepFraction = dtMax, fraction
  return config


#---------------------------------------------------------------- bending

class SpecialRelativistic(NewtonianCalculator):
  """
  special relativity with Newton's gravity as a force on the light's energy, F = (E/c^2) g: then
  dv/dt = g - (g . v) v / c^2, and light keeps to c, its path turned by the part of g across it - half general
  relativity's bend. second order (the midpoint's rates), |v| held at c
  """
  def move(self, p, dt):
    acc = lambda x, v: (lambda g: g - (g @ v)*v/C**2)(self.gravity(x))
    xm = p.pos + p.v*dt/2
    vm = p.v + acc(p.pos, p.v)*dt/2
    p.v = p.v + acc(xm, vm)*dt
    p.v = p.v*C/np.linalg.norm(p.v)
    p.pos = p.pos + vm*dt
    p.pt += dt
    p.t += dt


def bend(start, b, fraction=FRACTION, newton=False, kind=None):
  """
  light from (-start, b) along +x to x = +start: its bend, GR's impact parameter as it starts, closest approach.
  kind: None, the flow model; 'newton', Newtonian gravity at c; 'newtonflow', the Newtonian flow procedure (plain
  addition, studies/newtonian_flow.py, second order); 'special', special relativity with Newton's gravity
  """
  kind = 'newton' if newton else kind
  calc = {'newton': lambda: NewtonianCalculator([Body(MS)]), 'special': lambda: SpecialRelativistic([Body(MS)]),
          'newtonflow': lambda: NewtonianFlow([Body(MS)], order=2)}.get(kind, lambda: SpecialFlowCalculator([Body(MS)], order=2))()
  newton = kind in ('newton', 'special')
  p = Particle()
  p.pos = np.array([-start, b])
  if newton:
    p.v = np.array([C, 0.0])
    p.u = np.zeros(2)
    p.w = p.v.copy()
  else:
    calc.initPW(p, np.array([C, 0.0]))
  bGR = impactParameter(p.pos, p.w, p.u)
  closest = float('inf')
  for dt in calc.steps(p, adaptive(1e9, fraction), 2*start/C):
    calc.move(p, dt)
    closest = min(closest, float(np.linalg.norm(p.pos)))
  w = p.v if newton else p.w
  return math.atan2(-w[1], w[0]), bGR, closest


def bending(lines):
  start = 10*AU
  lines.append('BENDING: light from 10 AU before to 10 AU after, step fraction %g' % FRACTION)
  lines.append('')
  lines.append('  the Sun, b = 1 solar radius:')
  sim, bGR, closest = bend(start, RSUN)
  newt, _, _ = bend(start, RSUN, newton=True)
  nflow, _, _ = bend(start, RSUN, kind='newtonflow')
  special, _, _ = bend(start, RSUN, kind='special')
  exact = grDeflectionExact(bGR)
  lines.append('    flow model %.7e rad (%.4f arcsec); GR exact at its impact parameter %.7e; ratio - 1 %.2e' %
               (sim, sim/ARCSEC, exact, sim/exact - 1))
  lines.append('    Newtonian gravity at c %.7e rad (%.4f arcsec), %.5f of GR; 4GM/c^2 b %.7e' %
               (newt, newt/ARCSEC, newt/exact, 4*G*MS/(C*C*RSUN)))
  lines.append('    Newtonian flow %.7e rad (%.4f arcsec), %.5f of GR' % (nflow, nflow/ARCSEC, nflow/exact))
  lines.append('    special relativity, Newton\'s gravity on the light\'s energy %.7e rad (%.4f arcsec), %.5f of GR' %
               (special, special/ARCSEC, special/exact))
  lines.append('    (closest approach %.0f m; GR\'s impact parameter %.6f of b: u/c at the start)' % (closest, bGR/RSUN))
  lines.append('')
  lines.append('  a 1 solar-mass hole (r_s = %.1f m):' % RS)
  lines.append('  %12s %10s %14s %14s %14s %12s %12s' % ('b (m)', 'b/r_s', 'closest (m)', 'flow model', 'GR exact',
                                                   'ratio - 1', 'finer - 1'))
  worst = 0.0
  for b in (RSUN, RSUN/10, RSUN/100, RSUN/1000, RSUN/10000, 7*RS):
    sim, bGR, closest = bend(start, b)
    fine, bGR2, _ = bend(start, b, FRACTION/3)
    exact, exact2 = grDeflectionExact(bGR), grDeflectionExact(bGR2)
    worst = max(worst, abs(sim/exact - 1))
    lines.append('  %12.6g %10.1f %14.6g %14.7e %14.7e %12.2e %12.2e' % (b, b/RS, closest, sim, exact, sim/exact - 1,
                                                                    fine/exact2 - 1))
    print(lines[-1], flush=True)
  lines.append('  (finer: a third of the step. 4GM/c^2 b, the weak-field bend, is %.1f%% short at 7 r_s)'
               % (100*(1 - 4*G*MS/(C*C*7*RS)/grDeflectionExact(7*RS))))
  lines.append('')
  return worst


#---------------------------------------------------------------- precession

def precessionTable(lines):
  lines.append('PRECESSION: Mercury\'s orbit scaled down, 6 orbits; against GR exact for the orbit\'s own periapsis and'
               ' apoapsis')
  lines.append('  %8s %8s %10s %14s %14s %14s %8s' % ('scale', 'a/r_s', 'fraction', 'flow model', 'GR exact',
                                                'ratio - 1', 'time s'))
  for scale in (1e4, 1e5, 3e5):
    r, v = MERCURY_MAX/scale, MERCURY_SPEED_AT_MAX*math.sqrt(scale)
    a = (MERCURY_MAX + PERIHELION)/2/scale
    period = orbitPeriod(a)
    for fraction in (1e-3, 3e-4, 1e-4):
      t0 = time.time()
      peris, apos, n, wall = orbit(r, v, 7.5*period, adaptive(period/20, fraction))
      rp, ra = np.mean([d for d, _ in peris]), np.mean([d for d, _ in apos])
      measured, exact = precession(peris), grPrecessionExact(rp, ra)
      lines.append('  %8g %8.0f %10g %14.7e %14.7e %14.2e %8.1f' % (scale, a/RS, fraction, measured, exact,
                                                                measured/exact - 1, time.time() - t0))
      print(lines[-1], flush=True)
  lines.append('  (the difference falls as the step squared: the second-order step)')
  lines.append('')


#---------------------------------------------------------------- the orbit, for the viewer

def strongOrbit(folder, lines):
  rp, ra = 20*RS, 60*RS
  a = (rp + ra)/2
  speed = math.sqrt(G*MS*(2/ra - 1/a))      #the Newtonian ellipse's speed at apoapsis
  made = []
  for name, calc, style in (('orbit_flow', SpecialFlowCalculator([Body(MS)], 2), 'solid'),
                            ('orbit_newton', NewtonianCalculator([Body(MS)]), 'dashed')):
    p = Particle()
    p.pos = np.array([ra, 0.0])
    if style == 'solid':
      calc.initPV(p, np.array([0.0, speed]))
    else:
      p.v = np.array([0.0, speed]); p.u = np.zeros(2); p.w = p.v.copy()
    rows, turned, last, n = [(p.t, *p.pos, *p.v)], 0.0, 0.0, 0
    while turned < 12*2*math.pi:
      dt = 0.0005*np.linalg.norm(p.pos)/max(np.linalg.norm(p.v), np.linalg.norm(p.u))
      calc.move(p, dt)
      angle = math.atan2(p.pos[1], p.pos[0])
      turned += (angle - last + math.pi) % (2*math.pi) - math.pi
      last = angle
      n += 1
      if n % 20 == 0:
        rows.append((p.t, *p.pos, *p.v))
    rows.append((p.t, *p.pos, *p.v))
    path = os.path.join(folder, name + '.csv')
    with open(path, 'w', newline='') as f:
      out = csv.writer(f)
      out.writerow(['t', 'pos_x', 'pos_y', 'v_x', 'v_y'])
      out.writerows([['%.10g' % v for v in row] for row in rows])
    with open(path[:-4] + '.log', 'w') as f:
      f.write(BODY_LINES % 'black')
      f.write('an orbit from apoapsis at 60 r_s with the Newtonian ellipse\'s speed there (periapsis 20 r_s), twelve'
              ' times round: %s\n' % ('the flow model' if style == 'solid' else 'Newtonian gravity'))
    made.append((path, '#2a78d6', style))
  writeViewerFiles(folder, 'orbit', made, preferences={'showFlow': True, 'graduateOrbits': True},
                   frames=SpecialFlowCalculator([Body(MS)], 2))
  lines.append('ORBIT: 20 to 60 r_s, twelve times round, written for the viewer (orbit.full.json)')
  lines.append('')


#---------------------------------------------------------------- Shapiro

def shoot(calc, start, target, aim, fraction):
  """light from start aimed at angle aim, until it crosses target's distance from the Sun on the way out: the angle
  it misses target by there (rad), the time (s), and its closest approach"""
  p = Particle()
  p.pos = start.copy()
  calc.initPW(p, C*np.array([math.cos(aim), math.sin(aim)]))
  rT = float(np.linalg.norm(target))
  closest = float('inf')
  r = float(np.linalg.norm(p.pos))
  for dt in calc.steps(p, adaptive(1e9, fraction)):
    t0, pos0, r0 = p.t, p.pos.copy(), r
    calc.move(p, dt)
    r = float(np.linalg.norm(p.pos))
    closest = min(closest, r)
    if r > r0 and r >= rT:
      f = (rT - r0)/(r - r0)
      pos = pos0 + f*(p.pos - pos0)
      miss = (math.atan2(pos[1], pos[0]) - math.atan2(target[1], target[0]) + math.pi) % (2*math.pi) - math.pi
      return miss, t0 + f*(p.t - t0), closest
  raise RuntimeError('never arrived')


def leg(calc, start, target, fraction):
  """the light's time from start to target, aimed by the secant method until it arrives within 1e-14 rad"""
  d = target - start
  a0 = math.atan2(d[1], d[0])
  a1 = a0 + 1e-6
  m0, t, c = shoot(calc, start, target, a0, fraction)
  m1, t, c = shoot(calc, start, target, a1, fraction)
  for _ in range(30):
    if abs(m1) < 1e-14 or m1 == m0:
      break
    a0, a1, m0 = a1, a1 - m1*(a1 - a0)/(m1 - m0), m1
    m1, t, c = shoot(calc, start, target, a1, fraction)
  return t, c, m1


def shapiro(lines):
  rE, rV = AU, 0.723*AU
  calc = SpecialFlowCalculator([Body(MS)], order=2)
  gp = lambda r: RS/C*(2*math.sqrt(r/RS) + math.log((math.sqrt(r/RS) - 1)/(math.sqrt(r/RS) + 1)))
  lines.append('SHAPIRO: radar from the Earth (1 AU) past the Sun to Venus (0.723 AU) and back; each planet placed where'
               ' GR\'s exact ray with this closest approach takes it; step fraction %g' % SHAPIRO_FRACTION)
  lines.append('  times in seconds; delay = round trip less the straight-line distance there and back at c')
  lines.append('  %6s %11s %11s %13s %13s %11s %13s %13s %11s' % ('r0/Rsun', 'out', 'back', 'delay model', 'delay GR',
                                                          'ratio - 1', 'finer - 1', 'Shapiro', 'GR/Shapiro'))
  rows = []
  for k in (1, 2, 5, 10, 20, 30):
    r0 = k*RSUN
    pe, te = grRayExact(r0, rE)
    pv, tv = grRayExact(r0, rV)
    E = rE*np.array([math.cos(math.pi/2 + pe), math.sin(math.pi/2 + pe)])
    V = rV*np.array([math.cos(math.pi/2 - pv), math.sin(math.pi/2 - pv)])
    flat = 2*np.linalg.norm(E - V)/C
    out, closest, _ = leg(calc, E, V, SHAPIRO_FRACTION)
    back, _, _ = leg(calc, V, E, SHAPIRO_FRACTION)
    outF, _, _ = leg(calc, E, V, SHAPIRO_FRACTION/3)
    backF, _, _ = leg(calc, V, E, SHAPIRO_FRACTION/3)
    exact = 2*(te + tv) - flat
    model, fine = out + back - flat, outF + backF - flat
    weak = shapiroDelay(rE, rV, flat*C/2)
    rows.append((k, out, back, model, exact, weak))
    lines.append('  %6g %11.6f %11.6f %13.7e %13.7e %11.2e %13.2e %13.7e %11.5f' %
                 (k, out, back, model, exact, model/exact - 1, fine/exact - 1, weak, exact/weak))
    print(lines[-1], flush=True)
  lines.append('  out - back is the two ends\' clocks: the model runs on Gullstrand-Painleve time, which differs from'
               ' Schwarzschild time by %.6f s at the Earth and %.6f s at Venus, so out - back = 2 x %.6f s plus the'
               ' (small) asymmetry of the Shapiro delay itself; measured %.6f s at 1 solar radius'
               % (gp(rE), gp(rV), gp(rE) - gp(rV), rows[0][1] - rows[0][2]))
  lines.append('  Shapiro\'s formula, (4GM/c^3) ln((rE + rV + R)/(rE + rV - R)), with R the straight distance in these'
               ' (Schwarzschild) coordinates, is GR\'s delay plus a constant 2 r_s/c = %.3e s: %s' %
               (2*RS/C, ', '.join('%.3e' % (w - e) for *_, e, w in rows)))
  lines.append('  the pattern the 1960s experiment measured, the delay\'s change from 30 solar radii in:')
  for k, out, back, model, exact, weak in rows:
    lines.append('    %4g Rsun: model %.7e s, GR %.7e s, Shapiro %.7e s' % (k, model - rows[-1][3], exact - rows[-1][4],
                                                                       weak - rows[-1][5]))
  lines.append('')


#---------------------------------------------------------------- Mercury, a century

def mercuryOrbits(fraction, orbits):
  """Mercury's real orbit, the Sun alone, for so many orbits at this step: its perihelia (time, distance, position),
  aphelia, and the wall time"""
  calc = SpecialFlowCalculator([Body(MS)], order=2)
  p = Particle()
  p.pos = np.array([0.0, MERCURY_MAX])
  calc.initPV(p, np.array([MERCURY_SPEED_AT_MAX, 0.0]))
  period = orbitPeriod((MERCURY_MAX + PERIHELION)/2)
  last, peris, apos = [], [], []
  t0 = time.time()
  for dt in calc.steps(p, adaptive(period/20, fraction), (orbits + 0.6)*period):
    calc.move(p, dt)
    last = (last + [(p.t, float(np.linalg.norm(p.pos)), p.pos.copy())])[-3:]
    if len(last) == 3:
      (_, a, _), (_, b, _), (_, c, _) = last
      if b < a and b <= c:
        peris.append(apsis([x[0] for x in last], [x[1] for x in last], [x[2] for x in last]))
        if len(peris) % 50 == 0:
          print('  %d orbits, %.0f s' % (len(peris), time.time() - t0), flush=True)
      if b > a and b >= c:
        apos.append(apsis([x[0] for x in last], [x[1] for x in last], [x[2] for x in last]))
  return peris, apos, time.time() - t0


def mercuryFit(peris, apos):
  """the perihelion's advance orbit by orbit (rad, from the first), its fitted rate (rad an orbit), GR's exact rate
  for the orbit's own perihelion and aphelion, and the orbit's period"""
  ts = np.array([t for t, _, _ in peris])
  angles = -np.unwrap([math.atan2(q[1], q[0]) for _, _, q in peris])     #clockwise orbit: forward is clockwise
  advance = angles - angles[0]
  slope = np.polyfit(np.arange(len(advance)), advance, 1)[0]
  rp, ra = np.mean([r for _, r, _ in peris]), np.mean([r for _, r, _ in apos])
  return ts, advance, slope, grPrecessionExact(rp, ra), float(np.mean(np.diff(ts))), rp, ra


def mercurySteps():
  """Mercury's real orbit, 10 orbits at smaller and smaller steps: the step's own error is about the same angle an
  orbit at every scale (4e-8 rad at 3e-4), which for the real orbit's 5e-7 is large; it falls as the step squared"""
  folder = os.path.join(LOG_DIR, 'mercurySteps', 'mercurySteps_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = ['MERCURY\'S REAL ORBIT, 10 orbits at each step: the perihelion\'s advance against GR exact for the orbit',
           '  %10s %16s %16s %12s %14s %8s' % ('fraction', 'rad an orbit', 'GR exact', 'ratio - 1', 'arcsec/century', 'time s')]
  for fraction in (3e-4, 1e-4, 3e-5, 1e-5):
    peris, apos, wall = mercuryOrbits(fraction, 10)
    ts, advance, slope, exact, orbitTime, rp, ra = mercuryFit(peris, apos)
    lines.append('  %10g %16.8e %16.8e %12.2e %14.4f %8.0f' % (fraction, slope, exact, slope/exact - 1,
                                                          slope/orbitTime*100*YEAR/ARCSEC, wall))
    print(lines[-1], flush=True)
  with open(os.path.join(folder, 'checks.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines))
  print('written to', folder)


def mercury(fraction):
  folder = os.path.join(LOG_DIR, 'mercuryCentury', 'mercuryCentury_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  period = orbitPeriod((MERCURY_MAX + PERIHELION)/2)
  t0 = time.time()
  peris, apos, wall = mercuryOrbits(fraction, int(math.ceil(100*YEAR/period)))
  ts, advance, slope, exact, orbitTime, rp, ra = mercuryFit(peris, apos)
  perCentury = lambda perOrbit: perOrbit/orbitTime*100*YEAR/ARCSEC
  lines = ['MERCURY: its real orbit, %d orbits (a century), step fraction %g, %.0f s' % (len(peris), fraction, time.time() - t0),
           '  periapsis %.6e m, apoapsis %.6e m, orbit %.4f days' % (rp, ra, orbitTime/86400),
           '  perihelion advance (a straight line fitted orbit by orbit): %.7e rad an orbit, %.4f arcsec a century' %
           (slope, perCentury(slope)),
           '  GR exact for this orbit: %.7e rad an orbit, %.4f arcsec a century; ratio - 1 %.2e' %
           (exact, perCentury(exact), slope/exact - 1),
           '  (scatter of the orbit-by-orbit angles about the line: %.2e rad)' %
           float(np.std(advance - slope*np.arange(len(advance))))]
  #the viewer: the perihelion's advance (arcsec) against time (years), the model's orbit by orbit and GR's line
  model = os.path.join(folder, 'perihelion_flow.csv')
  with open(model, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'years (yr)', 'advance (arcsec)'])
    for t, adv in zip(ts, advance):
      out.writerow(['%.10g' % t, '%.8g' % ((t - ts[0])/YEAR), '%.8g' % (adv/ARCSEC)])
  gr = os.path.join(folder, 'perihelion_gr.csv')
  with open(gr, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'years (yr)', 'advance (arcsec)'])
    for t in (ts[0], ts[-1]):
      out.writerow(['%.10g' % t, '%.8g' % ((t - ts[0])/YEAR), '%.8g' % ((t - ts[0])/orbitTime*exact/ARCSEC)])
  for path, text in ((model, 'the flow model: Mercury\'s perihelion, orbit by orbit, its angle from the first'),
                     (gr, 'general relativity, exact: %.4f arcsec a century' % perCentury(exact))):
    with open(path[:-4] + '.log', 'w') as f:
      f.write(BODY_LINES % 'white' + text + '\n')
  writeViewerFiles(folder, 'mercuryCentury', [(model, '#2a78d6', 'solid'), (gr, '#eb6834', 'dashed')],
                   selection=(('years (yr)', 'advance (arcsec)'),),
                   styles=lambda colour, style='solid': {'years (yr) / advance (arcsec)': [colour, style, colour]},
                   preferences={'equalAspect': False, 'showBodies': False, 'showSchwarzschild': False, 'showFlow': False})
  with open(os.path.join(folder, 'checks.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines))
  print('written to', folder)


def main(parts):
  if 'mercury' in parts:
    mercury(MERCURY_FRACTION)
  if 'mercurysteps' in parts:
    mercurySteps()
  rest = [p for p in parts if p in ('bending', 'precession', 'orbit', 'shapiro')]
  if not rest:
    return
  folder = os.path.join(LOG_DIR, 'fourTests', 'fourTests_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = ['the four tests in the flow model (second order, adaptive steps) against exact general relativity', '']
  if 'bending' in rest:
    bending(lines)
  if 'precession' in rest:
    precessionTable(lines)
  if 'orbit' in rest:
    strongOrbit(folder, lines)
  if 'shapiro' in rest:
    shapiro(lines)
  with open(os.path.join(folder, 'checks.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main(sys.argv[1:] or ['bending', 'precession', 'orbit', 'shapiro', 'mercury'])
