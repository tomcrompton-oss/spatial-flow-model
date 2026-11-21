"""
spacetimes past the flow model's: a lapse and a curved space as well as a flow - GR's 3+1 (ADM) form,

  ds^2 = -N^2 c^2 dt^2 + gamma_ij (dx^i - u^i dt)(dx^j - u^j dt)

  N      the lapse: how fast the clocks of observers moving with the flow tick, per unit of t. the flow model has
         N = 1 (they are in free fall, and every clock's slowing is its speed through space)
  u      the flow: those observers' velocity through the coordinates (GR's shift is -u)
  gamma  the metric of space at each t. the flow model's is flat

a Spacetime gives N - 1 (lapseOffset), u (flow) and gamma - delta (space: None for flat), as functions of place and
time - each kept as its difference from the flat, unflowing value, so nothing is lost in rounding against c^2.
MetricCalculator moves particles along its paths by Hamilton's equations on the momentum p_i (per unit mass, m/s;
for light any length):

  H = N c sqrt(c^2 + |p|^2) + u . p        (light: N c |p| + u . p),   |p|^2 = gamma^ij p_i p_j
  dx/dt = dH/dp = N c gamma^-1 p / sqrt(c^2 + |p|^2) + u,    dp/dt = -dH/dx,    dtau/dt = N c/sqrt(c^2 + |p|^2)

by the midpoint rule (as engine/flow.py's momentum step, which this is with N = 1 and flat space), dH/dx by
fourth-order centred differences of H at fixed p, less the part c sqrt(c^2 + p.p) that doesn't change with x. H is the energy -p_t, kept
when the spacetime is steady; x cross p about a body is kept when it looks the same turned about it

the spacetimes:
  FlowSpacetime        any flow calculator's flow (engine/flow.py: one body, vectors, along g, eikonal, turning,
                       waves), with a lapse and a curved space added - its own functions, or the two shares below
  IsotropicSchwarzschild  one body in isotropic coordinates: N = (1 - m/2r)/(1 + m/2r), gamma = (1 + m/2r)^4 delta, no
                       flow - the same spacetime as the one-body flow, in other coordinates (a check of the engine)
  PostNewtonian        GR's first post-Newtonian metric of bodies moving on given paths (harmonic coordinates): the
                       reference the multi-body models are measured against

FlowSpacetime's transverse space, for any flow, keeping N = 1 (the clocks still slowed only by their speed through
space): GR's static metric sliced by the proper time of observers falling from rest far away has, to first order,
N = 1, a flow along their way u, and space curved across it - gamma = (1 + 2 Phi/c^2) delta - (2 Phi/c^2) n n, n along
u - with |u|^2 = 2 Phi (1 - Phi/c^2) for g_tt's Phi^2 (slower; GR's beta). for one body that is flat space in other
coordinates; with more, it holds the bodies' cross terms

FlowSpacetime's shares, for any flow (Phi = sum GM/d, the bodies where they are at t):
  lapse    lambda: N^2 = 1 - 2 lambda Phi/c^2 + (a Phi^2 term, GR's beta), the flow scaled by sqrt(1 - lambda) - so
           -g_tt = N^2 c^2 - |u|^2 is the same for any lambda (Newton's g is kept for the squares rule), and lambda of
           gravity is in the clocks. with it come lambda of GR's moving-body and cross terms (PostNewtonian's psi in
           the lapse, its vector potential 4 U_j/c^2 in the flow), so lambda = kappa = 1 is GR's 1PN metric exactly
  curve    kappa: gamma = (1 + 2 kappa Phi/c^2) delta, space curved as GR's harmonic coordinates have it at kappa = 1
"""
import math
import numpy as np
from engine.constants import C
from engine.flow import Calculator, Particle, turn
from engine.vectors import length

ZERO = np.zeros(2)


def potential(bodies, x, t):
  """Newton's potential, sum GM/d (> 0), the bodies where they are at t"""
  return sum(b.GM/length(x - b.at(t)) for b in bodies)


