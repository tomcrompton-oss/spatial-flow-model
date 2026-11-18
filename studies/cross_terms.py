"""
which of GR's cross terms the split model (engine/split.py) leaves out: GR's equations of motion at first
post-Newtonian order (Einstein-Infeld-Hoffmann, harmonic coordinates) with each kind of cross term - a term in which
one body's pull on another hangs on a third body, or on the one pulled - scaled by a coefficient, 1 being GR's and 0
leaving it out. the split model gives each body its one-body flow (GR's for a test particle round it, boosted to its
velocity), so what it leaves out is among these:

  F   the place pulled sitting in other bodies' potential: -4 sum_{c != a, b} G m_c/r_ac in body b's pull on a
  S   the source sitting in other bodies' potential: -sum_{c != a, b} G m_c/r_bc
  Sa  the source sitting in the pulled body's potential: -G m_a/r_ab (comparable masses only)
  C   the source accelerating: C1 +1/2 (x_b - x_a).a_b in the bracket, C2 7/2 G m_b a_b/(c^2 r_ab)

the velocity terms are a moving source's field (a boosted one-body solution), so the split model has them

binary: the binary of studies/binary_pulsar.py run in these equations with Sa and C switched, against the model's
periastron advance there (free-fall frames 1 - 0.66 eta of GR's, Lorentz frames 1 + 1.0 eta) and its centre of mass
(free-fall frames accelerating at 0.17 m/s^2 at m2/m1 = 0.1)

moon: the de Sitter test's 90-day tracks (studies/de_sitter.py's, the model's Moon extrapolated to zero step and taken
to harmonic coordinates). first, how much of GR's de Sitter precession each kind of term carries: GR with it left out,
fitted by GR whole with its start, GM_Earth and k free (k as in studies/de_sitter.py: 0 GR's precession, 1 none). then
GR fitted to the model's track with its start, GM_Earth and one term's coefficient free (and with k free as well):
the coefficient the model acts as if it had, and how much of the model's difference from GR the term takes out

run: python3 studies/cross_terms.py binary|moon [tracks folder]   (prints, and writes
     logs/multiBody/crossTerms_<what>_<datetime>/summary.log; moon's tracks: the latest deSitter_90d_eccentric and
     _lunar runs)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.logger import LOG_DIR
from engine.constants import *
import binary_pulsar as bp
import lunar_orbit as lo
import de_sitter as ds


def eih(gms, xs, vs, terms, accel=None):
  """each body's acceleration by EIH, the cross terms scaled by terms {F, S, Sa, C1, C2}; accel: the bodies' accelerations
  for the C terms (Newton's if None)"""
  n, c2 = len(gms), C*C
  if accel is None:
    accel = [sum(gms[b]*(xs[b] - xs[a])/np.linalg.norm(xs[b] - xs[a])**3 for b in range(n) if b != a) for a in range(n)]
  out = []
  for a in range(n):
    acc = np.zeros_like(xs[a])
    v = vs[a]
    for b in range(n):
      if b == a:
        continue
      d = xs[b] - xs[a]
      r = np.linalg.norm(d)
      nBA, nAB = d/r, -d/r
      vb, ab = vs[b], accel[b]
      third = [c for c in range(n) if c not in (a, b)]
      F = sum(gms[c]/np.linalg.norm(xs[a] - xs[c]) for c in third)
      S = sum(gms[c]/np.linalg.norm(xs[b] - xs[c]) for c in third)
      Sa = gms[a]/r
      bracket = (1 - 4*gms[b]/(r*c2) - 4*terms['F']*F/c2 - terms['S']*S/c2 - terms['Sa']*Sa/c2 + v @ v/c2
                 + 2*(vb @ vb)/c2 - 4*(v @ vb)/c2 - 1.5*(vb @ nAB)**2/c2 + terms['C1']*0.5*(d @ ab)/c2)
      acc += (gms[b]*nBA/r**2*bracket + gms[b]/(c2*r*r)*(nAB @ (4*v - 3*vb))*(v - vb)
              + terms['C2']*3.5*gms[b]*ab/(c2*r))
    out.append(acc)
  return out


ALL = dict(F=1.0, S=1.0, Sa=1.0, C1=1.0, C2=1.0)


def binary(ratio, terms, steps=4000, orbits=bp.ORBITS):
  """the binary of studies/binary_pulsar.py in EIH with terms, by fourth-order Runge-Kutta: (advance per orbit (rad),
  period, the centre of mass's acceleration (m/s^2))"""
  M = bp.MTOTAL
  m1 = M/(1 + ratio)
  m2 = M - m1
  rp = bp.A*(1 - bp.E)
  vrel = math.sqrt(G*M*(1 + bp.E)/rp)
  gms = [G*m1, G*m2]
  x = np.array([[m2/M*rp, 0.0], [-m1/M*rp, 0.0]])
  v = np.array([[0.0, m2/M*vrel], [0.0, -m1/M*vrel]])
  period = 2*math.pi*math.sqrt(bp.A**3/(G*M))
  dt = period/steps
  f = lambda x, v: np.array(eih(gms, list(x), list(v), terms))
  t, seps, centre, times = 0.0, [], [], []
  while t < (orbits + 0.5)*period:
    k1x, k1v = v, f(x, v)
    k2x, k2v = v + k1v*dt/2, f(x + k1x*dt/2, v + k1v*dt/2)
    k3x, k3v = v + k2v*dt/2, f(x + k2x*dt/2, v + k2v*dt/2)
    k4x, k4v = v + k3v*dt, f(x + k3x*dt, v + k3v*dt)
    x = x + (k1x + 2*k2x + 2*k3x + k4x)*dt/6
    v = v + (k1v + 2*k2v + 2*k3v + k4v)*dt/6
    t += dt
    rel = x[0] - x[1]
    seps.append((t, np.linalg.norm(rel), math.atan2(rel[1], rel[0])))
    centre.append((m1*x[0] + m2*x[1])/M)
    times.append(t)
  peri = []
  for i in range(1, len(seps) - 1):
    if seps[i][1] < seps[i - 1][1] and seps[i][1] <= seps[i + 1][1]:
      (t0, r0, a0), (t1, r1, a1), (t2, r2, a2) = seps[i - 1], seps[i], seps[i + 1]
      s = 0.5*(r0 - r2)/(r0 - 2*r1 + r2)
      peri.append((t1 + s*dt, a1 + s*math.remainder(a2 - a0, 2*math.pi)/2))
  k, P = bp.advance(peri)
  acc = 2*np.polyfit(np.array(times), np.array(centre), 2)[0]
  return k, P, np.linalg.norm(acc)


def binaryJob(job):
  ratio, name, terms = job
  k, P, acc = binary(ratio, terms)
  gr = 3*(G*bp.MTOTAL*2*math.pi/P)**(2/3)/(C*C*(1 - bp.E**2))*2*math.pi
  return job, k/gr, acc


VARIANTS = {'GR': ALL, 'no Sa': dict(ALL, Sa=0.0), 'no C': dict(ALL, C1=0.0, C2=0.0), 'no C1': dict(ALL, C1=0.0),
            'no C2': dict(ALL, C2=0.0), 'no Sa, no C': dict(ALL, Sa=0.0, C1=0.0, C2=0.0),
            'no Sa, C1': dict(ALL, Sa=0.0, C1=0.0), 'no Sa, C2': dict(ALL, Sa=0.0, C2=0.0)}


STEPS = {'k': 0.01, 'earth': 1e-9, 'F': 0.01, 'S': 0.01, 'C1': 0.01, 'C2': 0.01}
LATEST = {'eccentric': 'deSitter_90d_eccentric_2026-11-18_20-00-07', 'lunar': 'deSitter_90d_lunar_2026-11-18_20-00-07'}


def moonTarget(start, mapped=True):
  """the model's Moon from GR's Earth, from studies/de_sitter.py's tracks, at zero step and in harmonic coordinates"""
  z = np.load(os.path.join(LOG_DIR, 'multiBody', LATEST[start], 'tracks.npz'))
  rel = (4*z['c1_dt2.5'] - z['c1_dt5'])/3
  return ds.harmonic(z['ts'], rel, start) if mapped else (z['ts'], rel)


def grMoon(start, ts, p, free, terms=None):
  """GR's Moon from its Earth at ts: p the start (4) then the free parameters' values"""
  e = dict(zip(free, p[4:]))
  setup = lo.Setup(True, True, turn=e.get('k', 0.0)*ds.DESITTER, earthScale=1 + e.get('earth', 0.0),
                   start=ds.STARTS[start])
  setup.terms = dict(terms or {})
  for name in ('F', 'S', 'C1', 'C2'):
    if name in e:
      setup.terms[name] = 1.0 + e[name]
  lo.SPAN = ts[-1] + DAY
  return ds.relative(lo.grRun(setup, (p[:2], p[2:4]), ds.GRDT), setup, ts)


def moonFit(job):
  """GR (its start and the free parameters) fitted to target, by Levenberg-Marquardt (parameters scaled by their
  steps; a step taken only if it lowers the residual): the free parameters, the rms left (m)"""
  name, start, (ts, target), free = job
  n = 4 + len(free)
  steps = np.array([1.0, 1.0, 1e-6, 1e-6] + [STEPS[f] for f in free])
  resid = lambda q: (grMoon(start, ts, q*steps, free) - target).ravel()
  q = np.concatenate([ds.STARTS[start][0], ds.STARTS[start][1], np.zeros(len(free))])/steps
  r = resid(q)
  lam = 1e-3
  for _ in range(8):
    J = np.array([resid(q + np.eye(n)[k]) - r for k in range(n)]).T
    A, g = J.T @ J, J.T @ r
    for _ in range(6):
      q1 = q - np.linalg.solve(A + lam*np.diag(np.diag(A)), g)
      r1 = resid(q1)
      if r1 @ r1 < r @ r:
        q, r, lam = q1, r1, lam/10
        break
      lam *= 10
    else:
      break
  return job[:2] + (free,), (q*steps)[4:], math.sqrt(np.mean(r*r))


def leftOut(job):
  """GR's Moon with some terms left out, at the de Sitter test's samples"""
  start, terms = job
  ts = ds.samples(90.0)
  return grMoon(start, ts, np.concatenate(ds.STARTS[start]), [], terms)


def moon():
  from multiprocessing import Pool
  ts = ds.samples(90.0)
  out = {'F': dict(F=0.0), 'S': dict(S=0.0), 'C1': dict(C1=0.0), 'C2': dict(C2=0.0), 'C': dict(C1=0.0, C2=0.0)}
  with Pool(9) as pool:
    tracks = dict(zip(out, pool.map(leftOut, [('eccentric', t) for t in out.values()])))
    jobs = [('GR without ' + k, 'eccentric', (ts, tr), ['earth', 'k']) for k, tr in tracks.items()]
    for start in ('eccentric', 'lunar'):
      target = moonTarget(start)
      jobs += [('the model', start, target, free) for free in
               (['earth'], ['earth', 'k'], ['earth', 'F'], ['earth', 'S'], ['earth', 'C1'], ['earth', 'C2'],
                ['earth', 'k', 'C1'], ['earth', 'k', 'C2'], ['earth', 'C1', 'C2'])]
    found = pool.map(moonFit, jobs)
  lines = ['moon: GR\'s cross terms against the model\'s Moon (90 days, studies/de_sitter.py\'s tracks, zero step,'
           ' harmonic coordinates). k: GR turning at k times the de Sitter rate (0 GR\'s precession, 1 none);'
           ' earth: GM_Earth\'s change; F, S, C1, C2: the term\'s coefficient less 1 (-1: left out)']
  for (name, start, free), vals, rms in found:
    lines.append('  %-16s %-9s free %-14s %s; rms %.3f m' % (name, start, ', '.join(free),
                 ', '.join('%s %+.3g' % fv for fv in zip(free, vals)), rms))
  return lines


def main():
  what = sys.argv[1] if len(sys.argv) > 1 else 'binary'
  folder = os.path.join(LOG_DIR, 'multiBody', 'crossTerms_%s_%s' % (what, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
  os.makedirs(folder, exist_ok=True)
  lines = moon() if what == 'moon' else binaryLines()
  print('\n'.join(lines))
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)


def binaryLines():
  from multiprocessing import Pool
  variants = {k: v for k, v in VARIANTS.items() if v is not None}
  jobs = [(q, name, terms) for name, terms in variants.items() for q in bp.RATIOS]
  with Pool(8) as pool:
    found = pool.map(binaryJob, jobs)
  lines = ['binary in EIH with cross terms switched (studies/binary_pulsar.py\'s, 2 solar masses, a = 1e8 m, e = 0.3):'
           ' the periastron advance over GR\'s 1PN formula, and the centre of mass\'s acceleration. the split model:'
           ' free-fall frames 0.834 / 0.946 / 0.994, Lorentz 1.250 / 1.083 / 1.011 (m2/m1 = 1, 0.1, 0.01); centre of'
           ' mass (free-fall) 0.17 m/s^2 at 0.1, 0.07 at 0.01']
  for (q, name, _), ratio, acc in found:
    eta = q/(1 + q)**2
    lines.append('  %-12s m2/m1 %-5g eta %.4f: advance / GR %.5f (%+.2f eta); centre of mass %.3f m/s^2'
                 % (name, q, eta, ratio, (ratio - 1)/eta, acc))
  return lines


if __name__ == '__main__':
  main()
