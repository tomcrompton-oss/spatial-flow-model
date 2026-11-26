"""
the Moon's own orbit and de Sitter precession for the moving-body flow in engine/metric.py: the Sun and the Earth going
round each other (studies/turning_eikonal.py), the Moon a test particle round the Earth, run in the spacetime for 90
days, against GR. the method is studies/de_sitter.py's: the Moon's track (from the Earth, every 6 hours) is taken to
GR's harmonic coordinates, and GR's Moon (EIH, with the same Sun and Earth) fitted to it, its start free and its
track turned by -k times GR's de Sitter rate (1.5 V g/c^2, 19.2 mas a year):

  k = 0    the model has GR's de Sitter precession
  k = 1    it has none

and the rms left by the fit is what of the Moon's orbit no start and k can take up (the test's floor is the GR row's).
also fitted with GM_Earth free (lunar laser ranging fits it). the model's track is run at 60 and 30 s steps and taken
to zero step (Richardson: the step error goes as dt^2, or dt^4 with order=4)

the models (MODELS):
  GR                               GR's first post-Newtonian metric of the same bodies (engine/metric.py
                                   PostNewtonian), through the same engine: the pipeline's check (k = 0, rms the floor)
  turning, flat                    the turning flow, N = 1, flat space (the flow model)
  turning, N = 1, space from u     the same, space stretched across the flow by its own |u|^2/c^2
  turning J = 0, ...               the turning flow with Jacobi constant 0: one potential over the whole plane
  GR in the turning time, ...      GR's 1PN metric in the turning flow's time, J = 0 (engine/carried.py
                                   FreeFallTurning; 'carried J' for the carried one), as 'GR in free-fall time'
                                   (chi, no lapse, no moving, ...) is in the carried flow's
  ..., Einstein's space            space from Einstein's constraint, (2 Phi delta - u u)/c^2: stretched by the
                                   flow's head, d phi/dT + |u|^2/2 = Phi
  carried                          engine/carried.py: each body's river carried at its velocity, with the other's tide
  GR in free-fall time             engine/carried.py FreeFallPN: GR's metric with the carried flow's time (a check of
                                   the mapping: it is GR, to the carried flow's miss of Newton's equation - 4% of
                                   the Sun's tide at the Moon, which differencing doesn't remove from its 1PN terms),
                                   with its small lapse or that left at 1
  GR in the carried time           engine/metric.py SlicedPN: GR's metric transformed exactly to t = T + phi/c^2,
                                   phi the Earth's river at its velocity (a 30 km/s flow, nothing assumed): the
                                   engine and mapping's check with a flow the models' size (k +0.017, 0.027 m)

to GR's harmonic coordinates: the flow's time is the time of things falling from rest far away, T = t + S(x)/c^2,
S = sum 2 sqrt(2 GM r) over the bodies (each one's own river), so GR's time at the Moon is T less the Moon's S less
the Earth's (the constant keeps the Earth's phase). flat space's r is areal, so also x less GM/c^2 along each body's
direction (r_harmonic = r - GM/c^2); space from u needs no change of x: dr^2 + (1 + 2 Phi/c^2) r^2 dphi^2 is GR's
harmonic space at first order with r unchanged. GR's Earth goes round where it falls freely (radius)

run: python3 studies/lapse_moon.py [days]     (default 90; prints, and writes
     logs/modelChecks/lapseMoon_<days>d_<datetime>/summary.log and tracks.npz; while it runs, progress.log there
     has a line as each run passes each tenth of its days, with the time left, and as each run ends: tail -f it)
     python3 studies/lapse_moon.py [days] differenced     (the relativistic part alone: each model at c less at
                                                          c x 1000, added to Newton's - its Newtonian errors out)
     python3 studies/lapse_moon.py refit <folder>/tracks.npz     (the fits again, from a run's tracks)
     python3 studies/lapse_moon.py residuals <folder>/tracks.npz     (GR's Moon with its de Sitter turn fitted to each
                                                                     model's, and what is left by day: for the viewer)
     python3 studies/lapse_moon.py 90 [differenced] 'models=GR|turning, flat'     (a chosen set of models)
     python3 studies/lapse_moon.py 90 [differenced] 'steps=30|15'     (other steps than 60 and 30 s)
     python3 studies/lapse_moon.py 90 [differenced] order=4     (Runge-Kutta's rule, not the midpoint rule: needed
                                                                for the J = 0 flows, whose step error is 100x GR's)
"""
import math
import os
import time
import sys
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, SpecialFlowCalculator
from engine.metric import MetricCalculator, FlowSpacetime, PostNewtonian, bodyVelocityAt
from engine.logger import LOG_DIR
from engine.constants import *
from turning_eikonal import bodies, OMEGA, MU
from multi_body_pn import NODES, WEIGHTS

