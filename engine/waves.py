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
"""
import math
import numpy as np


class PlaneWave:
  """
  h+ = plus sin(2 pi f (t - start) + phasePlus), hx = cross sin(2 pi f (t - start) + phaseCross) from start on (0
  before it, when the wave has not arrived), centred on centre (m)
  """

  def __init__(self, plus=0.0, cross=0.0, frequency=1.0, phasePlus=0.0, phaseCross=0.0, start=0.0, centre=(0.0, 0.0)):
    self.plus, self.cross = plus, cross
    self.frequency = frequency
    self.phasePlus, self.phaseCross = phasePlus, phaseCross
    self.start = start
    self.centre = np.array(centre, dtype=float)
    self.omega = 2*math.pi*frequency

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
    p, x = self.rate(t)
    X, Y = pos[0] - self.centre[0], pos[1] - self.centre[1]
    return np.array([(p*X + x*Y)/2, (x*X - p*Y)/2])

  def describe(self):
    """the wave in words, for logs"""
    return ('plane wave along z: h+ %g, hx %g, %g Hz (phases %g, %g rad), from t = %g s, centred at (%g, %g) m'
            % (self.plus, self.cross, self.frequency, self.phasePlus, self.phaseCross, self.start, *self.centre))
