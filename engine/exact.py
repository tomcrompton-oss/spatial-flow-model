"""
exact results to check the simulations against
"""
import math
from engine.constants import *


def schwarzschildRadius(mass):
  """2GM/c^2 (m): where the flow speed reaches c"""
  return 2*G*mass/C**2


def fallTime(gm, a, d):
  """falling from rest at infinity, the time to fall from a to d: (2/3)(a^1.5 - d^1.5)/sqrt(2GM)"""
  return (2/3)*(a**1.5 - d**1.5)/math.sqrt(2*gm)


def rayTime(rs, r0, r1):
  """
  time for light sent straight out from r0 to reach r1: dr/dt = c - u = c(1 - sqrt(rs/r))
  with s = sqrt(r/rs) the integral is (2 rs/c)[s^2/2 + s + ln(s - 1)]
  """
  f = lambda r: (lambda s: s*s/2 + s + math.log(s - 1))(math.sqrt(r/rs))
  return 2*rs/C*(f(r1) - f(r0))


def grPrecession(a, e, mass=MS):
  """GR's precession of an orbit (rad per orbit): 6 pi GM / (c^2 a (1 - e^2))"""
  return 6*math.pi*G*mass/(C**2*a*(1 - e*e))


def orbitPeriod(a, mass=MS):
  """newtonian period of an orbit with semi-major axis a (s)"""
  return 2*math.pi*math.sqrt(a**3/(G*mass))


#---- exact general relativity (Schwarzschild), by quadrature: no series in GM/c^2 r, so the flow model can be
#compared with GR beyond its leading terms. u = 1/r throughout; the integrals are smoothed by substitutions that
#take the square-root singularities at the turning points out of the integrands

GAUSS_POINTS = 200


def _gauss(f, a, b, n=GAUSS_POINTS):
  """the integral of f from a to b by n-point Gauss-Legendre quadrature"""
  import numpy as np
  x, w = np.polynomial.legendre.leggauss(n)
  return (b - a)/2*sum(wi*f((b - a)/2*xi + (b + a)/2) for xi, wi in zip(x, w))


def grDeflectionExact(b, mass=MS):
  """
  GR's bending of light passing mass at impact parameter b, from infinity to infinity (rad):
    alpha = 2 * integral from 0 to u0 of du / sqrt(f(u))  -  pi,   f(u) = 1/b^2 - u^2 + rs u^3
  where u0 = 1/r0 at the closest approach, the smallest root of f. f(u) = f(u) - f(u0) = (u0 - u) g(u),
  g(u) = (u + u0) - rs (u^2 + u u0 + u0^2), is used rather than f itself, which near u0 is a small difference of
  large numbers (series: 4GM/c^2 b + (15 pi/4)(GM/c^2 b)^2 + ...)
  """
  rs = schwarzschildRadius(mass)
  f = lambda u: 1/b**2 - u*u + rs*u**3
  u0 = 1/b
  for _ in range(100):   #Newton's method from 1/b, the flat-space closest approach
    u0 -= f(u0)/(-2*u0 + 3*rs*u0*u0)
  g = lambda u: (u + u0) - rs*(u*u + u*u0 + u0*u0)
  #u = u0 (1 - s^2): du = -2 u0 s ds and u0 - u = u0 s^2, so du/sqrt(f) = 2 sqrt(u0) ds / sqrt(g) - smooth
  integral = _gauss(lambda s: 2*math.sqrt(u0)/math.sqrt(g(u0*(1 - s*s))), 0.0, 1.0)
  return 2*integral - math.pi


def grPrecessionExact(rPeri, rApo, mass=MS):
  """
  GR's periapsis precession (rad per orbit) of a bound orbit with these closest and farthest distances: with
  u = 1/r, (du/dphi)^2 = rs (u - u1)(u2 - u)(u3 - u), u1 = 1/rApo, u2 = 1/rPeri, u3 = 1/rs - u1 - u2, so
    precession = 4 * integral from 0 to pi/2 of dtheta / sqrt(rs (u3 - u)),  u = u1 + (u2 - u1) sin^2 theta,  - 2 pi
  (series: 6 pi GM / c^2 p + (3 pi/2)(18 + e^2)(GM / c^2 p)^2 + ..., p the semi-latus rectum)
  """
  rs = schwarzschildRadius(mass)
  u1, u2 = 1/rApo, 1/rPeri
  u3 = 1/rs - u1 - u2
  integral = _gauss(lambda th: 1/math.sqrt(rs*(u3 - (u1 + (u2 - u1)*math.sin(th)**2))), 0.0, math.pi/2)
  return 4*integral - 2*math.pi