MODELS = ['GR', 'turning, flat', 'turning, N = 1, space from u from its body', 'carried, flat',
          'carried, N = 1, space from u from its body']
DTS = (60.0, 30.0)
#the integrator's order (engine/metric.py MetricCalculator): 2, the midpoint rule, or 4, Runge-Kutta's. from the
#environment, so that the pool's workers (spawned, not forked: they don't see main's globals) have it too
ORDER = int(os.environ.get('LAPSE_MOON_ORDER', '2'))
SAMPLE = 6*3600.0
GRDT = 120.0
DMOON = 3.844e8
START = (np.array([0.0, -DMOON]), np.array([1080.0, 0.0]))   #from the Earth, its velocity added: eccentricity about 0.12
V = AU*OMEGA
EPS = V*V/(2*C*C)
DESITTER = 1.5*math.sqrt(G*MS/AU)*G*MS/AU**2/C**2   #rad/s


def spacetime(model):
  if model == 'GR':
    return PostNewtonian(bodies())
  if model == 'GR in the carried time':
    from engine.metric import SlicedPN
    return SlicedPN(bodies())
  if model.startswith('GR in the turning time'):
    from engine.carried import FreeFallTurning
    from engine.turning import carriedJacobi
    J = 0.0
    if 'carried J' in model:
      J = carriedJacobi(bodies(), SpecialFlowCalculator(bodies(), 2, combine='turning').omega)
    return FreeFallTurning(bodies(), lapse='no lapse' not in model, retarded='at T' not in model,
                           keep=[w for w in ('space', 'scale', 'moving', 'psi') if 'no ' + w not in model],
                           chi=1 if 'chi' in model else None, jacobi=J, fine=False if 'ray table' in model else None)
  if model.startswith('GR in free-fall time'):
    from engine.carried import FreeFallPN
    return FreeFallPN(bodies(), lapse='no lapse' not in model, retarded='at T' not in model,
                      tides='transported' if 'transported' in model else True,
                      keep=[w for w in ('space', 'scale', 'moving', 'psi') if 'no ' + w not in model],
                      chi=1 if 'chi' in model else None)
  if model.startswith('carried'):
    from engine.carried import CarriedSpacetime
    return CarriedSpacetime(bodies(), transverse='gr' if "GR's space" in model else 'from its body' in model and 'source',
                            tides='transported' if 'transported' in model else True)
  flow = SpecialFlowCalculator(bodies(), 2, combine='turning')
  if 'J = 0' in model:
    flow.jacobi = 0.0   #one potential over the whole plane (the Sun's paths reach everywhere)
  if "Einstein's space" in model:
    return FlowSpacetime(flow, transverse='constraint')
  if 'from its body' in model:
    return FlowSpacetime(flow, transverse='source')
  if 'space from u' in model:
    return FlowSpacetime(flow, transverse='flow', slower='unslowed' not in model)
  return FlowSpacetime(flow)


def samples(days):
  return np.arange(DAY, (days - 1)*DAY + 1, SAMPLE)


def setC(scale):
  """c times scale, everywhere it is used (in this process: a pool's workers set it for each job). from c itself,
  not the module's current value, so it doesn't compound from one job to the next"""
  c = 299792458.0
  for name in list(sys.modules):
    m = sys.modules[name]
    if (name.startswith('engine.') or name in ('__main__', 'lapse_moon', 'studies.lapse_moon')) and hasattr(m, 'C'):
      m.C = c*scale
  globals()['C'] = c*scale


