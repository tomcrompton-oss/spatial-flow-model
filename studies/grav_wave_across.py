"""
a gravitational wave travelling across the screen, left to right (along +x, in the plane), in the flow model - and
where the model's version of it parts from GR (engine/waves.py: in the plane the wave also curves space, which the
model's flat space cannot, so its flow u = (1/2) h'(t - x/c) y (along y only) is the nearest it gets)

rings: a small ring (radius a twentieth of a wavelength) and a large one (half a wavelength) of free particles
(w = 0), in a 100 Hz plus wave (wavelength 2998 km) whose front crosses x = 0 at t = 0 and sweeps right, at h = 0.2
so it shows. the wave is transverse: the rings squeeze and stretch along y only, the large one in a ripple, as the
wave's phase changes across it. each ring is round in TT coordinates. with DYNAMIC_BACKGROUNDS (on; --static turns
it off) the wave's flow is written as frames (engine/background_frames.py), so the viewer's u arrows and lines of
equal |u| sweep across with it in a replay

checks, at h = 1e-6, against GR to first order in h (TT coordinates, ds^2 = -c^2 dt^2 + dx^2 + (1 + h) dy^2):
  light   radar from the centre to a free mirror at L, at angles from the wave's direction, and back: GR's time is
          2 L/c + the integral of h e_y^2/2 along the light's path, at the wave's time there. the error, as a
          fraction of h L/c, shows where the flat-space flow parts from GR
  fast    particles moving along the wave at speed v, y0 from its line: GR keeps them at their TT y, so
          y = y0 (1 + h(t - x/c)/2); the model's, as a fraction of h y0
each is done twice: by the model, and by the true geodesics of the flow-only metric (Geodesic, Hamilton's equations)
- which tells what the flat-space flow itself gets wrong (the curvature it cannot hold) from what the model's step
adds (its step is the flow's geodesic only where the flow has no curl; this one has curl). and, as a control, all of
it again for a wave along z, through the plane, where the flow is exact and has no curl: there all three agree

found (checks.log): light along or across the wave is right at any distance, and the model's light is the flow's
geodesic exactly; light at an angle is off by about (L/wavelength)/2 of h L/c, for short arms, up to 0.46 of it at a
wavelength - all from flat space. particles moving fast along the wave are off by ~3 h y0 from flat space (0.2 at
0.99c, nearly riding with the wave) and by up to ~30 h y0 from the model's step. the control agrees to ~1e-6

writes logs/gravWaveAcross/gravWaveAcross_<datetime>/: per ring a csv of its particles' paths (ring_<name>, dotted)
and of its shape at 8 moments in the last period (shapes_<name>), logs naming the frames, gravWaveAcross.full.json for
the viewer, and checks.log

run: python3 studies/grav_wave_across.py [--static]
"""
import copy
import csv
import math
import os
import shutil
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import SpecialFlowCalculator, Particle
from engine.waves import PlaneWave
from engine.logger import Log, LOG_DIR
from engine.background_frames import writeFrames, LOG_LINE
from engine.constants import *
from two_body_escapes import writeViewerFiles

FREQUENCY = 100.0
WAVELENGTH = C/FREQUENCY
SHOWN = 0.2
PERIODS = 3           #the rings' run: long enough for the front to cross the large ring
STEPS = 400           #steps a period
EVERY = 4             #steps between csv rows
SHAPES = 8
DYNAMIC_BACKGROUNDS = True
FRAMES = 32           #background frames a period
FRAME_BOX = (-4.0e6, 4.5e6, -1.8e6, 1.8e6)   #the frames' grid (m)
FRAME_CELLS = (48, 21)
RINGS = [   #(name, centre x (m), radius (m), particles, colour)
  ('small', -3.0e6, WAVELENGTH/20, 24, '#2a78d6'),
  ('large', 2.5e6, WAVELENGTH/2, 48, '#eb6834'),
]
SMALL = 1e-6
ANGLES = (0, 30, 45, 60, 90)                  #degrees from the wave's direction
DISTANCES = (0.01, 0.1, 0.25, 0.5, 1.0)       #wavelengths
SPEEDS = (0.0, 0.5, 0.9, 0.99)                #fast particles: v/c along the wave


