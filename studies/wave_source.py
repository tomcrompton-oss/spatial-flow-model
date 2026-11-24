"""
a binary's waves solved from their equation (engine/wave_source.py): the TT part of space, in the model's free-fall
slicing (N = 1), obeys (1/c^2) h'' - laplacian h = (16 pi G/c^4) tau^TT - the flow drops out - and its retarded
solution, h_ij = (4G/c^4) integral of tau_ij(t - |x - x'|/c)/|x - x'|, is worked out here directly, with the source
at Newton's order (the bodies' momentum flux and the cross term of the field's stress). checks:

  source     the source's integral over all space against (1/2) Q'' (conservation), at three grid sizes; matter
             alone, which misses the field's half
  near->far  h+ and hx from the retarded integral, on the binary's axis and in its plane (edge on), from a third of a
             wavelength out to 1000 wavelengths, against the quadrupole formula h^TT = (2G/c^4 D) Q''^TT at t - D/c
             (engine/radiation.py's BinaryWave). h_ij of a compact source is already 1/D just outside it, so the
             error is the same at every distance: the floor below. (the near zone's own terms are in the full,
             non-local TT projection and the metric's other parts, which this algebraic projection doesn't test)
  floor      that floor, far out, for orbital speeds v/c = 0.01, 0.03 and 0.1, equal and unequal masses: the
             quadrupole formula is the first term in v/c - unequal masses seen edge on add the octupole, at v/c
             of it; equal masses, or on the axis, (v/c)^2. (the field's grid has its foci where each body was when
             its light left: laid at one retarded time for both, equal masses edge on had a numerical floor of
             3e-4 at 0.01c)
  matter     the bodies' momentum flux alone, far out: half the wave of a circular orbit

writes logs/waveSource/waveSource_<datetime>/checks.log

run: python3 studies/wave_source.py        (a minute or two)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.wave_source import CircularBinary, SpheroidalGrid, sourceIntegral, retarded
from engine.logger import LOG_DIR
from engine.constants import *

M1 = 1.4*MS
GRIDS = [(16, 12, 8), (32, 24, 16), (64, 48, 24)]
TIMES = 8                    #moments over an orbit's half (the waves' period) at which each h is compared


def separation(speed, ratio):
  """the separation giving a relative orbital speed v/c = speed, masses M1 and ratio M1"""
  return G*M1*(1 + ratio)/(speed*C)**2


def tt(h, n):
  """(h+, hx) of h_ij for a wave travelling along the unit vector n: e1, e2 across it (e1 in the (x, y) plane)"""
  n = np.asarray(n, dtype=float)
  e1 = np.cross([0.0, 0.0, 1.0], n)
  if np.linalg.norm(e1) < 1e-12:
    e1 = np.array([1.0, 0.0, 0.0])
  e1 /= np.linalg.norm(e1)
  e2 = np.cross(n, e1)
  return 0.5*(e1 @ h @ e1 - e2 @ h @ e2), e1 @ h @ e2


def compare(b, n, D, grid, parts=False):
  """the worst error of the retarded (h+, hx), over a wave period, against the quadrupole formula, as a fraction of its
  amplitude; with parts, also matter alone's amplitude over the formula's"""
  lam = math.pi*C/b.omega                             #the waves' wavelength (twice the orbit's frequency)
  observer = D*np.asarray(n, dtype=float)
  worst, amp, ampMatter = 0.0, 0.0, 0.0
  rows = []
  for k in range(TIMES):
    t = D/C + k*math.pi/b.omega/TIMES
    matter, field = retarded(b, observer, t, grid)
    got = np.array(tt(matter + field, n))
    want = np.array(tt(2*G/(C**4*D)*b.quadrupoleRate2(t - D/C), n))
    rows.append((got, want, np.array(tt(matter, n))))
    amp = max(amp, np.linalg.norm(want))
  for got, want, m in rows:
    worst = max(worst, np.linalg.norm(got - want)/amp)
    ampMatter = max(ampMatter, np.linalg.norm(m))
  return (worst, ampMatter/amp) if parts else worst


def main():
  folder = os.path.join(LOG_DIR, 'waveSource', 'waveSource_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = ["a binary's waves from their equation: the retarded solution of the wave equation for space's TT part in the"
           " model's slicing, with Newton's source, against the quadrupole formula", '']
  #the source's integral
  lines.append('SOURCE: its integral over all space against (1/2) Q\'\', error / |Q\'\'/2|, worst of 5 moments')
  lines.append('  %-22s %-14s %12s %12s %12s %14s' % ('binary', '', *['grid %dx%dx%d' % g for g in GRIDS], 'matter alone'))
  for ratio in (1.0, 0.3):
    b = CircularBinary(M1, ratio*M1, separation(0.03, ratio))
    errs, alone = [0.0]*len(GRIDS), 0.0
    for t in np.linspace(0, math.pi/b.omega, 5):
      want = b.quadrupoleRate2(t)/2
      scale = np.max(np.abs(want))
      for i, g in enumerate(GRIDS):
        m, f = sourceIntegral(b, t, SpheroidalGrid(*g))
        errs[i] = max(errs[i], np.max(np.abs(m + f - want))/scale)
      alone = max(alone, np.max(np.abs(m - want))/scale)
    lines.append('  %-22s %-14s %12.1e %12.1e %12.1e %14.2f' % ('m2/m1 = %g, v = 0.03c' % ratio, '', *errs, alone))
  lines.append('')
  grid = SpheroidalGrid(*GRIDS[-1])
  #near zone to wave zone
  b = CircularBinary(M1, M1, separation(0.01, 1.0))
  lam = math.pi*C/b.omega
  lines.append('NEAR TO FAR: equal masses, v = 0.01c (wavelength %.4g km, separation %.4g km); error of (h+, hx) /'
               ' amplitude, worst over a wave period' % (lam/1e3, b.d/1e3))
  lines.append('  %-10s %14s %14s' % ('D/lambda', 'on the axis', 'edge on'))
  for f in (0.3, 1, 3, 10, 30, 100, 1000):
    lines.append('  %-10g %14.2e %14.2e' % (f, compare(b, (0, 0, 1), f*lam, grid), compare(b, (1, 0, 0), f*lam, grid)))
  lines.append('')
  #the floor, far out
  lines.append('FLOOR at 1000 wavelengths: error / amplitude by orbital speed')
  lines.append('  %-8s %16s %16s %16s %16s' % ('v/c', 'equal, axis', 'equal, edge on', 'm2 = 0.3 m1, axis', '0.3, edge on'))
  for speed in (0.01, 0.03, 0.1):
    row = []
    for ratio in (1.0, 0.3):
      b = CircularBinary(M1, ratio*M1, separation(speed, ratio))
      lam = math.pi*C/b.omega
      for n in ((0, 0, 1), (1, 0, 0)):
        row.append(compare(b, n, 1000*lam, grid))
    lines.append('  %-8g %16.2e %16.2e %16.2e %16.2e' % (speed, *row))
  lines.append('')
  b = CircularBinary(M1, M1, separation(0.01, 1.0))
  lam = math.pi*C/b.omega
  err, matter = compare(b, (0, 0, 1), 1000*lam, grid, parts=True)
  lines.append("MATTER ALONE, on the axis at 1000 wavelengths: the bodies' momentum flux gives %.4f of the wave; the"
               " field's stress the rest" % matter)
  with open(os.path.join(folder, 'checks.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