def run(job):
  """the Moon in the model at c times scale: its place at the samples, in the lab (and the Earth's, the Sun's, and
  the flow's integral from the Earth to it)"""
  model, dt, days, scale = job
  setC(scale)
  calc = MetricCalculator(spacetime(model), order=ORDER)
  B = calc.spacetime.bodies
  p = Particle()
  p.pos = B[1].at(0.0) + START[0]
  calc.initPV(p, bodyVelocityAt(B[1], 0.0) + START[1])
  ts = samples(days)
  out, i = [], 0
  started, tenth = time.time(), 1
  every = int(round(SAMPLE/dt))
  first = int(round(ts[0]/dt))
  n = 0
  while i < len(ts):
    calc.move(p, dt)
    n += 1
    if n >= first and (n - first) % every == 0:
      out.append((p.pos.copy(), B[0].at(p.t), B[1].at(p.t), flowIntegral(calc.spacetime, B[1].at(p.t), p.pos, p.t)))
      i += 1
      while tenth <= 10 and i >= tenth*len(ts)/10:   #each tenth of the samples (a short run's samples pass several)
        spent = time.time() - started
        progress('%-44s step %g s, c x %g: %3d%% (day %.0f of %g), %s so far, about %s left'
                 % (model, dt, scale, 10*tenth, p.t/DAY, days, clock(spent), clock(spent*(len(ts) - i)/i)))
        tenth += 1
  return job, out


PROGRESS = None   #the run's progress.log (main sets it; the pool's workers, forked, inherit it)


def progress(line):
  """a line with the time, printed and added to the run's progress.log (tail -f it to follow a run)"""
  line = '%s  %s' % (datetime.now().strftime('%H:%M:%S'), line)
  print(line, flush=True)
  if PROGRESS:
    with open(PROGRESS, 'a') as f:
      f.write(line + '\n')


def clock(seconds):
  return '%dh%02dm' % divmod(round(seconds/60), 60) if seconds >= 3600 else '%.0f min' % (seconds/60)


def flowIntegral(S, a, b, t, pieces=24):
  """the integral of the model's own flow (unslowed) from a to b along the line: GR's time there is T + this/c^2
  less the same at a (a flow with no curl is the gradient of S, T = t - S/c^2 ... with t harmonic)"""
  span = length(b - a)
  n = (b - a)/span
  from engine.carried import CarriedSpacetime, FreeFallPN, FreeFallTurning
  from engine.metric import SlicedPN
  if isinstance(S, SlicedPN):
    return S.potential(b, t)[0]   #less phi at a, the Earth, where it is 0
  if isinstance(S, FreeFallPN) and not isinstance(S, FreeFallTurning):
    S = S.carried
  if isinstance(S, FreeFallTurning):   #its own flow, the turning one (with J = 0 ~50 km/s at the Moon, not the carried)
    along = lambda y: S.baseFlow(y, t, S.region(y, t)) @ n
  elif isinstance(S, CarriedSpacetime):
    raw = CarriedSpacetime(S.bodies, tides=S.tides)   #its flow unslowed
    along = lambda y: raw.flow(y, t) @ n
  elif isinstance(S, FlowSpacetime):
    along = lambda y: S.calc.flow(y, S.calc.region(y, t), t) @ n
  else:
    return 0.0
  edges = np.concatenate([[0.0], np.geomspace(1e3, span, pieces)])
  total = 0.0
  for lo, hi in zip(edges[:-1], edges[1:]):
    for x, wt in zip(NODES, WEIGHTS):
      y = a + ((lo + hi)/2 + (hi - lo)/2*x)*n
      total += wt*(hi - lo)/2*along(y)
  return total