class Spacetime:
  """a spacetime in the 3+1 form (see the module notes): flat, at rest, unless a subclass says otherwise"""
  bodies = []
  static = True      #nothing changes with t: H, the energy, is kept
  centre = None      #a point it looks the same turned about: x cross p about it is kept
  omega = None       #steady in a frame turning at omega about the origin: H - omega L is kept

  def lapseOffset(self, x, t):
    """N - 1"""
    return 0.0

  def flow(self, x, t, region=None):
    return ZERO

  def space(self, x, t, region=None):
    """gamma - delta (a 2 x 2 array), or None for flat space (region: the side of any seam, as for the flow)"""
    return None

  def region(self, x, t):
    """the side of any seam x is on (as engine/flow.py's), or None"""
    return None

  def seamVelocity(self, x):
    return ZERO

  def describe(self):
    return type(self).__name__

  #---- what the mover needs, from those three

  def parts(self, x, t, region):
    """N - 1, u, and gamma's inverse less delta (None for flat)"""
    a, u, h = self.lapseOffset(x, t), self.flow(x, t, region), self.space(x, t, region)
    if h is None:
      return a, u, None
    return a, u, np.linalg.inv(np.eye(2) + h) - np.eye(2)

  @staticmethod
  def norm2(p, k):
    """|p|^2 = gamma^ij p_i p_j, and its difference from p . p (k = gamma^-1 - delta, or None)"""
    flat = p @ p
    extra = 0.0 if k is None else p @ k @ p
    return flat + extra, extra

  def reduced(self, x, p, t, light, region):
    """H less its part that doesn't change with x (c sqrt(c^2 + p . p), or c |p| for light), worked from small parts"""
    a, u, k = self.parts(x, t, region)
    pp, extra = self.norm2(p, k)
    flat = p @ p
    if light:
      root, root0 = math.sqrt(pp), math.sqrt(flat)
    else:
      root, root0 = math.sqrt(C*C + pp), math.sqrt(C*C + flat)
    return a*C*root + C*extra/(root + root0) + u @ p

  def velocity(self, x, p, t, light, region):
    """dx/dt = dH/dp"""
    a, u, k = self.parts(x, t, region)
    pp, _ = self.norm2(p, k)
    kp = p if k is None else p + k @ p
    return (1 + a)*C*kp/(math.sqrt(pp) if light else math.sqrt(C*C + pp)) + u

  def force(self, x, p, t, light, region, nearest):
    """
    dp/dt = -dH/dx, by fourth-order centred differences 10^-3 of the distance to the nearest body across: H holds the
    potential energy (9 x 10^8 J/kg from the Sun at 1 AU) to a part in 10^16, so a narrower difference loses the
    relativistic part to rounding, and a second-order one this wide its error (10^-6 of g)
    """
    h = 1e-3*nearest
    out = np.zeros(2)
    H = lambda y: self.reduced(y, p, t, light, region)
    for i in range(2):
      e = np.zeros(2)
      e[i] = h
      out[i] = -(8*(H(x + e) - H(x - e)) - (H(x + 2*e) - H(x - 2*e)))/(12*h)
    return out

  def energy(self, x, p, t, light, region):
    """H, less the rest energy c^2 for a particle (light: H itself)"""
    flat = p @ p
    rest = C*flat/(math.sqrt(flat) + 0.0) if light else C*flat/(math.sqrt(C*C + flat) + C)
    return self.reduced(x, p, t, light, region) + rest

  def rate(self, x, p, t, region):
    """a particle's dtau/dt: N c/sqrt(c^2 + |p|^2)"""
    a, u, k = self.parts(x, t, region)
    pp, _ = self.norm2(p, k)
    return (1 + a)*C/math.sqrt(C*C + pp)

  def momentum(self, x, v, t, region):
    """
    the momentum of a particle moving at v: with w = v - u, gamma w is along p, and |w|_gamma = N c |p|/sqrt(c^2 +
    |p|^2), so p = gamma w c/sqrt(N^2 c^2 - |w|^2_gamma)
    """
    a, u, _ = self.parts(x, t, region)
    w = v - u
    h = self.space(x, t, region)
    gw = w if h is None else w + h @ w
    W = w @ gw
    N = 1 + a
    return gw*C/math.sqrt(N*N*C*C - W)

  def lightMomentum(self, x, n, t, region):
    """light going the way of the unit vector n (its coordinate velocity), and its velocity: |v - u|_gamma = N c"""
    a, u, _ = self.parts(x, t, region)
    h = self.space(x, t, region)
    g = np.eye(2) if h is None else np.eye(2) + h
    N = 1 + a
    #|s n - u|^2_gamma = N^2 c^2:  s^2 (n g n) - 2 s (n g u) + (u g u) - N^2 c^2 = 0, the root ahead
    A, B, D = n @ g @ n, n @ g @ u, u @ g @ u - N*N*C*C
    s = (B + math.sqrt(B*B - A*D))/A
    v = s*n
    return g @ (v - u), v


