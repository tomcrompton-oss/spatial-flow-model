"""
clocks with more than one body - the second multi-body question: with the Sun's flow (42 km/s at the Earth) and the
Earth's (11 km/s at its surface) added as vectors, |u|^2 has a cross term, 2 u_E . u_S, which changes round the Earth;
a clock at rest ticks at sqrt(1 - |w|^2/c^2) with w = -u, so it would run fast or slow by u_E . u_S/c^2 - about 5
parts in 10^9 - with the time of day. with the flows combined by their squares, |u|^2 = 2 sum GM/d, there is no cross
term: a clock at rest ticks at GR's first-order rate everywhere. the Sun at rest 1 AU from the Earth (the Earth not
going round it), all in the plane:

  rates     a clock on the Earth's equator, turning with it (465 m/s), and a GPS clock (26,560 km, half a sidereal day
            round), over a day: the rate each rule gives, sqrt(1 - |v - u|^2/c^2), against GR's 1 - (U + v^2/2)/c^2.
            part of the model's rate, u . v/c^2, is only the model's clocks (Gullstrand-Painleve time) being set
            differently from GR's static time from place to place: with no curl, its integral round any loop is 0, so
            it is taken out (the rates below are in GR's static time). what is left, after a steady rate (which a
            clock's calibration takes up), against GR: its swing in rate, and in the time it keeps (and that times c,
            in range for GPS)
  signals   that the difference is there to be seen: two clocks at rest on the equator, one where it is noon and one
            at dusk, 90 degrees round, the first sending the second light pulses a second apart (light run in the
            model, round the Earth's flow); the second's count of the interval, against the first's - for each rule,
            and for GR. (the flow is steady, so the pulses arrive as far apart as they left, in the model's time:
            the count is the ratio of the two clocks' rates)

writes logs/multiBody/multiBodyClocks_<datetime>/: a csv of each clock's rate against GR over the day, a viewer file
(multiBody_clocks.full.json, rate against time), and summary.log

run: python3 studies/multi_body_clocks.py      (then: python3 scripts/publish_run.py logs/multiBody/multiBodyClocks_<datetime>)
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
from multi_body_rules import SUN_EARTH, RULES

SIDEREAL_DAY = 86164.1
SPIN = 2*math.pi/SIDEREAL_DAY
GPS_RADIUS = 2.656e7
GPS_SPEED = math.sqrt(G*ME/GPS_RADIUS)
SAMPLES = 2000   #over the day


def ground(t):
  """the equator clock at time t: position and velocity (noon - facing the Sun - at t = 0)"""
  a = math.pi + SPIN*t
  return REARTH*np.array([math.cos(a), math.sin(a)]), REARTH*SPIN*np.array([-math.sin(a), math.cos(a)])


def gps(t):
  """the GPS clock at time t, starting between the Earth and the Sun"""
  a = math.pi + GPS_SPEED/GPS_RADIUS*t
  return GPS_RADIUS*np.array([math.cos(a), math.sin(a)]), GPS_SPEED*np.array([-math.sin(a), math.cos(a)])


def potential(pos):
  return sum(b.GM/np.linalg.norm(pos - b.pos) for b in SUN_EARTH)


def residuals(calc, clock):
  """
  over a day: the model's rate (in GR's static time) less GR's, at each sample, and the time kept less GR's, each
  after the steady part is taken out - the swing in the rate and in the time
  """
  ts = np.linspace(0.0, 86400.0, SAMPLES + 1)
  rate, gauge = [], []
  for t in ts:
    x, v = clock(t)
    u = calc.flow(x)
    w = v - u
    rate.append(math.sqrt(1 - (w @ w)/C**2))
    gauge.append(u @ v/C**2)
  #in GR's static time T: dT/dt = 1 + u . v/c^2 (to first order: for one body dT = dt + u dr/(c^2 - u^2), u < 0
  #inwards); the rate per unit T is the rate per t over that
  model = np.array(rate)/(1 + np.array(gauge))
  gr = np.array([1 - (potential(clock(t)[0]) + (clock(t)[1] @ clock(t)[1])/2)/C**2 for t in ts])
  diff = model - gr
  diff = diff - diff.mean()
  kept = np.concatenate([[0.0], np.cumsum((diff[1:] + diff[:-1])/2*np.diff(ts))])
  kept = kept - np.polyval(np.polyfit(ts, kept, 1), ts)   #a steady rate is calibration
  return ts, diff, kept


def rates(folder):
  lines = ['rates: over a day, the model\'s clock rate (in GR\'s static time) less GR\'s, the steady part taken out -'
           ' its swing, and the swing in the time the clock keeps; the Sun at rest 1 AU away',
           '  %-22s %-20s %16s %16s %14s' % ('clock', 'rule', 'rate (+/-)', 'time (+/- ns)', 'range (+/- m)')]
  made, found = [], {}
  for clockName, clock, colours in (('equator', ground, COLOURS[:2]), ('GPS', gps, COLOURS[2:4])):
    for (rule, title), colour in zip(RULES, colours):
      calc = Calculator(SUN_EARTH, combine=rule)
      ts, diff, kept = residuals(calc, clock)
      swing, timeSwing = (diff.max() - diff.min())/2, (kept.max() - kept.min())/2
      found[(clockName, rule)] = (swing, timeSwing)
      lines.append('  %-22s %-20s %16.3e %16.3f %14.3f' % (clockName, title, swing, timeSwing*1e9, timeSwing*C))
      rows = [(t, d*1e9, k*1e9) for t, d, k in zip(ts, diff, kept)]
      made.append((write(folder, 'clock_%s_%s' % (clockName, rule), calc, rows, ['t', 'rate_ppb', 'time_ns'],
                         ['the %s clock\'s rate (parts in 10^9) and time (ns) against GR over a day, flows combined as'
                          ' %s; the steady part taken out' % (clockName, title), lines[-1]]), colour))
  writeViewerFiles(folder, 'multiBody_clocks', made, selection=(('t', 'rate_ppb'),),
                   styles=lambda colour, style='solid': {'t / rate_ppb': [colour, style, colour]},
                   preferences={'mode': 'xy', 'equalAspect': False, 'showBodies': False, 'showFlow': False})
  lines.append('  the cross term u_E . u_S/c^2 at the surface: %.3e; at GPS: %.3e'
               % (math.sqrt(2*G*ME/REARTH)*math.sqrt(2*G*MS/AU)/C**2, math.sqrt(2*G*ME/GPS_RADIUS)*math.sqrt(2*G*MS/AU)/C**2))
  return lines, found


def pulse(calc, start, end, t0):
  """light from start at time t0, aimed (by trial) to reach end: its arrival time there"""
  aim = math.atan2(*(end - start)[::-1])
  def shoot(angle):
    p = Particle()
    p.pos, p.t = start.copy(), t0
    calc.initPW(p, C*np.array([math.cos(angle), math.sin(angle)]))
    best = (float('inf'), None)
    while True:
      dt = min(1e-4, 0.02*np.linalg.norm(p.pos - end)/C + 1e-7)
      calc.move(p, dt)
      gap = np.linalg.norm(p.pos - end)
      if gap < best[0]:
        best = (gap, p.t, p.pos.copy())
      elif gap > best[0] + 1e5:
        break
    gap, t, pos = best
    along, off = end - start, pos - end
    return along[0]*off[1] - along[1]*off[0], t
  lo, hi = aim - 1e-4, aim + 1e-4
  slo, _ = shoot(lo)
  for _ in range(36):
    mid = (lo + hi)/2
    s, t = shoot(mid)
    if (s > 0) == (slo > 0):
      lo, slo = mid, s
    else:
      hi = mid
  return t


def signals(folder):
  noon, dusk = ground(0.0)[0], ground(SIDEREAL_DAY/4)[0]
  lines = ['signals: light pulses 1 s apart from a clock at rest where it is noon to one at dusk (90 degrees round the'
           ' equator), the Earth not turning: the second clock\'s count of the interval over the first\'s, less 1']
  gr = (1 - potential(dusk)/C**2)/(1 - potential(noon)/C**2) - 1
  found = {}
  for rule, title in RULES:
    calc = SpecialFlowCalculator(SUN_EARTH, 2, combine=rule)
    rate = lambda x: math.sqrt(1 - (calc.flow(x) @ calc.flow(x))/C**2)
    t1, t2 = pulse(calc, noon, dusk, 0.0), pulse(calc, noon, dusk, 1.0)
    ratio = (t2 - t1)*rate(dusk)/(1.0*rate(noon)) - 1
    found[rule] = ratio
    lines.append('  %-20s %.4e   (against GR: %+.3e; the pulses arrived %.6f s apart)' % (title, ratio, ratio - gr, t2 - t1))
  lines.append('  %-20s %.4e   (the clocks\' potentials, sum GM/d c^2)' % ('GR', gr))
  return lines, found


def main():
  folder = os.path.join(LOG_DIR, 'multiBody', 'multiBodyClocks_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = []
  for section in (rates, signals):
    found = section(folder)[0]
    lines += found + ['']
    print('\n'.join(found), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  return folder


if __name__ == '__main__':
  main()
