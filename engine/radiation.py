"""
gravitational waves from a binary, for the flow model: the first step towards bodies that radiate

the model so far holds a wave that is given to it (engine/waves.py PlaneWave): a plane wave travelling straight
through the (x, y) plane is, to first order in its strain, exactly a flow of space, u = (1/2) (h+' X + hx' Y,
hx' X - h+' Y). nothing in the model makes such a wave: each body's flow is set by where the bodies are now, with no
equation for u that carries a change outward at c. this module supplies the two missing pieces at GR's leading
(quadrupole) order, so the rest of the model can be tested against them:

  1. the source. a binary of point masses moving under Newton's gravity plus the radiation reaction of its own waves
     (Burke-Thorne: each body feels a_i = -(2G/5c^5) Q^(5)_ij x_j, Q the binary's tracefree quadrupole moment,
     Q_ij = sum m (x_i x_j - delta_ij r^2/3), ^(5) its fifth time derivative). the energy this takes from the orbit is
     the energy the quadrupole formula says the waves carry off, so the orbit shrinks and the waves chirp (Peters)

  2. the wave. far away along the binary's axis (z, at distance D), the binary's waves are plane waves travelling
     along z, with h+ = (G/c^4 D) (Q''_xx - Q''_yy), hx = (2G/c^4 D) Q''_xy, taken at the retarded time t - D/c.
     BinaryWave gives them the same interface as PlaneWave, so a SpecialFlowCalculator(..., wave=BinaryWave(...))
     carries the binary's own waves through a detector's plane as a flow of space

the derivatives of Q are exact along the Newtonian orbit: the relative orbit's Taylor series is built term by term
(truncated power series arithmetic, KeplerJet), so Q's derivatives are k! times its coefficients, with no finite
differences. the radiation reaction's own effect on Q^(5) is of higher order (1/c^5 of it) and is left out, as usual

this is GR's quadrupole physics put into the model, not derived from it: the wave equation for the flow that would
produce it is still to be found. what it tests is the model's side - that the waves, once made, are carried by flowing
space as GR says, and that the orbit can lose energy to them

  binary = Binary(1.4*MS, 1.4*MS, a=3e5, e=0.0)
  binary.run(10.0)                                   integrate 10 s, keeping the history the wave reads from
  wave = BinaryWave(binary, distance=1e24)           h+, hx on the axis 1e24 m away (retarded)
  calc = SpecialFlowCalculator([], 2, wave=wave)
"""
import bisect
import math
import numpy as np
from engine.constants import C, G


# --- truncated power series: the coefficients of a quantity's Taylor series in time, f(t0 + s) = sum f_k s^k ---------

def series_mul(a, b, n):
  return [sum(a[i]*b[k - i] for i in range(k + 1)) for k in range(n)]


def series_pow(f, alpha, n):
  """f^alpha, for f[0] != 0: g_k = (1/(k f_0)) sum_{j=1..k} (alpha j - (k - j)) f_j g_{k-j}"""
  g = [f[0]**alpha]
  for k in range(1, n):
    g.append(sum((alpha*j - (k - j))*f[j]*g[k - j] for j in range(1, k + 1))/(k*f[0]))
  return g


def kepler_jet(x, v, GM, order):
  """
  the Taylor coefficients, to s^order, of the relative orbit x(t0 + s) under x'' = -GM x/r^3, from x and v at t0:
  [[x_0, x_1, ...], [y_0, y_1, ...]]. built order by order: x_{k+2} = a_k/((k+1)(k+2)), a = -GM x (x . x)^(-3/2)
  """
  X = [[x[0], v[0]], [x[1], v[1]]]
  for k in range(order - 1):
    n = k + 1                                        #coefficients known so far: 0..k+1; a needs 0..k
    r2 = [a + b for a, b in zip(series_mul(X[0], X[0], n), series_mul(X[1], X[1], n))]
    s = series_pow(r2, -1.5, n)
    for i in range(2):
      a = series_mul(X[i], s, n)[k]*(-GM)
      X[i].append(a/((k + 1)*(k + 2)))
  return X


def quadrupole_derivatives(x, v, GM, mu, orders):
  """
  the in-plane quadrupole Q_ij = mu (x_i x_j - delta_ij r^2/3) of a binary with relative position x and velocity v
  (reduced mass mu), and its zz part, differentiated: {k: (Qxx, Qxy, Qyy, Qzz)} for each k in orders
  """
  top = max(orders) + 1
  X = kepler_jet(x, v, GM, top)
  xx = series_mul(X[0], X[0], top)
  xy = series_mul(X[0], X[1], top)
  yy = series_mul(X[1], X[1], top)
  out = {}
  for k in orders:
    f = math.factorial(k)
    a, b, c = xx[k]*f, xy[k]*f, yy[k]*f
    r2 = a + c
    out[k] = (mu*(a - r2/3), mu*b, mu*(c - r2/3), -mu*r2/3)
  return out


