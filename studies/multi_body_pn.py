"""
beyond Newton with more than one body - the fourth multi-body question. with the flows combined by their squares,
|u|^2 = 2 sum GM/d, pointing down the eikonal paths (engine/two_centre.py), clocks and slow bodies follow GR's first
order (studies/multi_body_rules.py, multi_body_clocks.py), and for one body the flow is GR exactly. but round a body
in another's field, the other's potential c0 = GM'/D is in |u|^2 too: round the Earth, space falls in at
sqrt(2GM/r + 2 c0) - 43.6 km/s at the surface, not 11.2. in GR a uniform potential changes nothing that can be
measured there; in the flow the radial distances round the body stretch, by c0/c^2 (the static form of the metric,
-(c^2 - u^2) dT^2 + c^2 dr^2/(c^2 - u^2) + r^2 dphi^2, has g_rr's 2GM/r and also 2 c0). in GR's terms the flow is not
empty space: Einstein's equations ask that (div u)^2 - du_i/dx_j du_j/dx_i = 0 outside matter (the flat slices'
constraint), and for this flow it is 4 c0/r^2. each run in the flow model, the bodies at rest:

  lunar     radar from the Earth's surface to a mirror at the Moon's distance and back, the Sun 1 AU away, at each
            angle from the Sun (the Moon's synodic phase, D): the round trip less the Earth's alone (GR's for the Earth
            alone, with the Sun only adding a tide of under a micrometre), as a range, c dt/2, against how big the
            mirror's orbit is (its circumference over 2 pi, which the flow leaves alone). the round trip is worked out
            along the straight line (light's bending changes it only to second order) and checked by light run in
            the model; and at the Earth's nearest to the Sun and farthest, for the change over the year. against
            lunar laser ranging's fit to the synodic range term, (2.8 +- 4.1) mm cos D
  jupiter   light passing Jupiter, the Sun 5.2 AU away: the bending with both, less the Sun's alone and Jupiter's alone
            (in GR they add, to first order in G); light run in the model, 10 AU either side, at 1 to 1000 Jupiter
            radii, on the side away from the Sun. against Jupiter's own bending, and VLBI's measurement of it
            (1190 microarcseconds at 3.7 arcminutes, positions to under 10)
  constraint  Einstein's constraint round the Earth and Jupiter: (div u)^2 - du_i/dx_j du_j/dx_i, from the flow by
            differences (in 3d: about the line through both bodies, the flow's third rate is u_y/y), against 4 c0/r^2

writes logs/multiBody/multiBodyPN_<datetime>/: a csv of the lunar range by angle, a viewer file (multiBody_lunar.full
.json) and summary.log

run: python3 studies/multi_body_pn.py      (then: python3 scripts/publish_run.py logs/multiBody/multiBodyPN_<datetime>)
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

DMOON = 3.844e8
MJ, RJ = 1.898e27, 7.1492e7      #Jupiter's mass, equatorial radius
DJ = 7.785e11                    #Jupiter to the Sun
PERIHELION, APHELION = 0.98329*AU, 1.01671*AU
NODES, WEIGHTS = np.polynomial.legendre.leggauss(16)


def roundTrip(calc, a, b, pieces=400):
  """
  light's round trip a -> b -> a in the model's time, along the straight line: in a steady flow it crosses each
  length dl at c+ along the line one way and c- the other, and 1/c+ + 1/c- = 2 sqrt(c^2 - u_perp^2)/(c^2 - u^2).
  pieces spaced in log distance from a (Gauss-Legendre in each)
  """
  span = np.linalg.norm(b - a)
  n = (b - a)/span
  edges = np.concatenate([[0.0], np.geomspace(1.0, span, pieces)])
  total = 0.0
  for lo, hi in zip(edges[:-1], edges[1:]):
    for x, wt in zip(NODES, WEIGHTS):
      s = (lo + hi)/2 + (hi - lo)/2*x
      u = calc.flow(a + s*n)
      along = u @ n
      perp2 = u @ u - along*along
      total += wt*(hi - lo)/2*2*math.sqrt(C*C - perp2)/(C*C - u @ u)
  return total


def emitterRate(calc, x):
  u = calc.flow(x)
  return math.sqrt(1 - (u @ u)/C**2)


def radar(calc, a, b, fraction=0.002):
  """the same round trip by light run in the model: aimed (by secant steps on the miss) from a to b, then back"""
  def leg(start, end, t0):
    aim0 = math.atan2(*(end - start)[::-1])
    def shoot(angle):
      p = Particle()
      p.pos, p.t = start.copy(), t0
      calc.initPW(p, C*np.array([math.cos(angle), math.sin(angle)]))
      span = np.linalg.norm(end - start)
      n = (end - start)/span
      while (p.pos - start) @ n < span:
        last = (p.pos.copy(), p.t)
        calc.move(p, calc.stepSize(p, fraction, 0.2*max(np.linalg.norm(end - p.pos), 1e3)/C))
      #back to where it crosses the line through end, square to the way it went
      over = (p.pos - start) @ n - span
      back = over/((p.pos - last[0]) @ n)
      pos = p.pos - back*(p.pos - last[0])
      t = p.t - back*(p.t - last[1])
      off = pos - end
      return n[0]*off[1] - n[1]*off[0], t
    x0, x1 = aim0, aim0 + 1e-9
    f0, t = shoot(x0)
    f1, t = shoot(x1)
    for _ in range(8):
      if f1 == f0 or abs(f1) < 1e-4:
        break
      x0, x1, f0 = x1, x1 - f1*(x1 - x0)/(f1 - f0), f1
      f1, t = shoot(x1)
    return t
  there = leg(a, b, 0.0)
  return leg(b, a, there)


def lunar(folder):
  lines = ['lunar: radar from the Earth\'s surface to a mirror at the Moon\'s distance (%.0f km), the Sun 1 AU away, by'
           ' the mirror\'s angle from the Sun (D); the round trip less the Earth\'s alone, as a range (c dt/2, at the'
           ' Earth\'s clock), against the mirror\'s orbit\'s size' % (DMOON/1000)]
  alone = Calculator([Body(ME)])
  def extra(sunDistance, D, calc=None):
    calc = calc or Calculator([Body(MS, -sunDistance, 0.0), Body(ME)])
    out = np.array([-math.cos(math.radians(D)), math.sin(math.radians(D))])
    a, b = REARTH*out, DMOON*out
    withSun = roundTrip(calc, a, b)*emitterRate(calc, a)
    return C*(withSun - roundTrip(alone, a, b)*emitterRate(alone, a))/2, calc
  c0 = G*MS/AU
  lines.append('  the Sun\'s potential at the Earth, c0/c^2 = %.4e; c0/c^2 times the distance from the surface: %.3f m'
               % (c0/C**2, c0/C**2*(DMOON - REARTH)))
  lines.append('  %8s %14s %10s' % ('D (deg)', 'range (m)', 'in region'))
  rows, calc = [], None
  for D in range(0, 361, 10):
    metres, calc = extra(AU, D, calc)
    out = np.array([-math.cos(math.radians(D)), math.sin(math.radians(D))])
    region = 'Earth' if calc.region(DMOON*out) == 1 else 'Sun'
    rows.append((D, metres))
    if D % 30 == 0:
      lines.append('  %8d %14.4f %10s' % (D, metres, region))
  Ds = np.radians([r[0] for r in rows[:-1]])
  ms = np.array([r[1] for r in rows[:-1]])
  cosD = 2*np.mean(ms*np.cos(Ds))
  lines.append('  its cos D part: %.3f m; mean %.3f m; swing over the month %.3f m'
               % (cosD, ms.mean(), (ms.max() - ms.min())/2))
  lines.append('  lunar laser ranging (Williams, Turyshev and Boggs 2004): (2.8 +- 4.1) mm cos D - the flow\'s is %.0f'
               ' times the uncertainty' % (abs(cosD)/0.0041))
  near, _ = extra(PERIHELION, 90)
  far, _ = extra(APHELION, 90)
  lines.append('  over the year (D = 90): %.4f m at perihelion, %.4f m at aphelion - a swing of %.1f cm'
               % (near, far, (near - far)/2*100))
  tide = G*MS*DMOON**2/AU**3/C**2*DMOON
  lines.append('  GR: the Sun adds only its tide, about GM_S D_moon^3/(AU^3 c^2) = %.1e m' % tide)
  #the same round trip by light run in the model, twice
  for D in (90, 0):
    out = np.array([-math.cos(math.radians(D)), math.sin(math.radians(D))])
    a, b = REARTH*out, DMOON*out
    checks = []
    for c in (SpecialFlowCalculator([Body(MS, -AU, 0.0), Body(ME)]), SpecialFlowCalculator([Body(ME)])):
      run, line = radar(c, a, b), roundTrip(c, a, b)
      checks.append((run, line))
    run = C*(checks[0][0]*emitterRate(calc, a) - checks[1][0]*emitterRate(alone, a))/2
    lines.append('  check, D = %d: light run in the model gives %.4f m (the straight line %.4f); its round trips'
                 ' differ from the line\'s by %.2e and %.2e s' % (D, run, extra(AU, D, calc)[0],
                                                                    checks[0][0] - checks[0][1], checks[1][0] - checks[1][1]))
  path = write(folder, 'lunar_range', calc, rows, ['D', 'range_m'],
               ['the extra lunar range (m) the Sun\'s potential makes in the flow, by angle D from the Sun'] + lines[-6:])
  writeViewerFiles(folder, 'multiBody_lunar', [(path, COLOURS[0])], selection=(('D', 'range_m'),),
                   styles=lambda colour, style='solid': {'D / range_m': [colour, style, colour]},
                   preferences={'equalAspect': False, 'showBodies': False, 'showFlow': False})
  return lines


def bend(calc, b, half=10*AU, fraction=0.002):
  """light leaving (DJ + b, -half) along +y (its v straight up), run in the model to y = +half: v's turn (radians)"""
  p = Particle()
  p.pos = np.array([DJ + b, -half])
  u = calc.flow(p.pos) if calc.bodies else np.array([0.0, 0.0])
  speed = u[1] + math.sqrt(C*C - u[0]**2)          #|v y^ - u| = c
  calc.initPV(p, np.array([0.0, speed]))
  while p.pos[1] < half:
    calc.move(p, calc.stepSize(p, fraction, 0.01*AU/C))
  return math.atan2(-p.v[0], p.v[1])               #towards -x (the Sun and Jupiter) positive


