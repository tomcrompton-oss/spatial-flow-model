"""
light sent back from an object that falls towards a black hole and comes back out

the object falls from rest at infinity (moving with the flow, v = u, w = 0) from START towards a single black hole,
as astroDescendBlack in coded_studies.py. it can't come back from the Schwarzschild radius, so at TURN Schwarzschild radii it
turns round and climbs back to START at the escape speed, w = u relativistically added to itself away from the body
(as astroAscend in coded_studies.py). every interval, on the way down and back up, it sends a light ray straight out
(w = c away from the body), which is followed until it gets back to the object's starting distance

the interval is a round number giving RAYS rays before a fall all the way to the horizon (200 s for the 4e6 MS case)

each run writes to logs/lightEcho/lightEcho_<datetime>/:
  object_<datetime>.csv / .log   the object, down and back up in one path
  ray<n>_<datetime>.csv / .log   each light ray, with t carrying on from its emission time
the .log files list the body, so csv_viewer.py draws it for any of them

run: python3 studies/light_echo.py      (then: python3 viewer/csv_viewer.py logs/lightEcho/lightEcho_<datetime>/*.csv)
"""
import math
import os
from datetime import datetime
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, Particle, SpecialFlowCalculator
from engine.logger import Log, LOG_DIR
from engine.constants import *
from engine.exact import fallTime, rayTime

MASS = 4000000*MS
START = 1.025*AU
DT = 0.01               #seconds per step
OBJECT_FREQ = 10        #seconds between csv rows for the object
RAY_FREQ = 10           #seconds between csv rows for each ray
RAYS = 6                #rays in a fall to the horizon - sets the interval
TURN = 2.0              #the object turns round this many Schwarzschild radii from the body
MAX_JOURNEY_TIME = 100  #the object's climb is given up on after this many times the fall time
MAX_RAY_TIME = 100      #a ray that has not got back after this many times the fall time is given up on


def niceBelow(value):
  """the largest round number (1, 2, 2.5 or 5 x 10^n) not above value"""
  mag = 10 ** math.floor(math.log10(value))
  return max(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag <= value)


def firstRow(log, p, t):
  """the starting row, which updatePosition (writing after each step) leaves out"""
  log.csvWriter.writerow([t, p.pt, np.linalg.norm(p.pos), p.pos[0], p.pos[1], p.v[0], p.v[1]])


def logDir(stamp):
  return os.path.join(LOG_DIR, 'lightEcho', 'lightEcho_' + stamp)


def fall(calc, gm, rs, interval, folder):
  """the falling object; returns (t, pos, pt) at each emission"""
  log = Log('object', True, True, folder)
  log.freq = OBJECT_FREQ
  log.print('object falling to %g rs from a black hole and back, sending light back out every %g s' % (TURN, interval))
  log.logBodies(calc)
  p = Particle()
  p.pos = np.array([0.0, START])
  calc.initPFreefall(p)   #moving with the flow: v = u, w = 0
  log.print('initial pos', p.pos)
  log.print('initial v', p.v)
  log.print('Schwarzschild radius', rs)
  log.print('dt', DT)
  firstRow(log, p, 0.0)
  emissions = []
  every = round(interval/DT)
  step = 0
  leg = 'down'
  limit = MAX_JOURNEY_TIME*fallTime(gm, START, TURN*rs)
  while True:
    calc.move(p, DT)
    log.updatePosition(p, DT)
    step += 1
    d = np.linalg.norm(p.pos)
    if step % every == 0:
      emissions.append((step*DT, p.pos.copy(), p.pt, leg))
      log.print('ray %d sent on the way %s at t %g s, d %.6e m (%.4f rs), pt %.4f s' % (len(emissions), leg, step*DT, d, d/rs, p.pt))
    if leg == 'down' and d <= TURN*rs:
      turned = step*DT
      predicted = fallTime(gm, START, d)
      log.print()
      log.print('turned round at %.6e m (%.4f rs) at t %g s (fall predicted %.4f s, accuracy %.5f%%), pt %.4f s'
                % (d, d/rs, turned, predicted, 100 - 100*abs(turned - predicted)/predicted, p.pt))
      log.print('  v before', p.v, ' |v|/c', np.linalg.norm(p.v)/C)
      u = calc.flow(p.pos)
      calc.initPW(p, calc.addSI(-u, -u))   #the escape speed outwards: u added to itself, away from the body
      log.print('  v after ', p.v, ' |v|/c', np.linalg.norm(p.v)/C, '  w', p.w, ' |w|/c', np.linalg.norm(p.w)/C)
      log.print()
      leg = 'up'
    elif leg == 'up' and d >= START:
      break
    if step*DT > limit:
      log.print('did not get back within %g s' % limit)
      break
  log.csvFile.flush()
  t = step*DT
  log.print()
  log.print('back at %.6e m at t %g s: %g s down, %g s up, pt %.4f s' % (d, t, turned, t - turned, p.pt))
  log.print('final v', p.v, ' |v|/c', np.linalg.norm(p.v)/C)
  return emissions, turned, t


