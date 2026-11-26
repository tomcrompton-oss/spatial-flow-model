"""
the carried flow: each body's own river carried at the body's velocity, with the other bodies' tides in it - a flow
for any number of bodies moving any way (engine/metric.py's Spacetime, so the lapse is 1 and it is run by
MetricCalculator), and the bodies moved by it

regions: x is in body k's region where its GM/d^3 is the largest - where its own pull beats the others' tides (for
the Sun and the Earth, out to 2.2 x 10^9 m from the Earth, past its Hill sphere; for equal masses, the nearer one)

the flow in k's region, in k's free-falling frame (moving at V_k, falling at the others' g at the body): the body's
river s_k = -sqrt(2 GM_k/r) r^ and the others' tide carried in along it. the flow has no curl, u = grad phi, and keeps
Bernoulli's equation d phi/dt + |u|^2/2 = Phi + f(t) (space falls at g) when, to first order in the tide,

  s_k . grad sigma = Phi_T,   Phi_T(x) = Phi_others(x) - Phi_others(x_k) - (x - x_k) . g_others(x_k)

so sigma, zero at the body, is the integral of -Phi_T/|s_k| out along the radius, and u = V_k + s_k + grad sigma.
left out: the tide's square (|grad sigma|^2/2) and its change while space falls in (d sigma/dt): about 1% and 5% of the
tide's flow at the Moon's distance from the Earth. so Newton is only approximate, and the studies take a model's
relativistic part as its run at c less its run at c x 1000 (studies/lapse_moon.py differenced). that takes out the
Newtonian error, not its product with the relativistic terms: 0.7 m on the Moon in 90 days. tides='transported'
keeps d sigma/dt, exactly (the tide taken where the falling space will be when it passes each radius: transported),
and the square from the first order's gradient: Newton's equation is then met to 0.1% of the tide at the Moon

transverse 'gr': space as Einstein's Hamiltonian constraint has it for any flow with no curl, gamma = delta + (2 Phi
delta - u u)/c^2 (Phi = sum GM/d, u the lab's flow; studies/constraints.py), the flow relative to its body slowed as
for 'source'

transverse 'source': space curved across the flow relative to its body, by its own speed (engine/metric.py
FlowSpacetime), w = u - V_k: gamma = delta + (|w|^2 delta - w w)/c^2, w slowed by sqrt(1 - |w|^2/2c^2)

the bodies moved by it (CarriedBodies): each body moves as a test particle (MetricCalculator's step on its momentum)
in the carried flow of the others, its own left out (and of any bodies held fixed) - for two bodies, the other's river carried at its velocity,
which is that body's Schwarzschild field in a frame moving with it: Newton exactly
"""
import math
import numpy as np
from engine.constants import *
from engine.flow import Body, Particle
from engine.metric import Spacetime, MetricCalculator, bodyVelocityAt, bodyAcceleration

NODES, WEIGHTS = np.polynomial.legendre.leggauss(12)


def velocityOf(b, t):
  """the velocity a body's flow is carried at (a Proxy's: see there)"""
  return b.velocityAt(t) if hasattr(b, 'velocityAt') else bodyVelocityAt(b, t)


def accelerationOf(b, t):
  return b.accelerationAt(t) if hasattr(b, 'accelerationAt') else bodyAcceleration(b, t)


def placesAt(b, times):
  """a body's places at many times at once (m x 2): circling, moving straight, a Proxy's parabola, or one by one"""
  times = np.asarray(times, float)
  if isinstance(b, Proxy):
    q = (times - b.t0)[:, None]
    return b.x0 + b.v0*q + 0.5*b.a0*q*q
  if getattr(b, 'circling', 0.0):
    a = b.circling*times
    c, s = np.cos(a), np.sin(a)
    return np.stack([c*b.pos[0] - s*b.pos[1], s*b.pos[0] + c*b.pos[1]], axis=1)
  if not getattr(b, 'moving', False):
    return np.tile(b.pos, (len(times), 1))
  return np.array([b.at(t) for t in times])


