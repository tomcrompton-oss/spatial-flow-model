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
which is how the viewer finds it
"""
import csv
import numpy as np

LOG_LINE = 'background frames:'   #the log line naming a run's frames file


def writeFrames(path, calc, box, times, cells=32):
  """
  the frames of calc's flow (calc.flow(pos, None, t)) on a cells x cells grid (or cells = (nx, ny)) over box
  (x0, x1, y0, y1, m), at each of times (s), into the csv at path
  """
  x0, x1, y0, y1 = box
  nx, ny = cells if isinstance(cells, tuple) else (cells, cells)
  xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
  h = 1e-4*max(x1 - x0, y1 - y0)                       #for the differences in space
  spacing = (times[-1] - times[0])/max(1, len(times) - 1) if len(times) > 1 else 1.0
  dt = 1e-3*spacing                                    #and in time
  with open(path, 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['t', 'x', 'y', 'u_x', 'u_y', 'a_x', 'a_y'])
    for t in times:
      for y in ys:
        for x in xs:
          pos = np.array([x, y])
          u = calc.flow(pos, None, t)
          change = (calc.flow(pos, None, t + dt) - calc.flow(pos, None, t - dt))/(2*dt)
          size = float(np.hypot(u[0], u[1]))
          if size > 0:
            along = u/size
            change = change + size*(calc.flow(pos + h*along, None, t) - calc.flow(pos - h*along, None, t))/(2*h)
          out.writerow(['%.10g' % t, '%.10g' % x, '%.10g' % y] + ['%.8g' % v for v in (*u, *change)])


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


def readFrames(path):
  """the Frames in the csv at path (written by writeFrames)"""
  data = np.loadtxt(path, delimiter=',', skiprows=1, ndmin=2)
  times = np.unique(data[:, 0])
  xs, ys = np.unique(data[:, 1]), np.unique(data[:, 2])
  shape = (times.size, ys.size, xs.size, 2)
  return Frames(times, xs, ys, data[:, 3:5].reshape(shape), data[:, 5:7].reshape(shape))