class FlowSpacetime(Spacetime):
  """
  a flow calculator's flow (engine/flow.py Calculator, any rule), with a lapse and a curved space: lapse and space
  are functions (x, t) -> N - 1 and -> gamma - delta, or the shares share (lambda) and curve (kappa) of the module
  notes set them from Newton's potential. with neither it is the flow model itself
  """

  def __init__(self, calc, lapse=None, space=None, share=0.0, curve=0.0, transverse=False, slower=True):
    """transverse: True, space stretched across the flow by 2 Phi/c^2 (GR's static metric sliced by free fall);
    'flow', by the flow's own |u|^2/c^2 - the same for the eikonal flow, where |u|^2 = 2 Phi, and set by the flow
    alone for any other; 'source', by the flow relative to the body whose flow it is (u - that body's velocity), which
    a uniform change of frame leaves alone, where 'flow' does not"""
    self.calc = calc
    self.bodies = calc.bodies
    self.lapseFn, self.spaceFn = lapse, space
    self.share, self.curve = share, curve
    self.transverse, self.slower = transverse, slower   #the clocks left alone, space curved across the flow
    self.flowScale = math.sqrt(1 - share)
    self.pn = PostNewtonian(self.bodies) if share else None   #GR's moving-body and cross terms, lambda of them
    self.omega = getattr(calc, 'omega', None) if calc.combine == 'turning' else None
    self.static = not calc.moving and calc.wave is None
    self.centre = self.bodies[0].pos if len(self.bodies) == 1 and self.static else None

  def describe(self):
    extra = []
    if self.share:
      extra.append('lapse share %g' % self.share)
    if self.curve:
      extra.append('curved space %g' % self.curve)
    if self.transverse == 'source':
      extra.append('space curved across the flow by its speed relative to its body')
    elif self.transverse == 'flow':
      extra.append('space curved across the flow by its own speed, (|u|^2 delta - u u)/c^2'
                   + (', the flow slowed by sqrt(1 - |u|^2/2c^2)' if self.slower else ''))
    elif self.transverse:
      extra.append('space curved across the flow' + (', the flow slowed by sqrt(1 - Phi/c^2)' if self.slower else ''))
    if self.lapseFn:
      extra.append('its own lapse')
    if self.spaceFn:
      extra.append('its own space')
    return 'the flow of %r%s' % (self.calc, (', ' + ', '.join(extra)) if extra else '')

  def lapseOffset(self, x, t):
    a = self.lapseFn(x, t) if self.lapseFn else 0.0
    if self.share:
      U, _, psi = self.pn.terms(x, t)
      U /= C**2
      #N^2 = 1 - s; the U^2 term makes g_tt's own 2 lambda U^2 once |u|^2_gamma's U^2 part (from curved space) is in;
      #psi is GR's lapse's moving-body and cross terms (PostNewtonian), so that lambda = kappa = 1 is its metric
      s = 2*self.share*U - 2*(self.share + 2*self.curve*(1 - self.share))*U*U + 2*self.share*psi/C**4
      a += -s/(1 + math.sqrt(1 - s))   #sqrt(1 - s) - 1
    return a

  def flow(self, x, t, region=None):
    u = self.calc.flow(x, region, t)
    if self.transverse in ('flow', 'source') and self.slower:
      s = u - self.sourceVelocity(x, t, region) if self.transverse == 'source' else u
      u = u - s*(1 - math.sqrt(1 - (s @ s)/(2*C*C)))   #the same, with the flow's own u^2/2 for Phi
    elif self.transverse and self.slower:
      u = u*math.sqrt(1 - potential(self.bodies, x, t)/C**2)   #|u|^2 = 2 Phi (1 - Phi/c^2): g_tt's Phi^2, GR's beta
    if not self.share:
      return u
    return u*self.flowScale + self.share*self.pn.flow(x, t)   #and lambda of GR's vector potential, 4 U_j/c^2

  def space(self, x, t, region=None):
    h = self.spaceFn(x, t) if self.spaceFn else None
    if self.transverse:
      u = self.calc.flow(x, self.calc.region(x, t) if region is None else region, t)
      if self.transverse == 'source':
        u = u - self.sourceVelocity(x, t, self.calc.region(x, t) if region is None else region)
      if self.transverse in ('flow', 'source'):
        k = ((u @ u)*np.eye(2) - np.outer(u, u))/C**2   #decided by the flow alone: its speed, and its direction
      else:
        n = u/length(u)
        k = 2*potential(self.bodies, x, t)/C**2*(np.eye(2) - np.outer(n, n))
      h = k if h is None else h + k
    if self.curve:
      k = 2*self.curve*potential(self.bodies, x, t)/C**2*np.eye(2)
      h = k if h is None else h + k
    return h

  def region(self, x, t):
    return self.calc.region(x, t)

  def seamVelocity(self, x):
    return self.calc.seamVelocity(x)

  def sourceVelocity(self, x, t, region):
    """the velocity of the body whose flow x is in (its region; else the nearest body)"""
    if region is None:
      region = int(np.argmin([length(x - b.at(t)) for b in self.bodies]))
    return bodyVelocityAt(self.bodies[region], t)


