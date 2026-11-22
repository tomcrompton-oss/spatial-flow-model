"""
step 4.3's spin, run: frame dragging round one spinning body, from 4.2's moving-potential term alone

the model's spin for several bodies has no twist: a body's spin enters through rule 5, the 4 U_j/c^2 of its own
rotating matter, which outside it is a curl in the flow,

  u = (Part 1's river, -sqrt(2GM/r) r^)  +  2 G J x r / (c^2 r^3)     (J along the spin axis, here out of the plane)

with N = 1 and flat space (a body at rest: the J = 0 rules' space and corrections are then Part 1's flat river in other
coordinates). in the equatorial plane - the engine is planar - frame dragging shows in the orbits: going round with
the spin, the periapsis moves on less; against it, more. Lense-Thirring's part, odd in the spin, per orbit:
  -8 pi chi (GM/c^2 a)^(3/2) / (1 - e^2)^(3/2),     chi = c J / (G M^2)
measured: the precession with and against the spin, its odd part (half the difference) against Lense-Thirring's and
against exact Kerr's odd part for the same apsides (engine/exact.py), and with no spin against exact Schwarzschild.
the twist of Part 1's river model of a Kerr hole (engine/kerr.py) isn't used: this is 4.3's flow, not 1.3's

run: python3 studies/frame_dragging.py     (a few minutes; prints, and writes
     logs/modelChecks/frameDragging_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.constants import *
from engine.flow import Body, Particle
from engine.metric import Spacetime, MetricCalculator
from engine.exact import kerrPrecessionExact, grPrecessionExact
from engine.logger import LOG_DIR
from studies.compare_second_order import apsis

MASS = 4e6*MS
FRACTION = 3e-4
ORBITS = 4


class SpinningBody(Spacetime):
  """one body at rest at the origin, spin chi: Part 1's river plus 4.2's curl from its rotation; N = 1, flat space"""

  def __init__(self, chi):
    self.bodies = [Body(MASS)]
    self.chi = chi
    self.J = chi*G*MASS**2/C            #angular momentum, along +z (anticlockwise in the plane)
    self.centre = np.zeros(2)

  def describe(self):
    return 'a spinning body (chi %g): the river plus 2GJ x r/c^2 r^3' % self.chi

  def flow(self, x, t, region=None):
    r = math.hypot(x[0], x[1])
    river = -math.sqrt(2*G*MASS/r)*x/r
    return river + 2*G*self.J/(C*C*r**3)*np.array([-x[1], x[0]])


def precession(chi, rStart, speed, prograde):
  """precession per orbit at its periapses, and its mean periapsis and apoapsis distances"""
  calc = MetricCalculator(SpinningBody(chi))
  p = Particle()
  p.pos = np.array([0.0, rStart])
  calc.initPV(p, np.array([(-1.0 if prograde else 1.0)*speed, 0.0]))   #-x from the top is anticlockwise
  last, peris, apos = [], [], []
  turned, prev = 0.0, math.atan2(p.pos[1], p.pos[0])
  while turned < 2*math.pi*(ORBITS + 0.5):
    calc.move(p, calc.stepSize(p, FRACTION))
    angle = math.atan2(p.pos[1], p.pos[0])
    turned += abs((angle - prev + math.pi) % (2*math.pi) - math.pi)
    prev = angle
    last = (last + [(p.t, np.linalg.norm(p.pos), p.pos.copy())])[-3:]
    if len(last) == 3:
      (_, x0, _), (_, x1, _), (_, x2, _) = last
      for found, store in ((x1 < x0 and x1 <= x2, peris), (x1 > x0 and x1 >= x2, apos)):
        if found:
          store.append(apsis([q[0] for q in last], [q[1] for q in last], [q[2] for q in last]))
  sense = 1.0 if p.pos[0]*p.v[1] - p.pos[1]*p.v[0] > 0 else -1.0
  turn = sense*float(np.mean(np.diff(np.unwrap([math.atan2(q[2][1], q[2][0]) for q in peris]))))
  return turn, float(np.mean([q[1] for q in peris])), float(np.mean([q[1] for q in apos]))


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'frameDragging_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = []
  def say(s):
    lines.append(s)
    print(s, flush=True)
  M = G*MASS/C**2
  say('step 4.3 for one body: the river plus 2GJ x r/c^2 r^3, N = 1, flat space; a %g solar-mass body, sizes in M = GM/c^2' % (MASS/MS))
  say('precession per orbit (rad): with the spin, against it; the odd part, half the difference, against Lense-Thirring')
  say("and against exact Kerr's odd part for each orbit's own apsides")
  for rStart, speed in ((100, 0.085), (400, 0.043)):
    p0, rp0, ra0 = precession(0.0, rStart*M, speed*C, True)
    say('')
    say('from %d M at %.3f c; no spin: %.6e, exact Schwarzschild for its apsides %.6e (peri %.1f M, apo %.1f M)'
        % (rStart, speed, p0, grPrecessionExact(rp0, ra0, MASS), rp0/M, ra0/M))
    for chi in (0.1, 0.5):
      pw, rpw, raw = precession(chi, rStart*M, speed*C, True)
      pa, rpa, raa = precession(chi, rStart*M, speed*C, False)
      odd = (pw - pa)/2
      kerr = (kerrPrecessionExact(rpw, raw, MASS, chi, True) - kerrPrecessionExact(rpa, raa, MASS, chi, False))/2
      a = (rpw + raw)/2/M
      e = (raw - rpw)/(raw + rpw)
      lt = -8*math.pi*chi*a**-1.5/(1 - e*e)**1.5
      say('  chi %.1f: with %.6e, against %.6e; odd part %.4e; Lense-Thirring %.4e (odd/LT %.4f); Kerr %.4e (odd/Kerr %.4f)'
          % (chi, pw, pa, odd, lt, odd/lt, kerr, odd/kerr))
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
