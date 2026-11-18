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

the model's track is extrapolated to zero step from DTS (Richardson, the step being second order) and taken to GR's
harmonic coordinates (harmonic: without it the two differ by metres), and k is found again with c a thousand times
larger (Newton's then; any k there is the steps' or the fit's). k is also fitted with GM_Earth free (a turning and
a change in the Moon's mean motion both move it along its orbit; only the perigee tells them apart). the calibration
fits GR to GR run turning at the de Sitter rate, which must give k = 1

run: DESITTER_ORBIT=near|reverse|far python3 studies/de_sitter.py [days [start [boost]]]      (default 90 eccentric freefall; start eccentric or lunar
     (studies/lunar_orbit.py's), boost freefall, carried or heavier (engine/split.py); prints, and writes
     logs/multiBody/deSitter_<days>d_<start>[_<boost>]_<datetime>/summary.log)
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

DTS = (5.0, 2.5)                  #the model's steps, the second half the first (worked from the Earth, and each step's
                                  #changes as changes: engine/split.py moveLorentz, studies/lunar_orbit.py Centred)
SCALES = (1.0, 1e3)               #c, times
GRDT = 60.0
STARTS = {'eccentric': (np.array([0.0, -lo.DMOON]), np.array([1080.0, 0.0])),   #eccentricity about 0.12
          'lunar': lo.START}
ORBIT = os.environ.get('DESITTER_ORBIT', 'near')   #the Earth's orbit: 'near' (1 AU, the Moon's sense), 'reverse' (the
                                                  #other way round) or 'far' (2 AU); set from the command line
RADIUS, SENSE = {'near': (AU, 1), 'reverse': (AU, -1), 'far': (2*AU, 1)}[ORBIT]
DESITTER = SENSE*lo.Setup(True, True, RADIUS, SENSE).deSitter()   #rad/s, at c: k's unit at either scale (signed:
                                                                 #the turning reverses with the orbit)


def setC(scale):
  split.C = flow.C = lo.C = C*scale


def samples(days):
  return np.arange(DAY, days*DAY - DAY, DAY/4)


def relative(track, setup, ts):
  return np.array([track.at(t) - setup.earth(t) for t in ts])


def model(job):
  """the model's Moon from the Earth at the samples, in the model's coordinates"""
  days, dt, scale, start, boost = job
  setC(scale)
  lo.SPAN = days*DAY - DAY
  setup = lo.Setup(True, False, RADIUS, SENSE, start=STARTS[start])
  _, track = lo.modelRun(setup, dt, boost, centred=True)
  return job, relative(track, setup, samples(days))


def harmonic(T, rel, start):
  """
  the model's Moon (rel from the model's Earth at its times T) in GR's harmonic coordinates, from GR's Earth: the
  model's lab is the Sun's flowing-space coordinates, areal r and the space's own time T (Gullstrand-Painleve), and
  harmonic ones are r - GM/c^2 and t = T - (f(r) - f(AU)), f(r) = 2 sqrt(2 m r)/c, m = GM/c^2, to first order (the
  constant f(AU) keeps the Earth's phase). left out, the two differ by metres (the Earth-Moon line by 1e-8 across,
  and a time shift of u/c^2 per metre from the Earth), more than the test is after
  """
  model, gr = lo.Setup(True, False, RADIUS, SENSE, start=STARTS[start]), lo.Setup(True, True, RADIUS, SENSE, start=STARTS[start])
  m = G*MS/lo.C**2
  X = np.array([model.earth(t) for t in T]) + rel
  r = np.linalg.norm(X, axis=1)
  f = lambda r: 2*np.sqrt(2*m*r)/lo.C
  t = T - (f(r) - f(model.orbit))
  return t, X*(1 - m/r)[:, None] - np.array([gr.earth(x) for x in t])


def fit(job):
  """GR's start and k (and with earth, GM_Earth) fitted to the model's Moon: k, GM_Earth's change, the rms left (m)"""
  days, scale, start, rel, mapped, earth = job
  setC(scale)
  ts = samples(days)
  ts, target = harmonic(ts, rel, start) if mapped else (ts, rel)
  lo.SPAN = ts[-1] + DAY
  n = 6 if earth else 5
  steps = np.array([1.0, 1.0, 1e-6, 1e-6, 0.01, 1e-9][:n])
  def resid(p):
    setup = lo.Setup(True, True, RADIUS, SENSE, turn=p[4]*DESITTER, earthScale=1 + (p[5] if earth else 0.0), start=STARTS[start])
    return (relative(lo.grRun(setup, (p[:2], p[2:4]), GRDT), setup, ts) - target).ravel()
  p = np.concatenate([STARTS[start][0], STARTS[start][1], np.zeros(n - 4)])
  for _ in range(5):
    r = resid(p)
    J = np.array([(resid(p + np.eye(n)[k]*steps[k]) - r)/steps[k] for k in range(n)]).T
    p = p - np.linalg.lstsq(J, r, rcond=None)[0]
  r = resid(p)
  return p[4], (p[5] if earth else 0.0), math.sqrt(np.mean(r*r))


def turned(job):
  """GR in a frame turning at the de Sitter rate"""
  days, start = job
  lo.SPAN = days*DAY - DAY
  setup = lo.Setup(True, True, RADIUS, SENSE, turn=DESITTER, start=STARTS[start])
  return relative(lo.grRun(setup, STARTS[start], GRDT), setup, samples(days))


def main():
  days = float(sys.argv[1]) if len(sys.argv) > 1 else 90.0
  start = sys.argv[2] if len(sys.argv) > 2 else 'eccentric'
  boost = sys.argv[3] if len(sys.argv) > 3 else 'freefall'
  folder = os.path.join(LOG_DIR, 'multiBody', 'deSitter_%gd_%s%s%s_%s' % (days, start, '' if boost == 'freefall' else
                        '_' + boost, '' if ORBIT == 'near' else '_' + ORBIT, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
  os.makedirs(folder, exist_ok=True)
  with Pool(8) as pool:
    calTarget = pool.apply_async(turned, [(days, start)])
    runs = {job[1:3]: rel for job, rel in pool.map(model, [(days, dt, s, start, boost) for dt in DTS for s in SCALES])}
    np.savez(os.path.join(folder, 'tracks.npz'), ts=samples(days),
             **{'c%g_dt%g' % (s, dt): rel for (dt, s), rel in runs.items()})
    zero = {s: (4*runs[(DTS[1], s)] - runs[(DTS[0], s)])/3 for s in SCALES}
    cal = calTarget.get()
    jobs = {('step %g s' % dt, 1.0, False): (days, 1.0, start, runs[(dt, 1.0)], True, False) for dt in DTS}
    jobs.update({
      ('extrapolated', 1.0, False): (days, 1.0, start, zero[1.0], True, False),
      ('extrapolated', 1.0, True): (days, 1.0, start, zero[1.0], True, True),
      ('extrapolated, not mapped', 1.0, False): (days, 1.0, start, zero[1.0], False, False),
      ('extrapolated', 1e3, False): (days, 1e3, start, zero[1e3], True, False),
      ('calibration', 1.0, False): (days, 1.0, start, cal, False, False),
      ('calibration', 1.0, True): (days, 1.0, start, cal, False, True)})
    found = dict(zip(jobs, pool.map(fit, list(jobs.values()))))
  lines = ['de Sitter (%s frames, the Earth\'s orbit %s): the Moon (start %s) round the Earth on its orbit for %g days; GR fitted to the model\'s track'
           ' (taken to harmonic coordinates), its start and k free, GR turning at k times the de Sitter rate (19.2 mas a'
           ' year): k = 0 the model has GR\'s de Sitter precession, k = 1 none' % (boost, ORBIT, start, days)]
  for (name, scale, earth), (k, gm, rms) in found.items():
    lines.append('  %-26s %-8s k %+.4f%s, fit rms %.3f m' % (name + ':', 'c x 1000' if scale > 1 else '', k,
                 ', GM_Earth %+.2e' % gm if earth else '', rms))
  lines.append('  (calibration: GR fitted to GR turning at the de Sitter rate, which must give k = 1)')
  print('\n'.join(lines))
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