class Binary:
  """
  two point masses m1, m2 on a relative orbit of semi-major axis a and eccentricity e, started at periastron with the
  centre of mass at rest at the origin, orbiting anticlockwise (seen from +z, the side the waves are taken on).
  reaction: True for the radiation reaction (the orbit shrinks); False for a fixed Newtonian orbit
  """

  def __init__(self, m1, m2, a, e=0.0, reaction=True):
    self.m1, self.m2 = m1, m2
    self.M = m1 + m2
    self.mu = m1*m2/self.M
    self.GM = G*self.M
    self.reaction = reaction
    rp = a*(1 - e)
    vp = math.sqrt(self.GM*(1 + e)/rp)
    self.a0, self.e0 = a, e
    self.times = [0.0]
    self.states = [np.array([rp, 0.0, 0.0, vp])]        #relative x, y, vx, vy
    self.merged = None                                   #the time the bodies touch (r below rMin), if they do
    self.rMin = 6*self.GM/C**2                           #stop at the innermost stable circular orbit, roughly

  def period(self):
    return 2*math.pi*math.sqrt(self.semiMajorAxis(self.states[-1])**3/self.GM)

  def acceleration(self, s):
    x = s[:2]
    r = math.hypot(*x)
    acc = -self.GM*x/r**3
    if self.reaction:
      Q5 = quadrupole_derivatives(x, s[2:], self.GM, self.mu, (5,))[5]
      Qx = np.array([Q5[0]*x[0] + Q5[1]*x[1], Q5[1]*x[0] + Q5[2]*x[1]])
      acc = acc - 2*G/(5*C**5)*Qx                       #each body: -(2G/5c^5) Q5 x_body; relative: x1 - x2 = x
    return acc

  def derivative(self, s):
    return np.concatenate([s[2:], self.acceleration(s)])

  def rk4(self, s, h):
    k1 = self.derivative(s)
    k2 = self.derivative(s + h/2*k1)
    k3 = self.derivative(s + h/2*k2)
    k4 = self.derivative(s + h*k3)
    return s + h/6*(k1 + 2*k2 + 2*k3 + k4)

  def stepFor(self, s, perOrbit):
    """a step a fixed fraction of the local orbital time r/v, so periastron is resolved as well as apastron"""
    r = math.hypot(s[0], s[1])
    v = math.hypot(s[2], s[3])
    return 2*math.pi*r/v/perOrbit

  def run(self, duration, perOrbit=2000):
    """integrate to duration (s) past the last state kept, or until the bodies reach rMin"""
    end = self.times[-1] + duration
    t, s = self.times[-1], self.states[-1]
    while t < end:
      h = min(self.stepFor(s, perOrbit), end - t)
      s = self.rk4(s, h)
      t += h
      self.times.append(t)
      self.states.append(s)
      if math.hypot(s[0], s[1]) < self.rMin:
        self.merged = t
        break
    return self

  def state(self, t):
    """the relative state at t: the kept state just before t, stepped on to t (a step under one kept step: exact to
    the integrator's order)"""
    if t <= self.times[0]:
      return self.states[0]
    i = bisect.bisect_right(self.times, t) - 1
    if i >= len(self.times) - 1:
      if t > self.times[-1] + 1e-12:
        raise ValueError('t = %g s is beyond the binary run (to %g s)' % (t, self.times[-1]))
      return self.states[-1]
    h = t - self.times[i]
    return self.states[i] if h == 0 else self.rk4(self.states[i], h)

  def bodies(self, t):
    """the two bodies' positions at t (the centre of mass at the origin)"""
    s = self.state(t)
    return self.m2/self.M*s[:2], -self.m1/self.M*s[:2]

  def quadrupole(self, t, orders=(2, 3)):
    """
    Q's derivatives at t along the Newtonian orbit through the state there. with the radiation reaction on, Q''' is
    then made the true rate of change of that Q'' = mu (2 v v + a_N x + x a_N), a_N Newton's pull: its rate is
    mu (2 (a v + v a) + (a_N v + v a_N) + a_N' x + x a_N'), the first part with the orbit's whole acceleration,
    the reaction's included, where the Newtonian series has a_N. without that, h' would not be
    the rate of h by a fraction (da/dt)/(a n) - 1e-3 near the end of an inspiral - and a wave's h and its flow
    would drift apart
    """
    s = self.state(t)
    out = quadrupole_derivatives(s[:2], s[2:], self.GM, self.mu, orders)
    if self.reaction and 3 in orders:
      r = self.acceleration(s) + self.GM*s[:2]/math.hypot(*s[:2])**3       #the reaction's part of the acceleration
      v = s[2:]
      dxx, dxy, dyy = 4*r[0]*v[0], 2*(r[0]*v[1] + v[0]*r[1]), 4*r[1]*v[1]
      tr = (dxx + dyy)/3
      xx, xy, yy, zz = out[3]
      out[3] = (xx + self.mu*(dxx - tr), xy + self.mu*dxy, yy + self.mu*(dyy - tr), zz - self.mu*tr)
    return out

  def energy(self, s):
    """the orbit's Newtonian energy (J)"""
    return self.mu*(0.5*(s[2]**2 + s[3]**2) - self.GM/math.hypot(s[0], s[1]))

  def semiMajorAxis(self, s):
    r = math.hypot(s[0], s[1])
    return 1/(2/r - (s[2]**2 + s[3]**2)/self.GM)

  def eccentricity(self, s):
    x, v = s[:2], s[2:]
    h = x[0]*v[1] - x[1]*v[0]                            #angular momentum per reduced mass (z)
    ev = np.array([v[1]*h, -v[0]*h])/self.GM - x/math.hypot(*x)
    return math.hypot(*ev)

  def luminosity(self, t):
    """the power the quadrupole formula gives the waves, (G/5c^5) Q'''_ij Q'''_ij (W)"""
    xx, xy, yy, zz = self.quadrupole(t, (3,))[3]
    return G/(5*C**5)*(xx*xx + 2*xy*xy + yy*yy + zz*zz)

  def describe(self):
    return ('binary: %.4g + %.4g solar masses, a = %g m, e = %g, %s radiation reaction'
            % (self.m1/1.989e30, self.m2/1.989e30, self.a0, self.e0, 'with' if self.reaction else 'no'))


