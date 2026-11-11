"""
a set of paths round the two holes of studies/two_body_escapes.py (one solar mass each, fixed at x = -0.5 AU and
+0.5 AU) in the flow model, with the flow along the net g (Calculator.direction 'g', the default) or another
direction given on the command line ('eikonal': down zero-energy paths, no curl): falls, orbits round one hole,
orbits round both, flybys, escapes and light

each runs in the flow model (SpecialFlowCalculator, second order) and, unless it is light, again under newtonian
gravity (RK4) from the same start for comparison. both stop at 1 Schwarzschild radius from a hole (captured), 20 AU
from the centre of mass (escaped), the test's time limit or the step limit

starts: 'rest' still in the flat background (v = 0), 'free' moving with space (w = 0: a fall from rest at infinity),
'v' a velocity through the background, 'w' a velocity relative to space (light: |w| = c). a circular orbit started
at the newtonian speed sqrt(GM/r) round one hole is exactly circular in GR too (Kepler's third law holds exactly in
Schwarzschild time, which is the flow model's time)

for orbits the periapsides and apoapsides are found round the test's centre (a hole, or the centre of mass) and the
periapsis precession measured; round one hole it is compared with GR's for that hole alone (engine/exact.py), and
light's bend with GR's at its impact parameter

writes logs/twoBodyTests/twoBodyTests_<datetime>/ (twoBodyTests_<direction>_<datetime> for a direction other than g): a csv for each test (and <name>_newton.csv), summary.log, and a
viewer config for each group (flow model solid, newtonian dashed)

run: python3 studies/two_body_tests.py [direction]      (e.g. eikonal)
"""
import csv
import json
import math
import os
import sys
import time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import SpecialFlowCalculator, Particle
from engine.logger import Log, LOG_DIR
from engine.constants import *
from engine.integrate import rk4Gravity
from engine.vectors import length
from engine.exact import grPrecessionExact, grDeflectionExact, schwarzschildRadius
from two_body_escapes import BODIES, writeViewerFiles

DESCRIPTION = 'along g'        #the flow's direction, for the logs (set by main)
RS = schwarzschildRadius(MS)   #each hole's Schwarzschild radius
YEAR = 365.25*DAY
STEP = 0.002          #each step moves about this fraction of the distance to the nearest hole
EVERY = 20            #steps between csv rows
MAX_STEPS = 3000000
ESCAPE = 20*AU        #escaped this far from the centre of mass
CAPTURE = 1.0         #captured this many Schwarzschild radii from a hole's centre
COLOURS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948', '#5b6770']

LEFT, RIGHT = BODIES[0].pos, BODIES[1].pos
CENTRE = np.array([0.0, 0.0])
X, Y = np.array([1.0, 0.0]), np.array([0.0, 1.0])


def au(x, y):
  return np.array([x, y])*AU


def tangent(rel, sense=1):
  """the unit vector round a centre, anticlockwise (sense 1) or clockwise (-1), at rel from it"""
  return sense*np.array([-rel[1], rel[0]])/length(rel)


def circular(centre, r, gm, sense=1, angle=0.0):
  """a start r from centre at angle, at the circular speed sqrt(gm/r)"""
  rel = r*np.array([math.cos(angle), math.sin(angle)])
  return centre + rel, math.sqrt(gm/r)*tangent(rel, sense)


def periapsisStart(centre, peri, e, gm):
  """a start at the periapsis of a newtonian orbit of eccentricity e round centre (on its +x side)"""
  return centre + peri*X, math.sqrt(gm*(1 + e)/peri)*Y


def period(r, gm):
  return 2*math.pi*math.sqrt(r**3/gm)


GM1, GM2 = G*MS, 2*G*MS


