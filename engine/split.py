"""
the bodies taken one at a time: each body has its own flow, the one-body flow straight in at sqrt(2GM/d), in its own
rest frame, and nothing combines the flows. a step works out what each body's flow alone would do to the particle -
the one-body model's step (engine/flow.py SpecialFlowCalculator, second order), in that body's frame - and applies the
changes to the particle's velocity one after the other: body A's, then body B's. the particle moves once, at its
velocity in the frame the bodies are given in

with one body this is the flow model exactly. with more, each body's pull is its own, so g is Newton's sum of them, and
neither the vector rule's cross term nor the squares rule's other bodies' potential comes into it

clocks and light need one more rule, since the flows no longer make one space for them to tick and move in: each body
changes a clock's interval by what it would change it by alone, |v - u_k|^2 - |v - V_k|^2 (u_k its flow, V_k its own
velocity), so

  c^2 dtau^2 = (c^2 - v^2 - sum_k (|v - u_k|^2 - |v - V_k|^2)) dt^2

which is the one-body metric for one body, and for bodies at rest the sum of their one-body metrics:
-(c^2 - sum u_k^2) dt^2 - 2 (sum u_k) . dx dt + dx^2. light's speed along its way is set after each step, as the
one-body model keeps |w| = c, by one of two rules (light):

  'interval'  where that interval is 0
  'static'    each body's own change to light's speed in its static time (Schwarzschild's: c(1 - beta) radially,
              c sqrt(1 - beta) across, beta = u_k^2/c^2), added up; then into the model's time, which runs behind each
              body's static time by its own shift, dT = dt + sum u_k . dx/(c^2 - u_k^2). bodies at rest only

the two agree for one body, and differ with more by (n . u_A)(n . u_B)/c^2 terms: see studies/split_bodies.py

a moving body (boost): 'galilean' takes its frame by subtracting its velocity, the flow carried at it, as above. but
light keeps c only in the frame empty space is at rest in, and orbits round a moving body then don't contract: radar
to the Moon changes with direction by L V^2/2c^2 (studies/split_checks.py). 'lorentz' takes each body's frame by a
Lorentz boost - the particle's place, time and velocity - does the one-body step there, and boosts the velocity back.
with it, each body's change to a clock's proper time is added (its one-body rate less the free rate, in its frame, per
lab second), and light's 'static' rule becomes: each body's change to light's slowness (1/speed) in its own frame,
the one-body speed a + sqrt(c^2 - u_perp^2) along light's direction there, times D^2 = gamma^2 (1 - V . n/c)^2 (how a
delay along a light ray carries from a frame moving at V), added up. for bodies at rest the two boosts are the same
step; the clock and light rules agree with the others to first order in G

'local' is 'lorentz' with each body's frame boosted from the other bodies' static time, T = t + phi/c^2 (phi their
one-body potentials for the flow, u = grad phi), not the lab's time: in GR a body's local frame is set against the
space round it, and a body moving at V through another's flow u sees simultaneity shifted by u . x/c^2 (radar along
a moving Earth picks up (n . V)(n . u_Sun) L/c^2 with 'lorentz': studies/lunar_orbit.py). the other bodies are taken
at rest for their phi and u. but a static frame is held up against the others' pull, not falling freely, and with it
the Moon's range is out by 240 m

'freefall' sets each body's frame in the local free-fall frame of the other bodies' space: shifted (Galilean, the
flow's time being its free-falling observers' own) to the others' flow at the body's centre, U0, then Lorentz-boosted
by the body's velocity through that space, V - U0 - all in the Lorentz frame of the other body pulling hardest, so that
a system moving together is the same as one at rest. the others' flow is taken uniform across the body's region
(their tide left out)
"""
import math
import numpy as np
from engine.constants import C
from engine.flow import Calculator, length


def bodyVelocity(b, t):
  """body b's velocity at time t"""
  if hasattr(b, 'velocityAt'):   #a body moving under the model's own steps (studies/binary_pulsar.py)
    return b.velocityAt(t)
  if b.circling:
    x = b.at(t)
    return b.circling*np.array([-x[1], x[0]])
  return b.velocity


