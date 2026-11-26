"""
the players for Part 2's Seams page: viewer runs of the seam investigation (studies/seam_crossing.py, seam_rules.py,
seam_moving.py, seam_energy.py, seam_frames.py), each a set of paths with a backgrounds file of the flow where it
has one (engine/backgrounds.py), in one folder:

  crossing     light crossing the seam between two solar masses 200,000 km apart, the model with space
               curved (solid) against general relativity (dashed)
  without      particles crossing it with the engine's rule, and with the momentum kept as it is (no rule)
  orbit        an orbit round both bodies crossing the seam 27 times, the model against GR; and its energy over the run
  placement    the seam moved (the constant between the two bodies' S), and light crossing each
  observers    one body, with observers arriving from one direction on parabolas: their seam, the half-line behind it
  moving       a body moving at 0.1 c, the model's time inside a boundary and GR's outside: a boundary where the two
               times agree, and a circle where they don't, against GR

run: python3 studies/seam_players.py     (a few minutes; writes logs/seamPlayers/seamPlayers_<datetime>/, then
     python3 scripts/publish_run.py logs/seamPlayers/<run> seams)
"""
import csv
import math
import os
import pickle
import sys
import time
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import Body, Particle, SpecialFlowCalculator
from engine.metric import MetricCalculator, FlowSpacetime, PostNewtonian
from engine.logger import LOG_DIR
from engine.constants import MS, C, G
import seam_crossing as sc
import seam_moving as sm

D, HALF = sc.D, sc.HALF
LIMIT = 600                 #s of computing a path may take before it is stopped
BLUE, ORANGE, GREEN, AMBER, PURPLE, PINK, GREY = '#2a78d6', '#eb6834', '#1baf7a', '#d6a21e', '#8a5cd8', '#d64c7a', '#7a7a74'

FLOW_DESCRIPTION = ('The potential flow round two bodies of a solar mass each, 200,000 km apart and at rest: space falls'
                    ' in from far away down the paths of things falling from rest, each body has a region of its own,'
                    ' and the dashed seam is where the regions meet. Between the bodies, space flows away from the seam'
                    ' on both sides. Arrows show the flow u; the colour its speed.')


def shiftedCalc(shift):
  calc = SpecialFlowCalculator(sc.BODIES(), 2)
  if shift:
    field = calc.rayField()
    field.offsets[1] += shift*field.action(field.saddle(0, 1), 0)
  return calc


def path(job):
  """one path: its times, places, the energy's share of change from its start, and the times it changed region"""
  kind, rule, start, direction, speed, shift, until = job
  if kind == 'GR':
    S = PostNewtonian(sc.BODIES())
    calc = MetricCalculator(S)
  else:
    S = FlowSpacetime(shiftedCalc(shift), transverse=False if kind == 'flat' else 'flow')
    calc = sc.RULES[rule](S)
  p = Particle()
  p.pos = np.array(start, dtype=float)
  n = np.array(direction, dtype=float)/np.linalg.norm(direction)
  if speed is None:
    calc.initLight(p, n)
    dt = sc.DT_LIGHT
  else:
    v = speed*n
    if kind != 'GR':
      u = S.flow(p.pos, 0.0, S.region(p.pos, 0.0))
      v = v/(1 - (u @ v)/C**2)
    calc.initPV(p, v)
    dt = sc.DT_LIGHT*C/speed
  E0 = calc.conserved(p)['E'] if until else None
  rows, crossings, before, started = [(p.t, p.pos.copy(), 0.0)], [], calc.sideOf(p), time.time()
  while time.time() - started < LIMIT and len(rows) < 400000:
    if until:
      if p.t >= until:
        break
      calc.move(p, calc.stepSize(p, 0.002, 5.0))
    else:
      if np.linalg.norm(p.pos) > 1.2*HALF:
        break
      calc.move(p, dt)
    rows.append((p.t, p.pos.copy(), (calc.conserved(p)['E'] - E0)/abs(E0) if until else 0.0))
    if getattr(p, 'region', None) is not None and p.region != before:
      crossings.append(p.t)
      before = p.region
  return job, (rows, crossings, time.time() - started >= LIMIT)