def tests():
  """(group, name, description, start kind, position, velocity, centre for apsides or None, time limit, circular)"""
  out = []
  add = lambda *t: out.append(t)
  #falls
  add('falls', 'fallOutside', 'from rest at (2, 0) AU, outside the pair on the axis', 'rest', au(2, 0), None, None, 5*YEAR, False)
  add('falls', 'fallYAxis', 'from rest at (0, 1) AU, on the line half way between', 'rest', au(0, 1), None, None, 5*YEAR, False)
  add('falls', 'fallBetween', 'from rest at (0.1, 0) AU, between the holes', 'rest', au(0.1, 0), None, None, 5*YEAR, False)
  add('falls', 'fallOffMiddle', 'from rest at (0.05, 0.5) AU, just off the half-way line', 'rest', au(0.05, 0.5), None, None, 5*YEAR, False)
  add('falls', 'fallAbove', 'from rest at (0.5, 0.2) AU, above the right hole', 'rest', au(0.5, 0.2), None, None, 5*YEAR, False)
  add('falls', 'fallClose', 'from rest 10 Schwarzschild radii out from the right hole', 'rest', RIGHT + 10*RS*X, None, None, YEAR, False)
  add('falls', 'freeFallAxis', 'moving with space (w = 0) from (5, 0) AU', 'free', au(5, 0), None, None, 5*YEAR, False)
  add('falls', 'freeFallYAxis', 'moving with space (w = 0) from (0, 5) AU, down the half-way line', 'free', au(0, 5), None, None, 5*YEAR, False)
  #orbits round the right hole
  for r in (0.05, 0.1, 0.2):
    pos, v = circular(RIGHT, r*AU, GM1)
    add('oneHole', 'circle%gAU' % r, 'circular, %g AU from the right hole' % r, 'v', pos, v, RIGHT, 20*period(r*AU, GM1), True)
  pos, v = periapsisStart(RIGHT, 0.025*AU, 0.5, GM1)
  add('oneHole', 'ellipse0.05AU', 'periapsis 0.025 AU, e 0.5 (newtonian), round the right hole', 'v', pos, v, RIGHT, 20*period(0.05*AU, GM1), False)
  for k in (10, 4, 2.8):
    pos, v = circular(RIGHT, k*RS, GM1)
    add('nearHole', 'circle%grs' % k, 'circular, %g Schwarzschild radii from the right hole%s' % (k, ' (inside the ISCO, 3)' if k < 3 else ''),
        'v', pos, v, RIGHT, 30*period(k*RS, GM1), True)
  pos, v = circular(RIGHT, 10*RS, GM1, -1)
  add('nearHole', 'circle10rsBack', 'as circle10rs, going round clockwise', 'v', pos, v, RIGHT, 30*period(10*RS, GM1), True)
  for peri, e in ((20, 0.3), (5, 0.5)):
    pos, v = periapsisStart(RIGHT, peri*RS, e, GM1)
    a = peri*RS/(1 - e)
    add('nearHole', 'ellipse%grs' % peri, 'periapsis %g Schwarzschild radii, e %g (newtonian), round the right hole' % (peri, e),
        'v', pos, v, RIGHT, 20*period(a, GM1), False)
  #orbits round both
  for r in (1.2, 2, 3, 5):
    pos, v = circular(CENTRE, r*AU, GM2, angle=math.pi/2)
    add('bothHoles', 'around%gAU' % r, 'circular (for 2 MS at the centre), %g AU from the centre of mass' % r, 'v', pos, v, CENTRE,
        10*period(r*AU, GM2), True)
  pos, v = periapsisStart(CENTRE, 1.5*AU, 0.5, GM2)
  add('bothHoles', 'aroundEllipse', 'periapsis 1.5 AU, e 0.5, round the centre of mass', 'v', pos, v, CENTRE, 10*period(3*AU, GM2), False)
  pos = au(0, -2)
  add('bothHoles', 'aroundBack2AU', 'as around2AU, going round clockwise', 'v', pos, math.sqrt(GM2/(2*AU))*X, CENTRE, 10*period(2*AU, GM2), True)
  #flybys and escapes
  start = au(0, 0.01)
  speed = 0.8*math.sqrt(4*GM1/(0.5*AU))
  add('others', 'tangle', 'from (0, 0.01) AU at 0.8 of the local escape speed, heading up and right at 45 degrees', 'v', start,
      speed*np.array([1, 1])/math.sqrt(2), None, 10*YEAR, False)
  add('others', 'flyby', 'from (5, 0.05) AU at 50 km/s towards -x, past the right hole', 'v', au(5, 0.05), -50000*X, None, 5*YEAR, False)
  add('others', 'escapeExact', 'from 10 Schwarzschild radii outside the left hole, outwards at the escape speed |u|', 'escape',
      LEFT - 10*RS*X, -X, None, 50*YEAR, False)
  add('others', 'escapeFast', 'from 10 Schwarzschild radii above the right hole, upwards at 1.1 |u|', 'escape',
      RIGHT + 10*RS*Y, 1.1*Y, None, 50*YEAR, False)
  #light
  for b in (2.5, 3, 10):
    add('light', 'light%grs' % b, 'light from (-3, %g Schwarzschild radii) along +x, past the left hole' % b, 'w',
        np.array([-3*AU, b*RS]), C*X, None, YEAR, False)
  add('light', 'lightYAxis', 'light from (0, -3) AU up the half-way line', 'w', au(0, -3), C*Y, None, YEAR, False)
  add('light', 'lightOut', 'light from 1.5 Schwarzschild radii outside the right hole, outwards', 'w', RIGHT + 1.5*RS*X, C*X,
      None, YEAR, False)
  return out


