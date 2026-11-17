"""
test 1 of the split model (engine/split.py, 'static' light, 'lorentz' boosts): lunar laser ranging with the Moon's
own orbit. the Sun at rest, the Earth going round it on a circle, the Moon round the Earth (a test particle): the Moon
run in the model for two synodic months, and radar from a station on the Earth's surface (under the Moon) to the Moon
and back, every two hours, as a range at the station's clock - against GR's

GR's: the Moon by the Einstein-Infeld-Hoffmann equations (first post-Newtonian, harmonic coordinates; the Earth's
circle there of radius AU - GM_S/c^2, at the same angular speed), light's time by Shapiro's delay for each body, the
station's clock at 1 - U/c^2 - v^2/2c^2. the two run in different coordinates, so GR's Moon starts where a fit puts it:
its starting place and velocity, and a constant in the range, chosen to match the model's range best (as lunar laser
ranging fits the Moon's orbit). what is left is what the model predicts that GR doesn't

the model's step error goes as dt^2 (4 m in the range at 20 s steps), so its ranges are run at 10 s and 20 s steps
and extrapolated (Richardson: (4 R_10 - R_20)/3). control: the Earth alone, moving at 29.8 km/s in a straight line -
the model is then GR exactly, so what is left is the test's floor

the model's light is timed along the straight line, at its light speed (studies/split_bodies.py roundTrip, with the
ends moving; bending changes the time only to second order)

run: python3 studies/lunar_orbit.py      (prints, and writes logs/multiBody/lunarOrbit_<datetime>/: summary.log and a
     csv of each residual)
"""
import csv
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle
from engine.split import SplitFlowCalculator, Boost
from engine.logger import LOG_DIR
from engine.constants import *
from multi_body_pn import NODES, WEIGHTS

DMOON = 3.844e8
OMEGA = math.sqrt(G*MS/AU**3)         #the Earth's angular speed round the Sun
SYNODIC = 29.5306*DAY
SPAN = 2*SYNODIC
SAMPLE = 2*3600.0
START = (np.array([0.0, -DMOON]), np.array([1022.0, 0.0]))   #the Moon from the Earth at first: behind it on its
                                                            #orbit (the Earth at +x, going +y), going round anticlockwise


class Track:
  """a path stored at each step (t, x, v), read at any time between by cubic Hermite interpolation"""

  def __init__(self):
    self.t, self.x, self.v = [], [], []

  def add(self, t, x, v):
    self.t.append(t)
    self.x.append(np.array(x, dtype=float))
    self.v.append(np.array(v, dtype=float))

  def at(self, t):
    i = min(max(np.searchsorted(self.ts, t) - 1, 0), len(self.ts) - 2)
    t0, h = self.ts[i], self.ts[i + 1] - self.ts[i]
    s = (t - t0)/h
    x0, x1, v0, v1 = self.x[i], self.x[i + 1], self.v[i]*h, self.v[i + 1]*h
    return (2*s**3 - 3*s**2 + 1)*x0 + (s**3 - 2*s**2 + s)*v0 + (-2*s**3 + 3*s**2)*x1 + (s**3 - s**2)*v1

  def done(self):
    self.ts = np.array(self.t)
    return self


#the bodies

class Setup:
  """the Earth's path, the Sun at the origin or none: in the model's coordinates or GR's"""

  def __init__(self, sun, harmonic):
    self.sun = sun
    self.radius = AU - (G*MS/C**2 if harmonic else 0.0)
    self.V = np.array([0.0, 29.8e3])

  def earth(self, t):
    if self.sun:
      a = OMEGA*t
      return self.radius*np.array([math.cos(a), math.sin(a)])
    return np.array([AU, 0.0]) + self.V*t

  def earthV(self, t):
    if self.sun:
      a = OMEGA*t
      return self.radius*OMEGA*np.array([-math.sin(a), math.cos(a)])
    return self.V

  def earthA(self, t):
    return -OMEGA**2*self.earth(t) if self.sun else np.array([0.0, 0.0])

  def bodies(self):
    earth = Body(ME, AU, 0.0, circling=OMEGA) if self.sun else Body(ME, AU, 0.0, velocity=self.V)
    return ([Body(MS)] if self.sun else []) + [earth]


#the model

