"""
background frames: the flow of space u and its acceleration on a grid, at a run of times - for a flow that changes
with time (a gravitational wave, engine/waves.py), so the viewer can draw its backgrounds as they were at each moment
of a replay

the acceleration is that of space moving with the flow, du/dt + (u . grad) u (by centred differences): for a steady
flow with no curl it is g, and in a wave it is the tidal acceleration of space

  writeFrames(path, calc, (x0, x1, y0, y1), times)   a csv: t, x, y, u_x, u_y, a_x, a_y - one row per grid point,
                                                     a frame per time
  frames = readFrames(path)                          the viewer's side
  frame = frames.at(t)                               between the two frames either side of t (linear in time)
  frame.flow(pos), frame.gravity(pos)                at pos (bilinear in space; nan outside the grid)
  frame.speed(x, y)                                  |u| on arrays of points, for lines of equal |u|
  frames.reference('u'), frames.speedRange()         scales for the whole run, so arrows and lines of equal |u| grow
                                                     and shrink from frame to frame instead of each filling its own

a study writes its frames with writeFrames and names the file in its log (LOG_LINE + the file name, next to the log),
which is how the viewer finds it. (the browser viewer draws a run's backgrounds from a backgrounds file instead,
engine/backgrounds.py, when it has one; these frames are for the desktop viewer.)

a steady flow (round fixed bodies) is one frame, at t = 0: staticFrame writes it on a grid over its results' paths
(boxAround), for a viewer that cannot work the flow out itself (the browser viewer, web/); the desktop viewer works a
steady flow out exactly instead
"""
import csv
import numpy as np

LOG_LINE = 'background frames:'   #the log line naming a run's frames file


def writeFrames(path, calc, box, times, cells=32, digits=8):
  """
  the frames of calc's flow (calc.flow(pos, None, t)) on a cells x cells grid (or cells = (nx, ny)) over box
  (x0, x1, y0, y1, m), at each of times (s), into the csv at path; u and a to digits significant figures
  """
  x0, x1, y0, y1 = box
  nx, ny = cells if isinstance(cells, tuple) else (cells, cells)
  xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
  h = 1e-4*max(x1 - x0, y1 - y0)                       #for the differences in space
  steady = len(times) == 1                             #one frame: the flow does not change with time
  spacing = (times[-1] - times[0])/max(1, len(times) - 1) if len(times) > 1 else 1.0
  dt = 1e-3*spacing                                    #for the differences in time
  warn = getattr(calc, 'warn', None)
  calc.warn = lambda message: None   #a grid point where g = 0 just has no flow
  try:
    writeRows(path, calc, xs, ys, times, h, steady, dt, digits)
  finally:
    calc.warn = warn


def writeRows(path, calc, xs, ys, times, h, steady, dt, digits=8):
  """writeFrames' rows"""
  with open(path, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'x', 'y', 'u_x', 'u_y', 'a_x', 'a_y'])
    for t in times:
      for y in ys:
        for x in xs:
          u, change = flowAndChange(lambda q, s: calc.flow(q, None, s), np.array([x, y]), t, h, steady, dt)
          out.writerow(['%.10g' % t, '%.10g' % x, '%.10g' % y] + ['%.*g' % (digits, v) for v in (*u, *change)])


def flowAndChange(flow, pos, t, h, steady, dt):
  """
  u = flow(pos, t) and the acceleration of space moving with it, du/dt + (u . grad) u, by centred differences (h in
  space, dt in time; no du/dt if steady); both nan where there is no value (on a body)
  """
  try:
    u = flow(pos, t)
    change = np.zeros(2) if steady else (flow(pos, t + dt) - flow(pos, t - dt))/(2*dt)
    size = float(np.hypot(u[0], u[1]))
    if size > 0:
      along = u/size
      change = change + size*(flow(pos + h*along, t) - flow(pos - h*along, t))/(2*h)
    return u, change
  except (ZeroDivisionError, ValueError, FloatingPointError):
    return np.array([np.nan, np.nan]), np.array([np.nan, np.nan])


