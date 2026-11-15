"""
the eikonal flow for two bodies going round each other on circles - the flow turning with them, so that each body
carries its own flow (Calculator combine 'turning'; studies/turning_eikonal.py)

the flow has no curl, u = grad phi, and space falls at g when phi keeps Bernoulli's equation,
d phi/dt + |u|^2/2 = U + f(t) - which also gives clocks GR's first-order rates, the bodies moving or not. in the frame
turning with the bodies (at Omega, about their centre of mass) the flow is steady, and the equation becomes a static
eikonal for the flow relative to that frame, w = u - Omega x x:

  |w|^2 = 2 (U + Omega^2 rho^2/2 + J)       (U + Omega^2 rho^2/2 is the Roche potential, J a constant: Jacobi's)

its paths are the restricted three-body problem's, all with Jacobi constant J. a seam keeps the metric continuous only
if the flows either side have the same J, so J is one number for the whole flow. with J = 0 the flow round the
secondary (the Earth) has the primary's potential and the orbit's speed in it, |w|^2 = 2GM/r + 3GM_S/a: the stretch of
studies/multi_body_pn.py, half as big again. carried - the Earth's own flow, with none of the Sun's in it - needs
J = -(the Roche potential at the Earth, less the Earth's own), CARRIED: then round the Earth |w|^2 = 2GM/r + tides

that J is below zero, so in three dimensions there is no flow at all along the axis of the orbit beyond about
2/3 AU (|w|^2 = 2(GM_S/z + J) < 0 there): this works only in the plane

TurningRayField is engine/eikonal.py's RayField in the turning frame: each body's paths, run out from it backwards in
time (outwards; the Coriolis force then turns them the other way), with the Roche potential's g, |w|^2 from J, and S
the integral of -u . dx (u = -grad S): S grows by (|w| - (Omega x x) . w/|w|) ds. paths that turn back (the primary's
reach only GM_S/|J| = 2a/3, as for anything let go from rest at that energy) leave the table
"""
import math
import numpy as np
from engine.constants import *
from engine.eikonal import RayField


def carriedJacobi(bodies, omega):
  """J for which the flow round the lighter body has none of the heavier one's potential: minus the Roche potential at
  the lighter body, less its own term"""
  light = min(bodies, key=lambda b: b.mass)
  others = sum(b.GM/np.linalg.norm(light.pos - b.pos) for b in bodies if b is not light)
  return -(others + omega**2*(light.pos @ light.pos)/2)


class TurningRayField(RayField):
  """
  RayField in the frame turning at omega about the origin (the bodies' centre of mass), the bodies at their places
  there (as at t = 0), with Jacobi constant J. a path leaves the table once it turns 60 degrees from radial: there it
  is about to turn back (the primary's, at 2a/3) or curl round, and the paths would cross
  """
  steepest = 0.5

  def __init__(self, bodies, omega, J, **kwargs):
    self.omega, self.J = omega, J
    kwargs.setdefault('maxR', 3*AU)
    super().__init__(bodies, **kwargs)

  def accel(self, x, y):
    """g of the Roche potential (the bodies' and the centrifugal) at (x, y), and |w|^2 there"""
    gx, gy, n2 = super().accel(x, y)
    w2 = self.omega**2
    return gx + w2*x, gy + w2*y, n2 + w2*(x*x + y*y) + 2*self.J

  def turn(self, x, y, n2):
    #a path run backwards in time feels the Coriolis force the other way: across it 2 Omega |w|
    return 2*self.omega*np.sqrt(n2)

  def actionRate(self, x, y, c, s, n2):
    #dS/ds = -u . (c, s), u = -|w|(c, s) + Omega x x on the way out
    return np.sqrt(n2) - self.omega*(-y*c + x*s)

  def speed2(self, pos):
    """|w|^2 at pos (in the turning frame)"""
    x, y = np.array([pos[0]]), np.array([pos[1]])
    return float(self.accel(x, y)[2][0])
