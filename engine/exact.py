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
    alpha = 2 * integral from 0 to u0 of du / sqrt(1/b^2 - u^2 + rs u^3)  -  pi
  where u0 = 1/r0 at the closest approach, the smallest root of 1/b^2 - u^2 + rs u^3 = 0
  (series: 4GM/c^2 b + (15 pi/4)(GM/c^2 b)^2 + ...)
  """
  rs = schwarzschildRadius(mass)
  f = lambda u: 1/b**2 - u*u + rs*u**3
  u0 = 1/b
  for _ in range(100):   #Newton's method from 1/b, the flat-space closest approach
    u0 -= f(u0)/(-2*u0 + 3*rs*u0*u0)
  #u = u0 (1 - s^2): du = -2 u0 s ds, and f ~ s^2 near s = 0, so the integrand is smooth
  integral = _gauss(lambda s: 2*u0*s/math.sqrt(f(u0*(1 - s*s))), 0.0, 1.0)
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
