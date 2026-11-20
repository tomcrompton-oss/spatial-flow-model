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
relativistic part as its run at c less its run at c x 1000 (studies/lapse_moon.py differenced)

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
  return b.velocityAt(t) if hasattr(b, 'velocityAt') else bodyVelocityAt(b, t)


def accelerationOf(b, t):
  return b.accelerationAt(t) if hasattr(b, 'accelerationAt') else bodyAcceleration(b, t)


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

  def ownFlow(self, k, x, t):
    """the flow relative to body k (its river and the tide), in k's region"""
    d = x - self.bodies[k].at(t)
    r = length(d)
    return -math.sqrt(2*self.bodies[k].GM/r)*d/r + self.tidalFlow(k, x, t)

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
    return ((w @ w)*np.eye(2) - np.outer(w, w))/C**2

  def seamVelocity(self, x, t=0.0):
    """the seam's velocity across itself at x: the seam is where ln(GM_a/d_a^3) = ln(GM_b/d_b^3), for the two largest"""
    if len(self.bodies) == 1:
      return np.zeros(2)
    ranks = np.argsort([-b.GM/length(x - b.at(t))**3 for b in self.bodies])[:2]
    def f(y, s):
      a, b = self.bodies[ranks[0]], self.bodies[ranks[1]]
      return 3*math.log(length(y - b.at(s))) - 3*math.log(length(y - a.at(s))) + math.log(a.GM/b.GM)
    h = 1e-6*min(length(x - self.bodies[i].at(t)) for i in ranks)
    grad = np.array([(f(x + e, t) - f(x - e, t))/(2*h) for e in (np.array([h, 0.0]), np.array([0.0, h]))])
    dt = 1.0
    rate = (f(x, t + dt) - f(x, t - dt))/(2*dt)
    return -rate*grad/(grad @ grad)


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
