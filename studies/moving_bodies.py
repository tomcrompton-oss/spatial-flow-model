"""
moving bodies - the third multi-body question: a body moving through space, its flow moving with it. either the flow
pattern only moves with it (taken along: the space round it still at rest far off, so the body moves through space)
or the space round it moves with it too (carried: u = V + its own flow, for one body - a Galilean change of frame of
the body at rest, so exact GR). taken along, the Earth's 29.8 km/s across its own 11 km/s inflow puts a cross term
V . u_E into |u - V|^2 in the Earth's frame - a preferred-frame effect. each run in the flow model (engine/flow.py,
Body.velocity, Calculator.carried), in the Earth's frame:

  alone     the Earth alone, moving at 29.8 km/s (along +y): g at eight points round it (a particle let go at rest
            beside it, its acceleration over 0.01 s against Newton's), and clocks at rest on it - a light pulse a
            second from the clock ahead of the Earth to the one at its side, the second's count against the first's
  system    the Sun and the Earth, the Earth moving past the Sun on its orbit (29.8 km/s, at right angles to the
            Sun), the flows added as vectors (the eikonal flows are for bodies at rest); the Earth carries its flow
            near it (Calculator.carry: its velocity through the Sun's space, with its share of g): the same g, and
            clock rates round the equator against GR's
  drops     balls let go at rest beside the moving Earth, from eight places round it: 100 km up for 150 s (the
            numbers), and one Earth radius up until they land (the viewer), drawn in the Earth's frame - the flow
            taken along (solid) - they are swept off; carried (dashed) - they fall straight down. the viewer's
            backgrounds are the space as the Earth sees it, each way, with its surface

writes logs/multiBody/movingBodies_<datetime>/: a csv and log for each motion (a path per ball), a viewer file
(multiBody_moving.full.json), its backgrounds (multiBody_moving.backgrounds.json) and summary.log

run: python3 studies/moving_bodies.py      (then: python3 scripts/publish_run.py logs/multiBody/movingBodies_<datetime>)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Calculator, SpecialFlowCalculator, Particle
from engine.logger import LOG_DIR
from engine.constants import *
from part1_examples import write, COLOURS
from two_body_escapes import writeViewerFiles
from multi_body_rules import ANGLES

V = 29780.0                     #m/s, the Earth's orbital speed
MOTIONS = ((False, 'taken along'), (True, 'carried'))


def earthAlone():
  return [Body(ME, velocity=(0.0, V))]


def sunAndEarth():
  return [Body(MS, -AU, 0.0), Body(ME, velocity=(0.0, V))]


def newton(bodies, pos, t):
  return sum((-b.GM*(pos - b.at(t))/np.linalg.norm(pos - b.at(t))**3 for b in bodies), np.array([0.0, 0.0]))


def released(calc, earth, offset, duration=0.01, dt=1e-4):
  """let go at rest beside the Earth (moving with it), offset from its centre: mean acceleration, and Newton's"""
  p = Particle()
  p.pos = earth.at(0.0) + offset
  calc.initPV(p, earth.velocity.copy())
  for _ in range(round(duration/dt)):
    calc.move(p, dt)
  return (p.v - earth.velocity)/duration, newton(calc.bodies, earth.at(duration/2) + offset, duration/2)


def gravity(bodies, combine, lines, shares=(1,)):
  """g round the moving Earth, each motion (carried, with each share: Calculator.carry) against Newton"""
  earth = bodies[-1]
  lines.append('    %-20s' % 'flow' + ''.join('%11s' % ('%d deg' % a) for a in ANGLES) + '   (|a - g_Newton|, m/s^2)')
  worst = {}
  for carried, title, share in [(False, 'taken along', 1)] + [(True, 'carried' if len(shares) == 1 else
                                                               'carried, by g^%d' % n, n) for n in shares]:
    calc = SpecialFlowCalculator(bodies, 2, combine=combine, carried=carried)
    calc.share = share
    errors = []
    for a in ANGLES:
      offset = REARTH*np.array([-math.cos(math.radians(a)), math.sin(math.radians(a))])
      got, want = released(calc, earth, offset)
      errors.append(np.linalg.norm(got - want))
    worst[(carried, share)] = max(errors)
    lines.append('    %-20s' % title + ''.join('%11.3g' % e for e in errors))
  return worst


def rate(calc, pos, v, t):
  w = v - calc.flow(pos, None, t)
  return math.sqrt(1 - (w @ w)/C**2)


def pulse(calc, start, end, t0):
  """light from the moving point start(t) at time t0, aimed (by trial) to meet the moving point end(t): arrival time"""
  a, b = start(t0), end(t0)
  aim = math.atan2(*(b - a)[::-1])
  def shoot(angle):
    p = Particle()
    p.pos, p.t = a.copy(), t0
    calc.initPW(p, C*np.array([math.cos(angle), math.sin(angle)]))
    best = (float('inf'), None, None)
    while True:
      calc.move(p, min(1e-4, 0.02*np.linalg.norm(p.pos - end(p.t))/C + 1e-7))
      gap = np.linalg.norm(p.pos - end(p.t))
      if gap < best[0]:
        best = (gap, p.t, p.pos - end(p.t))
      elif gap > best[0] + 1e5:
        break
    along = b - a
    return along[0]*best[2][1] - along[1]*best[2][0], best[1]
  lo, hi = aim - 1e-3, aim + 1e-3
  slo, _ = shoot(lo)
  for _ in range(40):
    mid = (lo + hi)/2
    s, t = shoot(mid)
    if (s > 0) == (slo > 0):
      lo, slo = mid, s
    else:
      hi = mid
  return t


