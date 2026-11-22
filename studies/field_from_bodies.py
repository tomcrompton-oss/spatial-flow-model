"""
where the moving bodies' terms come from: each body's own field, boosted to its velocity and set in the others' clocks
and rulers

the J = 0 rules take three things from GR's first post-Newtonian metric in harmonic coordinates
(studies/flow_field_equations.py):

  g_00 = -1 + 2U - 2U^2 + 2 psi,   psi = sum_b (m_b/r_b)(3/2 v_b^2 - U_others(z_b)) + 1/2 d_t^2 sum_b m_b r_b
  g_0i = -4 U_i,                   U_i = sum_b m_b v_b,i / r_b          (rule 5's 4U_j)
  g_ij = (1 + 2U) delta_ij                                              (rule 2's space, before the slicing)

psi is chi's source (rule 4): its 1/r parts are the bodies' kinetic energy (3/2 v^2) and binding energy (-U_others).
here, exactly (sympy), from one body's static field alone - g_00 = -1 + 2m/R - 2m^2/R^2, g_ij = (1 + 2m/R) delta, the
one-body flow of Part 1 in these coordinates:

  A. a moving body: that field Lorentz-boosted to velocity v (special relativity), against the metric above for one
     body moving at v. order counting m ~ eps^2, v ~ eps; g_00 to eps^4, g_0i to eps^3, g_ij to eps^2
  B. a body in another's field: body 2's static field written in body 1's clocks and rulers where body 2 is
     (dt_local = sqrt(-g_00) dt, dx_local = sqrt(1 + 2U_1) dx, U_1 = a there), against the metric above near body 2
     for two bodies at rest: the terms in m_2 a / r_2

  C. what the bodies' own fields don't give - the nonlinearity between them: for bodies at rest the ball law for
     observers at rest, in vacuum, is R_nn = (lap_gamma N)/N = 0 (a static spacetime's identity), lap_gamma the
     Laplacian of the space gamma = (1 + 2U) delta. two point masses, U = m_1/r_1 + m_2/r_2, at points away from them:
     g_00 = -(1 - 2U + 2U^2 - 2 psi) with psi harmonic (its binding part, sum c_b/r_b) meets it to eps^4, for any c_b;
     with -2U^2 changed it doesn't. so -2U^2 - every product of the bodies' potentials - is the ball law's, and only
     psi's binding constants are left, which B fixes near each body

run: python3 studies/field_from_bodies.py     (needs sympy: pip install sympy; a few seconds. prints, and writes
     logs/modelChecks/fieldFromBodies_<datetime>/summary.log)
"""
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import sympy as sp
from engine.logger import LOG_DIR

Q = sp.Rational
POINTS = ((Q(7, 5), Q(-2, 3), Q(1, 2), Q(1, 3)), (Q(-3, 2), Q(1, 4), Q(-6, 5), Q(-1, 2)), (Q(2), Q(5, 3), Q(0), Q(3, 4)))


def boosted():
  """A: the static one-body field boosted to v along x, against the harmonic metric for one body moving at v"""
  t, x, y, z, eps, m, v = sp.symbols('t x y z epsilon m v', real=True)
  M, V = eps**2*m, eps*v
  gam = 1/sp.sqrt(1 - V**2)
  T, Xb = gam*(t - V*x), gam*(x - V*t)                         #the body's own frame: it sits at its origin
  R = sp.sqrt(Xb**2 + y**2 + z**2)
  gb = sp.diag(-1 + 2*M/R - 2*M**2/R**2, 1 + 2*M/R, 1 + 2*M/R, 1 + 2*M/R)
  Xs, Bs = [t, x, y, z], [T, Xb, y, z]
  L = sp.Matrix(4, 4, lambda a, mu: sp.diff(Bs[a], Xs[mu]))
  g = L.T*gb*L                                                 #the lab metric
  r = sp.sqrt((x - V*t)**2 + y**2 + z**2)
  U = M/r
  psi = U*Q(3, 2)*V**2 + sp.diff(M*r, t, 2)/2
  want = sp.zeros(4)
  want[0, 0] = -1 + 2*U - 2*U**2 + 2*psi
  want[0, 1] = want[1, 0] = -4*U*V
  for i in range(1, 4):
    want[i, i] = 1 + 2*U
  orders = {(0, 0): 4, (0, 1): 3, (0, 2): 3, (0, 3): 3}
  out = []
  for (a, b), label in (((0, 0), 'g_00'), ((0, 1), 'g_0x'), ((0, 2), 'g_0y'), ((1, 1), 'g_xx'), ((2, 2), 'g_yy'),
                        ((1, 2), 'g_xy')):
    n = orders.get((a, b), 2)
    d = sp.series(g[a, b] - want[a, b], eps, 0, n + 1).removeO()
    worst = max(abs(sp.N(d.subs({t: p[3], x: p[0], y: p[1], z: p[2], m: Q(3, 2), v: Q(2, 7), eps: 1}), 30))
                for p in POINTS)
    out.append((label, n, worst))
  return out