class Apsides:
  """turning points of the distance from a centre: (distance, angle, t), each one interpolated to its turning point"""

  def __init__(self, centre):
    self.centre = centre
    self.recent = []
    self.peri, self.apo = [], []

  def add(self, pos, t):
    rel = pos - self.centre
    self.recent = (self.recent + [(length(rel), math.atan2(rel[1], rel[0]), t)])[-3:]
    if len(self.recent) < 3:
      return
    (d0, a0, t0), (d1, a1, t1), (d2, a2, t2) = self.recent
    if not ((d1 < d0 and d1 <= d2) or (d1 > d0 and d1 >= d2)):
      return
    curve = d0 - 2*d1 + d2
    f = (d0 - d2)/(2*curve) if curve else 0.0   #where the parabola through the three turns, -1 to 1 about d1
    turn = lambda a, b: (b - a + math.pi) % (2*math.pi) - math.pi
    point = (d1 - (d0 - d2)**2/(8*curve) if curve else d1, a1 + f*turn(a0, a2)/2, t1 + f*(t2 - t0)/2)
    (self.peri if d1 < d0 else self.apo).append(point)

  def summary(self, sense):
    """mean periapsis and apoapsis, the mean periapsis precession per orbit (rad, positive the way it goes round) and
    the mean time between periapsides; None where there are too few"""
    mean = lambda xs: sum(xs)/len(xs) if xs else None
    turn = lambda a, b: sense*((b - a + math.pi) % (2*math.pi) - math.pi)
    p = self.peri
    return {'peri': mean([d for d, _, _ in p]), 'apo': mean([d for d, _, _ in self.apo]), 'orbits': max(len(p) - 1, 0),
            'precession': mean([turn(a, b) for (_, a, _), (_, b, _) in zip(p, p[1:])]),
            'period': (p[-1][2] - p[0][2])/(len(p) - 1) if len(p) > 1 else None}


def stopReason(pos):
  if not np.all(np.isfinite(pos)):
    return 'not finite'
  for name, b in (('left', LEFT), ('right', RIGHT)):
    if length(pos - b) < CAPTURE*RS:
      return 'captured by ' + name
  if length(pos) > ESCAPE:
    return 'escaped'
  return None


def runFlow(calc, test):
  """the flow model run: rows (t, pt, pos, v, w), why it stopped, steps, the run's record"""
  group, name, text, kind, pos, vel, centre, limit, round_ = test
  p = Particle()
  p.pos = np.array(pos, dtype=float)
  if kind == 'rest':
    calc.initPV(p, np.array([0.0, 0.0]))
  elif kind == 'free':
    calc.initPFreefall(p)
  elif kind == 'escape':
    calc.initPV(p, vel*length(calc.flow(p.pos)))   #vel is the direction times a multiple of |u|
  elif kind == 'w':
    calc.initPW(p, np.array(vel, dtype=float))
  else:
    calc.initPV(p, np.array(vel, dtype=float))
  start = (p.v.copy(), p.w.copy())
  rows = [(p.t, p.pt, p.pos.copy(), p.v.copy(), p.w.copy())]
  rec = record(centre, p.pos, p.v)
  reason = None
  for i in range(1, MAX_STEPS + 1):
    dt = calc.stepSize(p, STEP)
    if p.t + dt > limit:
      dt = limit - p.t
    calc.move(p, dt)
    rec.step(p.pos, p.t)
    reason = stopReason(p.pos) or ('time limit' if p.t >= limit*(1 - 1e-12) else None)
    if reason or i % EVERY == 0:
      rows.append((p.t, p.pt, p.pos.copy(), p.v.copy(), p.w.copy()))
    if reason:
      return rows, reason, i, rec, start
  return rows, 'step limit', MAX_STEPS, rec, start


