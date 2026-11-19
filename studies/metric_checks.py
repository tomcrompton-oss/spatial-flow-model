"""
checks of engine/metric.py, the lapse and curved-space engine:

  river      the one-body flow through the new engine (FlowSpacetime, no lapse, flat) against the flow model's own
             momentum step: an orbit from 200 to 600 Schwarzschild radii, the end points
  isotropic  the same spacetime in isotropic coordinates (no flow; the lapse and curved space carry it): the orbit
             with the same energy and angular momentum - its precession against exact GR for its apsides (in
             Schwarzschild's r), E and L kept; light passing at 20-1000 m from 100 AU, its bending against GR's for
             its impact parameter cL/E; a fall from rest far away, its proper time against the exact fall time
  pn         GR's first post-Newtonian metric (PostNewtonian) of the Sun and the Earth going round each other, a test
             particle near the Earth: its acceleration against EIH's (studies/cross_terms.py) with its mass 0, as a
             fraction of the relativistic part (EIH less Newton) - from velocities 0.1 s either side, so rounding
             (10^-11 m/s^2) limits it far from the Earth; and along a Moon-like orbit for 5 days, where it builds up
  shares     the shares of the lapse (lambda) and of curved space (kappa) on the one-body flow (FlowSpacetime share,
             curve): the close orbit's precession and light's bending against GR's, and a clock at rest - which
             choices are still GR at first order

run: python3 studies/metric_checks.py [check ...]     (default all; prints, and writes
     logs/modelChecks/metricChecks_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, Config, SpecialFlowCalculator
from engine.metric import (MetricCalculator, FlowSpacetime, IsotropicSchwarzschild, PostNewtonian, bodyVelocityAt,
                           bodyAcceleration)
from engine.exact import grPrecessionExact, grDeflectionExact, fallTime
from engine.logger import LOG_DIR
from engine.vectors import length
from engine.constants import *

RS = 2*G*MS/C**2
M = G*MS/C**2
RP, RA = 200*RS, 600*RS


def schwarzschildStart():
  """the close orbit's start in the flow model: at periapsis, moving across at the speed for apoapsis RA (Newton's)"""
  a = (RP + RA)/2
  return np.array([RP, 0.0]), np.array([0.0, math.sqrt(G*MS*(2/RP - 1/a))])


def run(calc, p, span, fraction=2e-4):
  """p moved for span; its distance from the body at each step, and the conserved quantities' largest change"""
  config = Config()
  config.dt, config.stepFraction = span, fraction
  q0 = calc.conserved(p)
  most = {k: 0.0 for k in q0}
  track = []
  for dt in calc.steps(p, config, span):
    calc.move(p, dt)
    q = calc.conserved(p)
    for k in q0:
      most[k] = max(most[k], abs(q[k]/q0[k] - 1))
    track.append((p.t, p.pos.copy()))
  return track, most


def apsides(track, radius):
  """the periapsides' angles and the mean periapsis and apoapsis, distances by radius(x)"""
  r = [radius(x) for _, x in track]
  ang = np.unwrap([math.atan2(x[1], x[0]) for _, x in track])
  peri, rp, ra = [], [], []
  for i in range(1, len(r) - 1):
    if (r[i] < r[i - 1] and r[i] <= r[i + 1]) or (r[i] > r[i - 1] and r[i] >= r[i + 1]):
      #the parabola through the three steps round it, in the angle: its vertex
      a0, a1, a2 = ang[i - 1:i + 2]
      A = np.array([[a*a, a, 1.0] for a in (a0, a1, a2)])
      k = np.linalg.solve(A, np.array(r[i - 1:i + 2]))
      top = -k[1]/(2*k[0])
      (peri if r[i] < r[i - 1] else ra).append((top, k[2] - k[1]**2/(4*k[0])))
  return np.array([a for a, _ in peri]), np.mean([d for _, d in peri]), np.mean([d for _, d in ra])