def jupiter(folder):
  lines = ['jupiter: light passing Jupiter on the side away from the Sun (5.2 AU off), 10 AU either side: the bending'
           ' with both less the Sun\'s alone and Jupiter\'s alone (GR: 0 to first order in G)',
           '  %10s %16s %16s %16s %16s' % ('b (R_J)', 'Jupiter (uas)', 'GR 4GM/bc^2', 'both - each', 'of Jupiter\'s')]
  uas = 180/math.pi*3600e6
  sun, jup = Body(MS, 0.0, 0.0), Body(MJ, DJ, 0.0)
  found = {}
  for radii in (1, 10, 100, 1000):
    b = radii*RJ
    both = bend(SpecialFlowCalculator([sun, jup]), b)
    s = bend(SpecialFlowCalculator([sun]), b)
    j = bend(SpecialFlowCalculator([jup]), b)
    gr = 4*G*MJ/(b*C*C)
    found[radii] = both - s - j
    lines.append('  %10d %16.2f %16.2f %16.3f %15.1f%%' % (radii, j*uas, gr*uas, (both - s - j)*uas, (both - s - j)/j*100))
  c0 = G*MS/DJ
  lines.append('  the Sun\'s potential at Jupiter, c0/c^2 = %.3e; pi c0/c^2 = %.0f uas (the bending a cone\'s stretch'
               ' of c0/c^2 would give a line passing right through Jupiter\'s region)' % (c0/C**2, math.pi*c0/C**2*uas))
  lines.append('  VLBI (Fomalont and Kopeikin 2003): Jupiter\'s bending 1190 uas at 3.7 arcmin (so b = %.1f R_J),'
               ' positions to under 10 uas' % (4*G*MJ/(C*C*RJ)*uas/1190))
  return lines


