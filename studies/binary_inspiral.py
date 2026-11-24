"""
a binary moved by the flow model's own motion, losing energy to its waves (Model to-do, Gravitational waves 4).

the model's motion: in the J = 0 flow each body moves with the regular part of its space, which is GR's first
post-Newtonian motion, EIH (studies/binary_regularized.py, eccentric_bodies.py). the reaction rides in the flow
(studies/flow_reaction.py): Bernoulli's equation holds for the J = 0 flow, so a body moving with its space feels
-grad Phi_RR at itself, whatever the masses. so the binary moves by EIH plus Burke-Thorne (engine/radiation.py
EIHBinary), Q's derivatives along the EIH orbit. checks:

  circular   two neutron stars (M = 2.8 solar masses) at x = (G M Omega)^(2/3)/c^2 = 0.001, 0.002, 0.005, 0.01,
             40 orbits each, less a control without the reaction: x's rate against the leading order, Peters',
             dx/dt = (64/5) eta (c^3/GM) x^5. this motion and this reaction make it 1 + (2 - 2 eta) x more: the
             orbit's EIH energy drains at the reaction's work times 1 + (9/2 - 7 eta/2) x (its velocity terms), the
             EIH orbit's radiated power is 1 - 4 (1 - eta/3) x of Peters', and dE/dx is 1 - (3/2 + eta/6) x of
             Newton's. GR's own rate is 1 - (743/336 + 11 eta/4) x: at first post-Newtonian order the flux has
             corrections from the source beyond its quadrupole, and the reaction its own 3.5PN terms, that a
             leading-order reaction leaves out - for the waves' next order, not the motion's
  eccentric  e = 0.6, GM/c^2 a = 0.001 and 0.002: the reaction's work and torque over one orbit (periastron to
             periastron), against Peters and Mathews' energy and angular momentum losses at leading order. the orbit's
             EIH energy changes by more than the work (its velocity terms, as above): given too
  pulsar     PSR B1913+16, Hulse and Taylor's: masses 1.438 and 1.390 solar masses, P = 27906.98 s, e = 0.6171340
             (Weisberg and Huang 2016). the reaction's work over one orbit (periastron to periastron: the EIH orbit
             takes a little longer than Newton's, and nearly all the power is at periastron) gives dE/dt, and the
             period's rate dP/dt = -(3/2) (P/E) dE/dt, against GR's (Peters-Mathews) -2.40263e-12 and the observed
             0.9983 +- 0.0016 of it (after the Galaxy's acceleration)

writes logs/binaryInspiral/binaryInspiral_<datetime>/checks.log

run: python3 studies/binary_inspiral.py      (several minutes)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.radiation import EIHBinary, peters
from engine.logger import LOG_DIR
from engine.constants import *

M1 = M2 = 1.4*MS
PER_ORBIT = 2000


def omegaOf(s):
  x, v = s[:2], s[2:]
  return (x[0]*v[1] - x[1]*v[0])/(x @ x)


def xRate(eta, x0, reaction):
  """a circular EIH orbit at x0, 40 orbits: x averaged orbit by orbit, its fitted rate, and its mean"""
  GMt = G*(M1 + M2)
  r0 = GMt/(C*C*x0)/(1 + (1 - eta/3)*x0)                       #EIH's circular radius (harmonic) for x0
  b = EIHBinary(M1, M2, r0, 0.0, reaction)
  Om = math.sqrt(GMt/r0**3*(1 - (3 - eta)*GMt/(C*C*r0)))      #EIH's circular angular speed
  b.states[0] = np.array([r0, 0.0, 0.0, Om*r0])
  period = 2*math.pi/Om
  b.run(40*period, PER_ORBIT)
  ts, xs = [], []
  for k in range(1, 41):
    t0 = (k - 1)*period
    xs.append(np.mean([(GMt*omegaOf(b.state(t0 + j*period/64)))**(2/3)/C**2 for j in range(64)]))
    ts.append(t0 + period/2)
  return np.polyfit(ts[1:], xs[1:], 1)[0], float(np.mean(xs[1:]))


def circular(lines):
  lines.append('CIRCULAR: two %g solar-mass bodies, %d steps an orbit, 40 orbits; x\'s rate less a control\'s, over'
               ' Peters\' leading-order rate' % (M1/MS, PER_ORBIT))
  eta = M1*M2/(M1 + M2)**2
  lines.append('  %8s %12s %16s %16s %16s' % ('x', 'ratio', '(ratio - 1)/x', 'this motion', 'GR\'s 1PN'))
  worst = 0.0
  for x0 in (0.001, 0.002, 0.005, 0.01):
    rate, x = xRate(eta, x0, True)
    control, _ = xRate(eta, x0, False)
    ratio = (rate - control)/(64/5*eta*C**3/(G*(M1 + M2))*x**5)
    k = (ratio - 1)/x
    worst = max(worst, abs(k - (2 - 2*eta))*x)
    lines.append('  %8.4f %12.6f %16.3f %16.3f %16.3f' % (x, ratio, k, 2 - 2*eta, -(743/336 + 11*eta/4)))
    print(lines[-1], flush=True)
  lines.append('')
  return worst


def angularMomentum(b, s):
  """EIH's conserved angular momentum (z, J s): mu x cross v [1 + ((1 - 3 eta) v^2/2 + (3 + eta) GM/r)/c^2]"""
  x, v = s[:2], s[2:]
  r = math.hypot(*x)
  return b.mu*(x[0]*v[1] - x[1]*v[0])*(1 + ((1 - 3*b.eta)*(v @ v)/2 + (3 + b.eta)*b.GM/r)/C**2)


