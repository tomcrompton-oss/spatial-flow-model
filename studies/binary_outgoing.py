"""
a binary's waves travelling outward across its own plane, for the viewer (docs Part 5): three ways of seeing them

  colour map  the strain h+ over the plane, from the quadrupole formula at the retarded time t - r/c
              (engine/radiation.py OutgoingWave): two spiral arms, red where space is stretched across the wave's
              way, blue squeezed, winding outward at c and fading as 1/r. inside half a wavelength (towards the near zone, where the
              formula doesn't hold) the arms are held at their strength there and fade smoothly out by FADED, so the
              orbits at the centre stay clear. for a circular orbit the pattern turns rigidly with the stars, so
              it is kept once, in their turning frame (engine/radiation.py starsFrame)
  arrows      u and g, the flow of space and its acceleration, as two backgrounds to choose between, never added: the
              stars' own flow over the whole plane, at its true scale (engine/radiation.py starFlow: each star's
              inflow from where it is), and the wave's - the plane-wave flow each ring moves in, within PATCH
              wavelengths of it (the model's flow for the outgoing wave is worked out only about each ring; it is a
              shear about the ring's centre), scaled up as the strain is, so thousands of times its true size; and a
              third, the stars' eikonal flow turning with them and the seam where their regions meet
              (engine/radiation.py TurningStars), within 4 a of them, where it holds
  rings       rings of free particles at one and two wavelengths out, in two directions, each moved by the flow model
              in its own patch of the outgoing wave: a plane wave along the way out (LocalPlaneWave), held exactly
              with curved space (engine/metric.py WaveSpacetime 'flow', MetricCalculator). the further rings stretch
              later and less; rings in other directions at other moments, as the arms sweep round

the binary: two 1.4 solar-mass bodies 100 km apart (waves at about 195 Hz, wavelength about 1,550 km), moving by
Newton plus the radiation reaction, run long enough for its waves to have crossed the box; the viewer keeps 8 wave
periods. the strain is scaled up so the rings at one wavelength stretch by about a quarter; the colour map shows
the same scaled strain

writes logs/binaryOutgoing/binaryOutgoing_<datetime>/: the bodies' and rings' csvs, logs,
binaryOutgoing.backgrounds.json (engine/backgrounds.py: the three backgrounds, with their descriptions), and
binaryOutgoing.full.json

run: python3 studies/binary_outgoing.py      (a few minutes; then: python3 scripts/publish_run.py logs/binaryOutgoing/...)
"""
import csv
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import Particle
from engine.metric import MetricCalculator, WaveSpacetime
from engine.radiation import Binary, OutgoingWave, LocalPlaneWave, starFlow, TurningStars, starsFrame
from engine.backgrounds import Backgrounds, polar, box as grid, LOG_LINE
from engine.logger import LOG_DIR
from engine.constants import *
from two_body_escapes import writeViewerFiles

M1 = M2 = 1.4*MS
A0 = 1e5                      #the bodies' separation at the start (m)
PERIODS = 8                   #wave periods kept
FRAMES = 8                    #background times a wave period: the turning frame's, and the rings' waves'
SHOWN = 0.25                  #the strain at one wavelength, scaled up to this
FADED = 1.5e5                 #the colour map fades to nothing by this radius (m), three times the bodies' orbit
RING = 0.15                   #the rings' radius, in wavelengths
PATCH = 0.4                   #each ring's wave flow is drawn within this many wavelengths of its centre
PARTICLES = 16
RINGS = [(1.0, 0), (2.0, 0), (1.0, 135), (2.0, 135)]   #(distance in wavelengths, direction in degrees)
COLOURS = ['#1baf7a', '#7fd4a8', '#8a5cd6', '#c3a8ee']
STEPS = 200                   #ring steps a wave period
EVERY = 10                    #steps between rows


