"""
the eikonal flow carried by moving bodies, in the plane (engine/turning.py, Calculator combine 'turning'): the Sun
and the Earth on circles about their centre of mass, the flow turning with them, with the one Jacobi constant J for
which the flow round the Earth has none of the Sun's potential in it (carriedJacobi). does that fix
studies/multi_body_pn.py's stretch, and can it fill the plane?

  paths     the space paths themselves, in the turning frame (run back in time out of each body, as the tables are
            built): the Sun's turn back at about 2/3 AU - nothing let go from the Sun at that J gets further - and
            the Earth's leave it, curl round past its Hill sphere and cross. in the browser viewer
  newton    a particle let go beside the Earth, moving with it (and the turning frame), at its surface and the Moon's
            distance: its acceleration over 0.01 s against Newton's, the Sun and the Earth where they are then
  einstein  Einstein's constraint round the Earth, against 4 c0/r^2 (what the bodies-at-rest flow gives:
            studies/multi_body_pn.py), for this flow and for that one
  lunar     radar from the Earth's surface to a mirror at the Moon's distance and back, both turning with the
            Earth, against the Earth alone - as studies/multi_body_pn.py, whose flow put 3.4-3.7 m on it and a 0.11 m
            cos D term (in the turning frame the flow is steady, u - Omega x x)
  swirl     what the rest of the plane would need: past about 1.1 AU, the only paths with this J that can fill it
            come in from far away with angular momentum L = -J/Omega (energy 0) - space swirling round the Sun, at
            L/r. light passing the Sun 2-5 AU out, through that flow, against GR's (the Sun's own flow, straight in)
  sun       the cost: the Sun's own paths leave it with no angular momentum, so their energy is J, not 0 - the
            stretch moves from round the Earth to round the Sun (Einstein's constraint 4J/r^2). light passing the
            Sun, inside its region, against GR's

writes logs/turningEikonal/turningEikonal_<datetime>/: the paths (csv and log each), a viewer file
(turning_paths.full.json) and summary.log

run: python3 studies/turning_eikonal.py      (then: python3 scripts/publish_run.py logs/turningEikonal/turningEikonal_<datetime>)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Calculator, SpecialFlowCalculator, Particle
from engine.logger import LOG_DIR
from engine.constants import *
from part1_examples import write, COLOURS
from two_body_escapes import writeViewerFiles
from multi_body_pn import roundTrip, einstein, DMOON
from engine.turning import carriedJacobi

MU = ME/(MS + ME)
OMEGA = math.sqrt(G*(MS + ME)/AU**3)


def bodies():
  return [Body(MS, -MU*AU, 0.0, circling=OMEGA), Body(ME, (1 - MU)*AU, 0.0, circling=OMEGA)]


def turningCalc(cls=Calculator):
  return cls(bodies(), combine='turning') if cls is Calculator else cls(bodies(), 2, combine='turning')


def paths(folder):
  """space paths out of each body, run back in time in the turning frame (as the tables are)"""
  calc = turningCalc()
  field = calc.rayField()
  made, lines = [], ['paths: out of each body, run back in time in the turning frame, the Coriolis force turned'
                     ' round (as engine/turning.py\'s tables are built); J = %.9e m^2/s^2' % field.J]
  def rates(x, w):
    gx, gy, n2 = field.accel(np.array([x[0]]), np.array([x[1]]))
    return w, np.array([gx[0], gy[0]]) + 2*OMEGA*np.array([-w[1], w[0]])
  for index, body, count, last in ((0, calc.bodies[0], 12, 4e7), (1, calc.bodies[1], 12, 3e7)):
    for k in range(count):
      angle = 2*math.pi*(k + 0.5)/count
      out = np.array([math.cos(angle), math.sin(angle)])
      x = body.pos + 1e-6*AU*out
      w = math.sqrt(field.speed2(x))*out
      rows, t, far = [(0.0, *x)], 0.0, 0.0
      while t < last:
        r = np.linalg.norm(x - body.pos)
        dt = min(2e4, 2e-3*r/max(np.linalg.norm(w), 1.0))
        k1 = rates(x, w)
        k2 = rates(x + k1[0]*dt/2, w + k1[1]*dt/2)
        k3 = rates(x + k2[0]*dt/2, w + k2[1]*dt/2)
        k4 = rates(x + k3[0]*dt, w + k3[1]*dt)
        x = x + (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])*dt/6
        w = w + (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])*dt/6
        t += dt
        far = max(far, np.linalg.norm(x - body.pos))
        if len(rows) < 4000 and (t - rows[-1][0] > last/2000 or r < 0.01*AU):
          rows.append((t, *x))
        if index == 0 and np.linalg.norm(x - body.pos) < 0.5*far:   #the Sun's: back half way in
          break
      rows.append((t, *x))
      if k == 0:
        lines.append('  %s\'s: out to %.3f AU from it' % (('the Sun', 'the Earth')[index], far/AU))
      made.append((write(folder, 'path_%s_%02d' % (('sun', 'earth')[index], k), calc, rows, ['t', 'pos_x', 'pos_y'],
                         ['a space path out of %s, run back in time in the turning frame (J = %.9e)'
                          % (('the Sun', 'the Earth')[index], field.J)]), COLOURS[index]))
  writeViewerFiles(folder, 'turning_paths', made)
  sun = max(k for k in range(field.rows) if field.covered[0][k].any())
  cross = field.crossings[1][0] if field.crossings[1] else field.rows - 1
  lines.append('  the tables: the Sun\'s paths fill %.3f AU round it (then turn back); the Earth\'s are clean to'
               ' %.3g m (%.1f Hill radii) and cross beyond' % (field.minR*math.exp(sun*field.du)/AU,
               field.minR*math.exp(cross*field.du), field.minR*math.exp(cross*field.du)/(AU*(MU/3)**(1/3))))
  return lines


def newton(folder):
  lines = ['newton: let go beside the moving Earth (moving with the turning frame), its acceleration over 0.01 s'
           ' against Newton\'s', '    %-16s' % 'distance' + ''.join('%11s' % ('%d deg' % a) for a in range(0, 360, 45))
           + '   (|a - g_Newton|, m/s^2)']
  calc = turningCalc(SpecialFlowCalculator)
  earth = calc.bodies[1]
  for r, label in ((REARTH, 'surface'), (DMOON, 'Moon')):
    errors = []
    for a in range(0, 360, 45):
      p = Particle()
      p.pos = earth.pos + r*np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
      calc.initPV(p, OMEGA*np.array([-p.pos[1], p.pos[0]]))
      v0, start, dt = p.v.copy(), p.pos.copy(), 1e-4
      for _ in range(100):
        calc.move(p, dt)
      mid = (start + p.pos)/2
      g = sum((-b.GM*(mid - b.at(p.t/2))/np.linalg.norm(mid - b.at(p.t/2))**3 for b in calc.bodies), np.zeros(2))
      errors.append(np.linalg.norm((p.v - v0)/p.t - g))
    lines.append('    %-16s' % label + ''.join('%11.3g' % e for e in errors))
  lines.append('    (the Sun\'s tide at the surface, for scale: %.2e m/s^2)' % (2*G*MS*REARTH/AU**3))
  return lines


def constraint(folder):
  lines = ['einstein: (div u)^2 - du_i/dx_j du_j/dx_i round the Earth, over 4 c0/r^2 (c0 = GM_S/AU); the bodies at'
           ' rest gave 1', '    %8s' % 'r (R_E)' + ''.join('%10s' % ('%d deg' % a) for a in (30, 60, 90, 120, 150))]
  calc = turningCalc()
  c0 = G*MS/AU
  earth = calc.bodies[1]
  for radii in (2, 10, 30):
    row = []
    for a in (30, 60, 90, 120, 150):
      off = radii*REARTH*np.array([-math.cos(math.radians(a)), math.sin(math.radians(a))])
      #einstein() works about the x axis through the bodies: shift the Earth to the origin
      #and seen from the turning frame (its own turning has no symmetric part, but would spoil u_y/y)
      shifted = Calculator([Body(MS, -AU, 0.0), Body(ME)])
      relative = Relative(calc)
      shifted.flow = lambda x, side=None, t=0.0: relative.flow(x + earth.pos, side)
      shifted.region = lambda x, t=0.0: calc.region(x + earth.pos)
      row.append(einstein(shifted, off, shifted.bodies)/(4*c0/(radii*REARTH)**2))
    lines.append('    %8d' % radii + ''.join('%10.2e' % v for v in row))
  return lines


class Relative:
  """the turning flow seen from the turning frame (steady there): u - Omega x x, at t = 0"""
  def __init__(self, calc):
    self.calc = calc

  def flow(self, x, region=None, t=0.0):
    return self.calc.flow(x, region) - OMEGA*np.array([-x[1], x[0]])


def lunar(folder):
  lines = ['lunar: radar from the Earth\'s surface to a mirror at the Moon\'s distance, both turning with the Earth;'
           ' the round trip less the Earth\'s alone, as a range (c dt/2, at the Earth\'s clock)']
  calc = Relative(turningCalc())
  alone = Calculator([Body(ME)])
  earth = bodies()[1].pos
  rate = lambda c, x: math.sqrt(1 - (c.flow(x) @ c.flow(x))/C**2)
  ranges = []
  for D in range(0, 360, 30):
    out = np.array([-math.cos(math.radians(D)), math.sin(math.radians(D))])
    a, b = earth + REARTH*out, earth + DMOON*out
    here = roundTrip(calc, a, b)*rate(calc, a)
    there = roundTrip(alone, REARTH*out, DMOON*out)*rate(alone, REARTH*out)
    ranges.append(C*(here - there)/2)
  Ds = np.radians(np.arange(0, 360, 30))
  ms = np.array(ranges)
  lines.append('  by angle from the Sun (every 30 deg): ' + ' '.join('%.2e' % m for m in ms) + ' m')
  lines.append('  its cos D part %.2e m (bodies at rest: 0.111 m; LLR: 2.8 +- 4.1 mm); mean %.2e m'
               % (2*np.mean(ms*np.cos(Ds)), ms.mean()))
  return lines


class Swirl(SpecialFlowCalculator):
  """
  the Sun alone, its space coming in from far away with angular momentum L and energy 0 - u_r = -sqrt(2GM/r -
  L^2/r^2), u_phi = L/r - the flow with this J that could fill the plane past r_p = L^2/2GM. no curl, and
  |u|^2 = 2GM/r, so Newton and the clocks are right; light is the test
  """
  def __init__(self, L):
    super().__init__([Body(MS)], 2)
    self.L = L

  def flow(self, pos, region=None, t=0.0):
    r = np.linalg.norm(pos)
    radial = math.sqrt(max(0.0, 2*G*MS/r - (self.L/r)**2))
    rhat = pos/r
    return -radial*rhat + self.L/r*np.array([-rhat[1], rhat[0]])


def bend(calc, b, half=20*AU, fraction=0.002):
  """light leaving (b, -half) along +y (its v straight up), run in the model to y = +half: v's turn, towards the Sun"""
  p = Particle()
  p.pos = np.array([b, -half])
  u = calc.flow(p.pos)
  calc.initPV(p, np.array([0.0, u[1] + math.sqrt(C*C - u[0]**2)]))
  while p.pos[1] < half:
    calc.move(p, calc.stepSize(p, fraction, 0.01*AU/C))
  return math.atan2(-p.v[0], p.v[1])


