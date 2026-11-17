"""
de Sitter precession in the split model (engine/split.py, 'static' light, 'freefall' frames): the Moon round the Earth
on its orbit round the Sun, against GR (studies/lunar_orbit.py's EIH equations).

the effect is 19.2 mas a year in a perigee turning 1.1 rad a year (the Sun's tide), and the tide's rate hangs on the
Moon's orbit: a start 1 part in 10^8 different (the size of the model's and GR's coordinates' differences) turns it
by tens of mas a year, so the perigee's rate from a common start can't show it, nor can it with GR's start fitted
(the rate trades with the orbit's size and shape). so GR is fitted to the model's track (the Moon from the Earth,
least squares over the run) with its start and k free, GR run in a frame turning at k times the de Sitter rate:

  k = 0     the model has GR's de Sitter precession
  k = 1     it has none (GR seen from a frame turning with the de Sitter rate, in its place)

the model's track is extrapolated to zero step from DTS (Richardson, the step being second order), and k is found
again with c a thousand times larger (Newton's then; any k there is the steps' or the fit's) and taken off. the
calibration fits GR to GR run turning at the de Sitter rate, which must give k = 1

run: python3 studies/de_sitter.py [days [start]]      (default 90 eccentric; start eccentric or lunar
     (studies/lunar_orbit.py's); prints, and writes logs/multiBody/deSitter_<days>d_<start>_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
import engine.split as split
import engine.flow as flow
from engine.logger import LOG_DIR
from engine.constants import *
import lunar_orbit as lo

DTS = (20.0, 10.0)                #the model's steps, the second half the first (below 5 s rounding takes over: the
                                  #Moon's place from the Earth, 1.5e11 m from the Sun, to 3e-5 m at each step)
SCALES = (1.0, 1e3)               #c, times
GRDT = 60.0
STARTS = {'eccentric': (np.array([0.0, -lo.DMOON]), np.array([1080.0, 0.0])),   #eccentricity about 0.12
          'lunar': lo.START}
DESITTER = lo.Setup(True, True).deSitter()   #rad/s, at c: k's unit at either scale


def setC(scale):
  split.C = flow.C = lo.C = C*scale


def samples(days):
  return np.arange(DAY, days*DAY - DAY, DAY/4)


def relative(track, setup, ts):
  return np.array([track.at(t) - setup.earth(t) for t in ts])


def model(job):
  """the model's Moon from the Earth at the samples"""
  days, dt, scale, start = job
  setC(scale)
  lo.SPAN = days*DAY - DAY
  setup = lo.Setup(True, False, start=STARTS[start])
  _, track = lo.modelRun(setup, dt, 'freefall')
  return job, relative(track, setup, samples(days))


def fit(job):
  """GR's start and k fitted to target: k, and the rms left (m)"""
  days, scale, start, target = job
  setC(scale)
  lo.SPAN = days*DAY - DAY
  ts = samples(days)
  steps = np.array([1.0, 1.0, 1e-6, 1e-6, 0.01])
  def resid(p):
    setup = lo.Setup(True, True, turn=p[4]*DESITTER, start=STARTS[start])
    return (relative(lo.grRun(setup, (p[:2], p[2:4]), GRDT), setup, ts) - target).ravel()
  p = np.concatenate([STARTS[start][0], STARTS[start][1], [0.0]])
  for _ in range(4):
    r = resid(p)
    J = np.array([(resid(p + np.eye(5)[k]*steps[k]) - r)/steps[k] for k in range(5)]).T
    p = p - np.linalg.lstsq(J, r, rcond=None)[0]
  r = resid(p)
  return p[4], math.sqrt(np.mean(r*r))


def turned(job):
  """GR in a frame turning at the de Sitter rate"""
  days, start = job
  lo.SPAN = days*DAY - DAY
  setup = lo.Setup(True, True, turn=DESITTER, start=STARTS[start])
  return relative(lo.grRun(setup, STARTS[start], GRDT), setup, samples(days))


def main():
  days = float(sys.argv[1]) if len(sys.argv) > 1 else 90.0
  start = sys.argv[2] if len(sys.argv) > 2 else 'eccentric'
  folder = os.path.join(LOG_DIR, 'multiBody', 'deSitter_%gd_%s_%s' % (days, start, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
  os.makedirs(folder, exist_ok=True)
  with Pool(8) as pool:
    calTarget = pool.apply_async(turned, [(days, start)])
    runs = {job[1:3]: rel for job, rel in pool.map(model, [(days, dt, s, start) for dt in DTS for s in SCALES])}
    jobs, names = [], []
    for s in SCALES:
      for dt in DTS:
        jobs.append((days, s, start, runs[(dt, s)]))
        names.append((s, dt))
      jobs.append((days, s, start, (4*runs[(DTS[1], s)] - runs[(DTS[0], s)])/3))
      names.append((s, 0.0))
    jobs.append((days, 1.0, start, calTarget.get()))
    names.append('calibration')
    found = dict(zip(names, pool.map(fit, jobs)))
  lines = ['de Sitter: the Moon (start %s) round the Earth on its orbit for %g days; GR fitted to the model\'s track,'
           ' its start and k free, GR turning at k times the de Sitter rate (19.2 mas a year): k = 0 the model has GR\'s'
           ' de Sitter precession, k = 1 none' % (start, days)]
  for dt in DTS + (0.0,):
    (a, ra), (b, rb) = found[(1.0, dt)], found[(1e3, dt)]
    lines.append('  %-12s k %+.4f (fit rms %.3f m); with c x 1000 %+.4f (%.3f m); the difference %+.4f'
                 % ('step %g s:' % dt if dt else 'extrapolated:', a, ra, b, rb, a - b))
  k, rms = found['calibration']
  lines.append('  calibration: GR fitted to GR turning at the de Sitter rate: k %+.4f (fit rms %.3f m), as it must be 1'
               % (k, rms))
  print('\n'.join(lines))
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