def impactParameter(pos, w, u):
  """
  GR's impact parameter b = cL/E of light at pos moving at w relative to the flow u (flow model / Painleve-Gullstrand
  coordinates): the conserved energy is E = eps (1 + u.w/c^2) and the angular momentum L = eps |r x w| / c^2, for
  a photon of energy eps as a free faller sees it, so
    b = |r x w| / (c (1 + u.w/c^2))
  light started a distance b0 off the axis, along it, where the flow runs along it at u, has b = b0/(1 + u/c): it
  passes a little closer than b0, and bends by u/c more than 4GM/c^2 b0 (4.4e-5 more, starting at 10 AU)
  """
  cross = abs(pos[0]*w[1] - pos[1]*w[0])
  return cross/(C*(1 + (u[0]*w[0] + u[1]*w[1])/C**2))


#---- exact Kerr (a rotating hole), in its equatorial plane, Boyer-Lindquist r (the same r as the river model's
#Doran coordinates). geometric units inside: M = GM/c^2 and a = spin*M, both in metres; spin is -1 to 1, positive
#when the hole turns anticlockwise. equatorial geodesics with energy E and angular momentum L per unit mass (or,
#for light, E = 1 and L = b, the impact parameter) obey (Chandrasekhar)
#  (r^2 dr/dlam)^2 = Rk(r) = [E(r^2 + a^2) - aL]^2 - Delta [mu^2 r^2 + (L - aE)^2],   Delta = r^2 - 2Mr + a^2
#  r^2 dphi/dlam = (a/Delta)[E(r^2 + a^2) - aL] - (aE - L)
#with mu = 1 for a mass and 0 for light

def _kerrMA(mass, spin):
  M = G*mass/C**2
  return M, spin*M


def _kerrR(r, E, L, M, a, mu):
  delta = r*r - 2*M*r + a*a
  return (E*(r*r + a*a) - a*L)**2 - delta*(mu*r*r + (L - a*E)**2)


def _kerrDphi(r, E, L, M, a):
  """r^2 dphi/dlam"""
  delta = r*r - 2*M*r + a*a
  return a/delta*(E*(r*r + a*a) - a*L) - (a*E - L)


def kerrHorizon(mass, spin):
  """the outer horizon r+ = M + sqrt(M^2 - a^2) (m)"""
  M, a = _kerrMA(mass, spin)
  return M + math.sqrt(M*M - a*a)


def kerrPhotonOrbit(mass, spin, prograde=True):
  """the radius of the circular photon orbit, r = 2M (1 + cos(2/3 arccos(-+ a/M))), prograde or retrograde (m)"""
  M, a = _kerrMA(mass, abs(spin))
  return 2*M*(1 + math.cos(2/3*math.acos((-1 if prograde else 1)*a/M)))


def kerrISCO(mass, spin, prograde=True):
  """the innermost stable circular orbit (Bardeen, Press & Teukolsky 1972) (m)"""
  M, a = _kerrMA(mass, abs(spin))
  x = a/M
  z1 = 1 + (1 - x*x)**(1/3)*((1 + x)**(1/3) + (1 - x)**(1/3))
  z2 = math.sqrt(3*x*x + z1*z1)
  return M*(3 + z2 - (1 if prograde else -1)*math.sqrt((3 - z1)*(3 + z1 + 2*z2)))


def kerrDeflectionExact(b, mass, spin):
  """
  Kerr's bending of light in the equatorial plane, from infinity to infinity, at impact parameter b = L/E (m):
  positive b goes round anticlockwise - with the hole for positive spin. returns the bend (rad), positive towards
  the hole. with u = 1/r, Rk/r^4 = F(u) = 1 + (a^2 - b^2) u^2 + 2M (b - a)^2 u^3 and
    bend = 2 * integral from 0 to u0 of h(u) du / sqrt(F(u))  -  pi,   h = a (1 + (a^2 - ab) u^2)/(1 - 2Mu + a^2 u^2) + b - a
  u0 the smallest root of F; F(u) = (u0 - u) G(u) is used, as in grDeflectionExact, to keep its precision
  """
  M, a = _kerrMA(mass, spin)
  sign = 1.0 if b >= 0 else -1.0
  b, a = abs(b), sign*a   #mirror a clockwise pass into an anticlockwise one round the opposite spin
  F = lambda u: 1 + (a*a - b*b)*u*u + 2*M*(b - a)**2*u**3
  dF = lambda u: 2*(a*a - b*b)*u + 6*M*(b - a)**2*u*u
  u0 = 1/b
  for _ in range(100):   #Newton's method from 1/b, the flat-space closest approach
    u0 -= F(u0)/dF(u0)
  G = lambda u: -(a*a - b*b)*(u + u0) - 2*M*(b - a)**2*(u*u + u*u0 + u0*u0)
  h = lambda u: a*(1 + (a*a - a*b)*u*u)/(1 - 2*M*u + a*a*u*u) + b - a
  def f(s):
    u = u0*(1 - s*s)
    return h(u)*2*math.sqrt(u0)/math.sqrt(G(u))
  return 2*_gauss(f, 0.0, 1.0) - math.pi