def swirl(folder):
  L = -carriedJacobi(bodies(), OMEGA)/OMEGA
  lines = ['swirl: light passing the Sun through the flow that would fill the plane past %.3f AU (L = -J/Omega ='
           ' %.4e m^2/s), against the Sun\'s own flow straight in (GR); 20 AU either side' % (L*L/(2*G*MS)/AU, L),
           '    %8s %16s %16s %14s' % ('b (AU)', 'GR (uas)', 'swirl (uas)', 'difference')]
  uas = 180/math.pi*3600e6
  for b in (2.0, 3.0, 5.0):
    gr = bend(SpecialFlowCalculator([Body(MS)], 2), b*AU)
    sw = bend(Swirl(L), b*AU)
    lines.append('    %8.1f %16.1f %16.1f %13.1f%%' % (b, gr*uas, sw*uas, (sw - gr)/gr*100))
  lines.append('  (4GM/bc^2 at 2 AU is %.1f uas, less over a finite path; VLBI measures the Sun\'s bending, gamma, to'
               ' about 1 part in 10^4)' % (4*G*MS/(2*AU*C*C)*uas))
  return lines


def sun(folder):
  """the cost: the Sun's own region, whose paths (with no angular momentum) have energy J"""
  calc = turningCalc()
  J = calc.rayField().J
  sunPos = calc.bodies[0].pos
  lines = ['sun: round the Sun the flow is its paths with energy J (they leave it with no angular momentum):'
           ' |u|^2 = 2GM/r + 2J, so Einstein\'s constraint there is 4J/r^2 - the stretch, turned into a squeeze',
           '    %10s' % 'r (AU)' + ''.join('%10s' % ('%d deg' % a) for a in (30, 60, 90, 120, 150))]
  relative = Relative(calc)
  for r in (0.01, 0.1, 0.3):
    row = []
    for a in (30, 60, 90, 120, 150):
      off = r*AU*np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
      shifted = Calculator([Body(MS), Body(ME, AU, 0.0)])
      shifted.flow = lambda x, side=None, t=0.0: relative.flow(x + sunPos, side)
      shifted.region = lambda x, t=0.0: calc.region(x + sunPos)
      row.append(einstein(shifted, off, shifted.bodies)/(4*J/(r*AU)**2))
    lines.append('    %10.2f' % r + ''.join('%10.4f' % v for v in row))
  lines.append('  light passing the Sun, 0.5 AU either side (inside its region): the turning flow\'s bending against'
               ' the Sun\'s own flow straight in (GR)')
  lines.append('    %10s %14s %14s %14s %12s' % ('b (R_sun)', 'GR (mas)', 'turning (mas)', 'less (mas)', 'of GR'))
  mas = 180/math.pi*3600e3
  turning = turningCalc(SpecialFlowCalculator)
  for radii in (2, 10, 50):
    b = radii*RSUN
    gr = bendAt(SpecialFlowCalculator([Body(MS)], 2), np.zeros(2), b)
    tu = bendAt(turning, sunPos, b)
    lines.append('    %10d %14.4f %14.4f %14.4f %11.3f%%' % (radii, gr*mas, tu*mas, (tu - gr)*mas, (tu - gr)/gr*100))
  lines.append('  pi J/c^2 = %.2f mas (a cone\'s worth); Cassini measured gamma to 2.3 x 10^-5, about %.3f mas at 2'
               ' solar radii' % (math.pi*J/C**2*mas, 2.3e-5/2*4*G*MS/(2*RSUN*C*C)*mas))
  return lines


def bendAt(calc, centre, b, half=0.5*AU, fraction=0.001):
  """light from centre + (b, -half) along +y to y = +half, run in the model: v's turn towards the Sun (radians)"""
  p = Particle()
  p.pos = centre + np.array([b, -half])
  u = calc.flow(p.pos)
  calc.initPV(p, np.array([0.0, u[1] + math.sqrt(C*C - u[0]**2)]))
  while p.pos[1] < centre[1] + half:
    calc.move(p, calc.stepSize(p, fraction, 0.002*AU/C))
  return math.atan2(-p.v[0], p.v[1])


def main():
  folder = os.path.join(LOG_DIR, 'turningEikonal', 'turningEikonal_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = []
  for section in (paths, newton, constraint, lunar, swirl, sun):
    found = section(folder)
    lines += found + ['']
    print('\n'.join(found), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  return folder


if __name__ == '__main__':
  main()