def main():
  folder = os.path.join(LOG_DIR, 'binaryOutgoing', 'binaryOutgoing_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  GMt = G*(M1 + M2)
  fgw = 2*math.sqrt(GMt/A0**3)/(2*math.pi)
  lam = C/fgw
  period = 1/fgw
  box = 2.6*lam
  t0 = 1.5*math.hypot(box, box)/C                       #the waves have crossed the box by then
  t1 = t0 + PERIODS*period
  b = Binary(M1, M2, A0, 0.0).run(t1 + 0.01, 2000)
  peak = abs(OutgoingWave(b).plus(lam, 0.0, t0)).max()
  wave = OutgoingWave(b, scale=SHOWN/peak*1.0)
  #the colour map
  label = 'h+ (strain, scaled up %.3g times)' % wave.scale
  def field(X, Y, t):
    #inside half a wavelength the formula no longer holds: hold the arms' strength at what it is there (not rising as
    #1/r) and fade them smoothly to nothing by FADED, so the spiral runs on in towards the binary and the orbits show
    r = np.hypot(X, Y)
    f = np.clip((r - FADED)/(lam/2 - FADED), 0, 1)
    with np.errstate(divide='ignore', invalid='ignore'):
      out = wave.plus(X, Y, t)*np.minimum(1, r/(lam/2))*f*f*(3 - 2*f)
    return np.where(r > FADED, out, 0.0)
  logLines = '%s binaryOutgoing.backgrounds.json\n' % LOG_LINE
  made, patches = [], []
  #the bodies, over the kept window
  for n, (sign, mass) in enumerate(((1, M2), (-1, M1))):
    path = os.path.join(folder, 'body%d.csv' % (n + 1))
    with open(path, 'w', newline='') as f:
      out = csv.writer(f)
      out.writerow(['t', 'pos_x', 'pos_y', 'v_x', 'v_y'])
      for t in np.linspace(t0, t1, PERIODS*48 + 1):
        s = b.state(t)
        k = sign*mass/b.M
        out.writerow([t, k*s[0], k*s[1], k*s[2], k*s[3]])
    with open(path[:-4] + '.log', 'w') as f:
      f.write('%s\nbody %d: %.2f solar masses\n%s' % (b.describe(), n + 1, mass/MS, logLines))
    made.append((path, '#2a78d6' if n == 0 else '#eb6834', 'solid'))
  #the rings
  for k, ((dist, angle), colour) in enumerate(zip(RINGS, COLOURS)):
    a = math.radians(angle)
    P = dist*lam*np.array([math.cos(a), math.sin(a)])
    local = LocalPlaneWave(wave, P)
    local.tabulate(t0 - RING*lam/C - period, t1 + RING*lam/C + period)
    calc = MetricCalculator(WaveSpacetime(local, 'flow'))
    patches.append((calc, P, '%g wavelengths out at %d degrees' % (dist, angle)))
    ps = []
    for j in range(PARTICLES):
      th = 2*math.pi*j/PARTICLES
      xi = RING*lam*np.array([math.cos(th), math.sin(th)])
      p = Particle()
      p.t = t0
      h, _ = local.strain(local.when(P + xi, t0))
      p.pos = P + xi + h*float(local.across @ xi)/2*local.across     #round in TT coordinates
      calc.initPW(p, np.array([0.0, 0.0]))
      ps.append(p)
    rows = [[] for _ in ps]
    dt = period/STEPS
    for step in range(PERIODS*STEPS + 1):
      if step % EVERY == 0:
        for p, r in zip(ps, rows):
          r.append([p.t, p.pos[0], p.pos[1], p.v[0], p.v[1]])
      if step < PERIODS*STEPS:
        for p in ps:
          calc.move(p, dt)
    name = 'ring_%gl_%ddeg' % (dist, angle)
    path = os.path.join(folder, name + '.csv')
    with open(path, 'w', newline='') as f:
      out = csv.writer(f)
      out.writerow(['t', 'pos_x', 'pos_y', 'v_x', 'v_y'])
      for r in rows:
        out.writerows(r)
        out.writerow([''] * 5)
    widest = max(abs(np.linalg.norm(np.array(r[i][1:3]) - P)/(RING*lam) - 1) for r in rows for i in range(len(r)))
    with open(path[:-4] + '.log', 'w') as f:
      f.write('%s\n%d free particles on a ring of %.4g m round (%.4g, %.4g) m, %g wavelengths out at %d degrees; moved'
              ' by the flow model with curved space\nstretched by up to %.3f of its radius\n%s'
              % (local.describe(), PARTICLES, RING*lam, *P, dist, angle, widest, logLines))
    made.append((path, colour, 'dotted'))
    print('%s: stretched by up to %.3f of its radius' % (name, widest), flush=True)
  #the backgrounds (engine/backgrounds.py): three, never added together, each with the waves' strain behind it
  times = t0 + np.arange(PERIODS*FRAMES + 1)*period/FRAMES
  turningFrame, scaledFrame = starsFrame(b, times, scaled=False), starsFrame(b, times)
  first = []
  def strain(b):
    """the strain map behind b: worked out once, shared by the others (kept once in the file)"""
    if first:
      return b.share(first[0])
    first.append(b)
    return b.scalar(label, field, polar(FADED/2, 2*box, 200, 128), [t0], turningFrame)
  behind = (' Behind it, the waves\' strain h+, scaled up %.3g times: red where space is stretched across the wave\'s'
            ' way, blue where it is squeezed.' % wave.scale)
  bg = Backgrounds()
  strain(bg.add("the stars' flow, true scale",
                "The stars' own flow of space at its true scale: each star's inflow, sqrt(2GM/d), from where the star is"
                " at that moment (not where it was a light-travel time before), combined and pointing along g; g is the"
                " acceleration of space." + behind)
         ).field("the stars' flow", starFlow(b), polar(0.02*A0, 1000*A0), [t0], scaledFrame)
  rings = strain(bg.add('the wave about each ring, \u00d7%.3g' % wave.scale,
                        "The flow of space each ring moves in: the outgoing wave near the ring taken as a plane wave,"
                        " a shear about the ring's centre - scaled up %.3g times, as the strain is, so thousands of times"
                        " its true size. Drawn only near each ring, where the model's flow for the wave is worked out;"
                        " never added to the stars' flow, which is at its true scale." % wave.scale + behind))
  for calc, P, where in patches:
    side = PATCH*lam
    rings.field('the wave ' + where, calc, grid(P[0] - side, P[0] + side, P[1] - side, P[1] + side, 12, 12), times)
  stars_ = TurningStars(b)
  stars_.seam(t0)                                   #works out the seam's lines, in the reference orbit's frame
  turning = strain(bg.add("the stars' turning flow and its seam, within 4 a",
                          "The stars' eikonal flow turning with them, at its true scale: each star carries its own"
                          " flow, down zero-energy paths out of it, and their regions meet at the seam (dashed), which"
                          " turns with them. It is a Newtonian flow, built in the frame turning with the stars, which"
                          " moves at c about 5 orbit radii (a) out, so it is drawn only within 4 a." + behind))
  refFrame = starsFrame(b, times, ref=TurningStars.REF)     #its pattern: the reference orbit's, as stars_.lines
  turning.field("the stars' turning flow", stars_, polar(0.02*TurningStars.REF, 4.2*TurningStars.REF), [t0], refFrame)
  turning.lines("the seam, where the stars' regions of flow meet", lambda t: stars_.lines, [t0], refFrame)
  bg.write(os.path.join(folder, 'binaryOutgoing.backgrounds.json'))
  print('backgrounds written', flush=True)
  writeViewerFiles(folder, 'binaryOutgoing', made, preferences={'showFlow': False, 'showScalar': True})
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('%s\nwaves at %.1f Hz, wavelength %.0f km; box +-%.0f km; kept t = %.4f to %.4f s; strain scaled %.4g times\n'
            % (b.describe(), fgw, lam/1e3, box/1e3, t0, t1, wave.scale))
  print('written to', folder)


if __name__ == '__main__':
  main()
