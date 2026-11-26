"""
the J = 0 flow's bodies off circles: does each body still move with its space?

studies/binary_regularized.py moves the circular binary's bodies as geodesics of the whole J = 0 metric with their own
singular terms removed (Hadamard's partie finie), and shows that this is GR's motion (EIH) given two facts about the
flow at a body: its time's rate there is 1 (phi constant along the body's path, kappa = 0), and the flow's regular part
there is the body's own velocity - the flow round the body, averaged over a small circle, is the body's velocity (on
circles, to below 1e-9 m/s round the Earth). the rules' metric is GR's first post-Newtonian one in the J = 0 time for
any flow that keeps Bernoulli's equation (studies/flow_field_equations.py), so with those two facts the bodies move
by EIH whatever the orbit - and EIH gives GR's periastron advance at any eccentricity, keeps the centre of mass
(at first post-Newtonian order) still, and has no Nordtvedt effect

studies/eccentric_flow.py builds the flow for an eccentric binary with kappa = 0 by construction. this measures the
second fact: each body's flow near it, from the paths that arrive at it shortly after the snapshot (rings of 256
paths, at distances 0.002-0.1 a), averaged over the direction round the body, less the body's velocity, as a fraction
of the flow's own speed there. a regular part equal to the body's velocity means that average goes to 0 as the ring
shrinks, as the tide's terms average out on a circle; it is also given as a fraction of the body's own orbital speed

cases: mass ratios 0.1 and 1, e = 0 (the check) and 0.6, at periastron and apastron

run: python3 studies/eccentric_bodies.py     (under a minute; prints, and writes
     logs/modelChecks/eccentricBodies_<datetime>/summary.log, and a viewer file, ownSpace.full.json, of four of the
     cases)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.logger import LOG_DIR
import eccentric_flow as ef

ef.BACK = 0.02      #only paths that arrive soon after the snapshot: rings close to the body
ef.HITS = 40
RINGS = (2, 4, 7, 11, 16, 23, 31, 40)


def rings(orbit, k, ts):
  """for rows of arrival times: the ring's mean distance, |mean over direction of (u - v_body)| / mean |u - v_body|, and
  that mean / the body's own speed"""
  x, u, phi, alive = ef.family(orbit, k, ts)
  z, v = orbit.bodies(ts)[k]
  out = []
  for i in RINGS:
    i -= 1
    d = x[i] - z
    ang = np.arctan2(d[:, 1], d[:, 0])
    o = np.argsort(ang)
    ang, w = ang[o], (u[i] - v)[o]
    a2 = np.concatenate([ang, ang[:1] + 2*math.pi])
    w2 = np.concatenate([w, w[:1]], 0)
    da = np.diff(a2)
    mean = np.sum((w2[1:] + w2[:-1])/2*da[:, None], 0)/(2*math.pi)          #over the direction round the body
    speed = np.sum((np.linalg.norm(w2[1:], axis=1) + np.linalg.norm(w2[:-1], axis=1))/2*da)/(2*math.pi)
    out.append((float(np.mean(np.linalg.norm(d, axis=1))), float(np.linalg.norm(mean)/speed),
                float(np.linalg.norm(mean)/np.linalg.norm(v))))
  return out


PLOTTED = {(1.0, 0.0, 'periastron', 'heavier'): ('equal masses, circular', '#2a78d6', 'solid'),
           (1.0, 0.6, 'periastron', 'heavier'): ('equal masses, e 0.6, at periastron', '#1baf7a', 'solid'),
           (0.1, 0.6, 'periastron', 'heavier'): ('mass ratio 0.1, e 0.6, the heavier', '#eb6834', 'solid'),
           (0.1, 0.6, 'periastron', 'lighter'): ('mass ratio 0.1, e 0.6, the lighter', '#d6a21e', 'dashed')}


def writePlot(folder, plotted):
  """for the viewer: for a few of the cases, how far each body's averaged space is from moving with it (the mean less
  the body's velocity, / the body's speed) against the ring's mean distance, both as log10"""
  sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  from two_body_escapes import writeViewerFiles
  made = []
  x, y = 'ring distance (log10 r/a)', 'averaged flow less body velocity (log10 of its speed)'
  for key, (title, colour, style) in PLOTTED.items():
    if key not in plotted:
      continue
    path = os.path.join(folder, title + '.csv')
    with open(path, 'w') as f:
      f.write('%s,%s\n' % (x, y))
      for r, _, b in plotted[key]:
        f.write('%.6g,%.6g\n' % (math.log10(r), math.log10(b)))
    with open(path[:-4] + '.log', 'w') as f:
      f.write('the one-potential flow round a body of an eccentric binary (%s): its average round rings at mean distance'
              ' r (the separation a = 1), less the body\'s velocity, as a share of the body\'s speed; both log10\n' % title)
    made.append((path, colour, style))
  writeViewerFiles(folder, 'ownSpace', made, selection=((x, y),),
                   styles=lambda colour, style='solid': {'%s / %s' % (x, y): [colour, style, colour]},
                   preferences={'equalAspect': False, 'showBodies': False, 'showSchwarzschild': False,
                                'showGrid': True, 'showPathLegend': True})


def main():
  folder = os.path.join(LOG_DIR, 'modelChecks', 'eccentricBodies_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  lines = []
  def say(s):
    lines.append(s)
    print(s, flush=True)
  say('the flow round each body, averaged over the direction, less the body\'s velocity, / the flow\'s speed there;')
  say('rings at mean distance r (a = 1), from the nearest out')
  plotted = {}
  for q in (0.1, 1.0):
    for e in (0.0, 0.6):
      orbit = ef.Orbit(q, e)
      for ts, label in ((0.0, 'periastron'), (math.pi, 'apastron')):
        for k, name in ((0, 'heavier'), (1, 'lighter')):
          rs = rings(orbit, k, ts)
          power = np.polyfit(np.log([r for r, _, _ in rs[:4]]), np.log([f for _, f, _ in rs[:4]]), 1)[0]
          say('q %.1f e %.1f %-10s %-7s  r: %s' % (q, e, label, name, ' '.join('%.4f' % r for r, _, _ in rs)))
          say('%33s mean / flow speed: %s   (goes as r^%.1f)' % ('', ' '.join('%.1e' % f for _, f, _ in rs), power))
          say('%33s mean / body speed: %s' % ('', ' '.join('%.1e' % b for _, _, b in rs)))
          if (q, e, label, name) in PLOTTED:
            plotted[(q, e, label, name)] = rs
  writePlot(folder, plotted)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
