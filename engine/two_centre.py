"""
the eikonal flow for exactly two bodies, worked out exactly - no tables - from the separation of the zero-energy
Hamilton-Jacobi equation in elliptic coordinates (Euler's problem of two fixed centres). the same flow as
engine/eikonal.py's RayField (zero-energy newtonian paths straight out of each body, the seam where the bodies' S
are equal, through the saddle of the potential), and the same calls, but only for two bodies

for a body ('the source') and the other body, with the source at +a and the other at -a on a local x axis,
z = x + iy = a cosh(mu + i nu): mu >= 0 grows outwards (mu = 0 is the line between them), nu runs from 0 (the axis
beyond the source) to pi (the axis beyond the other). the metric is conformal, ds^2 = a^2 (sinh^2 mu + sin^2 nu)
(dmu^2 + dnu^2), and |grad S|^2 = |u|^2 = 2G (M/r + M'/r') becomes

  S_mu^2 + S_nu^2 = k cosh mu + c cos nu,   k = 2a(GM + GM'),  c = 2a(GM - GM')

which separates: S = A(mu) + B(nu), A'^2 = k cosh mu + beta, B'^2 = c cos nu - beta. beta labels the path (beta = c
runs out along the axis beyond the source, beta = -k along the axis to the other body). along a path, in a
parameter tau, dmu/dtau = A' and dnu/dtau = B' (so mu'' = (k/2) sinh mu, and nu is a pendulum, nu'' = -(c/2) sin nu):

  tau(mu) = sqrt(2/k) F(theta | 1 - eps),   eps = (k + beta)/2k,  tan theta = sinh(mu/2)/sqrt(eps)
  nu(tau) = 2 am(sqrt(c - beta) tau/2 | 2c/(c - beta))           (nu goes round: 0 <= 2c/(c - beta) <= 1)
            2 arcsin(sn(sqrt(c/2) tau | (c - beta)/2c) sqrt((c - beta)/2c))   (it swings back: 2c/(c - beta) > 1)
            pi - 2 am(K - sqrt(|c| - beta) tau/2 | 2|c|/(|c| - beta))         (c < 0, the source the lighter)

with S the integral of A'^2 + B'^2 over tau, in incomplete elliptic integrals too. the path through a point is the
beta for which nu(tau(mu)) is the point's nu - one equation, solved in log((k + beta)/(c - beta)), since paths near
the line between the bodies have k + beta exponentially small, and paths near the axis beyond the source c - beta. the
flow is -grad S, S_x + i S_y proportional to
(S_mu + i S_nu) sinh(mu + i nu)

  field = TwoCentreField(bodies)    (two bodies; nothing to build)
  field.direction(pos)              unit direction of the flow at pos
  field.region(pos)                 index of the body whose region pos is in (smallest S)
  field.action(pos, i)              body i's S at pos, with its constant
  field.direction(pos, region)      the direction from region's paths, either side of the seam
"""
import cmath
import math
import numpy as np


def carlsonRF(x, y, z):
  """Carlson's symmetric elliptic integral R_F(x, y, z) (x, y, z >= 0, at most one 0), by duplication"""
  for _ in range(200):
    sx, sy, sz = math.sqrt(x), math.sqrt(y), math.sqrt(z)
    lam = sx*sy + sy*sz + sz*sx
    x, y, z = (x + lam)/4, (y + lam)/4, (z + lam)/4
    mean = (x + y + z)/3
    dx, dy, dz = 1 - x/mean, 1 - y/mean, 1 - z/mean
    if max(abs(dx), abs(dy), abs(dz)) < 1e-4:
      break
  e2, e3 = dx*dy - dz*dz, dx*dy*dz
  return (1 - e2/10 + e3/14 + e2*e2/24 - 3*e2*e3/44)/math.sqrt(mean)