def river():
  x, v = schwarzschildStart()
  period = 2*math.pi*math.sqrt(((RP + RA)/2)**3/(G*MS))
  ends = []
  for calc in (SpecialFlowCalculator([Body(MS)]), MetricCalculator(FlowSpacetime(SpecialFlowCalculator([Body(MS)])))):
    p = Particle()
    p.pos = x.copy()
    calc.initPV(p, v)
    track, most = run(calc, p, 2*period)
    ends.append(p.pos.copy())
  return ['river: the one-body flow through the metric engine against the flow model\'s momentum step, 2 orbits'
          ' from 200 to 600 rs: end points %.2e m apart (%.1e of the distance)' % (length(ends[0] - ends[1]),
                                                                               length(ends[0] - ends[1])/RP)]


def isotropicStart(S):
  """the close orbit in isotropic coordinates: at the periapsis, its energy and angular momentum the flow model's"""
  x, v = schwarzschildStart()
  flow = SpecialFlowCalculator([Body(MS)])
  p = Particle()
  p.pos = x
  flow.initPV(p, v)
  L = flow.conserved(p)['L']
  rho = (RP - M + math.sqrt(RP*RP - 2*M*RP))/2   #r = rho (1 + m/2 rho)^2
  q = Particle()
  q.pos = np.array([rho, 0.0])
  q.light = False
  q.q = np.array([0.0, L/rho])                   #at an apsis p_r = 0, and x cross p = L
  return q, L


def isotropic():
  S = IsotropicSchwarzschild(Body(MS))
  calc = MetricCalculator(S)
  lines = ['isotropic: one body in isotropic coordinates - no flow, the lapse and curved space carry it all']
  p, L = isotropicStart(S)
  calc.keep(p)
  period = 2*math.pi*math.sqrt(((RP + RA)/2)**3/(G*MS))
  track, most = run(calc, p, 4*period)
  peri, rp, ra = apsides(track, S.radius)
  turnAngle = float(np.mean(np.diff(peri))) - 2*math.pi
  exact = grPrecessionExact(rp, ra, MS)
  lines.append('  the close orbit (the flow model\'s E and L): periapsis %.6g rs, apoapsis %.6g rs (Schwarzschild\'s r);'
               ' precession %.8f rad an orbit, exact GR %.8f: %+.1e; E and L kept to %.1e, %.1e'
               % (rp/RS, ra/RS, turnAngle, exact, turnAngle/exact - 1, most['E'], most['L']))
  for b in (20*RS, 300*RS, 1e4*RS):
    D = 100*AU
    q = Particle()
    q.pos = np.array([-D, b])
    calc.initLight(q, np.array([1.0, 0.0]))
    bGR = abs(calc.conserved(q)['b'])
    config = Config()
    config.dt, config.stepFraction = 2*D/C, 3e-4
    for dt in calc.steps(q, config, 2*D/C):
      calc.move(q, dt)
    bend = math.atan2(-q.v[1], q.v[0])
    lines.append('  light at %g rs from 100 AU: bend %.10e, exact GR for its impact parameter %.10e: %+.1e'
                 % (b/RS, bend, grDeflectionExact(bGR), bend/grDeflectionExact(bGR) - 1))
  #a fall from rest far away: H = c^2 (E = 0), starting radially in
  r0, r1 = 1e4*RS, 10*RS
  q = Particle()
  rho0 = (r0 - M + math.sqrt(r0*r0 - 2*M*r0))/2
  q.pos = np.array([rho0, 0.0])
  q.light = False
  lo, hi = -C, 0.0
  for _ in range(200):   #the inward momentum with E = 0
    mid = (lo + hi)/2
    if S.energy(q.pos, np.array([mid, 0.0]), 0.0, False, None) > 0:
      lo = mid
    else:
      hi = mid
  q.q = np.array([(lo + hi)/2, 0.0])
  calc.keep(q)
  rho1 = (r1 - M + math.sqrt(r1*r1 - 2*M*r1))/2
  dt = 1e-4
  while q.pos[0] > rho1:
    prev = (q.pos[0], q.pt)
    calc.move(q, dt)
  f = (prev[0] - rho1)/(prev[0] - q.pos[0])
  pt = prev[1] + f*(q.pt - prev[1])
  exact = fallTime(G*MS, r0, r1)
  lines.append('  a fall from rest far away, %g rs to %g rs: proper time %.10f s, exact %.10f s: %+.1e'
               % (r0/RS, r1/RS, pt, exact, pt/exact - 1))
  return lines


