"""
flows with curl - the other way out of the one-Jacobi-constant problem (studies/turning_eikonal.py). with no curl,
Bernoulli's constant B = |w|^2/2 - U_R (w the flow relative to the turning frame, U_R the Roche potential) is the
same everywhere, and no value suits both the Sun (B = 0, its paths falling from rest far away) and the Earth (B = J,
its own flow carried). with curl it can differ from streamline to streamline - Crocco's theorem, for space falling at
g in the steady turning frame:

  grad B = w x omega,     omega = curl u (the flow's own vorticity, the frame's included)

so to go from B = 0 round the Sun to B = J round the Earth across a layer of width L the flow needs vorticity
|omega| >= |J|/(L |w|). what that costs, in two ways:

  einstein  Einstein's momentum constraint for a river (flat slices, unit lapse) is
            curl(omega) = -16 pi G (rho w_m)/c^2, w_m the matter's velocity through space: outside matter, omega must
            have no curl as well as no divergence - so, bounded, it is uniform (a turning frame: no physics). vorticity
            that changes across a layer needs matter streaming through it: rho w_m = c^2 |curl omega|/16 pi G
  force     anything moving through space at w feels -w x omega as well as g (the metric's own paths:
            dv/dt = g - w x omega): at 1 km/s, as the Moon goes round the Earth through the Earth's space

for two layers: round the Earth's own region (its Hill sphere, 1.5 million km), and across the gap between the Sun's
region and the Earth's orbit (0.63 to 1 AU). |w| is the turning flow's (engine/turning.py) where the layer is

run: python3 studies/curl_flows.py      (prints; no files)
"""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Calculator
from engine.constants import *
from turning_eikonal import turningCalc, OMEGA

SOLAR_WIND = 8e-21*4e5   #kg/m^2/s: about 5 protons/cm^3 at 400 km/s, the most matter streaming through the inner
                         #solar system


def main():
  calc = turningCalc()
  field = calc.rayField()
  J = field.J
  earth = calc.bodies[1].pos
  hill = AU*(ME/(3*MS))**(1/3)
  lines = ['curl: the vorticity a flow needs to carry B from 0 (the Sun\'s) to J = %.4e m^2/s^2 (the Earth\'s)'
           ' across a layer, and its cost' % J,
           '  %-34s %10s %10s %12s %14s %14s %14s' % ('layer', 'width (m)', '|w| (m/s)', 'omega (1/s)', 'rho w_m',
                                                       'x solar wind', '-w x omega, 1 km/s')]
  for title, centre, width in (('round the Earth (its Hill sphere)', earth + np.array([hill, 0.0]), hill),
                               ('the gap, 0.63 to 1 AU', np.array([0.8*AU, 0.0]), 0.37*AU)):
    #|w| there for B half way between: |w|^2 = 2(U_R + B)
    w2 = field.speed2(centre) - J
    w = math.sqrt(max(w2, 0.0))
    omega = abs(J)/(width*w)
    curl = omega/width                                   #the vorticity changing across the layer
    flux = C*C*curl/(16*math.pi*G)                       #kg/m^2/s of matter streaming through space
    moon = 1.0e3*omega                                   #something moving through space at 1 km/s, as the Moon does
    lines.append('  %-34s %10.3g %10.3g %12.3g %14.3g %14.3g %11.3g m/s^2' % (title, width, w, omega, flux,
                                                                               flux/SOLAR_WIND, moon))
  lines.append('  (rho w_m in kg/m^2/s; the solar wind carries about %.1g. the Earth\'s pull on the Moon is %.2g'
               ' m/s^2; the turning frame\'s own vorticity, 2 Omega = %.2g/s, is the uniform kind and costs nothing)'
               % (SOLAR_WIND, G*ME/3.844e8**2, 2*OMEGA))
  lines.append('  GR has curl in the river too - frame dragging - but sourced by matter moving through space, so of'
               ' order G M w_m/(c^2 r^2): %.1g/s round the Earth from its orbital motion, against the %.1g/s needed'
               % (G*ME*29.8e3/(C*C*REARTH**2), abs(J)/(hill*math.sqrt(max(field.speed2(earth + np.array([hill, 0.0])) - J, 0)))))
  print('\n'.join(lines))
  return lines


if __name__ == '__main__':
  main()
