"""
a flow direction for several bodies with no curl, so that space moving with the flow falls exactly as newtonian
gravity says it should

the flow's magnitude is fixed, |u|^2 = sum of 2GM/d over the bodies. for the flow model's acceleration (u . grad) u
to be g, the flow lines have to be zero-energy newtonian paths (released from rest at infinity): each one curves at
g across it / |u|^2. equivalently u = -grad S with |grad S| = |u|, the eikonal equation. with more than one body
no such field is smooth everywhere (the flow into each body, plus infinity, needs a point where u = 0, and |u| is
never 0), so it has a seam. each body's region is filled by zero-energy paths running straight out of it, S growing
along them from 0 at the body (S = the integral of |u| along the path); a point is in the region of the body whose S
there is smallest, so the seam is where two bodies' S are equal and S itself is continuous across it (the river's
time, static time + S/c^2 to first order, has a kink there but no jump). each body's S can have any constant added;
they are set so the seam goes through the saddle of the potential between body 0 and each other body (the point
where g = 0 on the line between them, which nothing at rest there leaves) - for equal masses the half-way line

RayField builds, for each body, a table of those paths: launched straight out from very close to the body, they are
integrated outwards (in log distance) through the combined g of all the bodies, until they are well into another
body's region (OVERLAP) or MAX_R; the angle between each path and the radial direction (small: about (d/D)^2/2 at
distance d from a body D from its companion), S, and their rates of change are tabled against log distance and angle
round the body, and interpolated cubically in distance (so the flow lines' curvature, which sets the acceleration, is
smooth). the flow points back down the path - into a black body, out of a white one

  field = RayField(bodies)          (built once; a few seconds)
  field.direction(pos)              unit direction of the flow at pos
  field.region(pos)                 index of the body whose region pos is in (smallest S)
  field.action(pos, i)              body i's S at pos, with its constant (None where its paths do not reach)
  field.direction(pos, region)      the direction carried on from region's paths, either side of the seam

for exactly two bodies engine/two_centre.py works out the same flow exactly, with no tables (Calculator direction
'eikonal-exact', the default for two bodies; this one is 'eikonal', the default for three or more)
"""
import math
import numpy as np
from engine.constants import *

MIN_R = 1e-6*AU      #the paths start this far from their body; nearer than this the flow is taken as radial
MAX_R = 60*AU        #and the table stops this far out (beyond it the flow points along g)
PER_DECADE = 100     #table rows per factor of 10 in distance
SUBSTEPS = 4         #RK4 steps per row
RAYS = 4096          #paths from each body
OVERLAP = 1.5        #the paths carry on past the seam until they are this many times farther from their own body
                     #than from another (times the mass ratio, if their body is the heavier: the seam is nearer the
                     #lighter body), so the flow either side of it can be followed a step across
ANGLES = 2048        #table columns round each body