def pn():
  from studies.cross_terms import eih, ALL
  mu = ME/(MS + ME)
  omega = math.sqrt(G*(MS + ME)/AU**3)
  bodies = [Body(MS, -mu*AU, 0.0, circling=omega), Body(ME, (1 - mu)*AU, 0.0, circling=omega)]
  S = PostNewtonian(bodies)
  calc = MetricCalculator(S)
  lines = ['pn: GR\'s first post-Newtonian metric, the Sun and the Earth going round each other; a test particle near the'
           ' Earth, its acceleration against EIH\'s with its mass 0 (as a fraction of EIH less Newton)']
  t = 0.1*365.25*DAY
  E = bodies[1].at(t)
  for offset, vel in ((np.array([3.84e8, 0.0]), np.array([0.0, 1.0e3])), (np.array([0.0, 4e7]), np.array([5e3, 2e3])),
                      (np.array([-1e9, 5e8]), np.array([-2e4, 1e4]))):
    x, v = E + offset, bodyVelocityAt(bodies[1], t) + vel
    p = Particle()
    p.pos, p.t = x.copy(), t
    calc.initPV(p, v)
    h = 0.1   #seconds either side: the change in the pull over it is far below the relativistic part
    #the acceleration: a centred difference of the velocity over two steps from the middle, back and forward
    back, fwd = Particle(), Particle()
    for q, s in ((back, -h), (fwd, h)):
      q.pos, q.t = x.copy(), t
      calc.initPV(q, v)
      calc.move(q, s)
    a = (fwd.v - back.v)/(2*h)
    gms = [b.GM for b in bodies] + [0.0]
    xs = [b.at(t) for b in bodies] + [x]
    vs = [bodyVelocityAt(b, t) for b in bodies] + [v]
    accel = [bodyAcceleration(b, t) for b in bodies] + [np.zeros(2)]
    ref = eih(gms, xs, vs, ALL, accel)[2]
    newton = sum(b.GM*(xb - x)/length(xb - x)**3 for b, xb in zip(bodies, xs[:2]))
    lines.append('  %.3g m from the Earth: |a - EIH| %.2e m/s^2, of EIH less Newton %.2e m/s^2: %.1e'
                 % (length(offset), length(a - ref), length(ref - newton), length(a - ref)/length(ref - newton)))
  return lines + pnOrbit()


def shares():
  lines = ['shares: the one-body flow with lambda of gravity in the lapse and space curved by kappa (FlowSpacetime);'
           ' the close orbit\'s precession and light\'s bending (at 300 rs from 100 AU) against GR\'s, and a clock at rest'
           ' at 200 rs']
  x, v = schwarzschildStart()
  period = 2*math.pi*math.sqrt(((RP + RA)/2)**3/(G*MS))
  for lam, kappa in SHARES:
    S = FlowSpacetime(SpecialFlowCalculator([Body(MS)]), share=lam, curve=kappa)
    calc = MetricCalculator(S)
    p = Particle()
    p.pos = x.copy()
    calc.initPV(p, v)
    track, most = run(calc, p, 4*period)
    peri, rp, ra = apsides(track, lambda y: length(y))
    prec = float(np.mean(np.diff(peri))) - 2*math.pi
    q = Particle()
    D, b = 100*AU, 300*RS
    q.pos = np.array([-D, b])
    calc.initLight(q, np.array([1.0, 0.0]))
    bGR = abs(calc.conserved(q)['b'])
    config = Config()
    config.dt, config.stepFraction = 2*D/C, 3e-4
    for dt in calc.steps(q, config, 2*D/C):
      calc.move(q, dt)
    bend = math.atan2(-q.v[1], q.v[0])
    clock = S.rate(np.array([RP, 0.0]), S.momentum(np.array([RP, 0.0]), np.zeros(2), 0.0, None), 0.0, None)
    gr = math.sqrt(1 - RS/RP)
    lines.append('  lambda %.2f kappa %.2f: precession / GR\'s (for its apsides, in its own r) %.4f; bending / GR\'s %.4f;'
                 ' clock at rest %+.1e of GR\'s; E kept to %.0e'
                 % (lam, kappa, prec/grPrecessionExact(rp, ra, MS), bend/grDeflectionExact(bGR), clock/gr - 1,
                    most['E']))
  return lines


