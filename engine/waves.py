"""
a plane gravitational wave in the flow model, travelling along z - straight through the (x, y) plane the engine works
in - to first order in its strain h

in GR, in TT coordinates, the wave is ds^2 = -c^2 dt^2 + (1 + h+) dx^2 + (1 - h+) dy^2 + 2 hx dx dy + dz^2, with h+ and
hx functions of t - z/c only, so on the plane z = 0 of t alone. measuring distances properly instead,
X = x + (h+ x + hx y)/2, Y = y + (hx x - h+ y)/2, it becomes, to first order in h,

  ds^2 = -c^2 dt^2 + |dX - u dt|^2,   u = (1/2) (h+' X + hx' Y,  hx' X - h+' Y)     (' = d/dt)

which is the flow model's form exactly: flat space, flowing at u. so the wave is a flow of space - a shear, stretching
along one axis while squeezing along the other (h+: along x and y, hx: at 45 degrees) - with no curl
(u = -grad S, S = -(h+' (X^2 - Y^2) + 2 hx' X Y)/4) and no divergence. this holds for any distance in the plane
(the wave does not change across it), not just near the centre; the centre is the point space does not move at, the
one fixed free particle (any other is the same flow plus a uniform velocity)

space moving with the flow (w = 0) stays at fixed TT coordinates: it moves as X = X0 (1 + h/2) does, the familiar
ring of free particles stretching and squeezing. a particle the flow model moves accelerates at
du/dt + (v . grad) u = (1/2) h'' X + ..., the tidal acceleration of the wave (geodesic deviation), and light sent
along x and back over a distance L takes 2L/c + (1/2) integral of h+ dt over the trip (TT coordinates)

  wave = PlaneWave(plus=1e-6, frequency=100.0)       h+ = 1e-6 sin(2 pi 100 t)
  calc = SpecialFlowCalculator([], wave=wave)        no bodies: the wave alone (or with bodies: their flow plus it)

a wave travelling WITHIN the plane (along = a direction n in it) is not exact in the model. it is transverse: its
plus polarization stretches the plane's direction across it, m, and z (out of the plane) against each other, and its
cross polarization shears m against z, which in the plane z = 0 moves nothing. the strain is h(t - n.X/c), and
measuring along m properly, M = m.X (1 + h/2), the metric becomes, to first order,

  ds^2 = -c^2 dt^2 + dN^2 + (dM - (1/2) h' M dt + (1/2c) h' M dN)^2

the first two terms in the bracket are a flow of space, u = (1/2) h'(t - n.X/c) (m.X) m, which is what PlaneWave
gives; the last is not - it makes the plane itself curved (its curvature is about -h''/2c^2, the wave's R_NMNM, which
no choice of time slices removes at first order), and the flow model's space is always flat. so this is the model's
nearest version of the wave. studies/grav_wave_across.py measures how near, against GR:
  - things at rest or slow, and light along n or across it (along m), at any distance: right
  - light at an angle to n: off by about (L/wavelength)/2 of the effect, h L/c, for short arms L, and 0.1-0.5 of it
    by a wavelength - from the missing term alone (true geodesics of the flow do the same)
  - things moving fast along n: off by a few h y0 from the missing term, and by more (up to ~30 h y0 at 0.9c) in the
    model, whose step takes w' = -(w . grad) u: the same as the flow's geodesics only where u has no curl, and this
    flow has curl (du_m/dn = -h'' (m.X)/2c). a wave along z has neither problem

  wave = PlaneWave(plus=1e-6, frequency=100.0, along=(1, 0))    travelling left to right
"""
import math
import numpy as np
from engine.constants import C


class PlaneWave:
  """
  h+ = plus sin(2 pi f (t - start) + phasePlus), hx = cross sin(2 pi f (t - start) + phaseCross) from start on (0
  before it, when the wave has not arrived), centred on centre (m); travelling along z (along None), or along the
  direction along in the plane, when t is the time the wave's front passes the centre's line across it
  (t - n.(X - centre)/c: strain and rate take that)
  """

  def __init__(self, plus=0.0, cross=0.0, frequency=1.0, phasePlus=0.0, phaseCross=0.0, start=0.0, centre=(0.0, 0.0),
               along=None):
    self.plus, self.cross = plus, cross
    self.frequency = frequency
    self.phasePlus, self.phaseCross = phasePlus, phaseCross
    self.start = start
    self.centre = np.array(centre, dtype=float)
    self.omega = 2*math.pi*frequency
    self.along = None if along is None else np.array(along, dtype=float)/np.linalg.norm(along)   #n
    self.across = None if along is None else np.array([-self.along[1], self.along[0]])          #m

  def when(self, pos, t):
    """the wave's own time at pos: t for a wave along z, t - n.(pos - centre)/c for one in the plane"""
    if self.along is None:
      return t
    return t - float(np.dot(np.asarray(pos) - self.centre, self.along))/C

  def strain(self, t):
    """(h+, hx) at time t"""
    if t < self.start:
      return 0.0, 0.0
    a = self.omega*(t - self.start)
    return self.plus*math.sin(a + self.phasePlus), self.cross*math.sin(a + self.phaseCross)

  def rate(self, t):
    """(h+', hx') at time t"""
    if t < self.start:
      return 0.0, 0.0
    a = self.omega*(t - self.start)
    return self.plus*self.omega*math.cos(a + self.phasePlus), self.cross*self.omega*math.cos(a + self.phaseCross)

  def integral(self, t0, t1):
    """the integrals of h+ and hx over time from t0 to t1, for light's travel time"""
    def one(amplitude, phase):
      at = lambda t: -math.cos(self.omega*(max(t, self.start) - self.start) + phase)/self.omega
      return amplitude*(at(t1) - at(t0))
    return one(self.plus, self.phasePlus), one(self.cross, self.phaseCross)

  def flow(self, pos, t):
    """the flow of space the wave adds at pos, time t"""
    X, Y = pos[0] - self.centre[0], pos[1] - self.centre[1]
    if self.along is not None:   #in the plane: along m only, from h+ (hx moves things out of the plane)
      p, _ = self.rate(self.when(pos, t))
      return p*(self.across[0]*X + self.across[1]*Y)/2*self.across
    p, x = self.rate(t)
    return np.array([(p*X + x*Y)/2, (x*X - p*Y)/2])

  def describe(self):
    """the wave in words, for logs"""
    way = 'along z' if self.along is None else 'in the plane along (%g, %g)' % tuple(self.along)
    return ('plane wave %s: h+ %g, hx %g, %g Hz (phases %g, %g rad), from t = %g s, centred at (%g, %g) m'
            % (way, self.plus, self.cross, self.frequency, self.phasePlus, self.phaseCross, self.start, *self.centre))
