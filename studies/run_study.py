"""
run one simulation from a json config - used by the viewer's Sim tab, and runnable on its own

config (SI units):
  name          the log name; files are logs/<study>/<name>_<datetime>.log / .csv (and .json, the config), <study> being the name up to its first _
  type          'orbit' or 'hyperbolic'
  calculator    a name in flow.CALCULATORS, e.g. 'SpecialFlowCalculator, second order' (older names work too)
  bodies        [{"mass": kg, "x": m, "y": m, "black": true}, ...]
  position      [x, y] m      the particle's start
  velocity      [vx, vy] m/s  its starting velocity
  dt            seconds per step; with stepFraction, the longest step
  stepFraction  optional: adaptive steps, each moving at most this fraction of the distance to the nearest body
                (flow.Calculator.stepSize); without it every step is dt
  every         seconds between csv rows (with fixed steps, rounded to whole steps)
  logDir        optional: a folder for the files instead of logs/<folder>/ (the regression tests use it)
  end           {"kind": "time", "value": s}          elapsed time
                {"kind": "min", "value": m}           closer than this to any body
                {"kind": "max", "value": m}           farther than this from every body
                {"kind": "orbits", "value": n}        n measured orbits (orbit runs; the first crossing is a warmup)

while running it prints 'progress <fraction>' lines, and at the end 'file <csv path>'; with --status <path> it also
keeps a small json status file up to date (pid, state, progress, file), which is how the viewer follows a run -
the run doesn't depend on the viewer, so it carries on if the viewer is closed, and the viewer picks up the result
when it is next opened. a SIGTERM (the viewer's Cancel) stops the run and marks it cancelled

run: python3 studies/run_study.py config.json [--status status.json]
"""
import json
import math
import os
import signal
import sys
import time
import traceback
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
import engine.flow as flow
from engine.flow import Body, Particle
from engine.logger import Log
from engine.constants import *
from engine.vectors import length

PROGRESS_EVERY = 0.5     #seconds between progress lines
ESTIMATE_STEPS = 2000    #steps timed for the duration estimate
COARSE_STEPS = 20000     #most steps in a coarse run used to estimate how long an end condition takes
LOG_OVERHEAD = 1.2       #logging and checks on top of the calculator's own time per step


class Cancelled(Exception):
  pass


def say(*args):
  """print, ignoring a closed pipe (nothing is listening any more)"""
  try:
    print(*args, flush=True)
  except (BrokenPipeError, OSError):
    pass


def writeStatus(path, **fields):
  """update the status file: read it, change fields, write it back in one step"""
  if not path:
    return
  try:
    with open(path) as f:
      status = json.load(f)
  except (OSError, ValueError):
    status = {}
  status.update(fields)
  tmp = path + '.tmp'
  with open(tmp, 'w') as f:
    json.dump(status, f)
  os.replace(tmp, path)


def calculators():
  """the calculators a sim can use, by name"""
  return list(flow.CALCULATORS)


def build(cfg):
  """the calculator and the particle at its start"""
  bodies = [Body(b['mass'], b['x'], b['y'], black=b['black']) for b in cfg['bodies']]
  calc = flow.makeCalculator(cfg['calculator'], bodies)
  p = Particle()
  p.pos = np.array(cfg['position'], dtype=float)
  v = np.array(cfg['velocity'], dtype=float)
  if hasattr(calc, 'initPV'):
    calc.initPV(p, v)   #flow calculators also need u and w
  else:
    p.v = v
  return calc, p


def nearest(calc, pos):
  return min(length(pos - b.pos) for b in calc.bodies)


class Ending:
  """the end condition, and roughly how far through it a run is"""

  def __init__(self, cfg, calc, p):
    self.kind, self.value = cfg['end']['kind'], float(cfg['end']['value'])
    self.d0 = nearest(calc, p.pos)
    self.angle = 0.0   #turned round the origin, for orbit runs
    self.crossings = 0

  def step(self, old, pos):
    a0, a1 = math.atan2(old[1], old[0]), math.atan2(pos[1], pos[0])
    self.angle += abs((a1 - a0 + math.pi) % (2*math.pi) - math.pi)
    crossed = old[1] < 0 and pos[1] >= 0   #as Calculator.orbitalSim counts orbits
    if crossed:
      self.crossings += 1
    return crossed

  def done(self, t, calc, pos):
    if not np.all(np.isfinite(pos)):
      return 'position is not finite'
    if self.kind == 'time':
      return t >= self.value and 'elapsed time reached'
    d = nearest(calc, pos)
    if self.kind == 'min':
      return d < self.value and 'reached %g m from a body' % self.value
    if self.kind == 'max':
      return d > self.value and '%g m from every body' % self.value
    return self.crossings >= self.value + 1 and '%d orbits' % self.value   #+1 for the warmup crossing

  def progress(self, t, calc, pos):
    if self.kind == 'time':
      f = t / self.value
    elif self.kind == 'orbits':
      f = self.angle / (2*math.pi*(self.value + 1))
    else:
      d = nearest(calc, pos)
      f = (self.d0 - d) / (self.d0 - self.value) if self.kind == 'min' else (d - self.d0) / (self.value - self.d0)
    return min(max(f, 0.0), 0.999)


def timePerStep(cfg):
  calc, p = build(cfg)
  t0 = time.time()
  for _ in range(ESTIMATE_STEPS):
    calc.move(p, cfg['dt'])
  return (time.time() - t0) / ESTIMATE_STEPS * LOG_OVERHEAD