def harmonic(model, ts, rows):
  """the model's Moon from the Earth, in GR's harmonic coordinates: (GR's times, the Moon from GR's Earth)"""
  m = lambda gm: gm/C**2
  f = lambda gm, r: 2*math.sqrt(2*gm*r)/C**2
  times, rel = [], []
  for T, (x, sun, earth, I) in zip(ts, rows):
    rs, re = length(x - sun), length(x - earth)
    if model == 'GR':
      times.append(T)
      rel.append(x - earth)
      continue
    t = T + I/C**2
    X = x
    if 'flat' in model:
      X = X - m(G*MS)*(x - sun)/rs - m(G*ME)*(x - earth)/re
      E = earth - m(G*MS)*(earth - sun)/length(earth - sun)
    else:
      E = earth
    times.append(t)
    #GR's Earth at the Moon's GR time t, not at T: it has moved on by its velocity times T - t
    rel.append(X - E + places(T, radius(model))[1][1]*(T - t))
  return np.array(times), np.array(rel)


def length(v):
  return math.sqrt(v @ v)


def radius(model):
  """
  the Earth's distance from the Sun in GR's fit: where GR's Earth falls freely on a circle at the bodies' angular
  speed in the model's time T. GR's time at the Earth runs at dt/dT = 1 + kappa/c^2, kappa = d phi/dT along it: for the
  carried flow (and the turning flow with the carried J) kappa = -J = 1.5 GM_Sun/AU, and the Earth at Omega in T is
  GR's free fall at harmonic r = AU - GM_Sun/c^2 (Schwarzschild's Omega^2 = GM/R^3, R = r + GM/c^2) - held anywhere
  else, the Moon drifts from it (by 200 m in 90 days at AU). the GR row is the metric with the Earth held at AU, so
  its fit is too; and so are the times in which phi is steady at the Earth (kappa = 0): the river carried with it
  (GR in the carried time) and the turning flow with J = 0
  """
  steady = model in ('GR', 'GR in the carried time') or 'J = 0' in model or (
    model.startswith('GR in the turning time') and 'carried J' not in model)
  return AU if steady else AU - G*MS/C**2


def places(t, D, omega=OMEGA):
  """the Sun and the Earth on their circles (separation D, angular speed omega), and their velocities and
  accelerations"""
  a = omega*t
  e = np.array([math.cos(a), math.sin(a)])
  w = np.array([-math.sin(a), math.cos(a)])
  return (-MU*D*e, (1 - MU)*D*e), (-MU*D*omega*w, (1 - MU)*D*omega*w), (MU*D*omega**2*e, -(1 - MU)*D*omega**2*e)


def eihParticle(x, v, xs, vs, accs, gms):
  """EIH's acceleration of a test particle (studies/cross_terms.py eih with its mass 0)"""
  c2 = C*C
  acc = np.zeros(2)
  for b in range(len(gms)):
    d = xs[b] - x
    r = length(d)
    nBA = d/r
    vb, ab = vs[b], accs[b]
    F = sum(gms[c]/length(x - xs[c]) for c in range(len(gms)) if c != b)
    S = sum(gms[c]/length(xs[b] - xs[c]) for c in range(len(gms)) if c != b)
    bracket = (1 - 4*gms[b]/(r*c2) - 4*F/c2 - S/c2 + v @ v/c2 + 2*(vb @ vb)/c2 - 4*(v @ vb)/c2 - 1.5*(vb @ -nBA)**2/c2
               + 0.5*(-d @ ab)/c2)
    acc += gms[b]*nBA/r**2*bracket + gms[b]/(c2*r*r)*(-nBA @ (4*v - 3*vb))*(v - vb) + 3.5*gms[b]*ab/(c2*r)
  return acc


