"""
the split model's terms in sqrt(M_Earth M_Sun): GR's equations of motion are a series in the masses (the cross terms
go as M_Earth M_Sun), but the model's flows go as sqrt(M), so a frame rule that mixes the two bodies' flows can give
terms in sqrt(M_Earth M_Sun), which GR doesn't have. a body's flow can as well run out as in (outgoing
Gullstrand-Painleve coordinates: the same Schwarzschild space outside the body, with t = T - 2 sqrt(2 m r)/c in place
of +): GR's predictions don't change, but a term odd in a body's flow changes sign

so the de Sitter test (studies/de_sitter.py: the Moon for 90 days, the model's track at zero step in harmonic
coordinates, GR fitted with its start and k free, and with GM_Earth free too) is run with the Earth's flow, the Sun's,
or both, running out. the k's should agree; half the difference of two is the part odd in that flow, and the mean of
all four the part even in both

run: python3 studies/flow_sign.py [boost [start [days]]]   (default heavier eccentric 90; prints, and writes
     logs/multiBody/flowSign_<boost>_<start>_<datetime>/summary.log and tracks.npz)
"""
import math
import os
import sys
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.logger import LOG_DIR
from engine.constants import *
import lunar_orbit as lo
import de_sitter as ds

CASES = {'both in': (), 'the Earth out': ('earth',), 'the Sun out': ('sun',), 'both out': ('earth', 'sun')}
CENTRED = lo.Centred.__init__


def model(job):
  """the model's Moon from the Earth at the samples, the flows in white running out"""
  days, dt, start, boost, white = job
  lo.SPAN = days*DAY - DAY
  setup = lo.Setup(True, False, start=ds.STARTS[start])
  def init(self, s):
    CENTRED(self, s)
    self.sun.black, self.earth.black = 'sun' not in white, 'earth' not in white
  lo.Centred.__init__ = init
  _, track = lo.modelRun(setup, dt, boost, centred=True)
  return job, ds.relative(track, setup, ds.samples(days))


def harmonic(T, rel, start, sunOut):
  """de_sitter.harmonic, the Sun's flow in or out (its time shift the other way)"""
  if not sunOut:
    return ds.harmonic(T, rel, start)
  model, gr = lo.Setup(True, False, start=ds.STARTS[start]), lo.Setup(True, True, start=ds.STARTS[start])
  m = G*MS/C**2
  Xs = np.array([model.earth(x) for x in T]) + rel
  r = np.linalg.norm(Xs, axis=1)
  f = lambda r: 2*np.sqrt(2*m*r)/C
  t = T + (f(r) - f(model.orbit))
  return t, Xs*(1 - m/r)[:, None] - np.array([gr.earth(x) for x in t])


def fitTarget(days, start, ts, target, earth):
  """de_sitter.fit's least squares, on a target already in harmonic coordinates at times ts"""
  lo.SPAN = ts[-1] + DAY
  n = 6 if earth else 5
  steps = np.array([1.0, 1.0, 1e-6, 1e-6, 0.01, 1e-9][:n])
  def resid(p):
    setup = lo.Setup(True, True, turn=p[4]*ds.DESITTER, earthScale=1 + (p[5] if earth else 0.0), start=ds.STARTS[start])
    return (ds.relative(lo.grRun(setup, (p[:2], p[2:4]), ds.GRDT), setup, ts) - target).ravel()
  p = np.concatenate([ds.STARTS[start][0], ds.STARTS[start][1], np.zeros(n - 4)])
  for _ in range(5):
    r = resid(p)
    J = np.array([(resid(p + np.eye(n)[k]*steps[k]) - r)/steps[k] for k in range(n)]).T
    p = p - np.linalg.lstsq(J, r, rcond=None)[0]
  r = resid(p)
  return p[4], (p[5] if earth else 0.0), math.sqrt(np.mean(r*r))


def main():
  boost = sys.argv[1] if len(sys.argv) > 1 else 'heavier'
  start = sys.argv[2] if len(sys.argv) > 2 else 'eccentric'
  days = float(sys.argv[3]) if len(sys.argv) > 3 else 90.0
  folder = os.path.join(LOG_DIR, 'multiBody', 'flowSign_%s_%s_%s' % (boost, start,
                        datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
  os.makedirs(folder, exist_ok=True)
  with Pool(8) as pool:
    jobs = [(days, dt, start, boost, white) for white in CASES.values() for dt in ds.DTS]
    runs = {(job[4], job[1]): rel for job, rel in pool.map(model, jobs)}
    np.savez(os.path.join(folder, 'tracks.npz'), ts=ds.samples(days),
             **{'%s_dt%g' % ('-'.join(w) or 'in', dt): rel for (w, dt), rel in runs.items()})
    fits = []
    for name, white in CASES.items():
      zero = (4*runs[(white, ds.DTS[1])] - runs[(white, ds.DTS[0])])/3
      ts, target = harmonic(ds.samples(days), zero, start, 'sun' in white)
      fits += [(name, earth, (days, start, ts, target, earth)) for earth in (False, True)]
    found = pool.starmap(fitTarget, [f[2] for f in fits])
  lines = ['flow sign (%s frames): the de Sitter test (the Moon, start %s, %g days; k = 0 GR\'s precession, 1 none)'
           ' with each body\'s flow running in or out - GR\'s predictions the same either way' % (boost, start, days)]
  ks = {}
  for (name, earth, _), (k, gm, rms) in zip(fits, found):
    ks[(name, earth)] = k
    lines.append('  %-14s k %+.4f%s, fit rms %.3f m' % (name + ':', k, ', GM_Earth %+.2e' % gm if earth else '', rms))
  for earth in (False, True):
    get = lambda n: ks[(n, earth)]
    tag = ' (GM_Earth free)' if earth else ''
    lines.append('  %s: odd in the Earth\'s flow %+.4f, odd in the Sun\'s %+.4f, odd in both %+.4f; even in both %+.4f'
                 % (tag or 'k', (get('both in') - get('the Earth out') + get('the Sun out') - get('both out'))/4,
                    (get('both in') + get('the Earth out') - get('the Sun out') - get('both out'))/4,
                    (get('both in') - get('the Earth out') - get('the Sun out') + get('both out'))/4,
                    (get('both in') + get('the Earth out') + get('the Sun out') + get('both out'))/4))
  print('\n'.join(lines))
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
