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
"""
import math
import numpy as np
from engine.constants import C
from engine.flow import Calculator, length


def bodyVelocity(b, t):
  """body b's velocity at time t"""
  if b.circling:
    x = b.at(t)
    return b.circling*np.array([-x[1], x[0]])
  return b.velocity


class Boost:
  """the Lorentz frame moving at V whose origin is the event (t0, x0)"""

  def __init__(self, V, t0, x0):
    self.V, self.t0, self.x0 = np.array(V, dtype=float), t0, np.array(x0, dtype=float)
    speed = length(self.V)
    self.gamma = 1/math.sqrt(1 - speed*speed/C**2)
    self.n = self.V/speed if speed > 0 else np.array([1.0, 0.0])

  def event(self, t, x):
    """(t', x') of the event (t, x)"""
    dt, dx = t - self.t0, x - self.x0
    along = dx @ self.n
    return self.gamma*(dt - self.V @ dx/C**2), dx + (self.gamma - 1)*along*self.n - self.gamma*self.V*dt

  def velocity(self, v):
    """v seen in the frame"""
    along = (v @ self.n)*self.n
    return (along - self.V + (v - along)/self.gamma)/(1 - v @ self.V/C**2)

  def back(self, v):
    """a velocity in the frame, seen in the lab"""
    along = (v @ self.n)*self.n
    return (along + self.V + (v - along)/self.gamma)/(1 + v @ self.V/C**2)

  def time(self, v):
    """dt'/dt along a path moving at v"""
    return self.gamma*(1 - v @ self.V/C**2)


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
    if boost not in ('galilean', 'lorentz'):
      raise ValueError("boost is 'galilean' or 'lorentz', not %r" % (boost,))
    if light == 'static' and self.moving and boost == 'galilean':
      raise ValueError("the 'static' light rule with Galilean boosts is for bodies at rest")
    if light == 'interval' and boost == 'lorentz':
      raise ValueError("the 'lorentz' boost has the 'static' light rule")
    self.light, self.boost = light, boost

  def __repr__(self):
    return '<split.SplitFlowCalculator object>'

  def bodyFlow(self, b, pos, t=0.0):
    """body b's own flow at pos, at time t: straight in at sqrt(2GM/d), carried at b's velocity"""
    return super().bodyFlow(b, pos, t) + bodyVelocity(b, t)

  def flow(self, pos, region=None, t=0.0):
    """the sum of the bodies' own flows (for the particle's p.u; the steps take each alone)"""
    return sum((self.bodyFlow(b, pos, t) for b in self.bodies), np.array([0.0, 0.0]))

  def interval(self, pos, v, t=0.0):
    """(c dtau/dt)^2 at pos for velocity v: c^2 - v^2 less each body's own change"""
    q = C*C - v @ v
    for b in self.bodies:
      w, rest = v - self.bodyFlow(b, pos, t), v - bodyVelocity(b, t)
      q -= w @ w - rest @ rest
    return q

  def frame(self, b, t):
    """body b's rest frame at time t, b at its origin"""
    return Boost(bodyVelocity(b, t), t, b.at(t))

  def restFlow(self, b, x):
    """body b's one-body flow in its own rest frame, at x there (b at the origin)"""
    d = length(x)
    return (-1 if b.black else 1)*math.sqrt(2*b.GM/d)*x/d

  def rate(self, pos, v, t=0.0):
    """a clock's rate, dtau/dt, at pos moving at v"""
    if self.boost == 'lorentz':
      free = math.sqrt(max(1 - v @ v/C**2, 0.0))
      r = free
      for b in self.bodies:
        f = self.frame(b, t)
        x = f.event(t, pos)[1]
        vb = f.velocity(v)
        w = vb - self.restFlow(b, x)
        r += f.time(v)*(math.sqrt(max(1 - w @ w/C**2, 0.0)) - math.sqrt(max(1 - vb @ vb/C**2, 0.0)))
      return max(r, 0.0)
    q = self.interval(pos, v, t)
    return math.sqrt(q)/C if q > 0 else 0.0

  def lightSpeed(self, pos, n, t=0.0):
    """light's speed along the unit vector n at pos, by the light rule"""
    if self.boost == 'lorentz':
      slowness = 1/C
      for b in self.bodies:
        f = self.frame(b, t)
        x = f.event(t, pos)[1]
        m = f.velocity(C*n)
        m = m/length(m)
        u = self.restFlow(b, x)
        a = u @ m
        s = a + math.sqrt(C*C - (u @ u - a*a))
        D = f.gamma*(1 - f.V @ n/C)
        slowness += D*D*(1/s - 1/C)
      return 1/slowness
    if self.light == 'static':
      sT, shift = C, 0.0
      for b in self.bodies:
        u = self.bodyFlow(b, pos, t)
        beta = (u @ u)/C**2
        r = pos - b.at(t)
        cos2 = (n @ r)**2/(r @ r)
        sT += C*math.sqrt((1 - beta)/(cos2/(1 - beta) + 1 - cos2)) - C
        shift += (u @ n)/(C*C - u @ u)
      return sT/(1 - sT*shift)
    #the root of interval(s n) = 0
    a, s2 = 0.0, 0.0
    for b in self.bodies:
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
    if self.boost == 'lorentz':
      return self.moveLorentz(p, dt)
    x, v, t = p.pos, p.v, p.t
    middle, end = t + dt/2, t + dt
    xm = x + v*dt/2
    #half a step, body by body: what each flow alone does to the velocity by the middle
    vm = v.copy()
    for b in self.bodies:
      V = bodyVelocity(b, t)
      u0, um = self.bodyFlow(b, x, t) - V, self.bodyFlow(b, xm, middle) - V
      w = vm - V - u0
      wm = self.addSI(w, self.bodyFlow(b, x + (u0 + V)*dt/2, middle) - V - um)
      vm = vm + (wm - w) + (um - u0)
    x1 = x + vm*dt
    #the whole step, body by body, at the middle's velocity
    for b in self.bodies:
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
    move with the 'lorentz' boost: the same two passes, each body's part in its rest frame at the step's start - the
    step's start, middle and end events boosted there, the particle's velocity boosted there and its change boosted back
    """
    x, v, t = p.pos, p.v, p.t
    middle, end = t + dt/2, t + dt
    xm = x + v*dt/2
    frames = [self.frame(b, t) for b in self.bodies]
    #half a step, body by body
    vm = v.copy()
    for b, f in zip(self.bodies, frames):
      t0, x0 = f.event(t, x)
      tm, xmb = f.event(middle, xm)
      h = tm - t0
      u0, um = self.restFlow(b, x0), self.restFlow(b, xmb)
      vb = f.velocity(vm)
      w = vb - u0
      wm = self.addSI(w, self.restFlow(b, x0 + u0*h) - um)
      vm = f.back(vb + (wm - w) + (um - u0))
    x1 = x + vm*dt
    #the whole step, body by body, at the middle's velocity
    for b, f in zip(self.bodies, frames):
      t0, x0 = f.event(t, x)
      xmb = f.event(middle, xm)[1]
      t1, x1b = f.event(end, x1)
      T = t1 - t0
      wm = f.velocity(vm) - self.restFlow(b, xmb)
      dw = self.restFlow(b, xmb - wm*T/2) - self.restFlow(b, xmb + wm*T/2)
      vb = f.velocity(v) + (self.addSI(wm, dw) - wm) + (self.restFlow(b, x1b) - self.restFlow(b, x0))
      v = f.back(vb)
    if getattr(p, 'light', False):
      n = v/length(v)
      v = self.lightSpeed(x1, n, end)*n
    p.pt += dt*self.rate(xm, vm, middle)
    p.d += length(vm*dt)
    p.pos, p.v, p.t = x1, v, end
    self.keep(p)
