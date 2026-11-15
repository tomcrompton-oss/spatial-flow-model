"""
how the bodies' flows combine - the first multi-body question: Part 3 of the write-up adds them as vectors (so between
the Earth and the Moon the flows cancel, and a clock there would run at full speed); the simulation takes the square
root of the sum of their squares, |u|^2 = sum 2GM/d, pointing down the eikonal flow (engine/two_centre.py). each is
run in the flow model (engine/flow.py combine 'vectors' and 'squares'), with the bodies at rest:

  surface   g at the Earth's surface with the Sun 1 AU away: a particle let go from rest at eight points round the
            Earth, and at the Moon's distance, its acceleration over 0.01 s against Newton's. space falling at u
            accelerates at (u . grad) u = grad(u^2/2), so the squares give Newton's g exactly; the vectors add
            grad(u_E . u_S), a cross term between the Sun's flow (42 km/s at the Earth) and the Earth's (11 km/s)
  line      Part 3's Earth-Moon line: the flow and the time dilation of a clock at rest along it, for each rule,
            against GR's (the potential, sum GM/d c^2); where the vectors cancel, and where g is 0 (Part 3's P)
  drops     balls let go from rest 100 km above the Earth, at eight points round it, the Sun 1 AU away (to the
            left), for 150 s: with the vectors (solid) they veer sideways; with the squares (dashed) they fall
            straight down, as Newton's do - in the browser viewer, with each rule's flow drawn behind

writes logs/multiBody/multiBodyRules_<datetime>/: a csv and log for each path, a viewer file for the drops
(multiBody_drops.full.json), and summary.log

run: python3 studies/multi_body_rules.py      (then: python3 scripts/publish_run.py logs/multiBody/multiBodyRules_<datetime>)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Calculator, SpecialFlowCalculator, NewtonianCalculator, Particle
from engine.logger import LOG_DIR
from engine.constants import *
from part1_examples import write, follow, COLOURS
from two_body_escapes import writeViewerFiles

MMOON = 7.342e22   #kg
DMOON = 3.844e8    #m, the Earth to the Moon
SUN_EARTH = [Body(MS, -AU, 0.0), Body(ME)]   #the Earth at the origin, the Sun 1 AU to the left
RULES = (('vectors', 'vectors'), ('squares', 'squares (eikonal)'))
ANGLES = range(0, 360, 45)   #degrees round the Earth, from the side facing the Sun


def calculators(bodies):
  return [(title, SpecialFlowCalculator(bodies, 2, combine=rule)) for rule, title in RULES]


def newton(bodies, pos):
  return NewtonianCalculator(bodies).gravity(pos)


def released(calc, pos, duration=0.01, dt=1e-4):
  """a particle let go from rest (v = 0) at pos: its mean acceleration over duration"""
  p = Particle()
  p.pos = np.array(pos, dtype=float)
  calc.initPV(p, np.array([0.0, 0.0]))
  for _ in range(round(duration/dt)):
    calc.move(p, dt)
  return p.v/duration


def surface(folder):
  """g at the Earth's surface and the Moon's distance, the Sun 1 AU away: each rule against Newton"""
  lines = ['surface: a particle let go from rest, its acceleration over 0.01 s against Newton\'s (the Earth at the'
           ' origin, the Sun 1 AU away); angle from the side facing the Sun',
           '  the Sun\'s tide at the Earth\'s surface, for scale: 2 GM_S R_E/AU^3 = %.2e m/s^2' % (2*G*MS*REARTH/AU**3)]
  worst = {}
  for height, label in ((REARTH, 'the surface'), (DMOON, 'the Moon\'s distance')):
    lines.append('  at %s (%.0f km from the centre):' % (label, height/1000))
    lines.append('    %-20s' % 'rule' + ''.join('%11s' % ('%d deg' % a) for a in ANGLES) + '   (|a - g_Newton|, m/s^2)')
    for title, calc in calculators(SUN_EARTH):
      errors = []
      for a in ANGLES:
        pos = height*np.array([-math.cos(math.radians(a)), math.sin(math.radians(a))])
        errors.append(np.linalg.norm(released(calc, pos) - newton(SUN_EARTH, pos)))
      worst[(title, label)] = max(errors)
      lines.append('    %-20s' % title + ''.join('%11.3g' % e for e in errors))
    g = G*ME/height**2
    lines.append('    (the Earth\'s g there: %.4g m/s^2)' % g)
  return lines, worst


def line(folder):
  """Part 3's Earth-Moon line: flow and clock rates by rule, against GR"""
  bodies = [Body(ME), Body(MMOON, DMOON, 0.0)]
  q = math.sqrt(MMOON/ME)
  P = DMOON/(1 + q)                    #where g = 0: GM_E/d^2 = GM_M/(D - d)^2
  zero = DMOON/(1 + MMOON/ME)          #where the vectors cancel: sqrt(GM_E/d) = sqrt(GM_M/(D - d))
  lines = ['line: Part 3\'s Earth-Moon line, a clock at rest on it (the Sun left out, as in Part 3)',
           '  g = 0 (Part 3\'s P) %.0f km from the Earth (%.0f km from the Moon); the vectors cancel %.0f km from the'
           ' Earth (%.0f km from the Moon)' % (P/1000, (DMOON - P)/1000, zero/1000, (DMOON - zero)/1000),
           '  %-14s %13s %13s %13s %13s %13s' % ('from Earth', '|u| vectors', '|u| squares', 'GR dilation',
                                                'vectors', 'squares'),
           '  %-14s %13s %13s %13s %13s %13s' % ('(km)', '(km/s)', '(km/s)', '(U/c^2)', '(1 - rate)', '(1 - rate)')]
  calcs = dict((title, calc) for title, calc in calculators(bodies))
  rows = []
  for d in sorted([REARTH, 2e7, 1e8, 2e8, 3e8, P, zero, DMOON - 1e7, DMOON - 2e6]):
    pos = np.array([d, 0.0])
    U = G*ME/d + G*MMOON/(DMOON - d)
    us = [np.linalg.norm(calcs[t].flow(pos)) for _, t in RULES]
    rates = [1 - math.sqrt(1 - u*u/C**2) for u in us]
    tag = ' (P)' if d == P else ' (cancel)' if d == zero else ''
    lines.append('  %-14s %13.4f %13.4f %13.4e %13.4e %13.4e' % ('%.0f%s' % (d/1000, tag), us[0]/1000, us[1]/1000,
                                                                U/C**2, *rates))
    rows.append((d, U/C**2, *rates))
  return lines, rows, P, zero


