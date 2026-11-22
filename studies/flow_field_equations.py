"""
where the J = 0 rules' first post-Newtonian pieces come from: Einstein's equations in the slicing N = 1, for any flow
u0 = grad phi that keeps Bernoulli's equation (d phi/dT + |u0|^2/2 = U, J = 0) and Einstein's space (rule 2,
gamma = delta + (2U delta - u0 u0)/c^2). the flow's correction (gamma u = u0 + A/c^2 - grad chi/c^2) is the rules'
A = f u0 + a: rule 3, f = -(U + |u0|^2/2); rule 5, a = 4 U_j. K~ = c K = (-d_T gamma + D_i beta_j + D_j beta_i)/2,
beta = -u, in vacuum (away from the bodies), at first post-Newtonian order (eps = 1/c^2):

  momentum constraint   D_j K~^j_i - D_i K~ = 0. on a correction it acts as -(1/2) curl curl, so it fixes the
                        correction's curl and nothing else; space's next order (c^-4) doesn't enter. tested with
                        rules 3 and 5, each alone, and neither
  trace of the evolution equation (Raychaudhuri's, for the observers moving with the flow: with N = 1 they fall
                        freely)   d_T K~ - beta . grad K~ - K~ : K~ = -c^2 lap N. no space's next order either; it
                        fixes the correction's divergence. the rules' metric without chi (N = 1 left out) should miss
                        it by -lap Q/c^2, Q = c^4 (N^2 - 1)/2 the lapse chi takes away - so the equation asks of chi
                        just what N = 1 does. tested with psi whole and with psi's 1/r parts (the bodies' kinetic
                        and binding energy) left out: harmonic away from the bodies, the vacuum equation can't see
                        them

everything exact (sympy), at three points, t = 0: G = 1, two bodies (masses 1 and 1/2) on general curved paths, and
phi an arbitrary smooth function at t = 0, its rates from Bernoulli. nothing here is the J = 0 flow's own table: the
results hold for every flow with Bernoulli's equation

run: python3 studies/flow_field_equations.py     (needs sympy: pip install sympy; about two minutes. prints, and
     writes logs/modelChecks/flowFieldEquations_<datetime>/summary.log)
"""
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
from engine.logger import LOG_DIR

POINTS = ((1, 3, 1, 2, -1, 4), (-1, 2, -1, 3, 2, 5), (1, 1, 1, 5, 1, 7))   #numerator, denominator pairs


def setup():
  import sympy as sp
  R = sp.Rational
  x, y, z, t, eps = sp.symbols('x y z t epsilon', real=True)
  X = [x, y, z]
  bodies = [(R(1), sp.Matrix([R(-1, 3) + R(1, 5)*t + R(1, 7)*t**2, R(1, 4)*t - R(1, 9)*t**2, R(1, 11)*t])),
            (R(1, 2), sp.Matrix([R(2, 3) - R(2, 5)*t, -R(1, 2)*t + R(1, 13)*t**2, R(1, 6)*t**2]))]
  P = sp.Matrix(X)
  dist = lambda zb: sp.sqrt(((P - zb).T*(P - zb))[0])
  U = sum(m/dist(zb) for m, zb in bodies)
  Uj = sum((m*zb.diff(t)/dist(zb) for m, zb in bodies), sp.zeros(3, 1))
  phi0 = R(3, 10)*x*y - R(1, 5)*x**2*z + R(1, 3)*y*z**2 + sp.sin(x + 2*z)/4 + R(1, 2)*x
  g0 = sp.Matrix([sp.diff(phi0, c) for c in X])
  pT = U - (g0.T*g0)[0]/2
  pT0 = pT.subs(t, 0)
  pTT = (sp.diff(U, t) - (g0.T*sp.Matrix([sp.diff(pT0, c) for c in X]))[0]).subs(t, 0)
  phi = phi0 + t*pT0 + t**2/2*pTT                          #Bernoulli's first two rates at t = 0
  u0 = sp.Matrix([sp.diff(phi, c) for c in X])
  return locals()


def metric(s, rule3, rule5):
  import sympy as sp
  X, t, eps, U, Uj, u0 = s['X'], s['t'], s['eps'], s['U'], s['Uj'], s['u0']
  f = -(U + (u0.T*u0)[0]/2) if rule3 else 0
  A = f*u0 + (4*Uj if rule5 else sp.zeros(3, 1))
  h = 2*U*sp.eye(3) - u0*u0.T
  g, gi = sp.eye(3) + eps*h, sp.eye(3) - eps*h
  beta = -(u0 + eps*A)
  Gam = [[[sum(gi[l, m]*(sp.diff(g[m, i], X[k]) + sp.diff(g[m, k], X[i]) - sp.diff(g[i, k], X[m]))/2
               for m in range(3)) for k in range(3)] for i in range(3)] for l in range(3)]
  Db = [[sp.diff(beta[j], X[i]) - sum(Gam[l][i][j]*beta[l] for l in range(3)) for j in range(3)] for i in range(3)]
  K = [[(-sp.diff(g[i, j], t) + Db[i][j] + Db[j][i])/2 for j in range(3)] for i in range(3)]
  trK = sum(gi[j, k]*K[j][k] for j in range(3) for k in range(3))
  return A, g, gi, beta, Gam, K, trK


