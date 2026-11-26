"""
is the seam always in the same place? the potential flow's seam is built from one family of free-fall paths: those
starting from rest far away in every direction, in the frame where the bodies are at rest. its time T = t + S/c^2 is
one way of slicing GR's spacetime. two other frames:

  carried    the same two bodies moving together at V, with their space carried along (Part 3's rule): a Galilean
             change of frame of everything - the flow is u + V, and the seam moves with the bodies, unchanged
  stream     the same two bodies moving at V through space at rest far away: in the bodies' frame, space streams past
             at -V far upstream. the flow (no swirl, keeping Bernoulli's equation) is then the free-fall paths that
             arrive from one direction with speed V far away, |w|^2 = 2U + V^2, and its potential phi (w = grad phi)
             is integrated along each path, d phi = |w|^2 dt. where paths cross, the flow takes the one with the
             largest phi (as the rest frame's takes the smallest S), and the seam is where that choice changes from
             one family of paths to another

the stream paths are traced (Newton, RK4, steps set by the distance to the nearer body), and binned on a grid: each
cell keeps the largest phi among the paths through it, and which family that path belongs to - which side of each
body it passed. seams are the edges between families. V = 0 is the limit: paths of zero energy, arriving parallel
from one direction (parabolas round a single body). writes each case's seam as a viewer file, with the paths

run: python3 studies/seam_frames.py     (a few minutes; prints, and writes logs/modelChecks/seamFrames_<datetime>/)
"""
import math
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.flow import Body, SpecialFlowCalculator
from engine.logger import LOG_DIR
from engine.constants import MS, G

D = 2e8
GM = G*MS
BOX = 3.0*D
CELLS = 120
RAYS = 16000


def trace(bodies, V, direction, start=40.0, spread=3.5):
  """free-fall paths arriving from far along -direction... i.e. moving along direction, speed V far away; their
  places, phi, and each one's family (the side it passed each body on, or the body it fell into)"""
  d = np.array(direction, dtype=float)/np.linalg.norm(direction)
  side = np.array([-d[1], d[0]])
  pos = np.array([b.pos for b in bodies])
  gms = np.array([b.GM for b in bodies])
  b = np.linspace(-spread*D, spread*D, RAYS)
  x = -start*D*d[None, :] + b[:, None]*side[None, :]
  U = sum(g/np.linalg.norm(x - p, axis=1) for g, p in zip(gms, pos))
  speed = np.sqrt(V*V + 2*U)
  v = speed[:, None]*d[None, :]
  phi = np.zeros(RAYS)
  passed = np.zeros((RAYS, len(bodies)))              #which side of each body: +1/-1, 0 not yet
  alive = np.ones(RAYS, bool)
  samples = []
  def acc(x):
    a = np.zeros_like(x)
    for g, p in zip(gms, pos):
      r = x - p
      a -= g*r/np.linalg.norm(r, axis=1)[:, None]**3
    return a
  for step in range(200000):
    if not alive.any():
      break
    rmin = np.min([np.linalg.norm(x - p, axis=1) for p in pos], axis=0)
    sp = np.linalg.norm(v, axis=1)
    dt = np.minimum(0.02*rmin/sp, 0.02*np.sqrt(rmin**3/GM))
    dt = np.where(alive, dt, 0.0)
    k1x, k1v = v, acc(x)
    k2x, k2v = v + 0.5*dt[:, None]*k1v, acc(x + 0.5*dt[:, None]*k1x)
    k3x, k3v = v + 0.5*dt[:, None]*k2v, acc(x + 0.5*dt[:, None]*k2x)
    k4x, k4v = v + dt[:, None]*k3v, acc(x + dt[:, None]*k3x)
    xn = x + dt[:, None]/6*(k1x + 2*k2x + 2*k3x + k4x)
    vn = v + dt[:, None]/6*(k1v + 2*k2v + 2*k3v + k4v)
    phi += dt*0.5*(np.sum(v*v, 1) + np.sum(vn*vn, 1))
    for k, p in enumerate(pos):          #the side passed: the sign across the stream as the path goes by the body
      before, after = (x - p) @ d, (xn - p) @ d
      crossing = alive & (before < 0) & (after >= 0) & (passed[:, k] == 0)
      passed[crossing, k] = np.sign((xn[crossing] - p) @ side)
    x, v = xn, vn
    captured = rmin < 1e-4*D
    passed[captured & alive, :] = 9 + np.argmin([np.linalg.norm(x[captured & alive] - p, axis=1) for p in pos], axis=0)[:, None] if (captured & alive).any() else passed[captured & alive, :]
    alive &= ~captured & ((x @ d) < start*D) & (np.abs(x @ side) < 2*spread*D)
    if step % 4 == 0:
      inbox = alive & (np.abs(x[:, 0]) < BOX) & (np.abs(x[:, 1]) < BOX)
      samples.append((x[inbox].copy(), phi[inbox].copy(), np.nonzero(inbox)[0]))
  #each path's family: where it finally went - the side it passed each body on, or the body it fell into
  return [(x_, ph, passed[idx]) for x_, ph, idx in samples]