def grTrack(params, ts, D, earthScale=1.0, omega=OMEGA):
  """GR's Moon from the Earth (EIH, RK4 at GRDT, worked from the Earth so nothing rounds at 1 AU), at times ts,
  turned by -k de Sitter: params = start place (2), velocity (2), k, and the coordinates' stretch along the Earth's
  velocity and across it (a, b: x (1 + a) along, (1 + b) across - GR's Lorentz contraction is a = -V^2/2c^2)"""
  gms = [G*MS, G*ME*earthScale]
  y = np.concatenate([params[:2], params[2:4]])   #the Moon from the Earth: place, velocity
  def rate(t, y):
    xs, vs, accs = places(t, D, omega)
    E, VE, AE = xs[1], vs[1], accs[1]
    x, v = E + y[:2], VE + y[2:]
    return np.concatenate([y[2:], eihParticle(x, v, xs, vs, accs, gms) - AE])
  out, t, i = [], 0.0, 0
  while i < len(ts):
    h = min(GRDT, ts[i] - t)
    if h <= 0:
      a = -params[4]*DESITTER*t
      R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
      w = places(t, D, omega)[1][1]
      w = w/length(w)
      across = np.array([-w[1], w[0]])
      out.append((np.eye(2) + params[5]*np.outer(w, w) + params[6]*np.outer(across, across)) @ R @ y[:2])
      i += 1
      continue
    k1 = rate(t, y)
    k2 = rate(t + h/2, y + k1*h/2)
    k3 = rate(t + h/2, y + k2*h/2)
    k4 = rate(t + h, y + k3*h)
    y = y + (k1 + 2*k2 + 2*k3 + k4)*h/6
    t += h
  return np.array(out)


def newtonTrack(job):
  """GR's Moon (EIH) at c x 1000, from the start, the Earth at AU: Newton's, with the same integrator as the fits"""
  ts = job
  setC(1e3)
  return grTrack(np.concatenate([START[0], START[1], np.zeros(3)]), ts, AU)


def column(job):
  setC(1.0)
  params, k, step, ts, D, earth = job
  q = params.copy()
  q[k] += step
  return grTrack(q[:7], ts, D, 1 + (q[7] if earth else 0.0))


def fit(pool, ts, target, D, earth):
  """GR's start, k, the stretch a, b (and GM_Earth's change) fitted to the target track: k, a, b, the change, the
  rms left (m)"""
  n = 8 if earth else 7
  steps = np.array([1.0, 1.0, 1e-6, 1e-6, 0.01, 1e-9, 1e-9, 1e-9][:n])
  p = np.concatenate([START[0], START[1], np.zeros(n - 4)])
  setC(1.0)
  base = lambda p: grTrack(p[:7], ts, D, 1 + (p[7] if earth else 0.0))
  r = (base(p) - target).ravel()
  for _ in range(8):   #Gauss-Newton, the Jacobian again each time, until the rms settles
    cols = pool.map(column, [(p, k, steps[k], ts, D, earth) for k in range(n)])
    J = np.array([((c - target).ravel() - r)/steps[k] for k, c in enumerate(cols)]).T
    before = math.sqrt(np.mean(r*r))
    p = p - np.linalg.lstsq(J, r, rcond=None)[0]
    r = (base(p) - target).ravel()
    if abs(before - math.sqrt(np.mean(r*r))) < 1e-4*before:
      break
  return p[4], p[5], p[6], (p[7] if earth else 0.0), math.sqrt(np.mean(r*r))


def refit(path):
  """the fits again, from a run's tracks.npz (the targets in GR's coordinates)"""
  data = np.load(path)
  ts = data['ts']
  with Pool(8) as pool:
    for m in [k for k in data.files if k != 'ts' and not k.endswith(' step')]:
      k, a, b, gm, rms = fit(pool, ts, data[m], radius(m), False)
      print('  %-44s k %+.4f   stretch along %+.2f, across %+.2f V^2/2c^2   rms %.4f m' % (m, k, a/EPS, b/EPS, rms), flush=True)