def ringRun(folder, calc, name, x, radius, count):
  """one ring's csvs and log, in the wave of calc; returns their paths"""
  wave = calc.wave
  log = Log('ring_' + name, True, False, folder)
  calc.log = log
  log.logBodies(calc)
  log.print('%d free particles (w = 0) on a ring of %g m (%.3g wavelengths) round (%g, 0) m, round in TT coordinates;'
            ' %d periods, %d steps a period' % (count, radius, radius/WAVELENGTH, x, PERIODS, STEPS))
  dt = 1/FREQUENCY/STEPS
  path = log.file.name[:-4] + '.csv'
  every = PERIODS*STEPS - STEPS + np.arange(SHAPES)*STEPS//SHAPES
  shapes = {step: [] for step in every}
  with open(path, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'pos_x', 'pos_y', 'v_x', 'v_y', 'u_x', 'u_y'])
    for n in range(count):
      a = 2*math.pi*n/count
      tt = np.array([x + radius*math.cos(a), radius*math.sin(a)])
      p = Particle()
      p.pos = tt + np.array([0.0, tt[1]*wave.strain(wave.when(tt, 0.0))[0]/2])   #M = y (1 + h/2)
      calc.initPW(p, np.array([0.0, 0.0]))
      for step in range(PERIODS*STEPS + 1):
        if step % EVERY == 0:
          out.writerow([p.t, p.pos[0], p.pos[1], p.v[0], p.v[1], p.u[0], p.u[1]])
        if step in shapes:
          shapes[step].append((p.t, p.pos.copy()))
        if step < PERIODS*STEPS:
          calc.move(p, dt)
      out.writerow([''] * 7)
  shapePath = os.path.join(folder, os.path.basename(path).replace('ring_', 'shapes_', 1))
  with open(shapePath, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'pos_x', 'pos_y'])
    for step in every:
      for t, pos in shapes[step] + shapes[step][:1]:
        out.writerow([t, pos[0], pos[1]])
      out.writerow([''] * 3)
  return log, path, shapePath


def radar(calc, mirrorPos, e, t0, steps=4000):
  """light from the wave's centre along e to a free mirror at mirrorPos and back: the time it takes"""
  origin = calc.wave.centre
  light, mirror = Particle(), Particle()
  light.t = mirror.t = t0
  light.pos, mirror.pos = origin.copy(), np.array(mirrorPos, dtype=float)
  calc.initPW(light, C*e)
  calc.initPW(mirror, np.array([0.0, 0.0]))
  dt = 2*np.dot(mirror.pos - origin, e)/C/steps
  out = True
  gap = lambda l, m: np.dot((m.pos - l.pos) if out else (l.pos - origin), e)
  while True:
    before = copy.deepcopy(light), copy.deepcopy(mirror)
    calc.move(light, dt)
    calc.move(mirror, dt)
    g = gap(light, mirror)
    if g > 0:
      continue
    lo, hi, glo, ghi = 0.0, dt, gap(*before), g
    for _ in range(40):
      f = lo - glo*(hi - lo)/(ghi - glo)
      light, mirror = copy.deepcopy(before[0]), copy.deepcopy(before[1])
      calc.move(light, f)
      calc.move(mirror, f)
      g = gap(light, mirror)
      if abs(g) < 1e-9:
        break
      lo, glo, hi, ghi = (f, g, hi, ghi) if g > 0 else (lo, glo, f, g)
    if not out:
      return light.t - t0
    light.w = light.w - 2*np.dot(light.w, e)*e   #the mirror is at rest in its space: w reverses along the arm
    light.v = light.w + light.u
    out = False


def grRadar(wave, e, L, t0, points=4001):
  """
  GR's radar time to a mirror at TT distance L along e and back: 2L/c + 1/2c times the integral of h_ee along the
  light's path, at the wave's time there (h_ee = h+ (e.m)^2 for a wave in the plane; h+ (ex^2 - ey^2) + 2 hx ex ey
  for one along z)
  """
  s = np.linspace(0, L, points)
  if wave.along is None:
    along = lambda tau: np.array([wave.strain(t)[0]*(e[0]**2 - e[1]**2) + 2*wave.strain(t)[1]*e[0]*e[1] for t in tau])
    en = 0.0
  else:
    em = float(np.dot(e, wave.across))
    along = lambda tau: np.array([wave.strain(t)[0]*em*em for t in tau])
    en = float(np.dot(e, wave.along))
  out = along(t0 + s/C - s*en/C)                       #at s along the arm, on the way out
  back = along(t0 + L/C + s/C - (L - s)*en/C)          #s back from the mirror
  simpson = lambda f: (s[1] - s[0])/3*(f[0] + f[-1] + 4*f[1:-1:2].sum() + 2*f[2:-1:2].sum())
  return 2*L/C + (simpson(out) + simpson(back))/(2*C)