def signals(bodies, combine, lines):
  """a pulse a second from the clock ahead of the moving Earth to the one at its side: the count ratio less 1"""
  earth = bodies[-1]
  ahead = lambda t: earth.at(t) + REARTH*earth.velocity/np.linalg.norm(earth.velocity)
  side = lambda t: earth.at(t) + REARTH*np.array([1.0, 0.0])
  found = {}
  for carried, title in MOTIONS:
    calc = SpecialFlowCalculator(bodies, 2, combine=combine, carried=carried)
    t1, t2 = pulse(calc, ahead, side, 0.0), pulse(calc, ahead, side, 1.0)
    count = (t2 - t1)*rate(calc, side(t1), earth.velocity, t1)/rate(calc, ahead(0.0), earth.velocity, 0.0) - 1
    found[carried] = count
    lines.append('    %-14s %+.4e   (the pulses arrived %.9f s apart)' % (title, count, t2 - t1))
  return found


def clockRates(bodies, lines, share=1):
  """clocks at rest round the moving Earth's equator, each motion: their rates' swing round it, against GR's"""
  earth = bodies[-1]
  found = {}
  for carried, title in MOTIONS:
    calc = Calculator(bodies, combine='vectors', carried=carried)
    calc.share = share
    diffs = []
    for a in range(0, 360, 15):
      offset = REARTH*np.array([-math.cos(math.radians(a)), math.sin(math.radians(a))])
      model = rate(calc, earth.at(0.0) + offset, earth.velocity, 0.0)
      #GR, in the Earth's freely falling frame: its own potential and the Sun's tide (less the Sun's pull at the centre)
      d = earth.at(0.0) + offset - bodies[0].pos
      D = earth.at(0.0) - bodies[0].pos
      tide = G*MS/np.linalg.norm(d) - G*MS/np.linalg.norm(D) + G*MS*(offset @ D)/np.linalg.norm(D)**3
      gr = 1 - (G*ME/REARTH + tide)/C**2
      diffs.append(model - gr)
    diffs = np.array(diffs) - np.mean(diffs)
    found[carried] = (diffs.max() - diffs.min())/2
    lines.append('    %-14s %.3e' % (title, found[carried]))
  return found


HIGH = REARTH                   #the player's balls are let go this far up (m), so their paths show at the Earth's scale


class EarthFrame:
  """a calculator's flow seen from the moving Earth: u at the place that far from the Earth, less its velocity"""

  def __init__(self, calc, earth):
    self.calc, self.earth = calc, earth

  def flow(self, q, region=None, t=0.0):
    if np.linalg.norm(q) < REARTH:
      raise ValueError('inside the Earth')
    return self.calc.flow(q + self.earth.at(t), None, t) - self.earth.velocity


def drop(calc, earth, out, height, until):
  """a ball let go at rest beside the moving Earth, height up on the side out: its rows (t, place and velocity in the
  Earth's frame) every 10 s and at the end, until it lands, gets 6 Earth radii away, or the time until"""
  p = Particle()
  p.pos = earth.at(0.0) + (REARTH + height)*out
  calc.initPV(p, earth.velocity.copy())
  rows, dt = [(0.0, *(p.pos - earth.at(0.0)), 0.0, 0.0)], 0.5
  while p.t < until - 1e-9:
    calc.move(p, dt)
    rel = p.pos - earth.at(p.t)
    done = np.linalg.norm(rel) <= REARTH or np.linalg.norm(rel) > 6*REARTH
    if done or round(p.t/dt) % 20 == 0:
      rows.append((p.t, *rel, *(p.v - earth.velocity)))
    if done:
      break
  return rows


