"""
a plane gravitational wave passing through the plane (engine/waves.py) in the flow model, with no bodies: the wave is
a flow of space, u = (1/2) (h+' x + hx' y, hx' x - h+' y), and everything else is the flow model's usual rules

rings: three rings of 24 free particles (moving with space, w = 0) at 100 km, in a wave of 100 Hz, for two periods -
plus polarization (left), cross (middle), circular (right: plus and cross a quarter period apart) - at h = 0.2 so the
stretching and squeezing shows. each ring is round in TT coordinates (a circular wave's strain is never 0, so in
proper distance it starts as an ellipse). the model is first order in h: at this size it also drifts slowly from
GR's ring, by about h^3 of the radius a period

checks, at h = 1e-6, against GR to first order in h (TT coordinates):
  free     particles moving with space stay at fixed TT coordinates: X = X0 + h X0/2 (h the strain matrix)
  at rest  particles starting at rest in the background (v = 0) move as geodesic deviation says, X'' = h'' X/2:
           X = X0 + (h(t) - h(0) - h'(0) t) X0/2
  light    a round trip from the centre to a free mirror at L and back takes 2 L_TT/c + (1/2) integral of h_ee dt
           (e the arm's direction, L_TT = L (1 - h_ee(0)/2) the mirror's TT distance), for arms from 0.01 to 1.3
           wavelengths: the wave's change during the trip included
each error is given as a fraction of the wave's effect (h X0, or h L/c)

DYNAMIC_BACKGROUNDS (on; --static turns it off): each ring's flow - and the acceleration of space - on a grid at 32
moments a period (background_<name>, engine/background_frames.py), named in its log, so the viewer's backgrounds (u
and g arrows, lines of equal |u|) follow the wave during a replay; pick a ring's environment under Background

writes logs/gravWave/gravWave_<datetime>/: per ring a csv of its particles' paths (ring_<name>: an empty row ending
each, drawn dotted), a csv of its shape at 8 moments (shapes_<name>) through the last period (solid) and a log; gravWave.full.json to open them
in the viewer, and checks.log

run: python3 studies/grav_wave.py [--static]      (then: python3 viewer/csv_viewer.py logs/gravWave/gravWave_<datetime>/gravWave.full.json)
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

FREQUENCY = 100.0     #Hz
RADIUS = 1e5          #the rings' radius (m)
PARTICLES = 24        #per ring
SHOWN = 0.2           #the rings' strain, large enough to see
SHAPES = 8            #moments in the last period at which each ring's shape is written
PERIODS = 2           #how long the rings run
STEPS = 400           #steps a period
EVERY = 4             #steps between csv rows
SMALL = 1e-6          #the checks' strain
DYNAMIC_BACKGROUNDS = True   #write each ring's flow at a run of times, so the viewer's backgrounds change in replays
FRAMES = 32           #background frames a period
FRAME_CELLS = 24      #grid points across each frame
RINGS = [   #(name, centre in ring radii, wave settings, colour)
  ('plus', -3, {'plus': SHOWN}, '#2a78d6'),
  ('cross', 0, {'cross': SHOWN}, '#eb6834'),
  ('circular', 3, {'plus': SHOWN, 'cross': SHOWN, 'phaseCross': -math.pi/2}, '#1baf7a'),
]


def strainMatrix(wave, t):
  hp, hx = wave.strain(t)
  return np.array([[hp, hx], [hx, -hp]])


def rateMatrix(wave, t):
  rp, rx = wave.rate(t)
  return np.array([[rp, rx], [rx, -rp]])


def ring(folder, name, centre, settings):
  """
  one ring: a csv of its particles' paths, a csv of its shape at SHAPES moments through the last period (each a closed
  loop round the ring, an empty row ending it), and a log; returns the two csvs' paths
  """
  middle = np.array([centre*RADIUS, 0.0])
  calc = SpecialFlowCalculator([], 2, wave=PlaneWave(frequency=FREQUENCY, centre=middle, **settings))
  log = Log('ring_' + name, True, False, folder)
  calc.log = log
  log.logBodies(calc)
  log.print('%d free particles (w = 0) on a ring of %g m round (%g, %g) m, %d periods, %d steps a period'
            % (PARTICLES, RADIUS, middle[0], middle[1], PERIODS, STEPS))
  dt = 1/FREQUENCY/STEPS
  path = log.file.name[:-4] + '.csv'
  widest = 0.0
  every = PERIODS*STEPS - STEPS + np.arange(SHAPES)*STEPS//SHAPES   #the steps at which the shape is taken
  shapes = {step: [] for step in every}
  with open(path, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'pos_x', 'pos_y', 'v_x', 'v_y', 'u_x', 'u_y'])
    for n in range(PARTICLES):
      a = 2*math.pi*n/PARTICLES
      p = Particle()
      round_ = RADIUS*np.array([math.cos(a), math.sin(a)])
      p.pos = middle + round_ + strainMatrix(calc.wave, 0.0) @ round_/2   #round in TT coordinates
      calc.initPW(p, np.array([0.0, 0.0]))
      for step in range(PERIODS*STEPS + 1):
        if step % EVERY == 0:
          out.writerow([p.t, p.pos[0], p.pos[1], p.v[0], p.v[1], p.u[0], p.u[1]])
        widest = max(widest, abs(np.linalg.norm(p.pos - middle)/RADIUS - 1))
        if step in shapes:
          shapes[step].append((p.t, p.pos.copy()))
        if step < PERIODS*STEPS:
          calc.move(p, dt)
      out.writerow([''] * 7)   #an empty row ends the path
  shapePath = os.path.join(folder, os.path.basename(path).replace('ring_', 'shapes_', 1))
  with open(shapePath, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'pos_x', 'pos_y'])
    for step in every:
      for t, pos in shapes[step] + shapes[step][:1]:
        out.writerow([t, pos[0], pos[1]])
      out.writerow([''] * 3)
  if DYNAMIC_BACKGROUNDS:
    framesPath = os.path.join(folder, os.path.basename(path).replace('ring_', 'background_', 1))
    span = 1.6*RADIUS
    writeFrames(framesPath, calc, (middle[0] - span, middle[0] + span, middle[1] - span, middle[1] + span),
                np.arange(PERIODS*FRAMES + 1)/FRAMES/FREQUENCY, FRAME_CELLS)
    log.print(LOG_LINE, os.path.basename(framesPath))
  log.print('the ring stretched and squeezed by up to %.4g of its radius (h/2 = %g)' % (widest, SHOWN/2))
  log.print('its shape at %d moments in the last period: %s' % (SHAPES, os.path.basename(shapePath)))
  log.close()
  shutil.copy(path[:-4] + '.log', shapePath[:-4] + '.log')   #the same log, for the viewer
  return path, shapePath


def particleChecks(lines):
  """free and at-rest particles at h = SMALL against GR; the worst error as a fraction of h X0"""
  wave = PlaneWave(plus=SMALL, cross=0.5*SMALL, frequency=FREQUENCY, phasePlus=0.3, phaseCross=1.1)
  calc = SpecialFlowCalculator([], 2, wave=wave)
  dt = 1/FREQUENCY/2000
  lines.append('particles: h+ %g, hx %g, %g Hz, %d steps a period, 5 periods; error / (h |X0|), worst over the run'
               % (SMALL, 0.5*SMALL, FREQUENCY, 2000))
  results = {}
  for kind in ('free', 'at rest'):
    worst = 0.0
    for X0 in (np.array([1e6, 4e5]), np.array([-3e5, 7e5]), np.array([2e4, -9e5])):
      p = Particle()
      p.pos = X0.copy()
      if kind == 'free':
        calc.initPW(p, np.array([0.0, 0.0]))
        tt = X0 - strainMatrix(wave, 0.0) @ X0/2   #its TT coordinates, which it keeps
      else:
        calc.initPV(p, np.array([0.0, 0.0]))
      for _ in range(5*2000):
        calc.move(p, dt)
        if kind == 'free':
          want = tt + strainMatrix(wave, p.t) @ tt/2
        else:
          want = X0 + (strainMatrix(wave, p.t) - strainMatrix(wave, 0.0) - rateMatrix(wave, 0.0)*p.t) @ X0/2
        worst = max(worst, np.linalg.norm(p.pos - want)/(SMALL*np.linalg.norm(X0)))
    results[kind] = worst
    lines.append('  %-8s %.2e' % (kind, worst))
  return results


def roundTrip(calc, L, e, t0, steps=4000):
  """light from the wave's centre along e to a free mirror at L and back: the time it takes"""
  light, mirror = Particle(), Particle()
  light.t = mirror.t = t0
  light.pos = calc.wave.centre.copy()
  mirror.pos = calc.wave.centre + L*e
  calc.initPW(light, C*e)
  calc.initPW(mirror, np.array([0.0, 0.0]))
  dt = 2*L/C/steps
  out = True
  gap = lambda l, m: np.dot((m.pos - l.pos) if out else (l.pos - calc.wave.centre), e)
  while True:
    before = copy.deepcopy(light), copy.deepcopy(mirror)
    calc.move(light, dt)
    calc.move(mirror, dt)
    g = gap(light, mirror)
    if g > 0:
      continue
    #it got there during this step: find when (regula falsi on the step's length), and stop it there
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
    #the mirror is at rest in the space it is in (w = 0), so in that frame the light's w reverses along the arm
    light.w = light.w - 2*np.dot(light.w, e)*e
    light.v = light.w + light.u
    out = False