def runNewton(calc, test, v0):
  """the same start under newtonian gravity (RK4), at the flow run's starting v; rows (t, t, pos, v, v)"""
  group, name, text, kind, pos, vel, centre, limit, round_ = test
  pos, v, t = np.array(pos, dtype=float), np.array(v0, dtype=float), 0.0
  rows = [(t, t, pos, v, v)]
  rec = record(centre, pos, v)
  for i in range(1, MAX_STEPS + 1):
    speed = max(length(v), length(calc.flow(pos)))   #as the flow run's steps
    dt = min(STEP*calc.nearest(pos)/speed, limit - t)
    pos, v = rk4Gravity(calc, pos, v, dt)
    t += dt
    rec.step(pos, t)
    reason = stopReason(pos) or ('time limit' if t >= limit*(1 - 1e-12) else None)
    if reason or i % EVERY == 0:
      rows.append((t, t, pos, v, v))
    if reason:
      return rows, reason, i, rec
  return rows, 'step limit', MAX_STEPS, rec


class record:
  """what a run did: the closest it came to each hole, and its apsides round its centre"""

  def __init__(self, centre, pos, v):
    self.closest = [length(pos - LEFT), length(pos - RIGHT)]
    self.apsides = Apsides(centre) if centre is not None else None
    self.sense = 1.0
    if centre is not None:
      rel = pos - centre
      self.sense = 1.0 if rel[0]*v[1] - rel[1]*v[0] >= 0 else -1.0
      self.apsides.add(pos, 0.0)

  def step(self, pos, t):
    self.closest = [min(self.closest[0], length(pos - LEFT)), min(self.closest[1], length(pos - RIGHT))]
    if self.apsides:
      self.apsides.add(pos, t)


def writeCsv(path, rows):
  with open(path, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'proper_t', 'pos_x', 'pos_y', 'v_x', 'v_y', 'w_x', 'w_y'])
    for t, pt, pos, v, w in rows:
      out.writerow([t, pt, pos[0], pos[1], v[0], v[1], w[0], w[1]])


def writeLog(path, lines):
  """the .log beside a csv: the bodies, in Log.logBodies' form (the viewer reads them to draw the bodies and their
  backgrounds), then lines"""
  with open(path, 'w') as f:
    f.write('bodies: %d\n' % len(BODIES))
    for i, b in enumerate(BODIES):
      f.write('body %d: mass %.6e kg (%.6g MS)  x %.6e m  y %.6e m  %s\n' % (i + 1, b.mass, b.mass/MS, b.x, b.y,
              'black' if b.black else 'white'))
    f.write('flow direction: %s\n' % DESCRIPTION + ''.join(line + '\n' for line in lines))


def distance(d):
  """a distance in Schwarzschild radii when close, else AU"""
  return '%.3g rs' % (d/RS) if d < 1e-4*AU else '%.4g AU' % (d/AU)


def duration(t):
  return '%.4g s' % t if t < DAY else '%.4g d' % (t/DAY) if t < YEAR else '%.4g yr' % (t/YEAR)