class Boost:
  """
  the Lorentz frame moving at V whose origin is the event (t0, x0) - boosted from the lab's time t, or, given the
  other bodies' phi and flow U (u = grad phi), from their static time T = t + phi/c^2, in which a velocity is
  dx/dT = v/(1 + v . U/c^2); or, given shift, boosted from the frame moving at shift (Galilean: the same t, x less
  shift t - the local free-fall frame of a flow moving at shift, whose time is the lab's)
  """

  def __init__(self, V, t0, x0, phi=None, U=None, shift=None):
    self.V, self.t0, self.x0 = np.array(V, dtype=float), t0, np.array(x0, dtype=float)
    self.shift = np.zeros(2) if shift is None else np.array(shift, dtype=float)
    speed = length(self.V)
    self.gamma = 1/math.sqrt(1 - speed*speed/C**2)
    self.n = self.V/speed if speed > 0 else np.array([1.0, 0.0])
    self.phi, self.U = phi, U
    self.T0 = t0 + (phi(self.x0)/C**2 if phi else 0.0)

  def event(self, t, x):
    """(t', x') of the event (t, x)"""
    dt, dx = t + (self.phi(x)/C**2 if self.phi else 0.0) - self.T0, x - self.x0
    dx = dx - self.shift*(t - self.t0)
    along = dx @ self.n
    return self.gamma*(dt - self.V @ dx/C**2), dx + (self.gamma - 1)*along*self.n - self.gamma*self.V*dt

  def velocity(self, v, x=None):
    """v (at x) seen in the frame"""
    if self.U:
      v = v/(1 + v @ self.U(self.x0 if x is None else x)/C**2)
    v = v - self.shift
    along = (v @ self.n)*self.n
    return (along - self.V + (v - along)/self.gamma)/(1 - v @ self.V/C**2)

  def back(self, v, x=None):
    """a velocity in the frame (at x), seen in the lab"""
    along = (v @ self.n)*self.n
    v = (along + self.V + (v - along)/self.gamma)/(1 + v @ self.V/C**2) + self.shift
    if self.U:
      v = v/(1 - v @ self.U(self.x0 if x is None else x)/C**2)
    return v

  def time(self, v, x=None):
    """dt'/dt along a path moving at v (at x)"""
    shift = v @ self.U(self.x0 if x is None else x)/C**2 if self.U else 0.0
    return self.gamma*(1 + shift - (v - self.shift) @ self.V/C**2)

  def light(self, n):
    """
    how a change in light's slowness along n carries from this frame to the lab: D^2 = gamma^2 (1 - V . n_F/c)^2 for
    the boost, n_F light's direction in the shifted frame, times (s_F/c)/(1 + n_F . shift/s_F) for the shift, s_F its
    speed there
    """
    w = C*n - self.shift
    sF = length(w)
    nF = w/sF
    D = self.gamma*(1 - self.V @ nF/C)
    return D*D*(sF/C)/(1 + nF @ self.shift/sF)


class Chain:
  """frames one after another: the first from the lab, each next from the one before"""

  def __init__(self, *stages):
    self.stages = stages

  def event(self, t, x):
    for f in self.stages:
      t, x = f.event(t, x)
    return t, x

  def velocity(self, v, x=None):
    for f in self.stages:
      v = f.velocity(v)
    return v

  def back(self, v, x=None):
    for f in reversed(self.stages):
      v = f.back(v)
    return v

  def time(self, v, x=None):
    rate = 1.0
    for f in self.stages:
      rate *= f.time(v)
      v = f.velocity(v)
    return rate

  def light(self, n):
    factor = 1.0
    for f in self.stages:
      factor *= f.light(n)
      n = f.velocity(C*n)
      n = n/length(n)
    return factor


