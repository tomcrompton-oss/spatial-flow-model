"""
the J = 0 flow's bodies: a circular binary of comparable masses, each body moved as a geodesic of the whole
one-potential metric with its own singular terms removed - Hadamard's partie finie, the r^0 coefficient of the
body's acceleration on a small sphere round it, averaged over the sphere (the regularization GR's post-Newtonian
two-body motion is derived with; at first post-Newtonian order it is unambiguous)

why this is the J = 0 flow's rule, and why it can be worked out in GR's harmonic time:

  1. the flow at the body. round the Earth the J = 0 flow moves at ~51 km/s through the turning frame, but it streams
     out from the Earth equally every way: its average over a circle round the Earth is 0 at every radius (part 1
     below, from engine/turning.py LocalTurningFlow). so the flow's regular part at the body is the body's own
     velocity: a body at rest in the turning frame moves with its space
  2. the time. the J = 0 rules (docs Lapse and curved space: N = 1, Einstein's space, the flow slowed by
     (U + u^2/2)/c^2, chi, and the flow plus 4 U_j/c^2) are GR's first post-Newtonian metric in the time
     t = T + phi/c^2 + chi/c^4 (engine/carried.py FreeFallTurning); without rule 5, less the moving bodies'
     4 U_j/c^2 (keep without 'moving'): leaving it out changes only the
     flow, g_Ti, and taken back to harmonic time only g_ti (g_ij at O(c^-4), which moves bodies at 2PN). the
     time's rate at the body is 1 (phi steady there, kappa = 0), and the products of the time's singular parts with
     the field's have no r^0 part on the sphere (half powers of r, or odd in the direction), so at 1PN the
     regularized body moves as it would in harmonic time; chi moves bodies only at 2PN
  so each body moves as a regularized geodesic of GR's harmonic 1PN metric (less 4 U_j without rule 5): part 2,
  exactly, with sympy

part 2: G = M = a = 1, eps = 1/c^2, the bodies on circles about their centre of mass at Newton's omega; per unit
mass L = v^2/2 + U + eps (v^4/8 + 3/2 U v^2 - U^2/2 + psi - 4 U_j v_j), U, U_j, psi as engine/metric.py
PostNewtonian's (psi with each body's kinetic and binding energy and its field's motion, d^2/dt^2 sum GM r/2). each
body's acceleration from Lagrange's equations at points r n round it, moving with it; its finite part; then
omega^2 = 1 + eps k from the two bodies' relative acceleration. GR (EIH): k = -(3 - eta), eta = m1 m2/M^2. for five
metrics: GR's (the J = 0 rules, all five), the rules without rule 5 (less 4 U_j), and the other body's field
alone (with and without its binding term, and without 4 U_j)

part 3: the periastron advance, from the two-body Lagrangian these give. with the relative motion's
L/mu = v^2/2 + GM/r + [lambda v^4/8 + (GM/2r)(alpha v^2 + beta (n.v)^2) - delta (GM)^2/(2 r^2)]/c^2, the advance per
orbit over 2 pi is (GM/(c^2 p)) (lambda/2 + alpha + beta/2 - delta/2) (first-order perturbation, the average of the
1PN Hamiltonian differentiated by the angular momentum at fixed a): 3 for a test body and for EIH at any eta.
leaving out 4 U_j takes -4 G m1 m2 v1 . v2/(r c^2) out of EIH's Lagrangian: alpha 3 + eta -> 3 - 7 eta

run: python3 studies/binary_regularized.py     (needs sympy: pip install sympy; part 2 takes about a minute. prints,
     and writes logs/modelChecks/binaryRegularized_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.logger import LOG_DIR

METRICS = (('GR, the whole metric: the J = 0 rules, all five', 1, True, True),
           ('J = 0 rules without rule 5: GR less 4 U_j', 0, True, True),
           ('the other body alone', 1, False, False),
           ('the other body alone, with its binding term', 1, False, True),
           ('the other body alone, less 4 U_j', 0, False, False))


def flowAtBody(lines):
  """part 1: the J = 0 flow round the Earth (Sun and Earth on circles), averaged over circles round it"""
  from engine.flow import SpecialFlowCalculator
  from engine.turning import LocalTurningFlow
  from turning_eikonal import bodies
  b = bodies()
  omega = SpecialFlowCalculator(b, 2, combine='turning').omega
  f = LocalTurningFlow(b, omega, 0.0)
  lines.append('part 1: the J = 0 flow round the Earth, relative to the turning frame (LocalTurningFlow)')
  th = 2*math.pi*np.arange(720)/720
  for r in (1e6, 1e7, 1e8, 3e8):
    W = np.array([f.w(f.z + r*np.array([math.cos(a), math.sin(a)])) for a in th])
    mean = W.mean(axis=0)
    lines.append('  r %.0e m   |w| %6.0f m/s   its average round the circle (%+.1e, %+.1e) m/s'
                 % (r, np.mean(np.hypot(W[:, 0], W[:, 1])), mean[0], mean[1]))
    print(lines[-1], flush=True)


def regularized(lines):
  """part 2: omega^2 = 1 + eps k for each metric, exactly in the mass ratio q = m2/m1"""
  import sympy as sp
  x, y, z, t, eps = sp.symbols('x y z t epsilon', real=True)
  r = sp.Symbol('r', positive=True)
  nx, ny, nz = sp.symbols('n_x n_y n_z', real=True)
  vx, vy, vz = sp.symbols('v_x v_y v_z', real=True)
  q = sp.Symbol('q', positive=True)
  X, V = sp.Matrix([x, y, z]), sp.Matrix([vx, vy, vz])
  masses = [1/(1 + q), q/(1 + q)]
  round_ = sp.Matrix([sp.cos(t), sp.sin(t), 0])
  paths = [masses[1]*round_, -masses[0]*round_]
  eta = sp.simplify(masses[0]*masses[1])

  def lagrangian(g, which, binding):
    U, Uj, psi = 0, sp.zeros(3, 1), 0
    for b in which:
      zb = paths[b]
      vb = zb.diff(t)
      d = sp.sqrt(((X - zb).T*(X - zb))[0])
      others = sum(masses[o]/sp.sqrt(((zb - paths[o]).T*(zb - paths[o]))[0]) for o in (0, 1) if o != b) if binding else 0
      U += masses[b]/d
      Uj += masses[b]*vb/d
      psi += masses[b]/d*(sp.Rational(3, 2)*(vb.T*vb)[0] - others) + sp.Rational(1, 2)*sp.diff(masses[b]*d, t, 2)
    v2 = (V.T*V)[0]
    return v2/2 + U + eps*(v2**2/8 + sp.Rational(3, 2)*U*v2 - U**2/2 + psi - 4*g*(Uj.T*V)[0])

  def acceleration(L):
    """Lagrange's equations solved for the acceleration to first order in eps: (F0, F1 - M1 F0)"""
    p = sp.Matrix([L.diff(c) for c in V])
    M1 = (p.jacobian(V) - sp.eye(3)).applyfunc(lambda e: sp.expand(e).coeff(eps, 1))
    F = sp.Matrix([L.diff(c) for c in X]) - p.jacobian(X)*V - p.diff(t)
    F0 = F.applyfunc(lambda e: e.subs(eps, 0))
    return F0, F.applyfunc(lambda e: sp.diff(e, eps).subs(eps, 0)) - M1*F0

  def sphereAverage(poly):
    double = lambda k: 1 if k <= 0 else k*double(k - 2)
    total = 0
    for (a, b, c), co in sp.Poly(sp.expand(poly), nx, ny, nz).terms():
      if not (a % 2 or b % 2 or c % 2):
        total += co*sp.Rational(double(a - 1)*double(b - 1)*double(c - 1), double(a + b + c + 1))
    return sp.simplify(total)

  def finitePart(expr, body, own):
    zb, vb = paths[body].subs(t, 0), paths[body].diff(t).subs(t, 0)
    e = expr.subs(t, 0).subs({vx: vb[0], vy: vb[1], vz: vb[2]})
    e = e.subs({x: zb[0] + r*nx, y: zb[1] + r*ny, z: zb[2] + r*nz})
    N2 = nx**2 + ny**2 + nz**2
    swap = {}
    for P in e.atoms(sp.Pow):
      base = sp.expand(P.base)
      if sp.expand(base - r**2*N2) == 0:
        swap[P] = r**(2*P.exp)                                   #the body's own distance: r
      else:
        swap[P] = base.subs(nz**2, 1 - nx**2 - ny**2)**P.exp     #the other's: analytic in r
    e = e.xreplace(swap)
    if not own:
      return sp.simplify(e.subs(r, 0))
    e = sp.expand(sp.series(sp.expand(e)*r**5, r, 0, 6).removeO())
    return sphereAverage(e.coeff(r, 5))

  lines.append('part 2: omega^2 = (GM/a^3)(1 + k GM/(a c^2)), each body its metric\'s regularized geodesic '
               '(GR: k = -(3 - eta))')
  for name, g, own, binding in METRICS:
    parts = []
    for body in (0, 1):
      L = lagrangian(g, (0, 1) if own else (1 - body,), binding)
      a0, a1 = acceleration(L)
      parts.append([finitePart(a0[0], body, own), finitePart(a1[0], body, own), finitePart(a1[1], body, own)])
    newton = sp.simplify(-(parts[0][0] - parts[1][0]))
    k = sp.simplify(-(parts[0][1] - parts[1][1]))
    across = sp.simplify(parts[0][2] - parts[1][2])
    lines.append('  %-46s k = -3 + %s eta    (Newton %s, across the line %s; exactly %s)'
                 % (name, sp.simplify((k + 3)/eta), newton, across, sp.factor(k)))
    print(lines[-1], flush=True)


def advance(lines):
  """part 3: periastron advance per orbit / 2 pi, in units of GM/(c^2 p), from the relative Lagrangian's
  coefficients"""
  lines.append('part 3: periastron advance / (2 pi GM/(c^2 p)), from the two-body Lagrangian')
  k = lambda lam, alpha, beta, delta: lam/2 + alpha + beta/2 - delta/2
  for eta in (0.0, 0.1, 0.2, 0.25):
    gr = k(1 - 3*eta, 3 + eta, eta, 1)
    rules = k(1 - 3*eta, 3 - 7*eta, eta, 1)
    lines.append('  eta %.2f   GR %.3f   without rule 5 %.3f (%.2f of GR\'s)' % (eta, gr, rules, rules/gr))
    print(lines[-1], flush=True)


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'binaryRegularized_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = []
  flowAtBody(lines)
  try:
    import sympy
  except ImportError:
    lines.append('part 2 needs sympy (pip install sympy)')
    print(lines[-1])
  else:
    regularized(lines)
  advance(lines)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