def carlsonRD(x, y, z):
  """Carlson's R_D(x, y, z) = R_J(x, y, z, z) (x, y >= 0, at most one 0; z > 0), by duplication"""
  total, scale = 0.0, 1.0
  for _ in range(200):
    sx, sy, sz = math.sqrt(x), math.sqrt(y), math.sqrt(z)
    lam = sx*sy + sy*sz + sz*sx
    total += scale/(sz*(z + lam))
    scale /= 4
    x, y, z = (x + lam)/4, (y + lam)/4, (z + lam)/4
    mean = (x + y + 3*z)/5
    dx, dy, dz = 1 - x/mean, 1 - y/mean, 1 - z/mean
    if max(abs(dx), abs(dy), abs(dz)) < 1e-4:
      break
  ea, eb = dx*dy, dz*dz
  ec, ed = ea - eb, ea - 6*eb
  ee = ed + ec + ec
  series = 1 + ed*(-3/14 + 9*ed/88 - 4.5*dz*ee/26) + dz*(ee/6 + dz*(-9*ec/22 + 3*dz*ea/26))
  return 3*total + scale*series/(mean*math.sqrt(mean))


#each takes the complementary parameter 1 - m too, if it is known more precisely than 1 - m works out (m near 1)

def ellipticK(m, m1=None):
  """the complete elliptic integral of the first kind, K(m)"""
  return carlsonRF(0.0, 1 - m if m1 is None else m1, 1.0)


def ellipticE(phi, m, m1=None):
  """the incomplete elliptic integral of the second kind E(phi | m), any phi (m <= 1)"""
  m1 = 1 - m if m1 is None else m1
  turns = round(phi/math.pi)
  r = phi - turns*math.pi
  s, c = math.sin(abs(r)), math.cos(abs(r))
  d2 = c*c + m1*s*s                    #1 - m sin^2
  part = s*carlsonRF(c*c, d2, 1.0) - m/3*s**3*carlsonRD(c*c, d2, 1.0)
  whole = 2*(carlsonRF(0.0, m1, 1.0) - m/3*carlsonRD(0.0, m1, 1.0)) if turns else 0.0
  return turns*whole + math.copysign(part, r)


def jacobi(u, m, m1=None):
  """the Jacobi elliptic functions sn, cn, dn of u (parameter 0 <= m <= 1) and the amplitude am(u), unwrapped"""
  m1 = 1 - m if m1 is None else m1
  if m1 <= 1e-300:
    ph = 2*math.atan(math.tanh(u/2))   #the m = 1 limit (the gudermannian)
  else:
    a, b, cs = [1.0], math.sqrt(m1), [math.sqrt(m)]
    while abs(cs[-1]) > 1e-16 and len(a) < 40:   #the arithmetic-geometric mean
      a.append((a[-1] + b)/2)
      cs.append((a[-2] - b)/2)
      b = math.sqrt(a[-2]*b)
    ph = 2**(len(a) - 1)*a[-1]*u
    for n in range(len(a) - 1, 0, -1):
      ph = (ph + math.asin(cs[n]/a[n]*math.sin(ph)))/2
  sn, cn = math.sin(ph), math.cos(ph)
  return sn, cn, math.sqrt(cn*cn + m1*sn*sn), ph