def stepConfig(cfg, factor=1):
  """the steps' Config: fixed dt, or adaptive with stepFraction - both made factor times bigger for a quick run"""
  config = flow.Config()
  config.dt = cfg['dt'] * factor
  if cfg.get('stepFraction'):
    config.stepFraction = cfg['stepFraction'] * factor
  return config


def coarseSteps(cfg, factor):
  """steps to the end condition with steps factor times bigger, or None if not reached in COARSE_STEPS"""
  calc, p = build(cfg)
  ending = Ending(cfg, calc, p)
  t = 0.0
  for n, dt in enumerate(calc.steps(p, stepConfig(cfg, factor)), 1):
    old = p.pos.copy()
    calc.move(p, dt)
    t += dt
    ending.step(old, p.pos)
    if ending.done(t, calc, p.pos):
      return n
    if n >= COARSE_STEPS:
      return None


def estimate(cfg):
  """(steps or None, seconds or None, how it was worked out)"""
  per = timePerStep(cfg)
  dt = cfg['dt']
  end = cfg['end']
  adaptive = bool(cfg.get('stepFraction'))
  if end['kind'] == 'time' and not adaptive:
    steps, how = end['value'] / dt, 'exact'
  else:
    steps, how = None, ''
    if end['kind'] == 'orbits' and not adaptive:
      gm = G * sum(b['mass'] for b in cfg['bodies'])
      r = length(cfg['position'])
      v = length(cfg['velocity'])
      inv = 2/r - v*v/gm
      if inv > 0:
        a = 1/inv
        steps, how = (end['value'] + 1) * 2*math.pi*math.sqrt(a**3/gm) / dt, "from the orbit's period"
    if steps is None:
      #a quick run with much larger steps, then scaled back: finer if the end came too soon to count well
      for factor in ((100, 10, 1) if adaptive else (1000, 100, 10, 1)):
        n = coarseSteps(cfg, factor)
        if n is None:
          if steps is None:
            return None, None, 'the end condition was not reached in a quick run of %d steps' % COARSE_STEPS
          break
        steps, how = n * factor, 'from a quick run with %s x %d' % ('the step fraction' if adaptive else 'dt', factor)
        if n >= 500:
          break
  return steps, steps * per, how


def run(cfg, configPath=None, statusPath=None):
  calc, p = build(cfg)
  dt = cfg['dt']
  adaptive = bool(cfg.get('stepFraction'))
  log = Log(cfg['name'], True, True, cfg.get('logDir'))   #logDir: tests send theirs to tests/logs
  calc.log = log
  every = cfg['every'] if adaptive else dt * max(1, round(cfg['every'] / dt))   #fixed steps: a whole number between rows
  log.freq = every
  log.print('study type: %s' % cfg['type'])   #the viewer splits orbit runs into their orbits
  log.print('sim from the viewer:', json.dumps(cfg))
  log.print('calc: ', calc)
  log.logSteps(stepConfig(cfg))
  log.logBodies(calc)
  log.print('initial pos', p.pos)
  log.print('initial v', p.v)
  log.starttime = time.time()
  log.startpos = p.pos
  log.csvWriter.writerow([0.0, p.pt, length(p.pos), p.pos[0], p.pos[1], p.v[0], p.v[1]])   #the starting row
  with open(log.file.name[:-4] + '.json', 'w') as f:
    json.dump(cfg, f, indent=2)

  ending = Ending(cfg, calc, p)
  n, t, last = 0, 0.0, 0.0
  for dt in calc.steps(p, stepConfig(cfg)):
    n += 1
    old = p.pos.copy()
    calc.move(p, dt)
    t += dt
    wrote = log.updatePosition(p, dt)
    if ending.step(old, p.pos) and cfg['type'] == 'orbit':
      log.logOrbit()
    reason = ending.done(t, calc, p.pos)
    if reason:
      break
    now = time.time()
    if now - last > PROGRESS_EVERY:
      f = ending.progress(t, calc, p.pos)
      say('progress %.4f' % f)
      writeStatus(statusPath, progress=f)
      last = now
  if not wrote:   #the last row, unless updatePosition has just written it
    log.csvWriter.writerow([log.t, p.pt, length(p.pos), p.pos[0], p.pos[1], p.v[0], p.v[1]])
  log.print()
  log.print('stopped:', reason, 'after', n, 'steps')
  if cfg['type'] == 'orbit':
    log.finishOrbit()
  else:
    log.finishHyperbolic(p)
  log.print('final pos', p.pos)
  log.print('final v', p.v)
  log.print('final pt', p.pt)
  log.close()
  say('progress 1')
  say('file', log.csvFile.name)
  return log.csvFile.name


def main(argv):
  configPath = argv[1]
  statusPath = argv[argv.index('--status') + 1] if '--status' in argv else None

  def stop(signum, frame):
    raise Cancelled()
  signal.signal(signal.SIGTERM, stop)
  writeStatus(statusPath, pid=os.getpid(), state='running', progress=0.0)
  try:
    with open(configPath) as f:
      csvPath = run(json.load(f), configPath, statusPath)
  except Cancelled:
    writeStatus(statusPath, state='cancelled')
    return 1
  except BaseException:
    writeStatus(statusPath, state='failed', error=traceback.format_exc()[-2000:])
    raise
  writeStatus(statusPath, state='done', progress=1.0, file=csvPath, finished=time.time())
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
