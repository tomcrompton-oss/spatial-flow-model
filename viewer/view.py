"""what is plotted where: path values in each mode, time markers, the view (zoom, pan, fit, aspect, ct) and screen coordinates"""
from viewer.common import *


class View:
  """mixed into Viewer (viewer/app.py)"""

  def pathValues(self, p):
    """a path's x and y before log scaling: position in units, or (distance in units, time)"""
    scale = UNITS[self.unit.get()][1]
    data = p.result.data
    x = data.values[p.xcol][p.rows]
    y = data.values[p.ycol][p.rows]
    if p.result.orbitMask is not None:
      hidden = ~p.result.orbitMask[p.rows]   #rows of hidden orbits
      x, y = np.where(hidden, np.nan, x), np.where(hidden, np.nan, y)
    if self.mode.get() == 'time':
      col = self.axisTimeName(data)
      t = data.values[col][p.rows] if col else np.full(p.rows.size, np.nan)
      return np.hypot(x, y) / scale, t * self.timeFactor()
    return x / scale, y / scale

  def plotPoint(self, x, y, t):
    """a position (m) at time t (s) in plotted space, the way pathValues and prepare place a path's rows"""
    scale = UNITS[self.unit.get()][1]
    if self.mode.get() == 'time':
      px, py = math.hypot(x, y) / scale, t * self.timeFactor()
    else:
      px, py = x / scale, y / scale
    return float(self.toPlot(np.array(px), self.logX.get())), float(self.toPlot(np.array(py), self.logY.get()))

  def prepare(self):
    """convert path values into plotted space (mode, units, log)"""
    self.updateTimeLabels()
    for p in self.allPaths():
      col = self.columnForTime(TIME_COLUMNS[0][0], p.result.data)
      p.tvals = p.result.data.values[col][p.rows] if col else None   #global t of each row, for replays
      x, y = self.pathValues(p)
      p.x = self.toPlot(x, self.logX.get())
      p.y = self.toPlot(y, self.logY.get())
      sx, sy = self.straightValues(p)
      p.straightX = self.toPlot(sx, self.logX.get())
      p.straightY = self.toPlot(sy, self.logY.get())
    self.prepareTimeMarks()

  def straightValues(self, p):
    """
    the path with no gravity, p0 + v0 (t - t0), before log scaling, in the same form as pathValues
    v0 is the first row of the result's velocity columns (v_x/v_y ...), or else the first step of the path;
    with no time column the line steps on by that first step each row
    """
    data = p.result.data
    scale = UNITS[self.unit.get()][1]
    x = data.values[p.xcol][p.rows]
    y = data.values[p.ycol][p.rows]
    nan = np.full(p.rows.size, np.nan)
    ok = np.nonzero(np.isfinite(x) & np.isfinite(y))[0]
    if ok.size < 2:
      return nan, nan
    i0, i1 = ok[0], ok[1]
    tcol = self.columnForTime(TIME_COLUMNS[0][0], data)
    t = data.values[tcol][p.rows] if tcol else None

    velocity = velocityColumns(data)
    if t is not None and velocity:
      vx0, vy0 = data.values[velocity[0]][p.rows][i0], data.values[velocity[1]][p.rows][i0]
    elif t is not None and t[i1] != t[i0]:
      vx0, vy0 = (x[i1] - x[i0]) / (t[i1] - t[i0]), (y[i1] - y[i0]) / (t[i1] - t[i0])
    else:
      t = np.arange(p.rows.size, dtype=float)   #no time: one first step per row
      vx0, vy0 = (x[i1] - x[i0]) / (i1 - i0), (y[i1] - y[i0]) / (i1 - i0)
    sx = x[i0] + vx0 * (t - t[i0])
    sy = y[i0] + vy0 * (t - t[i0])
    if self.mode.get() == 'time':
      col = self.axisTimeName(data)
      axis = data.values[col][p.rows] if col else nan
      return np.hypot(sx, sy) / scale, axis * self.timeFactor()
    return sx / scale, sy / scale

  def columnForTime(self, label, data=None):
    """the csv column for a time option in a dataset (default: the first that has it), or None"""
    datasets = [data] if data is not None else [r.data for r in self.results]
    for d in datasets:
      names = dict((n.lower(), n) for n in d.numeric)
      for option, candidates in TIME_COLUMNS:
        if option == label:
          for c in candidates:
            if c in names:
              return names[c]
    return None

  def axisTimeName(self, data=None):
    """the time column on the x axis in distance / time mode"""
    return self.columnForTime(self.timeColumn.get(), data)

  def timeColumnName(self, data=None):
    """the time column the markers follow"""
    if self.mode.get() == 'time':
      others = [label for label, _ in TIME_COLUMNS if label != self.timeColumn.get()]
      return next((self.columnForTime(o, data) for o in others if self.columnForTime(o, data)), None)
    return self.columnForTime(self.timeColumn.get(), data)

  def updateTimeLabels(self):
    timeMode = self.mode.get() == 'time'
    header = 'Time axis (markers use the other)' if timeMode else 'Markers use'
    self.timeLabel.config(text='Time axis' if timeMode else 'Markers use')
    self.timeMenu.entryconfig(self.timeMenuHeader, label=header)
    marker = self.timeColumnName()
    self.everyLabel.config(text='%s every' % marker if timeMode and marker else 'every')

  def updateTimeChoices(self, resetInterval):
    """offer only the time options the loaded files have"""
    names = set(n.lower() for r in self.results for n in r.data.numeric)
    available = [label for label, candidates in TIME_COLUMNS if any(c in names for c in candidates)]
    for box in self.timeBoxes:
      box.config(values=available or ['(no time column)'])
    if self.timeColumn.get() not in available:
      self.timeColumn.set(available[0] if available else '(no time column)')
    if resetInterval:
      self.timeInterval.set(self.autoInterval())

  def autoInterval(self):
    """a round interval giving about 10 markers"""
    ts = [r.data.values[self.timeColumnName(r.data)] for r in self.results if self.timeColumnName(r.data)]
    if not ts:
      return ''
    t = np.concatenate(ts)
    t = t[np.isfinite(t)]
    if t.size < 2 or t.max() <= t.min():
      return ''
    return formatShort(niceStep(t.max() - t.min(), 10))

  def prepareTimeMarks(self):
    """positions along each path at every interval of the chosen time"""
    self.timeNote = ''
    for p in self.allPaths():
      p.markX = p.markY = p.markT = np.array([])
    col = self.timeColumnName()
    if self.showTimeMarks.get() and col is None and self.mode.get() == 'time' and self.results:
      self.timeNote = 'no second time column for markers'
    if not self.showTimeMarks.get() or col is None:
      return
    try:
      interval = float(self.timeInterval.get())
    except ValueError:
      self.timeNote = 'time interval is not a number'
      return
    if not interval > 0:
      self.timeNote = 'time interval must be above 0'
      return
    for p in self.allPaths():
      col = self.timeColumnName(p.result.data)
      if col is None:
        continue
      t = p.result.data.values[col][p.rows]
      x, y = self.pathValues(p)
      ok = np.isfinite(t) & np.isfinite(x) & np.isfinite(y)
      t, x, y = t[ok], x[ok], y[ok]
      if t.size < 2:
        continue
      if np.any(np.diff(t) < 0):
        self.timeNote = '%s does not always increase along %s' % (col, p.name)
        continue
      marks = np.arange(math.ceil(t[0] / interval - 1e-9), math.floor(t[-1] / interval + 1e-9) + 1) * interval
      rowsOk = np.nonzero(ok)[0]
      if rowsOk.size and rowsOk[-1] - rowsOk[0] + 1 != rowsOk.size:
        #rows are missing (hidden orbits): no markers in the gaps
        j = np.clip(np.searchsorted(t, marks), 1, t.size - 1)
        marks = marks[(rowsOk[j] - rowsOk[j - 1] == 1) | (t[j] == marks) | (t[j - 1] == marks)]
      if marks.size > MAX_TIME_MARKS:
        self.timeNote = 'interval too small (%d markers) - try a larger one' % marks.size
        continue
      p.markT = marks
      p.markX = self.toPlot(np.interp(marks, t, x), self.logX.get())
      p.markY = self.toPlot(np.interp(marks, t, y), self.logY.get())

  def modeChanged(self):
    if self.results and self.mode.get() == 'time' and self.axisTimeName() is None:
      messagebox.showinfo('Distance / time', 'The loaded files have no t or pt column to plot against.')
      self.mode.set('xy')
    self.updateAspectOption()
    if self.results:
      self.updateTimeLabels()
      self.timeInterval.set(self.autoInterval())
      self.prepare()
    self.fit()

  def timeChanged(self):
    if self.results:
      self.prepareTimeMarks()
      self.redraw()

  def timeColumnChanged(self):
    if self.results:
      self.updateTimeLabels()
      self.timeInterval.set(self.autoInterval())
    if self.results and self.mode.get() == 'time':
      self.prepare()
      self.fit()
    else:
      self.timeChanged()

  @staticmethod
  def toPlot(v, log):
    if not log:
      return v
    with np.errstate(divide='ignore', invalid='ignore'):
      return np.where(v > 0, np.log10(np.where(v > 0, v, 1)), np.nan)

  def plotRect(self):
    w = max(self.canvas.winfo_width(), 200)
    h = max(self.canvas.winfo_height(), 150)
    return MARGIN_LEFT, MARGIN_TOP, w - MARGIN_RIGHT, h - MARGIN_BOTTOM

  def aspectActive(self):
    """a unit the same length on both axes: equal aspect in x / y mode, ct in distance / time mode"""
    on = self.equalAspect.get() if self.mode.get() == 'xy' else self.ctTime.get()
    return on and not self.logX.get() and not self.logY.get()

  def timeFactor(self):
    """plotted time per second: c in the distance unit when time is shown as ct, else 1"""
    if self.mode.get() == 'time' and self.ctTime.get():
      return C / UNITS[self.unit.get()][1]
    return 1.0

  def updateAspectOption(self):
    """the Axis tab and Scale menu offer equal aspect in x / y mode and ct in distance / time mode"""
    self.aspectCheck.tooltip.text = ('Distance / time: time as ct in the distance unit on a 1:1 scale, so light with no gravity is at 45°'
                                     if self.mode.get() == 'time' else TIPS['Equal aspect'])
    if self.mode.get() == 'time':
      self.aspectCheck.config(text='ct (light at 45°)', variable=self.ctTime, command=self.ctChanged)
      self.scaleMenu.entryconfig(self.aspectMenuIndex, label='Time as ct (light at 45°)', variable=self.ctTime, command=self.ctChanged)
    else:
      self.aspectCheck.config(text='Equal aspect', variable=self.equalAspect, command=self.aspectChanged)
      self.scaleMenu.entryconfig(self.aspectMenuIndex, label='Equal aspect (1:1)', variable=self.equalAspect, command=self.aspectChanged)

  def ctChanged(self):
    if self.results:
      self.prepare()
    self.fit()

  def applyAspect(self):
    """grow one axis so a unit is the same length on both"""
    if not self.aspectActive():
      return
    l, t, r, b = self.plotRect()
    x0, x1, y0, y1 = self.view
    xpp = (x1 - x0) / (r - l)
    ypp = (y1 - y0) / (b - t)
    upp = max(xpp, ypp)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    self.view = [cx - upp * (r - l) / 2, cx + upp * (r - l) / 2, cy - upp * (b - t) / 2, cy + upp * (b - t) / 2]

  def fit(self):
    xs = [p.x[np.isfinite(p.x)] for p in self.paths]
    ys = [p.y[np.isfinite(p.y)] for p in self.paths]
    xs = np.concatenate(xs) if xs else np.array([])
    ys = np.concatenate(ys) if ys else np.array([])
    if xs.size == 0 or ys.size == 0:
      self.view = [0.0, 1.0, 0.0, 1.0]
    else:
      x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
      xspan, yspan = x1 - x0, y1 - y0
      #a path along one axis has no width on the other: borrow the other span
      fallback = max(xspan, yspan) or max(abs(x0), abs(y0)) * 0.1 or 1.0
      if xspan == 0:
        xspan = fallback
        x0, x1 = x0 - xspan / 2, x1 + xspan / 2
      if yspan == 0:
        yspan = fallback
        y0, y1 = y0 - yspan / 2, y1 + yspan / 2
      pad = 0.05
      self.view = [x0 - xspan * pad, x1 + xspan * pad, y0 - yspan * pad, y1 + yspan * pad]
    self.applyAspect()
    self.redraw()

  def zoom(self, factor):
    l, t, r, b = self.plotRect()
    self.zoomAt(factor, (l + r) / 2, (t + b) / 2)

  def zoomAt(self, factor, px, py):
    x, y = self.toData(px, py)
    x0, x1, y0, y1 = self.view
    self.view = [x - (x - x0) * factor, x + (x1 - x) * factor, y - (y - y0) * factor, y + (y1 - y) * factor]
    self.requestRedraw()

  def pan(self, fx, fy):
    x0, x1, y0, y1 = self.view
    dx, dy = self.xSign() * (x1 - x0) * fx, (y1 - y0) * fy   #the arrows move the way they point on screen
    self.view = [x0 + dx, x1 + dx, y0 + dy, y1 + dy]
    self.redraw()

  def scaleChanged(self):
    self.unitBox.current(self.unit.get())
    if self.results:
      self.prepare()
    self.fit()

  def aspectChanged(self):
    self.applyAspect()
    self.redraw()

  def xReversed(self):
    """distance / time mode with the distance axis reversed: x runs right to left"""
    return self.reverseX.get() and self.mode.get() == 'time'

  def xSign(self):
    """the screen direction of increasing x: 1 left to right, -1 when reversed"""
    return -1 if self.xReversed() else 1

  def toScreen(self, x, y):
    l, t, r, b = self.plotRect()
    x0, x1, y0, y1 = self.view
    sx = l + (x - x0) * (r - l) / (x1 - x0)
    return (l + r - sx if self.xReversed() else sx), b - (y - y0) * (b - t) / (y1 - y0)

  def toData(self, px, py):
    l, t, r, b = self.plotRect()
    x0, x1, y0, y1 = self.view
    if self.xReversed():
      px = l + r - px
    return x0 + (px - l) * (x1 - x0) / (r - l), y0 + (b - py) * (y1 - y0) / (b - t)

  def fromPlot(self, v, log):
    return 10 ** v if log else v