class IsotropicSchwarzschild(Spacetime):
  """one body in isotropic coordinates (see the module notes): no flow, the lapse and the curved space carry it all"""

  def __init__(self, body):
    self.bodies = [body]
    self.m = body.GM/C**2
    self.centre = body.pos

  def lapseOffset(self, x, t):
    q = self.m/(2*length(x - self.bodies[0].pos))
    return -2*q/(1 + q)   #(1 - q)/(1 + q) - 1

  def space(self, x, t, region=None):
    q = self.m/(2*length(x - self.bodies[0].pos))
    return ((1 + q)**4 - 1)*np.eye(2)

  def radius(self, x):
    """Schwarzschild's r at isotropic x: rho (1 + m/2 rho)^2"""
    rho = length(x - self.bodies[0].pos)
    return rho*(1 + self.m/(2*rho))**2


def bodyAcceleration(b, t):
  """a body's acceleration on its path: going round the origin, -Omega^2 x; a body moved step by step (engine/carried.py
  Proxy), its path's; on a straight line, 0"""
  if hasattr(b, 'pathAccelerationAt'):
    return b.pathAccelerationAt(t)
  if getattr(b, 'circling', 0.0):
    return -b.circling**2*b.at(t)
  return ZERO


def bodyVelocityAt(b, t):
  if hasattr(b, 'pathVelocityAt'):
    return b.pathVelocityAt(t)
  if getattr(b, 'circling', 0.0):
    x = b.at(t)
    return b.circling*np.array([-x[1], x[0]])
  return b.velocity