class CarriedSpacetime(Spacetime):

  timedSeams = True

  def __init__(self, bodies, transverse=False, slower=True, tides=True):
    self.bodies = list(bodies)
    self.transverse, self.slower, self.tides = transverse, slower, tides
    self.static = False
    self.centre = None

  def describe(self):
    return 'the carried flow of %d bodies%s%s' % (len(self.bodies), '' if self.tides else ', no tides',
                                                ', space curved across the flow relative to its body' if self.transverse else '')

  def region(self, x, t):
    if len(self.bodies) == 1:
      return 0
    return int(np.argmax([b.GM/length(x - b.at(t))**3 for b in self.bodies]))

  def others(self, k, y, t):
    """the other bodies' potential and g at y"""
    phi, g = 0.0, np.zeros(2)
    for j, b in enumerate(self.bodies):
      if j != k:
        d = b.at(t) - y
        r = length(d)
        phi += b.GM/r
        g = g + b.GM*d/r**3
    return phi, g

  def tidalFlow(self, k, x, t):
    """grad sigma: the others' tide carried in along body k's river (see the module notes)"""
    if not self.tides or len(self.bodies) == 1:
      return np.zeros(2)
    xk = self.bodies[k].at(t)
    d = x - xk
    r = length(d)
    n = d/r
    side = np.array([-n[1], n[0]])
    others = [(b.GM, b.at(t)) for j, b in enumerate(self.bodies) if j != k]
    #the others' potential at x and at the body, and their g at the body and at the quadrature's points along the radius
    rr = r*(NODES + 1)/2
    ys = xk + np.outer(rr, n)
    phiX, phi0, g0, gYs = 0.0, 0.0, np.zeros(2), np.zeros((len(rr), 2))
    for GM, xb in others:
      dx, d0 = xb - x, xb - xk
      phiX += GM/length(dx)
      phi0 += GM/length(d0)
      g0 = g0 + GM*d0/length(d0)**3
      dy = xb - ys
      gYs += GM*dy/np.linalg.norm(dy, axis=1)[:, None]**3
    PhiT = phiX - phi0 - d @ g0
    GMk = self.bodies[k].GM
    radial = -PhiT/math.sqrt(2*GMk/r)
    #(1/r) d sigma/d theta = -(1/r) integral over r' < r of r' side . grad Phi_T / s(r'), s(r') = sqrt(2GM/r')
    total = np.sum(WEIGHTS*r/2*rr*((gYs - g0) @ side)/np.sqrt(2*GMk/rr))
    return radial*n - total/r*side

  def tidalPotential(self, k, D, times):
    """
    Phi_T at the offsets D (m x 2) from body k, each at its own time: the others' potential less its value and slope
    at the body, worked without cancelling the potential itself (9 x 10^8 from the Sun at 1 AU, against a tide of
    10^4): with e the other body's place from k and q = |e - D|, R = |e|,
      1/q - 1/R - e . D/R^3 = (2 e . D - D^2)/(q R (q + R)) - e . D/R^3
    """
    out = np.zeros(len(D))
    xk = placesAt(self.bodies[k], times)
    for j, b in enumerate(self.bodies):
      if j != k:
        e = placesAt(b, times) - xk
        R = np.linalg.norm(e, axis=1)
        q = np.linalg.norm(e - D, axis=1)
        eD = np.sum(e*D, axis=1)
        out += b.GM*((2*eD - np.sum(D*D, axis=1))/(q*R*(q + R)) - eD/R**3)
    return out

  def transported(self, k, D, t):
    """
    sigma at the points D (m x 2, from body k) with the tide's change: s . grad sigma + d sigma/dt = Phi_T (d/dt at
    fixed place from the body) is carried along the river's paths, falling straight in at s(r) = sqrt(2 GM/r) and
    reaching the body (sigma 0) a time f(r) = (2/3) r^(3/2)/sqrt(2 GM) later, so

      sigma(D, t) = -integral over r' < r of Phi_T(r' n, at t + f(r) - f(r'))/s(r') dr'

    the tide where that space will be when it passes r'. exact for this linear part; the square, -|grad sigma|^2/2 in
    the source, is added by squared() (from the first order's gradient: its own change is 10% of a 0.1% part)
    """
    GM = self.bodies[k].GM
    r = np.linalg.norm(D, axis=1)
    rr = r[:, None]*(NODES + 1)/2
    f = lambda q: (2/3)*q**1.5/math.sqrt(2*GM)
    times = (t + f(r)[:, None] - f(rr)).ravel()
    S = self.tidalPotential(k, (rr[..., None]*(D/r[:, None])[:, None, :]).reshape(-1, 2), times).reshape(rr.shape)
    return -np.sum(WEIGHTS*r[:, None]/2*S/np.sqrt(2*GM/rr), axis=1)

  def firstGradients(self, k, P, t):
    """grad sigma at the first order (as tidalFlow), at many points P (m x 2) at once"""
    xk = self.bodies[k].at(t)
    GM = self.bodies[k].GM
    D = P - xk
    r = np.linalg.norm(D, axis=1)
    n = D/r[:, None]
    side = np.stack([-n[:, 1], n[:, 0]], axis=1)
    rr = r[:, None]*(NODES + 1)/2
    Y = xk + rr[..., None]*n[:, None, :]                            #m x nodes x 2
    g0, gY = np.zeros(2), np.zeros(Y.shape)
    PhiT = np.zeros(len(P))
    for j, b in enumerate(self.bodies):
      if j != k:
        z = b.at(t)
        d0 = z - xk
        r0 = length(d0)
        g0 = g0 + b.GM*d0/r0**3
        dY = z - Y
        gY += b.GM*dY/np.linalg.norm(dY, axis=2)[..., None]**3
        PhiT += b.GM/np.linalg.norm(z - P, axis=1) - b.GM/r0 - b.GM*(D @ d0)/r0**3
    radial = -PhiT/np.sqrt(2*GM/r)
    across = np.sum(WEIGHTS*r[:, None]/2*rr*np.sum((gY - g0)*side[:, None, :], axis=2)/np.sqrt(2*GM/rr), axis=1)
    return radial[:, None]*n - (across/r)[:, None]*side

  def squared(self, k, D, t):
    """sigma's part from the tide's square: s . grad sigma = -|grad sigma|^2/2, so +integral of |grad sigma|^2/2s"""
    GM = self.bodies[k].GM
    xk = self.bodies[k].at(t)
    r = np.linalg.norm(D, axis=1)
    rr = r[:, None]*(NODES + 1)/2
    P = (xk + rr[..., None]*(D/r[:, None])[:, None, :]).reshape(-1, 2)
    G1 = self.firstGradients(k, P, t)
    S = (0.5*np.sum(G1*G1, axis=1)).reshape(rr.shape)
    return np.sum(WEIGHTS*r[:, None]/2*S/np.sqrt(2*GM/rr), axis=1)

  def transportedFlow(self, k, x, t):
    """grad sigma (transported), by fourth-order differences"""
    D = x - self.bodies[k].at(t)
    e = 1e-3*length(D)
    steps = np.array([[e, 0], [-e, 0], [2*e, 0], [-2*e, 0], [0, e], [0, -e], [0, 2*e], [0, -2*e]])
    v = self.transported(k, D + steps, t) + self.squared(k, D + steps, t)
    return np.array([8*(v[0] - v[1]) - (v[2] - v[3]), 8*(v[4] - v[5]) - (v[6] - v[7])])/(12*e)

  def ownFlow(self, k, x, t):
    """the flow relative to body k (its river and the tide), in k's region"""
    d = x - self.bodies[k].at(t)
    r = length(d)
    w = -math.sqrt(2*self.bodies[k].GM/r)*d/r
    if self.tides == 'transported' and len(self.bodies) > 1:
      return w + self.transportedFlow(k, x, t)
    return w + self.tidalFlow(k, x, t)

  def flow(self, x, t, region=None):
    k = self.region(x, t) if region is None else region
    w = self.ownFlow(k, x, t)
    if self.transverse and self.slower:
      w = w*math.sqrt(1 - (w @ w)/(2*C*C))
    return velocityOf(self.bodies[k], t) + w

  def space(self, x, t, region=None):
    if not self.transverse:
      return None
    k = self.region(x, t) if region is None else region
    w = self.ownFlow(k, x, t)
    if self.transverse == 'gr':
      #what Einstein's Hamiltonian constraint asks for any flow with no curl (studies/constraints.py): stretched by
      #Newton's potential, contracted along the flow - the lab's flow - by u^2/c^2
      u = velocityOf(self.bodies[k], t) + w
      phi = sum(b.GM/length(x - b.at(t)) for b in self.bodies)
      return (2*phi*np.eye(2) - np.outer(u, u))/C**2
    return ((w @ w)*np.eye(2) - np.outer(w, w))/C**2

  def seamNormal(self, x, t=0.0):
    """the seam's direction across itself at x (engine/metric.py crossSeam: the flow's jump here is not across it,
    as it is for the flows whose seams are where the two sides' speeds are equal)"""
    grad, _ = self.seamGradient(x, t)
    return grad/length(grad)

  def seamVelocity(self, x, t=0.0):
    """the seam's velocity across itself at x: the seam is where ln(GM_a/d_a^3) = ln(GM_b/d_b^3), for the two largest"""
    if len(self.bodies) == 1:
      return np.zeros(2)
    grad, rate = self.seamGradient(x, t)
    return -rate*grad/(grad @ grad)

  def seamGradient(self, x, t):
    """the gradient of the seam's function at x, and its rate of change there"""
    ranks = np.argsort([-b.GM/length(x - b.at(t))**3 for b in self.bodies])[:2]
    def f(y, s):
      a, b = self.bodies[ranks[0]], self.bodies[ranks[1]]
      return 3*math.log(length(y - b.at(s))) - 3*math.log(length(y - a.at(s))) + math.log(a.GM/b.GM)
    h = 1e-6*min(length(x - self.bodies[i].at(t)) for i in ranks)
    grad = np.array([(f(x + e, t) - f(x - e, t))/(2*h) for e in (np.array([h, 0.0]), np.array([0.0, h]))])
    dt = 1.0
    rate = (f(x, t + dt) - f(x, t - dt))/(2*dt)
    return grad, rate


