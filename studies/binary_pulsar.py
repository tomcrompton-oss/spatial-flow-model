"""
a binary of comparable masses in the split model (engine/split.py): each body moves in the other's flow, by the
model's own step (its own flow left out), so the coupling between the two bodies' fields that GR has and the split
model leaves out shows where it is largest. against GR's periastron advance at first post-Newtonian order, exact for
any mass ratio:

  k = (advance per orbit)/2 pi = 3 (G M n)^(2/3)/(c^2 (1 - e^2)),    M = m1 + m2, n = 2 pi/P (P from periastron to
                                                                     periastron), e the eccentricity

for a light body round a heavy one the split model is the one-body flow model, which is GR, so k must agree there;
with equal masses the coupling is largest. the binary pulsars measure k with the masses known from other effects:
the double pulsar to about 10^-4

two bodies of 2 solar masses in all, a = 1e8 m (a period of 6.6 minutes, an advance of 6 x 10^-4 rad an orbit), e = 0.3,
started at periastron with the centre of mass at rest; run for ORBITS orbits at two step sizes, and the advance
extrapolated to zero step (Richardson: the step is second order). also the centre of mass (Newton's), which GR's
conserved momentum keeps from accelerating: at first post-Newtonian order it only swings, by metres here. its
acceleration is fitted over the run; the scheme's own floor, with c a thousand times larger, is about 0.002 m/s^2

run: python3 studies/binary_pulsar.py [boost ...]      (default freefall and lorentz; prints, and writes
     logs/multiBody/binaryPulsar_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle
from engine.split import SplitFlowCalculator
from engine.logger import LOG_DIR
from engine.constants import *

MTOTAL = 2*MS
A = 1e8
E = 0.3
ORBITS = 12
RATIOS = (1.0, 0.1, 0.01)          #m2/m1
STEPS = 4000                       #per orbit, at the coarser step


class MovingBody(Body):
  """a body moved by the model's steps: during a step, where it is and how fast it goes, from the step's start"""

  def __init__(self, mass, x, v):
    super().__init__(mass, x[0], x[1], velocity=v)
    self.set(0.0, x, v, np.zeros(2))

  def set(self, t, x, v, a):
    self.t0, self.x0, self.v0, self.a0 = t, np.array(x, dtype=float), np.array(v, dtype=float), np.array(a, dtype=float)
    self.pos, self.velocity = self.x0, self.v0

  def at(self, t):
    s = t - self.t0
    return self.x0 + self.v0*s + 0.5*self.a0*s*s

  def velocityAt(self, t):
    return self.v0 + self.a0*(t - self.t0)

  @property
  def moving(self):
    return True


def run(ratio, boost, steps):
  """the binary for ORBITS orbits: each periastron's time and angle (of body 1 from body 2), and the centre of mass's
  place over time"""
  m1 = MTOTAL/(1 + ratio)
  m2 = MTOTAL - m1
  rp = A*(1 - E)
  vrel = math.sqrt(G*MTOTAL*(1 + E)/rp)
  bodies = [MovingBody(m1, [m2/MTOTAL*rp, 0.0], [0.0, m2/MTOTAL*vrel]),
            MovingBody(m2, [-m1/MTOTAL*rp, 0.0], [0.0, -m1/MTOTAL*vrel])]
  calcs = []
  for b in bodies:
    calc = SplitFlowCalculator(bodies, 'static', boost)
    calc.skip = b
    calcs.append(calc)
  for i, b in enumerate(bodies):   #a first acceleration, Newton's, for the first step's guess of the other's path
    o = bodies[1 - i]
    r = o.x0 - b.x0
    b.set(0.0, b.x0, b.v0, G*o.mass*r/np.linalg.norm(r)**3)
  period = 2*math.pi*math.sqrt(A**3/(G*MTOTAL))
  dt = period/steps
  t = 0.0
  seps, centre = [], []
  while t < (ORBITS + 0.5)*period:
    new = []
    for b, calc in zip(bodies, calcs):
      p = Particle()
      p.pos, p.t = b.x0.copy(), t
      calc.initPV(p, b.v0.copy())
      calc.move(p, dt)
      new.append((p.pos, p.v))
    for b, (x, v) in zip(bodies, new):
      b.set(t + dt, x, v, (v - b.v0)/dt)
    t += dt
    rel = bodies[0].x0 - bodies[1].x0
    seps.append((t, np.linalg.norm(rel), math.atan2(rel[1], rel[0])))
    centre.append((t, (m1*bodies[0].x0 + m2*bodies[1].x0)/MTOTAL))
  #periastra: the separation's minima, by a parabola through the three samples round each
  peri = []
  for i in range(1, len(seps) - 1):
    if seps[i][1] < seps[i - 1][1] and seps[i][1] <= seps[i + 1][1]:
      (t0, r0, a0), (t1, r1, a1), (t2, r2, a2) = seps[i - 1], seps[i], seps[i + 1]
      f = 0.5*(r0 - r2)/(r0 - 2*r1 + r2)   #offset of the minimum, in steps from t1
      da = math.remainder(a2 - a0, 2*math.pi)/2
      peri.append((t1 + f*dt, a1 + f*da))
  return peri, np.array([c[1] for c in centre]), np.array([c[0] for c in centre])


def advance(peri):
  """the advance per orbit (rad) and the period, by straight-line fits to the periastra's angles and times"""
  n = np.arange(len(peri))
  times = np.array([p[0] for p in peri])
  angles = np.unwrap([p[1] for p in peri])
  return np.polyfit(n, angles, 1)[0], np.polyfit(n, times, 1)[0]


def main():
  boosts = sys.argv[1:] or ['freefall', 'lorentz']
  folder = os.path.join(LOG_DIR, 'multiBody', 'binaryPulsar_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = ['binary: 2 solar masses in all, a = %.0e m, e = %.1f, %d orbits; the periastron advance against GR\'s'
           ' 3 (GMn)^(2/3)/(c^2 (1 - e^2)) per 2 pi, extrapolated from %d and %d steps an orbit' % (A, E, ORBITS, STEPS, 2*STEPS)]
  print(lines[0], flush=True)
  for boost in boosts:
    for ratio in RATIOS:
      found = {}
      for steps in (STEPS, 2*STEPS):
        peri, centre, times = run(ratio, boost, steps)
        found[steps] = advance(peri) + (centre, times)
      k1, P1, centre, times = found[STEPS]
      k2, P2, centre2, times2 = found[2*STEPS]
      k = (4*k2 - k1)/3
      P = (4*P2 - P1)/3
      gr = 3*(G*MTOTAL*2*math.pi/P)**(2/3)/(C*C*(1 - E*E))*2*math.pi
      accel = 2*np.polyfit(times2, centre2, 2)[0]   #m/s^2, x and y
      lines.append('  %-9s m2/m1 %-5g advance %.6e rad an orbit (steps: %.6e, %.6e), GR %.6e: ratio %.5f;'
                   ' centre of mass accelerating at %.3f m/s^2'
                   % (boost, ratio, k, k1, k2, gr, k/gr, np.linalg.norm(accel)))
      print(lines[-1], flush=True)
  lines.append('  the double pulsar checks GR\'s periastron advance to about 10^-4, with both masses known from other effects')
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
