"""
check 2, the flow against g: space moving with the flow should accelerate at Newton's g, so the flow's change along
itself - the difference in the flow between two close points on its own path - is g:

  a = (u . grad) u + du/dt  ~  [u(x + u h/2, t + h/2) - u(x - u h/2, t - h/2)]/h,   h = 2e-4 d/|u|

(d the distance to the nearest body: the two points 1e-4 d either side of x, both from x's side of any seam; and
again at half that, the two combined to take out the difference's h^2 error - smaller steps lose more to rounding the
flow at 1 AU's coordinates than they gain). a is
compared with g from the bodies where they are at t, over a grid across the bodies and rings round each, and the error
taken against the sum of the bodies' pulls there, sum GM/d^2 (the scale a cross term between them would have; g itself
is 0 at the saddle). for one body every flow is the one-body flow, whose a is g exactly, so it is the floor

the split model has no one flow: each body's flow acts alone, in that body's frame (engine/split.py frame). its a is
the same difference for each body's flow there, mapped back to the lab and added up - what its steps use. its frame
rules move the frames at the others' flow, which changes a only at order (that flow/c)^2. with Galilean frames a
moving body's flow is carried at its velocity, whose change (the body's own acceleration) the steps leave out, and so
does a here. (the sum of its flows, which
no step uses, is the vectors' flow)

  one        one body (the floor): rings and grid round it on the AU's scale
  equal      two equal masses 1 AU apart
  unequal    1 and 0.1 solar masses 1 AU apart
  sunEarth   the Sun and the Earth 1 AU apart: the grid, and rings round the Earth from its surface to 0.1 AU (and the
             error at its surface in m/s^2, where the vectors were 37-74 m/s^2 out: studies/multi_body_rules.py)
  three      1, 0.5 and 0.3 solar masses on a triangle: the eikonal flow from its ray tables (engine/eikonal.py)
  turning    the Sun and the Earth going round each other, the eikonal flow turning with them (combine 'turning',
             studies/turning_eikonal.py): with du/dt, at t = a tenth of a year; where its flow has no paths (|w|^2 < 0)
             the point is counted as not covered, and so is one past its tables (where the flow is only a stand-in, straight
             in to the nearest body)

run: python3 studies/flow_gravity.py [setup ...]     (default all; prints, and writes
     logs/modelChecks/flowGravity_<datetime>/summary.log)
"""
import io
import contextlib
import math
import os
import sys
from datetime import datetime
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, SpecialFlowCalculator, turn
from engine.split import SplitFlowCalculator, bodyVelocity
from engine.logger import LOG_DIR
from engine.vectors import length
from engine.constants import *

STEP = float(os.environ.get('FLOWG_STEP', 1e-4))   #each point this fraction of the distance to the nearest body from x
                                                  #(and half that: see richardson)
RINGS = (0.01, 0.03, 0.1, 0.3)   #ring radii round each body, in the bodies' separation
ANGLES = 16
GOOD = 1e-3            #an error this small (of the pulls) counts as matching
SPLIT = ('galilean', 'lorentz', 'local', 'freefall', 'carried', 'heavier', 'heavier-only', 'heavier-centre')
YEAR = 365.25*DAY


def setups():
  mu = ME/(MS + ME)
  omega = math.sqrt(G*(MS + ME)/AU**3)
  return {
    'one': ([Body(MS)], 0.0),
    'equal': ([Body(MS, -AU/2, 0.0), Body(MS, AU/2, 0.0)], 0.0),
    'unequal': ([Body(MS, -AU/2, 0.0), Body(0.1*MS, AU/2, 0.0)], 0.0),
    'sunEarth': ([Body(MS, -AU, 0.0), Body(ME)], 0.0),
    'three': ([Body(MS, -AU/2, 0.0), Body(0.5*MS, AU/2, 0.0), Body(0.3*MS, 0.0, 0.8*AU)], 0.0),
    'turning': ([Body(MS, -mu*AU, 0.0, circling=omega), Body(ME, (1 - mu)*AU, 0.0, circling=omega)], 0.1*YEAR),
  }