def thin(rows, most=3000):
  step = max(1, len(rows)//most)
  return rows[::step] + ([rows[-1]] if (len(rows) - 1) % step else [])


def writeCsv(folder, name, columns, rows, note, bodies=sc.BODIES):
  """a csv and its log: the bodies (for the viewer to draw), then note"""
  csvPath = os.path.join(folder, name + '.csv')
  with open(csvPath, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(columns)
    out.writerows(rows)
  bodies = bodies() if bodies else []
  with open(csvPath[:-4] + '.log', 'w') as f:
    f.write('bodies: %d\n' % len(bodies))
    for i, b in enumerate(bodies):
      f.write('body %d: mass %.6e kg (%.6g MS)  x %.6e m  y %.6e m  %s\n' % (i + 1, b.mass, b.mass/MS, b.x, b.y,
              'black' if b.black else 'white'))
    f.write(note + '\n')
  return csvPath


def xy(rows):
  return [(t, pos[0], pos[1]) for t, pos, _ in thin(rows)]


LIGHT = [('light across the middle, 30,000 km off the line', (-HALF, 3e7), (1, 0), None, BLUE),
         ('light at 45 degrees to the seam', (-HALF/math.sqrt(2), -HALF/math.sqrt(2) + 5e7), (1, 1), None, ORANGE),
         ('light crossing near a body', (-HALF, 2e7), (1, 0.08), None, GREEN),
         ('light across, 300,000 km off the line', (-HALF, 3e8), (1, 0), None, PURPLE)]
PARTICLES = [('a particle at 3,000 km per second', (-2e8, 5e7), (1, 0), 3e6, BLUE),
             ('a particle at 10,000 km per second, near a body', (-3e8, 2e7), (1, 0), 1e7, GREEN)]
ORBIT = ('an orbit round both bodies', (0.0, 1.5e8), (1, 0), 1.4e6, 2e4)
SHIFTS = [(-0.3, BLUE), (0.0, GREY), (0.3, ORANGE)]
PLACED = [('30,000 km off the line', (-HALF, 3e7), (1, 0)), ('at 45 degrees', (-HALF/math.sqrt(2), -HALF/math.sqrt(2) + 5e7), (1, 1))]


def seamLine(calc, n=200):
  """the seam, points where the region changes along lines across the pair (y from -3D to 3D)"""
  pts = []
  for y in np.linspace(-0.8*HALF, 0.8*HALF, n):
    lo, hi = -D/2*0.999, D/2*0.999
    if calc.region(np.array([lo, y])) == calc.region(np.array([hi, y])):
      continue
    for _ in range(50):
      mid = (lo + hi)/2
      if calc.region(np.array([mid, y])) == calc.region(np.array([lo, y])):
        lo = mid
      else:
        hi = mid
    pts.append(((lo + hi)/2, y))
  return pts


def parabolas(GM, qs, reach):
  """zero-energy paths round one body at the origin arriving from far away at -x, moving towards +x: the confocal
  parabolas y^2 = 4q(q - x), traced from x = -reach in on one arm, coming round the body to where they cross the line
  behind it; each with its time, from |v| = sqrt(2GM/r)"""
  out = []
  for q in qs:
    for sign in (1, -1):              #arriving above the axis, or below it
      xs = np.linspace(-reach, q, 1500)                      #in, to where it crosses the line behind the body
      ys = sign*np.sqrt(np.maximum(0, 4*q*(q - xs)))
      ts = [0.0]
      for k in range(1, len(xs)):
        ds = math.hypot(xs[k] - xs[k - 1], ys[k] - ys[k - 1])
        r = math.hypot((xs[k] + xs[k - 1])/2, (ys[k] + ys[k - 1])/2)
        ts.append(ts[-1] + ds/math.sqrt(2*GM/r))
      out.append((q, sign, list(zip(ts, xs, ys))))
  return out


def levelSet(GM, V, R, reach, n=241):
  """the boundary where the body's carried slicing and GR's time agree, V d_y - 2 sqrt(2 GM |d|) = -2 sqrt(2 GM R)
  (the body moving along +y): an open curve below the body, one point for each d_x, as points relative to it"""
  pts = []
  for x in np.linspace(-reach, reach, n):
    f = lambda y: V*y - 2*math.sqrt(2*GM*math.hypot(x, y)) + 2*math.sqrt(2*GM*R)
    lo, hi = -50*reach, 50*reach                   #f < 0 far below, > 0 far above
    for _ in range(100):
      mid = (lo + hi)/2
      if f(mid) > 0:
        hi = mid
      else:
        lo = mid
    pts.append((x, (lo + hi)/2))
  return pts


def main():
  from two_body_escapes import writeViewerFiles
  folder = os.path.join(LOG_DIR, 'seamPlayers', 'seamPlayers_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  jobs = []
  for label, start, d, speed, _ in LIGHT:
    jobs += [('GR', 'rule', start, d, speed, 0.0, None), ('curved', 'rule', start, d, speed, 0.0, None)]
  for label, start, d, speed, _ in PARTICLES:
    jobs += [('GR', 'rule', start, d, speed, 0.0, None), ('curved', 'rule', start, d, speed, 0.0, None),
             ('curved', 'keep p', start, d, speed, 0.0, None)]
  _, oStart, oDir, oSpeed, oUntil = ORBIT
  jobs += [('GR', 'rule', oStart, oDir, oSpeed, 0.0, oUntil), ('curved', 'rule', oStart, oDir, oSpeed, 0.0, oUntil)]
  for shift, _ in SHIFTS:
    for _, start, d in PLACED:
      jobs.append(('curved', 'rule', start, d, None, shift, None))
  for _, start, d in PLACED:
    jobs.append(('GR', 'rule', start, d, None, 0.0, None))
  passing = HALF/C*sm.V
  moving = [(s, passing + 3e7) for s in ('GR', 'level set', 'circle')]
  cache = os.environ.get('SEAM_PLAYERS_CACHE')     #a file to keep the paths in, to redo only the writing
  if cache and os.path.exists(cache):
    with open(cache, 'rb') as f:
      out = pickle.load(f)
  else:
    with Pool(8) as pool:
      waiting = [pool.apply_async(path, (j,)) for j in jobs] + [pool.apply_async(sm.light, (j,)) for j in moving]
      out = {}
      for w in waiting:
        job, result = w.get(timeout=3*LIMIT)
        out[job] = result
        print('done', job[:3], flush=True)
    if cache:
      with open(cache, 'wb') as f:
        pickle.dump(out, f)
  summary = []

  #crossing: light and particles, the model with space curved against GR
  made = []
  for label, start, d, speed, colour in LIGHT:
    for kind, style, who in (('curved', 'solid', 'the model'), ('GR', 'dashed', 'general relativity')):
      rows, crossings, hung = out[(kind, 'rule', start, d, speed, 0.0, None)]
      made.append((writeCsv(folder, '%s (%s)' % (label, who), ['t', 'pos_x', 'pos_y'], xy(rows),
                            '%s: %s%s; crosses the seam %d times' % (label, who, ', space curved' if kind == 'curved' else '',
                                                                    len(crossings))), colour, style))
      summary.append('crossing: %s, %s: %d crossings%s' % (label, who, len(crossings), ' (stopped)' if hung else ''))
  calc = SpecialFlowCalculator(sc.BODIES(), 2)
  writeViewerFiles(folder, 'crossing', made, preferences={'showFlow': True, 'showSeam': True, 'unit': 4, 'replaySpeed': '1'},
                   frames=calc, background=('the potential flow round two bodies', FLOW_DESCRIPTION))

  #without: the particles with the rule and without it
  made = []
  for label, start, d, speed, colour in PARTICLES:
    for kind, rule, style, who, c in (('GR', 'rule', 'dashed', 'general relativity', GREY),
                                      ('curved', 'rule', 'solid', 'the crossing rule', colour),
                                      ('curved', 'keep p', 'solid', 'no rule, the momentum kept', PINK if colour == BLUE else AMBER)):
      rows, crossings, hung = out[(kind, rule, start, d, speed, 0.0, None)]
      made.append((writeCsv(folder, '%s (%s)' % (label, who), ['t', 'pos_x', 'pos_y'], xy(rows),
                            '%s: %s' % (label, who)), c, style))
  writeViewerFiles(folder, 'without', made, preferences={'showFlow': True, 'showSeam': True, 'unit': 4, 'replaySpeed': '1'},
                   frames=SpecialFlowCalculator(sc.BODIES(), 2), background=('the potential flow round two bodies', FLOW_DESCRIPTION))

  #orbit: round both bodies, and its energy
  made, energy = [], []
  for kind, style, who, colour in (('curved', 'solid', 'the model', BLUE), ('GR', 'dashed', 'general relativity', GREY)):
    rows, crossings, hung = out[(kind, 'rule', oStart, oDir, oSpeed, 0.0, oUntil)]
    made.append((writeCsv(folder, 'orbit (%s)' % who, ['t', 'pos_x', 'pos_y'], xy(rows),
                          'an orbit round both bodies: %s; crosses the seam %d times' % (who, len(crossings))), colour, style))
    if kind == 'curved':
      e = writeCsv(folder, 'orbit energy', ['time (s)', 'energy change (parts in 10^6)'],
                   [(t, 1e6*de) for t, _, de in thin(rows)],
                   'the orbit\'s energy H, its change from the start, over the run; the seam is crossed at t = %s s'
                   % ', '.join('%.0f' % c for c in crossings), bodies=None)
      energy.append((e, colour, 'solid'))
      summary.append('orbit: %d crossings in %.0f s; the energy changed by at most %.2e of itself%s'
                     % (len(crossings), rows[-1][0], max(abs(r[2]) for r in rows), ' (stopped)' if hung else ''))
  writeViewerFiles(folder, 'orbit', made, preferences={'showFlow': True, 'showSeam': True, 'unit': 4, 'replaySpeed': '10'},
                   frames=SpecialFlowCalculator(sc.BODIES(), 2), background=('the potential flow round two bodies', FLOW_DESCRIPTION))
  styles = lambda colour, style='solid': {'time (s) / energy change (parts in 10^6)': [colour, style, colour]}
  writeViewerFiles(folder, 'orbitEnergy', energy, selection=(('time (s)', 'energy change (parts in 10^6)'),), styles=styles,
                   preferences={'equalAspect': False, 'showBodies': False, 'showGrid': True, 'replaySpeed': '10'})

  #placement: the seam moved, and light crossing each
  made = []
  for shift, colour in SHIFTS:
    c = shiftedCalc(shift)
    #the engine's own seam, for equal bodies, is the plane half way between them (its region test is noisy there to
    #the rounding of S, the two being equal all along it)
    line_ = seamLine(c) if shift else [(0.0, y) for y in np.linspace(-0.8*HALF, 0.8*HALF, 50)]
    made.append((writeCsv(folder, 'the seam, moved by %+.1f' % shift, ['pos_x', 'pos_y'], line_,
                          'the seam with the constant between the two bodies\' S changed by %+.1f of S at the saddle' % shift),
                 colour, 'dotted'))
    for label, start, d in PLACED:
      rows, crossings, hung = out[('curved', 'rule', start, d, None, shift, None)]
      made.append((writeCsv(folder, 'light %s, the seam moved by %+.1f' % (label, shift), ['t', 'pos_x', 'pos_y'], xy(rows),
                            'light %s, the seam moved by %+.1f; the model, space curved' % (label, shift)), colour, 'solid'))
  for label, start, d in PLACED:
    rows, _, _ = out[('GR', 'rule', start, d, None, 0.0, None)]
    made.append((writeCsv(folder, 'light %s (general relativity)' % label, ['t', 'pos_x', 'pos_y'], xy(rows),
                          'light %s: general relativity' % label), GREY, 'dashed'))
  writeViewerFiles(folder, 'placement', made, preferences={'showFlow': False, 'showSeam': False, 'unit': 4, 'replaySpeed': '1'})

  #observers: one body, observers arriving from one direction on parabolas
  GM, made = G*MS, []
  qs = [0.03, 0.08, 0.15, 0.25, 0.4, 0.6, 0.85, 1.2]
  one = lambda: [Body(MS, 0.0, 0.0)]
  for q, sign, rows in parabolas(GM, [D*k for k in qs], 3*D):
    made.append((writeCsv(folder, 'arriving %s the axis, %.2f D out at its closest' % ('above' if sign > 0 else 'below', q/D),
                          ['t', 'pos_x', 'pos_y'], [r for r in rows if abs(r[2]) < 3*D][::3],
                          'a zero-energy path arriving from far away at -x, %s the axis: the parabola y^2 = 4q(q - x),'
                          ' q = %.3e m' % ('above' if sign > 0 else 'below', q), bodies=one), BLUE if sign > 0 else ORANGE, 'solid'))
  made.append((writeCsv(folder, 'their seam', ['pos_x', 'pos_y'], [(x, 0.0) for x in np.linspace(0, 3*D, 50)],
                        'the seam of these observers: the half-line behind the body', bodies=one), PINK, 'dashed'))
  writeViewerFiles(folder, 'observers', made, preferences={'showFlow': False, 'showSeam': False, 'unit': 4,
                                                          'showPathLegend': False, 'replaySpeed': '10'})

  #moving: a body at 0.1 c, a boundary where the times agree and one where they don't
  made = []
  GMb = G*MS
  for shape, colour, style, who in (('GR', GREY, 'dashed', 'general relativity'), ('level set', GREEN, 'solid', 'a boundary where the times agree'),
                                    ('circle', PINK, 'solid', 'a circle, where they don\'t')):
    pts, dirs, turns, hung = out[(shape, passing + 3e7)]
    rows = [(k*2e-3, x, y) for k, (x, y) in enumerate(pts)]
    made.append((writeCsv(folder, 'light, %s' % who, ['t', 'pos_x', 'pos_y'], thin(rows),
                          'light passing a body moving at 0.1 c: %s' % who, bodies=None), colour, style))
    summary.append('moving: %s: %d crossings, turns %s' % (shape, len(turns), ', '.join('%.1e' % t for t in turns)))
  T = 2*HALF/C
  made.append((writeCsv(folder, 'the body, moving at 0.1 c', ['t', 'pos_x', 'pos_y'],
                        [(t, 0.0, sm.V*t) for t in np.linspace(0, T, 200)], 'the body\'s path: one solar mass moving at 0.1 c',
                        bodies=None), '#1a1a1a', 'solid'))
  tc = HALF/C                         #about when the light reaches the boundaries
  made.append((writeCsv(folder, 'the boundary where the times agree (as the light passes)', ['pos_x', 'pos_y'],
                        [(x, y + sm.V*tc) for x, y in levelSet(GMb, sm.V, sm.R, HALF)], 'the level set, drawn where it is as the light passes',
                        bodies=None), GREEN, 'dotted'))
  made.append((writeCsv(folder, 'the circle (as the light passes)', ['pos_x', 'pos_y'],
                        [(sm.R*math.cos(a), sm.R*math.sin(a) + sm.V*tc) for a in np.linspace(0, 2*math.pi, 121)],
                        'the circle, drawn where it is as the light passes', bodies=None), PINK, 'dotted'))
  writeViewerFiles(folder, 'moving', made, preferences={'showFlow': False, 'showSeam': False, 'showBodies': False, 'unit': 4,
                                                       'replaySpeed': '1'})
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(summary) + '\n')
  print('\n'.join(summary))
  print('written to', folder)


if __name__ == '__main__':
  main()
