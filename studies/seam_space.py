"""
the seam as a source of space: with the potential flow round two bodies at rest (engine/two_centre.py's exact
flow, turned about the line through the bodies into 3D), the flow on each side of the seam points away from it, so
the seam is a sheet where space appears, at sigma = (u_1 - u_0) . n per unit area (n from region 0 into 1). elsewhere
the flow converges, div u = -(3/2) |u|/r round one body, so space disappears through the volume, and the bodies, as
points, take in none (|u| r^2 -> 0). within a sphere of radius R about the pair's middle:

  in through the sphere  + made at the seam  =  lost in the volume

measured for two equal bodies and for the Sun and the Earth (each at rest, the flow flat - the model of Part 2's
Potential Flow: these are coordinate volumes, the flow's own bookkeeping). also: the largest jump across the seam,
and how the seam's rate compares with a body's own inflow at the seam's distance

run: python3 studies/seam_space.py     (a minute or two; prints, and writes logs/modelChecks/seamSpace_<datetime>/summary.log)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import Body, SpecialFlowCalculator
from engine.logger import LOG_DIR
from engine.constants import MS, ME, AU, G

CASES = [('two equal bodies of a solar mass, 200,000 km apart', [Body(MS, -1e8, 0.0), Body(MS, 1e8, 0.0)], 2e8),
         ('the Sun and the Earth, 1 AU apart', [Body(MS, 0.0, 0.0), Body(ME, AU, 0.0)], AU)]


def seamCurve(calc, D, light, n=400, reach=30.0):
  """the seam in the half plane y > 0: points where the region changes, found along rays out of the lighter body
  (angles 0 to pi), each by halving; None where no change is found out to reach x D"""
  field = calc.rayField()
  centre = calc.bodies[light].pos
  pts = []
  for th in np.linspace(1e-4, math.pi - 1e-4, n):
    d = np.array([math.cos(th), math.sin(th)])
    lo, hi = 1e-3*D, reach*D
    if field.region(centre + hi*d) == light:
      continue
    for _ in range(60):
      mid = math.sqrt(lo*hi)
      if field.region(centre + mid*d) == light:
        lo = mid
      else:
        hi = mid
    pts.append(centre + math.sqrt(lo*hi)*d)
  return np.array(pts)


def jump(calc, x, light):
  """the flow on the lighter body's side and the other's at x, and the normal from the light side out"""
  other = 1 - light
  u0, u1 = calc.flow(x, light), calc.flow(x, other)
  n = (u1 - u0)/np.linalg.norm(u1 - u0)
  return u0, u1, n


def budget(calc, D, light, R, curve):
  """within a sphere of radius R about the middle: made at the seam (m^3/s), in through the sphere, lost in the volume"""
  middle = (calc.bodies[0].pos + calc.bodies[1].pos)/2
  made = 0.0
  for a, b in zip(curve[:-1], curve[1:]):
    m = (a + b)/2
    if np.linalg.norm(m - middle) > R:
      continue
    u0, u1, n = jump(calc, m, light)
    sigma = (u1 - u0) @ n
    made += sigma*2*math.pi*abs(m[1])*np.linalg.norm(b - a)    #turned about the line through the bodies
  inflow = 0.0
  ths = np.linspace(0, math.pi, 721)
  for t0, t1 in zip(ths[:-1], ths[1:]):
    th = (t0 + t1)/2
    x = middle + R*np.array([math.cos(th), math.sin(th)])
    u = calc.flow(x, calc.region(x))
    inflow += -(u @ ((x - middle)/R))*2*math.pi*R*math.sin(th)*R*(t1 - t0)
  return made, inflow, inflow + made


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'seamSpace_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = ['the seam as a source of space, the flow flat and the bodies at rest, in 3D (the flow turned about the line'
           ' through the bodies); volumes per second within a sphere of radius R about the middle']
  for label, bodies, D in CASES:
    calc = SpecialFlowCalculator(bodies, 2)
    light = int(np.argmin([b.mass for b in bodies]))
    curve = seamCurve(calc, D, light)
    lines.append(label + ': the seam found at %d of 400 angles round the lighter body' % len(curve))
    jumps = [(np.linalg.norm(jump(calc, x, light)[1] - jump(calc, x, light)[0]), x) for x in curve]
    big, where = max(jumps, key=lambda j: j[0])
    u0, u1, n = jump(calc, where, light)
    lines.append('  the largest jump in the flow across it: %.3e m/s at (%.3e, %.3e) m; the flow there %.3e m/s;'
                 ' across the seam the flows point %s it' % (big, where[0], where[1], np.linalg.norm(u0),
                                                           'away from' if (u1 - u0) @ n > 0 else 'into'))
    for R in (0.6*D, 1.0*D, 3.0*D, 10.0*D):
      made, inflow, lost = budget(calc, D, light, R, curve)
      lines.append('  R = %4.1f D: made at the seam %.3e m^3/s, in through the sphere %.3e, lost in the volume %.3e;'
                   ' the seam\'s share %.3f' % (R/D, made, inflow, lost, made/lost))
    print('\n'.join(lines), flush=True)
  lines.append('the same, for the two equal bodies with the seam moved (the constant between their S, in units of S at'
               ' the saddle - studies/seam_rules.py shows light still follows GR): how much the seam makes depends on'
               ' where it is put')
  label, bodies, D = CASES[0]
  for shift in (-0.3, -0.1, 0.0, 0.1, 0.3):
    calc = SpecialFlowCalculator([Body(b.mass, b.pos[0], b.pos[1]) for b in bodies], 2)
    field = calc.rayField()
    field.offsets[1] += shift*field.action(field.saddle(0, 1), 0)
    curve = seamCurve(calc, D, 0)
    made, inflow, lost = budget(calc, D, 0, 1.0*D, curve)
    lines.append('  shift %+.1f: within R = 1 D, made at the seam %.3e m^3/s, lost in the volume %.3e, the seam\'s share %.3f'
                 % (shift, made, lost, made/lost))
    print(lines[-1], flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
