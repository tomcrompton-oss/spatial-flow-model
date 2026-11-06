"""
SpecialFlowCalculator's second-order step (order=2) against its first-order step (order=1, the original)

1. Mercury's orbit at 1/10 scale for 12 days (compareSingleBodyOrbits, the flow-calculator to-do): how much the
   periapsis and apoapsis grow each orbit, and the precession measured at each, for black and white bodies over
   a range of dt - at small dt the two should agree, and the second-order one should hold steady at large dt
2. the close orbit (closeOrbits: Mercury at 1/100,000 scale, ~3 degrees of precession an orbit): precession
   against the GR value for a range of steps per orbit
3. light sent straight out from 4 Schwarzschild radii of a 4e6 MS black hole to 1.025 AU (as in light_echo.py):
   flight time against the exact value

writes logs/compareSecondOrder/compareSecondOrder_<datetime>.log

run: python3 studies/compare_second_order.py      (about 10 minutes)
"""
import math
import time
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, SpecialFlowCalculator
from engine.logger import Log
from engine.constants import *
from engine.exact import rayTime, grPrecession

CALCS = [('first order', lambda bodies: SpecialFlowCalculator(bodies, order=1)),
         ('second order', lambda bodies: SpecialFlowCalculator(bodies, order=2))]
PERIHELION = 46000000000.0   #Mercury's


def apsis(ts, rs, ps):
  """time, distance and position of an extreme of r from three samples round it (a parabola through them)"""
  (t0, t1, t2), (r0, r1, r2) = ts, rs
  den = r0 - 2*r1 + r2
  f = 0.5*(r0 - r2)/den if den != 0 else 0.0   #steps from the middle sample, -1 to 1
  f = max(-1.0, min(1.0, f))
  r = r1 - 0.25*(r0 - r2)*f
  #position on the parabola through the three points
  p = ps[1] + 0.5*f*(ps[2] - ps[0]) + 0.5*f*f*(ps[0] - 2*ps[1] + ps[2])
  return t1 + f*(t2 - t1), r, p


def orbit(calc, r, v, dt, duration):
  """
  run an orbit from (0, r) moving +x at v; returns each whole orbit's periapsis and apoapsis (distance, angle),
  the wall time and the final position. orbits are counted at crossings of +y, as Calculator.orbitalSim does
  """
  p = Particle()
  p.pos = np.array([0.0, r])
  calc.initPV(p, np.array([v, 0.0]))
  steps = int(round(duration/dt))
  last = [(0.0, np.linalg.norm(p.pos), p.pos.copy())]   #the last three samples
  peris, apos, crossings = [], [], 0
  current = {'peri': None, 'apo': None}
  t0 = time.time()
  for n in range(1, steps + 1):
    old = p.pos.copy()
    calc.move(p, dt)
    last.append((n*dt, np.linalg.norm(p.pos), p.pos.copy()))
    if len(last) > 3:
      last.pop(0)
    if len(last) == 3:
      (_, a, _), (_, b, _), (_, c, _) = last
      if b < a and b <= c:
        current['peri'] = apsis([x[0] for x in last], [x[1] for x in last], [x[2] for x in last])
      if b > a and b >= c:
        current['apo'] = apsis([x[0] for x in last], [x[1] for x in last], [x[2] for x in last])
    if old[1] < 0 and p.pos[1] >= 0:
      crossings += 1
      if crossings > 1 and current['peri'] and current['apo']:   #the first crossing ends the warmup part orbit
        for store, key in ((peris, 'peri'), (apos, 'apo')):
          _, dist, pos = current[key]
          store.append((dist, math.atan2(pos[1], pos[0])))
      current = {'peri': None, 'apo': None}
  return peris, apos, time.time() - t0, p.pos.copy(), p.pt


def precession(points):
  """
  mean change of the apsis angle per orbit (rad), counted the way the orbit goes: these orbits start at (0, r)
  moving +x, so clockwise, and a forward (GR-like) precession turns the apsides clockwise too
  """
  angles = np.unwrap([a for _, a in points])
  return -float(np.mean(np.diff(angles))) if len(angles) > 1 else float('nan')


def growth(points):
  """mean change of the apsis distance per orbit (m)"""
  d = [x for x, _ in points]
  return float(np.mean(np.diff(d))) if len(d) > 1 else float('nan')