class RayField:

  def __init__(self, bodies, minR=MIN_R, maxR=MAX_R, perDecade=PER_DECADE, rays=RAYS, angles=ANGLES):
    self.bodies = list(bodies)
    self.pos = np.array([b.pos for b in self.bodies])
    self.GM = np.array([b.GM for b in self.bodies])
    self.minR, self.maxR = minR, maxR
    self.du = math.log(10)/perDecade
    self.rows = int(math.ceil(math.log(maxR/minR)/self.du)) + 1
    self.angles = angles
    self.dphi = 2*math.pi/angles
    self.tables = []     #per body: [row, column] angle of the path from radial, beta
    self.slopes = []     #per body: [row, column] its rate of change with log distance, for cubic interpolation
    self.actions = []    #per body: [row, column] S, the integral of |u| out along the path from the body
    self.actionSlopes = []   #per body: [row, column] dS/d(log distance)
    self.covered = []    #per body: [row, column] whether its paths reach there
    self.crossings = []  #per body: rows where neighbouring paths crossed (should be none)
    self.reach = []      #per body: [row] the farthest angle covered either side of the gap, for the diagnostics
    for i in range(len(self.bodies)):
      table, slopes, actions, actionSlopes, covered, crossings, reach = self.build(i, rays)
      self.tables.append(table)
      self.slopes.append(slopes)
      self.actions.append(actions)
      self.actionSlopes.append(actionSlopes)
      self.covered.append(covered)
      self.crossings.append(crossings)
      self.reach.append(reach)
    self.offsets = [0.0]*len(self.bodies)   #each body's constant in S
    for i in range(1, len(self.bodies)):
      saddle = self.saddle(0, i)
      a, b = self.action(saddle, 0), self.action(saddle, i)
      if a is not None and b is not None:
        self.offsets[i] = a - b

  def accel(self, x, y):
    """newtonian g at the points (x, y) (arrays), and |u|^2 there"""
    gx, gy, n2 = np.zeros_like(x), np.zeros_like(x), np.zeros_like(x)
    for (bx, by), gm in zip(self.pos, self.GM):
      dx, dy = x - bx, y - by
      d2 = dx*dx + dy*dy
      d = np.sqrt(d2)
      gx -= gm*dx/(d2*d)
      gy -= gm*dy/(d2*d)
      n2 += 2*gm/d
    return gx, gy, n2

  def saddle(self, i, j):
    """the point between bodies i and j where g along the line between them is 0 (by bisection)"""
    a, b = self.pos[i], self.pos[j]
    along = (b - a)/np.linalg.norm(b - a)
    pull = lambda f: float(np.dot(np.array([q[0] for q in self.accel(*(np.array([v]) for v in a + f*(b - a)))[:2]]), along))
    lo, hi = 1e-6, 1 - 1e-6   #pulled towards i (negative) near i, towards j near j
    for _ in range(100):
      mid = (lo + hi)/2
      if pull(mid) < 0:
        lo = mid
      else:
        hi = mid
    return a + (lo + hi)/2*(b - a)

  def overlap(self, x, y, i):
    """
    how far the points (x, y) are into another body's region: distance from body i over another's, divided by
    their mass ratio when body i is the heavier (the seam lies about where the distances are in the inverse ratio of
    the masses), the largest over the other bodies
    """
    d2 = [(x - bx)**2 + (y - by)**2 for bx, by in self.pos]
    worst = np.zeros_like(x)
    for j in range(len(self.pos)):
      if j != i:
        worst = np.maximum(worst, np.sqrt(d2[i]/d2[j])/max(1.0, self.GM[i]/self.GM[j]))
    return worst

  def build(self, i, rays):
    """the table for body i: paths launched straight out at evenly spaced angles, integrated out in log r"""
    bx, by = self.pos[i]
    theta = 2*math.pi*np.arange(rays)/rays
    x, y, psi = bx + self.minR*np.cos(theta), by + self.minR*np.sin(theta), theta.copy()
    S = np.full(rays, 2*math.sqrt(2*self.GM[i]*self.minR))   #the integral of sqrt(2GM/r) from the body's centre
    alive = np.ones(rays, bool)
    table = np.zeros((self.rows, self.angles))
    slopes = np.zeros((self.rows, self.angles))
    actions = np.zeros((self.rows, self.angles))
    actionSlopes = np.zeros((self.rows, self.angles))
    covered = np.zeros((self.rows, self.angles), bool)
    reach = np.zeros(self.rows)
    crossings = []
    grid = self.dphi*np.arange(self.angles)

    def rates(x, y, psi):
      #d/du of x, y, psi and S, with u = ln r (r from body i): ds/du = r/cos(beta), dpsi/ds = g across / |u|^2,
      #dS/ds = |u|
      dx, dy = x - bx, y - by
      r = np.sqrt(dx*dx + dy*dy)
      c, s = np.cos(psi), np.sin(psi)
      cosb = (dx*c + dy*s)/r
      gx, gy, n2 = self.accel(x, y)
      ds = r/cosb
      return c*ds, s*ds, (-gx*s + gy*c)/n2*ds, np.sqrt(n2)*ds

    for row in range(self.rows):
      if row > 0:
        h = self.du/SUBSTEPS
        for _ in range(SUBSTEPS):
          k1 = rates(x, y, psi)
          k2 = rates(x + k1[0]*h/2, y + k1[1]*h/2, psi + k1[2]*h/2)
          k3 = rates(x + k2[0]*h/2, y + k2[1]*h/2, psi + k2[2]*h/2)
          k4 = rates(x + k3[0]*h, y + k3[1]*h, psi + k3[2]*h)
          x = x + (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])*h/6
          y = y + (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])*h/6
          psi = psi + (k1[2] + 2*k2[2] + 2*k3[2] + k4[2])*h/6
          S = S + (k1[3] + 2*k2[3] + 2*k3[3] + k4[3])*h/6
        #a path leaves the table once it is in another body's region, or turns more than ~84 degrees from radial
        phi = np.arctan2(y - by, x - bx)
        beta = (psi - phi + math.pi) % (2*math.pi) - math.pi
        alive &= (self.overlap(x, y, i) <= OVERLAP) & (np.cos(beta) > 0.1) & np.isfinite(x)
      phi = np.arctan2(y - by, x - bx)
      beta = (psi - phi + math.pi) % (2*math.pi) - math.pi
      if alive.sum() < 2:
        for out in (table, slopes, actions, actionSlopes):
          out[row:] = out[row - 1] if row else 0.0
        break
      #d beta/du = d psi/du - d phi/du, and d phi/du = tan(beta)
      now = rates(x, y, psi)
      slope = now[2] - np.tan(beta)
      #the live paths in launch order, their angles round the body unwrapped from the first: the arc they cover
      live = np.flatnonzero(alive)
      if not alive.all():   #start just after the gap so the live arc is contiguous
        gap = np.flatnonzero(~alive)
        after = np.flatnonzero(np.diff(alive.astype(int)) == 1)
        first = (after[0] + 1) if len(after) else live[0]
        live = np.concatenate([live[live >= first], live[live < first]])
      a = np.unwrap(phi[live])
      if np.any(np.diff(a) <= 0):
        crossings.append(row)
        order = np.argsort(a)
        a = a[order]
        live = live[order]
      b, db, sv, dsv = beta[live], slope[live], S[live], now[3][live]
      if alive.all():   #the whole circle: wrap round
        a = np.concatenate([a, [a[0] + 2*math.pi]])
        b, db, sv, dsv = [np.concatenate([q, [q[0]]]) for q in (b, db, sv, dsv)]
        reach[row] = 2*math.pi
      else:
        reach[row] = a[-1] - a[0]
      #each column's angle measured from the start of the arc; past its end (in the gap, the other region) the
      #nearer end's value carries on
      at = a[0] + (grid - a[0]) % (2*math.pi)
      past = at > a[-1]
      gapWidth = 2*math.pi - (a[-1] - a[0])
      nearStart = past & (at - a[-1] > gapWidth/2)
      for out, values in ((table, b), (slopes, db), (actions, sv), (actionSlopes, dsv)):
        col = np.interp(at, a, values)
        col[past] = values[-1]
        col[nearStart] = values[0]
        out[row] = col
      covered[row] = ~past
      #the slopes along the paths, which also move round the body (d phi/du = tan beta), at a fixed angle instead
      for value, out in ((table, slopes), (actions, actionSlopes)):
        across = (np.roll(value[row], -1) - np.roll(value[row], 1))/(2*self.dphi)
        out[row] -= across*np.tan(table[row])
    return table, slopes, actions, actionSlopes, covered, crossings, reach

  def cell(self, pos, i):
    """where pos is in body i's table: (r, phi, row, fraction, column, next column, fraction), or None past it"""
    bx, by = self.pos[i]
    dx, dy = pos[0] - bx, pos[1] - by
    r = math.hypot(dx, dy)
    if r >= self.maxR:
      return None
    phi = math.atan2(dy, dx)
    k = math.log(max(r, self.minR)/self.minR)/self.du
    k0 = min(int(k), self.rows - 2)
    m = (phi % (2*math.pi))/self.dphi
    m0 = int(m) % self.angles
    return r, phi, k0, k - k0, m0, (m0 + 1) % self.angles, m - int(m)

  def hermite(self, values, slopes, k0, fk, m0, m1, fm):
    """cubic in log distance between rows k0 and k0 + 1, from the values and slopes there; linear round the body"""
    b0 = (1 - fm)*values[k0, m0] + fm*values[k0, m1]
    b1 = (1 - fm)*values[k0 + 1, m0] + fm*values[k0 + 1, m1]
    d0 = ((1 - fm)*slopes[k0, m0] + fm*slopes[k0, m1])*self.du
    d1 = ((1 - fm)*slopes[k0 + 1, m0] + fm*slopes[k0 + 1, m1])*self.du
    f2, f3 = fk*fk, fk*fk*fk
    return (2*f3 - 3*f2 + 1)*b0 + (f3 - 2*f2 + fk)*d0 + (-2*f3 + 3*f2)*b1 + (f3 - f2)*d1

  def action(self, pos, i):
    """body i's S at pos - the integral of |u| along its zero-energy path from the body - or None where its paths
    do not reach"""
    at = self.cell(pos, i)
    if at is None:
      return None
    r, phi, k0, fk, m0, m1, fm = at
    offset = self.offsets[i] if hasattr(self, 'offsets') else 0.0
    if r <= self.minR:
      return 2*math.sqrt(2*self.GM[i]*r) + offset
    c = self.covered[i]
    if not (c[k0, m0] and c[k0, m1] and c[k0 + 1, m0] and c[k0 + 1, m1]):
      return None
    return self.hermite(self.actions[i], self.actionSlopes[i], k0, fk, m0, m1, fm) + offset

  def region(self, pos):
    """index of the body whose region pos is in: the one whose S there is smallest (the nearest, past the tables)"""
    best, region = None, None
    for i in range(len(self.bodies)):
      S = self.action(pos, i)
      if S is not None and (best is None or S < best):
        best, region = S, i
    if region is None:
      d = [(pos[0] - bx)**2 + (pos[1] - by)**2 for bx, by in self.pos]
      region = d.index(min(d))
    return region

  def direction(self, pos, region=None):
    """
    the unit direction of the flow at pos: back down region's path through pos (by default the region pos is in) -
    towards a black body, away from a white one; None past the table (MAX_R out)
    """
    i = self.region(pos) if region is None else region
    at = self.cell(pos, i)
    if at is None:
      return None
    r, phi, k0, fk, m0, m1, fm = at
    beta = 0.0 if r <= self.minR else self.hermite(self.tables[i], self.slopes[i], k0, fk, m0, m1, fm)
    psi = phi + beta
    sign = -1.0 if self.bodies[i].black else 1.0
    return np.array([sign*math.cos(psi), sign*math.sin(psi)])