def kerrOrbitConstants(rPeri, rApo, mass, spin):
  """E and L (per unit mass, geometric units) of the equatorial orbit with these turning points; L > 0 anticlockwise"""
  M, a = _kerrMA(mass, spin)
  E = math.sqrt(1 - 2*M/(rPeri + rApo))
  L = math.sqrt(2*M*rPeri*rApo/(rPeri + rApo))   #newtonian, to start from
  for _ in range(100):   #Newton's method on Rk(rPeri) = Rk(rApo) = 0
    F = [_kerrR(rPeri, E, L, M, a, 1.0)/rPeri**4, _kerrR(rApo, E, L, M, a, 1.0)/rApo**4]
    hE, hL = 1e-9, 1e-9*L
    J = [[(_kerrR(r, E + hE, L, M, a, 1.0) - _kerrR(r, E - hE, L, M, a, 1.0))/(2*hE)/r**4,
          (_kerrR(r, E, L + hL, M, a, 1.0) - _kerrR(r, E, L - hL, M, a, 1.0))/(2*hL)/r**4] for r in (rPeri, rApo)]
    det = J[0][0]*J[1][1] - J[0][1]*J[1][0]
    dE = (F[0]*J[1][1] - F[1]*J[0][1])/det
    dL = (J[0][0]*F[1] - J[1][0]*F[0])/det
    E, L = E - dE, L - dL
    if abs(dE) < 1e-15 and abs(dL) < 1e-15*L:
      break
  return E, L


def kerrPrecessionExact(rPeri, rApo, mass, spin, prograde=True):
  """
  Kerr's periapsis precession (rad per orbit) of an equatorial orbit with these turning points, going round with the
  hole (prograde) or against it: 2 * integral from rPeri to rApo of (dphi/dr) dr  -  2 pi
  """
  M, a = _kerrMA(mass, abs(spin))
  a = a if prograde else -a
  E, L = kerrOrbitConstants(rPeri, rApo, mass, a/M)
  import numpy as np
  #Rk is a quartic with roots rPeri and rApo: divide them out, leaving a quadratic q with Rk = (r - rPeri)(rApo - r) q
  c4 = E*E - 1
  c3 = 2*M
  c2 = a*a*(E*E - 1) - L*L
  c1 = 2*M*(L - a*E)**2
  c0 = 0.0   #Rk = c4 r^4 + c3 r^3 + c2 r^2 + c1 r (the constant term cancels for mu = 1)
  quartic = [c4, c3, c2, c1, c0]
  quotient, remainder = np.polydiv(quartic, np.poly1d([-1.0, rPeri + rApo, -rPeri*rApo]).coeffs)
  q = np.poly1d(quotient)
  #r = rPeri + (rApo - rPeri) sin^2 theta takes out the square-root zeros at both ends
  def f(th):
    r = rPeri + (rApo - rPeri)*math.sin(th)**2
    return 2*_kerrDphi(r, E, L, M, a)/math.sqrt(q(r))
  return 2*_gauss(f, 0.0, math.pi/2) - 2*math.pi


def kerrImpactParameter(pos, w, u, a):
  """
  the impact parameter b = L/E of light at pos (from the hole) moving at w relative to the river u, in the river
  model of a hole with spin length a (m): E = eps (1 + u.w/c^2) and L = eps ((r x w)_z + a u.w/c)/c, so
    b = ((r x w)_z/c + a u.w/c^2) / (1 + u.w/c^2)
  (a = 0: the non-rotating impactParameter, but signed - positive anticlockwise)
  """
  uw = (u[0]*w[0] + u[1]*w[1])/C**2
  return ((pos[0]*w[1] - pos[1]*w[0])/C + a*uw)/(1 + uw)