def models(setup):
  """the models run on a setup, by name"""
  if setup == 'one':
    return ['one body']
  if setup == 'turning':
    return ['turning'] + ['split ' + b for b in SPLIT]
  flows = ['vectors', 'along g', 'eikonal (tables)' if setup == 'three' else 'eikonal']
  return flows + ['split ' + b for b in SPLIT]


def calculator(model, bodies):
  if model == 'one body':
    return SpecialFlowCalculator(bodies, 2)
  if model == 'vectors':
    return SpecialFlowCalculator(bodies, 2, combine='vectors')
  if model == 'along g':
    return SpecialFlowCalculator(bodies, 2, direction='g')
  if model == 'eikonal':
    return SpecialFlowCalculator(bodies, 2, direction='eikonal-exact')
  if model == 'eikonal (tables)':
    return SpecialFlowCalculator(bodies, 2, direction='eikonal')
  if model == 'turning':
    return SpecialFlowCalculator(bodies, 2, combine='turning')
  boost = model.split(' ', 1)[1]
  return SplitFlowCalculator(bodies, 'interval' if boost == 'galilean' else 'static', boost)


def points(bodies, t):
  """the grid over the bodies (spaced a tenth of their separation, none within 2% of one) and the rings round each"""
  places = [b.at(t) for b in bodies]
  centre = sum(places)/len(places)
  sep = max(length(a - b) for a in places for b in places) or AU   #one body: rings and grid on the AU's scale
  out = []
  for y in np.arange(-1.5, 1.501, 0.1):
    for x in np.arange(-2.0, 2.001, 0.1):
      q = centre + sep*np.array([x, y])
      if min(length(q - X) for X in places) > 0.02*sep:
        out.append(('grid', q))
  for i, X in enumerate(places):
    for r in RINGS:
      for k in range(ANGLES):
        a = 2*math.pi*(k + 0.5)/ANGLES
        out.append(('ring %d %.2g' % (i, r), X + r*sep*np.array([math.cos(a), math.sin(a)])))
  return out


def newton(bodies, x, t):
  """Newton's g at x with the bodies where they are at t, and the sum of their pulls' sizes"""
  g, pulls = np.zeros(2), 0.0
  for b in bodies:
    r = x - b.at(t)
    d = length(r)
    g -= b.GM*r/d**3
    pulls += b.GM/d**2
  return g, pulls


def flowAccel(calc, x, t):
  """the flow's change along itself at x, t (None where it has no flow)"""
  side = calc.region(x, t)
  if calc.combine == 'turning' or calc.direction == 'eikonal':
    field = calc.rayField()
    there = turn(x, -calc.omega*t) if calc.combine == 'turning' else x
    if all(field.action(there, i) is None for i in range(len(calc.bodies))):
      return None   #past its tables: the flow there is only a stand-in (straight in to the nearest body, or along g)
  u = calc.flow(x, side, t)
  speed = length(u)
  if speed == 0:
    return None
  def change(step):
    h = 2*step*min(calc.nearest(x, t)/speed, turnTime(calc))
    return (calc.flow(x + u*h/2, side, t + h/2) - calc.flow(x - u*h/2, side, t - h/2))/h
  return richardson(change)


def turnTime(calc):
  """1/Omega for bodies going round (h is kept below the step's fraction of it, as the bodies move); else infinite"""
  spins = [abs(b.circling) for b in calc.bodies if b.circling]
  return 1/max(spins) if spins else float('inf')


def richardson(change):
  """(4 a(STEP/2) - a(STEP))/3: the centred difference's h^2 error taken out, at a step rounding doesn't swamp"""
  return (4*change(STEP/2) - change(STEP))/3