class PostNewtonian(Spacetime):
  """
  GR's first post-Newtonian metric of point bodies on given paths, harmonic coordinates (Poisson & Will, Gravity,
  ch. 7-9):
    g_tt = -c^2 + 2U + 2(psi - U^2)/c^2,  g_tj = -4 U_j/c^2,  g_jk = (1 + 2U/c^2) delta_jk
    U = sum GM/r,  U_j = sum GM v_j/r,  psi = sum (GM/r)(3 v^2/2 - sum_others GM'/r') + (1/2) d^2/dt^2 sum GM r
  (r from each body; d^2 r/dt^2 = (v^2 - (n . v)^2)/r - n . a, n from the body). in the 3+1 form: gamma u = 4 U_j/c^2
  (gamma's lowering), N^2 c^2 = -g_tt + |u|^2_gamma. a test particle's paths are EIH's with its mass 0
  """

  def __init__(self, bodies):
    self.bodies = list(bodies)
    self.static = not any(b.moving for b in self.bodies)
    self.centre = self.bodies[0].pos if len(self.bodies) == 1 and self.static else None
    circling = set(getattr(b, 'circling', 0.0) for b in self.bodies)
    if len(circling) == 1 and 0.0 not in circling:
      self.omega = circling.pop()
      self.static = False

  def terms(self, x, t):
    U, Uj, psi = 0.0, np.zeros(2), 0.0
    places = [b.at(t) for b in self.bodies]
    for i, b in enumerate(self.bodies):
      d = x - places[i]
      r = length(d)
      n = d/r
      v, acc = bodyVelocityAt(b, t), bodyAcceleration(b, t)
      others = sum(o.GM/length(places[i] - places[j]) for j, o in enumerate(self.bodies) if j != i)
      U += b.GM/r
      Uj = Uj + b.GM*v/r
      psi += b.GM/r*(1.5*(v @ v) - others) + 0.5*b.GM*((v @ v - (n @ v)**2)/r - n @ acc)
    return U, Uj, psi

  def lapseOffset(self, x, t):
    U, Uj, psi = self.terms(x, t)
    #N^2 = 1 - 2U/c^2 - 2(psi - U^2)/c^4 + |u|^2/c^2, |u|^2 = 16 U_j^2/c^4 (to this order)
    s = 2*U/C**2 + 2*(psi - U*U)/C**4 - 16*(Uj @ Uj)/C**6
    return -s/(1 + math.sqrt(1 - s))

  def flow(self, x, t, region=None):
    U, Uj, _ = self.terms(x, t)
    return 4*Uj/C**2/(1 + 2*U/C**2)

  def space(self, x, t, region=None):
    U = sum(b.GM/length(x - b.at(t)) for b in self.bodies)
    return 2*U/C**2*np.eye(2)


