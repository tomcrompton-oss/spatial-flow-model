"""drawing the plot: axes, paths (with orbit colours), markers, apsides, end arrows, the legend and hover"""
from viewer.common import *


class Drawing:
  """mixed into Viewer (viewer/app.py)"""

  def drawEmpty(self):
    self.canvas.delete('all')
    w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
    self.canvas.create_text(w / 2, h / 2, text='File > Open... to choose a csv file', fill=INK2, font=('Helvetica', 14))
    self.status.config(text='No file loaded')

  def requestRedraw(self):
    if not getattr(self, 'redrawPending', False):
      self.redrawPending = True
      self.root.after_idle(self.redraw)

  def redraw(self):
    self.redrawPending = False
    if not self.results:
      self.drawEmpty()
      return
    c = self.canvas
    c.delete('all')
    l, t, r, b = self.plotRect()
    w, h = c.winfo_width(), c.winfo_height()
    c.create_rectangle(l, t, r, b, fill=SURFACE, outline='')

    xticks, xstep = self.ticks(self.view[0], self.view[1], self.logX.get(), (r - l) / 100)
    yticks, ystep = self.ticks(self.view[2], self.view[3], self.logY.get(), (b - t) / 60)

    if self.showGrid.get():
      for v, _ in xticks:
        sx, _ = self.toScreen(v, 0)
        c.create_line(sx, t, sx, b, fill=GRID)
      for v, _ in yticks:
        _, sy = self.toScreen(0, v)
        c.create_line(l, sy, r, sy, fill=GRID)

    if self.fieldVisible():
      self.drawField()

    self.screenPoints = []
    self.labelCells = set()   #grid cells already holding a time label, shared by all paths
    for p in self.paths:
      self.drawPath(p)

    if self.fieldVisible() and self.showBodies.get():
      self.drawBodies()
    if self.fieldVisible() and self.showSchwarzschild.get():
      self.drawSchwarzschild()

    #cover anything drawn outside the plot area
    c.create_rectangle(0, 0, w, t, fill=PAGE, outline='')
    c.create_rectangle(0, b, w, h, fill=PAGE, outline='')
    c.create_rectangle(0, 0, l, h, fill=PAGE, outline='')
    c.create_rectangle(r, 0, w, h, fill=PAGE, outline='')
    c.create_rectangle(l, t, r, b, outline=AXIS)

    font = ('Helvetica', 11)
    for v, label in xticks:
      sx, _ = self.toScreen(v, 0)
      c.create_line(sx, b, sx, b + 5, fill=AXIS)
      c.create_text(sx, b + 8, text=label, anchor='n', fill=MUTED, font=font)
    for v, label in yticks:
      _, sy = self.toScreen(0, v)
      c.create_line(l - 5, sy, l, sy, fill=AXIS)
      c.create_text(l - 8, sy, text=label, anchor='e', fill=MUTED, font=font)

    xname, yname = self.axisNames()
    c.create_text((l + r) / 2, h - 10, text=xname, anchor='s', fill=INK2, font=('Helvetica', 12))
    c.create_text(14, (t + b) / 2, text=yname, angle=90, anchor='n', fill=INK2, font=('Helvetica', 12))

    shown = [r for r in self.results if r.visible.get()]
    if len(self.results) == 1:
      title = os.path.basename(self.results[0].path)
      if len(self.paths) == 1:
        title += '  —  ' + self.paths[0].name
    else:
      title = '%d of %d results shown' % (len(shown), len(self.results))
    c.create_text(l, t - 14, text=title, anchor='sw', fill=INK, font=('Helvetica', 13, 'bold'))
    if self.timeNote:
      c.create_text(r, t - 14, text=self.timeNote, anchor='se', fill=INK2, font=('Helvetica', 11))
    elif self.showMarkNote.get() and any(p.markT.size for p in self.paths):
      c.create_text(r, t - 14, text='\u25cf  every %s of %s' % (self.timeInterval.get(), self.timeColumnName()),
                    anchor='se', fill=INK2, font=('Helvetica', 11))

    if len(self.paths) >= 2 and self.showPathLegend.get():
      self.drawLegend(r, t)
    self.drawHover()
    self.updateStatus()

  def ticks(self, v0, v1, log, count):
    """(position in plotted space, label) pairs for an axis"""
    count = max(2, int(count))
    if log and v1 - v0 >= count / 2:
      step = max(1, math.ceil((v1 - v0) / count))
      first = math.ceil(v0 / step) * step
      return [(e, '1e%d' % e) for e in range(int(first), int(math.floor(v1)) + 1, step)], step
    if log and v1 - v0 >= 0.5:
      #a few decades: 1, 2, 5 (or 1 to 9) in each decade
      for mults in ((1,), (1, 2, 5), (1, 2, 3, 4, 5, 6, 7, 8, 9)):
        vals = [m * 10.0 ** e for e in range(math.floor(v0), math.ceil(v1) + 1) for m in mults]
        vals = [v for v in vals if v0 <= math.log10(v) <= v1]
        if len(vals) >= 4 or mults[-1] == 9:
          break
      return [(math.log10(v), formatShort(v)) for v in vals], 1
    if log:
      lo, hi = 10 ** v0, 10 ** v1
      vals, step = linearTicks(lo, hi, count)
      vals = [v for v in vals if v > 0]
      return list(zip([math.log10(v) for v in vals], formatTicks(vals, step))), step
    vals, step = linearTicks(v0, v1, count)
    return list(zip(vals, formatTicks(vals, step))), step

  def axisNames(self):
    unit = UNITS[self.unit.get()][2]
    if self.mode.get() == 'time':
      xname = 'distance from origin' + (' (%s)' % unit if unit else '')
      yname = self.axisTimeName() or 'time'
      if self.ctTime.get():
        yname = ('ct' if yname == 't' else 'c·' + yname) + (' (%s)' % unit if unit else '')
    else:
      xs = sorted(set(p.xcol for p in self.paths)) or ['x']
      ys = sorted(set(p.ycol for p in self.paths)) or ['y']
      xname = xs[0] if len(xs) == 1 else 'x'
      yname = ys[0] if len(ys) == 1 else 'y'
      if unit:
        xname, yname = '%s (%s)' % (xname, unit), '%s (%s)' % (yname, unit)
    if self.logX.get():
      xname += '  [log]'
    if self.logY.get():
      yname += '  [log]'
    return xname, yname

  def drawStraight(self, p):
    """dashed no-gravity comparison line under the path"""
    sx, sy = self.toScreen(p.straightX, p.straightY)
    ok = np.isfinite(sx) & np.isfinite(sy)
    if np.count_nonzero(ok) < 2:
      return
    idx = np.nonzero(ok)[0]
    if idx.size > 4000:
      idx = idx[np.linspace(0, idx.size - 1, 4000).astype(int)]   #plenty for a line or a gentle curve
    coords = np.column_stack((np.clip(sx[idx], -1e6, 1e6), np.clip(sy[idx], -1e6, 1e6))).ravel().tolist()
    self.canvas.create_line(*coords, fill=p.color, width=1.5, dash=(6, 4))

  def orbitColour(self, p, o):
    """
    an orbit's colour on path p: the first shown whole orbit is p.color, the last p.color2, and those between an
    even mix of the two (the middle one exactly halfway); a hidden orbit is grey
    """
    if not o.visible.get():
      return AXIS
    if not p.color2:
      return p.color
    shown = [x for x in o.result.orbits if x.visible.get() and x.full]
    if not o.full:
      #the part before the first crossing takes the first colour, the part after the last the last colour
      return p.color if o is o.result.orbits[0] else p.color2
    f = shown.index(o) / (len(shown) - 1) if len(shown) > 1 else 0.0
    return mixColour(p.color, p.color2, f)

  def rowColours(self, p):
    """each row's colour for an orbit run (its orbit's colour), or None for a path in one colour"""
    r = p.result
    if not r.orbits or not p.color2:
      return None
    colours = np.array([self.orbitColour(p, o) for o in r.orbits] + [p.color], dtype=object)
    return colours[r.rowOrbit[p.rows]]   #-1 (no orbit) picks the last entry, p.color

  def drawPath(self, p):
    c = self.canvas
    l, t, r, b = self.plotRect()
    if p.result.showStraight.get() and self.replayState == 'stopped':
      self.drawStraight(p)
    sx, sy = self.toScreen(p.x, p.y)
    finite = np.isfinite(sx) & np.isfinite(sy)
    window = self.replayWindow(p)
    if window is not None:
      finite &= window   #only the trail so far

    #keep points near the view, plus their neighbours so lines leave the edge correctly
    w, h = r - l, b - t
    near = finite & (sx > l - 2 * w) & (sx < r + 2 * w) & (sy > t - 2 * h) & (sy < b + 2 * h)
    keep = near.copy()
    keep[1:] |= near[:-1] & finite[1:]
    keep[:-1] |= near[1:] & finite[:-1]

    #split into runs of consecutive rows, then drop points on the same pixel as the previous one
    idx = np.nonzero(keep)[0]
    seg = np.zeros(idx.size, dtype=np.int64)
    if idx.size:
      px = np.round(sx[idx]).astype(np.int64)
      py = np.round(sy[idx]).astype(np.int64)
      gap = np.ones(idx.size, dtype=bool)
      gap[1:] = np.diff(idx) > 1
      seg = np.cumsum(gap)
      moved = np.ones(idx.size, dtype=bool)
      moved[1:] = (np.diff(px) != 0) | (np.diff(py) != 0)
      last = np.zeros(idx.size, dtype=bool)
      last[:-1] = gap[1:]
      last[-1] = True
      colours = self.rowColours(p)
      if colours is not None:
        changed = np.zeros(idx.size, dtype=bool)   #keep each orbit's first point, where its colour starts
        changed[1:] = colours[idx[1:]] != colours[idx[:-1]]
        moved |= changed
      keepPoint = moved | gap | last
      idx, seg = idx[keepPoint], seg[keepPoint]

    colours = self.rowColours(p)
    xs = np.clip(sx[idx], -1e6, 1e6)
    ys = np.clip(sy[idx], -1e6, 1e6)
    breaks = np.nonzero(np.diff(seg) != 0)[0] + 1
    for run in np.split(np.arange(idx.size), breaks):
      if run.size >= 2:
        if colours is None:
          pieces = [(run, p.color)]
        else:
          #one piece per orbit, each starting from the last point of the one before so the line joins up
          rc = colours[idx[run]]
          starts = [0] + list(np.nonzero(rc[1:] != rc[:-1])[0] + 1)
          pieces = []
          for k, a in enumerate(starts):
            e = starts[k + 1] if k + 1 < len(starts) else run.size
            pieces.append((run[max(a - 1, 0):e], rc[a]))
        for piece, colour in pieces:
          if piece.size >= 2:
            coords = np.column_stack((xs[piece], ys[piece])).ravel().tolist()
            c.create_line(*coords, fill=colour, width=2, capstyle='round', joinstyle='round', dash=p.dash)
      elif run.size == 1:
        x, y = xs[run[0]], ys[run[0]]
        c.create_oval(x - 2, y - 2, x + 2, y + 2, fill=p.color if colours is None else colours[idx[run[0]]], outline='')

    self.screenPoints.append((p, idx, xs, ys))

    if p.markT.size:
      self.drawTimeMarks(p)

    if p.result.showEnds.get() and self.mode.get() == 'xy' and not self.logX.get() and not self.logY.get() and self.replayState == 'stopped':
      self.drawEndArrows(p)

    if p.result.orbits and (p.result.showPeri.get() or p.result.showApo.get()):
      self.drawApsides(p)

    head = self.replayHead(p)
    if head is not None:
      #the trail's leading edge: on from the last row to where the path is now, and a dot there
      hx, hy, j = head
      x, y = self.toScreen(hx, hy)
      colour = p.color if colours is None else colours[j]
      if finite[j]:
        x0, y0 = sx[j], sy[j]
        c.create_line(x0, y0, x, y, fill=colour, width=2, capstyle='round', dash=p.dash)
      if math.isfinite(x) and math.isfinite(y):
        c.create_oval(x - 6, y - 6, x + 6, y + 6, fill=SURFACE, outline='')
        c.create_oval(x - 4.5, y - 4.5, x + 4.5, y + 4.5, fill=colour, outline=colour, width=2)

    if self.showMarkers.get():
      valid = np.nonzero(finite)[0]
      if valid.size:
        ends = [(valid[0], False)] + ([(valid[-1], True)] if head is None else [])
        for i, filled in ends:
          x, y = sx[i], sy[i]
          colour = p.color if colours is None else colours[i]
          if l - 6 <= x <= r + 6 and t - 6 <= y <= b + 6:
            c.create_oval(x - 6, y - 6, x + 6, y + 6, fill=SURFACE, outline='')
            c.create_oval(x - 4.5, y - 4.5, x + 4.5, y + 4.5, fill=colour if filled else SURFACE, outline=colour, width=2)

  def apsisMarker(self, x, y, kind, colour):
    """an open square (periapsis) or open diamond (apoapsis) at a screen point"""
    c = self.canvas
    if kind == PERIAPSIS:
      k = 4.5
      c.create_rectangle(x - k, y - k, x + k, y + k, fill='', outline=colour, width=2)
    else:
      k = 6
      c.create_polygon(x, y - k, x + k, y, x, y + k, x - k, y, fill='', outline=colour, width=2)

  def drawApsides(self, p):
    """
    each shown whole orbit's periapsis (open square) and apoapsis (open diamond), as picked, in the orbit's
    colour; in a replay only those already passed
    """
    l, t, r, b = self.plotRect()
    replaying = self.replayState != 'stopped'
    for o in p.result.orbits:
      if not o.visible.get() or not o.full:
        continue
      colour = self.orbitColour(p, o)
      for kind, attr in ((PERIAPSIS, 'peri'), (APOAPSIS, 'apo')):
        if not (p.result.showPeri if kind == PERIAPSIS else p.result.showApo).get():
          continue
        point = getattr(o, attr)
        if point is None:
          continue
        if replaying and not (self.trailStart <= point[2] <= self.replayT):
          continue
        x, y = self.toScreen(*self.plotPoint(*point))
        if math.isfinite(x) and math.isfinite(y) and l - 6 <= x <= r + 6 and t - 6 <= y <= b + 6:
          self.apsisMarker(x, y, kind, colour)

  def endVectors(self, data):
    """velocity-like column pairs (v_x/v_y, u_x/u_y ...) as (label, xcol, ycol)"""
    return [pair for pair in data.pairs() if not isPositionLabel(pair[0])][:len(END_COLORS)]

  def pathEnds(self, p):
    """rows of the path that end a run of positions - a row of empty cells in the csv ends a run"""
    data = p.result.data
    ok = np.isfinite(data.values[p.xcol][p.rows]) & np.isfinite(data.values[p.ycol][p.rows])
    last = ok.copy()
    last[:-1] &= ~ok[1:]
    return p.rows[last]

  def endReference(self, result):
    """the largest velocity at any path end of a result, which gets the longest arrow"""
    sizes = [0.0]
    for p in result.paths:
      rows = self.pathEnds(p)
      for _, vx, vy in self.endVectors(result.data):
        size = np.hypot(result.data.values[vx][rows], result.data.values[vy][rows])
        sizes.extend(size[np.isfinite(size)].tolist())
    return max(sizes)

  def drawEndArrows(self, p):
    """an arrow at the end of each run of the path for each velocity pair, all to one scale"""
    c = self.canvas
    data = p.result.data
    reference = self.endReference(p.result)
    if not reference > 0:
      return
    scale = UNITS[self.unit.get()][1]
    rows = self.pathEnds(p)
    sx, sy = self.toScreen(data.values[p.xcol][rows] / scale, data.values[p.ycol][rows] / scale)
    for k, (_, vx, vy) in enumerate(self.endVectors(data)):
      dx = data.values[vx][rows] / reference * END_LENGTH
      dy = -data.values[vy][rows] / reference * END_LENGTH   #screen y runs down
      for x, y, ax, ay in zip(sx, sy, dx, dy):
        if np.isfinite(ax) and np.isfinite(ay):
          c.create_line(x, y, x + ax, y + ay, fill=END_COLORS[k], width=1.5, arrow='last', arrowshape=(7, 8, 3))

  def endKeys(self):
    """key entries for the end arrows of the shown results"""
    keys = []
    if self.mode.get() != 'xy':
      return keys
    for r in self.results:
      if r.visible.get() and r.showEnds.get():
        reference = self.endReference(r)
        for k, (label, _, _) in enumerate(self.endVectors(r.data)):
          text = '%s at the path ends  %s km/s' % (label, formatShort(float('%.3g' % (reference / 1000))))
          if (END_COLORS[k], text) not in keys:
            keys.append((END_COLORS[k], text))
    return keys

  def drawTimeMarks(self, p):
    """dots on the path at each time interval, labelled where there is room"""
    c = self.canvas
    l, t, r, b = self.plotRect()
    sx, sy = self.toScreen(p.markX, p.markY)
    inView = np.isfinite(sx) & np.isfinite(sy) & (sx >= l - 5) & (sx <= r + 5) & (sy >= t - 5) & (sy <= b + 5)
    if self.replayState != 'stopped' and p.tvals is not None:
      #the markers' times in global t (they may be in proper time), kept only along the trail
      col = self.timeColumnName(p.result.data)
      mt = p.result.data.values[col][p.rows] if col else p.tvals
      ok = np.isfinite(mt) & np.isfinite(p.tvals)
      tm = np.interp(p.markT, mt[ok], p.tvals[ok]) if ok.sum() >= 2 else np.full(p.markT.size, np.nan)
      inView &= (tm >= self.trailStart) & (tm <= self.replayT)
    cellW, cellH = 48, 16
    for i in np.nonzero(inView)[0]:
      x, y = sx[i], sy[i]
      c.create_oval(x - 4.5, y - 4.5, x + 4.5, y + 4.5, fill=SURFACE, outline='')
      c.create_oval(x - 3, y - 3, x + 3, y + 3, fill=p.color, outline='')
      #label only where no other label is nearby
      cx, cy = int(x // cellW), int(y // cellH)
      near = [(cx + dx, cy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
      if self.showMarkLabels.get() and not any(cell in self.labelCells for cell in near):
        c.create_text(x + 8, y - 1, text=formatShort(p.markT[i]), anchor='w', fill=INK2, font=('Helvetica', 10))
        self.labelCells.add((cx, cy))

  def drawLegend(self, right, top):
    c = self.canvas
    font = ('Helvetica', 11)
    rowH = 18
    width = max(len(self.pathLabel(p)) for p in self.paths) * 7 + 44
    height = rowH * len(self.paths) + 10
    x0, y0 = right - width - 10, top + 10
    c.create_rectangle(x0, y0, x0 + width, y0 + height, fill=SURFACE, outline=GRID)
    for i, p in enumerate(self.paths):
      y = y0 + 5 + rowH * i + rowH / 2
      if p.result.orbits and p.color2:
        for k in range(4):   #first orbit's colour to the last's
          c.create_line(x0 + 10 + 5 * k, y, x0 + 15 + 5 * k, y, fill=mixColour(p.color, p.color2, k / 3), width=2)
      else:
        c.create_line(x0 + 10, y, x0 + 30, y, fill=p.color, width=2, dash=p.dash)
      c.create_text(x0 + 36, y, text=self.pathLabel(p), anchor='w', fill=INK, font=font)

  def nearest(self, mx, my):
    best = None
    for p, idx, xs, ys in getattr(self, 'screenPoints', []):
      if idx.size == 0:
        continue
      d2 = (xs - mx) ** 2 + (ys - my) ** 2
      i = int(np.argmin(d2))
      if d2[i] <= 12 ** 2 and (best is None or d2[i] < best[0]):
        best = (d2[i], p, int(idx[i]), xs[i], ys[i])
    return best

  def setHover(self, hover):
    if hover != self.hover:
      self.hover = hover
      self.requestRedraw()

  def drawHover(self):
    if not self.hover:
      return
    p, i, x, y = self.hover
    c = self.canvas
    l, t, r, b = self.plotRect()
    c.create_oval(x - 7, y - 7, x + 7, y + 7, outline=SURFACE, width=3)
    c.create_oval(x - 5, y - 5, x + 5, y + 5, fill=p.color, outline='')

    row = p.rows[i]
    data = p.result.data
    names = data.names
    lines = [self.pathLabel(p)] + ['%s  %s' % (n, data.text[n][row]) for n in names[:12]]
    if len(names) > 12:
      lines.append('... %d more columns' % (len(names) - 12))
    text = '\n'.join(lines)
    item = c.create_text(0, 0, text=text, anchor='nw', fill=INK, font=('Helvetica', 11), justify='left')
    bx0, by0, bx1, by1 = c.bbox(item)
    tw, th = bx1 - bx0 + 16, by1 - by0 + 12
    tx = x + 14 if x + 14 + tw < r else x - 14 - tw
    ty = min(max(y - th / 2, t), b - th)
    box = c.create_rectangle(tx, ty, tx + tw, ty + th, fill=SURFACE, outline=AXIS)
    c.create_rectangle(tx, ty, tx + 4, ty + th, fill=p.color, outline='')
    c.coords(item, tx + 10, ty + 6)
    c.tag_raise(item, box)