def splitAccel(calc, x, t):
  """each body's flow's change along itself, in its own frame (as the steps take it), back in the lab, added up"""
  a = np.zeros(2)
  for b in calc.bodies:
    if calc.boost == 'galilean':
      V = bodyVelocity(b, t)
      u = calc.bodyFlow(b, x, t)
      def change(step):
        h = 2*step*min(length(x - b.at(t))/length(u - V), turnTime(calc))
        a = (calc.bodyFlow(b, x + u*h/2, t + h/2) - calc.bodyFlow(b, x - u*h/2, t - h/2))/h
        return a - (bodyVelocity(b, t + h/2) - bodyVelocity(b, t - h/2))/h   #as the steps: the flow's change only
      a += richardson(change)
      continue
    f = calc.frame(b, t, x)
    x0 = f.event(t, x)[1]
    u0 = calc.restFlow(b, x0)
    def change(step):
      h = 2*step*length(x0)/length(u0)
      du = calc.restFlowChange(b, x0 - u0*h/2, u0*h)   #the change from x0 - u0 h/2 to x0 + u0 h/2, in b's frame
      T = f.delta(t, x, h, f.back(u0, x)*h)[0]           #frame time for lab time h along that motion
      return f.backChange(u0, du)/(h*h/T)                #per lab second: du per frame time h, times T/h
    a += richardson(change)
  return a


def measure(job):
  """one model on one setup: each point's error against Newton, of the pulls there"""
  setup, model = job
  bodies, t = setups()[setup]
  calc = calculator(model, bodies)
  rows = []
  with contextlib.redirect_stdout(io.StringIO()):
    for kind, x in points(bodies, t):
      g, pulls = newton(bodies, x, t)
      a = splitAccel(calc, x, t) if model.startswith('split') else flowAccel(calc, x, t)
      rows.append((kind, x, None if a is None else length(a - g)/pulls, None if a is None else length(a - g)))
    surface = None
    if setup in ('sunEarth', 'turning'):
      earth = bodies[1]
      errs = []
      for k in range(8):
        ang = 2*math.pi*k/8
        x = earth.at(t) + REARTH*np.array([math.cos(ang), math.sin(ang)])
        a = splitAccel(calc, x, t) if model.startswith('split') else flowAccel(calc, x, t)
        errs.append(math.nan if a is None else length(a - newton(bodies, x, t)[0]))
      surface = max(errs)
  return job, rows, surface


def describe(model, rows, surface):
  errs = np.array([r[2] for r in rows if r[2] is not None])
  covered = len(errs)/len(rows)
  near = [r[2] for r in rows if r[2] is not None and r[0].startswith('ring')]
  worst = max((r for r in rows if r[2] is not None), key=lambda r: r[2])
  text = ('  %-22s median %.1e  90%% %.1e  max %.1e  matching (< %g) %3.0f%%  rings max %.1e  covered %3.0f%%'
          '  worst at (%.2f, %.2f) AU [%s]'
          % (model, np.median(errs), np.percentile(errs, 90), errs.max(), GOOD, 100*np.mean(errs < GOOD),
             max(near), 100*covered, worst[1][0]/AU, worst[1][1]/AU, worst[0]))
  if surface is not None:
    text += '  Earth surface %.2e m/s^2' % surface
  return text


def main():
  chosen = sys.argv[1:] or [s for s in setups() if s != 'one']
  folder = os.path.join(LOG_DIR, 'modelChecks', 'flowGravity_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  jobs = [(s, m) for s in ['one'] + chosen for m in models(s)]
  with Pool(8) as pool:
    results = {job: (rows, surface) for job, rows, surface in pool.imap_unordered(measure, jobs)}
  lines = ['the flow against g: the flow\'s change along itself, [u(x + u h/2, t + h/2) - u(x - u h/2, t - h/2)]/h, '
           'against Newton\'s g; errors |a - g| as fractions of the sum of the bodies\' pulls there (grid and rings)']
  for s in ['one'] + chosen:
    lines.append('')
    lines.append('== %s' % s)
    for m in models(s):
      lines.append(describe(m, *results[(s, m)]))
  print('\n'.join(lines))
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