def fitFixedK(pool, ts, target, D):
  """GR's Moon, with GR's own de Sitter turn (k held at 0), fitted to the target track - its start and the stretch
  free: the fitted track"""
  free = [0, 1, 2, 3, 5, 6]
  steps = np.array([1.0, 1.0, 1e-6, 1e-6, 0.01, 1e-9, 1e-9])
  p = np.concatenate([START[0], START[1], np.zeros(3)])
  setC(1.0)
  base = lambda p: grTrack(p, ts, D)
  r = (base(p) - target).ravel()
  for _ in range(8):
    cols = pool.map(column, [(p, k, steps[k], ts, D, False) for k in free])
    J = np.array([((c - target).ravel() - r)/steps[k] for k, c in zip(free, cols)]).T
    before = math.sqrt(np.mean(r*r))
    p[free] = p[free] - np.linalg.lstsq(J, r, rcond=None)[0]
    r = (base(p) - target).ravel()
    if abs(before - math.sqrt(np.mean(r*r))) < 1e-4*before:
      break
  return base(p)


RESIDUAL_MODELS = (('turning, flat', 'the turning flow', '#eb6834', 'solid'),
                   ('turning, N = 1, space from u from its body', 'the turning flow, space curved', '#d6a21e', 'dashed'),
                   ('GR in the turning time, chi, no lapse', 'one potential', '#2a78d6', 'solid'),
                   ('GR', 'general relativity (the check)', '#7a7a74', 'dotted'))


