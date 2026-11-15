"""
the true paths (geodesics) of the flow's metric, ds^2 = -c^2 dt^2 + |dx - u dt|^2, for any flow u - with curl or
without, steady or not - by Hamilton's equations:
  dx/dt = u + w,   dp/dt = -(grad u) . p,   p = gamma w (for light, p along w, |w| = c)
taken by fourth-order Runge-Kutta steps

the model's own step (engine/flow.py SpecialFlowCalculator) takes dw/dt = -(w . grad) u instead, which is the same
only where the flow has no curl. the bodies' flows by themselves have none; a carried flow round more than one moving
body (Calculator.carried) has some where the bodies' shares change, and so does a wave crossing the plane - so this
tells the model's step from the metric's own paths there

this is studies/grav_wave_across.py's Geodesic, for any calculator's flow rather than a wave's alone
"""
import math
import numpy as np
from engine.constants import C
from engine.flow import Calculator


class GeodesicCalculator(Calculator):
  """the flow of Calculator (bodies, direction, wave, combine, carried), moving particles along its geodesics"""
  runspeed = 8000

  def __repr__(self):
    return '<geodesic.GeodesicCalculator object>'

  def initPV(self, p, v):
    """start moving at v"""
    p.u = self.flow(p.pos, None, p.t)
    p.v = np.array(v, dtype=float)
    p.w = p.v - p.u

  def initPW(self, p, w):
    """start moving at w relative to the local space"""
    p.w = np.array(w, dtype=float)
    p.u = self.flow(p.pos, None, p.t)
    p.v = p.w + p.u

  def initPFreefall(self, p):
    """moving with the flow (v = u, w = 0)"""
    self.initPW(p, (0.0, 0.0))

  def rates(self, t, x, q, light, side):
    """dx/dt and dq/dt at x, time t, for momentum q (per unit mass; for light, any length along w)"""
    flow = lambda at: self.flow(at, side, t)
    h = 1e-5*max(self.nearest(x, t), 1.0) if self.bodies else 1e-3*max(1.0, float(np.max(np.abs(x))))
    grad = np.array([(flow(x + [h, 0.0]) - flow(x - [h, 0.0]))/(2*h), (flow(x + [0.0, h]) - flow(x - [0.0, h]))/(2*h)])
    w = C*q/np.linalg.norm(q) if light else C*q/math.sqrt(C*C + q @ q)
    return flow(x) + w, -grad @ q   #grad[i][j] = du_j/dx_i, so (grad @ q)_i = q_j du_j/dx_i

  def move(self, p, dt):
    self.seamStep(p, dt, self.step)

  def step(self, p, dt):
    """one fourth-order step, the flow from the side of any seam it starts on"""
    light = abs(np.linalg.norm(p.w) - C) < 1e-9*C
    q = p.w if light else p.w/math.sqrt(1 - (p.w @ p.w)/C**2)
    x, t = p.pos, p.t
    side = self.sideOf(p)
    k1 = self.rates(t, x, q, light, side)
    k2 = self.rates(t + dt/2, x + k1[0]*dt/2, q + k1[1]*dt/2, light, side)
    k3 = self.rates(t + dt/2, x + k2[0]*dt/2, q + k2[1]*dt/2, light, side)
    k4 = self.rates(t + dt, x + k3[0]*dt, q + k3[1]*dt, light, side)
    step = (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])*dt/6
    p.pos = x + step
    p.d += np.linalg.norm(step)
    end = q + (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])*dt/6
    if not light:   #proper time runs at 1/gamma = 1/sqrt(1 + q^2/c^2): the mean of the step's two ends
      p.pt += dt*(1/math.sqrt(1 + (q @ q)/C**2) + 1/math.sqrt(1 + (end @ end)/C**2))/2
    q = end
    p.t = t + dt
    p.w = C*q/np.linalg.norm(q) if light else C*q/math.sqrt(C*C + q @ q)
    p.u = self.flow(p.pos, side, p.t)
    p.v = p.w + p.u