def seamLines(region, box, cells=160, halvings=30):
  """
  the seam of a flow with regions (each body's own, engine/eikonal.py): where region(pos) - an index, or None where
  there is no flow - changes, over box (x0, x1, y0, y1) on a cells x cells grid (or (nx, ny)). each crossing of a grid
  edge is found by halving along it; within a cell they are joined in pairs (two crossings: one piece; four: the two
  nearest each other's edges), and the pieces into lines. returns a list of lines, each an (n, 2) array (m)
  """
  x0, x1, y0, y1 = box
  nx, ny = cells if isinstance(cells, tuple) else (cells, cells)
  xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
  labels = [[region(np.array([x, y])) for x in xs] for y in ys]
  crossings = {}

  def crossing(i0, j0, i1, j1):
    """where the region changes along the grid edge from (i0, j0) to (i1, j1), or None"""
    key = (i0, j0, i1, j1)
    if key not in crossings:
      a, b = labels[j0][i0], labels[j1][i1]
      if a == b or a is None or b is None:
        crossings[key] = None
      else:
        p, q = np.array([xs[i0], ys[j0]]), np.array([xs[i1], ys[j1]])
        for _ in range(halvings):
          mid = (p + q)/2
          if region(mid) == a:
            p = mid
          else:
            q = mid
        crossings[key] = (key, (p + q)/2)
    return crossings[key]

  pieces = []
  for j in range(ny - 1):
    for i in range(nx - 1):
      edges = [crossing(i, j, i + 1, j), crossing(i + 1, j, i + 1, j + 1),
               crossing(i, j + 1, i + 1, j + 1), crossing(i, j, i, j + 1)]
      found = [e for e in edges if e is not None]
      if len(found) == 2:
        pieces.append(tuple(found))
      elif len(found) == 4:     #a saddle, or three regions: the nearest crossings together
        a, b, c, d = found
        if np.hypot(*(a[1] - b[1])) + np.hypot(*(c[1] - d[1])) <= np.hypot(*(a[1] - d[1])) + np.hypot(*(b[1] - c[1])):
          pieces += [(a, b), (c, d)]
        else:
          pieces += [(a, d), (b, c)]
  #join the pieces at the grid edges they share
  ends = {}
  for n, (a, b) in enumerate(pieces):
    ends.setdefault(a[0], []).append(n)
    ends.setdefault(b[0], []).append(n)
  used, lines = set(), []
  for n in range(len(pieces)):
    if n in used:
      continue
    used.add(n)
    line = [pieces[n][0], pieces[n][1]]
    for forward in (True, False):
      while True:
        end = line[-1] if forward else line[0]
        nexts = [m for m in ends.get(end[0], []) if m not in used]
        if not nexts:
          break
        m = nexts[0]
        used.add(m)
        a, b = pieces[m]
        step = b if a[0] == end[0] else a
        if forward:
          line.append(step)
        else:
          line.insert(0, step)
    lines.append(np.array([point for _, point in line]))
  return lines


def writeScalarFrames(path, field, box, times, cells=64):
  """
  a scalar field (a wave's strain, say) at a run of times: a csv of t, x, y, s - field(xs, ys, t) gives s on the
  grid (arrays, (ny, nx)), nan where it has no value. the browser viewer draws it as a colour map; name the file in a
  log with LOG_LINE as for frames, and what s is with SCALAR_LINE
  """
  x0, x1, y0, y1 = box
  nx, ny = cells if isinstance(cells, tuple) else (cells, cells)
  xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
  X, Y = np.meshgrid(xs, ys)
  with open(path, 'w', newline='') as f:
    f.write('t,x,y,s\n')
    for t in times:
      values = field(X, Y, t)
      f.write(''.join('%.7g,%.6g,%.6g,%s\n' % (t, x, y, ('%.4g' % v) if np.isfinite(v) else 'nan')
                      for x, y, v in zip(X.ravel(), Y.ravel(), np.asarray(values).ravel())))


SCALAR_LINE = 'background scalar:'   #the log line saying what a scalar frames file's s is


def boxAround(csvPaths, margin=0.1):
  """(x0, x1, y0, y1): the pos_x / pos_y of the csvs' rows, with margin of the larger side added all round"""
  xs, ys = [], []
  for path in csvPaths:
    with open(path, newline='') as f:
      for row in csv.DictReader(f):
        try:
          xs.append(float(row['pos_x']))
          ys.append(float(row['pos_y']))
        except (KeyError, TypeError, ValueError):   #an empty row between paths
          pass
  x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
  pad = margin*max(x1 - x0, y1 - y0, 1.0)
  return x0 - pad, x1 + pad, y0 - pad, y1 + pad


def staticFrame(path, calc, box, longest=64):
  """a steady flow's one frame, at t = 0, over box: longest points along its longer side, the same spacing across"""
  x0, x1, y0, y1 = box
  across = max(x1 - x0, y1 - y0)
  nx = max(8, round(longest*(x1 - x0)/across))
  ny = max(8, round(longest*(y1 - y0)/across))
  writeFrames(path, calc, box, [0.0], (nx, ny))


