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


class SplitFlowCalculator(Calculator):
  """
  the flow model with each body's flow taken alone and its changes applied one at a time (see the module's note).
  p.u is the sum of the bodies' flows and p.w = v - p.u, kept only so step sizes and logs have them: no step uses them
  """
  runspeed = 12000

  def __init__(self, bodies=None, light='interval'):
    super().__init__(bodies, direction='g')
    if light not in ('interval', 'static'):
      raise ValueError("light is 'interval' or 'static', not %r" % (light,))
    if light == 'static' and self.moving:
      raise ValueError("the 'static' light rule is for bodies at rest")
    self.light = light

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

  def rate(self, pos, v, t=0.0):
    """a clock's rate, dtau/dt, at pos moving at v"""
    q = self.interval(pos, v, t)
    return math.sqrt(q)/C if q > 0 else 0.0

  def lightSpeed(self, pos, n, t=0.0):
    """light's speed along the unit vector n at pos, by the light rule"""
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
