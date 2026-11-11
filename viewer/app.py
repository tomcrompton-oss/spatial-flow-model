"""the window: the menus, the option tabs, events and dialogs, and the Viewer class that combines the rest"""
from viewer.common import *
from viewer.panel import ResultsPanel
from viewer.loading import Loading
from viewer.view import View
from viewer.drawing import Drawing
from viewer.backgrounds import Backgrounds
from viewer.replay import Replay
from viewer.sim_tab import SimTab
from viewer.config_tab import ConfigTab


class Viewer(ResultsPanel, Loading, View, Drawing, Backgrounds, Replay, SimTab, ConfigTab):


  def __init__(self, root, paths=None):
    self.root = root
    self.results = []
    self.environments = {}   #(Environment.key(bodies), flow direction) -> Environment, shared by results with the same bodies
    self.colorCount = 0   #paths coloured so far, so each new path gets the next colour
    self.view = [0.0, 1.0, 0.0, 1.0]   #xmin, xmax, ymin, ymax in plotted (unit, log) space
    self.plotSize = None
    self.hover = None
    self.drag = None

    self.logX = tk.BooleanVar(value=False)
    self.logY = tk.BooleanVar(value=False)
    self.unit = tk.IntVar(value=0)
    self.equalAspect = tk.BooleanVar(value=True)
    self.ctTime = tk.BooleanVar(value=False)   #distance / time mode: time as ct, in the distance unit, on a 1:1 scale
    self.showGrid = tk.BooleanVar(value=True)
    self.showMarkers = tk.BooleanVar(value=True)
    self.showTimeMarks = tk.BooleanVar(value=True)
    #legends and labels, each shown or hidden from the Legends tab
    self.showPathLegend = tk.BooleanVar(value=True)    #path names and colours, top right
    self.showFieldKey = tk.BooleanVar(value=True)      #what the backgrounds mean, bottom left
    self.showMarkNote = tk.BooleanVar(value=True)      #'every N of t' above the plot
    self.showMarkLabels = tk.BooleanVar(value=True)    #the time beside each time marker
    self.showBodyLabels = tk.BooleanVar(value=True)    #each body's mass
    self.timeColumn = tk.StringVar(value=TIME_COLUMNS[0][0])
    self.timeInterval = tk.StringVar(value='')
    self.showSidebar = tk.BooleanVar(value=True)
    #replay: 'stopped' shows every path in full; 'playing' or 'paused' shows each path's trail, from
    #trailStart to replayT in global time (s)
    self.replayState = 'stopped'
    self.replayT = None
    self.trailStart = None
    self.replayJob = None
    self.replaySpeed = tk.StringVar(value='1×')
    self.replayPos = tk.DoubleVar(value=0.0)   #the slider, 0 to 1 through the time span
    self.mode = tk.StringVar(value='xy')
    self.showBodies = tk.BooleanVar(value=True)
    self.showFlow = tk.BooleanVar(value=True)
    self.showGravity = tk.BooleanVar(value=False)
    self.showContours = tk.BooleanVar(value=False)
    self.showCones = tk.BooleanVar(value=False)
    self.showFlowLines = tk.BooleanVar(value=False)
    self.showSchwarzschild = tk.BooleanVar(value=False)
    self.showTwist = tk.BooleanVar(value=False)
    self.showSpecialOrbits = tk.BooleanVar(value=False)
    self.reverseX = tk.BooleanVar(value=True)   #distance / time mode: distance runs right to left, 0 on the right
    self.timeNote = ''

    root.title('CSV Viewer')
    root.geometry('1400x800')
    root.configure(bg=PAGE)
    self.simInit()
    self.buildMenu()
    self.buildToolbar()
    self.status = tk.Label(root, anchor='w', bg=PAGE, fg=INK2, padx=8, pady=4)
    self.status.pack(side='bottom', fill='x')
    self.simStrip()
    self.panes = ttk.Panedwindow(root, orient='horizontal')
    self.panes.pack(fill='both', expand=True)
    self.canvas = tk.Canvas(self.panes, bg=PAGE, highlightthickness=0, cursor='crosshair', width=1000)
    self.panes.add(self.canvas, weight=1)
    self.buildSidebar()
    self.bindEvents()
    root.after(200, self.sidebarChanged)   #place the panel once the window has its size

    if paths:
      root.after(50, lambda: self.loadMany(paths))
    else:
      self.drawEmpty()
    root.after(600, self.simPickUp)   #sims started from an earlier viewer

  @property
  def paths(self):
    """paths of the results that are shown"""
    return [p for r in self.results if r.visible.get() for p in r.paths]

  def allPaths(self):
    return [p for r in self.results for p in r.paths]

  def current(self):
    """the result selected in the results list"""
    if not self.results:
      return None
    return self.selected if self.selected in self.results else self.results[0]

  def buildMenu(self):
    mod = 'Command' if sys.platform == 'darwin' else 'Control'
    acc = 'Cmd' if sys.platform == 'darwin' else 'Ctrl'
    menu = tk.Menu(self.root)

    fileMenu = tk.Menu(menu, tearoff=0)
    fileMenu.add_command(label='Open (adds tabs)...', accelerator=acc + '+O', command=self.openDialog)
    fileMenu.add_command(label='Reload all', accelerator=acc + '+R', command=self.reload)
    fileMenu.add_command(label='Close result', accelerator=acc + '+W', command=self.closeCurrent)
    fileMenu.add_separator()
    fileMenu.add_command(label='Quit', command=self.root.destroy)
    menu.add_cascade(label='File', menu=fileMenu)

    viewMenu = tk.Menu(menu, tearoff=0)
    for value, label in MODES:
      viewMenu.add_radiobutton(label=label, variable=self.mode, value=value, command=self.modeChanged)
    viewMenu.add_separator()
    viewMenu.add_command(label='Zoom in', accelerator='+', command=lambda: self.zoom(1 / ZOOM_STEP))
    viewMenu.add_command(label='Zoom out', accelerator='-', command=lambda: self.zoom(ZOOM_STEP))
    viewMenu.add_command(label='Fit to data', accelerator='0', command=self.fit)
    viewMenu.add_command(label='Set range...', command=self.rangeDialog)
    viewMenu.add_separator()
    viewMenu.add_command(label='Pan left', accelerator='Left', command=lambda: self.pan(-PAN_STEP, 0))
    viewMenu.add_command(label='Pan right', accelerator='Right', command=lambda: self.pan(PAN_STEP, 0))
    viewMenu.add_command(label='Pan up', accelerator='Up', command=lambda: self.pan(0, PAN_STEP))
    viewMenu.add_command(label='Pan down', accelerator='Down', command=lambda: self.pan(0, -PAN_STEP))
    viewMenu.add_separator()
    viewMenu.add_checkbutton(label='Grid', variable=self.showGrid, command=self.redraw)
    viewMenu.add_checkbutton(label='Start / end markers', variable=self.showMarkers, command=self.redraw)
    viewMenu.add_checkbutton(label='Bodies', variable=self.showBodies, command=self.redraw)
    viewMenu.add_checkbutton(label='Flow arrows (u)', variable=self.showFlow, command=self.redraw)
    viewMenu.add_checkbutton(label='Gravity arrows (g)', variable=self.showGravity, command=self.redraw)
    viewMenu.add_checkbutton(label='Lines of equal u', variable=self.showContours, command=self.redraw)
    viewMenu.add_checkbutton(label='Flow lines', variable=self.showFlowLines, command=self.redraw)
    viewMenu.add_checkbutton(label='Horizon (and a rotating hole\'s ergosphere and ring)', variable=self.showSchwarzschild, command=self.redraw)
    viewMenu.add_checkbutton(label='Twist arcs (rotating hole)', variable=self.showTwist, command=self.redraw)
    viewMenu.add_checkbutton(label='Photon orbits and ISCO (one hole)', variable=self.showSpecialOrbits, command=self.redraw)
    viewMenu.add_checkbutton(label='Reverse distance axis (distance / time)', variable=self.reverseX, command=self.redraw)
    viewMenu.add_checkbutton(label='Light cones (distance / time)', variable=self.showCones, command=self.redraw)
    legendMenu = tk.Menu(viewMenu, tearoff=0)
    for text, var in self.legendOptions():
      legendMenu.add_checkbutton(label=text, variable=var, command=self.redraw)
    viewMenu.add_cascade(label='Legends', menu=legendMenu)
    viewMenu.add_checkbutton(label='Results panel', accelerator=acc + '+L', variable=self.showSidebar, command=self.sidebarChanged)
    menu.add_cascade(label='View', menu=viewMenu)

    timeMenu = tk.Menu(menu, tearoff=0)
    timeMenu.add_checkbutton(label='Show time markers', variable=self.showTimeMarks, command=self.timeChanged)
    timeMenu.add_separator()
    timeMenu.add_command(label='Markers use', state='disabled')
    self.timeMenu = timeMenu
    self.timeMenuHeader = timeMenu.index('end')
    for label, _ in TIME_COLUMNS:
      timeMenu.add_radiobutton(label=label, variable=self.timeColumn, value=label, command=self.timeColumnChanged)
    timeMenu.add_separator()
    timeMenu.add_command(label='Set interval...', command=self.intervalDialog)
    timeMenu.add_command(label='Automatic interval', command=self.timeColumnChanged)
    menu.add_cascade(label='Time', menu=timeMenu)

    scaleMenu = tk.Menu(menu, tearoff=0)
    scaleMenu.add_command(label='X axis', state='disabled')
    scaleMenu.add_radiobutton(label='  Linear', variable=self.logX, value=False, command=self.scaleChanged)
    scaleMenu.add_radiobutton(label='  Logarithmic', variable=self.logX, value=True, command=self.scaleChanged)
    scaleMenu.add_command(label='Y axis', state='disabled')
    scaleMenu.add_radiobutton(label='  Linear', variable=self.logY, value=False, command=self.scaleChanged)
    scaleMenu.add_radiobutton(label='  Logarithmic', variable=self.logY, value=True, command=self.scaleChanged)
    scaleMenu.add_separator()
    scaleMenu.add_command(label='Units (csv in metres)', state='disabled')
    for i, (label, _, _) in enumerate(UNITS):
      scaleMenu.add_radiobutton(label='  ' + label, variable=self.unit, value=i, command=self.scaleChanged)
    scaleMenu.add_separator()
    scaleMenu.add_checkbutton(label='Equal aspect (1:1)', variable=self.equalAspect, command=self.aspectChanged)
    self.scaleMenu, self.aspectMenuIndex = scaleMenu, scaleMenu.index('end')
    menu.add_cascade(label='Scale', menu=scaleMenu)

    dataMenu = tk.Menu(menu, tearoff=0)
    dataMenu.add_command(label='Choose paths (selected tab)...', command=self.pathsDialog)
    menu.add_cascade(label='Data', menu=dataMenu)

    self.root.config(menu=menu)
    self.root.bind('<%s-o>' % mod, lambda e: self.openDialog())
    self.root.bind('<%s-r>' % mod, lambda e: self.reload())
    self.root.bind('<%s-w>' % mod, lambda e: self.closeCurrent())
    self.root.bind('<%s-l>' % mod, lambda e: self.toggleSidebar())

  def buildToolbar(self):
    """the options, grouped in tabs along the top"""
    style = ttk.Style()
    style.configure('Options.TFrame', background=PAGE)
    self.options = ttk.Notebook(self.root)
    self.options.pack(fill='x', padx=6, pady=(6, 4))
    self.optionTips = TabTips(self.options, TAB_TIPS)

    def tab(name):
      frame = ttk.Frame(self.options, style='Options.TFrame', padding=(6, 6))
      self.options.add(frame, text=name)
      return frame
    def button(parent, text, command, hover=None):
      widget = ttk.Button(parent, text=text, command=command, width=len(text) + 2 if len(text) > 2 else 3)
      widget.pack(side='left', padx=2)
      return tip(widget, hover or TIPS.get(text))
    def check(parent, text, variable, command, hover=None):
      widget = ttk.Checkbutton(parent, text=text, variable=variable, command=command)
      widget.pack(side='left', padx=4)
      return tip(widget, hover or TIPS.get(text))
    def label(parent, text):
      widget = tk.Label(parent, text=text, bg=PAGE, fg=INK2)
      widget.pack(side='left', padx=(10, 2))
      return widget
    def gap(parent):
      ttk.Separator(parent, orient='vertical').pack(side='left', fill='y', padx=8)
    self.timeBoxes = []
    def timeBox(parent):
      box = ttk.Combobox(parent, state='readonly', width=16, textvariable=self.timeColumn, values=[t[0] for t in TIME_COLUMNS])
      box.bind('<<ComboboxSelected>>', lambda e: self.timeColumnChanged())
      box.pack(side='left', padx=4)
      self.timeBoxes.append(box)

    data = tab('Data')
    button(data, 'Open...', self.openDialog)
    button(data, 'Reload all', self.reload)
    button(data, 'Close result', self.closeCurrent)
    gap(data)
    button(data, 'Choose paths...', self.pathsDialog)

    mode = tab('Mode')
    for value, text in MODES:
      tip(ttk.Radiobutton(mode, text=text, variable=self.mode, value=value, command=self.modeChanged), TIPS.get(text)).pack(side='left', padx=4)
    gap(mode)
    label(mode, 'Time axis (distance / time)')
    timeBox(mode)
    gap(mode)
    check(mode, 'Reverse distance (0 on the right)', self.reverseX, self.redraw)

    position = tab('Position')
    button(position, 'Zoom in', lambda: self.zoom(1 / ZOOM_STEP))
    button(position, 'Zoom out', lambda: self.zoom(ZOOM_STEP))
    button(position, 'Fit', self.fit)
    gap(position)
    button(position, '\u2190', lambda: self.pan(-PAN_STEP, 0))
    button(position, '\u2192', lambda: self.pan(PAN_STEP, 0))
    button(position, '\u2191', lambda: self.pan(0, PAN_STEP))
    button(position, '\u2193', lambda: self.pan(0, -PAN_STEP))
    gap(position)
    button(position, 'Set range...', self.rangeDialog)

    axis = tab('Axis')
    #equal aspect in x / y mode, ct in distance / time mode (updateAspectOption swaps them)
    self.aspectCheck = ttk.Checkbutton(axis, text='Equal aspect', variable=self.equalAspect, command=self.aspectChanged)
    self.aspectCheck.pack(side='left', padx=4)
    tip(self.aspectCheck, TIPS['Equal aspect'])
    check(axis, 'Log X', self.logX, self.scaleChanged)
    check(axis, 'Log Y', self.logY, self.scaleChanged)
    check(axis, 'Grid', self.showGrid, self.redraw)
    label(axis, 'Units')
    self.unitBox = ttk.Combobox(axis, state='readonly', width=18, values=[u[0] for u in UNITS])
    self.unitBox.current(0)
    self.unitBox.bind('<<ComboboxSelected>>', lambda e: (self.unit.set(self.unitBox.current()), self.scaleChanged()))
    self.unitBox.pack(side='left')

    markers = tab('Markers')
    check(markers, 'Time markers', self.showTimeMarks, self.timeChanged)
    self.timeLabel = label(markers, 'Markers use')
    timeBox(markers)
    self.everyLabel = label(markers, 'every')
    entry = ttk.Entry(markers, width=10, textvariable=self.timeInterval)
    entry.bind('<Return>', lambda e: self.timeChanged())
    entry.pack(side='left')
    button(markers, 'Apply', self.timeChanged)
    button(markers, 'Auto', self.timeColumnChanged)
    gap(markers)
    check(markers, 'Start / end markers', self.showMarkers, self.redraw)

    backgrounds = tab('Backgrounds')
    check(backgrounds, 'Bodies', self.showBodies, self.redraw)
    check(backgrounds, 'u arrows', self.showFlow, self.redraw)
    check(backgrounds, 'g arrows', self.showGravity, self.redraw)
    check(backgrounds, 'Lines of equal u', self.showContours, self.redraw)
    check(backgrounds, 'Flow lines', self.showFlowLines, self.redraw)
    check(backgrounds, 'Horizon', self.showSchwarzschild, self.redraw)
    check(backgrounds, 'Twist arcs', self.showTwist, self.redraw)
    check(backgrounds, 'Photon orbits / ISCO', self.showSpecialOrbits, self.redraw)
    check(backgrounds, 'Light cones (distance / time)', self.showCones, self.redraw)
    label(backgrounds, 'for the environment picked in the results panel; in distance / time mode along the line from the origin')

    replay = tab('Replay')
    button(replay, '▶ Play', self.replayPlay)
    button(replay, '❚❚ Pause', self.replayPause)
    button(replay, '⏮ Rewind', self.replayRewind)
    button(replay, '■ Stop', self.replayStop)
    gap(replay)
    label(replay, 'Speed')
    speed = ttk.Combobox(replay, state='readonly', width=6, values=REPLAY_SPEEDS, textvariable=self.replaySpeed)
    speed.pack(side='left')
    tip(speed, '1× plays the whole time span in %d seconds' % REPLAY_SECONDS)
    gap(replay)
    button(replay, 'Clear trails', self.replayClear)
    button(replay, 'Restore trails', self.replayRestore)
    gap(replay)
    self.replayScale = ttk.Scale(replay, from_=0.0, to=1.0, orient='horizontal', length=180, variable=self.replayPos,
                                 command=lambda v: self.replaySeek(float(v)))
    self.replayScale.pack(side='left', padx=4)
    tip(self.replayScale, 'Drag to jump to any point in the replay')
    self.replayLabel = label(replay, 'stopped - 1× plays the whole run in %d s' % REPLAY_SECONDS)

    legends = tab('Legends')
    for text, var in self.legendOptions():
      check(legends, text, var, self.redraw)
    gap(legends)
    button(legends, 'All', lambda: self.setLegends(True), 'Show every legend and label')
    button(legends, 'None', lambda: self.setLegends(False), 'Hide every legend and label')

    self.simTab(tab('Sim'), button, label, gap)
    self.configTab(tab('Config'), button, label, gap)

  def legendOptions(self):
    return [('Path legend', self.showPathLegend), ('Background key', self.showFieldKey),
            ('Marker interval', self.showMarkNote), ('Marker times', self.showMarkLabels), ('Body labels', self.showBodyLabels)]

  def setLegends(self, on):
    for _, var in self.legendOptions():
      var.set(on)
    self.redraw()

  def bindEvents(self):
    c = self.canvas
    c.bind('<Configure>', self.onResize)
    c.bind('<ButtonPress-1>', self.onPress)
    c.bind('<Shift-ButtonPress-1>', self.onBoxPress)
    c.bind('<B1-Motion>', self.onDrag)
    c.bind('<ButtonRelease-1>', self.onRelease)
    c.bind('<Motion>', self.onMotion)
    c.bind('<Leave>', lambda e: self.setHover(None))
    c.bind('<MouseWheel>', self.onWheel)
    c.bind('<Button-4>', lambda e: self.zoomAt(1 / 1.2, e.x, e.y))
    c.bind('<Button-5>', lambda e: self.zoomAt(1.2, e.x, e.y))
    def key(sequence, action):
      #ignore keys typed into entry boxes and the log text
      self.root.bind(sequence, lambda e: None if isinstance(e.widget, (tk.Entry, ttk.Entry, tk.Text)) else action())
    for sequence in ('<plus>', '<equal>', '<KP_Add>'):
      key(sequence, lambda: self.zoom(1 / ZOOM_STEP))
    for sequence in ('<minus>', '<KP_Subtract>'):
      key(sequence, lambda: self.zoom(ZOOM_STEP))
    key('<Left>', lambda: self.pan(-PAN_STEP, 0))
    key('<Right>', lambda: self.pan(PAN_STEP, 0))
    key('<Up>', lambda: self.pan(0, PAN_STEP))
    key('<Down>', lambda: self.pan(0, -PAN_STEP))
    key('0', self.fit)
    key('f', self.fit)

  def onResize(self, event):
    l, t, r, b = self.plotRect()
    size = (r - l, b - t)
    if self.plotSize and self.results:
      #keep the same units per pixel, growing or shrinking the view around its centre
      ow, oh = self.plotSize
      x0, x1, y0, y1 = self.view
      cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
      hx, hy = (x1 - x0) / 2 * size[0] / ow, (y1 - y0) / 2 * size[1] / oh
      self.view = [cx - hx, cx + hx, cy - hy, cy + hy]
    self.plotSize = size
    self.redraw()

  def onPress(self, event):
    self.drag = ('pan', event.x, event.y, list(self.view))
    self.canvas.config(cursor='fleur')

  def onBoxPress(self, event):
    self.drag = ('box', event.x, event.y, None)

  def onDrag(self, event):
    if not self.drag or not self.results:
      return
    kind, sx, sy, view = self.drag
    if kind == 'pan':
      l, t, r, b = self.plotRect()
      x0, x1, y0, y1 = view
      dx = self.xSign() * (event.x - sx) * (x1 - x0) / (r - l)
      dy = (event.y - sy) * (y1 - y0) / (b - t)
      self.view = [x0 - dx, x1 - dx, y0 + dy, y1 + dy]
      self.hover = None
      self.requestRedraw()
    else:
      self.canvas.delete('box')
      self.canvas.create_rectangle(sx, sy, event.x, event.y, outline=INK2, dash=(4, 3), tags='box')

  def onRelease(self, event):
    drag, self.drag = self.drag, None
    self.canvas.config(cursor='crosshair')
    if not drag or drag[0] != 'box' or not self.results:
      return
    _, sx, sy, _ = drag
    self.canvas.delete('box')
    if abs(event.x - sx) < 5 or abs(event.y - sy) < 5:
      return
    ax, ay = self.toData(min(sx, event.x), max(sy, event.y))
    bx, by = self.toData(max(sx, event.x), min(sy, event.y))
    self.view = [min(ax, bx), max(ax, bx), ay, by]
    self.applyAspect()
    self.redraw()

  def onWheel(self, event):
    if event.delta == 0:
      return
    self.zoomAt(1 / 1.15 if event.delta > 0 else 1.15, event.x, event.y)

  def onMotion(self, event):
    if self.drag or not self.results:
      return
    found = self.nearest(event.x, event.y)
    self.setHover(found[1:] if found else None)
    self.updateStatus(event.x, event.y)

  def updateStatus(self, mx=None, my=None):
    shown = [r for r in self.results if r.visible.get()]
    text = '%d of %d results shown   %d rows   %d paths' % (len(shown), len(self.results), sum(r.data.nrows for r in shown), len(self.paths))
    l, t, r, b = self.plotRect()
    if mx is not None and l <= mx <= r and t <= my <= b:
      x, y = self.toData(mx, my)
      x, y = self.fromPlot(x, self.logX.get()), self.fromPlot(y, self.logY.get())
      unit = UNITS[self.unit.get()][2]
      if self.mode.get() == 'time':
        tname = ('ct' if self.axisTimeName() == 't' else 'c·%s' % self.axisTimeName()) if self.ctTime.get() else self.axisTimeName()
        text = 'distance = %s %s   %s = %s%s      ' % (formatValue(x), unit, tname, formatValue(y), ' ' + unit if self.ctTime.get() else '') + text
      else:
        text = 'x = %s %s   y = %s %s      ' % (formatValue(x), unit, formatValue(y), unit) + text
    self.status.config(text=text)

  def rangeDialog(self):
    if not self.results:
      return
    dlg = tk.Toplevel(self.root)
    dlg.title('Set range')
    dlg.transient(self.root)
    dlg.resizable(False, False)
    lx, ly = self.logX.get(), self.logY.get()
    x0, x1, y0, y1 = self.view
    current = [self.fromPlot(x0, lx), self.fromPlot(x1, lx), self.fromPlot(y0, ly), self.fromPlot(y1, ly)]
    entries = []
    for i, label in enumerate(('X min', 'X max', 'Y min', 'Y max')):
      ttk.Label(dlg, text=label).grid(row=i, column=0, padx=10, pady=4, sticky='e')
      e = ttk.Entry(dlg, width=24)
      e.insert(0, formatValue(current[i]))
      e.grid(row=i, column=1, padx=10, pady=4)
      entries.append(e)
    unit = UNITS[self.unit.get()][2]
    ttk.Label(dlg, text='values in %s' % (unit or 'raw units'), foreground=MUTED).grid(row=4, column=0, columnspan=2)

    def apply():
      try:
        v = [float(e.get()) for e in entries]
      except ValueError:
        messagebox.showerror('Set range', 'Enter numbers for all four values', parent=dlg)
        return
      if not (v[1] > v[0] and v[3] > v[2]) or (lx and v[0] <= 0) or (ly and v[2] <= 0):
        messagebox.showerror('Set range', 'Max must be greater than min (and above 0 on a log axis)', parent=dlg)
        return
      tx = (lambda a: math.log10(a)) if lx else (lambda a: a)
      ty = (lambda a: math.log10(a)) if ly else (lambda a: a)
      self.view = [tx(v[0]), tx(v[1]), ty(v[2]), ty(v[3])]
      if self.aspectActive() and self.mode.get() == 'xy':
        self.equalAspect.set(False)   #an exact range wins over equal aspect
      dlg.destroy()
      self.redraw()

    buttons = ttk.Frame(dlg)
    buttons.grid(row=5, column=0, columnspan=2, pady=10)
    ttk.Button(buttons, text='Cancel', command=dlg.destroy).pack(side='left', padx=4)
    ttk.Button(buttons, text='Apply', command=apply).pack(side='left', padx=4)
    dlg.bind('<Return>', lambda e: apply())
    dlg.bind('<Escape>', lambda e: dlg.destroy())
    entries[0].focus_set()

  def pathsDialog(self):
    result = self.current()
    if result is None:
      return
    d = result.data
    dlg = tk.Toplevel(self.root)
    dlg.title('Choose paths - ' + result.name)
    dlg.transient(self.root)

    ttk.Label(dlg, text='Detected x/y column pairs').grid(row=0, column=0, columnspan=4, sticky='w', padx=10, pady=(10, 4))
    chosen = list(result.selection)
    pairVars = []
    listFrame = ttk.Frame(dlg)
    listFrame.grid(row=1, column=0, columnspan=4, sticky='w', padx=16)

    def refreshList():
      for child in listFrame.winfo_children():
        child.destroy()
      pairVars.clear()
      options = [(x, y) for _, x, y in d.pairs()]
      options += [s for s in chosen if s not in options]
      if not options:
        ttk.Label(listFrame, text='none found - add a pair below', foreground=MUTED).pack(anchor='w')
      for x, y in options:
        v = tk.BooleanVar(value=(x, y) in chosen)
        ttk.Checkbutton(listFrame, text='%s  vs  %s' % (y, x), variable=v).pack(anchor='w')
        pairVars.append(((x, y), v))

    refreshList()

    ttk.Label(dlg, text='Add a pair').grid(row=2, column=0, columnspan=4, sticky='w', padx=10, pady=(12, 4))
    ttk.Label(dlg, text='X').grid(row=3, column=0, sticky='e', padx=(16, 4))
    xBox = ttk.Combobox(dlg, state='readonly', values=d.numeric, width=16)
    xBox.grid(row=3, column=1, pady=2)
    ttk.Label(dlg, text='Y').grid(row=3, column=2, sticky='e', padx=(10, 4))
    yBox = ttk.Combobox(dlg, state='readonly', values=d.numeric, width=16)
    yBox.grid(row=3, column=3, pady=2, padx=(0, 10))
    if len(d.numeric) >= 2:
      xBox.current(0)
      yBox.current(1)

    def addPair():
      pair = (xBox.get(), yBox.get())
      if pair[0] and pair[1]:
        for s, v in pairVars:
          chosen[:] = [p for p in chosen if p != s] + ([s] if v.get() else [])
        if pair not in chosen:
          chosen.append(pair)
        refreshList()
    ttk.Button(dlg, text='Add', command=addPair).grid(row=4, column=3, sticky='e', padx=10, pady=4)

    ttk.Label(dlg, text='One path per value of').grid(row=5, column=0, columnspan=2, sticky='w', padx=10, pady=(12, 4))
    groupOptions = ['(none)'] + [n for n in d.names]
    groupBox = ttk.Combobox(dlg, state='readonly', values=groupOptions, width=16)
    groupBox.current(groupOptions.index(result.group) if result.group in groupOptions else 0)
    groupBox.grid(row=5, column=2, columnspan=2, sticky='w', pady=(12, 4))

    def apply():
      selection = [s for s, v in pairVars if v.get()]
      if not selection:
        messagebox.showerror('Choose paths', 'Select at least one pair', parent=dlg)
        return
      result.selection = selection
      result.group = None if groupBox.current() <= 0 else groupBox.get()
      dlg.destroy()
      self.buildPaths(result)
      self.fit()

    buttons = ttk.Frame(dlg)
    buttons.grid(row=6, column=0, columnspan=4, pady=12)
    ttk.Button(buttons, text='Cancel', command=dlg.destroy).pack(side='left', padx=4)
    ttk.Button(buttons, text='Apply', command=apply).pack(side='left', padx=4)
    dlg.bind('<Escape>', lambda e: dlg.destroy())

  def intervalDialog(self):
    dlg = tk.Toplevel(self.root)
    dlg.title('Time marker interval')
    dlg.transient(self.root)
    dlg.resizable(False, False)
    col = self.timeColumnName() or 'time'
    ttk.Label(dlg, text='Marker every').grid(row=0, column=0, padx=10, pady=10)
    entry = ttk.Entry(dlg, width=14)
    entry.insert(0, self.timeInterval.get())
    entry.grid(row=0, column=1, pady=10)
    ttk.Label(dlg, text='of %s' % col).grid(row=0, column=2, padx=10)
    def apply():
      self.timeInterval.set(entry.get().strip())
      self.showTimeMarks.set(True)
      dlg.destroy()
      self.timeChanged()
    buttons = ttk.Frame(dlg)
    buttons.grid(row=1, column=0, columnspan=3, pady=(0, 10))
    ttk.Button(buttons, text='Cancel', command=dlg.destroy).pack(side='left', padx=4)
    ttk.Button(buttons, text='Apply', command=apply).pack(side='left', padx=4)
    dlg.bind('<Return>', lambda e: apply())
    dlg.bind('<Escape>', lambda e: dlg.destroy())
    entry.focus_set()
    entry.select_range(0, 'end')
