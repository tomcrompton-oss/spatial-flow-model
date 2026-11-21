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


class LocalTurningFlow:
  """
  the turning flow round the lighter body (the Earth), worked out finely: TurningRayField's table falls at g only to
  ~1e-6 m/s^2 at the Moon with J = 0 (whose |w| there is ~51 km/s, so (w . grad) u ~ 7 m/s^2 must cancel to 1e-10).
  here the body's paths are followed out (backwards in time: dv/dtau = g + 2 Omega x v, v = -w) from r0 in u = ln r,
  with fine RK4 steps, all at once; at each Chebyshev node in ln r the paths' w is fitted round the circle with a
  Fourier series (least squares, more paths than harmonics), so w(r, theta) is smooth, a Chebyshev series in ln r of
  Fourier series in theta. the bodies are where they are at t = 0, in the turning frame
  """

  def __init__(self, bodies, omega, J, k=None, r0=1e3, rlo=1e6, rhi=3e9, nodes=48, harmonics=12, paths=96, step=5e-4):
    self.bodies = list(bodies)
    self.omega, self.J = omega, J
    self.k = min(range(len(self.bodies)), key=lambda i: self.bodies[i].mass) if k is None else k
    self.z = np.array(self.bodies[self.k].pos, dtype=float)
    self.rlo, self.rhi = rlo, rhi
    self.ulo, self.uhi = math.log(rlo), math.log(rhi)
    xs = np.cos(math.pi*(np.arange(nodes) + 0.5)/nodes)[::-1]          #Chebyshev nodes, increasing
    us = self.ulo + (self.uhi - self.ulo)*(xs + 1)/2
    self.m = np.arange(-harmonics, harmonics + 1)
    a = 2*math.pi*np.arange(paths)/paths
    th, vx, vy = self.launch(a, r0)
    u = math.log(r0)
    fits = np.zeros((nodes, 2, len(self.m)), dtype=complex)
    self.worst = 0.0
    for i, target in enumerate(us):
      n = max(1, int(math.ceil((target - u)/step)))
      h = (target - u)/n
      for _ in range(n):
        th, vx, vy = self.rk4(u, h, th, vx, vy)
        u += h
      r = math.exp(u)
      c, s = np.cos(th), np.sin(th)
      wr, wt = -(vx*c + vy*s), -(-vx*s + vy*c)                        #w = -v, along and across the radius
      M = np.exp(1j*np.outer(th, self.m))
      for j, f in enumerate((wr, wt)):
        fits[i, j] = np.linalg.lstsq(M, f.astype(complex), rcond=None)[0]
      self.worst = max(self.worst, float(np.max(np.abs(vx*vx + vy*vy - self.w2(r, c, s))
                                               /(vx*vx + vy*vy))))
    #Chebyshev coefficients in ln r of each Fourier coefficient
    T = np.cos(np.outer(np.arange(nodes), math.pi*(np.arange(nodes) + 0.5)/nodes))[:, ::-1]   #T_n at the nodes
    self.cheb = (2/nodes)*np.einsum('ni,ijm->njm', T, fits)
    self.cheb[0] /= 2

  def w2(self, r, c, s):
    """|w|^2 = 2 (U + Omega^2 rho^2/2 + J) at r (c, s) from the body (its own term from that, not from x - z: at
    r ~ 1 km, 1.5e11 m away from the origin, the difference would lose eight figures)"""
    x, y = self.z[0] + r*c, self.z[1] + r*s
    U = self.bodies[self.k].GM/r + sum(b.GM/np.sqrt((x - b.pos[0])**2 + (y - b.pos[1])**2)
                                       for i, b in enumerate(self.bodies) if i != self.k)
    return 2*(U + self.omega**2*(x*x + y*y)/2 + self.J)

  def launch(self, a, r0):
    c, s = np.cos(a), np.sin(a)
    v = np.sqrt(self.w2(r0, c, s))
    return a.copy(), v*c, v*s

  def rates(self, u, th, vx, vy):
    r = math.exp(u)
    c, s = np.cos(th), np.sin(th)
    x, y = self.z[0] + r*c, self.z[1] + r*s
    own = self.bodies[self.k].GM/(r*r)
    gx, gy = self.omega**2*x - own*c, self.omega**2*y - own*s
    for i, b in enumerate(self.bodies):
      if i == self.k:
        continue
      dx, dy = b.pos[0] - x, b.pos[1] - y
      d3 = (dx*dx + dy*dy)**1.5
      gx, gy = gx + b.GM*dx/d3, gy + b.GM*dy/d3
    ax, ay = gx - 2*self.omega*vy, gy + 2*self.omega*vx                #g + 2 Omega x v
    vr = vx*c + vy*s
    per = r/vr                                                        #d tau/du
    return (-vx*s + vy*c)/vr, ax*per, ay*per

  def rk4(self, u, h, th, vx, vy):
    k1 = self.rates(u, th, vx, vy)
    k2 = self.rates(u + h/2, th + h/2*k1[0], vx + h/2*k1[1], vy + h/2*k1[2])
    k3 = self.rates(u + h/2, th + h/2*k2[0], vx + h/2*k2[1], vy + h/2*k2[2])
    k4 = self.rates(u + h, th + h*k3[0], vx + h*k3[1], vy + h*k3[2])
    return tuple(q + h/6*(a + 2*b + 2*c + d) for q, a, b, c, d in zip((th, vx, vy), k1, k2, k3, k4))

  def covers(self, y):
    r = math.hypot(y[0] - self.z[0], y[1] - self.z[1])
    return self.rlo <= r <= self.rhi

  def w(self, y):
    """the flow relative to the turning frame at y (turning-frame coordinates, within rlo..rhi of the body)"""
    d = np.asarray(y, dtype=float) - self.z
    r = math.hypot(d[0], d[1])
    x = 2*(math.log(r) - self.ulo)/(self.uhi - self.ulo) - 1
    T = np.cos(np.arange(len(self.cheb))*math.acos(max(-1.0, min(1.0, x))))
    coef = np.tensordot(T, self.cheb, axes=(0, 0))                    #(2, harmonics)
    th = math.atan2(d[1], d[0])
    wr, wt = np.real(coef @ np.exp(1j*self.m*th))
    c, s = d[0]/r, d[1]/r
    return np.array([wr*c - wt*s, wr*s + wt*c])