def main(direction='g'):
  global DESCRIPTION
  folder = os.path.join(LOG_DIR, 'twoBodyTests', 'twoBodyTests_' + ('' if direction == 'g' else direction + '_')
                        + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  calc = SpecialFlowCalculator(BODIES, 2, direction)   #by default the flow along the net g
  DESCRIPTION = calc.describeDirection()
  warnings = []
  calc.warn = warnings.append
  summaries, groups = [], {}
  for test in tests():
    group, name, text, kind, pos, vel, centre, limit, round_ = test
    began = time.time()
    rows, reason, steps, rec, (v0, w0) = runFlow(calc, test)
    path = os.path.join(folder, name + '.csv')
    writeCsv(path, rows)
    writeLog(path[:-4] + '.log', [text, 'flow model (SpecialFlowCalculator, second order): %s after %d steps' % (reason, steps)])
    colour = COLOURS[sum(1 for other in summaries if other['group'] == group) % len(COLOURS)]
    groups.setdefault(group, []).append((path, colour, 'solid'))
    s = {'group': group, 'name': name, 'text': text, 'reason': reason, 'steps': steps, 't': rows[-1][0], 'pt': rows[-1][1],
         'end': list(rows[-1][2]/AU), 'v': length(rows[-1][3])/C, 'w': length(rows[-1][4])/C, 'closest': rec.closest,
         'v0': length(v0)/C, 'w0': length(w0)/C}
    if rec.apsides:
      s['apsides'] = rec.apsides.summary(rec.sense)
      a = s['apsides']
      if group in ('oneHole', 'nearHole') and not round_ and a['peri'] and a['apo']:
        s['gr'] = grPrecessionExact(a['peri'], a['apo'])
    if kind == 'w' and reason == 'escaped':
      s['bend'] = math.atan2(rows[-1][3][1], rows[-1][3][0]) - math.atan2(vel[1], vel[0])
      s['grBend'] = grDeflectionExact(abs(pos[1])) if 0 < abs(pos[1]) < AU else None
    if kind != 'w':
      nrows, nreason, nsteps, nrec = runNewton(calc, test, v0)
      npath = os.path.join(folder, name + '_newton.csv')
      writeCsv(npath, nrows)
      writeLog(npath[:-4] + '.log', [text, 'newtonian (RK4): %s after %d steps' % (nreason, nsteps)])
      groups[group].append((npath, colour, 'dashed'))
      s['newton'] = {'reason': nreason, 'steps': nsteps, 't': nrows[-1][0], 'end': list(nrows[-1][2]/AU),
                     'v': length(nrows[-1][3])/C, 'closest': nrec.closest}
      if nrec.apsides:
        s['newton']['apsides'] = nrec.apsides.summary(nrec.sense)
    s['seconds'] = time.time() - began
    summaries.append(s)
    print('%-16s %-14s %8d steps  t %-10s  (newton: %s)  %.1fs' % (name, reason, steps, duration(s['t']),
          s['newton']['reason'] if 'newton' in s else '-', s['seconds']), flush=True)
  lines = report(summaries, DESCRIPTION)
  if warnings:
    lines += ['', '%d flow warnings, e.g. %s' % (len(warnings), warnings[0])]
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  with open(os.path.join(folder, 'summary.json'), 'w') as f:
    json.dump(summaries, f, indent=1, default=float)
  print('\n'.join(lines))
  for group, made in groups.items():
    writeViewerFiles(folder, 'twoBodyTests_' + group, made)
  return folder


def report(summaries, description='along g'):
  lines = ['paths round two 1 MS holes at x = -0.5 and +0.5 AU, the flow %s (flow model) and newtonian' % description, '']
  for s in summaries:
    lines.append('%s  [%s]  %s' % (s['name'], s['group'], s['text']))
    lines.append('  flow:   %-18s t %-11s proper %-11s end (%.4g, %.4g) AU  |v| %.4gc  closest left %s right %s' % (
      s['reason'], duration(s['t']), duration(s['pt']), s['end'][0], s['end'][1], s['v'], distance(s['closest'][0]),
      distance(s['closest'][1])))
    if 'newton' in s:
      n = s['newton']
      lines.append('  newton: %-18s t %-11s %-18s end (%.4g, %.4g) AU  |v| %.4gc  closest left %s right %s' % (
        n['reason'], duration(n['t']), '', n['end'][0], n['end'][1], n['v'], distance(n['closest'][0]), distance(n['closest'][1])))
    for label, a in (('flow', s.get('apsides')), ('newton', s.get('newton', {}).get('apsides'))):
      if a and a['peri']:
        lines.append('  %-6s  apsides: periapsis %s apoapsis %s, %d orbits, period %s, precession %s' % (
          label, distance(a['peri']), distance(a['apo']) if a['apo'] else '-', a['orbits'],
          duration(a['period']) if a['period'] else '-',
          '%.6g deg/orbit' % math.degrees(a['precession']) if a['precession'] is not None else '-'))
    if s.get('gr') is not None:
      lines.append('  GR for the right hole alone at those apsides: %.6g deg/orbit' % math.degrees(s['gr']))
    if s.get('bend') is not None:
      lines.append('  bend %.6g deg%s' % (math.degrees(s['bend']),
                   ', GR for one hole at b: %.6g deg' % math.degrees(s['grBend']) if s.get('grBend') else ''))
    lines.append('')
  return lines


if __name__ == '__main__':
  main(sys.argv[1] if len(sys.argv) > 1 else 'g')
