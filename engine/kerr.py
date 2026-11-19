"""
a rotating (Kerr) black hole in the river model (Hamilton & Lisle, "The river model of black holes", Am. J. Phys. 76,
519 (2008), arXiv gr-qc/0411060), in the hole's equatorial plane

the river flows through a flat background - in the equatorial plane, flat (x, y) at distance R from the hole, where
Doran's (and Boyer-Lindquist's) r = sqrt(R^2 - a^2), a = spin GM/c^2:

  the flow u is straight inwards (no swirl), at c sqrt(2GM/c^2 r)
  the river also has a twist: a rotation, about the spin axis, of  mu = -(a/R) |u|/c + zeta,
    zeta = a * integral from r to infinity of beta / R^2 dr,  beta = sqrt(2Mr)/R
  space is not quite the flat background seen from the river: the metric is
    ds^2 = -c^2 dt^2 + |dx - u (dt + alpha.dx/c)|^2,   alpha = (a y / R^2, -a x / R^2)
  so something moving at w relative to the river moves through the background at  v = w + u (1 + alpha.w/c)

moving through the river, w changes by the river's change along the particle's motion relative to the river, w dt
(Hamilton & Lisle eq. 77: dp/dtau = (u^n d/dx^n) omega p, u^n the 4-velocity in the river's frame): boosted by the
change in u (added relativistically) and turned by the change in mu - both the river's value where the river goes
less its value where the particle goes. in a non-rotating hole w dt is the difference
between where the particle goes and where the river goes, (v - u) dt, as SpecialFlowCalculator has it; with spin
v - u = w + u (alpha.w)/c, and it is w dt that counts. with a = 0 this is SpecialFlowCalculator exactly
"""
import math
import numpy as np
from engine.constants import *
from engine.flow import SpecialFlowCalculator
from engine.vectors import length

ZETA_POINTS = 24   #Gauss-Legendre points for the twist's integral
_ZX, _ZW = np.polynomial.legendre.leggauss(ZETA_POINTS)
_ZT, _ZW = (_ZX + 1)/2, _ZW/2   #on 0 to 1


