"""the backgrounds for an environment: bodies, u and g arrows, equal-u lines, flow lines, Schwarzschild radius, light cones, and their key"""
from viewer.common import *


class Backgrounds:
  """mixed into Viewer (viewer/app.py)"""

  def fieldResult(self):
    """
    the Environment whose bodies and backgrounds are drawn: the one chosen under Background, or else the selected
    result's, or that of the first shown result with bodies
    """
    if self.fieldChoice in self.activeEnvironments():
      return self.fieldChoice if self.fieldChoice.bodies else None
    r = self.current()
    if r is not None and r.visible.get() and r.env.bodies:
      return r.env
    return next((r.env for r in self.results if r.visible.get() and r.env.bodies), None)

  def activeEnvironments(self):
    """the environments of the loaded results, in load order"""
    out = []
    for r in self.results:
      if r.env is not None and r.env not in out:   #None until the result's log is read
        out.append(r.env)
    return out

  def fieldVisible(self):
    """bodies and their field are drawn on linear axes"""
    return self.fieldResult() is not None and not self.logX.get() and not self.logY.get()

  def bodyScreen(self):
    """each body's screen point; in distance / time mode the point is on the time axis's start, at its distance"""
    scale = UNITS[self.unit.get()][1]
    if self.mode.get() == 'time':
      _, b = self.plotRect()[1::2]
      return [((self.toScreen(math.hypot(x, y) / scale, 0)[0], b), mass, black) for mass, x, y, black in self.fieldResult().bodies]
    return [(self.toScreen(x / scale, y / scale), mass, black) for mass, x, y, black in self.fieldResult().bodies]

  def drawBodies(self):
    c = self.canvas
    if self.mode.get() == 'time':
      #a body stays at its distance: a line up the time axis, labelled at the bottom
      l, t, r, b = self.plotRect()
      for (x, _), mass, black in self.bodyScreen():
        if l <= x <= r:
          c.create_line(x, t, x, b, fill=INK if black else MUTED, width=2, dash=() if black else (4, 3))
          if self.showBodyLabels.get():
            c.create_text(x + 4, b - 4, text='%s MS %s' % (formatShort(round(mass / MS, 4)), 'black' if black else 'white'),
                          anchor='sw', fill=INK2, font=('Helvetica', 10))
      return
    for (x, y), mass, black in self.bodyScreen():
      r = BODY_RADIUS
      c.create_oval(x - r - 2, y - r - 2, x + r + 2, y + r + 2, fill=SURFACE, outline='')
      c.create_oval(x - r, y - r, x + r, y + r, fill=INK if black else SURFACE, outline=INK, width=2)
      if self.showBodyLabels.get():
        c.create_text(x, y + r + 5, text='%s MS' % formatShort(round(mass / MS, 4)),
                      anchor='n', fill=INK2, font=('Helvetica', 10))

  @staticmethod
  def schwarzschild(mass):
    """the Schwarzschild radius 2GM/c^2 (m), where the flow speed reaches c"""
    return 2 * G * mass / C**2

  def drawSchwarzschild(self):
    """
    each body's Schwarzschild radius: x / y mode, a dotted circle round the body; distance / time mode, a dotted
    line up the time axis at that distance either side of the body (inside 0 is left out)
    """
    c = self.canvas
    l, t, r, b = self.plotRect()
    scale = UNITS[self.unit.get()][1]
    for mass, x, y, black in self.fieldResult().bodies:
      rs = self.schwarzschild(mass)
      if self.mode.get() == 'time':
        d = math.hypot(x, y)
        for edge in (d - rs, d + rs):
          if edge < 0:
            continue
          sx, _ = self.toScreen(edge / scale, 0)
          if l <= sx <= r:
            c.create_line(sx, t, sx, b, fill=SCHWARZ, width=1.5, dash=SCHWARZ_DASH)
            c.create_text(sx + 4 * self.xSign(), t + 4, text='Rs', anchor='nw' if self.xSign() > 0 else 'ne',
                          fill=INK2, font=('Helvetica', 10))
      else:
        (cx, cy), (ex, ey) = self.toScreen(x / scale, y / scale), self.toScreen((x + rs) / scale, (y + rs) / scale)
        rx, ry = abs(ex - cx), abs(ey - cy)
        c.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, outline=SCHWARZ, width=1.5, dash=SCHWARZ_DASH)

  def drawField(self):
    """equal-u lines, then flow and gravity arrows (and light cones against time), with a key for each"""
    keys = []
    timeMode = self.mode.get() == 'time'
    if self.showContours.get():
      self.drawContours()
    if not timeMode and self.showFlowLines.get() and self.drawFlowLines():
      keys.append((FLOW_LINE, 'flow lines: %d per body from %s m at |u|, outwards, under g' % (FLOW_LINES, formatShort(RSUN))))
    if timeMode and self.showFlowLines.get():
      #the flow line is in global time, like the cones
      if self.timeColumn.get() != TIME_COLUMNS[0][0]:
        keys.append((None, 'flow lines need global time (t) on the time axis'))
      else:
        every = self.drawFlowLinesTime()
        if every:
          keys.append((FLOW_LINE, 'flow line: space moving at u (dd/dt = u), repeated every %s s' % formatShort(every)))
    if self.showFlow.get():
      ref = self.drawArrows(lambda calc, pos: calc.flow(pos), 0.0, MUTED)
      if ref:
        keys.append((MUTED, 'u  %s km/s' % formatShort(float('%.3g' % (ref / 1000)))))
    if self.showGravity.get():
      ref = self.drawArrows(lambda calc, pos: calc.gravity(pos), 0.5, G_ARROW)
      if ref:
        keys.append((G_ARROW, 'g  %s m/s²' % formatShort(float('%.3g' % ref))))
    if timeMode and self.showCones.get():
      #proper time stands still for light, so the cones need t
      if self.timeColumn.get() != TIME_COLUMNS[0][0]:
        keys.append((None, 'light cones need global time (t) on the time axis'))
      elif self.drawCones():
        keys.append((CONE, 'light cones: local speed of light outwards and inwards, u ± c'))
    if self.showContours.get():
      keys.append((AXIS, 'lines of equal |u|, km/s'))
    if self.showSchwarzschild.get():
      radii = sorted({self.schwarzschild(mass) for mass, _, _, _ in self.fieldResult().bodies})
      keys.append((SCHWARZ, 'Schwarzschild radius 2GM/c²: %s m' % ', '.join(formatShort(float('%.4g' % rs)) for rs in radii)))
    if any(r.visible.get() and r.orbits and r.showPeri.get() for r in self.results):
      keys.append((PERIAPSIS, 'periapsis of each orbit'))
    if any(r.visible.get() and r.orbits and r.showApo.get() for r in self.results):
      keys.append((APOAPSIS, 'apoapsis of each orbit'))
    keys = self.endKeys() + keys
    if timeMode and keys:
      keys[0] = (keys[0][0], keys[0][1] + '  (along the line from the origin, at (d, 0))')
    if self.showFieldKey.get():
      self.drawFieldKey(keys)

  def flowLines(self, result):
    """each body's outward lines (positions in m), worked out once per environment"""
    if result.flowLines is None:
      result.flowLines = []
      calc = result.flowCalc
      if calc is not None and flowlines is not None:
        self.canvas.config(cursor='watch')
        self.root.update_idletasks()
        for home in calc.bodies:
          for n in range(FLOW_LINES):
            rows, _, _ = flowlines.line(calc, home, 2*math.pi*n/FLOW_LINES, RSUN, FLOW_LINE_REACH, FLOW_LINE_STEP, 2)
            result.flowLines.append(np.array([pos for _, pos, _ in rows]))
        self.canvas.config(cursor='crosshair')
    return result.flowLines

  def drawFlowLines(self):
    """the outward lines from each body, in x / y mode; returns whether any were drawn"""
    scale = UNITS[self.unit.get()][1]
    drawn = False
    for line in self.flowLines(self.fieldResult()):
      pts = []
      for x, y in line:
        pts.extend(self.toScreen(x / scale, y / scale))
      if len(pts) >= 4:
        self.canvas.create_line(*pts, fill=FLOW_LINE, width=1)
        drawn = True
    return drawn

  def flowLineTime(self):
    """
    the flow line across the screen in distance / time mode: space moving at the flow, dd/dt = u along the line
    from the origin, at (d, 0); u depends on d only, so t(d) = integral of dd / u is the same line at every start time
    returns runs of (d in axis units, t relative to the run's start), split where u is 0, changes sign or is not finite
    """
    calc = self.fieldResult().flowCalc
    scale = UNITS[self.unit.get()][1]
    x0, x1 = self.view[:2]
    if calc is None or x1 <= 0:
      return []
    d = np.linspace(max(x0, 0.0), x1, FLOW_LINE_POINTS) * scale
    u = np.array([calc.flow(np.array([v, 0.0]))[0] if v > 0 else np.nan for v in d])
    runs, start = [], 0
    for i in range(1, len(d) + 1):
      if i == len(d) or not (np.isfinite(u[i]) and u[i] != 0 and np.sign(u[i]) == np.sign(u[i - 1])):
        if i - start >= 2 and np.isfinite(u[start:i]).all() and (u[start:i] != 0).all():
          dd, uu = d[start:i], u[start:i]
          t = np.concatenate([[0.0], np.cumsum(np.diff(dd) * (1 / uu[1:] + 1 / uu[:-1]) / 2)])   #trapezium rule
          runs.append((dd / scale, t))
        start = i
    return runs

  def drawFlowLinesTime(self):
    """
    copies of the flow line spaced regularly up the time axis (at whole multiples of the spacing, so they stay put
    when panning); returns the spacing, or None if nothing was drawn
    """
    runs = self.flowLineTime()
    if not runs:
      return None
    tf = self.timeFactor()
    y0, y1 = self.view[2] / tf, self.view[3] / tf   #seconds
    every = niceStep(y1 - y0, FLOW_LINE_COPIES)
    c = self.canvas
    drawn = False
    for x, t in runs:
      lo, hi = float(t.min()), float(t.max())
      first, last = math.floor((y0 - hi) / every), math.ceil((y1 - lo) / every)
      if last - first > 40 * FLOW_LINE_COPIES:
        #a line that takes far longer than the view to cross the screen: only the copies through the view's corners
        first = max(first, math.floor((y0 - lo) / every) - 2 * FLOW_LINE_COPIES)
        last = min(last, first + 4 * FLOW_LINE_COPIES)
      for k in range(first, last + 1):
        ts = k * every + t
        inside = (ts >= y0 - (y1 - y0)) & (ts <= y1 + (y1 - y0))
        if inside.sum() < 2:
          continue
        pts = []
        for sx, sy in zip(*self.toScreen(x[inside], ts[inside] * tf)):
          pts.extend((sx, sy))
        c.create_line(*pts, fill=FLOW_LINE, width=1)
        drawn = True
    return every if drawn else None

  def fieldAt(self, sx, sy):
    """
    the position (m) whose field is drawn at a screen point
    x / y mode: that point; distance / time mode: (d, 0), d being the distance on the x axis
    """
    scale = UNITS[self.unit.get()][1]
    x, y = self.toData(sx, sy)
    if self.mode.get() == 'time':
      return np.array([x * scale, 0.0]) if x > 0 else None
    return np.array([x * scale, y * scale])

  def nearBody(self, sx, sy):
    """too close to a body (in distance / time mode, to a body's line) to draw the field"""
    for (bx, by), _, _ in self.bodyScreen():
      if self.mode.get() == 'time':
        if abs(sx - bx) < BODY_RADIUS:
          return True
      elif math.hypot(sx - bx, sy - by) < BODY_RADIUS + 6:
        return True
    return False

  def fieldGrid(self, offset):
    """screen points on a regular grid, shifted by offset cells, clear of the bodies"""
    l, t, r, b = self.plotRect()
    shift = FLOW_SPACING * (0.5 + offset)
    for sy in np.arange(t + shift, b, FLOW_SPACING):
      for sx in np.arange(l + shift, r, FLOW_SPACING):
        if not self.nearBody(sx, sy):
          yield sx, sy

  def drawArrows(self, field, offset, color):
    """
    arrows on a regular grid (shifted by offset cells) showing the direction and relative size of a field
    in distance / time mode the arrows are the part of the field along the distance axis
    returns the value a full-length arrow stands for, or None
    """
    calc = self.fieldResult().flowCalc
    if calc is None:
      return None
    c = self.canvas
    timeMode = self.mode.get() == 'time'

    points = []
    for sx, sy in self.fieldGrid(offset):
      pos = self.fieldAt(sx, sy)
      if pos is None:
        continue
      v = field(calc, pos)
      if timeMode:
        v = np.array([v[0], 0.0])
      size = float(np.linalg.norm(v))
      if size > 0 and math.isfinite(size):
        points.append((sx, sy, v / size, size))
    if not points:
      return None

    #lengths in proportion to the field, scaled so most arrows fit; the strongest are capped
    longest = FLOW_SPACING * 0.8
    reference = float(np.percentile([p[3] for p in points], 90))
    for sx, sy, direction, size in points:
      length = longest * min(1.0, size / reference)
      dx, dy = self.xSign() * direction[0] * length, -direction[1] * length   #screen y runs down
      c.create_line(sx - dx / 2, sy - dy / 2, sx + dx / 2, sy + dy / 2, fill=color, width=1,
                    arrow='last', arrowshape=(6, 7, 2.5))
    return reference

  def lightSpeeds(self, u):
    """
    the local speeds (m/s) of light going outwards and inwards where the flow is u along the distance axis
    light moves at c relative to the flowing space, w = +/- c, so against the axis it goes at v = u + w, as the
    light rays do in the flow calculators (initPW); near a black hole u is large and inwards, so light outwards
    is slowed to c - |u| and light inwards sped up to c + |u|: the cones tilt towards the hole and narrow
    """
    return u + C, u - C

  def drawCones(self):
    """
    the light cone at each grid point of distance against t: light sent outwards and inwards by an observer
    moving with the flow u (along the line from the origin, at (d, 0)); each side runs along that light's path,
    drawn the same length on screen, and a tilted ellipse joins their ends, like the cap of a cone in perspective
    """
    calc = self.fieldResult().flowCalc
    if calc is None:
      return False
    c = self.canvas
    l, t, r, b = self.plotRect()
    x0, x1, y0, y1 = self.view
    scale = UNITS[self.unit.get()][1]
    kd = self.xSign() * (r - l) / ((x1 - x0) * scale)  #pixels per metre, negative when the axis runs right to left
    kt = (b - t) * self.timeFactor() / (y1 - y0)   #pixels per second
    side = 2.2 * CONE_SIZE   #pixels along each side
    angles = np.linspace(0, 2 * math.pi, 33)
    for sx, sy in self.fieldGrid(-0.25):
      pos = self.fieldAt(sx, sy)
      if pos is None:
        continue
      u = float(calc.flow(pos)[0])
      if not math.isfinite(u):
        continue
      ends = []
      for speed in self.lightSpeeds(u):
        dx, dy = speed * kd, -kt   #screen movement per second; screen y runs down, time runs up
        n = math.hypot(dx, dy)
        ends.append((sx + side * dx / n, sy + side * dy / n))
      (ox, oy), (bx, by) = ends
      a = math.hypot(ox - bx, oy - by) / 2
      if a > 0.45 * FLOW_SPACING:
        #a wide-open cone (light nearly flat on screen) is shortened, both sides alike, to fit its grid cell
        f = 0.45 * FLOW_SPACING / a
        ox, oy, bx, by = sx + (ox - sx) * f, sy + (oy - sy) * f, sx + (bx - sx) * f, sy + (by - sy) * f
      #the cap: an ellipse through both ends, its long axis along the line between them
      cx, cy = (ox + bx) / 2, (oy + by) / 2
      a = math.hypot(ox - bx, oy - by) / 2
      if a > 0:
        ex, ey = (ox - bx) / (2 * a), (oy - by) / (2 * a)   #along the long axis
        minor = max(2.0, 0.3 * a)
        pts = []
        for th in angles:
          ca, sa = a * math.cos(th), minor * math.sin(th)
          pts.extend((cx + ca * ex - sa * ey, cy + ca * ey + sa * ex))
        c.create_line(*pts, fill=CONE, width=1, smooth=True)
      c.create_line(bx, by, sx, sy, ox, oy, fill=CONE, width=1)
      c.create_oval(sx - 1.5, sy - 1.5, sx + 1.5, sy + 1.5, fill=CONE, outline='')
    return True

  def drawFieldKey(self, keys):
    """what a full-length arrow means, bottom left of the plot"""
    c = self.canvas
    l, t, r, b = self.plotRect()
    longest = FLOW_SPACING * 0.8
    if not keys:
      return
    suffix = '  (%s)' % self.fieldResult().name if len(self.results) > 1 else ''
    kx, rowH = l + 12, 18
    ky0 = b - 14 - rowH * (len(keys) - 1)
    items = []
    for i, (color, text) in enumerate(keys):
      ky = ky0 + rowH * i
      items.append(c.create_text(kx + longest + 8, ky, text=text + (suffix if i == 0 else ''), anchor='w', fill=INK2, font=('Helvetica', 10)))
    right = max(c.bbox(item)[2] for item in items)
    box = c.create_rectangle(kx - 6, ky0 - 12, right + 8, b - 4, fill=SURFACE, outline=GRID)
    for item in items:
      c.tag_raise(item, box)
    for i, (color, text) in enumerate(keys):
      ky = ky0 + rowH * i
      if color == AXIS:
        c.create_line(kx, ky, kx + longest, ky, fill=AXIS, width=1.5)
      elif color in (PERIAPSIS, APOAPSIS):
        self.apsisMarker(kx + longest / 2, ky, color, INK2)
      elif color == SCHWARZ:
        c.create_line(kx, ky, kx + longest, ky, fill=SCHWARZ, width=1.5, dash=SCHWARZ_DASH)
      elif color == FLOW_LINE:
        c.create_line(kx, ky, kx + longest, ky, fill=FLOW_LINE, width=1)
      elif color == CONE:
        c.create_line(kx + longest, ky - 6, kx, ky, kx + longest, ky + 6, fill=CONE, width=1)
        c.create_oval(kx + longest - 2, ky - 6, kx + longest + 2, ky + 6, outline=CONE, width=1)
      elif color is None:
        pass   #a note, no symbol
      else:
        c.create_line(kx, ky, kx + longest, ky, fill=color, width=1, arrow='last', arrowshape=(6, 7, 2.5))

  def flowSpeedGrid(self):
    """
    |u| = sqrt(sum of 2GM/d) - the magnitude rule in flow.Calculator.flow - on a fine screen grid
    returns screen x, screen y and speed (m/s) arrays
    """
    l, t, r, b = self.plotRect()
    scale = UNITS[self.unit.get()][1]
    sx = np.arange(l, r + CONTOUR_SPACING, CONTOUR_SPACING, dtype=float)
    sy = np.arange(t, b + CONTOUR_SPACING, CONTOUR_SPACING, dtype=float)
    gx, gy = np.meshgrid(sx, sy)
    x, y = self.toData(gx, gy)
    x, y = x * scale, y * scale
    if self.mode.get() == 'time':
      x, y = np.where(x > 0, x, np.nan), np.zeros_like(y)   #distance on the x axis, taken along (d, 0)
    square = np.zeros_like(x)
    with np.errstate(divide='ignore', invalid='ignore'):
      for mass, bx, by, black in self.fieldResult().bodies:
        square += 2 * G * mass / np.hypot(x - bx, y - by)
    return sx, sy, np.sqrt(square)

  def drawContours(self):
    """lines of equal flow speed, traced with marching squares, each labelled once"""
    c = self.canvas
    sx, sy, speed = self.flowSpeedGrid()
    finite = speed[np.isfinite(speed)]
    if finite.size == 0:
      return
    lo, hi = np.percentile(finite, 2), np.percentile(finite, 98)
    if not hi > lo:
      return
    step = niceStep(hi - lo, 8)
    levels = np.arange(math.ceil(lo / step) * step, hi, step)

    #corners of every cell: a top-left, b top-right, cc bottom-right, d bottom-left
    a, bb, cc, d = speed[:-1, :-1], speed[:-1, 1:], speed[1:, 1:], speed[1:, :-1]
    x0, x1 = sx[:-1][None, :], sx[1:][None, :]
    y0, y1 = sy[:-1][:, None], sy[1:][:, None]
    labelled = []
    for level in levels:
      with np.errstate(invalid='ignore', divide='ignore'):
        def cross(p, q):
          return ((p >= level) != (q >= level)) & np.isfinite(p) & np.isfinite(q)
        def frac(p, q):
          return (level - p) / (q - p)
        edges = [
          (cross(a, bb), x0 + frac(a, bb) * (x1 - x0), np.broadcast_to(y0, a.shape)),     #top
          (cross(bb, cc), np.broadcast_to(x1, a.shape), y0 + frac(bb, cc) * (y1 - y0)),   #right
          (cross(d, cc), x0 + frac(d, cc) * (x1 - x0), np.broadcast_to(y1, a.shape)),     #bottom
          (cross(a, d), np.broadcast_to(x0, a.shape), y0 + frac(a, d) * (y1 - y0)),       #left
        ]
      hit = np.stack([e[0] for e in edges])
      px = np.stack([np.broadcast_to(e[1], a.shape) for e in edges])
      py = np.stack([np.broadcast_to(e[2], a.shape) for e in edges])
      count = hit.sum(axis=0)
      segments = []
      #two crossings: one segment between them
      rows, cols = np.nonzero(count == 2)
      if rows.size:
        which = np.argsort(~hit[:, rows, cols], axis=0, kind='stable')[:2]
        for k in range(rows.size):
          e0, e1 = which[0, k], which[1, k]
          i, j = rows[k], cols[k]
          segments.append((px[e0, i, j], py[e0, i, j], px[e1, i, j], py[e1, i, j]))
      #four crossings (a saddle): top with left, right with bottom
      for i, j in zip(*np.nonzero(count == 4)):
        segments.append((px[0, i, j], py[0, i, j], px[3, i, j], py[3, i, j]))
        segments.append((px[1, i, j], py[1, i, j], px[2, i, j], py[2, i, j]))
      for seg in segments:
        c.create_line(*seg, fill=AXIS, width=1.5)
      if segments:
        #label at the segment furthest right that is clear of other labels
        for seg in sorted(segments, key=lambda s: -(s[0] + s[2])):
          mx, my = (seg[0] + seg[2]) / 2, (seg[1] + seg[3]) / 2
          if all(math.hypot(mx - lx, my - ly) > 40 for lx, ly in labelled):
            item = c.create_text(mx, my, text=formatShort(float('%.3g' % (level / 1000))), fill=MUTED, font=('Helvetica', 9))
            x0b, y0b, x1b, y1b = c.bbox(item)
            box = c.create_rectangle(x0b - 2, y0b, x1b + 2, y1b, fill=SURFACE, outline='')
            c.tag_raise(item, box)
            labelled.append((mx, my))
            break