def mercuryTenth(log):
  r, v = MERCURY_MAX/10, MERCURY_SPEED_AT_MAX*math.sqrt(10)
  a, e = (MERCURY_MAX + PERIHELION)/20, (MERCURY_MAX - PERIHELION)/(MERCURY_MAX + PERIHELION)
  gr = grPrecession(a, e)
  log.print('1. Mercury at 1/10 scale, 12 days (about 4 orbits); GR precession %.4e rad/orbit' % gr)
  log.print('   growth: change per orbit of the periapsis / apoapsis distance; precession: change per orbit of its angle')
  log.print()
  log.print('  %-6s %-13s %7s %9s %14s %14s %14s %14s %12s' % ('body', 'calculator', 'dt (s)', 'time (s)', 'peri growth km',
            'apo growth km', 'peri prec rad', 'apo prec rad', 'end vs ref km'))
  runs = {'first order': [10, 5, 2.5, 1, 0.5, 0.25], 'second order': [200, 100, 50, 20, 10, 5, 2, 1, 0.5]}
  for black in (True, False):
    results = {}
    for name, cls in CALCS:
      for dt in runs[name]:
        peris, apos, wall, end, pt = orbit(cls([Body(MS, black=black)]), r, v, dt, 12*DAY)
        results[(name, dt)] = (peris, apos, wall, end)
    ref = results[('second order', 0.5)][3]
    for name, _ in CALCS:
      for dt in runs[name]:
        peris, apos, wall, end = results[(name, dt)]
        log.print('  %-6s %-13s %7g %9.1f %14.3f %14.3f %14.4e %14.4e %12.3f' % ('black' if black else 'white', name, dt, wall,
                  growth(peris)/1000, growth(apos)/1000, precession(peris), precession(apos), np.linalg.norm(end - ref)/1000))
    log.print()
  return gr


def closeOrbit(log):
  scale = 1e5
  r, v = MERCURY_MAX/scale, MERCURY_SPEED_AT_MAX*math.sqrt(scale)
  a = (MERCURY_MAX + PERIHELION)/2/scale
  e = (MERCURY_MAX - PERIHELION)/(MERCURY_MAX + PERIHELION)
  period = 2*math.pi*math.sqrt(a**3/(G*MS))
  gr = grPrecession(a, e)
  log.print('2. close orbit (Mercury at 1/100,000 scale, a = %.4g m), 6 orbits; GR precession %.5f rad/orbit' % (a, gr))
  log.print()
  log.print('  %-13s %10s %9s %14s %14s %10s %10s %14s' % ('calculator', 'steps/orbit', 'time (s)', 'peri prec rad', 'apo prec rad',
            'peri / GR', 'apo / GR', 'apo growth m'))
  for name, cls in CALCS:
    for perOrbit in (500, 1000, 2000, 5000, 20000, 50000):
      peris, apos, wall, end, pt = orbit(cls([Body(MS)]), r, v, period/perOrbit, 6.9*period)
      pp, pa = precession(peris), precession(apos)
      log.print('  %-13s %10d %9.1f %14.6f %14.6f %10.4f %10.4f %14.3f' % (name, perOrbit, wall, pp, pa, pp/gr, pa/gr, growth(apos)))
  log.print()


def lightRay(log):
  mass = 4000000*MS
  rs = 2*G*mass/C**2
  r0, r1 = 4*rs, 1.025*AU
  exact = rayTime(rs, r0, r1)
  log.print('3. light sent straight out from 4 rs of a 4e6 MS black hole to 1.025 AU; exact flight time %.4f s' % exact)
  log.print()
  log.print('  %-13s %7s %9s %14s %12s %12s' % ('calculator', 'dt (s)', 'time (s)', 'flight (s)', 'error (s)', 'error %'))
  for name, cls in CALCS:
    for dt in (5, 1, 0.1, 0.01):
      calc = cls([Body(mass)])
      p = Particle()
      p.pos = np.array([0.0, r0])
      calc.initPW(p, np.array([0.0, C]))
      t0 = time.time()
      n = 0
      prev = p.pos[1]
      while p.pos[1] < r1:
        prev = p.pos[1]
        calc.move(p, dt)
        n += 1
      flight = (n - 1)*dt + dt*(r1 - prev)/(p.pos[1] - prev)   #interpolated across the last step
      log.print('  %-13s %7g %9.2f %14.4f %12.4f %12.6f' % (name, dt, time.time() - t0, flight, flight - exact, 100*(flight - exact)/exact))
  log.print()


if __name__ == '__main__':
  log = Log('compareSecondOrder', True, False)
  log.print('SpecialFlowCalculator: second-order step (order=2) against the first-order step (order=1)')
  log.print()
  mercuryTenth(log)
  closeOrbit(log)
  lightRay(log)
