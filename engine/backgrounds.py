"""
a run's backgrounds for the browser viewer (web/): what is drawn behind its results - the flow of space (u arrows),
its acceleration (g arrows), a colour map (a wave's strain, say), lines (a seam) - as one small file,
<name>.backgrounds.json, named in each result's log (LOG_LINE + the file name). the viewer's Background menu lists
its backgrounds; picking one draws its layers and shows its description

backgrounds are pictures, not results: values are kept to 0.3% (16 bits: the sign and the log of the size, from
10^-20 to 10^20 of a scale), on grids
that are fine near the bodies and coarse far out, and a pattern that only moves - turns with two stars, grows or
shrinks with their orbit - is kept once, with the motion as a few numbers a frame. so a file is tens or hundreds of
kB, and covers the whole screen at any zoom

  bg = Backgrounds()
  b = bg.add(name, description)                    one background in the menu
  b.field(label, calc, grid, times=(0,), frame=None, steady=False)
                                                   u and g from calc.flow(pos, None, t) (g as the acceleration of
                                                   space, du/dt + (u . grad) u), sampled on grid at each of times
  b.scalar(label, field, grid, times=(0,), frame=None)
                                                   a colour map: field(X, Y, t) on arrays of points
  b.twist(label, field, grid, times=(0,), frame=None)
                                                   twist arcs: field(X, Y, t) a rate of turning (rad/s, positive
                                                   anticlockwise), drawn as an arc at each point
  b.lines(label, lines, times=(0,), frame=None)     lines(t): a list of (n, 2) arrays (a seam)
  b.linear(label, calc, centre, radius, times)     a flow straight in space about centre, u = M(t) (x - centre) (a
                                                   plane wave through the plane): two matrices a time
  bg.write(path)

grids (in the pattern's units - metres unless a frame scales them):
  polar(r0, r1, nr=160, nt=96)    nr rings spaced evenly in log r from r0 to r1, nt angles: fine near the centre,
                                  coarse far out
  box(x0, x1, y0, y1, nx, ny)     an even grid

a frame (Frame) moves a pattern: at time t its point p is at centre(t) + scale(t) R(angle(t)) p, its vectors turned by
angle(t) and multiplied by the quantity's own scale (u, a or s); sampled at times and interpolated linearly between.
a field sampled once with a frame is the same pattern at every moment, moved by the frame - right for a flow steady
in a turning frame (two stars on a circular orbit), and for an orbit that shrinks slowly, as the scales follow it

the file (version 1):
  {"kind": "backgrounds", "version": 1, "shared": [layer, ...], "backgrounds": [{"name", "description",
    "reference": {"u", "a", "s", "t"}, "layers": [layer or {"shared": k}, ...]}, ...]}
  field:  {"type": "field", "label", "grid", "components": ["u_x", "u_y", "a_x", "a_y"], ["s"] (a colour map) or ["t"]
           (twist arcs),
           "scale": {"u": ...}, "times": [...], "frame": frame or null, "data": base64 of little-endian int16,
           sign(v) (1 + round(800 (log10 |v/scale| + 20))) per component per point per time (0 for 0), -32768
           where there is no value}
  each background's "reference" is a fallback: the viewer scales arrows and colour maps from what is on screen
  lines:  {"type": "lines", "label", "times": [...], "frame", "lines": [[[x, y, x, y, ...], ...] per time]}
  linear: {"type": "linear", "label", "centre": [x, y], "radius", "times": [...], "u": [[mxx, mxy, myx, myy], ...],
           "a": [...]}
  frame:  {"times": [...], "x": [...], "y": [...], "angle": [...], "scale": [...], "u": [...], "a": [...], "s": [...]}
"""
import base64
import json
import math
import numpy as np
from engine.background_frames import flowAndChange

LOG_LINE = 'backgrounds:'   #the log line naming a run's backgrounds file
PER_DECADE = 800            #a value v (in its quantity's scale) is stored as its sign times 1 + PER_DECADE
DECADES = 20                #(log10 |v| + DECADES): to 0.3%, from 10^-20 to 10^20 of the scale; 0 is 0
NONE = -32768               #no value


