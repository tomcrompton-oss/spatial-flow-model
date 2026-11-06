"""
flow lines: a path out from a body, starting at the escape speed |u| heading straight away from it and moving
under the combined gravity g of all the bodies (RK4), until it reaches a body, gets far away, or runs too long -
used by studies/flow_lines.py and the viewer's Flow lines background
"""
import math
import numpy as np
from engine.constants import *

START = RSUN            #lines start this far from their body's centre
MAX_DISTANCE = 4*AU     #lines stop this far from the origin
STEP = 0.002            #each step moves about this fraction of the distance to the nearest body
MAX_STEPS = 200000      #lines stop after this many steps
CSV_EVERY = 10          #steps between saved rows


def line(calc, home, angle, start=START, maxDistance=MAX_DISTANCE, step=STEP, every=CSV_EVERY):
  """
  follow one line out from body home at angle (radians) - also used by the viewer's flow lines background
  returns the rows (t, pos, v) every few steps, why it stopped and the number of steps
  """
  out = np.array([math.cos(angle), math.sin(angle)])
  pos = home.pos + start*out
  v = np.linalg.norm(calc.flow(pos))*out
  t = 0.0
  rows = [(t, pos, v)]
  for i in range(1, MAX_STEPS + 1):
    nearest = min(np.linalg.norm(pos - b.pos) for b in calc.bodies)
    dt = step*nearest/np.linalg.norm(v)
    k1x, k1v = v, calc.gravity(pos)
    k2x, k2v = v + k1v*dt/2, calc.gravity(pos + k1x*dt/2)
    k3x, k3v = v + k2v*dt/2, calc.gravity(pos + k2x*dt/2)
    k4x, k4v = v + k3v*dt, calc.gravity(pos + k3x*dt)
    pos = pos + (k1x + 2*k2x + 2*k3x + k4x)*dt/6
    v = v + (k1v + 2*k2v + 2*k3v + k4v)*dt/6
    t += dt
    reason = None
    for b in calc.bodies:
      if np.linalg.norm(pos - b.pos) < start:
        reason = 'back to own body' if b is home else 'reached ' + ('black' if b.black else 'white') + ' body'
    if np.linalg.norm(pos) > maxDistance:
      reason = '%g AU out' % (maxDistance/AU)
    if reason or i % every == 0:
      rows.append((t, pos, v))
    if reason:
      return rows, reason, i
  return rows, 'step limit', MAX_STEPS