class Source:
  """one body's zero-energy paths, in the elliptic coordinates with it at +a and the other body at -a"""

  def __init__(self, body, other):
    self.origin = np.array(body.pos, dtype=float)
    apart = self.origin - np.asarray(other.pos, dtype=float)
    self.a = float(np.linalg.norm(apart))/2
    self.ex = apart/(2*self.a)                   #the local x axis, from the other body through this one
    self.ey = np.array([-self.ex[1], self.ex[0]])
    self.k = 2*self.a*(body.GM + other.GM)
    self.c = 2*self.a*(body.GM - other.GM)
    self.sign = -1.0 if body.black else 1.0      #the flow runs down the paths into a black body, out of a white one
    self.guess = 0.0                             #log((k + beta)/(c - beta)) of the last path found, to start from
    self.slope = None                            #and the rate of change of nu with it there
    self.last = None                             #(pos, result) of the last point

  def coordinates(self, pos):
    """mu, nu (0 to pi) of pos, w/2 = (mu + i nu)/2 as a complex number, and whether pos is below the local x axis"""
    d = np.asarray(pos, dtype=float) - self.origin
    x, y = float(np.dot(d, self.ex)), float(np.dot(d, self.ey))
    zeta = complex(x, abs(y))/self.a             #z/a - 1, from the source itself so nothing is lost near it
    half = cmath.asinh(cmath.sqrt(zeta/2))       #cosh w - 1 = 2 sinh^2(w/2)
    return 2*half.real, 2*half.imag, half, y < 0

  def outward(self, mu, A):
    """tau at mu along the path with k + beta = A, and the part of S from mu, the integral of A'^2 over tau"""
    k = self.k
    t = mu/2
    sh = math.sinh(t)
    eps = A/(2*k)
    q = eps + sh*sh
    s = sh/math.sqrt(q)                          #sin theta
    c2, d2 = eps/q, eps*math.cosh(t)**2/q        #cos^2 theta and 1 - (1 - eps) sin^2 theta
    rf = carlsonRF(c2, d2, 1.0)
    tau = math.sqrt(2/k)*s*rf
    E = s*rf - (1 - eps)/3*s**3*carlsonRD(c2, d2, 1.0)
    return tau, 2*math.sqrt(2*k)*(s*math.cosh(t) - E) + A*tau

  def round(self, tau, B):
    """nu at tau along the path with c - beta = B (nu'(0)^2), its rate nu' there, and the part of S from nu"""
    c = self.c
    if B <= 0:                                   #straight out along the axis beyond the source
      return 0.0, 0.0, 0.0
    if c >= 0 and 2*c <= B:                      #it goes round
      m = 2*c/B
      u = math.sqrt(B)*tau/2
      sn, cn, dn, ph = jacobi(u, m)
      return 2*ph, math.sqrt(B)*dn, 2*math.sqrt(B)*ellipticE(ph, m)
    if c >= 0:                                   #it swings back, at cos nu = beta/c
      n = B/(2*c)
      w = math.sqrt(c/2)*tau
      sn, cn, dn, ph = jacobi(w, n)
      return 2*math.asin(min(1.0, sn*math.sqrt(n))), math.sqrt(B)*cn, B*math.sqrt(2/c)*(ellipticE(ph, n) - (1 - n)*w)/n
    D = B - 2*c                                  #|c| - beta: the source is the lighter
    m, m1 = -2*c/D, B/D                          #m1 = 1 - m, small for paths near the axis beyond the source
    K = ellipticK(m, m1)
    sn, cn, dn, ph = jacobi(K - math.sqrt(D)*tau/2, m, m1)
    return math.pi - 2*ph, math.sqrt(D)*dn, 2*math.sqrt(D)*(ellipticE(math.pi/2, m, m1) - ellipticE(ph, m, m1))

  def path(self, mu, nu):
    """the path through (mu, nu): (S_mu, S_nu, S) there"""
    k, c = self.k, self.c
    if nu <= 0.0:                                #the axis beyond the source: beta = c
      return math.sqrt(k*math.cosh(mu) + c), 0.0, self.outward(mu, k + c)[1]
    if mu <= 0.0:                                #the line to the other body: beta = -k
      m = 2*c/(c + k)
      return 0.0, math.sqrt(c*math.cos(nu) + k), 2*math.sqrt(c + k)*ellipticE(nu/2, m)
    whole = k + c

    def split(x):
      #k + beta and c - beta (which add up to k + c) from x = log((k + beta)/(c - beta)), each to full precision
      #however near one end the path is - the line to the other body, or the axis beyond this one
      e = math.exp(-abs(x))
      big, small = whole/(1 + e), whole*e/(1 + e)
      return (big, small) if x >= 0 else (small, big)

    def miss(x):
      A, B = split(x)
      tau, SA = self.outward(mu, A)
      found = self.round(tau, B)
      last[:] = [x, A, SA, found]
      return found[0] - nu

    last = [None]*4
    x = self.root(miss, nu)
    if last[0] != x:
      miss(x)
    _, A, SA, (_, Snu, SB) = last
    self.guess = x
    return math.sqrt(A + 2*k*math.sinh(mu/2)**2), Snu, SA + SB

  def root(self, miss, nu):
    """
    the x = log((k + beta)/(c - beta)) of the path that reaches nu (miss(x) = 0): secant steps from the last path found
    (the next point is usually near it), or, if they wander, bracketing - nu at the point falls as the path starts
    nearer the axis beyond the source (x large, where it is 0) - and the Illinois method
    """
    x0 = self.guess
    f0 = miss(x0)
    x1 = x0 - f0/self.slope if self.slope else x0 - 1e-7*max(1.0, abs(x0))   #a newton step with the last slope
    if not -700 < x1 < 700:
      x1 = x0 - 1e-7*max(1.0, abs(x0))
    f1 = miss(x1)
    for _ in range(12):
      if f1 == 0 or f1 == f0:
        break
      self.slope = (f1 - f0)/(x1 - x0)
      x2 = x1 - f1/self.slope
      if not -700 < x2 < 700:
        break
      x0, f0, x1 = x1, f1, x2
      f1 = miss(x1)
      if abs(x1 - x0) < 1e-13*max(1.0, abs(x1)):
        break
    if abs(f1) < 1e-12:   #converged (a small step alone can be a stall, where nu barely changes with x)
      return x1
    if f1 > 0:
      lo, flo = x1, f1
      step = 0.25
      while True:
        hi = min(lo + step, 700.0)
        fhi = miss(hi) if hi < 700 else -nu
        if fhi <= 0:
          break
        lo, flo, step = hi, fhi, step*4
    else:
      hi, fhi = x1, f1
      step = 0.25
      while True:
        lo = hi - step
        flo = miss(lo)
        if flo > 0 or lo < -700:
          break
        hi, fhi, step = lo, flo, step*4
    side = 0
    x = (lo + hi)/2
    for _ in range(300):
      x = (lo*fhi - hi*flo)/(fhi - flo)
      if not lo < x < hi:
        x = (lo + hi)/2
      f = miss(x)
      if f == 0:
        break
      if f > 0:
        lo, flo = x, f
        if side == 1:
          fhi /= 2
        side = 1
      else:
        hi, fhi = x, f
        if side == -1:
          flo /= 2
        side = -1
      if hi - lo < 1e-14*max(1.0, abs(x)):
        break
    return x

  def solve(self, pos):
    """(unit direction of the flow, S) at pos, from this body's paths"""
    key = (float(pos[0]), float(pos[1]))
    if self.last is not None and self.last[0] == key:
      return self.last[1]
    mu, nu, half, below = self.coordinates(pos)
    Smu, Snu, S = self.path(mu, nu)
    grad = complex(Smu, Snu)*cmath.sinh(2*half)  #proportional to S_x + i S_y, in the local axes
    gx, gy = grad.real, (-grad.imag if below else grad.imag)
    g = gx*self.ex + gy*self.ey
    size = float(np.hypot(g[0], g[1]))
    if size == 0:                                #at the source itself
      g, size = np.array([1.0, 0.0]), 1.0
    result = (self.sign*g/size, S)
    self.last = (key, result)
    return result