def modelRun(setup, dt):
  calc = SplitFlowCalculator(setup.bodies(), 'static', 'lorentz')
  f = Boost(setup.earthV(0.0), 0.0, setup.earth(0.0))
  p = Particle()
  p.pos = setup.earth(0.0) + START[0]
  calc.initPV(p, f.back(START[1]))
  track = Track()
  track.add(p.t, p.pos, p.v)
  while p.t < SPAN + DAY:
    calc.move(p, dt)
    track.add(p.t, p.pos, p.v)
  return calc, track.done()


def modelLeg(calc, a, b, t0, earthEnd, pieces=40):
  """light's time from a (at t0) to b along the straight line, at the model's light speed - the pieces closer
  together at the end by the Earth"""
  span = np.linalg.norm(b - a)
  n = (b - a)/span
  edges = np.concatenate([[0.0], np.geomspace(1e3, span, pieces)])
  total = 0.0
  for lo, hi in zip(edges[:-1], edges[1:]):
    for x, wt in zip(NODES, WEIGHTS):
      s = (lo + hi)/2 + (hi - lo)/2*x
      along = s if earthEnd == 'a' else span - s
      total += wt*(hi - lo)/2/calc.lightSpeed(a + along*n, n, t0 + along/C)
  return total


#GR

def grAccel(setup, t, x, v):
  """the Moon's acceleration by the EIH equations (first post-Newtonian, harmonic coordinates)"""
  bodies = [(G*ME, setup.earth(t), setup.earthV(t), setup.earthA(t))]
  if setup.sun:
    bodies.append((G*MS, np.zeros(2), np.zeros(2), np.zeros(2)))
  c2 = C*C
  pot = sum(gm/np.linalg.norm(x - xb) for gm, xb, _, _ in bodies)
  a = np.zeros(2)
  for gm, xb, vb, ab in bodies:
    others = sum(g2/np.linalg.norm(xb - x2) for g2, x2, _, _ in bodies if x2 is not xb)
    d = xb - x
    r = np.linalg.norm(d)
    nBA = d/r
    nAB = -nBA
    bracket = (1 - 4*pot/c2 - others/c2 + v @ v/c2 + 2*(vb @ vb)/c2 - 4*(v @ vb)/c2 - 1.5*(vb @ nAB)**2/c2
               + 0.5*(d @ ab)/c2)
    a += gm*nBA/r**2*bracket + gm/(c2*r*r)*(nAB @ (4*v - 3*vb))*(v - vb) + 3.5*gm*ab/(c2*r)
  return a


def grRun(setup, start, dt=120.0):
  """the Moon in GR from start = (place, velocity) relative to the Earth at t = 0, by fourth-order Runge-Kutta"""
  x = setup.earth(0.0) + start[0]
  v = setup.earthV(0.0) + start[1]
  t = 0.0
  track = Track()
  track.add(t, x, v)
  while t < SPAN + DAY:
    k1x, k1v = v, grAccel(setup, t, x, v)
    k2x, k2v = v + k1v*dt/2, grAccel(setup, t + dt/2, x + k1x*dt/2, v + k1v*dt/2)
    k3x, k3v = v + k2v*dt/2, grAccel(setup, t + dt/2, x + k2x*dt/2, v + k2v*dt/2)
    k4x, k4v = v + k3v*dt, grAccel(setup, t + dt, x + k3x*dt, v + k3v*dt)
    x = x + (k1x + 2*k2x + 2*k3x + k4x)*dt/6
    v = v + (k1v + 2*k2v + 2*k3v + k4v)*dt/6
    t += dt
    track.add(t, x, v)
  return track.done()


def grLeg(setup, a, b, t0, t1, earthEnd):
  """light's time from a to b by Shapiro's delay, each body where it is when light is at the end nearer it"""
  R = np.linalg.norm(b - a)
  delay = 0.0
  for gm, centre in [(G*ME, setup.earth(t0 if earthEnd == 'a' else t1))] + ([(G*MS, np.zeros(2))] if setup.sun else []):
    r1, r2 = np.linalg.norm(a - centre), np.linalg.norm(b - centre)
    delay += 2*gm/C**3*math.log((r1 + r2 + R)/(r1 + r2 - R))
  return R/C + delay


def grRate(setup, x, t):
  U = G*ME/REARTH + (G*MS/np.linalg.norm(x) if setup.sun else 0.0)
  v = setup.earthV(t)
  return 1 - U/C**2 - (v @ v)/(2*C*C)


#ranges

def station(setup, moon, t):
  e = setup.earth(t)
  m = moon.at(t)
  return e + REARTH*(m - e)/np.linalg.norm(m - e)


