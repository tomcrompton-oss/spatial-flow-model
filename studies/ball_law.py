"""
the ball law in the flow: what flat space gets right, and what it leaves for curved space

Baez and Bunn's form of Einstein's equation: a small ball of test particles, at rest relative to an observer moving at
4-velocity n, starts to shrink at a rate set by the energy and pressure inside it,
R_nn = 4 pi G (rho + p_x + p_y + p_z) - for every n, every observer. Einstein's equation is this for all of them.

the flow model with flat space: ds^2 = -dt^2 + |dx - u dt|^2 (c = 1), clocks keeping the flow's time (N = 1), and a
flow with no curl, u = grad phi. the observers falling with the flow have n = d_t + u.grad. exact (sympy), for an
arbitrary phi(t, x, y, z):

  1. R_nn = -div(Du/Dt), Du/Dt = d_t u + (u.grad)u, the flow's acceleration. with Bernoulli's equation,
     d_t phi + |u|^2/2 = U, Du/Dt = grad U, so R_nn = -lap U = 4 pi G rho: the ball law for balls falling with the
     flow, exactly - to every order, not only Newton's
  2. R_ni = 0, n's mixed part (the momentum constraint): met by every flow with no curl
  3. G_nn = (K^2 - K_ij K_ij)/2, K_ij = d_i d_j phi: the Hamiltonian constraint, which flat space meets only where that
     is 8 pi G rho - for one body, not for two (studies/constraints.py: 13%, up to 82%, for the eikonal flow)
  4. one body, phi = -2 sqrt(2 M r) (Painleve-Gullstrand): every component of R_mu nu is 0, as Schwarzschild's are

so a ball moving through the flow at w (4-velocity proportional to n + w) sees R_nn + 2 w^i R_ni + w^i w^j R_ij: with
flat space the first two are the ball law's, and only w^i w^j R_ij is left to be wrong - an error of order w^2/c^2,
which is post-Newtonian for bodies, and whole for light (w = c). that is the part curved space is for

run: python3 studies/ball_law.py     (needs sympy: pip install sympy; under a minute. prints, and writes
     logs/modelChecks/ballLaw_<datetime>/summary.log)
"""
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import sympy as sp
from engine.logger import LOG_DIR

t, x, y, z = X = sp.symbols('t x y z')


def ricci(phi):
  """R_mu nu, its scalar, and the flow-falling observers' n, for ds^2 = -dt^2 + |dx - grad phi dt|^2"""
  u = [sp.diff(phi, v) for v in (x, y, z)]
  g = sp.zeros(4)
  g[0, 0] = -1 + sum(ui**2 for ui in u)
  for i in range(3):
    g[0, i+1] = g[i+1, 0] = -u[i]
    g[i+1, i+1] = 1
  gi = sp.zeros(4)                          #its inverse, exactly: g^00 = -1, g^0i = -u_i, g^ij = delta_ij - u_i u_j
  gi[0, 0] = -1
  for i in range(3):
    gi[0, i+1] = gi[i+1, 0] = -u[i]
    for j in range(3):
      gi[i+1, j+1] = (1 if i == j else 0) - u[i]*u[j]
  G = [[[sum(gi[a, d]*(sp.diff(g[d, b], X[c]) + sp.diff(g[d, c], X[b]) - sp.diff(g[b, c], X[d])) for d in range(4))/2
         for c in range(4)] for b in range(4)] for a in range(4)]
  R = sp.zeros(4)
  for b in range(4):
    for c in range(b, 4):
      R[b, c] = R[c, b] = sum(sp.diff(G[a][b][c], X[a]) - sp.diff(G[a][b][a], X[c])
                              + sum(G[a][a][d]*G[d][b][c] - G[a][c][d]*G[d][b][a] for d in range(4)) for a in range(4))
  scalar = sum(gi[b, c]*R[b, c] for b in range(4) for c in range(4))
  return R, scalar, [1] + u, u


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'ballLaw_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = []
  def say(s):
    lines.append(s)
    print(s, flush=True)
  phi = sp.Function('phi')(*X)
  R, scalar, n, u = ricci(phi)
  Rnn = sum(n[b]*n[c]*R[b, c] for b in range(4) for c in range(4))
  acc = [sp.diff(u[i], t) + sum(u[j]*sp.diff(u[i], X[j+1]) for j in range(3)) for i in range(3)]
  say('flat space, N = 1, u = grad phi, phi(t, x, y, z) arbitrary; n = d_t + u.grad:')
  say('  1. R_nn + div(Du/Dt)            = %s' % sp.simplify(sp.expand(Rnn + sum(sp.diff(acc[i], X[i+1]) for i in range(3)))))
  # n_mu = (-1, 0, 0, 0); a spatial vector orthogonal to n is e_i = d_i (g(n, d_i) = -u_i + u_i = 0)
  for i in range(3):
    Rni = sum(n[b]*R[b, i+1] for b in range(4))
    say('  2. R_n%s                          = %s' % ('xyz'[i], sp.simplify(sp.expand(Rni))))
  H = [[sp.diff(phi, X[i+1], X[j+1]) for j in range(3)] for i in range(3)]
  K2 = sum(H[i][i] for i in range(3))**2 - sum(H[i][j]**2 for i in range(3) for j in range(3))
  say('  3. G_nn - (K^2 - K_ij K_ij)/2   = %s' % sp.simplify(sp.expand(Rnn + scalar/2 - K2/2)))
  M = sp.symbols('M', positive=True)
  r = sp.sqrt(x**2 + y**2 + z**2)
  R1, _, _, _ = ricci(-2*sp.sqrt(2*M*r))
  Q = sp.Rational
  points = ({x: Q(13, 10), y: Q(-7, 10), z: Q(2, 5), M: Q(9, 10)}, {x: Q(1, 5), y: Q(1, 10), z: -3, M: 2},
            {x: -5, y: 4, z: 1, M: Q(1, 10)})
  worst = max(abs(R1[b, c].subs(p).evalf(40)) for p in points for b in range(4) for c in range(4))
  scale = max(abs((M/r**3).subs(p).evalf(40)) for p in points)
  say('  4. one body (Painleve-Gullstrand): the largest R_mu nu at three points, as a fraction of M/r^3: %.1e'
      % (worst/scale))
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
