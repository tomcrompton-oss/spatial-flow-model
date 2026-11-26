"""
a hunch, not for the docs: round a black hole, how much space does the curved-space model's stretching add, and how
fast? (Curved Space, docs/part2/curved-space.md: space stretched across the flow by u^2/c^2 = rs/r, unchanged along it)

for one hole, at r:
  the stretch     each of the two directions across the inflow is longer by sqrt(1 + rs/r), so a small volume is
                  (1 + rs/r) times the flat one: the extra space is a fraction rs/r of it (the same for every hole, at
                  the same r/rs)
  the rate        space flows in at u = c sqrt(rs/r); a parcel carried in is stretched more as it goes, so new space
                  appears in it at u . d/dr ln(1 + rs/r) = c (rs/r)^1.5 / (r (1 + rs/r)) per second, per unit of its
                  volume (against the flat inflow's convergence, (3/2)(c/r) sqrt(rs/r), which destroys space as it
                  falls in). it scales as c/rs, so as 1/M
  in all          the new space appearing per second between rs and r: 8 pi c rs^1.5 (sqrt r - sqrt rs) m^3/s

the model's stretch is first order in rs/r (first post-Newtonian), used here all the way to the horizon, where rs/r
is 1: a rough guide there, not a result. for one body this curved space is flat in other coordinates, so how much
"extra" space there is depends on what it is compared with - here, the flat space of the flow model's coordinates.

three holes: supermassive (4 million solar masses, Sagittarius A*), the Sun's mass, and microscopic (5e11 kg, about
the mass of a primordial black hole that would be evaporating by Hawking radiation now). for reference only, each
hole's Hawking temperature and power

writes logs/hawkingStretch/hawkingStretch_<datetime>/: stretch.csv (distance from the Schwarzschild radius, the
extra fraction, the rate per hole, the cumulative creation per hole) and summary.log

run: python3 studies/hawking_stretch.py
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.constants import *
from engine.exact import schwarzschildRadius
from engine.logger import LOG_DIR

HBAR = 1.054571817e-34
KB = 1.380649e-23
RHO_LAMBDA = 5.3e-10       #dark energy's density as measured (J/m^3): 0.69 of the critical density, Planck 2018
RHO_PLANCK = 4.6e113       #the vacuum energy if quantum fields count up to the Planck scale (J/m^3): c^7/(hbar G^2)
REGIONS = (1, 9)           #the new space counted from the horizon out to 2 rs, and to 10 rs (x = r/rs - 1)
HOLES = (('supermassive (4e6 solar masses)', 4e6*MS), ('the Sun\'s mass', MS), ('microscopic (5e11 kg)', 5e11))
X = np.logspace(-3, 3, 241)     #distance from the Schwarzschild radius, in Schwarzschild radii


def stretch(x):
  """the extra space, as a fraction of the flat volume, at r = rs (1 + x)"""
  return 1/(1 + x)

def rate(rs, x):
  """new space per second per unit volume from the stretching, at r = rs (1 + x) (1/s)"""
  r = rs*(1 + x)
  q = rs/r
  return C*q**1.5/(r*(1 + q))

def convergence(rs, x):
  """the flat inflow's own change of volume, div u (1/s, negative: space destroyed as it converges)"""
  r = rs*(1 + x)
  return -1.5*(C/r)*math.sqrt(rs/r)

def created(rs, x):
  """new space per second from the stretching, between rs and r (m^3/s)"""
  r = rs*(1 + x)
  return 8*math.pi*C*rs**1.5*(math.sqrt(r) - math.sqrt(rs))

def hawking(mass):
  """the Hawking temperature (K) and power (W)"""
  return HBAR*C**3/(8*math.pi*G*mass*KB), HBAR*C**6/(15360*math.pi*G**2*mass**2)


