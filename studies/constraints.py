"""
Einstein's constraints on each of the flow model's spacetimes: the field equations that space and its flow must meet
at each moment, whatever happens next. in the 3+1 form with the lapse N = 1 and space gamma = delta + h/c^2, to the
first order they come in (engine/metric.py notes):

  Hamiltonian   R~ + (div u)^2 - K~ : K~ = 16 pi G rho        (0 outside the bodies)
                R~ = d_i d_j h_ij - lap h_kk (c^2 times space's curvature), K~_ij = (d_i u_j + d_j u_i)/2
  momentum      d_j K~_ij - d_i div u = 0                      (8 pi G rho v/c^2 inside: next order)

two things follow, for any flow with no curl (K~_ij = d_i d_j phi):

  - h = -u u, space contracted along the flow by u^2/c^2, has R~ = -[(div u)^2 - K~ : K~] exactly: it cancels the
    flow's own term, whatever the flow
  - so h = 2 Phi delta - u u (Phi = sum GM/d, Newton's potential) meets the Hamiltonian constraint for every such
    flow, the rest being lap Phi = -4 pi G rho, Poisson's equation. this is GR's space in a free-fall slicing (the
    1PN metric with t = T - S/c^2, any S with u = -grad S); 'space from u', h = |u|^2 delta - u u, misses it by
    -2 lap(|u|^2 - 2 Phi): nothing for the eikonal flow (|u|^2 = 2 Phi), something for every other

measured here, in 3D, by fourth-order differences: the Hamiltonian constraint as a fraction of K~ : K~ (the size of
the flow's own term), and the momentum constraint as a fraction of |grad div u|, at points round the bodies, for

  flows   one body; vectors; along g; eikonal (two bodies at rest, the 2D flow turned about their line); carried
          (engine/carried.py's, in 3D: each body's river with the other's tide; at rest, and moving - the Sun and
          the Earth at their orbital velocities)
  spaces  flat; from u relative to its body (|w|^2 delta - w w, w = u - V_body); GR's (2 Phi delta - u u, the lab's u)

run: python3 studies/constraints.py     (prints, and writes logs/modelChecks/constraints_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.logger import LOG_DIR
from engine.constants import *

NODES, WEIGHTS = np.polynomial.legendre.leggauss(16)


class Bodies:
  """point bodies in 3D: GM, place and velocity"""

  def __init__(self, items):
    self.GM = np.array([g for g, x, v in items])
    self.x = np.array([x for g, x, v in items], float)
    self.v = np.array([v for g, x, v in items], float)

  def potential(self, y, skip=None):
    return sum(g/np.linalg.norm(y - x) for i, (g, x) in enumerate(zip(self.GM, self.x)) if i != skip)

  def pull(self, y, skip=None):
    return sum((g*(x - y)/np.linalg.norm(x - y)**3 for i, (g, x) in enumerate(zip(self.GM, self.x)) if i != skip),
               np.zeros(3))

  def region(self, y):
    return int(np.argmax(self.GM/np.linalg.norm(y - self.x, axis=1)**3))

  def nearest(self, y):
    return float(np.min(np.linalg.norm(y - self.x, axis=1)))


def river(B, k, y):
  d = y - B.x[k]
  r = np.linalg.norm(d)
  return -math.sqrt(2*B.GM[k]/r)*d/r


#---- the flows (each: y -> (u, the velocity of the body whose flow it is))

def oneBody(B):
  return lambda y: (river(B, 0, y), B.v[0])


def vectors(B):
  return lambda y: (sum((river(B, k, y) for k in range(len(B.GM))), np.zeros(3)), np.zeros(3))


def alongG(B):
  def f(y):
    g = B.pull(y)
    return -math.sqrt(2*B.potential(y))*(-g)/np.linalg.norm(g), np.zeros(3)
  return f


def carried(B):
  """engine/carried.py's flow in 3D: in k's region, V_k + its river + grad sigma, s . grad sigma = Phi_T"""
  def f(y):
    k = B.region(y)
    xk = B.x[k]
    d = y - xk
    r = np.linalg.norm(d)
    n = d/r
    phi0, g0 = B.potential(xk, k), B.pull(xk, k)
    PhiT = B.potential(y, k) - phi0 - d @ g0   #Phi = sum GM/d, g = grad Phi
    s = lambda q: math.sqrt(2*B.GM[k]/q)
    radial = -PhiT/s(r)
    total = np.zeros(3)
    for q, wt in zip(NODES, WEIGHTS):
      rr = r*(q + 1)/2
      gT = B.pull(xk + rr*n, k) - g0
      total += wt*r/2*rr*(gT - (gT @ n)*n)/s(rr)
    return B.v[k] + river(B, k, y) + radial*n - total/r, B.v[k]
  return f


def eikonal(B):
  """the 2D eikonal flow of two bodies at rest on the x axis (engine/flow.py 'eikonal-exact'), turned about the axis"""
  from engine.flow import Body, SpecialFlowCalculator
  calc = SpecialFlowCalculator([Body(g/G, x[0], 0.0) for g, x in zip(B.GM, B.x)], 2, direction='eikonal-exact')
  def f(y):
    rho = math.hypot(y[1], y[2])
    p = np.array([y[0], rho])
    u = calc.flow(p, calc.region(p))
    return np.array([u[0], u[1]*y[1]/rho, u[1]*y[2]/rho]), np.zeros(3)
  return f


#---- the spaces (h = c^2 (gamma - delta))

def flatSpace(B, flow):
  return lambda y: np.zeros((3, 3))


def fromBody(B, flow):
  def h(y):
    u, V = flow(y)
    w = u - V
    return (w @ w)*np.eye(3) - np.outer(w, w)
  return h


def grSpace(B, flow):
  def h(y):
    u, V = flow(y)
    return 2*B.potential(y)*np.eye(3) - np.outer(u, u)
  return h


#---- the constraints

def derivative(f, y, i, e):
  """d f/d y_i, fourth order"""
  step = np.zeros(3)
  step[i] = e
  return (8*(f(y + step) - f(y - step)) - (f(y + 2*step) - f(y - 2*step)))/(12*e)


def constraints(flow, space, y, e):
  """the Hamiltonian constraint (and the flow's own term K~:K~, its scale), the momentum constraint (and |grad div u|)"""
  U = lambda q: flow(q)[0]
  J = np.array([derivative(U, y, i, e) for i in range(3)])   #J[i, j] = d_i u_j
  K = (J + J.T)/2
  div = np.trace(J)
  kk = np.sum(K*K)
  #space's curvature: R~ = d_i d_j h_ij - lap h_kk, from the second differences of h (fourth order)
  H = lambda q: space(q)
  R = 0.0
  for i in range(3):
    for j in range(3):
      dj = lambda q, j=j: derivative(H, q, j, e)   #d_j h
      R += derivative(lambda q: dj(q)[i, j], y, i, e)
    R -= derivative(lambda q: derivative(lambda s: np.trace(H(s)), q, i, e), y, i, e)
  ham = R + div*div - kk
  #momentum: d_j K_ij - d_i div u
  Kf = lambda q: (lambda Jq: (Jq + Jq.T)/2)(np.array([derivative(U, q, i, e) for i in range(3)]))
  divf = lambda q: np.trace(np.array([derivative(U, q, i, e) for i in range(3)]))
  dK = sum(derivative(lambda q: Kf(q)[:, j], y, j, e) for j in range(3))
  gdiv = np.array([derivative(divf, y, i, e) for i in range(3)])
  mom = dK - gdiv
  return ham, kk, np.linalg.norm(mom), np.linalg.norm(gdiv)


def points(B, D):
  """round each body (at 0.05-0.3 of their separation) and between, off the axis (the eikonal flow's lift needs it)"""
  out = []
  for k in range(len(B.GM)):
    for f in (0.05, 0.15, 0.3):
      for a in np.linspace(0.3, 2*math.pi - 0.3, 5):
        out.append(B.x[k] + f*D*np.array([math.cos(a), math.sin(a), 0.2]))
  return out


FLOWS = {'one body': oneBody, 'vectors': vectors, 'along g': alongG, 'eikonal': eikonal, 'carried': carried}
SPACES = {'flat': flatSpace, 'from u, its body': fromBody, "GR's, 2 Phi - u u": grSpace}


def survey(name, B, D, flows):
  lines = [name]
  for fname in flows:
    flow = FLOWS[fname](B)
    for sname, sp in SPACES.items():
      space = sp(B, flow)
      hs, ms = [], []
      for y in points(B, D):
        e = 1e-3*B.nearest(y)
        ham, kk, mom, gdiv = constraints(flow, space, y, e)
        hs.append(abs(ham)/kk)
        ms.append(mom/gdiv if gdiv else 0.0)
      lines.append('  %-9s %-18s Hamiltonian / its flow term: median %.1e, max %.1e    momentum: median %.1e, max %.1e'
                   % (fname, sname, np.median(hs), max(hs), np.median(ms), max(ms)))
      print(lines[-1], flush=True)
  return lines


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'constraints_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  D = 1e9
  zero = np.zeros(3)
  lines = []
  lines += survey('one body (1 solar mass)', Bodies([(G*MS, zero, zero)]), D, ['one body'])
  pair = [(G*MS, zero, zero), (G*0.3*MS, np.array([D, 0, 0]), zero)]
  lines += survey('two bodies at rest, 1 and 0.3 solar masses, 1e9 m apart', Bodies(pair), D,
                  ['vectors', 'along g', 'eikonal', 'carried'])
  #moving: the pair going round each other (velocities about their centre of mass, along y)
  w = math.sqrt(G*1.3*MS/D**3)
  moving = [(G*MS, zero, np.array([0, -w*0.3/1.3*D, 0])), (G*0.3*MS, np.array([D, 0, 0]), np.array([0, w*D/1.3, 0]))]
  lines += survey('the same going round each other (the carried flow at their velocities)', Bodies(moving), D, ['carried'])
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