def lightChecks(lines):
  """light round trips at h = SMALL against GR; the error as a fraction of h L/c"""
  lines.append('')
  lines.append('light round trips: h = %g, %g Hz (wavelength %g km), sent at t = 0.002 s; extra time over 2L/c, and the'
               ' error / (h L/c)' % (SMALL, FREQUENCY, C/FREQUENCY/1000))
  lines.append('  %-8s %10s %8s %16s %16s %10s' % ('wave', 'L/lambda', 'arm', 'flow model (s)', 'GR (s)', 'error'))
  worst = 0.0
  t0 = 0.002
  for polarization in ('plus', 'cross'):
    wave = PlaneWave(frequency=FREQUENCY, phasePlus=0.4, phaseCross=0.4, **{polarization: SMALL})
    calc = SpecialFlowCalculator([], 2, wave=wave)
    for fraction in (0.01, 0.25, 0.5, 1.3):
      L = fraction*C/FREQUENCY
      for name, arm in (('x', (1, 0)), ('y', (0, 1)), ('diagonal', (1, 1))):
        e = np.array(arm, dtype=float)/np.linalg.norm(arm)
        along = lambda hp, hx: hp*(e[0]**2 - e[1]**2) + 2*hx*e[0]*e[1]   #h_ee
        T = roundTrip(calc, L, e, t0)
        want = 2*L*(1 - along(*wave.strain(t0))/2)/C + along(*wave.integral(t0, t0 + T))/2
        error = (T - want)/(SMALL*L/C)
        worst = max(worst, abs(error))
        lines.append('  %-8s %10g %8s %16.6e %16.6e %10.1e' % (polarization, fraction, name, T - 2*L/C, want - 2*L/C, error))
  return worst


def main():
  folder = os.path.join(LOG_DIR, 'gravWave', 'gravWave_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  made = []
  for name, centre, settings, colour in RINGS:
    tracks, shapes = ring(folder, name, centre, settings)
    made += [(shapes, colour, 'solid'), (tracks, colour, 'dotted')]
  writeViewerFiles(folder, 'gravWave', made, preferences={'showFlow': DYNAMIC_BACKGROUNDS})
  lines = ['gravitational wave checks: the flow model against GR, to first order in h', '']
  particles = particleChecks(lines)
  light = lightChecks(lines)
  lines += ['', 'worst: free %.1e, at rest %.1e of h X0; light %.1e of h L/c' % (particles['free'], particles['at rest'], light)]
  with open(os.path.join(folder, 'checks.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines))
  return folder


if __name__ == '__main__':
  if '--static' in sys.argv[1:]:
    DYNAMIC_BACKGROUNDS = False
  main()
