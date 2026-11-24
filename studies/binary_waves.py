"""
a binary's own gravitational waves, carried through a far-off plane by the flow model (engine/radiation.py): the first
step to bodies that radiate. the binary moves by Newton plus its waves' radiation reaction (Burke-Thorne), and its
waves reach a plane on its axis as the flow model's wave flow, u = (1/2) (h+' X + hx' Y, hx' X - h+' Y), with the
strain from the quadrupole formula at the retarded time. GR's quadrupole physics is put in, not derived (the flow
still has no wave equation); the checks say whether it is put in right, and whether flowing space then carries the
waves as GR does:

  source    two neutron stars (1.4 solar masses each):
            - circular, from a = 200 km to 60 km: a(t) against Peters' a^4 = a0^4 - (256/5) G^3 m1 m2 M t/c^5
            - eccentric, e = 0.6 from a = 300 km, 2 s: a(t) and e(t) against Peters' orbit-averaged equations
            - the orbit's energy lost against the quadrupole formula's power, integrated
  wave      on the axis 40 Mpc away, from the circular inspiral: the amplitude against 4 G^2 m1 m2/(c^4 a D), the
            frequency against twice the orbit's and against GR's chirp, f = (1/8 pi) (5/tau)^(3/8) (G Mc/c^3)^(-5/8)
            (tau the time to coalescence, Mc the chirp mass)
  detector  in the plane, the wave scaled up to h = 1e-6 (as studies/grav_wave.py checks a given wave), over the last
            0.1 s as the chirp sweeps up: free particles keep their TT coordinates, and light round trips to free
            mirrors take GR's time, 2 L_TT/c + (1/2) integral of h_ee dt

viewer: the binary spiralling in from 150 km, and beside it (though in truth far away along its axis) a ring of 24
free particles in its waves, scaled so the strain reaches 0.3 at the end: the ring's stretching grows and quickens
- the chirp. (binaryWaves.full.json)

writes logs/binaryWaves/binaryWaves_<datetime>/: checks.log; csvs of the two bodies' paths and the ring's particles;
the viewer files

run: python3 studies/binary_waves.py [--checks | --viewer]      (both by default; a few minutes)
"""
import csv
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import SpecialFlowCalculator, Particle
from engine.radiation import Binary, BinaryWave, peters
from engine.constants import *
from engine.logger import LOG_DIR
from grav_wave import roundTrip, strainMatrix
from two_body_escapes import writeViewerFiles

M1 = M2 = 1.4*MS
MPC = 3.0857e22
DISTANCE = 40*MPC
SMALL = 1e-6                  #the detector checks' strain
CHIRP = (M1*M2)**0.6/(M1 + M2)**0.2


def coalescence(a0):
  """Peters' time from a circular orbit of a0 to a = 0"""
  return 5*a0**4*C**5/(256*G**3*M1*M2*(M1 + M2))