class Proxy(Body):
  """
  a body moved by CarriedBodies, read during a step: its place on a parabola from where the step started (its real
  acceleration, a), and the velocity its flow is carried at - its mean velocity over the step, changing only by
  aFlow, the pull of the bodies in the same spacetime. its real acceleration is partly the pull of the body the
  spacetime leaves out, which must not carry its flow (that body would feel its own pull on this one)
  """

  def __init__(self, mass, x, v, a, aFlow, t0, dt):
    super().__init__(mass, x[0], x[1])
    self.x0, self.v0, self.a0, self.aFlow, self.t0 = (np.array(x, float), np.array(v, float), np.array(a, float),
                                                       np.array(aFlow, float), t0)
    self.vMid, self.tMid = self.v0 + self.a0*dt/2, t0 + dt/2

  def at(self, t):
    s = t - self.t0
    return self.x0 + self.v0*s + 0.5*self.a0*s*s

  def velocityAt(self, t):
    return self.vMid + self.aFlow*(t - self.tMid)

  def accelerationAt(self, t):
    return self.aFlow

  def pathVelocityAt(self, t):
    """its real velocity on its path (for GR's metric of it, engine/metric.py PostNewtonian)"""
    return self.v0 + self.a0*(t - self.t0)

  def pathAccelerationAt(self, t):
    return self.a0

  @property
  def moving(self):
    return True