def peters(a, e, m1, m2):
    """Peters (1964): (da/dt, de/dt), orbit-averaged, for the quadrupole radiation reaction"""
    M = m1 + m2
    k = G**3*m1*m2*M/C**5
    f = 1 - e*e
    dadt = -64/5*k/(a**3*f**3.5)*(1 + 73/24*e*e + 37/96*e**4)
    dedt = -304/15*e*k/(a**4*f**2.5)*(1 + 121/304*e*e)
    return dadt, dedt


class BinaryWave:
  """
  the binary's waves where they cross a plane far away on its axis (z, distance D): plane waves travelling along z,
  so with PlaneWave's interface (strain, rate, flow, integral) and its flow, a shear of space about centre.
  scale multiplies the strain, to make it large enough to see in the viewer (1 for the real thing)
  """

  along = None                                           #travelling along z, through the plane

  def __init__(self, binary, distance, centre=(0.0, 0.0), scale=1.0, delay=None):
    self.binary = binary
    self.distance = distance
    self.centre = np.array(centre, dtype=float)
    self.scale = scale
    self.delay = distance/C if delay is None else delay   #the light time; delay lets the plane's clock start anywhere
    self.amplitude = scale*G/(C**4*distance)

  def when(self, pos, t):
    return t

  def emitted(self, t):
    return t - self.delay

  def derivatives(self, t):
    """Q'' and Q''' at the retarded time for t, kept for the last few t asked for (a ring of particles stepped
    together asks for the same few times over and over)"""
    cache = self.__dict__.setdefault('_cache', {})
    if t not in cache:
      if len(cache) > 64:
        cache.clear()
      cache[t] = self.binary.quadrupole(self.emitted(t), (2, 3))
    return cache[t]

  def strain(self, t):
    """(h+, hx) in the plane at t"""
    xx, xy, yy, _ = self.derivatives(t)[2]
    return self.amplitude*(xx - yy), 2*self.amplitude*xy

  def rate(self, t):
    """(h+', hx') in the plane at t"""
    xx, xy, yy, _ = self.derivatives(t)[3]
    return self.amplitude*(xx - yy), 2*self.amplitude*xy

  def integral(self, t0, t1, n=400):
    """the integrals of h+ and hx from t0 to t1 (Simpson's rule), for light's travel time"""
    n += n % 2
    h = (t1 - t0)/n
    sp = sx = 0.0
    for i in range(n + 1):
      w = 1 if i in (0, n) else (4 if i % 2 else 2)
      p, x = self.strain(t0 + i*h)
      sp += w*p
      sx += w*x
    return sp*h/3, sx*h/3

  def flow(self, pos, t):
    X, Y = pos[0] - self.centre[0], pos[1] - self.centre[1]
    p, x = self.rate(t)
    return np.array([(p*X + x*Y)/2, (x*X - p*Y)/2])

  def describe(self):
    return ('the waves of a %s, on its axis %g m away (retarded by %g s), strain x %g, centred at (%g, %g) m'
            % (self.binary.describe(), self.distance, self.delay, self.scale, *self.centre))
