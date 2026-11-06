"""
run one simulation from a json config - used by the viewer's Sim tab, and runnable on its own

config (SI units):
  name          the log name; files are logs/<study>/<name>_<datetime>.log / .csv (and .json, the config), <study> being the name up to its first _
  type          (older configs: 'orbit' or 'hyperbolic' - no longer used: every run counts orbits as they happen)
  calculator    a name in flow.CALCULATORS, e.g. 'SpecialFlowCalculator, second order' (older names work too)
  bodies        [{"mass": kg, "x": m, "y": m, "black": true}, ...]
  position      [x, y] m      the particle's start
  velocity      [vx, vy] m/s  its starting velocity
  dt            seconds per step; with stepFraction, the longest step
  stepFraction  optional: adaptive steps, each moving at most this fraction of the distance to the nearest body
                (flow.Calculator.stepSize); without it every step is dt
  every         seconds between csv rows (with fixed steps, rounded to whole steps)
  logDir        optional: a folder for the files instead of logs/<folder>/ (the regression tests use it)
  end           one of these, or a list of them (the run stops at the first reached):
                {"kind": "time", "value": s}          elapsed time
                {"kind": "properTime", "value": s}    the particle's proper time
                {"kind": "min", "value": m}           closer than this to any body
                {"kind": "max", "value": m}           farther than this from every body
                {"kind": "orbits", "value": n}        n whole orbits (the part orbit before the first boundary aside)

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
from engine.run import Ending, OrbitCounter
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


def ends(cfg):
  """
  the end conditions as engine/run.py takes them: cfg['end'] is one {"kind", "value"} or a list of them, the run
  stopping at the first reached
  """
  end = cfg['end']
  return [(e['kind'], int(e['value']) if e['kind'] == 'orbits' else float(e['value'])) for e in (end if isinstance(end, list) else [end])]


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
  """steps to the end with steps factor times bigger, or None if not reached in COARSE_STEPS"""
  calc, p = build(cfg)
  counter = OrbitCounter(calc, p)
  ending = Ending(ends(cfg), calc, p, counter)
  t = 0.0
  for n, dt in enumerate(calc.steps(p, stepConfig(cfg, factor), ending.timeLimit()), 1):
    calc.move(p, dt)
    t += dt
    counter.step(p.pos)
    if ending.after(t, p):
      return n
    if n >= COARSE_STEPS:
      return None
  return n   #the time limit


def estimate(cfg):
  """(steps or None, seconds or None, how it was worked out)"""
  per = timePerStep(cfg)
  dt = cfg['dt']
  end = ends(cfg)
  adaptive = bool(cfg.get('stepFraction'))
  if [kind for kind, _ in end] == ['time'] and not adaptive:
    steps, how = end[0][1] / dt, 'exact'
  else:
    steps, how = None, ''
    if [kind for kind, _ in end] == ['orbits'] and not adaptive:
      gm = G * sum(b['mass'] for b in cfg['bodies'])
      r = length(cfg['position'])
      v = length(cfg['velocity'])
      inv = 2/r - v*v/gm
      if inv > 0:
        a = 1/inv
        steps, how = (end[0][1] + 0.75) * 2*math.pi*math.sqrt(a**3/gm) / dt, "from the orbit's period"
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
  log.print('sim from the viewer:', json.dumps(cfg))
  log.print('initial pos', p.pos)
  log.print('initial v', p.v)
  with open(log.file.name[:-4] + '.json', 'w') as f:
    json.dump(cfg, f, indent=2)

  last = [0.0]
  def progress(ending, t, p):
    now = time.time()
    if now - last[0] > PROGRESS_EVERY:
      f = ending.progress(t, p)
      say('progress %.4f' % f)
      writeStatus(statusPath, progress=f)
      last[0] = now
  calc.run(p, stepConfig(cfg), log, ends(cfg), progress)
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