class CarriedBodies:
  """
  bodies moved by the carried flow: each a test particle in the carried flow of the others (its own left out), all
  stepped together by the midpoint rule from the others' places, velocities and accelerations at the step's start
  (so to second order). masses (kg); places and velocities (m, m/s, arrays of 2)
  """

  def __init__(self, masses, places, velocities, transverse=False, tides=True, fixed=()):
    self.fixed = list(fixed)   #bodies held where they are (engine/flow.py Body), in every spacetime
    self.masses = list(masses)
    self.transverse, self.tides = transverse, tides
    self.t = 0.0
    self.particles = []
    self.acc = [np.zeros(2) for _ in masses]
    for k, (x, v) in enumerate(zip(places, velocities)):
      p = Particle()
      p.pos = np.array(x, float)
      p.v = np.array(velocities[k], float)   #the others' velocities are needed before any momentum is set
      p.t = 0.0
      self.particles.append(p)
    self.acc = self.newtonAccel()
    for k, v in enumerate(velocities):
      self.calc(k).initPV(self.particles[k], np.array(v, float))

  def newtonAccel(self):
    out = []
    for k, p in enumerate(self.particles):
      a = sum((b.GM*(b.pos - p.pos)/length(b.pos - p.pos)**3 for b in self.fixed), np.zeros(2))
      for j, q in enumerate(self.particles):
        if j != k:
          d = q.pos - p.pos
          a = a + G*self.masses[j]*d/length(d)**3
      out.append(a)
    return out

  def proxies(self, k, dt):
    out = []
    for j in range(len(self.masses)):
      if j == k:
        continue
      pull = np.zeros(2)   #Newton's pull on j from the bodies in this spacetime (all but k)
      for i in range(len(self.masses)):
        if i not in (j, k):
          d = self.particles[i].pos - self.particles[j].pos
          pull = pull + G*self.masses[i]*d/length(d)**3
      for b in self.fixed:
        d = b.pos - self.particles[j].pos
        pull = pull + b.GM*d/length(d)**3
      out.append(Proxy(self.masses[j], self.particles[j].pos, self.particles[j].v, self.acc[j], pull, self.t, dt))
    return self.fixed + out

  def calc(self, k, dt=0.0):
    if self.transverse == 'freefall-gr':
      return MetricCalculator(FreeFallPN(self.proxies(k, dt)))
    return MetricCalculator(CarriedSpacetime(self.proxies(k, dt), transverse=self.transverse, tides=self.tides))

  def step(self, dt):
    olds = [(p.pos.copy(), p.v.copy()) for p in self.particles]
    moved = []
    for k, p in enumerate(self.particles):
      calc = self.calc(k, dt)
      q = Particle()
      q.pos, q.t = p.pos.copy(), p.t
      calc.initPV(q, olds[k][1])   #from its velocity: its momentum is relative to the others' flow, which has moved
      calc.move(q, dt)
      moved.append(q)
    for k, q in enumerate(moved):
      self.acc[k] = (q.v - olds[k][1])/dt   #for the next step's parabolas
      self.particles[k] = q
    self.t += dt

  def places(self):
    return [p.pos.copy() for p in self.particles]

  def velocities(self):
    return [p.v.copy() for p in self.particles]


