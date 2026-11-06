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