def pnOrbit():
  """the same, along a path: a Moon-like orbit round the Earth for 5 days in the metric and in EIH (and Newton)"""
  from studies.cross_terms import eih, ALL
  mu = ME/(MS + ME)
  omega = math.sqrt(G*(MS + ME)/AU**3)
  bodies = [Body(MS, -mu*AU, 0.0, circling=omega), Body(ME, (1 - mu)*AU, 0.0, circling=omega)]
  calc = MetricCalculator(PostNewtonian(bodies))
  x0 = bodies[1].at(0.0) + np.array([3.84e8, 0.0])
  v0 = bodyVelocityAt(bodies[1], 0.0) + np.array([0.0, 1.02e3])
  span, dt = 5*DAY, 30.0
  ends = []
  for h in (dt, dt/2):   #the metric's midpoint steps at 30 s and 15 s, taken to zero step (their error goes as h^2)
    p = Particle()
    p.pos = x0.copy()
    calc.initPV(p, v0)
    for _ in range(int(round(span/h))):
      calc.move(p, h)
    ends.append(p.pos.copy())
  p.pos = (4*ends[1] - ends[0])/3
  def rk4(accel):
    x, v, t = x0.copy(), v0.copy(), 0.0
    f = lambda t, x, v: (v, accel(t, x, v))
    for _ in range(int(span/dt)):
      k1 = f(t, x, v)
      k2 = f(t + dt/2, x + k1[0]*dt/2, v + k1[1]*dt/2)
      k3 = f(t + dt/2, x + k2[0]*dt/2, v + k2[1]*dt/2)
      k4 = f(t + dt, x + k3[0]*dt, v + k3[1]*dt)
      x = x + (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])*dt/6
      v = v + (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])*dt/6
      t += dt
    return x
  gms = [b.GM for b in bodies] + [0.0]
  def gr(t, x, v):
    return eih(gms, [b.at(t) for b in bodies] + [x], [bodyVelocityAt(b, t) for b in bodies] + [v], ALL,
               [bodyAcceleration(b, t) for b in bodies] + [np.zeros(2)])[2]
  newton = lambda t, x, v: sum(b.GM*(b.at(t) - x)/length(b.at(t) - x)**3 for b in bodies)
  xg, xn = rk4(gr), rk4(newton)
  return ["  along a path: a Moon-like orbit round the Earth for 5 days: the metric (30 and 15 s steps, to zero step)'s end %.3g m from EIH's,"
          " whose end is %.3g m from Newton's: %.1e" % (length(p.pos - xg), length(xg - xn), length(p.pos - xg)/length(xg - xn))]


SHARES = ((0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5), (0.5, 0))
CHECKS = {'river': river, 'isotropic': isotropic, 'pn': pn, 'shares': shares}


def main():
  chosen = sys.argv[1:] or list(CHECKS)
  folder = os.path.join(LOG_DIR, 'modelChecks', 'metricChecks_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = []
  for name in chosen:
    out = CHECKS[name]()
    print('\n'.join(out), flush=True)
    lines += out + ['']
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
