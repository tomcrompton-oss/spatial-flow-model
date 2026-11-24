"""
a gravitational wave travelling within the plane, held exactly: the flow model's clocks (N = 1) and its flow, with
space curved (engine/metric.py WaveSpacetime). the first step of the gravitational-wave work (Model to-do, Gravitational
waves 1)

the archive's wave across the plane (studies/grav_wave_across.py) was the model's nearest version: its flat space
can't hold the term (1/2c) h' M dN in

  ds^2 = -c^2 dt^2 + dN^2 + (dM - (1/2) h' M dt + (1/2c) h' M dN)^2

so light at an angle to the wave was off by up to 0.46 of h L/c, and fast particles by a few h y0 (more with the old
step). the model now has a curved space, and that term is space's metric: gamma = delta + a (n m + m n) + a^2 n n,
a = h' (m.X)/2c, with the same flow u = (1/2) h' (m.X) m. the checks are grav_wave_across's, at h = 1e-6, by four movers:

  flat flow     the old model: PlaneWave's flow in flat space (SpecialFlowCalculator)
  flow + space  the model with curved space: WaveSpacetime 'flow' (MetricCalculator, Hamilton's equations)
  TT            the same spacetime in GR's TT coordinates, no flow at all: WaveSpacetime 'tt' - the cross-check
  (control)     all of it again for a wave along z, through the plane, where the flat flow is already exact

  light   radar from the centre to a free mirror at L (0.01-1 wavelengths), at 0-90 degrees to the wave, and back,
          against GR's time: error / (h L/c)
  fast    particles moving along the wave at 0-0.99c, y0 = 0.05 wavelengths off its line, for two periods; GR keeps
          them at their TT y: error / (h y0)

writes logs/gravWaveCurved/gravWaveCurved_<datetime>/checks.log

run: python3 studies/grav_wave_curved.py        (a few minutes)
"""
import copy
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import SpecialFlowCalculator, Particle
from engine.metric import MetricCalculator, WaveSpacetime
from engine.waves import PlaneWave
from engine.logger import LOG_DIR
from engine.constants import *
from grav_wave_across import radar, grRadar, mirrorAt, SMALL, ANGLES, DISTANCES, SPEEDS, FREQUENCY, WAVELENGTH


def movers(wave):
  return [('flat flow', SpecialFlowCalculator([], 2, wave=wave), 'flow'),
          ('flow + space', MetricCalculator(WaveSpacetime(wave, 'flow')), 'flow'),
          ('TT', MetricCalculator(WaveSpacetime(wave, 'tt')), 'tt')]


def metricRadar(calc, wave, mirrorPos, e, t0, steps=4000):
  """
  radar() for a MetricCalculator, whose particles move by their momentum q: at the mirror (at rest in its space,
  w = 0) the light's momentum along the arm is reversed, measured by space's metric there: q -> q - 2 (q.e^) gamma e^,
  e^ = e/|e|_gamma
  """
  origin = wave.centre
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
    h = calc.spacetime.space(light.pos, light.t)
    g = np.eye(2) if h is None else np.eye(2) + h
    eh = e/math.sqrt(e @ g @ e)
    light.q = light.q - 2*(light.q @ eh)*(g @ eh)
    calc.keep(light)
    out = False


def lightChecks(lines, wave):
  t0 = 0.002
  way = 'along z, through the plane' if wave.along is None else 'along x, in the plane'
  worst = {}
  for title, mover, form in movers(wave):
    lines.append('light, %s: radar to a free mirror and back, h = %g, %g Hz (wavelength %g km), the wave %s; error /'
                 ' (h L/c) by distance and angle from x' % (title, SMALL, FREQUENCY, WAVELENGTH/1000, way))
    lines.append('  %-10s' % 'L/lambda' + ''.join('%11s' % ('%d deg' % a) for a in ANGLES))
    worst[title] = 0.0
    for fraction in DISTANCES:
      L = fraction*WAVELENGTH
      row = []
      for angle in ANGLES:
        e = np.array([math.cos(math.radians(angle)), math.sin(math.radians(angle))])
        at = mirrorAt(wave, L, e, t0) if form == 'flow' else wave.centre + L*e
        if isinstance(mover, MetricCalculator):
          T = metricRadar(mover, wave, at, e, t0)
        else:
          T = radar(mover, at, e, t0)
        error = (T - grRadar(wave, e, L, t0))/(SMALL*L/C)
        row.append(error)
        worst[title] = max(worst[title], abs(error))
      lines.append('  %-10g' % fraction + ''.join('%11.2e' % v for v in row))
    lines.append('')
  return worst


def fastChecks(lines, wave):
  """particles moving along the wave (in the plane) at v, y0 off its line: GR keeps their TT y"""
  y0 = 0.05*WAVELENGTH
  lines.append('fast particles: moving along x at v, %g km off the x axis, two periods; GR keeps them at their TT y;'
               ' error / (h y0)' % (y0/1000))
  ms = movers(wave)
  lines.append('  %-8s' % 'v/c' + ''.join('%15s' % title for title, *_ in ms))
  worst = {title: 0.0 for title, *_ in ms}
  for speed in SPEEDS:
    row = []
    for title, mover, form in ms:
      start = np.array([0.0, y0])
      p = Particle()
      tau = wave.when(start + wave.centre, 0.0)
      if form == 'flow':
        p.pos = wave.centre + np.array([0.0, y0*(1 + wave.strain(tau)[0]/2)])
        mover.initPV(p, np.array([speed*C, y0*wave.rate(tau)[0]*(1 - speed)/2]))
      else:
        p.pos = wave.centre + start
        mover.initPV(p, np.array([speed*C, 0.0]))
      w = 0.0
      dt = 1/FREQUENCY/2000
      for _ in range(4000):
        mover.move(p, dt)
        tau = wave.when(np.array([speed*C*p.t, 0.0]) + wave.centre, p.t)
        want = y0*(1 + wave.strain(tau)[0]/2) if form == 'flow' else y0
        w = max(w, abs(p.pos[1] - want)/(SMALL*y0))
      row.append(w)
      worst[title] = max(worst[title], w)
    lines.append('  %-8g' % speed + ''.join('%15.2e' % v for v in row))
  lines.append('')
  return worst


def main():
  folder = os.path.join(LOG_DIR, 'gravWaveCurved', 'gravWaveCurved_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder)
  lines = ['a gravitational wave travelling in the plane, with N = 1 and curved space (WaveSpacetime), against GR to'
           ' first order in h; the old flat-space flow alongside, and a wave along z as the control', '']
  across = PlaneWave(plus=SMALL, frequency=FREQUENCY, phasePlus=0.4, start=-1.0, along=(1, 0))   #everywhere already
  through = PlaneWave(plus=SMALL, frequency=FREQUENCY, phasePlus=0.4, start=-1.0)
  light = lightChecks(lines, across)
  print('\n'.join(lines), flush=True)
  shown = len(lines)
  fast = fastChecks(lines, across)
  lines += ['control: the wave along z', '']
  control = lightChecks(lines, through)
  lines.append('worst light error / (h L/c), in the plane: %s' % ', '.join('%s %.1e' % kv for kv in light.items()))
  lines.append('worst light error / (h L/c), control:      %s' % ', '.join('%s %.1e' % kv for kv in control.items()))
  lines.append('worst fast-particle error / (h y0):        %s' % ', '.join('%s %.1e' % kv for kv in fast.items()))
  with open(os.path.join(folder, 'checks.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('\n'.join(lines[shown:]))
  print('written to', folder)
  return folder


if __name__ == '__main__':
  main()