def polar(r0, r1, nr=160, nt=96):
  return {'kind': 'polar', 'r0': float(r0), 'r1': float(r1), 'nr': int(nr), 'nt': int(nt)}


def box(x0, x1, y0, y1, nx=32, ny=32):
  return {'kind': 'box', 'x0': float(x0), 'x1': float(x1), 'y0': float(y0), 'y1': float(y1), 'nx': int(nx),
          'ny': int(ny)}


def points(grid):
  """the grid's points, (n, 2), in the order the data goes: polar ring by ring outwards, each from angle 0; box row by
  row from y0, each from x0"""
  if grid['kind'] == 'polar':
    rs = grid['r0']*(grid['r1']/grid['r0'])**(np.arange(grid['nr'])/(grid['nr'] - 1))
    ths = 2*math.pi*np.arange(grid['nt'])/grid['nt']
    R, T = np.meshgrid(rs, ths, indexing='ij')
    return np.column_stack([(R*np.cos(T)).ravel(), (R*np.sin(T)).ravel()])
  xs = np.linspace(grid['x0'], grid['x1'], grid['nx'])
  ys = np.linspace(grid['y0'], grid['y1'], grid['ny'])
  X, Y = np.meshgrid(xs, ys)
  return np.column_stack([X.ravel(), Y.ravel()])


class Frame:
  """
  how a pattern moves: at each of times, its centre, angle, scale and the scales of its quantities (u, a, s) - each
  a list as long as times, or one number for all of them
  """

  def __init__(self, times, x=0.0, y=0.0, angle=0.0, scale=1.0, u=1.0, a=1.0, s=1.0):
    self.times = np.asarray(times, dtype=float)
    n = self.times.size
    each = lambda v: np.full(n, float(v)) if np.isscalar(v) else np.asarray(v, dtype=float)
    self.values = {k: each(v) for k, v in (('x', x), ('y', y), ('angle', angle), ('scale', scale), ('u', u), ('a', a),
                                            ('s', s))}

  def at(self, t):
    """the frame's values at t (linear between its times; the first or last outside them)"""
    return {k: float(np.interp(t, self.times, v)) for k, v in self.values.items()}

  def toWorld(self, p, t):
    f = self.at(t)
    c, s = math.cos(f['angle']), math.sin(f['angle'])
    p = np.asarray(p, dtype=float)*f['scale']
    return np.column_stack([f['x'] + c*p[:, 0] - s*p[:, 1], f['y'] + s*p[:, 0] + c*p[:, 1]])

  def toPatternVectors(self, v, t, quantity):
    """world vectors v (n, 2) at t into the pattern's: turned back, divided by the quantity's scale"""
    f = self.at(t)
    c, s = math.cos(f['angle']), math.sin(f['angle'])
    return np.column_stack([c*v[:, 0] + s*v[:, 1], -s*v[:, 0] + c*v[:, 1]])/f[quantity]

  def json(self):
    out = {'times': [float('%.9g' % t) for t in self.times]}
    for k, v in self.values.items():
      out[k] = [float('%.7g' % x) for x in v]
    return out


def encode(values, scale):
  """values (any shape) as 16-bit integers: sign times 1 + PER_DECADE (log10 |value/scale| + DECADES), base64"""
  v = np.nan_to_num(values/scale, nan=0.0, posinf=0.0, neginf=0.0)
  with np.errstate(divide='ignore'):
    level = np.where(v != 0, 1 + np.round((np.log10(np.abs(v)) + DECADES)*PER_DECADE), 0)
  level = np.clip(level, 0, 32767)
  q = np.where(np.isfinite(values), np.sign(v)*level, NONE).astype('<i2')
  return base64.b64encode(q.tobytes()).decode('ascii')


def percentile(sizes, p):
  sizes = sizes[np.isfinite(sizes) & (sizes > 0)]
  return float(np.percentile(sizes, p)) if sizes.size else None


