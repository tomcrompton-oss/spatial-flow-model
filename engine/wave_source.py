"""
where a binary's gravitational waves come from, in the flow model's slicing: the second step of the gravitational-wave
work (Model to-do, Gravitational waves 2)

THE EQUATION. the model is GR sliced by free fall: N = 1, ds^2 = -c^2 dt^2 + gamma_ij (dx^i - u^i dt)(dx^j - u^j dt)
(GR's shift is -u). Einstein's evolution equations in that slicing, with K_ij the rate space is stretched (per second),
are

  d gamma_ij/dt = -2 K_ij - (D_i u_j + D_j u_i)
  d K_ij/dt     = c^2 R_ij + K K_ij - 2 K_ik K^k_j - (Lie derivative along u of K)_ij - (8 pi G/c^2) (S_ij - gamma_ij (S - E)/2)

(S_ij the matter's stress, E its energy density). the constraints (the Hamiltonian and momentum ones) and the trace of
the second are what the model already uses (docs: Lapse and curved space). what's left is the trace-free part. far
from the bodies, write gamma = delta + h and keep what is first order in the wave; then take the transverse-traceless
(TT) part. two things drop out:

  - the flow. (D_i u_j + D_j u_i) is the gradient of a vector, which has no TT part, so the flow enters neither the
    first equation's TT part nor (at first order) the second's. whatever the flow does near the bodies, the waves
    see only space
  - every pure trace (delta_ij) term

and R_ij at first order is -(1/2) laplacian of h for a TT h. so, with the terms of second order in the fields moved to
the right as an effective stress tau_ij (matter's plus the field's own),

  (1/c^2) d^2 h^TT/dt^2 - laplacian h^TT = (16 pi G/c^4) tau^TT

a wave equation for space's TT part, travelling at c, sourced by the bodies' stress: its retarded solution is

  h_ij(x, t) = (4G/c^4) integral of tau_ij(x', t - |x - x'|/c)/|x - x'| d^3x'          (then its TT part)

THE SOURCE, at Newton's order. tau_ij is matter's momentum flux, sum m v_i v_j delta(x - z), plus the gravitational
field's stress, t_ij = (1/4 pi G) (g_i g_j - delta_ij |g|^2/2), g the field. each body's own part of t_ij moves rigidly
with it and is the same at every moment, apart from a trace (which radiates nothing), so only the two bodies' cross
term radiates:

  t_ij = (1/4 pi G) (g1_i g2_j + g2_i g1_j - delta_ij g1 . g2)

and conservation makes the whole source's integral (1/2) d^2/dt^2 of sum m x_i x_j: for a binary
sum m v v - G m1 m2 n n/r. so far away h = (2G/c^4 D) Q'' - the quadrupole formula engine/radiation.py's BinaryWave
uses - and half of it (for a circular orbit) is the field's stress, not the bodies' motion

the field stress here is Newton's (Landau-Lifshitz) form. in the model's own slicing the second-order terms are
the flow's - K K ~ (grad u)^2 and the Lie derivative - which differ from point to point (each body's alone sums to zero
outside it: Gullstrand-Painleve is vacuum). the far wave doesn't see the difference: it takes only the source's
integral, and conservation fixes that at (1/2) Q'' in any slicing. where the terms are matters only near the bodies,
for space's TT part there, of order G Q''/c^4 r - second post-Newtonian, beyond the model's space (built to first
order, where its TT part is zero). nor is there a check with the bodies held at rest: in GR they need struts, and
the whole source then integrates to zero; the model holds them by fiat, with no struts, so its integral has no single
answer to compare with

NUMERICS. the cross term is singular (as 1/r^2) at both bodies, so it is integrated in prolate spheroidal coordinates
about them, x = mid + (d/2) cosh(mu) cos(nu) n + (d/2) sinh(mu) sin(nu) (cos(phi) e + sin(phi) z), in which the
integrand times the volume is bounded: Gauss-Legendre in mu (to MU_MAX), nu and phi
"""
import math
import numpy as np
from engine.constants import C, G

MU_MAX = 18.0                            #the outermost shell: r ~ (d/4) e^18, where the integrand is e^-18 of its peak


def gauss(n, a, b):
  x, w = np.polynomial.legendre.leggauss(n)
  return (b - a)/2*x + (a + b)/2, (b - a)/2*w


class CircularBinary:
  """two point masses on a circular Newtonian orbit of separation d about their centre of mass at the origin, turning
  anticlockwise about z: positions, velocities and the quadrupole's second derivative at any times (arrays allowed)"""

  def __init__(self, m1, m2, d):
    self.m1, self.m2, self.d = m1, m2, d
    self.M = m1 + m2
    self.omega = math.sqrt(G*self.M/d**3)
    self.r1, self.r2 = m2/self.M*d, m1/self.M*d

  def positions(self, t):
    t = np.asarray(t, dtype=float)
    c, s, zero = np.cos(self.omega*t), np.sin(self.omega*t), np.zeros_like(t)
    n = np.stack([c, s, zero], axis=-1)
    return self.r1*n, -self.r2*n

  def velocities(self, t):
    t = np.asarray(t, dtype=float)
    c, s, zero = np.cos(self.omega*t), np.sin(self.omega*t), np.zeros_like(t)
    e = np.stack([-s, c, zero], axis=-1)
    return self.omega*self.r1*e, -self.omega*self.r2*e

  def quadrupoleRate2(self, t):
    """d^2/dt^2 of sum m x_i x_j (3 x 3), exact: sum m (2 v v + a x + x a)"""
    (x1, x2), (v1, v2) = self.positions(t), self.velocities(t)
    out = np.zeros((3, 3))
    for m, x, v in ((self.m1, x1, v1), (self.m2, x2, v2)):
      a = -self.omega**2*x
      out += m*(2*np.outer(v, v) + np.outer(a, x) + np.outer(x, a))
    return out