def momentum(s, rule3, rule5):
  _, g, gi, beta, Gam, K, trK = metric(s, rule3, rule5)
  import sympy as sp
  X = s['X']
  M = []
  for i in range(3):
    total = 0
    for j in range(3):
      for k in range(3):
        total += gi[j, k]*(sp.diff(K[i][j], X[k]) - sum(Gam[l][k][i]*K[l][j] + Gam[l][k][j]*K[i][l] for l in range(3)))
    M.append(total - sp.diff(trK, X[i]))
  return M


def trace(s):
  import sympy as sp
  X, t, R = s['X'], s['t'], sp.Rational
  A, g, gi, beta, Gam, K, trK = metric(s, True, True)
  Ku = [[sum(gi[i, k]*gi[j, l]*K[k][l] for k in range(3) for l in range(3)) for j in range(3)] for i in range(3)]
  up = gi*beta
  E = (sp.diff(trK, t) - sum(up[i]*sp.diff(trK, X[i]) for i in range(3))
       - sum(K[i][j]*Ku[i][j] for i in range(3) for j in range(3)))
  P, U, u0, phi, pT = sp.Matrix(X), s['U'], s['u0'], s['phi'], s['pT']
  def psi(whole):
    total = 0
    for i, (m, zb) in enumerate(s['bodies']):
      vb = zb.diff(t)
      if whole:
        others = sum(mo/sp.sqrt(((zb - zo).T*(zb - zo))[0]) for j, (mo, zo) in enumerate(s['bodies']) if j != i)
        total += m/s['dist'](zb)*(R(3, 2)*(vb.T*vb)[0] - others)
      total += R(1, 2)*sp.diff(m*s['dist'](zb), t, 2)
    return total
  def lapQ(whole):
    v2 = (u0.T*u0)[0]
    Q = R(1, 2)*(-2*U*v2 + v2**2 + 2*(u0.T*A)[0] + pT**2 - 4*U*pT - 2*psi(whole) + 2*U**2 - 2*sp.diff(U, t)*phi)
    return sum(sp.diff(Q, c, 2) for c in X)
  return E, lapQ(True), lapQ(False)


def at(e, s, p, order):
  import sympy as sp
  sub = {s['x']: sp.Rational(p[0], p[1]), s['y']: sp.Rational(p[2], p[3]), s['z']: sp.Rational(p[4], p[5]), s['t']: 0}
  e = e.subs(s['eps'], 0) if order == 0 else sp.diff(e, s['eps']).subs(s['eps'], 0)
  return float(sp.N(e.subs(sub), 25))


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'flowFieldEquations_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  import sympy as sp
  s = setup()
  lines = ['momentum constraint, O(eps), at three points (each a vector); -2 grad dU/dt for comparison']
  for label, r3, r5 in (('rules 3 and 5', 1, 1), ('rule 3 alone', 1, 0), ('rule 5 alone', 0, 1), ('neither', 0, 0)):
    M = momentum(s, r3, r5)
    for p in POINTS:
      ref = [at(-2*sp.diff(sp.diff(s['U'], s['t']), c), s, p, 0) for c in s['X']]
      lines.append('  %-14s %s   O(1) %s   O(eps) [%s]   -2 grad dU/dt [%s]'
                   % (label, '(%d/%d, %d/%d, %d/%d)' % p, max(abs(at(Mi, s, p, 0)) for Mi in M),
                      ', '.join('%+.6e' % at(Mi, s, p, 1) for Mi in M), ', '.join('%+.6e' % q for q in ref)))
      print(lines[-1], flush=True)
  lines.append('trace of the evolution equation (rules 2, 3, 5; N = 1, no chi), O(eps), against -lap Q')
  E, lq, lq0 = trace(s)
  for p in POINTS:
    lines.append('  %s   O(1) %+.1e   O(eps) %+.12e   -lap Q %+.12e   -lap Q, psi without its 1/r parts %+.12e'
                 % ('(%d/%d, %d/%d, %d/%d)' % p, at(E, s, p, 0), at(E, s, p, 1), -at(lq, s, p, 0), -at(lq0, s, p, 0)))
    print(lines[-1], flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