class Background:

  def __init__(self, name, description):
    self.name, self.description = name, description
    self.layers = []
    self.sizes = {'u': [], 'a': [], 's': [], 't': []}       #for the background's reference scales

  def field(self, label, calc, grid, times=(0.0,), frame=None, steady=False):
    """u and g from calc on grid at each of times (see the module notes); steady: no du/dt (bodies at rest)"""
    pts = points(grid)
    times = [float(t) for t in times]
    flow = lambda q, t: calc.flow(q, None, t)
    warn = getattr(calc, 'warn', None)
    calc.warn = lambda message: None
    us, accs = [], []
    try:
      for t in times:
        world = frame.toWorld(pts, t) if frame else pts
        centre = np.array([frame.at(t)['x'], frame.at(t)['y']]) if frame else np.zeros(2)
        spacing = (times[-1] - times[0])/max(1, len(times) - 1) if len(times) > 1 else 1.0
        if frame is not None and len(frame.times) > 1:
          spacing = min(spacing, float(np.min(np.diff(frame.times))))
        #the differences in space a small part of the way from the centre: the polar grid's inner rings are close in
        rows = [flowAndChange(flow, pos, t, 1e-5*max(np.hypot(*(pos - centre)), 1e-30), steady, 1e-3*spacing)
                for pos in world]
        u = np.array([r[0] for r in rows], dtype=float)
        a = np.array([r[1] for r in rows], dtype=float)
        if frame:
          u, a = frame.toPatternVectors(u, t, 'u'), frame.toPatternVectors(a, t, 'a')
        us.append(u)
        accs.append(a)
    finally:
      calc.warn = warn
    u, a = np.array(us), np.array(accs)          #(times, points, 2)
    scale = {'u': percentile(np.hypot(u[..., 0], u[..., 1]).ravel(), 90) or 1.0,
             'a': percentile(np.hypot(a[..., 0], a[..., 1]).ravel(), 90) or 1.0}
    self.sizes['u'].append(self.worldSizes(u, frame, times, 'u'))
    self.sizes['a'].append(self.worldSizes(a, frame, times, 'a'))
    data = np.concatenate([u/scale['u'], a/scale['a']], axis=-1)   #(times, points, 4)
    self.layers.append({'type': 'field', 'label': label, 'grid': grid, 'components': ['u_x', 'u_y', 'a_x', 'a_y'],
                        'scale': scale, 'times': times, 'frame': frame.json() if frame else None,
                        'data': encode(data, 1.0)})
    return self

  def scalar(self, label, field, grid, times=(0.0,), frame=None):
    """a colour map: field(X, Y, t) at the grid's points (in the world) at each of times"""
    pts = points(grid)
    times = [float(t) for t in times]
    values = []
    for t in times:
      world = frame.toWorld(pts, t) if frame else pts
      v = np.asarray(field(world[:, 0], world[:, 1], t), dtype=float)
      values.append(v/(frame.at(t)['s'] if frame else 1.0))
    values = np.array(values)[..., None]
    scale = percentile(np.abs(values).ravel(), 98) or 1.0
    self.sizes['s'].append(self.worldSizes(np.abs(values[..., 0]), frame, times, 's'))
    self.layers.append({'type': 'field', 'label': label, 'grid': grid, 'components': ['s'], 'scale': {'s': scale},
                        'times': times, 'frame': frame.json() if frame else None,
                        'data': encode(values/scale, 1.0)})
    return self

  def twist(self, label, field, grid, times=(0.0,), frame=None):
    """
    twist arcs: field(X, Y, t) a rate of turning about the axis out of the plane (rad/s, positive anticlockwise) at the
    grid's points - a spinning hole's twist, say - drawn as an arc at each point turning that way, its sweep the rate
    """
    pts = points(grid)
    times = [float(t) for t in times]
    values = []
    for t in times:
      world = frame.toWorld(pts, t) if frame else pts
      values.append(np.asarray(field(world[:, 0], world[:, 1], t), dtype=float))
    values = np.array(values)[..., None]
    scale = percentile(np.abs(values[np.isfinite(values)]).ravel(), 90) or 1.0
    self.sizes['t'].append(np.abs(values[..., 0]).ravel())
    self.layers.append({'type': 'field', 'label': label, 'grid': grid, 'components': ['t'], 'scale': {'t': scale},
                        'times': times, 'frame': frame.json() if frame else None,
                        'data': encode(values/scale, 1.0)})
    return self

  def lines(self, label, lines, times=(0.0,), frame=None):
    """lines(t): a list of (n, 2) arrays - in the pattern's units if there is a frame, else the world's"""
    out = []
    for t in times:
      out.append([[float('%.5g' % v) for v in np.asarray(l, dtype=float).ravel()] for l in lines(t)])
    self.layers.append({'type': 'lines', 'label': label, 'times': [float(t) for t in times],
                        'frame': frame.json() if frame else None, 'lines': out})
    return self

  def linear(self, label, calc, centre, radius, times):
    """
    a flow straight in space about centre (a plane wave through the plane, engine/waves.py), u = M(t) (x - centre),
    its acceleration too: each matrix from the flow a little way along x and y, at each of times; drawn within radius
    of centre (None: everywhere)
    """
    centre = np.asarray(centre, dtype=float)
    L = 1e-3*(radius or 1.0)
    flow = lambda q, t: calc.flow(q, None, t)
    spacing = (times[-1] - times[0])/max(1, len(times) - 1) if len(times) > 1 else 1.0
    steady = len(times) == 1
    Mu, Ma = [], []
    for t in times:
        cols = [flowAndChange(flow, centre + L*e, t, 1e-3*L, steady, 1e-3*spacing) for e in (np.array([1.0, 0.0]), np.array([0.0, 1.0]))]
        Mu.append([cols[0][0][0]/L, cols[1][0][0]/L, cols[0][0][1]/L, cols[1][0][1]/L])
        Ma.append([cols[0][1][0]/L, cols[1][1][0]/L, cols[0][1][1]/L, cols[1][1][1]/L])
    Mu, Ma = np.array(Mu), np.array(Ma)
    reach = radius or 1.0
    self.sizes['u'].append(np.abs(Mu).max(axis=1)*reach)
    self.sizes['a'].append(np.abs(Ma).max(axis=1)*reach)
    sig = lambda m: [[float('%.4g' % v) for v in row] for row in m]
    self.layers.append({'type': 'linear', 'label': label, 'centre': [float(c) for c in centre],
                        'radius': None if radius is None else float(radius), 'times': [float(t) for t in times],
                        'u': sig(Mu), 'a': sig(Ma)})
    return self

  def share(self, other, k=0):
    """use another background's k-th layer here too (the same colour map behind several): kept once in the file"""
    self.layers.append(other.layers[k])
    for q in self.sizes:
      self.sizes[q] += other.sizes[q]
    return self

  @staticmethod
  def worldSizes(values, frame, times, quantity):
    """the sizes of a layer's values in the world (its frame's scales put back), for the reference scales"""
    sizes = np.hypot(values[..., 0], values[..., 1]) if values.ndim == 3 else np.abs(values)
    if frame:
      sizes = sizes*np.array([frame.at(t)[quantity] for t in times])[:, None]
    return sizes.ravel()

  def json(self):
    reference = {}
    for q, p in (('u', 90), ('a', 90), ('s', 98), ('t', 90)):
      if self.sizes[q]:
        reference[q] = percentile(np.concatenate(self.sizes[q]), p)
    return {'name': self.name, 'description': self.description, 'reference': reference, 'layers': self.layers}