def length(v):
  return math.sqrt(v @ v)


class ChiTable:
  """
  chi round a body going round on a circle (or at rest): the time shift T' = T + chi/c^4 that takes GR's lapse in the
  carried flow's free-fall time to 1. D chi/DT = Q = c^4 (N^2 - 1)/2: chi is Q carried along the flow. the body's
  circle makes the whole system steady in the frame turning with it, where D/DT = w . grad, w = u - Omega x x; so chi
  is worked out once, at T = 0 (transported: each path followed out from r_min, chi 0 there, along w), and turned
  with the body: chi(d, T) = table(R(-omega T) d). (transport='radial' carries it along the body's straight infall
  alone, at s(r) = sqrt(2 GM/r) - which leaves ~10% of the lapse's gradient at the Moon: the turning frame's swirl and
  the tide's flow matter.)

  Q has a V . n s^3 part, so chi has a logarithm at the body, and r_min fixes it (its gradient, the flow's correction,
  is ~GM V/(r c^2)). the table is a Fourier series in angle, each coefficient a natural cubic spline in ln r, so the
  flow's correction - its exact gradient - has no curl. left: 0.1% of the lapse's gradient along the Moon's orbit
  (0.2% at most; finer in r, less)
  """

  def __init__(self, source, k, rmin=1e6, rmax=3e9, radii=384, angles=96, nodes=32, transport='flow'):
    b = source.bodies[k]
    self.body, self.omega = b, getattr(b, 'circling', 0.0) or 0.0
    if getattr(b, 'moving', False) and not self.omega:
      raise ValueError('chi is tabled for a body going round on a circle, or at rest')
    GM = b.GM
    self.rmin, self.rmax = rmin, rmax
    self.us = np.linspace(math.log(rmin), math.log(rmax), radii)
    self.du = self.us[1] - self.us[0]
    thetas = 2*math.pi*np.arange(angles)/angles
    x, w = np.polynomial.legendre.leggauss(nodes)
    f = lambda r: (2/3)*r**1.5/math.sqrt(2*GM)
    values = self.transported(source, k, thetas) if transport == 'flow' else np.zeros((radii, angles))
    for i, u in enumerate(self.us[1:] if transport != 'flow' else [], 1):
      ups = math.log(rmin) + (u - math.log(rmin))*(x + 1)/2   #the nodes in ln r'
      weights = w*(u - math.log(rmin))/2
      rr = np.exp(ups)
      r = math.exp(u)
      times = f(r) - f(rr)
      for j, th in enumerate(thetas):
        n = np.array([math.cos(th), math.sin(th)])
        Q = np.array([C**4*source.parts3(b.at(tt) + q*n, tt, k)[2]/2 for q, tt in zip(rr, times)])
        values[i, j] = -np.sum(weights*Q/np.sqrt(2*GM/rr)*rr)   #dr = r du
    self.angles = angles
    self.coef = np.fft.rfft(values, axis=1)/angles              #chi = sum over m of Re(c_m e^{i m theta}) (x2 for m > 0)
    self.coef[:, 1:] *= 2
    if angles % 2 == 0:
      self.coef[:, -1] /= 2
    self.m = np.arange(self.coef.shape[1])
    self.second = self.spline(self.coef)

  def transported(self, source, k, thetas, paths=2, substeps=2):
    """chi on the grid, carried along the flow itself - w = u - Omega x x, the flow in the frame turning with the
    body, where the setup is steady and D chi/DT = w . grad chi = Q. each path starts at r_min (chi 0) and is followed
    back out, in u = ln r: d theta/du = (w . side)/(w . n), d chi/du = Q r/(w . n); the paths' chi at each radius is
    fitted round the circle with the table's harmonics (least squares: paths x as many paths as angles), so no
    jitter from one radius to the next"""
    b = source.bodies[k]
    z = b.at(0.0)
    P = paths*len(thetas)
    def rates(u, th):
      r = math.exp(u)
      out = np.zeros((2, len(th)))
      for i, a in enumerate(th):
        n = np.array([math.cos(a), math.sin(a)])
        x = z + r*n
        flow, _, s = source.parts3(x, 0.0, k)
        w = flow - self.omega*np.array([-x[1], x[0]])
        radial = min(w @ n, -1e-3)                       #inward; a path that turns outward is cut off there
        out[0, i] = (w @ np.array([-n[1], n[0]]))/radial
        out[1, i] = C**4*s/2*r/radial
      return out
    th = 2*math.pi*np.arange(P)/P
    chi = np.zeros(P)
    values = np.zeros((len(self.us), len(thetas)))
    for i in range(1, len(self.us)):
      h = self.du/substeps
      for j in range(substeps):
        u = self.us[i - 1] + j*h
        k1 = rates(u, th)
        k2 = rates(u + h/2, th + h/2*k1[0])
        k3 = rates(u + h/2, th + h/2*k2[0])
        k4 = rates(u + h, th + h*k3[0])
        th = th + h/6*(k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
        chi = chi + h/6*(k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
      #the Fourier series (the table's harmonics) that best fits the paths' chi, at the grid's angles
      M = np.exp(1j*np.outer(th, np.arange(-(len(thetas)//2) + 1, len(thetas)//2)))
      c = np.linalg.lstsq(M, chi.astype(complex), rcond=None)[0]
      values[i] = np.real(np.exp(1j*np.outer(thetas, np.arange(-(len(thetas)//2) + 1, len(thetas)//2))) @ c)
    return values

  def spline(self, y):
    """a natural cubic spline's second derivatives in u, for each column of y"""
    n = len(self.us)
    A = np.zeros((n, n))
    rhs = np.zeros(y.shape, dtype=y.dtype)
    A[0, 0] = A[-1, -1] = 1.0
    for i in range(1, n - 1):
      A[i, i - 1], A[i, i], A[i, i + 1] = 1/6, 2/3, 1/6
      rhs[i] = (y[i + 1] - 2*y[i] + y[i - 1])/self.du**2
    return np.linalg.solve(A, rhs)

  def at(self, d, t):
    """chi and its gradient at d from the body, at time t"""
    r = math.sqrt(d @ d)
    if r <= self.rmin:
      return 0.0, np.zeros(2)
    a = -self.omega*t
    c, s = math.cos(a), math.sin(a)
    e = np.array([c*d[0] - s*d[1], s*d[0] + c*d[1]])   #into the table's orientation
    u = min(math.log(r), self.us[-1])
    i = min(int((u - self.us[0])/self.du), len(self.us) - 2)
    A = (self.us[i + 1] - u)/self.du
    B = 1 - A
    h = self.du
    y0, y1, s0, s1 = self.coef[i], self.coef[i + 1], self.second[i], self.second[i + 1]
    val = A*y0 + B*y1 + ((A**3 - A)*s0 + (B**3 - B)*s1)*h*h/6
    dval = (y1 - y0)/h + (-(3*A*A - 1)*s0 + (3*B*B - 1)*s1)*h/6
    th = math.atan2(e[1], e[0])
    rot = np.exp(1j*self.m*th)
    chi = float(np.real(np.sum(val*rot)))
    dchi_du = float(np.real(np.sum(dval*rot)))
    dchi_dth = float(np.real(np.sum(1j*self.m*val*rot)))
    n = e/r
    side = np.array([-n[1], n[0]])
    g = dchi_du/r*n + dchi_dth/r*side
    return chi, np.array([c*g[0] + s*g[1], -s*g[0] + c*g[1]])   #back to the lab's orientation


class FreeFallPN(Spacetime):
  """
  GR's first post-Newtonian metric (engine/metric.py PostNewtonian) in the free-fall time of the carried flow:
  t = T + phi/c^2, u0 = grad phi the carried flow (the lab's, flat, with its tides), phi_T = U - |u0|^2/2 (Bernoulli).
  in the 3+1 form (studies/constraints.py; docs Lapse and curved space):

    gamma = (1 + 2U/c^2) delta - u0 u0/c^2
    gamma u = u0 (1 + (phi_T - 2U)/c^2) + 4 U_j/c^2
    N^2 = 1 + [(u . gamma u - |u0|^2) + (phi_T^2 - 4 U phi_T - 2 psi + 2 U^2)/c^2]/c^2

  N is 1 at Newton's order; its first post-Newtonian part is what a further term chi/c^4 in the time would move into
  the flow (D chi/DT = Q), so that N = 1 exactly. this spacetime is GR (to the carried flow's Newtonian error), so it
  checks the studies' mapping to GR's coordinates; and N - 1 is how far GR in free-fall time is from the premise's
  clocks before chi
  """

  timedSeams = True

  def __init__(self, bodies, lapse=True, retarded=True, tides=True, keep=('space', 'scale', 'moving', 'psi'), chi=None):
    """keep: GR's pieces kept beyond the carried flow, to see what each does - 'space' (gamma), 'scale' (u0's
    (phi_T - 2U)/c^2) 'moving' (the moving bodies' 4 U_j/c^2) and 'psi' (GR's psi in the lapse). chi: the index of a body round which the time is
    shifted by chi/c^4 (ChiTable), taking the lapse to 1 there and its 1PN part into the flow; lapse then keeps only
    what the table leaves"""
    from engine.metric import PostNewtonian
    self.keep = set(keep)
    self.chiBody, self.chiTable = chi, None
    self.bodies = list(bodies)
    self.carried = CarriedSpacetime(self.bodies, tides=tides)
    self.tides = tides
    self.pn = PostNewtonian(self.bodies)
    self.useLapse = lapse
    self.retarded = retarded
    self.static = False
    self.centre = None

  def describe(self):
    return "GR's 1PN metric in the carried flow's free-fall time%s" % ('' if self.useLapse else ', its lapse left at 1')

  def region(self, x, t):
    return self.carried.region(x, t)

  def seamVelocity(self, x, t=0.0):
    return self.carried.seamVelocity(x, t)

  def seamNormal(self, x, t=0.0):
    return self.carried.seamNormal(x, t)

  def shift(self, x, t, region):
    """
    the potential's change from GR's metric being at harmonic time t + Delta/c^2, not at t: Delta = phi(x) - phi(body),
    phi the potential of the region's flow (its body's velocity and river: V . d - 2 sqrt(2 GM r); the tide's part is
    ~1e-4 of these near the body). U at Newton's order moves the flow, which has the bodies at t; GR's U is at the
    point's own harmonic time, so the difference, dU/dt Delta/c^2, is first post-Newtonian (N^2 has -2 of it /c^2)
    """
    from engine.metric import bodyVelocityAt
    b = self.bodies[region]
    d = x - b.at(t)
    r = math.sqrt(d @ d)
    delta = bodyVelocityAt(b, t) @ d - 2*math.sqrt(2*b.GM*r)
    rate = 0.0
    for o in self.bodies:
      e = x - o.at(t)
      rate += o.GM*(e @ bodyVelocityAt(o, t))/(e @ e)**1.5   #dU/dt: each body's GM/|x - z(t)|
    return rate*delta/C**2

  def parts3(self, x, t, region):
    u0 = self.baseFlow(x, t, region)
    U, Uj, psi = self.pn.terms(x, t)
    v2 = u0 @ u0
    phiT = U - v2/2
    h = (2*U*np.eye(2) - np.outer(u0, u0))/C**2 if 'space' in self.keep else np.zeros((2, 2))
    k = -h + h @ h                                    #gamma^-1 - delta
    a = (u0*(phiT - 2*U)/C**2 if 'scale' in self.keep else 0.0) + (4*Uj/C**2 if 'moving' in self.keep else 0.0)
    u = u0 + a + k @ (u0 + a)
    #u . gamma u - |u0|^2 = u0 . k u0 + 2 a . gamma^-1 u0 + a . gamma^-1 a
    extra = u0 @ k @ u0 + 2*(a @ (u0 + k @ u0)) + a @ a
    s = (extra + (phiT*phiT - 4*U*phiT - (2*psi if 'psi' in self.keep else 0.0) + 2*U*U)/C**2)/C**2
    if self.retarded:
      s -= 2*self.shift(x, t, region)/C**2
    if self.chiBody is not None and region == self.chiBody:
      u, s = self.shifted(x, t, u, s)
    return u, h, s

  def shifted(self, x, t, u, s):
    """the flow and N^2 - 1 in the time T + chi/c^4: gamma u less grad chi/c^2 (u, to first post-Newtonian order),
    and N^2 less 2 D chi/DT/c^4"""
    if self.chiTable is None:
      self.chiTable = ChiTable(self.withLapse(), self.chiBody)
    b = self.bodies[self.chiBody]
    d = x - b.at(t)
    _, grad = self.chiTable.at(d, t)
    dt = 10.0
    rate = (self.chiTable.at(x - b.at(t + dt), t + dt)[0] - self.chiTable.at(x - b.at(t - dt), t - dt)[0])/(2*dt)
    return u - grad/C**2, s - 2*(rate + u @ grad)/C**4

  def withLapse(self):
    """the same spacetime with its lapse, unshifted: the source chi is worked out from"""
    return FreeFallPN(self.bodies, lapse=True, retarded=self.retarded, tides=self.tides, keep=self.keep)

  def baseFlow(self, x, t, region):
    """u0: the flow (keeping Newton's equation, with Bernoulli's phi_T = U - |u0|^2/2) whose time this is"""
    return self.carried.flow(x, t, region)

  def flow(self, x, t, region=None):
    k = self.region(x, t) if region is None else region
    return self.parts3(x, t, k)[0]

  def space(self, x, t, region=None):
    k = self.region(x, t) if region is None else region
    return self.parts3(x, t, k)[1]

  def lapseOffset(self, x, t):
    if not self.useLapse:
      return 0.0
    s = self.parts3(x, t, self.region(x, t))[2]
    return s/(1 + math.sqrt(1 + s))


class FreeFallTurning(FreeFallPN):
  """
  FreeFallPN in the time of the turning flow with Jacobi constant 0 (engine/turning.py, SpecialFlowCalculator combine
  'turning'): one potential, phi = -S, over the whole plane, for two bodies going round their centre of mass. its
  Bernoulli's phi_T + |u|^2/2 = U + J is FreeFallPN's with J = 0, so the same 3+1 form is GR's metric in this time;
  with chi (ChiTable carries Q along this flow in the turning frame) the lapse is 1
  """

  def __init__(self, bodies, lapse=True, retarded=True, keep=('space', 'scale', 'moving', 'psi'), chi=None, jacobi=0.0,
               fine=None):
    """fine: round the lighter body (out to 3e9 m), the flow from LocalTurningFlow - the ray table's is off by a
    near-uniform ~1e-9 m/s^2 round the Moon's orbit with J = 0, which drives the Moon by ~100 m. by default, for J = 0
    only (with the carried J the flow is slow, ~1 km/s at the Moon, and its paths curl round within 3e9 m; there the
    ray table does)"""
    from engine.flow import SpecialFlowCalculator
    from engine.turning import LocalTurningFlow
    super().__init__(bodies, lapse=lapse, retarded=retarded, tides=True, keep=keep, chi=chi)
    self.jacobi = jacobi
    self.calc = SpecialFlowCalculator(self.bodies, 2, combine='turning')
    self.calc.jacobi = jacobi
    self.omega = self.calc.omega
    self.field = self.calc.rayField()
    self.fine = (jacobi == 0.0) if fine is None else fine
    self.local = LocalTurningFlow(self.bodies, self.omega, self.field.J) if self.fine else None

  def describe(self):
    return "GR's 1PN metric in the time of the turning flow, J = %g%s" % (self.jacobi, '' if self.useLapse else
                                                                         ', its lapse left at 1')

  def withLapse(self):
    return FreeFallTurning(self.bodies, lapse=True, retarded=self.retarded, keep=self.keep, jacobi=self.jacobi,
                           fine=self.fine)

  def baseFlow(self, x, t, region):
    from engine.flow import turn
    if self.local is not None and region == self.local.k:
      #the point from the body in the lab, then turned (LocalTurningFlow.wRel: turning the point first rounds it)
      d = turn(x - self.bodies[self.local.k].at(t), -self.omega*t)
      if self.local.coversRel(d):
        y = self.local.z + d
        return turn(self.local.wRel(d) + self.omega*np.array([-y[1], y[0]]), self.omega*t)
    return self.calc.turningFlow(x, region, t)

  def region(self, x, t):
    return self.calc.region(x, t)

  def seamVelocity(self, x, t=0.0):
    return self.omega*np.array([-x[1], x[0]])

  def seamNormal(self, x, t=0.0):
    """across the seam: grad (S_0 - S_1), the two regions' potentials, turned back to time t"""
    from engine.flow import turn
    y = turn(x, -self.omega*t)
    h = 1e5
    g = np.array([(self.field.action(y + h*e, 0) - self.field.action(y + h*e, 1)
                   - self.field.action(y - h*e, 0) + self.field.action(y - h*e, 1))/(2*h) for e in np.eye(2)])
    return turn(g/length(g), self.omega*t)

  def shift(self, x, t, region):
    """as FreeFallPN's, Delta = phi(x) - phi(body) = -(S(x) - S at the region's body, its offset)"""
    from engine.flow import turn
    from engine.metric import bodyVelocityAt
    y = turn(x, -self.omega*t)
    delta = -(self.field.action(y, region) - self.field.offsets[region])
    rate = 0.0
    for o in self.bodies:
      e = x - o.at(t)
      rate += o.GM*(e @ bodyVelocityAt(o, t))/(e @ e)**1.5
    return rate*delta/C**2
