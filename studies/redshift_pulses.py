"""
the Gravitational Redshift page (docs/part1/tests/redshift.md): light pulses sent out from the surface of a body by a
clock held still there, and received by a clock held still further out, in the flow model

a clock held still at r is moving out through space falling in at u = sqrt(2GM/r), so (special relativity) it runs at
sqrt(1 - u^2/c^2) = sqrt(1 - rs/r) of the flow's time. the emitter sends a pulse every PULSES of its own time; the
flow is steady, so each pulse takes the same time to climb out (the simulation shows it), and the receiver, whose clock
runs faster, counts more of its own time between arrivals. the ratio of the two clocks' intervals is the redshift,
against general relativity's sqrt((1 - rs/r_emitter)/(1 - rs/r_receiver))

  neutron star  1.4 solar masses within 12 km (rs = 4.1 km, a third of its radius), received at 20 times its radius:
                for the viewer, distance against time
  white dwarf   1 solar mass within 6,000 km, received at 1 AU
  the Sun       its surface, received at 1 AU

the light is the flow model's (SpecialFlowCalculator, second order); the two clocks are held still (w = -u), their
proper time running at sqrt(1 - w^2/c^2)

writes logs/redshift/redshift_<datetime>/: the neutron star's csvs and redshift_star.full.json, and summary.log

run: python3 studies/redshift_pulses.py      (then: python3 scripts/publish_run.py logs/redshift/redshift_<datetime>)
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
from engine.exact import schwarzschildRadius, rayTime
from part1_examples import write
from two_body_escapes import writeViewerFiles

PULSES = 8                #pulses each body's emitter sends
STEP = 1e-3               #each light step moves about this fraction of the distance to the body
EVERY = 10                #light steps between csv rows
COLUMNS = ['t', 'pt', 'pos_x', 'pos_y', 'v_x', 'v_y']
X_T = lambda colour, style='solid': {'pos_x / t': [colour, style, colour]}
COLOURS = {'emitter': '#2a78d6', 'receiver': '#52514e', 'pulse': '#eb6834'}
BODIES = (   #name, mass (kg), emitter's distance (m), receiver's (m), emitter's interval (its own seconds)
  ('neutron star', 1.4*MS, 12e3, 240e3, 1e-4),
  ('white dwarf', MS, 6e6, AU, 1.0),
  ('the Sun', MS, RSUN, AU, 1.0),
)


def heldRate(calc, r):
  """a clock held still at r: moving out through space at u, it runs at sqrt(1 - u^2/c^2) of the flow's time"""
  u = np.linalg.norm(calc.flow(np.array([r, 0.0]), None, 0.0))
  return math.sqrt(1 - u*u/C**2)


def pulse(calc, t, r0, r1):
  """light sent straight out from r0 at time t, followed to r1 (landing on it): its rows and arrival time"""
  p = Particle()
  p.pos, p.t = np.array([r0, 0.0]), t
  calc.initPW(p, np.array([C, 0.0]))
  rows, steps = [(p.t, p.pt, *p.pos, *p.v)], 0
  while p.pos[0] < r1:
    dt = STEP*p.pos[0]/C
    if p.pos[0] + p.v[0]*dt > r1:
      dt = (r1 - p.pos[0])/p.v[0]
    calc.move(p, dt)
    steps += 1
    if steps % EVERY == 0:
      rows.append((p.t, p.pt, *p.pos, *p.v))
  if rows[-1][0] != p.t:
    rows.append((p.t, p.pt, *p.pos, *p.v))
  return rows, p.t


def held(r, rate, t0, t1):
  """a clock held still at r from t0 to t1: its rows (proper time from 0 at t0)"""
  return [(t, (t - t0)*rate, r, 0.0, 0.0, 0.0) for t in np.linspace(t0, t1, 50)]


def run(folder, name, mass, r0, r1, interval, viewer):
  calc = SpecialFlowCalculator([Body(mass)], order=2)
  rs = schwarzschildRadius(mass)
  rateE, rateR = heldRate(calc, r0), heldRate(calc, r1)
  sent = [k*interval/rateE for k in range(PULSES)]               #the flow's time of each pulse, by the emitter's clock
  made, arrivals = [], []
  for k, t in enumerate(sent):
    rows, arrive = pulse(calc, t, r0, r1)
    arrivals.append(arrive)
    if viewer:
      made.append((write(folder, 'pulse%d' % k, calc, rows, COLUMNS, ['pulse %d, sent at %.6g s of the emitter\'s'
                         ' clock from %g m, received at %g m' % (k, k*interval, r0, r1)]), COLOURS['pulse'], 'solid'))
  gapsFlow = np.diff(arrivals)
  received = float(np.mean(gapsFlow))*rateR                       #the receiver's own time between arrivals
  ratio = interval/received                                       #received frequency over emitted
  exact = math.sqrt((1 - rs/r0)/(1 - rs/r1))
  climb = arrivals[0] - sent[0]
  lines = ['%s: %.4g kg, rs %.6g m; emitter at %.6g m (%.4g rs), clock %.9f; receiver at %.6g m, clock %.9f'
           % (name, mass, rs, r0, r0/rs, rateE, r1, rateR),
           '  pulses every %g s of the emitter\'s clock = %.9g s of the flow\'s time; they arrive every %.9g s of the'
           ' flow\'s time (spread %.1e s), = %.9g s of the receiver\'s clock' % (interval, interval/rateE,
                                                                               np.mean(gapsFlow), np.ptp(gapsFlow), received),
           '  each takes %.9g s to climb (exact %.9g s); received / emitted frequency %.12f, exact %.12f, ratio - 1 %.1e;'
           ' redshift z = %.6e' % (climb, rayTime(rs, r0, r1), ratio, exact, ratio/exact - 1, 1/ratio - 1)]
  if viewer:
    end = arrivals[-1]*1.05
    made.insert(0, (write(folder, 'emitter', calc, held(r0, rateE, 0.0, end), COLUMNS,
                          ['the emitter, held still at %g m: its clock at %.6f of the flow\'s time' % (r0, rateE)]),
                    COLOURS['emitter'], 'solid'))
    made.insert(1, (write(folder, 'receiver', calc, held(r1, rateR, 0.0, end), COLUMNS,
                          ['the receiver, held still at %g m: its clock at %.6f of the flow\'s time' % (r1, rateR)]),
                    COLOURS['receiver'], 'solid'))
    writeViewerFiles(folder, 'redshift_star', made, selection=(('pos_x', 't'),), styles=X_T,
                     preferences={'equalAspect': False, 'showBodies': False, 'showSchwarzschild': False,
                                  'showFlow': False, 'showPathLegend': False})
  return lines


def main():
  folder = os.path.join(LOG_DIR, 'redshift', 'redshift_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = []
  for k, (name, mass, r0, r1, interval) in enumerate(BODIES):
    lines += run(folder, name, mass, r0, r1, interval, k == 0) + ['']
    print('\n'.join(lines[-4:]), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)
  return folder


if __name__ == '__main__':
  main()