def drops(folder):
  """balls let go beside the moving Earth, each motion: 100 km up for the numbers, and one Earth radius up for the
  viewer, drawn in the Earth's frame over a background of the space as the Earth sees it"""
  from engine.backgrounds import Backgrounds, polar, LOG_LINE
  made, lines = [], []
  bg = Backgrounds()
  for (carried, title), colour, style in zip(MOTIONS, (COLOURS[1], COLOURS[0]), ('solid', 'dashed')):
    bodies = earthAlone()
    earth = bodies[0]
    calc = SpecialFlowCalculator(bodies, 2, carried=carried)
    rows = []
    for a in ANGLES:
      out = np.array([-math.cos(math.radians(a)), math.sin(math.radians(a))])
      low = drop(calc, earth, out, 1e5, 150.0)
      moved = np.array(low[-1][1:3]) - (REARTH + 1e5)*out
      lines.append('drops, %s: from %d deg (90 = ahead), 100 km up, after %.0f s: %.1f km down, %.1f km sideways'
                   % (title, a, low[-1][0], -(moved @ out)/1000, np.linalg.norm(moved - (moved @ out)*out)/1000))
      high = drop(calc, earth, out, HIGH, 3000.0)
      moved = np.array(high[-1][1:3]) - (REARTH + HIGH)*out
      lines.append('drops, %s: from %d deg, %.0f km up, after %.0f s: %.0f km down, %.0f km sideways, %s'
                   % (title, a, HIGH/1000, high[-1][0], -(moved @ out)/1000,
                      np.linalg.norm(moved - (moved @ out)*out)/1000,
                      'landed' if np.linalg.norm(high[-1][1:3]) <= REARTH else 'still falling'))
      rows += high + [None]
    name = 'the space carried' if carried else 'the pattern taken along'
    path = write(folder, name, calc, [], ['t', 'pos_x', 'pos_y', 'v_x', 'v_y'],
                 ['balls let go at rest beside the Earth (moving at %.0f m/s along +y), %.0f km up, from eight places'
                  ' round it; its flow %s; in the Earth\'s frame, a path per ball' % (V, HIGH/1000, title)])
    with open(path, 'w') as f:
      f.write('t,pos_x,pos_y,v_x,v_y\n')
      for row in rows[:-1]:
        f.write(',,,,\n' if row is None else ','.join('%.12g' % v for v in row) + '\n')
    with open(path[:-4] + '.log', 'a') as f:
      f.write('%s multiBody_moving.backgrounds.json\n' % LOG_LINE)
    made.append((path, colour, style))
    #the space as the Earth sees it, with the Earth's surface
    b = bg.add('Seen from the Earth: %s' % name,
               ('The space round the Earth, as seen from the Earth, which moves up the page at 29.8 km/s. '
                + ('Carried: the space moves with the Earth, so from the Earth it falls straight in, as round an Earth '
                   'at rest. A ball let go falls straight down.' if carried else
                   'Taken along: the flow\'s pattern moves with the Earth but the space does not, so from the Earth the '
                   'space streams past downwards at 29.8 km/s, bent in towards it. A ball let go beside the Earth is '
                   'moving through that space at 29.8 km/s, and is thrown off its fall.')))
    b.field('the flow of space, seen from the Earth', EarthFrame(calc, earth), polar(REARTH, 7*REARTH, 60, 48),
            steady=True)
    b.lines('the Earth\'s surface', lambda t: [np.array([[REARTH*math.cos(x), REARTH*math.sin(x)]
                                                         for x in np.linspace(0, 2*math.pi, 97)])])
  bg.items.reverse()   #carried first: the model
  bg.write(os.path.join(folder, 'multiBody_moving.backgrounds.json'))
  writeViewerFiles(folder, 'multiBody_moving', made, styles=lambda colour, style='solid': {'pos': [colour, style, colour]},
                   preferences={'showPathLegend': True, 'replaySpeed': '10', 'unit': 2, 'showFlow': True,
                                'showSeam': True})
  return lines


def main():
  folder = os.path.join(LOG_DIR, 'multiBody', 'movingBodies_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = ['alone: the Earth by itself, moving at %.0f m/s (along +y)' % V,
           '  g round it: a particle let go at rest beside it, its acceleration over 0.01 s against Newton\'s; angle'
           ' from the side facing -x (90 deg is ahead)']
  gravity(earthAlone(), 'squares', lines)
  lines.append('  clocks at rest on it: a pulse a second from the clock ahead to the one at its side, the count ratio'
               ' less 1 (GR: 0, as at rest)')
  signals(earthAlone(), 'squares', lines)
  lines.append('  the cross term, 2 V u_E/c^2 between the clocks ahead and behind: %.3e'
               % (2*V*math.sqrt(2*G*ME/REARTH)/C**2))
  print('\n'.join(lines), flush=True)
  lines += ['', 'system: the Sun, and the Earth 1 AU away moving at %.0f m/s at right angles to it; flows added as'
            ' vectors' % V,
            '  g round the Earth, against Newton\'s (the Sun\'s tide at the surface is %.2e m/s^2)'
            % (2*G*MS*REARTH/AU**3)]
  gravity(sunAndEarth(), 'vectors', lines, shares=(1, 2, 4, 8))
  lines.append('  (the Earth\'s share of g at its surface is 1 - %.1e; by g^n, 1 - that to the nth. what is left as the'
               ' share sharpens is the vectors\' own cross term, u_E . (u_S(x) - u_S(Earth)), about u_E u_S/AU ='
               ' %.1e m/s^2)' % (G*MS/AU**2/(G*ME/REARTH**2), math.sqrt(2*G*ME/REARTH)*math.sqrt(2*G*MS/AU)/AU))
  lines.append('  clocks at rest round the equator: the swing in their rates against GR\'s (the Earth\'s potential'
               ' and the Sun\'s tide)')
  clockRates(sunAndEarth(), lines, share=8)
  lines.append('')
  print('\n'.join(lines[lines.index('') + 1:]), flush=True)
  found = drops(folder)
  lines += found
  print('\n'.join(found), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  return folder


if __name__ == '__main__':
  main()