class Frame:
  """one moment's flow and acceleration on the grid: (ny, nx, 2) arrays over xs, ys"""

  def __init__(self, xs, ys, u, a, t):
    self.xs, self.ys, self.u, self.a, self.t = xs, ys, u, a, t

  def sample(self, field, x, y):
    """field bilinearly at the points (x, y) (arrays or numbers); nan outside the grid"""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    fx = np.interp(x, self.xs, np.arange(self.xs.size), left=np.nan, right=np.nan)
    fy = np.interp(y, self.ys, np.arange(self.ys.size), left=np.nan, right=np.nan)
    inside = np.isfinite(fx) & np.isfinite(fy)
    fx, fy = np.where(inside, fx, 0.0), np.where(inside, fy, 0.0)
    i0 = np.minimum(fx.astype(int), self.xs.size - 2)
    j0 = np.minimum(fy.astype(int), self.ys.size - 2)
    sx, sy = (fx - i0)[..., None], (fy - j0)[..., None]
    value = ((1 - sx)*(1 - sy)*field[j0, i0] + sx*(1 - sy)*field[j0, i0 + 1]
             + (1 - sx)*sy*field[j0 + 1, i0] + sx*sy*field[j0 + 1, i0 + 1])
    return np.where(inside[..., None], value, np.nan)

  def flow(self, pos, region=None):
    return self.sample(self.u, pos[0], pos[1])

  def gravity(self, pos):
    return self.sample(self.a, pos[0], pos[1])

  def speed(self, x, y):
    u = self.sample(self.u, x, y)
    return np.hypot(u[..., 0], u[..., 1])


class Frames:
  """a run's frames: times (nt), xs (nx), ys (ny), u and a (nt, ny, nx, 2)"""

  def __init__(self, times, xs, ys, u, a):
    self.times, self.xs, self.ys, self.u, self.a = times, xs, ys, u, a
    self.scales = {}

  def sizes(self, field):
    """the sizes of field ('u' or 'a') at every grid point of every frame, leaving out zeros (before a wave arrives)"""
    size = np.hypot(*np.moveaxis(self.u if field == 'u' else self.a, -1, 0)).ravel()
    return size[np.isfinite(size) & (size > 0)]

  def reference(self, field):
    """the 90th percentile of field's size over the whole run: what a full-length arrow stands for in every frame"""
    if field not in self.scales:
      size = self.sizes(field)
      self.scales[field] = float(np.percentile(size, 90)) if size.size else None
    return self.scales[field]

  def speedRange(self):
    """|u| from its 2nd to its 98th percentile over the whole run, for the levels of the lines of equal |u|"""
    if 'range' not in self.scales:
      size = self.sizes('u')
      self.scales['range'] = (float(np.percentile(size, 2)), float(np.percentile(size, 98))) if size.size else None
    return self.scales['range']

  def at(self, t):
    """the frame at time t: between the frames either side (linear in time), the first or last outside them"""
    k = int(np.clip(np.searchsorted(self.times, t, side='right') - 1, 0, self.times.size - 1))
    if k + 1 < self.times.size and t > self.times[k]:
      f = (t - self.times[k])/(self.times[k + 1] - self.times[k])
      return Frame(self.xs, self.ys, (1 - f)*self.u[k] + f*self.u[k + 1], (1 - f)*self.a[k] + f*self.a[k + 1], t)
    return Frame(self.xs, self.ys, self.u[k], self.a[k], float(self.times[k]))


def isSteady(path):
  """whether the frames file at path is one steady frame (its first and last rows at the same time)"""
  with open(path) as f:
    f.readline()
    first = f.readline()
    f.seek(0, 2)
    f.seek(max(0, f.tell() - 4096))
    last = [l for l in f.read().splitlines() if l.strip()][-1]
  return first.split(',')[0] == last.split(',')[0]


def readFrames(path):
  """the Frames in the csv at path (written by writeFrames)"""
  data = np.loadtxt(path, delimiter=',', skiprows=1, ndmin=2)
  if data.shape[1] == 4:          #a scalar field's frames: no flow here (the desktop viewer draws no colour maps)
    data = np.hstack([data[:, :3], np.zeros((data.shape[0], 4))])
  times = np.unique(data[:, 0])
  xs, ys = np.unique(data[:, 1]), np.unique(data[:, 2])
  shape = (times.size, ys.size, xs.size, 2)
  return Frames(times, xs, ys, data[:, 3:5].reshape(shape), data[:, 5:7].reshape(shape))