def sourceChecks(lines):
  lines.append('SOURCE: %g + %g solar masses, Newton plus the quadrupole radiation reaction (Burke-Thorne)' % (M1/MS, M2/MS))
  out = {}
  #circular: Peters' a(t)
  a0, aEnd = 2e5, 6e4
  tc = coalescence(a0)
  tEnd = tc*(1 - (aEnd/a0)**4)
  b = Binary(M1, M2, a0, 0.0).run(tEnd, 1000)
  k = 256/5*G**3*M1*M2*(M1 + M2)/C**5
  lines.append('')
  lines.append('circular, a0 = %g km: Peters coalescence in %.4f s; run to a = %g km (%.4f s, %d steps)'
               % (a0/1e3, tc, aEnd/1e3, tEnd, len(b.times)))
  lines.append('  %8s %12s %12s %14s %10s' % ('t (s)', 'a (km)', 'Peters (km)', 'error/(shrink)', 'e'))
  worst = 0.0
  for f in (0.2, 0.4, 0.6, 0.8, 0.9, 0.97, 1.0):
    t = f*tEnd
    s = b.state(t)
    a, want = b.semiMajorAxis(s), (a0**4 - k*t)**0.25
    err = (a - want)/(a0 - want)
    worst = max(worst, abs(err))
    lines.append('  %8.4f %12.5f %12.5f %14.2e %10.1e' % (t, a/1e3, want/1e3, err, b.eccentricity(s)))
  out['circular'] = worst
  #energy: lost against radiated
  ts = np.linspace(0, tEnd, 4001)
  L = [b.luminosity(t) for t in ts]
  radiated = (ts[1] - ts[0])/3*(L[0] + L[-1] + 4*sum(L[1:-1:2]) + 2*sum(L[2:-1:2]))
  lost = b.energy(b.states[0]) - b.energy(b.state(tEnd))
  out['energy'] = abs(lost/radiated - 1)
  lines.append('  energy: the orbit lost %.6e J, the quadrupole formula radiated %.6e J: ratio - 1 = %.1e'
               % (lost, radiated, lost/radiated - 1))
  #eccentric: Peters' a(t), e(t), orbit-averaged
  a0, e0, T = 3e5, 0.6, 2.0
  b = Binary(M1, M2, a0, e0).run(T, 4000)
  lines.append('')
  lines.append('eccentric, a0 = %g km, e0 = %g, %g s (%d steps); errors as fractions of the change since t = 0' % (a0/1e3, e0, T, len(b.times)))
  lines.append('  %8s %12s %12s %10s %10s %10s %10s' % ('t (s)', 'a (km)', 'Peters', 'error', 'e', 'Peters', 'error'))
  #Peters' equations by RK4; the model's osculating a and e are compared at periastron, where the orbit is closest to
  #its average (the radiation reaction's kick each pass makes them wobble within an orbit)
  def petersAt(t, n=4000):
    a, e = a0, e0
    h = t/n
    for _ in range(n):
      k1 = peters(a, e, M1, M2)
      k2 = peters(a + h/2*k1[0], e + h/2*k1[1], M1, M2)
      k3 = peters(a + h/2*k2[0], e + h/2*k2[1], M1, M2)
      k4 = peters(a + h*k3[0], e + h*k3[1], M1, M2)
      a += h/6*(k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
      e += h/6*(k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
    return a, e
  r = [math.hypot(*s[:2]) for s in b.states]
  peri = [i for i in range(1, len(r) - 1) if r[i] < r[i - 1] and r[i] <= r[i + 1]]
  wa = we = 0.0
  for i in peri[len(peri)//4 - 1::len(peri)//4]:
    t, s = b.times[i], b.states[i]
    a, e = b.semiMajorAxis(s), b.eccentricity(s)
    pa, pe = petersAt(t)
    ea, ee = (a - pa)/(a0 - pa), (e - pe)/(e0 - pe)
    wa, we = max(wa, abs(ea)), max(we, abs(ee))
    lines.append('  %8.4f %12.5f %12.5f %10.1e %10.6f %10.6f %10.1e' % (t, a/1e3, pa/1e3, ea, e, pe, ee))
  out['eccentric'] = max(wa, we)
  return out


def waveChecks(lines):
  a0, aEnd = 2e5, 6e4
  tc = coalescence(a0)
  tEnd = tc*(1 - (aEnd/a0)**4)
  b = Binary(M1, M2, a0, 0.0).run(tEnd, 1000)
  wave = BinaryWave(b, DISTANCE, delay=0.0)
  lines.append('')
  lines.append('WAVE on the axis at %g Mpc (the plane\'s clock counted from when the waves left)' % (DISTANCE/MPC))
  lines.append('  %8s %12s %12s %9s %10s %10s %10s %9s' % ('t (s)', 'h', '4G2m1m2/c4aD', 'error', 'f (Hz)', '2 f_orbit', 'GR chirp', 'error'))
  k = 256/5*G**3*M1*M2*(M1 + M2)/C**5
  wa = wf = 0.0
  for f in (0.2, 0.5, 0.8, 0.95, 0.99):
    t = f*tEnd
    hp, hx = wave.strain(t)
    rp, rx = wave.rate(t)
    h = math.hypot(hp, hx)
    s = b.state(t)
    a = b.semiMajorAxis(s)
    want = 4*G**2*M1*M2/(C**4*a*DISTANCE)
    fw = (hp*rx - hx*rp)/(h*h)/(2*math.pi)          #the rate the polarization pattern turns: d(atan2(hx, h+))/dt
    forbit = math.sqrt(b.GM/a**3)/(2*math.pi)
    chirp = (5/(tc - t))**0.375*(G*CHIRP/C**3)**-0.625/(8*math.pi)
    ea, ef = h/want - 1, fw/chirp - 1
    wa, wf = max(wa, abs(ea)), max(wf, abs(ef))
    lines.append('  %8.4f %12.4e %12.4e %9.1e %10.3f %10.3f %10.3f %9.1e' % (t, h, want, ea, fw, 2*forbit, chirp, ef))
  return {'amplitude': wa, 'frequency': wf}, b, tEnd


def detectorChecks(lines, b, tEnd):
  """free particles and light in the plane, the wave scaled to h = SMALL, over the last 0.1 s"""
  peak = math.hypot(*BinaryWave(b, DISTANCE, delay=0.0).strain(tEnd))
  #the plane's clock starts at 0 when the waves left at tEnd - 0.1 s, so its times are small and keep their precision
  #(at t = 5.8 s a double's rounding over a light trip's thousands of steps is 1e-12 s, the size of the effect)
  offset = tEnd - 0.1
  wave = BinaryWave(b, DISTANCE, delay=-offset, scale=SMALL/peak)
  calc = SpecialFlowCalculator([], 2, wave=wave)
  t0, tEnd = 0.0, 0.1
  fEnd = 2*math.sqrt(b.GM/b.semiMajorAxis(b.state(offset + tEnd))**3)/(2*math.pi)
  lines.append('')
  lines.append('DETECTOR in the plane: the wave scaled to h = %g at the end; the last 0.1 s of the run (the plane\'s clock'
               ' from 0 there), as f sweeps to %.0f Hz' % (SMALL, fEnd))
  dt = 1/fEnd/2000
  worst = 0.0
  for X0 in (np.array([1e6, 4e5]), np.array([-3e5, 7e5]), np.array([2e4, -9e5])):
    p = Particle()
    p.t = t0
    tt = X0 - strainMatrix(wave, t0) @ X0/2
    p.pos = X0.copy()
    calc.initPW(p, np.array([0.0, 0.0]))
    while p.t < tEnd - dt:
      calc.move(p, dt)
      want = tt + strainMatrix(wave, p.t) @ tt/2
      worst = max(worst, np.linalg.norm(p.pos - want)/(SMALL*np.linalg.norm(X0)))
  lines.append('  free particles keep their TT coordinates: worst error %.1e of h |X0|' % worst)
  lam = C/fEnd
  lines.append('  light round trips, sent at t = %.4f s; extra time over 2L/c, and the error / (h L/c)' % (tEnd - 0.02))
  lines.append('  %10s %8s %16s %16s %10s' % ('L/lambda', 'arm', 'flow model (s)', 'GR (s)', 'error'))
  wl = 0.0
  ts = tEnd - 0.02
  for fraction in (0.05, 0.25, 1.0):
    L = fraction*lam
    for name, arm in (('x', (1, 0)), ('y', (0, 1)), ('diagonal', (1, 1))):
      e = np.array(arm, dtype=float)/np.linalg.norm(arm)
      along = lambda hp, hx: hp*(e[0]**2 - e[1]**2) + 2*hx*e[0]*e[1]
      T = roundTrip(calc, L, e, ts)
      want = 2*L*(1 - along(*wave.strain(ts))/2)/C + along(*wave.integral(ts, ts + T))/2
      err = (T - want)/(SMALL*L/C)
      wl = max(wl, abs(err))
      lines.append('  %10g %8s %16.6e %16.6e %10.1e' % (fraction, name, T - 2*L/C, want - 2*L/C, err))
  return {'free': worst, 'light': wl}


def viewer(folder):
  """the binary spiralling in from 150 km, and a ring of free particles in its waves"""
  a0, aEnd = 1.5e5, 4e4
  tEnd = coalescence(a0)*(1 - (aEnd/a0)**4)
  b = Binary(M1, M2, a0, 0.0).run(tEnd, 1000)
  made = []
  for n, (sign, mass) in enumerate(((1, M2), (-1, M1))):
    path = os.path.join(folder, 'body%d.csv' % (n + 1))
    with open(path, 'w', newline='') as f:
      out = csv.writer(f)
      out.writerow(['t', 'pos_x', 'pos_y', 'v_x', 'v_y'])
      t = 0.0
      while t <= tEnd:
        s = b.state(t)
        k = sign*mass/b.M
        out.writerow([t, k*s[0], k*s[1], k*s[2], k*s[3]])
        t += 2*math.pi*math.hypot(*s[:2])/math.hypot(*s[2:])/48    #48 rows an orbit
    with open(path[:-4] + '.log', 'w') as f:
      f.write('%s\nbody %d: %.2f solar masses\n' % (b.describe(), n + 1, mass/MS))
    made.append((path, '#2a78d6' if n == 0 else '#eb6834', 'solid'))
  #the ring
  centre, radius, shown, particles = np.array([4.5e5, 0.0]), 1.2e5, 0.3, 24
  peak = math.hypot(*BinaryWave(b, DISTANCE, delay=0.0).strain(tEnd))
  wave = BinaryWave(b, DISTANCE, centre=centre, delay=0.0, scale=shown/peak)
  calc = SpecialFlowCalculator([], 2, wave=wave)
  ps = []
  for n in range(particles):
    a = 2*math.pi*n/particles
    p = Particle()
    round_ = radius*np.array([math.cos(a), math.sin(a)])
    p.pos = centre + round_ + strainMatrix(wave, 0.0) @ round_/2
    calc.initPW(p, np.array([0.0, 0.0]))
    ps.append(p)
  rows = [[] for _ in ps]
  t, step = 0.0, 0
  while t < tEnd:
    s = b.state(t)
    fgw = 2*math.sqrt(b.GM/b.semiMajorAxis(s)**3)/(2*math.pi)
    dt = min(1/fgw/200, tEnd - t)
    if step % 10 == 0:
      for p, r in zip(ps, rows):
        r.append([p.t, p.pos[0], p.pos[1], p.v[0], p.v[1], p.u[0], p.u[1]])
    for p in ps:
      calc.move(p, dt)
    t = ps[0].t
    step += 1
  path = os.path.join(folder, 'ring.csv')
  with open(path, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'pos_x', 'pos_y', 'v_x', 'v_y', 'u_x', 'u_y'])
    for r in rows:
      out.writerows(r)
      out.writerow([''] * 7)
  with open(path[:-4] + '.log', 'w') as f:
    f.write('%s\n%d free particles on a ring of %g m round (%g, %g) m; strain scaled to %g at the end\n'
            % (wave.describe(), particles, radius, *centre, shown))
  made.append((path, '#1baf7a', 'dotted'))
  writeViewerFiles(folder, 'binaryWaves', made)
  print('viewer: %d steps for the ring, to t = %.4f s' % (step, tEnd), flush=True)


def main():
  folder = os.path.join(LOG_DIR, 'binaryWaves', 'binaryWaves_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  args = sys.argv[1:]
  if '--viewer' not in args or '--checks' in args:
    lines = ["a binary's gravitational waves: its inspiral, its waves and their passage through the flow model's space,"
             ' against GR at quadrupole order', '']
    source = sourceChecks(lines)
    shown = len(lines)
    print('\n'.join(lines), flush=True)
    wave, b, tEnd = waveChecks(lines)
    detector = detectorChecks(lines, b, tEnd)
    lines += ['', 'worst: inspiral %.1e (circular), %.1e (eccentric) of the change; energy %.1e; amplitude %.1e,'
              ' frequency %.1e; free particles %.1e of h X0, light %.1e of h L/c'
              % (source['circular'], source['eccentric'], source['energy'], wave['amplitude'], wave['frequency'],
                 detector['free'], detector['light'])]
    with open(os.path.join(folder, 'checks.log'), 'w') as f:
      f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines[shown:]), flush=True)
  if '--checks' not in args or '--viewer' in args:
    viewer(folder)
  print('written to', folder)
  return folder


if __name__ == '__main__':
  main()