class SlicedPN(Spacetime):
  """
  GR's first post-Newtonian metric (PostNewtonian) in a moving time, exactly: t = T + phi(x, T)/c^2 with

    phi = V . d - 2 sqrt(2 GM r)        d = x - X, r = |d|, X and V a body's place and velocity at T

  the body's river carried at its velocity: grad phi = V - sqrt(2GM/r) n, its rate phi_T = A . d - V^2 + sqrt(2GM/r)
  n . V from the body's motion alone (A its acceleration). nothing is assumed of phi (it need not solve Newton's
  equation, as engine/carried.py FreeFallPN's must): the metric g' = J^T g J (J = dt/d(T, x)) is turned back into the
  3+1 form, each part kept as its offset from flat so nothing rounds against c^2,

    gamma' - delta = h - (1 + m) grad phi grad phi/c^2 - (grad phi (gamma w) + (gamma w) grad phi)/c^2
    gamma' u'      = A [(1 + m) grad phi + gamma w]        A = 1 + phi_T/c^2
    N'^2 - 1       = (A^2 - 1) + A^2 m + u' . gamma' u'/c^2

  (h, w and N the harmonic metric's space, flow and lapse at the point's harmonic time T + phi/c^2, m = N^2 - 1 -
  w . gamma w/c^2). the flow is the river at the body's velocity, about 30 km/s for the Earth, and Newton's gravity of
  everything else is in the lapse. GR, so in the studies a check of the engine and the mapping with a flow the
  moving-body models' size (the time at the body is T: phi is 0 there, so its clock and path keep T)
  """

  def __init__(self, bodies, around=1):
    self.bodies = list(bodies)
    self.pn = PostNewtonian(self.bodies)
    self.around = around
    self.static = False

  def describe(self):
    return "GR's 1PN metric in the time of the river carried with body %d" % self.around

  def potential(self, x, t):
    """phi, grad phi, phi_T"""
    b = self.bodies[self.around]
    d = x - b.at(t)
    r = length(d)
    n = d/r
    V, A = bodyVelocityAt(b, t), bodyAcceleration(b, t)
    s = math.sqrt(2*b.GM/r)
    return V @ d - 2*s*r, V - s*n, A @ d - V @ V + s*(n @ V)

  def pieces(self, x, t):
    """u, gamma - delta, N^2 - 1, and gamma^-1 - delta"""
    phi, grad, phiT = self.potential(x, t)
    th = t + phi/C**2
    o = self.pn.lapseOffset(x, th)
    w = self.pn.flow(x, th)
    h = self.pn.space(x, th)
    gw = w + h @ w
    m = 2*o + o*o - (w @ gw)/C**2
    K = h - (1 + m)*np.outer(grad, grad)/C**2 - (np.outer(grad, gw) + np.outer(gw, grad))/C**2
    a0 = phiT/C**2
    A = 1 + a0
    gu = A*((1 + m)*grad + gw)
    inv = np.eye(2) - K + K @ K
    u = inv @ gu
    s = (2*a0 + a0*a0) + A*A*m + (gu @ u)/C**2
    return u, K, s, inv - np.eye(2)

  def parts(self, x, t, region=None):
    """N - 1, u, gamma^-1 - delta (the base class's form, for the Hamiltonian)"""
    u, K, s, k = self.pieces(x, t)
    return s/(1 + math.sqrt(1 + s)), u, k

  def lapseOffset(self, x, t):
    return self.parts(x, t)[0]

  def flow(self, x, t, region=None):
    return self.pieces(x, t)[0]

  def space(self, x, t, region=None):
    return self.pieces(x, t)[1]