class Geodesic:
  """
  the true paths of the flow-only metric ds^2 = -c^2 dt^2 + |dx - u dt|^2 (u the wave's flow), by Hamilton's equations
  - x' = u + w, p' = -(grad u) . p, with p = gamma w (for light, p along w) - moving Particles as the calculators do.
  the model's own step takes w' = -(w . grad) u instead, which is the same only where u has no curl; the wave in the
  plane has curl (du_y/dx = -h'' y/2c), so this tells the model's step apart from the flat-space flow itself
  """

  def __init__(self, wave):
    self.wave = wave

  def initPW(self, p, w):
    p.w = np.array(w, dtype=float)
    p.u = self.wave.flow(p.pos, p.t)
    p.v = p.w + p.u

  def initPV(self, p, v):
    p.u = self.wave.flow(p.pos, p.t)
    p.v = np.array(v, dtype=float)
    p.w = p.v - p.u

  def rates(self, t, x, q, light):
    flow = lambda at: self.wave.flow(at, t)
    h = 1e-3*max(1.0, float(np.max(np.abs(x))))
    grad = np.array([(flow(x + [h, 0.0]) - flow(x - [h, 0.0]))/(2*h), (flow(x + [0.0, h]) - flow(x - [0.0, h]))/(2*h)])
    w = C*q/np.linalg.norm(q) if light else C*q/math.sqrt(C*C + q @ q)
    return flow(x) + w, -grad @ q

  def move(self, p, dt):
    light = abs(np.linalg.norm(p.w) - C) < 1e-9*C
    q = p.w if light else p.w/math.sqrt(1 - (p.w @ p.w)/C**2)
    x, t = p.pos, p.t
    k1 = self.rates(t, x, q, light)
    k2 = self.rates(t + dt/2, x + k1[0]*dt/2, q + k1[1]*dt/2, light)
    k3 = self.rates(t + dt/2, x + k2[0]*dt/2, q + k2[1]*dt/2, light)
    k4 = self.rates(t + dt, x + k3[0]*dt, q + k3[1]*dt, light)
    p.pos = x + (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])*dt/6
    q = q + (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])*dt/6
    p.t = t + dt
    p.w = C*q/np.linalg.norm(q) if light else C*q/math.sqrt(C*C + q @ q)
    p.u = self.wave.flow(p.pos, p.t)
    p.v = p.w + p.u


def lightChecks(lines, wave):
  """
  radar at h = SMALL against GR, for the model and for the flow-only metric's geodesics; returns the worst errors
  (fraction of h L/c) by distance, for each
  """
  movers = [('the model', SpecialFlowCalculator([], 2, wave=wave)), ('the flow-only metric (true geodesics)', Geodesic(wave))]
  t0 = 0.002
  way = 'along z, through the plane' if wave.along is None else 'along x, in the plane'
  worst = {}
  for title, mover in movers:
    lines.append('light, %s: radar from the centre to a free mirror and back, h = %g, %g Hz (wavelength %g km), the'
                 ' wave %s; error / (h L/c) by distance and angle from x' % (title, SMALL, FREQUENCY, WAVELENGTH/1000, way))
    lines.append('  %-10s' % 'L/lambda' + ''.join('%11s' % ('%d deg' % a) for a in ANGLES))
    worst[title] = {}
    for fraction in DISTANCES:
      L = fraction*WAVELENGTH
      row = []
      for angle in ANGLES:
        e = np.array([math.cos(math.radians(angle)), math.sin(math.radians(angle))])
        T = radar(mover, mirrorAt(wave, L, e, t0), e, t0)
        error = (T - grRadar(wave, e, L, t0))/(SMALL*L/C)
        row.append(error)
        worst[title][fraction] = max(worst[title].get(fraction, 0.0), abs(error))
      lines.append('  %-10g' % fraction + ''.join('%11.2e' % v for v in row))
    lines.append('')
  return worst


def mirrorAt(wave, L, e, t0):
  """
  where a mirror at TT distance L along e from the centre is at t0, in the model's coordinates: the TT coordinates
  stretched by h/2 (the strain matrix, for a wave along z; across the wave only, for one in the plane)
  """
  X = L*e
  if wave.along is None:
    hp, hx = wave.strain(t0)
    return wave.centre + X + np.array([hp*X[0] + hx*X[1], hx*X[0] - hp*X[1]])/2
  en, em = float(np.dot(e, wave.along)), float(np.dot(e, wave.across))
  return wave.centre + L*(en*wave.along + em*(1 + wave.strain(wave.when(X + wave.centre, t0))[0]/2)*wave.across)