class TwoCentreField:

  def __init__(self, bodies):
    self.bodies = list(bodies)
    if len(self.bodies) != 2:
      raise ValueError('the exact eikonal flow is for two bodies (%d given): use the rays (engine/eikonal.py)'
                       % len(self.bodies))
    self.pos = np.array([b.pos for b in self.bodies])
    self.GM = np.array([b.GM for b in self.bodies])
    self.sources = [Source(self.bodies[0], self.bodies[1]), Source(self.bodies[1], self.bodies[0])]
    self.offsets = [0.0, 0.0]
    saddle = self.saddle(0, 1)
    self.offsets[1] = self.action(saddle, 0) - self.action(saddle, 1)

  def saddle(self, i, j):
    """the point between bodies i and j where g is 0: d from i, with GM_i/d^2 = GM_j/(D - d)^2"""
    q = math.sqrt(self.GM[i]/self.GM[j])
    return self.pos[i] + q/(1 + q)*(self.pos[j] - self.pos[i])

  def action(self, pos, i):
    """body i's S at pos - the integral of |u| along its zero-energy path from the body - with its constant"""
    return self.sources[i].solve(pos)[1] + self.offsets[i]

  def region(self, pos):
    """index of the body whose region pos is in: the one whose S there is smallest"""
    return 0 if self.action(pos, 0) <= self.action(pos, 1) else 1

  def direction(self, pos, region=None):
    """the unit direction of the flow at pos, back down region's path through pos (by default the region pos is in)"""
    i = self.region(pos) if region is None else region
    return self.sources[i].solve(pos)[0]