def families(samples, bodies):
  """the grid: in each cell, the largest phi and its path's family; and the seam: cells next to another family"""
  X = np.concatenate([x for x, _, _ in samples])
  P = np.concatenate([ph for _, ph, _ in samples])
  F = np.concatenate([pa for _, _, pa in samples])
  _, key = np.unique(F, axis=0, return_inverse=True)
  key = key.ravel()
  i = ((X[:, 0] + BOX)/(2*BOX)*CELLS).astype(int)
  j = ((X[:, 1] + BOX)/(2*BOX)*CELLS).astype(int)
  ok = (i >= 0) & (i < CELLS) & (j >= 0) & (j < CELLS)
  cell, P, key = (i*CELLS + j)[ok], P[ok], key[ok]
  order = np.lexsort((-P, cell))                      #by cell, the largest phi first
  first = np.ones(len(order), bool)
  first[1:] = cell[order][1:] != cell[order][:-1]
  fam = np.full(CELLS*CELLS, -1, dtype=int)
  fam[cell[order][first]] = key[order][first]
  fam = fam.reshape(CELLS, CELLS)
  seam = []
  for ii in range(CELLS - 1):
    for jj in range(CELLS - 1):
      f = fam[ii, jj]
      if f < 0:
        continue
      for a_, b_ in ((ii + 1, jj), (ii, jj + 1)):
        if fam[a_, b_] >= 0 and fam[a_, b_] != f:
          seam.append(((ii + 0.5 + 0.5*(a_ - ii))/CELLS*2*BOX - BOX, (jj + 0.5 + 0.5*(b_ - jj))/CELLS*2*BOX - BOX))
  return fam, np.array(seam), (fam < 0).mean()


def restSeam(bodies):
  """the rest frame's seam (engine/two_centre.py): the cells where the region changes, on the same grid"""
  calc = SpecialFlowCalculator(bodies, 2)
  field = calc.rayField()
  pts = []
  xs = (np.arange(CELLS) + 0.5)/CELLS*2*BOX - BOX
  reg = np.array([[field.region(np.array([x, y])) for y in xs] for x in xs])
  for ii in range(CELLS - 1):
    for jj in range(CELLS - 1):
      if reg[ii + 1, jj] != reg[ii, jj] or reg[ii, jj + 1] != reg[ii, jj]:
        pts.append((xs[ii], xs[jj]))
  return np.array(pts)


def write(folder, name, rows, note):
  path = os.path.join(folder, name + '.csv')
  with open(path, 'w') as f:
    f.write('pos_x,pos_y\n')
    for x, y in rows:
      f.write('%.6g,%.6g\n' % (x, y))
  with open(path[:-4] + '.log', 'w') as f:
    f.write(note + '\n')
  return path


def describe(seam, bodies, label):
  """where the seam is: how much of it lies on the line through the bodies, behind them (downstream), and between"""
  if not len(seam):
    return '  %s: no seam' % label
  near = np.abs(seam[:, 1]) < 2*BOX/CELLS
  between = near & (np.abs(seam[:, 0]) < D/2)
  return ('  %s: %d seam cells; on the line through the bodies %d (between them %d); x from %.2f to %.2f D,'
          ' y from %.2f to %.2f D' % (label, len(seam), near.sum(), between.sum(), seam[:, 0].min()/D,
                                     seam[:, 0].max()/D, seam[:, 1].min()/D, seam[:, 1].max()/D))


def main():
  sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  from two_body_escapes import writeViewerFiles
  folder = os.path.join(LOG_DIR, 'modelChecks', 'seamFrames_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
  os.makedirs(folder, exist_ok=True)
  two = [Body(MS, -D/2, 0.0), Body(MS, D/2, 0.0)]
  one = [Body(MS, 0.0, 0.0)]
  saddleSpeed = math.sqrt(4*GM/(D/2))
  lines = ['where the seam is, for different families of free-fall observers (two solar masses %.0e m apart; the flow at'
           ' the rest frame\'s saddle %.2e m/s). the grid: %d x %d cells over %.1f D square' % (D, saddleSpeed, CELLS,
                                                                                         CELLS, 2*BOX/D)]
  rest = restSeam(two)
  lines.append(describe(rest, two, 'rest frame (the engine\'s seam), two bodies'))
  made = [(write(folder, 'rest frame', rest, 'the potential flow\'s seam, the bodies at rest'), '#7a7a74', 'solid')]
  colours = ['#2a78d6', '#eb6834', '#1baf7a', '#d6a21e', '#8a5cd8', '#d64c7a']
  cases = [('one body, space streaming past it, V = 0 (parabolic paths)', one, 0.0, (-1, 0)),
           ('one body, V = 0.5 of the saddle flow', one, 0.5*saddleSpeed, (-1, 0)),
           ('two bodies moving along the line joining them, V = 0', two, 0.0, (-1, 0)),
           ('two bodies moving along the line joining them, V = 0.5 of the saddle flow', two, 0.5*saddleSpeed, (-1, 0)),
           ('two bodies moving across the line joining them, V = 0', two, 0.0, (0, -1)),
           ('two bodies moving across the line joining them, V = 0.5 of the saddle flow', two, 0.5*saddleSpeed, (0, -1))]
  for (label, bodies, V, d), colour in zip(cases, colours):
    samples = trace(bodies, V, d)
    fam, seam, empty = families(samples, bodies)
    lines.append(describe(seam, bodies, label) + '; %.1f%% of cells reached by no path' % (100*empty))
    print(lines[-1], flush=True)
    made.append((write(folder, label.replace(',', '').replace('=', ''), seam,
                       'the seam of the free-fall paths streaming past (%s), space moving at %.3e m/s far away, along'
                       ' (%g, %g)' % (label, V, d[0], d[1])), colour, 'solid'))
  writeViewerFiles(folder, 'seam_frames', made, preferences={'equalAspect': True, 'showFlow': False,
                                                            'showPathLegend': True, 'unit': 2})
  lines.append('carried: the two bodies and their space moving together at any V is a change of frame of the whole flow'
               ' (u + V); the seam goes with them, unchanged - nothing to compute')
  print('\n'.join(lines), flush=True)
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines) + '\n')
  print('written to', folder)


if __name__ == '__main__':
  main()