def fastChecks(lines, wave):
  """
  particles moving along x at v, y0 from the centre's line, for two periods, against GR (they keep their TT y, so
  their model y is y0 (1 + h(t - x/c)/2)): the worst error (fraction of h y0) by speed, for the model and the
  geodesics
  """
  y0 = 0.05*WAVELENGTH
  movers = [('model', SpecialFlowCalculator([], 2, wave=wave)), ('geodesic', Geodesic(wave))]
  lines.append('fast particles: moving along x at v, %g km off the x axis, two periods; GR keeps them at their TT y;'
               ' error / (h y0)' % (y0/1000))
  lines.append('  %-10s %12s %12s' % ('v/c', 'model', 'geodesic'))
  results = {}
  for speed in SPEEDS:
    row = []
    for name, mover in movers:
      start = np.array([0.0, y0])
      p = Particle()
      if wave.along is None:   #through the plane: stretched by h(t)/2 everywhere, x too (along x, y0 off it: y only)
        hp, hx = wave.strain(0.0)
        p.pos = start + np.array([hx*y0, -hp*y0])/2
        rp, rx = wave.rate(0.0)
        mover.initPV(p, np.array([speed*C, 0.0]) + np.array([rx*y0, -rp*y0])/2)
      else:
        tau = wave.when(start + wave.centre, 0.0)
        p.pos = wave.centre + np.array([0.0, y0*(1 + wave.strain(tau)[0]/2)])
        #v along x, and the rate its stretched y changes as it goes, h'(1 - v/c) y0/2
        mover.initPV(p, np.array([speed*C, y0*wave.rate(tau)[0]*(1 - speed)/2]))
      worst = 0.0
      dt = 1/FREQUENCY/2000
      for _ in range(4000):
        mover.move(p, dt)
        if wave.along is None:
          hp, hx = wave.strain(p.t)
          want = y0 - hp*y0/2 + hx*speed*C*p.t/2
        else:
          want = y0*(1 + wave.strain(wave.when(np.array([speed*C*p.t, 0.0]) + wave.centre, p.t))[0]/2)
        worst = max(worst, abs(p.pos[1] - want)/(SMALL*y0))
      row.append(worst)
    results[speed] = row
    lines.append('  %-10g %12.2e %12.2e' % (speed, *row))
  lines.append('')
  return results


def main():
  folder = os.path.join(LOG_DIR, 'gravWaveAcross', 'gravWaveAcross_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  wave = PlaneWave(plus=SHOWN, frequency=FREQUENCY, along=(1, 0))
  calc = SpecialFlowCalculator([], 2, wave=wave)
  framesName = None
  if DYNAMIC_BACKGROUNDS:
    framesName = 'background_%s.csv' % os.path.basename(folder).split('_', 1)[1]
    writeFrames(os.path.join(folder, framesName), calc, FRAME_BOX, np.arange(PERIODS*FRAMES + 1)/FRAMES/FREQUENCY,
                FRAME_CELLS)
  made = []
  for name, x, radius, count, colour in RINGS:
    log, tracks, shapes = ringRun(folder, calc, name, x, radius, count)
    if framesName:
      log.print(LOG_LINE, framesName)
    log.close()
    shutil.copy(tracks[:-4] + '.log', shapes[:-4] + '.log')
    made += [(shapes, colour, 'solid'), (tracks, colour, 'dotted')]
  writeViewerFiles(folder, 'gravWaveAcross', made, preferences={'showFlow': DYNAMIC_BACKGROUNDS})
  lines = ['a gravitational wave travelling along x, in the plane: the flow model against GR, to first order in h',
           'each check also with the true geodesics of the flow-only metric (Geodesic), to tell the model\'s step from',
           'the flat-space flow itself; and, as a control, the same checks for a wave along z (through the plane), whose',
           'flow is exact and has no curl', '']
  across = PlaneWave(plus=SMALL, frequency=FREQUENCY, phasePlus=0.4, start=-1.0, along=(1, 0))   #everywhere already
  through = PlaneWave(plus=SMALL, frequency=FREQUENCY, phasePlus=0.4, start=-1.0)
  light = lightChecks(lines, across)
  fast = fastChecks(lines, across)
  lines += ['control: the wave along z', '']
  controlLight = lightChecks(lines, through)
  controlFast = fastChecks(lines, through)
  for name, worst in (('in the plane', light), ('control, along z', controlLight)):
    for title, byDistance in worst.items():
      lines.append('worst light error, %s, %s: %s' % (name, title, ', '.join('%g wavelengths %.1e' % kv for kv in byDistance.items())))
  for name, worst in (('in the plane', fast), ('control, along z', controlFast)):
    lines.append('worst fast-particle error, %s (model, geodesic): %s' % (name, ', '.join('%gc %.1e / %.1e' % (v, *r) for v, r in worst.items())))
  with open(os.path.join(folder, 'checks.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines))
  return folder


if __name__ == '__main__':
  if '--static' in sys.argv[1:]:
    DYNAMIC_BACKGROUNDS = False
  main()