def oneOrbit(b, period, steps):
  """run past one orbit; the averages over it, periastron to periastron, of the reaction's work, torque and the rate
  it drains the EIH energy at (W, N m, W), and the orbit's own semi-major axis and eccentricity (from its closest and
  furthest points) and period: the EIH orbit started with Newton's speed is not the Newtonian one, by GM/c^2 a"""
  b.run(1.2*period, steps)      #the EIH orbit started with Newton's speed at periastron runs a few percent longer
  r = [math.hypot(*s[:2]) for s in b.states]
  half = next(i for i, t in enumerate(b.times) if t > period/2)
  i1 = next(i for i in range(half, len(r) - 1) if r[i] < r[i - 1] and r[i] <= r[i + 1])
  t = np.array(b.times[:i1 + 1])
  work, torque, drain = [], [], []
  for s in b.states[:i1 + 1]:
    aR = b.acceleration(s) - b.conservative(s)
    x, v = s[:2], s[2:]
    work.append(b.mu*aR @ v)
    torque.append(b.mu*(x[0]*aR[1] - x[1]*aR[0]))
    h = 1e-6*math.sqrt(v @ v)
    grad = np.array([(b.energy(s + h*e) - b.energy(s - h*e))/(2*h) for e in np.eye(4)[2:]])
    drain.append(grad @ aR)
  avg = lambda f: float(np.sum((np.array(f[1:]) + np.array(f[:-1]))/2*np.diff(t))/(t[-1] - t[0]))
  rp, ra = min(r[:i1 + 1]), max(r[:i1 + 1])
  return avg(work), avg(torque), avg(drain), (rp + ra)/2, (ra - rp)/(ra + rp), t[-1] - t[0]


def eccentric(lines):
  e0 = 0.6
  GMt = G*(M1 + M2)
  f = lambda e: (1 + 73/24*e*e + 37/96*e**4)/(1 - e*e)**3.5
  lines.append('ECCENTRIC: e = %g, one orbit, %d steps; the reaction\'s work and torque against Peters and Mathews\''
               ' leading-order losses' % (e0, 20*PER_ORBIT))
  lines.append('  %10s %12s %12s %16s' % ('GM/c^2 a', 'work', 'torque', 'EIH energy\'s'))
  worst = 0.0
  growth = 0.0
  for xa in (0.001, 0.002):
    a0 = GMt/(C*C*xa)
    b = EIHBinary(M1, M2, a0, e0)
    W, T, D, a, e, _ = oneOrbit(b, 2*math.pi*math.sqrt(a0**3/GMt), 20*PER_ORBIT)
    wantE = -32/5*G**4*b.mu**2*b.M**3/(C**5*a**5)*f(e)
    wantL = -32/5*G**3.5*b.mu**2*b.M**2.5/(C**5*a**3.5)*(1 + 7/8*e*e)/(1 - e*e)**2
    worst = max(worst, abs(W/wantE - 1), abs(T/wantL - 1))
    growth = growth or a/a0 - 1
    lines.append('  %10g %12.6f %12.6f %16.6f    (each over Peters-Mathews)' % (xa, W/wantE, T/wantL, D/wantE))
    print(lines[-1], flush=True)
  lines.append('  (Peters-Mathews with the orbit\'s own a and e, from its closest and furthest points: started with Newton\'s'
               ' speed, it is %.1f%% larger than the a it was started for at GM/c^2 a = 0.001. each ratio is then'
               ' 1 + O(GM/c^2 a), the leading-order formula against first post-Newtonian motion)' % (100*growth))
  lines.append('')
  return worst


def pulsar(lines):
  mp, mc = 1.438*MS, 1.390*MS
  P, e = 27906.98, 0.6171340
  M = mp + mc
  a = (G*M*(P/(2*math.pi))**2)**(1/3)
  b = EIHBinary(mp, mc, a, e)
  dEdt, _, _, a, e, P = oneOrbit(b, P, 200000)     #the model orbit's own a, e and period
  E = -G*mp*mc/(2*a)
  Pdot = -1.5*P/E*dEdt
  f = (1 + 73/24*e*e + 37/96*e**4)/(1 - e*e)**3.5
  gr = -192*math.pi*G**(5/3)/(5*C**5)*(P/(2*math.pi))**(-5/3)*f*mp*mc/M**(1/3)
  lines.append('PULSAR B1913+16: masses %.3f and %.3f, started for P = 27906.98 s, e = 0.6171340; the model orbit\'s own'
               ' P = %.2f s, e = %.7f, and GR\'s formula with them' % (mp/MS, mc/MS, P, e))
  lines.append('  the model: dP/dt = %.5e    GR (Peters-Mathews) %.5e    ratio %.6f' % (Pdot, gr, Pdot/gr))
  lines.append('  observed, less the Galaxy\'s part: 0.9983 +- 0.0016 of GR (Weisberg and Huang 2016)')
  return Pdot/gr


def main():
  folder = os.path.join(LOG_DIR, 'binaryInspiral', 'binaryInspiral_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = ['a binary moved by the flow model\'s motion (EIH) with the reaction riding in the flow (Burke-Thorne)', '']
  c = circular(lines)
  ecc = eccentric(lines)
  ratio = pulsar(lines)
  lines += ['', 'worst: circular %.1e off 1 + (2 - 2 eta) x; eccentric %.1e off Peters-Mathews (GM/c^2 a <= 0.002);'
            ' pulsar %.6f of GR' % (c, ecc, ratio)]
  with open(os.path.join(folder, 'checks.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
