"""
the J = 0 flow off circles: one potential for two bodies on an eccentric orbit, at Newton's order

with the bodies on circles the J = 0 flow is steady in the turning frame (engine/turning.py). off circles there is no
such frame, so it is built in time: phi keeps Bernoulli's equation, d phi/dt + |grad phi|^2/2 = U (J = 0), a
Hamilton-Jacobi equation, whose characteristics are free-fall paths, du/dt = grad U, along which
d phi/dt = U + |u|^2/2. each body's flow lines are the paths that end in it, run backwards in time from it out to the
snapshot time, as the ray tables run them out from the bodies:

  - near body b the flow is its inflow, |u - v_b|^2 = 2 G m_b/r + 2 (U_other + |v_b|^2/2) - on circles the turning
    flow's |w|^2 at the body (|w|^2 = 2 (U + Omega^2 rho^2/2), Omega rho = v_b) - launched equally every way
  - phi is constant along each body's path through time (kappa = d phi/dT along the body = 0, as for J = 0 on circles,
    where it made the flow's time GR's at the bodies)
  - a point is in the region of the body whose phi there is largest (S = -phi smallest, engine/eikonal.py's rule), so
    phi is continuous across the seam; the bodies' two constants differ by one number, set (as the ray tables do)
    so that at periastron the seam goes through the saddle of the potential between them (Roche's, at the orbit's
    angular speed there), and then kept

measured, at snapshots round the orbit, on a grid within 2.5 a of the centre of mass (phi at a point from the
nearest path's sample, phi + u.(point - sample)): how much of the plane the winning region's paths cover without
folding (a fold - paths crossing - is where a family's flow stops being one-valued, and the flow a kink), and how
near the bodies a point won only past a fold comes; what is covered by neither; and where the seam crosses the
line between the bodies, against the saddle there, with the jump in the flow across it. a check: on circles the
flow must be steady in the turning frame, phi(R(Omega t) y, t) = phi(y, 0)

G = 1, M = m1 + m2 = 1, a = 1 (period 2 pi). numpy only

run: python3 studies/eccentric_flow.py     (about two hours; prints, and writes
     logs/modelChecks/eccentricFlow_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.logger import LOG_DIR

R0 = 1e-3            #launch distance from the body (units of a)
ANGLES = 256
HITS = 240           #arrival times, from the snapshot to BACK later
BACK = 7.0
H = 0.02             #step: dt = H min(distance to a body)/|u|
BOX = 2.5            #half-width of the measured square, and of the bins
BINS = 60


class Orbit:
  def __init__(self, q, e):
    self.m = np.array([1/(1 + q), q/(1 + q)])
    self.e = e

  def rel(self, t):
    """relative position and velocity (body 0 less body 1), periastron at t = 0, along +x"""
    t = np.asarray(t, float)
    E = t + self.e*np.sin(t)
    for _ in range(12):
      E = E - (E - self.e*np.sin(E) - t)/(1 - self.e*np.cos(E))
    c, s = np.cos(E), np.sin(E)
    b = math.sqrt(1 - self.e**2)
    x, y = c - self.e, b*s
    dE = 1/(1 - self.e*c)
    return np.stack([x, y], -1), np.stack([-s*dE, b*c*dE], -1)

  def bodies(self, t):
    r, v = self.rel(t)
    m0, m1 = self.m
    return [(m1*r, m1*v), (-m0*r, -m0*v)]          #body 0 the heavier, both about the centre of mass

  def potential(self, x, t):
    """U and grad U at points x (..., 2), time t (scalar or broadcastable)"""
    U = 0.0
    g = 0.0
    for (z, _), m in zip(self.bodies(t), self.m):
      d = x - z
      r2 = np.sum(d*d, -1)
      r = np.sqrt(r2)
      U = U + m/r
      g = g - m*d/(r2*r)[..., None]
    return U, g


def family(orbit, k, ts):
  """body k's paths, arriving at it at times ts + (0..BACK), run back to time ts: x, u, phi there, [hit, angle]"""
  hits = ts + BACK*(np.arange(1, HITS + 1)/HITS)**2          #denser near the snapshot (near the body)
  th = 2*math.pi*np.arange(ANGLES)/ANGLES
  T, A = np.meshgrid(hits, th, indexing='ij')
  T, A = T.ravel(), A.ravel()
  n = np.stack([np.cos(A), np.sin(A)], -1)
  z, v = orbit.bodies(T)[k]
  other = 1 - k
  zo = orbit.bodies(T)[other][0]
  Uo = orbit.m[other]/np.linalg.norm(z - zo, axis=-1)
  s = np.sqrt(2*orbit.m[k]/R0 + 2*(Uo + np.sum(v*v, -1)/2))
  x = z + R0*n
  u = v - s[:, None]*n                                         #falling in
  phi = np.sum(v*R0*n, -1) - 2*math.sqrt(2*orbit.m[k]*R0)      #the body's constant 0; its inflow's own term
  t = T.copy()
  alive = np.ones(len(T), bool)
  def rates(x, u, t):
    U, g = orbit.potential(x, t)
    return u, g, U + np.sum(u*u, -1)/2
  for _ in range(20000):
    left = t - ts
    go = alive & (left > 0)
    if not go.any():
      break
    zz = orbit.bodies(t)
    dmin = np.minimum(np.linalg.norm(x - zz[0][0], axis=-1), np.linalg.norm(x - zz[1][0], axis=-1))
    dt = np.minimum(H*dmin/np.maximum(np.linalg.norm(u, axis=-1), 1e-9), left)
    dt = np.where(go, -dt, 0.0)
    k1 = rates(x, u, t)
    k2 = rates(x + dt[:, None]/2*k1[0], u + dt[:, None]/2*k1[1], t + dt/2)
    k3 = rates(x + dt[:, None]/2*k2[0], u + dt[:, None]/2*k2[1], t + dt/2)
    k4 = rates(x + dt[:, None]*k3[0], u + dt[:, None]*k3[1], t + dt)
    x = x + dt[:, None]/6*(k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
    u = u + dt[:, None]/6*(k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
    phi = phi - (-dt)/6*(k1[2] + 2*k2[2] + 2*k3[2] + k4[2])  #back in time: phi falls by the integral
    t = t + dt
    zz = orbit.bodies(t)
    hitOther = np.linalg.norm(x - zz[other][0], axis=-1) < R0
    alive &= ~hitOther
  shape = (HITS, ANGLES)
  return x.reshape(shape + (2,)), u.reshape(shape + (2,)), phi.reshape(shape), alive.reshape(shape)


def unfolded(x, alive):
  """each path's samples up to its family's first fold: where the map (arrival, angle) -> place turns over"""
  dxh = np.gradient(x, axis=0)
  dxa = np.roll(x, -1, axis=1) - np.roll(x, 1, axis=1)
  J = dxh[..., 0]*dxa[..., 1] - dxh[..., 1]*dxa[..., 0]
  sign = np.sign(np.median(J[:5]))
  good = (J*sign > 0) & alive
  return np.cumprod(good, axis=0).astype(bool)                 #along each angle, from the body out


def binned(x, val, mask):
  """the mean of val over the samples in each bin of the square, NaN where none"""
  edges = np.linspace(-BOX, BOX, BINS + 1)
  i = np.digitize(x[..., 0][mask], edges) - 1
  j = np.digitize(x[..., 1][mask], edges) - 1
  ok = (i >= 0) & (i < BINS) & (j >= 0) & (j < BINS)
  tot = np.zeros((BINS, BINS))
  cnt = np.zeros((BINS, BINS))
  np.add.at(tot, (i[ok], j[ok]), val[mask][ok])
  np.add.at(cnt, (i[ok], j[ok]), 1)
  with np.errstate(invalid='ignore'):
    return np.where(cnt > 0, tot/cnt, np.nan)


def snapshot(orbit, ts):
  out = []
  for k in (0, 1):
    x, u, phi, alive = family(orbit, k, ts)
    ok = unfolded(x, alive)
    out.append(dict(x=x, u=u, phi=phi, ok=ok, alive=alive, good=binned(x, phi, ok)))
  return out


TOL = 0.04           #a point takes phi from a path's sample this near it, phi + u.(point - sample)

def phiAt(fam, pts, which):
  """phi and u at points from the nearest sample of the family ('alive': any path; 'ok': only unfolded), NaN if none
  within TOL"""
  m = fam[which].ravel()
  xs, us, ph = fam['x'].reshape(-1, 2)[m], fam['u'].reshape(-1, 2)[m], fam['phi'].ravel()[m]
  best = np.full(len(pts), np.inf)
  idx = np.zeros(len(pts), int)
  for c in range(0, len(xs), 4000):
    dd = np.sum((pts[:, None, :] - xs[None, c:c + 4000, :])**2, -1)
    j = dd.argmin(1)
    v = dd[np.arange(len(pts)), j]
    better = v < best
    best[better], idx[better] = v[better], j[better] + c
  if not len(xs):
    return np.full(len(pts), np.nan), np.full((len(pts), 2), np.nan)
  val = ph[idx] + np.sum((pts - xs[idx])*us[idx], -1)
  far = np.sqrt(best) >= TOL
  return np.where(far, np.nan, val), np.where(far[:, None], np.nan, us[idx])


def saddle(orbit, ts):
  """the saddle of the Roche potential (U + w^2 rho^2/2, w the orbit's angular speed at ts) on the bodies' line"""
  (z0, v0), (z1, v1) = orbit.bodies(ts)
  r, v = orbit.rel(ts)
  w = (r[0]*v[1] - r[1]*v[0])/(r @ r)
  lo, hi = 0.05, 0.95
  def f(p):
    y = z1 + p*(z0 - z1)
    _, g = orbit.potential(y, ts)
    g = g + w*w*y
    return g @ (z0 - z1)
  for _ in range(80):
    mid = (lo + hi)/2
    if f(lo)*f(mid) <= 0:
      hi = mid
    else:
      lo = mid
  return z1 + (lo + hi)/2*(z0 - z1), (lo + hi)/2


def seamAlongLine(orbit, ts, fam, offset):
  """where phi_0 = phi_1 + offset on the line between the bodies (a fraction from body 1, the lighter, to body 0),
  from the unfolded paths, and the jump in the flow there, |u_0 - u_1|, with the flow's speed"""
  (z0, _), (z1, _) = orbit.bodies(ts)
  ps = np.linspace(0.02, 0.98, 481)
  ys = z1[None, :] + ps[:, None]*(z0 - z1)[None, :]
  D = phiAt(fam[0], ys, 'ok')[0] - phiAt(fam[1], ys, 'ok')[0] - offset
  ok = ~np.isnan(D)
  ps, ys, D = ps[ok], ys[ok], D[ok]
  out = []
  for c in np.where(np.sign(D[:-1]) != np.sign(D[1:]))[0]:
    y = ys[c:c + 2].mean(0)[None]
    u0, u1 = phiAt(fam[0], y, 'ok')[1][0], phiAt(fam[1], y, 'ok')[1][0]
    out.append((float(ps[c:c + 2].mean()), float(np.linalg.norm(u0 - u1)), float(np.linalg.norm(u0))))
  return out


N = 48               #the measured grid, N x N over the square

def coverage(orbit, ts, fam, offset):
  """fractions of the square: covered by the winning region's unfolded paths; won only by folded paths; by neither;
  and the nearest a point won by folded paths is to a body, in units of the bodies' separation"""
  g = np.linspace(-BOX, BOX, N)
  P = np.stack(np.meshgrid(g, g, indexing='ij'), -1).reshape(-1, 2)
  a0, g0 = phiAt(fam[0], P, 'alive')[0], phiAt(fam[0], P, 'ok')[0]
  a1, g1 = phiAt(fam[1], P, 'alive')[0] + offset, phiAt(fam[1], P, 'ok')[0] + offset
  win0 = np.where(np.isnan(a1), True, np.where(np.isnan(a0), False, a0 >= a1))
  none = np.isnan(a0) & np.isnan(a1)
  ok = np.where(win0, ~np.isnan(g0), ~np.isnan(g1)) & ~none
  folded = ~ok & ~none
  (z0, _), (z1, _) = orbit.bodies(ts)
  sep = np.linalg.norm(z0 - z1)
  dist = np.minimum(np.linalg.norm(P - z0, axis=-1), np.linalg.norm(P - z1, axis=-1))/sep
  near = float(dist[folded].min()) if folded.any() else float('nan')
  return ok.mean(), folded.mean(), none.mean(), near


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'eccentricFlow_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = []
  def say(s):
    lines.append(s)
    print(s, flush=True)
  #the check: on circles, steady in the turning frame
  orbit = Orbit(0.1, 0.0)
  f0, f1 = snapshot(orbit, 0.0), snapshot(orbit, 1.0)
  c, s = math.cos(1.0), math.sin(1.0)
  diffs = []
  for k in (0, 1):
    x1 = f1[k]['x'] @ np.array([[c, -s], [s, c]])            #turned back by Omega t = 1
    b1 = binned(x1, f1[k]['phi'], f1[k]['ok'])
    d = b1 - f0[k]['good']
    scale = np.nanmax(np.abs(f0[k]['good']))
    diffs.append(np.nanmedian(np.abs(d))/scale)
  say('check, circles (q = 0.1): phi at t = 1 turned back, less phi at t = 0, median over the bins / max |phi|: '
      '%.1e, %.1e (the bins\' own scatter)' % tuple(diffs))
  for q in (0.1, 1.0):
    for e in (0.0, 0.3, 0.6):
      orbit = Orbit(q, e)
      fam0 = snapshot(orbit, 0.0)
      y, p = saddle(orbit, 0.0)
      offset = phiAt(fam0[0], y[None], 'ok')[0][0] - phiAt(fam0[1], y[None], 'ok')[0][0]
      if np.isnan(offset):
        say('q %.1f  e %.1f: a family does not reach the saddle at periastron' % (q, e))
        continue
      for ts, label in ((0.0, 'periastron'), (math.pi/2, 'a quarter period on'), (math.pi, 'apastron')):
        fam = fam0 if ts == 0.0 else snapshot(orbit, ts)
        cov = coverage(orbit, ts, fam, offset)
        seam = seamAlongLine(orbit, ts, fam, offset)
        _, ps = saddle(orbit, ts)
        say('q %.1f  e %.1f  %-20s one-valued %.3f  won by folded paths %.3f (nearest %.2f separations from a body)'
            '  no flow %.3f   seam on the line at %s (saddle %.3f, from the lighter body)'
            % (q, e, label, cov[0], cov[1], cov[3], cov[2],
               'none found' if not seam else ', '.join('%.3f |du| %.2f of |u| %.2f' % c for c in seam), ps))
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