def residuals(path):
    """from a differenced run's tracks.npz: for each model, GR's Moon with GR's de Sitter turn fitted to the model's
    (start and stretch free, k held at 0), and how far apart they are at each sample - the part of the model's Moon
    no start can take up. a csv per model (day against metres), a viewer file and summary.log, in a new folder
    logs/modelChecks/lapseMoonResiduals_<datetime>/"""
    import json
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from two_body_escapes import writeViewerFiles
    data = np.load(path)
    ts = data['ts']
    folder = os.path.join(LOG_DIR, 'modelChecks', 'lapseMoonResiduals_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(folder, exist_ok=True)
    made, lines = [], ['the Moon over %g days, from %s: GR\'s Moon with its own de Sitter turn (k = 0) fitted to each'
                       ' model\'s, its start and the stretch free; how far apart they are' % (ts[-1]/86400, path)]
    with Pool(8) as pool:
      for model, title, colour, style in RESIDUAL_MODELS:
        if model not in data.files:
          continue
        fitted = fitFixedK(pool, ts, data[model], radius(model))
        gap = np.linalg.norm(fitted - data[model], axis=1)
        name = os.path.join(folder, title)
        with open(name + '.csv', 'w') as f:
          f.write('time (days),gap (m)\n')
          for t, g in zip(ts, gap):
            f.write('%.6g,%.6g\n' % (t/86400, g))
        with open(name + '.log', 'w') as f:
          f.write('the Moon in %s (%s), against GR\'s Moon with its de Sitter turn fitted to it: how far apart, by day\n'
                  % (title, model))
        made.append((name + '.csv', colour, style))
        lines.append('  %-32s rms %.4f m, largest %.4f m' % (title, math.sqrt(np.mean(gap*gap)), gap.max()))
        print(lines[-1], flush=True)
    writeViewerFiles(folder, 'lapseMoon_residuals', made, selection=(('time (days)', 'gap (m)'),),
                     styles=lambda colour, style='solid': {'time (days) / gap (m)': [colour, style, colour]},
                     preferences={'equalAspect': False, 'showBodies': False, 'showSchwarzschild': False,
                                  'showPathLegend': True, 'showGrid': True, 'replaySpeed': '1'})
    with open(os.path.join(folder, 'summary.log'), 'w') as f:
      f.write('\n'.join(lines) + '\n')
    print('written to', folder)


def zeroStep(model, ts, runs, days, scale, mapped):
  """the model's Moon from the Earth taken to zero step, in GR's coordinates (mapped) and at GR's sample times; and
  the 60 s step's"""
  tracks, times = {}, None
  for dt in DTS:
    rows = runs[(model, dt, days, scale)]
    if mapped:
      times, tracks[dt] = harmonic(model, ts, rows)
    else:
      times, tracks[dt] = ts, np.array([x - earth for x, sun, earth, I in rows])
  k = 2**ORDER                                  #Richardson: the step error goes as dt^ORDER
  zero = (k*tracks[DTS[1]] - tracks[DTS[0]])/(k - 1)
  #GR's times at the Moon differ from T by under a millisecond: the track is moved to them along its velocity
  vel = np.gradient(zero, ts, axis=0)
  shift = vel*(ts - times)[:, None]
  return zero + shift, tracks[DTS[0]] + shift


def main():
  if len(sys.argv) > 2 and sys.argv[1] == 'refit':
    return refit(sys.argv[2])
  if len(sys.argv) > 2 and sys.argv[1] == 'residuals':
    return residuals(sys.argv[2])
  days = float(sys.argv[1]) if len(sys.argv) > 1 else 90.0
  differenced = 'differenced' in sys.argv[2:]
  global MODELS
  for a in sys.argv[2:]:
    if a.startswith('models='):
      MODELS = [m.strip() for m in a[len('models='):].split('|')]   #a chosen set of models, | between them
  global DTS, ORDER
  for a in sys.argv[2:]:
    if a.startswith('order='):
      ORDER = int(a[len('order='):])
      os.environ['LAPSE_MOON_ORDER'] = str(ORDER)   #for the pool's workers
  for a in sys.argv[2:]:
    if a.startswith('steps='):
      DTS = tuple(float(x) for x in a[len('steps='):].split('|'))     #the two steps (s), the second half the first
  folder = os.path.join(LOG_DIR, 'modelChecks', 'lapseMoon_%gd%s_%s' % (days, '_differenced' if differenced else '',
                                                                       datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
  os.makedirs(folder, exist_ok=True)
  ts = samples(days)
  scales = (1.0, 1e3) if differenced else (1.0,)
  global PROGRESS
  PROGRESS = os.path.join(folder, 'progress.log')
  jobs = [(m, dt, days, s) for m in MODELS for dt in DTS for s in scales]
  progress('%d runs of %g days on 8 workers (%s); progress in %s' % (len(jobs), days, ', '.join(MODELS), PROGRESS))
  started = time.time()
  with Pool(8) as pool:
    newton = pool.apply_async(newtonTrack, [ts]) if differenced else None
    runs = {}
    for job, out in pool.imap_unordered(run, jobs):
      runs[job] = out
      progress('done %d of %d: %s, step %g s, c x %g (%s in all)' % (len(runs), len(jobs), job[0], job[1], job[3],
                                                                     clock(time.time() - started)))
    lines = ['moon: the Moon round the Earth for %g days, the Sun and the Earth going round each other; GR (EIH) fitted to'
             ' the model\'s track in harmonic coordinates, its start and k free, turned by -k de Sitter (19.2 mas a year):'
             ' k = 0 the model has GR\'s de Sitter precession, k = 1 none; the rms left' % days,
             '  steps %g and %g s, %s' % (DTS[0], DTS[1], 'Runge-Kutta (order 4), its force an eighth-order difference'
                                          if ORDER == 4 else 'the midpoint rule (order 2)')]
    if differenced:
      lines.append('  differenced: the model\'s track is its track at c less its track at c x 1000, added to Newton\'s (EIH at'
                   ' c x 1000): its relativistic part alone, its Newtonian errors taken out')
      newton = newton.get()
    saved = {}
    progress('all runs done; fitting GR to each model')
    for m in MODELS:
      target, step = zeroStep(m, ts, runs, days, 1.0, True)
      if differenced:
        nz, ns = zeroStep(m, ts, runs, days, 1e3, False)
        target, step = newton + target - nz, newton + step - ns
      saved[m], saved[m + ' step'] = target, step
      for name, track in (('step %g s' % DTS[0], step), ('to zero step', target)):
        k, a, b, gm, rms = fit(pool, ts, track, radius(m), False)
        lines.append('  %-44s %-14s k %+.4f   stretch along %+.2f, across %+.2f V^2/2c^2   rms %.4f m'
                     % (m, name, k, a/EPS, b/EPS, rms))
        print(lines[-1], flush=True)
  np.savez(os.path.join(folder, 'tracks.npz'), ts=ts, **{m: v for m, v in saved.items()})
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