def constraint(folder):
  lines = ['constraint: Einstein\'s (div u)^2 - du_i/dx_j du_j/dx_i (0 in empty space, in GR), here over 4 c0/r^2,'
           ' round each body in the other\'s field (angle from the side facing the other body)']
  for title, bodies, R in (('the Earth, the Sun 1 AU away', [Body(MS, -AU, 0.0), Body(ME)], REARTH),
                           ('Jupiter, the Sun 5.2 AU away', [Body(MS, -DJ, 0.0), Body(MJ)], RJ)):
    calc = Calculator(bodies)
    c0 = bodies[0].GM/abs(bodies[0].x)
    lines.append('  %s:' % title)
    lines.append('    %12s' % 'r (radii)' + ''.join('%10s' % ('%d deg' % a) for a in (30, 60, 90, 120, 150)))
    one = Calculator([bodies[1]])
    for radii in (2, 10, 30):
      row = []
      for a in (30, 60, 90, 120, 150):
        pos = radii*R*np.array([-math.cos(math.radians(a)), math.sin(math.radians(a))])
        row.append(einstein(calc, pos, bodies)/(4*c0/(radii*R)**2))
      lines.append('    %12d' % radii + ''.join('%10.4f' % v for v in row))
    pos = 10*R*np.array([0.0, 1.0])
    lines.append('    (the body alone, at 10 radii: %.1e of that)' % (einstein(one, pos, bodies)/(4*c0/(10*R)**2)))
  return lines


def einstein(calc, pos, bodies):
  """(div u)^2 - du_i/dx_j du_j/dx_i at pos, in 3d about the line through the bodies (here the x axis)"""
  h = 1e-4*np.linalg.norm(pos)
  side = calc.region(pos)
  f = lambda x: calc.flow(x, side)
  J = np.array([(f(pos + [h, 0.0]) - f(pos - [h, 0.0]))/(2*h), (f(pos + [0.0, h]) - f(pos - [0.0, h]))/(2*h)])
  third = f(pos)[1]/pos[1]                         #d u_phi/(rho dphi) + u_rho/rho, about the axis
  rates = [J[0][0], J[1][1], third]
  div = sum(rates)
  return div*div - (J[0][0]**2 + J[1][1]**2 + 2*J[0][1]*J[1][0] + third**2)


def main():
  folder = os.path.join(LOG_DIR, 'multiBody', 'multiBodyPN_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = []
  for section in (constraint, lunar, jupiter):
    found = section(folder)
    lines += found + ['']
    print('\n'.join(found), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  return folder


if __name__ == '__main__':
  main()