class Backgrounds:

  def __init__(self):
    self.items = []

  def add(self, name, description):
    b = Background(name, description)
    self.items.append(b)
    return b

  def write(self, path):
    """the file; a layer in more than one background (Background.share) is kept once, in "shared", and named there
    by its index ({"shared": k})"""
    shared, seen = [], {}
    for b in self.items:
      for layer in b.layers:
        if sum(layer is l for c in self.items for l in c.layers) > 1 and id(layer) not in seen:
          seen[id(layer)] = len(shared)
          shared.append(layer)
    backgrounds = []
    for b in self.items:
      out = b.json()
      out['layers'] = [{'shared': seen[id(l)]} if id(l) in seen else l for l in b.layers]
      backgrounds.append(out)
    with open(path, 'w') as f:
      json.dump({'kind': 'backgrounds', 'version': 1, 'shared': shared, 'backgrounds': backgrounds}, f,
                separators=(',', ':'))


def seamAround(region, centre, r0, r1, cells=(200, 128)):
  """
  a flow's seam (where region(pos) changes, engine/background_frames.py seamLines) traced in log distance and angle
  round centre, from r0 to r1: as fine near the centre as far out. returns lines in metres
  """
  from engine.background_frames import seamLines
  centre = np.asarray(centre, dtype=float)
  at = lambda q: region(centre + math.exp(q[0])*np.array([math.cos(q[1]), math.sin(q[1])]))
  lines = seamLines(at, (math.log(r0), math.log(r1), 0.0, 2*math.pi), cells)
  return [centre + np.exp(l[:, :1])*np.column_stack([np.cos(l[:, 1]), np.sin(l[:, 1])]) for l in lines]