def crossStress(X, z1, z2, m1, m2):
  """the two bodies' cross term of the field's stress at points X (..., 3), the bodies at z1, z2 (broadcast): (..., 3, 3)"""
  def field(z, m):
    d = X - z
    r = np.sqrt((d*d).sum(axis=-1))
    return -G*m*d/r[..., None]**3
  g1, g2 = field(z1, m1), field(z2, m2)
  dot = (g1*g2).sum(axis=-1)
  t = g1[..., :, None]*g2[..., None, :]
  t = t + np.swapaxes(t, -1, -2)
  t = t - dot[..., None, None]*np.eye(3)
  return t/(4*math.pi*G)


class SpheroidalGrid:
  """quadrature points and weights (volumes) about two foci a distance d apart, centred on mid, the foci along n"""

  def __init__(self, nMu=64, nNu=48, nPhi=24, panels=6):
    mus, wmu = [], []
    edges = np.concatenate([[0.0], np.geomspace(0.05, MU_MAX, panels)])  #panels fine near the foci, wide far out
    for a, b in zip(edges[:-1], edges[1:]):
      x, w = gauss(nMu, a, b)
      mus.append(x)
      wmu.append(w)
    self.mu, self.wmu = np.concatenate(mus), np.concatenate(wmu)
    self.nu, self.wnu = gauss(nNu, 0.0, math.pi)
    self.phi = (np.arange(nPhi) + 0.5)*2*math.pi/nPhi                     #periodic: the midpoint rule is spectral
    self.wphi = np.full(nPhi, 2*math.pi/nPhi)

  def points(self, mid, n, d):
    """the points (N, 3) and their volumes (N,), for foci at mid -+ (d/2) n, n a unit vector in the (x, y) plane"""
    n = np.asarray(n, dtype=float)
    e = np.array([-n[1], n[0], 0.0])
    z = np.array([0.0, 0.0, 1.0])
    MU, NU, PHI = np.meshgrid(self.mu, self.nu, self.phi, indexing='ij')
    W = np.einsum('i,j,k->ijk', self.wmu, self.wnu, self.wphi)
    a = d/2
    along = a*np.cosh(MU)*np.cos(NU)
    across = a*np.sinh(MU)*np.sin(NU)
    X = (np.asarray(mid)[None, None, None, :] + along[..., None]*n + across[..., None]*(np.cos(PHI)[..., None]*e +
                                                                                    np.sin(PHI)[..., None]*z))
    vol = a**3*(np.sinh(MU)**2 + np.sin(NU)**2)*np.sinh(MU)*np.sin(NU)*W
    return X.reshape(-1, 3), vol.reshape(-1)


def sourceIntegral(binary, t, grid):
    """the integral over all space of the source at time t: (matter, field) each 3 x 3"""
    (z1, z2), (v1, v2) = binary.positions(t), binary.velocities(t)
    matter = binary.m1*np.outer(v1, v1) + binary.m2*np.outer(v2, v2)
    sep = z1 - z2
    X, vol = grid.points((z1 + z2)/2, sep/np.linalg.norm(sep), np.linalg.norm(sep))
    field = np.einsum('nij,n->ij', crossStress(X, z1, z2, binary.m1, binary.m2), vol)
    return matter, field


def retarded(binary, observer, t, grid):
    """
    h_ij at observer (3,) at time t: (4G/c^4) times the source's integral, each part at its own retarded time, over
    its distance. matter: each body at the time its light leaves for the observer (solved by iteration), with the
    Lienard-Wiechert factor 1/(1 - n.v/c) a point source's integral carries. field: the quadrature grid laid about
    the bodies; each point then
    takes the bodies where they were at its own retarded time. the integrand is singular where a point is where a body
    was when its light left for the observer, so the grid's foci go there: each body at its own retarded time
    returns (matter part, field part), each 3 x 3
    """
    observer = np.asarray(observer, dtype=float)
    k = 4*G/C**4
    matter = np.zeros((3, 3))
    foci = []
    for m, which in ((binary.m1, 0), (binary.m2, 1)):
      tr = t - np.linalg.norm(observer)/C
      for _ in range(50):
        z = binary.positions(tr)[which]
        tr2 = t - np.linalg.norm(observer - z)/C
        if abs(tr2 - tr) < 1e-15*max(1.0, abs(t)):
          break
        tr = tr2
      z, v = binary.positions(tr)[which], binary.velocities(tr)[which]
      foci.append(z)
      R = observer - z
      dist = np.linalg.norm(R)
      matter += k*m*np.outer(v, v)/(dist*(1 - (R/dist) @ v/C))
    z1, z2 = foci                       #the field's singular points: each body where it was when its light left
    sep = z1 - z2
    X, vol = grid.points((z1 + z2)/2, sep/np.linalg.norm(sep), np.linalg.norm(sep))
    dist = np.linalg.norm(observer - X, axis=-1)
    tr = t - dist/C
    Z1, Z2 = binary.positions(tr)
    field = k*np.einsum('nij,n->ij', crossStress(X, Z1, Z2, binary.m1, binary.m2), vol/dist)
    return matter, field


def onAxis(h):
    """(h+, hx) from h_ij for a wave travelling along z: the TT part of h_ij there"""
    return (h[0, 0] - h[1, 1])/2, h[0, 1]