def drops(folder):
  """balls let go from rest 100 km up, round the Earth, the Sun 1 AU to the left: each rule, in the viewer"""
  made, lines = [], []
  for (rule, title), colour, style in zip(RULES, (COLOURS[1], COLOURS[0]), ('solid', 'dashed')):
    calc = SpecialFlowCalculator(SUN_EARTH, 2, combine=rule)
    paths = []
    for a in ANGLES:
      p = Particle()
      p.pos = (REARTH + 1e5)*np.array([-math.cos(math.radians(a)), math.sin(math.radians(a))])
      calc.initPV(p, np.array([0.0, 0.0]))
      start = p.pos.copy()
      rows = follow(calc, p, lambda p: p.t >= 150 - 1e-9 or np.linalg.norm(p.pos) <= REARTH, lambda p: 0.5, every=4)
      down = start/np.linalg.norm(start)
      moved = p.pos - start
      sideways = moved - (moved @ down)*down
      lines.append('drops, %s: from %d deg, after %.0f s: %.1f km down, %.1f km sideways'
                   % (title, a, p.t, -(moved @ down)/1000, np.linalg.norm(sideways)/1000))
      name = 'drop_%s_%03d' % (rule, a)
      paths.append(write(folder, name, calc, rows, ['t', 'pos_x', 'pos_y', 'v_x', 'v_y'],
                         ['a ball let go from rest 100 km above the Earth, %d degrees from the side facing the Sun;'
                          ' flows combined as %s' % (a, title), lines[-1]]))
    made += [(path, colour, style) for path in paths]
    writeViewerFiles(folder, 'multiBody_drops_%s' % rule, [(path, colour, style) for path in paths],
                     styles=lambda colour, style='solid': {'pos': [colour, style, colour]}, frames=calc)
  writeViewerFiles(folder, 'multiBody_drops', made, styles=lambda colour, style='solid': {'pos': [colour, style, colour]})
  return lines


def main():
  folder = os.path.join(LOG_DIR, 'multiBody', 'multiBodyRules_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = []
  found, worst = surface(folder)
  lines += found + ['']
  print('\n'.join(found), flush=True)
  found, rows, P, zero = line(folder)
  lines += found + ['']
  print('\n'.join(found), flush=True)
  found = drops(folder)
  lines += found + ['']
  print('\n'.join(found), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  return folder


if __name__ == '__main__':
  main()