class MetricCalculator(Calculator):
  """
  particles on a Spacetime's paths (see the module notes): the midpoint rule on Hamilton's equations, from the side of
  any seam the step starts on; across a seam the momentum along it is kept and the energy H (as engine/flow.py's
  crossSeam). p.q is the momentum, p.v the velocity, p.u the flow there and p.w = v - u, for the step sizes and logs
  """
  runspeed = 8000

  def __init__(self, spacetime):
    super().__init__(spacetime.bodies or [], direction='g' if len(spacetime.bodies) > 1 else None)
    self.spacetime = spacetime

  def __repr__(self):
    return '<metric.MetricCalculator object: %s>' % self.spacetime.describe()

  def flow(self, pos, region=None, t=0.0):
    return self.spacetime.flow(pos, t, region)

  def region(self, pos, t=0.0):
    return self.spacetime.region(pos, t)

  def seamVelocity(self, pos):
    return self.spacetime.seamVelocity(pos)

  def nearestScale(self, x, t):
    return self.nearest(x, t) if self.bodies else max(1.0, float(np.max(np.abs(x))))

  def keep(self, p):
    side = self.sideOf(p)
    p.v = self.spacetime.velocity(p.pos, p.q, p.t, p.light, side)
    p.u = self.spacetime.flow(p.pos, p.t, side)
    p.w = p.v - p.u

  def initPV(self, p, v):
    """start moving at v"""
    p.light = False
    p.q = self.spacetime.momentum(p.pos, np.array(v, dtype=float), p.t, self.sideOf(p))
    self.keep(p)

  def initLight(self, p, n):
    """light leaving the way the unit vector n points (its velocity through the coordinates)"""
    p.light = True
    p.q, _ = self.spacetime.lightMomentum(p.pos, np.array(n, dtype=float), p.t, self.sideOf(p))
    self.keep(p)

  def initPW(self, p, w):
    """start at w relative to the flow; |w| = c is light, the way w points"""
    w = np.array(w, dtype=float)
    if abs(length(w) - C) < 1e-9*C:
      u = self.spacetime.flow(p.pos, p.t, self.sideOf(p))
      self.initLight(p, (w + u)/length(w + u))
    else:
      self.initPV(p, w + self.spacetime.flow(p.pos, p.t, self.sideOf(p)))

  def initPFreefall(self, p):
    self.initPV(p, self.spacetime.flow(p.pos, p.t, self.sideOf(p)))

  def move(self, p, dt):
    self.seamStep(p, dt, self.step)

  def step(self, p, dt):
    S, side, light = self.spacetime, self.sideOf(p), p.light
    x, q, t = p.pos, p.q, p.t
    middle = t + dt/2
    xm = x + S.velocity(x, q, t, light, side)*dt/2
    qm = q + S.force(x, q, t, light, side, self.nearestScale(x, t))*dt/2
    vm = S.velocity(xm, qm, middle, light, side)
    p.q = q + S.force(xm, qm, middle, light, side, self.nearestScale(xm, middle))*dt
    if not light:
      p.pt += dt*S.rate(xm, qm, middle, side)
    p.pos = x + vm*dt
    p.d += length(vm*dt)
    p.t = t + dt
    self.keep(p)

  def crossSeam(self, p, before):
    """across a seam (seamStep): the momentum along it kept, the momentum across it changed to keep H"""
    after = self.region(p.pos, p.t)
    if after == before:
      return
    p.region = after
    S = self.spacetime
    jump = S.flow(p.pos, p.t, before) - S.flow(p.pos, p.t, after)
    if not jump.any():
      return
    #across the seam: the jump's direction, where the seam is where the two sides' speeds are equal; else its own
    n = S.seamNormal(p.pos, p.t) if hasattr(S, 'seamNormal') else jump/length(jump)
    moving = S.seamVelocity(p.pos, p.t) if getattr(S, 'timedSeams', False) else self.seamVelocity(p.pos)
    #in the seam's own frame H' = H - moving . p is what is kept
    keepH = lambda q, side: S.reduced(p.pos, q, p.t, p.light, side) - moving @ q + (C*length(q) if p.light else
                                                                                       C*math.sqrt(C*C + q @ q))
    target = keepH(p.q, before)
    along, x = p.q - (p.q @ n)*n, p.q @ n
    for _ in range(30):
      q = along + x*n
      miss = keepH(q, after) - target
      slope = (S.velocity(p.pos, q, p.t, p.light, after) - moving) @ n
      x -= miss/slope
      if abs(miss) <= 1e-15*abs(target):
        break
    p.q = along + x*n
    self.keep(p)

  def conserved(self, p):
    """the energy H (less the rest energy), x cross p about a body, H - omega L, by the spacetime's symmetries;
    light: its impact parameter c L/H"""
    S, side = self.spacetime, self.sideOf(p)
    E = S.energy(p.pos, p.q, p.t, p.light, side)
    if p.light:
      if S.centre is None:
        return {}
      x = p.pos - S.centre
      return {'b': C*(x[0]*p.q[1] - x[1]*p.q[0])/E}
    out = {}
    if S.static:
      out['E'] = E
    if S.centre is not None:
      x = p.pos - S.centre
      out['L'] = x[0]*p.q[1] - x[1]*p.q[0]
    if S.omega is not None:
      out['J'] = E - S.omega*(p.pos[0]*p.q[1] - p.pos[1]*p.q[0])
    return out
