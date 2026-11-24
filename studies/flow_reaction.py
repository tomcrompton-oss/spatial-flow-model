"""
the radiation reaction as part of the flow (engine/radiation.py ReactionFlow; Model to-do, Gravitational waves 3): the
Burke-Thorne potential put into Bernoulli's equation changes the flow by du = grad dphi, d dphi/dt + u . grad dphi =
-Phi_RR, and everything in the flow then feels -grad Phi_RR - no force on the bodies. here a light body (1 solar
mass) orbits a heavy one (10) in the corrected flow, moving by the flow model's own step (SpecialFlowCalculator,
the momentum step), and nothing else:

  pointwise   at points round the orbit: dphi solves its equation, du = grad dphi, and space then accelerates at
              d du/dt + grad(u . du) = -grad Phi_RR (finite differences); and |du|/|u|
  inspiral    circular orbits at two radii, run for 60 orbits in the corrected flow: the orbit-averaged radius's
              rate of shrinking against Peters, dr/dt = -(64/5) G^3 m M^2/(c^5 r^3) (the light body's limit).
              the orbits are the model's, so GR's: their first post-Newtonian corrections to the rate (the orbit's
              energy and the waves' power at GM/c^2 r) are left in the comparison, at a few GM/c^2 r; halving
              GM/c^2 r should halve the difference. the energy's rate against the quadrupole formula's power, from
              the run's own quadrupole, is the sharper of the two. each rate is taken less a control's without the
              correction: the model's step lets an orbit's energy creep (1.5e-7 an orbit at 2000 steps), the same
              either way

writes logs/flowReaction/flowReaction_<datetime>/checks.log and a csv of each run's radius (orbit by orbit)

run: python3 studies/flow_reaction.py      (a minute or two)
"""
import csv
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import SpecialFlowCalculator, Particle, Body
from engine.radiation import ReactionFlow, quadrupole_derivatives
from engine.logger import LOG_DIR
from engine.constants import *

M, m = 10*MS, 1*MS
RADII = (3.7e6, 7.4e6)        #GM/c^2 r = 0.004 and 0.002
ORBITS = 60
STEPS = 8000                  #steps an orbit: the step's own energy creep falls as their square


def pointwise(lines, body, r0):
  rf = ReactionFlow(body, m)
  p = Particle()
  p.pos, p.v, p.t = np.array([r0, 0.0]), np.array([0.0, math.sqrt(body.GM/r0)]), 0.0
  rf.prepare(p)
  u = lambda x: -math.sqrt(2*body.GM/np.linalg.norm(x))*x/np.linalg.norm(x)
  h, dt = 1e-3*r0, 1e-5
  grad = lambda f, x: np.array([(f(x + [h, 0]) - f(x - [h, 0]))/(2*h), (f(x + [0, h]) - f(x - [0, h]))/(2*h)])
  worst = [0.0, 0.0, 0.0]
  size = 0.0
  scale = max(abs(rf.potential(x, t)) for x in (np.array([1.5*r0, 0.0]), np.array([0.0, 1.5*r0])) for t in (0.0, 0.1))
  for x in (np.array([0.8*r0, 0.3*r0]), np.array([-1.2*r0, 0.5*r0]), np.array([0.3*r0, -1.5*r0]), np.array([r0, 0.0])):
    for t in (0.0, 0.1, 0.37):
      gphi = grad(lambda y: rf.phi(y, t), x)
      eq = (rf.phi(x, t + dt) - rf.phi(x, t - dt))/(2*dt) + u(x) @ gphi + rf.potential(x, t)
      worst[0] = max(worst[0], abs(eq)/scale)
      worst[1] = max(worst[1], np.linalg.norm(rf.flow(x, t) - gphi)/np.linalg.norm(gphi))
      acc = (rf.flow(x, t + dt) - rf.flow(x, t - dt))/(2*dt) + grad(lambda y: u(y) @ rf.flow(y, t), x)
      want = -grad(lambda y: rf.potential(y, t), x)
      worst[2] = max(worst[2], np.linalg.norm(acc - want)/np.linalg.norm(want))
      size = max(size, np.linalg.norm(rf.flow(x, t))/np.linalg.norm(u(x)))
  lines.append('POINTWISE round an orbit of %g km (12 points and times), finite differences:' % (r0/1e3))
  lines.append('  d dphi/dt + u . grad dphi + Phi_RR:            %.1e of Phi_RR\'s size there' % worst[0])
  lines.append('  du - grad dphi:                                %.1e of du' % worst[1])
  lines.append('  d du/dt + grad(u . du) + grad Phi_RR:          %.1e of grad Phi_RR' % worst[2])
  lines.append('  |du|/|u|, the size of the correction:          up to %.1e' % size)
  lines.append('')