class SplitFlowCalculator(Calculator):
  """
  the flow model with each body's flow taken alone and its changes applied one at a time (see the module's note).
  p.u is the sum of the bodies' flows and p.w = v - p.u, kept only so step sizes and logs have them: no step uses them
  """
  runspeed = 12000

  def __init__(self, bodies=None, light='interval', boost='galilean'):
    super().__init__(bodies, direction='g')
    if light not in ('interval', 'static'):
      raise ValueError("light is 'interval' or 'static', not %r" % (light,))
    if boost not in ('galilean', 'lorentz', 'local', 'freefall'):
      raise ValueError("boost is 'galilean', 'lorentz', 'local' or 'freefall', not %r" % (boost,))
    if light == 'static' and self.moving and boost == 'galilean':
      raise ValueError("the 'static' light rule with Galilean boosts is for bodies at rest")
    if light == 'interval' and boost != 'galilean':
      raise ValueError("the '%s' boost has the 'static' light rule" % boost)
    self.light, self.boost = light, boost
    self.skip = None   #a body whose own flow is left out: when the particle moved is that body

  def __repr__(self):
    return '<split.SplitFlowCalculator object>'

  def bodyFlow(self, b, pos, t=0.0):
    """body b's own flow at pos, at time t: straight in at sqrt(2GM/d), carried at b's velocity"""
    return super().bodyFlow(b, pos, t) + bodyVelocity(b, t)

  @property
  def acting(self):
    """the bodies whose flows act on the particle: all but self.skip"""
    return [b for b in self.bodies if b is not self.skip]

  def flow(self, pos, region=None, t=0.0):
    """the sum of the bodies' own flows (for the particle's p.u; the steps take each alone)"""
    return sum((self.bodyFlow(b, pos, t) for b in self.acting), np.array([0.0, 0.0]))

  def interval(self, pos, v, t=0.0):
    """(c dtau/dt)^2 at pos for velocity v: c^2 - v^2 less each body's own change"""
    q = C*C - v @ v
    for b in self.acting:
      w, rest = v - self.bodyFlow(b, pos, t), v - bodyVelocity(b, t)
      q -= w @ w - rest @ rest
    return q

  def frame(self, b, t):
    """
    body b's rest frame at time t, b at its origin: with the 'local' boost, from the other bodies' static time (their
    phi = -2 sqrt(2GM d) each, with u = grad phi their flow - as for bodies at rest)
    """
    others = [o for o in self.bodies if o is not b]
    if self.boost == 'freefall' and others:
      #into the frame of the other body pulling hardest, the others' space seen there, then b's free-fall frame in it
      X = b.at(t)
      main = max(others, key=lambda o: o.GM/length(X - o.at(t))**2)
      base = Boost(bodyVelocity(main, t), t, X)
      U0 = np.zeros(2)
      for o in others:
        own = Boost(bodyVelocity(o, t), t, o.at(t))
        space = own.back(self.restFlow(o, own.event(t, X)[1]))   #o's space at b, in the lab
        U0 = U0 + base.velocity(space)
      return Chain(base, Boost(base.velocity(bodyVelocity(b, t)) - U0, 0.0, np.zeros(2), shift=U0))
    if self.boost != 'local' or not others:
      return Boost(bodyVelocity(b, t), t, b.at(t))
    def phi(x):
      return sum((-1 if o.black else 1)*2*math.sqrt(2*o.GM*length(x - o.at(t))) for o in others)
    def U(x):
      return sum(self.restFlow(o, x - o.at(t)) for o in others)
    return Boost(bodyVelocity(b, t), t, b.at(t), phi, U)

  def restFlow(self, b, x):
    """body b's one-body flow in its own rest frame, at x there (b at the origin)"""
    d = length(x)
    return (-1 if b.black else 1)*math.sqrt(2*b.GM/d)*x/d

  def rate(self, pos, v, t=0.0):
    """a clock's rate, dtau/dt, at pos moving at v"""
    if self.boost != 'galilean':
      free = math.sqrt(max(1 - v @ v/C**2, 0.0))
      r = free
      for b in self.acting:
        f = self.frame(b, t)
        x = f.event(t, pos)[1]
        vb = f.velocity(v, pos)
        w = vb - self.restFlow(b, x)
        r += f.time(v, pos)*(math.sqrt(max(1 - w @ w/C**2, 0.0)) - math.sqrt(max(1 - vb @ vb/C**2, 0.0)))
      return max(r, 0.0)
    q = self.interval(pos, v, t)
    return math.sqrt(q)/C if q > 0 else 0.0

  def lightSpeed(self, pos, n, t=0.0):
    """light's speed along the unit vector n at pos, by the light rule"""
    if self.boost != 'galilean':
      slowness = 1/C
      for b in self.acting:
        f = self.frame(b, t)
        x = f.event(t, pos)[1]
        m = f.velocity(C*n, pos)
        m = m/length(m)
        u = self.restFlow(b, x)
        a = u @ m
        s = a + math.sqrt(C*C - (u @ u - a*a))
        slowness += f.light(n)*(1/s - 1/C)
      return 1/slowness
    if self.light == 'static':
      sT, shift = C, 0.0
      for b in self.acting:
        u = self.bodyFlow(b, pos, t)
        beta = (u @ u)/C**2
        r = pos - b.at(t)
        cos2 = (n @ r)**2/(r @ r)
        sT += C*math.sqrt((1 - beta)/(cos2/(1 - beta) + 1 - cos2)) - C
        shift += (u @ n)/(C*C - u @ u)
      return sT/(1 - sT*shift)
    #the root of interval(s n) = 0
    a, s2 = 0.0, 0.0
    for b in self.acting:
      u, V = self.bodyFlow(b, pos, t), bodyVelocity(b, t)
      a += (u - V) @ n
      s2 += u @ u - V @ V
    #c^2 - s^2 + 2 s a - s2 = 0
    return a + math.sqrt(a*a + C*C - s2)

  def initPV(self, p, v):
    """start moving at v"""
    p.v = np.array(v, dtype=float)
    p.light = False
    self.keep(p)

  def initPW(self, p, w):
    """
    start moving at w relative to the bodies' summed flow; light (|w| = c) starts the way w points, at light's speed
    that way
    """
    w = np.array(w, dtype=float)
    p.light = abs(length(w) - C) < 1e-9*C
    if p.light:
      n = w/length(w)
      p.v = self.lightSpeed(p.pos, n, p.t)*n
    else:
      p.v = w + self.flow(p.pos, None, p.t)
    self.keep(p)

  def initLight(self, p, n):
    """light leaving the way the unit vector n points"""
    p.light = True
    p.v = self.lightSpeed(p.pos, n, p.t)*n
    self.keep(p)

  def initPFreefall(self, p):
    """at rest (v = 0): with the bodies taken one at a time there is no one flow to fall with"""
    self.initPV(p, np.array([0.0, 0.0]))

  def keep(self, p):
    p.u = self.flow(p.pos, None, p.t)
    p.w = p.v - p.u

  def move(self, p, dt):
    """
    the one-body second-order step for each body in turn, in its own frame: half a step for each to find the velocity
    at the step's middle, the particle moving there at it; then the whole step's change for each, applied one after the
    other
    """
    if self.boost != 'galilean':
      return self.moveLorentz(p, dt)
    x, v, t = p.pos, p.v, p.t
    middle, end = t + dt/2, t + dt
    xm = x + v*dt/2
    #half a step, body by body: what each flow alone does to the velocity by the middle
    vm = v.copy()
    for b in self.acting:
      V = bodyVelocity(b, t)
      u0, um = self.bodyFlow(b, x, t) - V, self.bodyFlow(b, xm, middle) - V
      w = vm - V - u0
      wm = self.addSI(w, self.bodyFlow(b, x + (u0 + V)*dt/2, middle) - V - um)
      vm = vm + (wm - w) + (um - u0)
    x1 = x + vm*dt
    #the whole step, body by body, at the middle's velocity
    for b in self.acting:
      V = bodyVelocity(b, middle)
      wm = vm - self.bodyFlow(b, xm, middle)
      dw = self.bodyFlow(b, xm - wm*dt/2, middle) - self.bodyFlow(b, xm + wm*dt/2, middle)
      v = v + (self.addSI(wm, dw) - wm) + (self.bodyFlow(b, x1, end) - self.bodyFlow(b, x, t))
      v = v + bodyVelocity(b, t) - bodyVelocity(b, end)   #the flow's change, not the body's speeding up
    if getattr(p, 'light', False):
      n = v/length(v)
      v = self.lightSpeed(x1, n, end)*n
    p.pt += dt*self.rate(xm, vm, middle)
    p.d += length(vm*dt)
    p.pos, p.v, p.t = x1, v, end
    self.keep(p)

  def moveLorentz(self, p, dt):
    """
    move with a Lorentz-type boost: the same two passes, each body's part in its rest frame at the step's middle - the
    step's start, middle and end events boosted there, the particle's velocity boosted there and its change boosted back
    """
    x, v, t = p.pos, p.v, p.t
    middle, end = t + dt/2, t + dt
    xm = x + v*dt/2
    frames = [self.frame(b, middle) for b in self.acting]   #at the middle, so the step stays symmetric
    #half a step, body by body
    vm = v.copy()
    for b, f in zip(self.acting, frames):
      t0, x0 = f.event(t, x)
      tm, xmb = f.event(middle, xm)
      h = tm - t0
      u0, um = self.restFlow(b, x0), self.restFlow(b, xmb)
      vb = f.velocity(vm, x)
      w = vb - u0
      wm = self.addSI(w, self.restFlow(b, x0 + u0*h) - um)
      vm = f.back(vb + (wm - w) + (um - u0), x)
    x1 = x + vm*dt
    #the whole step, body by body, at the middle's velocity
    for b, f in zip(self.acting, frames):
      t0, x0 = f.event(t, x)
      xmb = f.event(middle, xm)[1]
      t1, x1b = f.event(end, x1)
      T = t1 - t0
      wm = f.velocity(vm, xm) - self.restFlow(b, xmb)
      dw = self.restFlow(b, xmb - wm*T/2) - self.restFlow(b, xmb + wm*T/2)
      vb = f.velocity(v, x) + (self.addSI(wm, dw) - wm) + (self.restFlow(b, x1b) - self.restFlow(b, x0))
      v = f.back(vb, x1)
    if getattr(p, 'light', False):
      n = v/length(v)
      v = self.lightSpeed(x1, n, end)*n
    p.pt += dt*self.rate(xm, vm, middle)
    p.d += length(vm*dt)
    p.pos, p.v, p.t = x1, v, end
    self.keep(p)
