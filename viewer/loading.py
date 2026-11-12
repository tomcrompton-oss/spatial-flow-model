"""opening, reloading and closing results: their logs, environments, orbits and paths"""
from viewer.common import *


class Loading:
  """mixed into Viewer (viewer/app.py)"""

  def readLog(self, result):
    """the .log file with the same name as the csv, and the bodies it lists"""
    logPath = os.path.splitext(result.path)[0] + '.log'
    result.bodies = []
    result.spins = []   #a/M of each body, 0 if the log gives none
    result.frames = None      #the file of the flow's background frames, if it changes with time (engine/background_frames.py)
    result.direction = None   #the flow's direction, if the log names one the backgrounds can draw ('eikonal',
                              #'eikonal-exact')
    if not os.path.exists(logPath):
      result.logText = 'No log file - expected one at\n%s' % logPath
      self.setEnvironment(result)
      return
    with open(logPath) as f:
      result.logText = f.read()
    for m in BODY_LINE.finditer(result.logText):
      result.bodies.append((float(m.group(1)), float(m.group(2)), float(m.group(3)), m.group(4) == 'black'))
      result.spins.append(float(m.group(5)) if m.group(5) else 0.0)
    if 'flow direction: down zero-energy paths' in result.logText:
      result.direction = 'eikonal-exact' if 'exact two-body solution' in result.logText else 'eikonal'
    frames = re.search(r'^background frames: (.+)$', result.logText, re.M)
    if frames:
      result.frames = os.path.join(os.path.dirname(logPath), frames.group(1).strip())
    self.setEnvironment(result)
    self.findOrbits(result)

  def findOrbits(self, result):
    """
    split a run into its orbits, at the times its log says each orbit ended - any run that went round at least once
    (two orbit lines: the part orbit at the start and a whole one); a fall or flyby has none
    the full 'orbit N: t ... s  periapsis ...  apoapsis ...' lines give the apsides too; older logs only have
    'orbit <days> days', and the apsides are then the closest and farthest rows of each orbit
    """
    log, data = re.sub(r'np\.float64\(([^()]*)\)', r'\1', result.logText), result.data   #numbers printed by numpy's repr
    old = result.orbits
    result.orbits, result.orbitMask = [], None
    m = re.search(r'^(?:study|test) type:\s*(\w+)', log, re.M)   #older logs say what they were meant to be
    result.studyType = m.group(1) if m else None
    tcol = self.columnForTime(TIME_COLUMNS[0][0], data)
    if not tcol or not result.selection:
      return
    full = re.findall(r'^orbit \d+: t (\S+) s\s+periapsis \S+ m at \((\S+), (\S+)\)\s+apoapsis \S+ m at \((\S+), (\S+)\)', log, re.M)
    if full:
      ends = [float(f[0]) for f in full]
      apsides = [((float(f[1]), float(f[2])), (float(f[3]), float(f[4]))) for f in full]
    else:
      ends = [float(d) * DAY for d in re.findall(r'^orbit\s+(\S+) days', log, re.M)]
      apsides = [None] * len(ends)
    if len(ends) < 2:
      return   #not round once: no whole orbit
    t = data.values[tcol]
    xcol, ycol = result.selection[0]
    x, y = data.values[xcol], data.values[ycol]
    part = np.searchsorted(np.array(ends), t, side='right')   #0 before the first crossing, k between crossings k and k+1
    for k in range(len(ends) + 1):
      rows = np.nonzero((part == k) & np.isfinite(t))[0]
      if rows.size == 0:
        continue
      t0 = ends[k - 1] if k > 0 else float(t[rows[0]])
      t1 = ends[k] if k < len(ends) else float(t[rows[-1]])
      if k == 0:
        name = 'start (to the first crossing)'
      elif k == len(ends):
        name = 'end (part orbit)'
      else:
        name = 'orbit %d  (%s days)' % (k, formatShort(float('%.6g' % ((t1 - t0) / DAY))))
      d = np.hypot(x[rows], y[rows])
      if k < len(ends) and apsides[k]:
        (px, py), (ax, ay) = apsides[k]
        #the logger keeps where, not when: take the time of the nearest row
        near = lambda qx, qy: float(t[rows[np.argmin(np.hypot(x[rows] - qx, y[rows] - qy))]])
        peri, apo = (px, py, near(px, py)), (ax, ay, near(ax, ay))
      elif np.isfinite(d).any():
        i, j = rows[np.nanargmin(d)], rows[np.nanargmax(d)]
        peri, apo = (float(x[i]), float(y[i]), float(t[i])), (float(x[j]), float(y[j]), float(t[j]))
      else:
        peri = apo = None
      if rows[-1] + 1 < data.nrows:
        rows = np.append(rows, rows[-1] + 1)   #join up with the next orbit
      result.orbits.append(Orbit(result, name, rows, t0, t1, peri, apo))
    result.rowOrbit = np.full(data.nrows, -1)   #the orbit each row is in (its own, not the one it closes)
    for i, o in enumerate(result.orbits):
      result.rowOrbit[o.rows[:-1] if i + 1 < len(result.orbits) else o.rows] = i
    for o in result.orbits:   #a reload keeps which orbits were hidden
      prev = next((p for p in old if p.name.split('  ')[0] == o.name.split('  ')[0]), None)
      if prev is not None:
        o.visible.set(prev.visible.get())
    self.updateOrbitMask(result)

  def updateOrbitMask(self, result):
    """the rows to draw: those of the shown orbits (None when every orbit is shown)"""
    if not result.orbits or all(o.visible.get() for o in result.orbits):
      result.orbitMask = None
      return
    mask = np.zeros(result.data.nrows, dtype=bool)
    for o in result.orbits:
      if o.visible.get():
        mask[o.rows] = True
    result.orbitMask = mask

  def setEnvironment(self, result):
    """the shared Environment for a result's bodies"""
    spins = getattr(result, 'spins', [])
    direction = getattr(result, 'direction', None)
    frames = getattr(result, 'frames', None)
    key = (Environment.key(result.bodies, spins), direction, frames)
    if key not in self.environments:
      self.environments[key] = Environment(result.bodies, spins, direction, frames)
    result.env = self.environments[key]

  def openDialog(self):
    start = os.path.join(ROOT, 'logs')
    paths = filedialog.askopenfilenames(title='Open csv files', initialdir=start if os.path.isdir(start) else None,
                                        filetypes=[('CSV files', '*.csv *.tsv *.txt'), ('All files', '*')])
    if paths:
      self.loadMany(paths)

  def reload(self):
    for r in list(self.results):
      self.load(r.path, refit=False)
    self.redraw()

  def loadMany(self, paths):
    for path in paths:
      self.load(path, refit=False)
    first = next((r for r in self.results if os.path.abspath(r.path) == os.path.abspath(paths[0])), None) if paths else None
    if first:
      self.select(first)   #the first file, not the last, starts selected
    self.fit()

  def load(self, path, refit=True):
    """open a csv as a new tab, or reload it if it is already open"""
    try:
      data = Dataset(path)
    except Exception as e:
      messagebox.showerror('Could not open file', '%s\n\n%s' % (path, e))
      return
    existing = next((r for r in self.results if os.path.abspath(r.path) == os.path.abspath(path)), None)
    if existing and existing.data.names == data.names:
      result = existing
      result.data = data
    else:
      if existing:
        self.closeResult(existing, redraw=False)
        existing = None
      result = Result(data, self.colorCount)
      self.results.append(result)
    self.readLog(result)
    if existing is None:
      self.addTab(result)
    self.updateTimeChoices(resetInterval=existing is None)
    if self.mode.get() == 'time' and self.axisTimeName() is None:
      self.mode.set('xy')   #nothing to plot against
      self.timeInterval.set(self.autoInterval())
    self.buildPaths(result)
    if existing is None:
      self.colorCount += len(result.paths)
      self.refreshList()
      self.select(result)
    self.updateTitle()
    if refit:
      self.fit()
    if not result.paths:
      messagebox.showinfo('No paths found', '%s\n\nCould not find two numeric columns to plot.\nUse Data > Choose paths... to pick columns.' % result.name)

  def closeCurrent(self):
    r = self.current()
    if r:
      self.closeResult(r)

  def closeResult(self, result, redraw=True):
    i = self.results.index(result)
    self.results.remove(result)
    if self.fieldChoice is result:
      self.fieldChoice = None
    if self.selected is result:
      self.selected = self.results[min(i, len(self.results) - 1)] if self.results else None
    self.hover = None
    self.refreshList()
    self.showDetails()
    self.updateTitle()
    if redraw:
      self.redraw()

  def updateTitle(self):
    names = [r.name for r in self.results]
    self.root.title('CSV Viewer' + (' - ' + ', '.join(names) if names else ''))

  def buildPaths(self, result):
    result.paths = []
    d = result.data
    if result.group:
      groups = {}
      for i, g in enumerate(d.text[result.group]):
        groups.setdefault(g, []).append(i)
      groupItems = list(groups.items())
    else:
      groupItems = [(None, list(range(d.nrows)))]
    labels = dict(((x, y), label) for label, x, y in d.pairs())
    for xcol, ycol in result.selection:
      pairName = labels.get((xcol, ycol)) or ('%s / %s' % (xcol, ycol))
      for g, rows in groupItems:
        if g is None:
          name = pairName
        elif len(result.selection) > 1:
          name = '%s %s' % (g, pairName)
        else:
          name = str(g)
        result.paths.append(Path(result, name, xcol, ycol, np.array(rows, dtype=int)))
    for i, p in enumerate(result.paths):
      first = SERIES[(result.colorStart + i) % len(SERIES)]
      last = SERIES[(result.colorStart + i + 4) % len(SERIES)]   #far round the palette, for contrast
      p.color, p.style, p.color2 = result.styles.get(p.name, (first, 'solid', last))
    self.prepare()
    self.updateTab(result)

  def pathLabel(self, p):
    """legend name: the result's name, plus the path's when a result has several"""
    if len(self.results) == 1:
      return p.name
    if len(p.result.paths) == 1:
      return p.result.name
    return '%s %s' % (p.result.name, p.name)