def ray(calc, rs, n, sent, pos, folder, limit):
  """one light ray from pos, sent at time sent, straight away from the body; returns its arrival time or None"""
  log = Log('ray%d' % n, True, True, folder)
  log.freq = RAY_FREQ
  log.t = sent   #the csv's t carries on from the emission
  log.print('light ray %d: sent straight out at t %g s from d %.6e m (%.4f rs)' % (n, sent, np.linalg.norm(pos), np.linalg.norm(pos)/rs))
  log.logBodies(calc)
  p = Particle()
  p.pos = pos.copy()
  p.pt = 0.0
  calc.initPW(p, C*pos/np.linalg.norm(pos))   #c relative to the local flow, outwards
  log.print('initial v', p.v, ' (c - u = %.6e m/s)' % (C - np.linalg.norm(p.u)))
  firstRow(log, p, sent)
  steps = 0
  while np.linalg.norm(p.pos) < START:
    calc.move(p, DT)
    log.updatePosition(p, DT)
    steps += 1
    if steps*DT > limit:
      log.print('did not get back within %g s' % limit)
      return None
  log.csvFile.flush()
  arrived = sent + steps*DT
  predicted = rayTime(rs, np.linalg.norm(pos), START)
  log.print('back at %.6e m at t %g s: %g s in flight (predicted %.4f s, accuracy %.5f%%)'
            % (np.linalg.norm(p.pos), arrived, steps*DT, predicted, 100 - 100*abs(steps*DT - predicted)/predicted))
  return arrived


def main():
  stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
  folder = logDir(stamp)
  gm = G*MASS
  rs = 2*gm/C**2
  calc = SpecialFlowCalculator([Body(MASS)], order=1)
  interval = niceBelow(fallTime(gm, START, rs)/RAYS)
  emissions, turned, back = fall(calc, gm, rs, interval, folder)

  summary = Log('summary', True, False, folder)
  summary.print('light echo: %g MS black hole, object from %g AU to %g rs and back, ray every %g s' % (MASS/MS, START/AU, TURN, interval))
  summary.print('object turned round at t %g s and was back at t %g s' % (turned, back))
  summary.print()
  summary.print('  %-4s %-5s %10s %14s %12s %12s %14s' % ('ray', 'leg', 'sent (s)', 'd sent (rs)', 'flight (s)', 'back at (s)', 'gap (s)'))
  last = None
  for n, (sent, pos, pt, leg) in enumerate(emissions, 1):
    arrived = ray(calc, rs, n, sent, pos, folder, MAX_RAY_TIME*back)
    gap = '' if arrived is None or last is None else '%.2f' % (arrived - last)
    summary.print('  %-4d %-5s %10g %14.4f %12s %12s %14s' % (n, leg, sent, np.linalg.norm(pos)/rs,
                  '-' if arrived is None else '%.2f' % (arrived - sent), '-' if arrived is None else '%.2f' % arrived, gap))
    last = arrived if arrived is not None else last
  summary.print()
  summary.print('files in', folder)


if __name__ == '__main__':
  main()