def inField():
  """B: body 2's static field in the clocks and rulers of body 1's field, a = U_1 at body 2"""
  r2, m2, a, eps = sp.symbols('r_2 m_2 a epsilon', positive=True)
  M2, A = eps**2*m2, eps**2*a
  clock = 1 - 2*A + 2*A**2                                    #-g_00 of body 1's field there
  ruler = 1 + 2*A                                             #its g_ij
  rho = sp.sqrt(ruler)*r2                                     #the local distance from body 2
  g00 = (-1 + 2*M2/rho - 2*M2**2/rho**2)*clock
  gxx = (1 + 2*M2/rho)*ruler
  U = A + M2/r2                                               #near body 2: U_1 ~ a, plus body 2's own
  psi = (M2/r2)*(-A)                                          #its binding part, the only one at rest
  want00, wantxx = -1 + 2*U - 2*U**2 + 2*psi, 1 + 2*U
  d00 = sp.expand(sp.series(g00 - want00, eps, 0, 5).removeO())
  dxx = sp.expand(sp.series(gxx - wantxx, eps, 0, 3).removeO())
  cross = sp.expand(sp.series(g00, eps, 0, 5).removeO()).coeff(eps, 4).coeff(m2).coeff(a)
  return d00, dxx, cross*r2


def nonlinear():
  """C: the vacuum ball law for observers at rest, lap_gamma N = 0, with gamma = (1 + 2U) delta, for two bodies"""
  x, y, z, eps = sp.symbols('x y z epsilon', real=True)
  P = sp.Matrix([x, y, z])
  bodies = [(Q(1), sp.Matrix([Q(-1, 3), Q(1, 5), 0])), (Q(1, 2), sp.Matrix([Q(2, 3), Q(-1, 4), Q(1, 7)]))]
  dist = lambda zb: sp.sqrt(((P - zb).T*(P - zb))[0])
  U = sum(eps**2*m/dist(zb) for m, zb in bodies)
  c1, c2 = sp.symbols('c_1 c_2')
  psi = eps**4*(c1/dist(bodies[0][1]) + c2/dist(bodies[1][1]))          #any harmonic 1/r parts
  def residual(k):
    N = sp.sqrt(1 - 2*U + k*U**2 - 2*psi)
    gam = 1 + 2*U                                                        #gamma = gam delta: sqrt(det) = gam^(3/2)
    lap = sum(sp.diff(gam**Q(3, 2)*gam**-1*sp.diff(N, v), v) for v in (x, y, z))/gam**Q(3, 2)
    return lap
  points = ({x: Q(1, 2), y: Q(3, 2), z: Q(-1, 3)}, {x: Q(-2), y: Q(1, 3), z: Q(1, 2)}, {x: Q(5, 4), y: Q(-1), z: Q(2)})
  out = []
  for k in (2, 1, 3):
    r = residual(k)
    worst = 0
    for p in points:                                                     #at the point first, then the series in eps
      e = r.subs(p).subs({c1: Q(3, 7), c2: Q(-5, 11)})
      e = sp.series(e, eps, 0, 5).removeO().subs(eps, 1)
      worst = max(worst, abs(sp.N(e, 30)))
    out.append((k, worst))
  return out


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'fieldFromBodies_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = []
  def say(s):
    lines.append(s)
    print(s, flush=True)
  say('A. one body\'s static field, Lorentz-boosted to v, less the harmonic metric for a body moving at v')
  say('   (psi = (m/r) 3/2 v^2 + 1/2 d_t^2 (m r), g_0i = -4 m v_i / r), largest at three points, m = 3/2, v = 2/7:')
  for label, n, worst in boosted():
    say('   %-5s to eps^%d: %.1e' % (label, n, worst))
  d00, dxx, cross = inField()
  say('B. body 2\'s static field in body 1\'s clocks and rulers (U_1 = a at body 2), less the harmonic metric near body 2')
  say('   (psi = -(m_2/r_2) a, the binding part):')
  say('   g_00 to eps^4: %s' % d00)
  say('   g_xx to eps^2: %s' % dxx)
  say('   the m_2 a / r_2 term of g_00: %s (from -2U^2: -4; from 2 psi: -2)' % cross)
  say('C. the vacuum ball law for observers at rest, lap_gamma N = 0, gamma = (1 + 2U) delta, two bodies at rest,')
  say('   g_00 = -(1 - 2U + k U^2 - 2 psi), psi = c_1/r_1 + c_2/r_2 (any c_b), largest residual at three points to eps^4:')
  for k, worst in nonlinear():
    say('   k = %d%s: %.1e' % (k, ' (GR\'s -2U^2)' if k == 2 else '', worst))
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