def invariantCheck():
  """
  is the new space real? the volume change of falling space, theta = (1/sqrt gamma) d(sqrt gamma u^r)/dr, is the same
  in any coordinates. with curved space (transverse stretch 1 + rs/rho, the flow slowed as u^2 = 2 Phi (1 - Phi/c^2))
  it is compared with the flat flow model's (Gullstrand-Painleve), -(3/2) c sqrt(rs) R^-1.5, at the same areal radius
  R = rho sqrt(1 + rs/rho): if they agree, the stretching only moves volume change between "stretch" and "convergence".
  and at the horizon: the stretch rate (first-order and slowed flow) against the flow's own gradient du/dr, which is
  the surface gravity over c exactly - Unruh's analogue-gravity Hawking temperature is hbar (du/dr)/(2 pi kB)
  """
  rs, h = 1.0, 1e-6
  u = lambda r: math.sqrt(rs/r)*(1 - rs/(4*r))
  g = lambda r: r*r*(1 + rs/r)
  out = ['is the new space real? the volume change of falling space with curved space, against the flat flow\'s at the'
         ' same areal radius (units of c/rs)']
  for rho in (100, 30, 10, 5, 3, 2):
    total = -(g(rho + h)*u(rho + h) - g(rho - h)*u(rho - h))/(2*h)/g(rho)
    conv = -((rho + h)**2*u(rho + h) - (rho - h)**2*u(rho - h))/(2*h)/rho**2
    R = rho*math.sqrt(1 + rs/rho)
    gp = -1.5*rs**0.5*R**-1.5
    out.append('  rho %5g rs (R %.4f rs): convergence %+.4e, stretch %+.4e, total %+.6e; flat flow %+.6e; ratio - 1 %+.1e'
               % (rho, R, conv, total - conv, total, gp, total/gp - 1))
  flat = lambda r: math.sqrt(rs/r)
  out += ['  at the horizon: the flow\'s gradient |du/dr| %.4f c/rs = surface gravity / c (exact); the stretch rate %.4f c/rs'
          ' with the first-order flow, %.4f with the slowed flow; the volume change of falling space %.4f c/rs'
          % (abs(flat(rs + h) - flat(rs - h))/(2*h), flat(rs)*(rs/rs**2)/2, u(rs)*(rs/rs**2)/2, -1.5)]
  return out


def main():
  folder = os.path.join(LOG_DIR, 'hawkingStretch', 'hawkingStretch_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = ['the curved-space model\'s stretching round a black hole (first order in rs/r, taken to the horizon)', '']
  for name, mass in HOLES:
    rs = schwarzschildRadius(mass)
    T, P = hawking(mass)
    lines += ['%s: %.4g kg, rs %.4g m, c/rs %.4g /s' % (name, mass, rs, C/rs),
              '  extra space: %.3g of the volume at the horizon, %.3g at 2 rs, %.3g at 10 rs' % (stretch(1e-9), stretch(1), stretch(9)),
              '  creation rate: %.4g /s at the horizon, %.4g /s at 2 rs, %.4g /s at 10 rs (the flat inflow\'s convergence at'
              ' the horizon %.4g /s)' % (rate(rs, 0), rate(rs, 1), rate(rs, 9), convergence(rs, 0)),
              '  new space from the horizon to 2 rs: %.4g m^3/s; to 10 rs: %.4g m^3/s' % (created(rs, 1), created(rs, 9)),
              '  (for reference: Hawking temperature %.4g K, power %.4g W)' % (T, P), '']
  #if each cubic metre of new space carries an energy density rho, the new space carries energy away at rho dV/dt:
  #against the Hawking power. dV/dt goes as rs^2 (M^2), the Hawking power as 1/M^2, so the rho that matches goes as 1/M^4
  lines += ['the energy of the new space at density rho, against the Hawking power: the rho that matches, and the'
            ' power at dark energy\'s measured %.2g J/m^3' % RHO_LAMBDA]
  for k, x in enumerate(REGIONS):
    lines.append('  new space counted from the horizon to %g rs:' % (1 + x))
    for name, mass in HOLES:
      rs = schwarzschildRadius(mass)
      T, P = hawking(mass)
      dV = created(rs, x)
      lines.append('    %-32s dV/dt %.4g m^3/s; matching rho %.4g J/m^3 (%.3g of dark energy\'s); at dark energy\'s'
                   ' density %.4g W, %.3g of the Hawking power' % (name, dV, P/dV, P/dV/RHO_LAMBDA, RHO_LAMBDA*dV,
                                                                    RHO_LAMBDA*dV/P))
    #the mass whose matching rho is dark energy's, and the Planck-scale vacuum energy's: rho_match = (P_sun/dV_sun)(MS/M)^4
    rsSun = schwarzschildRadius(MS)
    base = hawking(MS)[1]/created(rsSun, x)
    for label, rho in (('dark energy\'s measured density', RHO_LAMBDA), ('the Planck-scale vacuum energy', RHO_PLANCK)):
      m = MS*(base/rho)**0.25
      lines.append('    they match at %s for a hole of %.3g kg (rs %.3g m, Hawking temperature %.3g K, power %.3g W)'
                   % (label, m, schwarzschildRadius(m), hawking(m)[0], hawking(m)[1]))
  lines.append('')
  lines += invariantCheck() + ['']
  with open(os.path.join(folder, 'stretch.csv'), 'w') as f:
    f.write('x_rs,extra_fraction,' + ','.join('rate_%d,created_%d' % (k, k) for k in range(len(HOLES))) + '\n')
    for x in X:
      cols = [x, stretch(x)]
      for _, mass in HOLES:
        rs = schwarzschildRadius(mass)
        cols += [rate(rs, x), created(rs, x)]
      f.write(','.join('%.6g' % v for v in cols) + '\n')
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