SEAM = "the seam, where the bodies' regions of flow meet"


def describeFlow(calc):
  """a sentence on what a calculator's steady flow is, for a background's description"""
  bodies = getattr(calc, 'bodies', None) or []
  if not bodies:
    return 'The flow of space u and its acceleration g.'
  mass = lambda m: '%.3g solar mass%s' % (m, '' if '%.3g' % m == '1' else 'es')
  names = ', '.join('%s at (%.3g, %.3g) m' % (mass(b.mass/1.989e30), b.x, b.y) for b in bodies)
  direction = getattr(calc, 'direction', None)
  how = {'eikonal-exact': ' Space flows down zero-energy paths out of each body (the eikonal flow, exact for two'
                          ' bodies), so each body has a region of its own; the regions meet at a seam.',
         'eikonal': ' Space flows down zero-energy paths out of each body (the eikonal flow), so each body has a region'
                    ' of its own; the regions meet at a seam.',
         'g': ' The flow points along g, its speed sqrt(sum of 2GM/d).'}.get(direction, '')
  if getattr(calc, 'combine', None) == 'vectors':
    how = ' Each body\'s own flow, straight in at sqrt(2GM/d), is added to the others\' as vectors.'
  if len(bodies) == 1:
    how = ' Space flows straight in at sqrt(2GM/r).'
  return ('The flow of space u (grey arrows) and its acceleration g (dark arrows) round %d bod%s: %s.%s'
          % (len(bodies), 'y' if len(bodies) == 1 else 'ies', names, how))


def steadyBackground(bg, calc, box, name, description=None):
  """
  a steady flow's background (bodies at rest), for writeViewerFiles and the converter: u and g on a polar grid round
  the body (or the middle of box, for more than one) from a thousandth of box's size to a thousand times it - the
  whole screen at any zoom - and its seam if it has one; a flow with no bodies (a shear) on even grids round box
  """
  x0, x1, y0, y1 = box
  size = max(x1 - x0, y1 - y0)
  middle = np.array([(x0 + x1)/2, (y0 + y1)/2])
  b = bg.add(name, description or describeFlow(calc))
  bodies = getattr(calc, 'bodies', None) or []
  if not bodies:
    #no bodies (a shear, say): an even grid over the paths, and a coarser one twenty times as wide
    for k, cells in ((0.6, 64), (20.0, 64)):
      b.field('the flow', calc, box_(middle[0] - k*size, middle[0] + k*size, middle[1] - k*size, middle[1] + k*size,
                                     cells, cells), [0.0], steady=True)
    return b
  centre = bodies[0].pos if len(bodies) == 1 else middle
  r0, r1 = 1e-3*size, 1e3*size
  b.field('the flow', calc, polar(r0, r1), [0.0], Frame([0.0], x=centre[0], y=centre[1]), steady=True)
  region = getattr(calc, 'region', None)
  if region is not None and region(centre + np.array([r1/2, 0.0])) is not None:
    lines = seamAround(region, centre, r0, r1)
    if lines:
      b.lines(SEAM, lambda t: lines)
  return b


box_ = box   #for functions with a box argument of their own