class KerrFlowCalculator(SpecialFlowCalculator):
  """
  the river model of one rotating hole, in its equatorial plane (see the module notes): the body's spin (-1 to 1,
  positive anticlockwise) sets a = spin GM/c^2. order as SpecialFlowCalculator (2 by default). the hole must be
  black; there is one body
  """

  def __init__(self, bodies=None, order=2, twist=1.0):
    super().__init__(bodies, order, step='velocity')   #its own step, with the twist (moveFirstOrder, moveSecondOrder)
    if len(self.bodies) != 1 or not self.bodies[0].black:
      raise ValueError('KerrFlowCalculator is for one black hole')
    hole = self.bodies[0]
    self.M = G*hole.mass/C**2          #GM/c^2 (m)
    self.a = getattr(hole, 'spin', 0.0)*self.M
    self.twist = twist                 #1: the river model; 0 leaves the twist out, -1 reverses it (to see what it does)

  def __repr__(self):
    return '<flow.KerrFlowCalculator object, order %d, spin %g>' % (self.order, self.a/self.M)

  #---- the river

  def radii(self, pos):
    """the flat distance R from the hole, and Doran / Boyer-Lindquist r"""
    R = length(pos - self.bodies[0].pos)
    return R, math.sqrt(max(R*R - self.a*self.a, 0.0))

  def flow(self, pos, region=None, t=0.0):
    """the river: straight in at c sqrt(2M/r); not a number at the ring singularity (R = a, r = 0) and inside it"""
    rel = pos - self.bodies[0].pos
    R, r = self.radii(pos)
    if r <= 0:
      return np.array([math.nan, math.nan])   #the run stops: its position is no longer finite
    return -C*math.sqrt(2*self.M/r)*rel/R

  def zeta(self, r):
    """
    a * integral from r to infinity of sqrt(2M r')/(r'^2 + a^2)^(3/2) dr'; with r' = r/t^2 it is
    a * 2 r sqrt(2M r) * integral from 0 to 1 of t^2/(r^2 + a^2 t^4)^(3/2) dt, which is smooth
    """
    a = self.a
    return a*2*r*math.sqrt(2*self.M*r)*float(np.dot(_ZW, _ZT**2/(r*r + a*a*_ZT**4)**1.5))

  def twistAt(self, pos):
    """the river's twist mu (rad): its rotation about the spin axis"""
    R, r = self.radii(pos)
    if r <= 0:
      return math.nan
    return self.twist*(-(self.a/R)*math.sqrt(2*self.M/r) + self.zeta(r))

  def twistGradient(self, pos):
    """
    how fast the twist changes outwards, d mu / dR (rad/m) - the ζ terms cancel, leaving a sqrt(2M) / (2 r^(5/2)):
    something moving outwards through the river at w_R is turned by -w_R d mu/dR each second (see change)
    """
    R, r = self.radii(pos)
    if r <= 0:
      return math.nan
    return self.twist*self.a*math.sqrt(2*self.M)/(2*r**2.5)

  def gravity(self, pos):
    """
    the river's acceleration, u du/dR = -(GM/r^2)(R/r) straight inwards: for a non-rotating hole GM/R^2, the
    newtonian pull, and stronger close to a rotating one
    """
    rel = pos - self.bodies[0].pos
    R, r = self.radii(pos)
    if r <= 0:
      return np.array([math.nan, math.nan])
    return -(G*self.bodies[0].mass/(r*r))*(R/r)*rel/R

  def alpha(self, pos):
    """alpha (dimensionless): how a motion round the hole tilts the river's flow through the background"""
    rel = pos - self.bodies[0].pos
    R2 = rel[0]**2 + rel[1]**2
    return np.array([self.a*rel[1]/R2, -self.a*rel[0]/R2])

  def angularMomentum(self, x, w, u):
    """
    the angle part of the momentum, per gamma: in ds^2 = -c^2 dt^2 + |dx - u (dt + alpha.dx/c)|^2 the momentum is
    gamma (w - alpha (u . w)/c), and x cross alpha = -a, so x cross w + a (u . w)/c (-p_t is gamma (c^2 + u . w) as
    without spin)
    """
    return x[0]*w[1] - x[1]*w[0] + self.a*(u @ w)/C

  def velocity(self, pos, u, w):
    """the motion through the background of something at w relative to the river: v = w + u (1 + alpha.w/c)"""
    return w + u*(1 + np.dot(self.alpha(pos), w)/C)

  #---- starting

  def initPV(self, p, v):
    """start moving at v through the background: w solves v = w + u (1 + alpha.w/c) (alpha.u = 0)"""
    p.u = self.flow(p.pos)
    d = v - p.u
    p.w = d - p.u*np.dot(self.alpha(p.pos), d)/C
    p.v = np.array(v, dtype=float)

  def initPW(self, p, w):
    p.w = np.array(w, dtype=float)
    p.u = self.flow(p.pos)
    p.v = self.velocity(p.pos, p.u, p.w)

  def initPFreefall(self, p):
    """moving with the river (w = 0): a fall from rest at infinity with no angular momentum"""
    p.u = self.flow(p.pos)
    p.v = p.u.copy()
    p.w = np.array([0.0, 0.0])

  #---- moving

  @staticmethod
  def rotate(w, angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([c*w[0] - s*w[1], s*w[0] + c*w[1]])

  def change(self, x, u, v, w, dt):
    """
    w after the river's change over dt from x: the difference between where the river goes (x + u dt) and a step w dt
    on from there, the particle's motion relative to the river - a boost by the change in u, then a turn by the
    change in mu
    """
    there = x + u*dt
    here = there + w*dt
    w = self.addSI(w, self.flow(there) - self.flow(here))
    return self.rotate(w, self.twistAt(there) - self.twistAt(here))

  def moveFirstOrder(self, p, dt):
    light = abs(length(p.w) - C) < 1e-9*C
    w = self.change(p.pos, p.u, p.v, p.w, dt)
    p.pos = p.pos + p.v*dt
    p.d += length(p.v*dt)
    p.w = w*C/length(w) if light else w
    p.u = self.flow(p.pos)
    p.v = self.velocity(p.pos, p.u, p.w)
    p.t += dt
    s = 1 - (length(p.w)**2)/C**2
    if s > 0.0:
      p.pt += dt*math.sqrt(s)

  def moveSecondOrder(self, p, dt):
    light = abs(length(p.w) - C) < 1e-9*C

    #half a step the first-order way, to the middle of the step
    xm = p.pos + p.v*dt/2
    wm = self.change(p.pos, p.u, p.v, p.w, dt/2)
    um = self.flow(xm)
    vm = self.velocity(xm, um, wm)

    #the whole step from the start, at the middle's rates: the river's change across the middle point, along the
    #particle's motion relative to the river (wm), applied to the middle w and added on
    d = wm*dt/2
    boost = self.addSI(wm, self.flow(xm - d) - self.flow(xm + d)) - wm
    turn = self.rotate(wm, self.twistAt(xm - d) - self.twistAt(xm + d)) - wm
    p.w = p.w + boost + turn
    if light:
      p.w = p.w*C/length(p.w)
    p.pos = p.pos + vm*dt
    p.d += length(vm*dt)
    p.u = self.flow(p.pos)
    p.v = self.velocity(p.pos, p.u, p.w)

    p.t += dt
    s = 1 - (length(wm)**2)/C**2
    if s > 0.0:
      p.pt += dt*math.sqrt(s)