def ranges(setup, moon, times, leg, rate):
  """at each time: light from the station to the Moon and back; the round trip at the station's clock, as a range"""
  out = []
  for t0 in times:
    a = station(setup, moon, t0)
    t1 = t0 + np.linalg.norm(moon.at(t0) - a)/C
    for _ in range(4):
      t1 = t0 + leg(a, moon.at(t1), t0, t1, 'a')
    b = moon.at(t1)
    t2 = t1 + np.linalg.norm(station(setup, moon, t1) - b)/C
    for _ in range(4):
      t2 = t1 + leg(b, station(setup, moon, t2), t1, t2, 'b')
    out.append(C*(t2 - t0)*rate(a, t0)/2)
  return np.array(out)


def modelRanges(setup, calc, moon, times):
  leg = lambda a, b, t0, t1, end: modelLeg(calc, a, b, t0, end)
  rate = lambda x, t: calc.rate(x, setup.earthV(t), t)
  return ranges(setup, moon, times, leg, rate)


def grRanges(setup, start, times):
  moon = grRun(setup, start)
  leg = lambda a, b, t0, t1, end: grLeg(setup, a, b, t0, t1, end)
  return ranges(setup, moon, times, leg, lambda x, t: grRate(setup, x, t))


def fit(setup, target, times, iterations=6):
  """GR's starting place and velocity (and a constant), by Gauss-Newton, to match target best"""
  params = np.concatenate([START[0], START[1]])
  steps = np.array([1.0, 1.0, 1e-5, 1e-5])
  for _ in range(iterations):
    base = grRanges(setup, (params[:2], params[2:]), times)
    J = [np.ones_like(times)]
    for i in range(4):
      q = params.copy()
      q[i] += steps[i]
      J.append((grRanges(setup, (q[:2], q[2:]), times) - base)/steps[i])
    J = np.array(J).T
    resid = target - base
    delta = np.linalg.lstsq(J, resid, rcond=None)[0]
    params = params + delta[1:]
    if np.abs(delta[1:]/steps).max() < 1e-3:
      break
  base = grRanges(setup, (params[:2], params[2:]), times)
  resid = target - base
  return resid - resid.mean(), params


def describe(times, resid, setup):
  """the residual's size, and its parts at the Moon's synodic angle D: cos D, sin D, cos 2D, sin 2D"""
  D = 2*math.pi*times/SYNODIC
  A = np.array([np.ones_like(D), np.cos(D), np.sin(D), np.cos(2*D), np.sin(2*D)]).T
  coef = np.linalg.lstsq(A, resid, rcond=None)[0]
  return ('rms %.4f m, largest %.4f m; cos D %+.4f, sin D %+.4f, cos 2D %+.4f, sin 2D %+.4f m'
          % (np.sqrt(np.mean(resid**2)), np.abs(resid).max(), *coef[1:]))


def main():
  folder = os.path.join(LOG_DIR, 'multiBody', 'lunarOrbit_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  times = np.arange(DAY, SPAN, SAMPLE)
  lines = ['lunar laser ranging with the Moon\'s orbit, the split model against GR: two synodic months, a range every'
           ' %.0f h; GR\'s Moon fitted to the model\'s range (its start, and a constant); what is left' % (SAMPLE/3600)]
  for title, sun in (('the Earth alone, moving at 29.8 km/s (the floor)', False),
                     ('the Sun, and the Earth on its orbit', True)):
    model = Setup(sun, harmonic=False)
    runs = {}
    for dt in (10.0, 20.0):
      calc, moon = modelRun(model, dt)
      runs[dt] = modelRanges(model, calc, moon, times)
    target = (4*runs[10.0] - runs[20.0])/3
    resid, params = fit(Setup(sun, harmonic=True), target, times)
    lines.append('  %s: %s' % (title, describe(times, resid, model)))
    print(lines[-1], flush=True)
    with open(os.path.join(folder, 'residual_%s.csv' % ('sun' if sun else 'alone')), 'w', newline='') as f:
      w = csv.writer(f)
      w.writerow(['t_days', 'range_m', 'residual_m'])
      for t, r, e in zip(times, target, resid):
        w.writerow([t/DAY, r, e])
  lines.append('  lunar laser ranging: range residuals at the millimetre level; its fit to the synodic term,'
               ' (2.8 +- 4.1) mm cos D')
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