def energy(body, p):
  """the orbit's energy in the model, per unit mass, from the heavy body's flow alone: gamma (c^2 + u . w) - c^2"""
  d = p.pos - np.array([body.x, body.y])
  r = math.sqrt(d @ d)
  u = -math.sqrt(2*body.GM/r)*d/r
  w = p.v - u
  return (C*C + u @ w)/math.sqrt(1 - (w @ w)/(C*C)) - C*C


def inspiral(folder, body, r0, reaction):
  """
  a circular orbit for ORBITS orbits, with or without the flow's correction. returns, each fitted to its values
  orbit by orbit: the rate of the orbit-averaged radius (m/s), of the energy (W/kg), and the quadrupole formula's
  power per unit mass, (G/5c^5) |Q^(3)|^2/m (W/kg), averaged over the run
  """
  rf = ReactionFlow(body, m) if reaction else None
  calc = SpecialFlowCalculator([body], 2, wave=rf)
  p = Particle()
  p.pos = np.array([r0, 0.0])
  calc.initPV(p, np.array([0.0, math.sqrt(body.GM/r0)]))   #a circular orbit: GR's dphi/dt = sqrt(GM/r^3), dr/dt = 0
  period = 2*math.pi*math.sqrt(r0**3/body.GM)
  dt = period/STEPS
  rows, sums, n, angle, last = [], np.zeros(3), 0, 0.0, math.atan2(p.pos[1], p.pos[0])
  for _ in range(ORBITS*STEPS):
    if rf:
      rf.prepare(p)
    calc.move(p, dt)
    xx, xy, yy, zz = quadrupole_derivatives(p.pos, p.v, body.GM, m, (3,))[3]
    sums += (np.linalg.norm(p.pos), energy(body, p), G/(5*C**5)*(xx*xx + 2*xy*xy + yy*yy + zz*zz)/m)
    n += 1
    a = math.atan2(p.pos[1], p.pos[0])
    angle += (a - last + math.pi) % (2*math.pi) - math.pi
    last = a
    if angle >= 2*math.pi:
      angle -= 2*math.pi
      rows.append((p.t, *(sums/n)))
      sums, n = np.zeros(3), 0
  t, r, E, L = np.array(rows).T
  name = 'r%g_%s' % (r0/1e3, 'reaction' if reaction else 'control')
  with open(os.path.join(folder, name + '.csv'), 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'mean_r', 'mean_E', 'mean_power'])
    out.writerows(rows)
  return np.polyfit(t[1:], r[1:], 1)[0], np.polyfit(t[1:], E[1:], 1)[0], L[1:].mean()


def main():
  folder = os.path.join(LOG_DIR, 'flowReaction', 'flowReaction_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  body = Body(M)
  lines = ['the radiation reaction as part of the flow: a %g solar-mass body round a %g solar-mass one, moving in the'
           ' corrected flow by the model\'s own step' % (m/MS, M/MS), '']
  pointwise(lines, body, RADII[0])
  lines.append('INSPIRAL: %d orbits, %d steps an orbit, fitted orbit by orbit. energy: the model\'s, per unit mass,'
               ' against the quadrupole formula\'s power from the run\'s own quadrupole; radius against Peters' % (ORBITS, STEPS))
  lines.append('  %8s %9s %14s %14s %10s %12s | %12s %12s %10s %12s' % ('r (km)', 'GM/c^2 r', 'dE/dt (W/kg)', '-power',
               'ratio - 1', 'control', 'dr/dt (m/s)', 'Peters', 'ratio - 1', 'control'))
  for r0 in RADII:
    dr, dE, L = inspiral(folder, body, r0, True)
    cdr, cdE, _ = inspiral(folder, body, r0, False)
    want = -64/5*G**3*m*M**2/(C**5*r0**3)
    x = G*M/(C*C*r0)
    dE, dr = dE - cdE, dr - cdr          #less the step's own creep, the same with the correction or without
    lines.append('  %8g %9.4f %14.6e %14.6e %10.2e %12.1e | %12.5e %12.5e %10.2e %12.1e'
                 % (r0/1e3, x, dE, -L, dE/-L - 1, cdE, dr, want, dr/want - 1, cdr))
    print(lines[-1], flush=True)
  lines.append('  (each rate less the control\'s: the model\'s step lets the energy creep, by 1.5e-7 an orbit at 2000 steps,'
               ' falling as the steps squared. the energy is GR\'s for the orbit and the power the leading-order formula,'
               ' so they part at first post-Newtonian order, a few GM/c^2 r)')
  with open(os.path.join(folder, 'checks.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
