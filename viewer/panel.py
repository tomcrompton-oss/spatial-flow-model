"""the results panel: the list of results (by environment, folder and orbit), the selected result's options, path styles, summary and log"""
from viewer.common import *


class ResultsPanel:
  """mixed into Viewer (viewer/app.py)"""

  def buildSidebar(self):
    """
    the results panel: a toggle button that always shows, and beside it a list of the loaded results
    (grouped by folder), a choice of which result's bodies the backgrounds come from, and the selected
    result's options and log
    """
    self.sidebar = tk.Frame(self.panes, bg=PAGE)
    self.sidebarButton = tk.Button(self.sidebar, command=self.toggleSidebar, relief='flat', bd=0, bg=GRID,
                                   activebackground=AXIS, fg=INK2, font=('Helvetica', 11), width=2, cursor='hand2')
    self.sidebarButton.pack(side='left', fill='y')
    tip(self.sidebarButton, 'Show or hide the results panel')
    self.sidebarContent = tk.Frame(self.sidebar, bg=PAGE, width=400)
    content = self.sidebarContent

    bar = tk.Frame(content, bg=PAGE)
    bar.pack(fill='x', padx=(6, 0), pady=(6, 2))
    for text, command in (('All', lambda: self.setVisible(self.results, True)),
                          ('None', lambda: self.setVisible(self.results, False)),
                          ('Only selected', self.showOnlySelected),
                          ('Close', self.closeSelected)):
      tip(ttk.Button(bar, text=text, command=command), {'All': 'Show every result', 'None': 'Hide every result'}.get(text, TIPS.get(text))).pack(side='left', padx=(0, 4))

    choose = tk.Frame(content, bg=PAGE)
    choose.pack(fill='x', padx=(6, 0), pady=(2, 4))
    tk.Label(choose, text='Background', bg=PAGE, fg=INK2).pack(side='left')
    self.fieldBox = ttk.Combobox(choose, state='readonly', width=30)
    self.fieldBox.bind('<<ComboboxSelected>>', lambda e: self.fieldChoiceChanged())
    self.fieldBox.pack(side='left', fill='x', expand=True, padx=(6, 0))
    tip(self.fieldBox, 'The environment (bodies) the backgrounds are drawn for; by default the selected result\'s')

    split = ttk.Panedwindow(content, orient='vertical')
    split.pack(fill='both', expand=True, padx=(6, 0))
    listFrame = tk.Frame(split, bg=PAGE)
    style = ttk.Style()
    style.configure('Results.Treeview', rowheight=22, font=('Helvetica', 11))
    style.configure('Results.Treeview.Heading', font=('Helvetica', 10))
    self.list = ttk.Treeview(listFrame, columns=('show', 'rows', 'end'), style='Results.Treeview', selectmode='extended', height=8)
    self.list.heading('#0', text='Result', anchor='w')
    self.list.heading('show', text='Shown')
    self.list.heading('rows', text='Rows')
    self.list.heading('end', text='End t')
    self.list.column('#0', width=190, stretch=True)
    self.list.column('show', width=50, anchor='center', stretch=False)
    self.list.column('rows', width=60, anchor='e', stretch=False)
    self.list.column('end', width=80, anchor='e', stretch=False)
    scroll = ttk.Scrollbar(listFrame, orient='vertical', command=self.list.yview)
    self.list.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right', fill='y')
    self.list.pack(fill='both', expand=True)
    self.list.bind('<<TreeviewSelect>>', lambda e: self.listSelected())
    self.list.bind('<Button-1>', self.listClicked)
    self.list.bind('<space>', lambda e: self.toggleSelected())
    self.list.bind('<Double-Button-1>', lambda e: self.showOnlySelected())
    tip(self.list, 'Click a Shown cell (or press space) to show or hide a row; double click to show only that row')
    self.noResults = tk.Label(listFrame, text='No results loaded\nData > Open... adds csv files', bg=SURFACE, fg=INK2, pady=20)
    self.noResults.place(relx=0.5, rely=0.3, anchor='n')
    split.add(listFrame, weight=1)

    #the selected result: its options, file and log
    self.details = tk.Frame(split, bg=PAGE)
    self.detailOptions = tk.Frame(self.details, bg=PAGE)
    self.detailOptions.pack(fill='x', pady=(6, 2))
    self.detailPath = tk.Label(self.details, text='', anchor='w', bg=PAGE, fg=MUTED, font=('Helvetica', 10), justify='left')
    self.detailPath.pack(fill='x')
    self.detailPaths = tk.Frame(self.details, bg=PAGE)   #a colour and line style for each path
    self.detailPaths.pack(fill='x', pady=(4, 0))
    self.summary = tk.Frame(self.details, bg=SURFACE, highlightthickness=1, highlightbackground=AXIS)
    self.summary.pack(fill='x', pady=(6, 0))
    body = tk.Frame(self.details, bg=PAGE)
    body.pack(fill='both', expand=True, pady=(4, 0))
    self.logWidget = tk.Text(body, wrap='none', font=('Menlo', 11), bg=SURFACE, fg=INK, relief='flat',
                             highlightthickness=1, highlightbackground=AXIS, padx=8, pady=6, width=46, state='disabled')
    yscroll = ttk.Scrollbar(body, orient='vertical', command=self.logWidget.yview)
    xscroll = ttk.Scrollbar(body, orient='horizontal', command=self.logWidget.xview)
    self.logWidget.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
    yscroll.pack(side='right', fill='y')
    xscroll.pack(side='bottom', fill='x')
    self.logWidget.pack(fill='both', expand=True)
    split.add(self.details, weight=2)

    self.selected = None        #the result whose options and log are shown
    self.fieldChoice = None     #the result the backgrounds come from, or None for automatic
    self.listItems = {}         #tree item -> result, or list of results for a folder
    self.panes.add(self.sidebar, weight=0)
    self.sidebarWidth = 460
    self.sidebarChanged()

  def addTab(self, result):
    self.refreshList()

  def updateTab(self, result):
    """refresh the list row (and the details, if selected) of a result after its paths change"""
    self.refreshList()
    if result is self.selected:
      self.showDetails()

  @staticmethod
  def swatch(colors):
    """a small image striped with the colours of a result's paths"""
    w, h = 16, 10
    img = tk.PhotoImage(width=w, height=h)
    colors = colors or [AXIS]
    for i, color in enumerate(colors[:4]):
      x0, x1 = i * w // min(len(colors), 4), (i + 1) * w // min(len(colors), 4)
      img.put(color, to=(x0, 1, x1, h - 1))
    return img

  def resultEnd(self, result):
    """the last global time in a result, as text"""
    col = self.columnForTime(TIME_COLUMNS[0][0], result.data)
    if not col:
      return ''
    t = result.data.values[col]
    t = t[np.isfinite(t)]
    return formatValue(float(t[-1])) if t.size else ''

  def resultGroups(self):
    """(folder, results) in load order; a folder holding one result is not grouped"""
    groups = {}
    for r in self.results:
      groups.setdefault(os.path.dirname(os.path.abspath(r.path)), []).append(r)
    return list(groups.items())

  def refreshList(self):
    """
    rebuild the results list - environments (the same bodies), then folders, then results - keeping the
    selection and which rows are open
    """
    tree = self.list
    keys = getattr(self, 'itemKeys', {})
    opened = {k for i, k in keys.items() if tree.exists(i) and tree.item(i, 'open')}
    known = set(keys.values())
    tree.delete(*tree.get_children())
    self.listItems = {}
    self.itemKeys = {}   #tree item -> a name that lasts through a rebuild, to keep rows open or closed
    self.envItems = {}
    self.swatches = []   #keep the images alive

    def group(parent, text, results, key):
      shown = sum(r.visible.get() for r in results)
      mark = '✓' if shown == len(results) else ('–' if shown else '')
      item = tree.insert(parent, 'end', text=text, values=(mark, '%d file%s' % (len(results), '' if len(results) == 1 else 's'), ''),
                         open=key in opened or key not in known)
      self.listItems[item] = results
      self.itemKeys[item] = key
      return item

    for env in self.activeEnvironments():
      envResults = [r for r in self.results if r.env is env]
      envItem = group('', env.name, envResults, 'env:' + env.name)
      self.envItems[envItem] = env
      folders = {}
      for r in envResults:
        folders.setdefault(os.path.dirname(os.path.abspath(r.path)), []).append(r)
      for folder, results in folders.items():
        parent = envItem
        if len(results) > 3 or (len(results) > 1 and len(folders) > 1):
          parent = group(envItem, os.path.basename(folder), results, 'dir:' + folder)
        for r in results:
          img = self.swatch([p.color for p in r.paths])
          self.swatches.append(img)
          someHidden = any(not o.visible.get() for o in r.orbits)
          mark = ('–' if someHidden else '✓') if r.visible.get() else ''
          key = 'res:' + os.path.abspath(r.path)
          item = tree.insert(parent, 'end', text=' ' + r.name, image=img, values=(mark, r.data.nrows, self.resultEnd(r)),
                             open=key in opened)   #a result's orbits start folded away
          self.listItems[item] = r
          self.itemKeys[item] = key
          r.listItem = item
          for o in r.orbits:
            oimg = self.swatch([self.orbitColour(r.paths[0], o)] if r.paths else [])
            self.swatches.append(oimg)
            o.listItem = tree.insert(item, 'end', text=' ' + o.name, image=oimg,
                                     values=('✓' if o.visible.get() else '', o.rows.size, formatValue(o.t1)))
            self.listItems[o.listItem] = o
    if self.results:
      self.noResults.place_forget()
    else:
      self.noResults.place(relx=0.5, rely=0.3, anchor='n')
    if self.selected in self.results:
      tree.selection_set(self.selected.listItem)
      tree.see(self.selected.listItem)
    self.updateFieldChoices()
    self.markBackground()

  def markBackground(self):
    """mark the environment row whose backgrounds are drawn"""
    shown = self.fieldResult()
    for item, env in getattr(self, 'envItems', {}).items():
      if self.list.exists(item):
        self.list.item(item, text=env.name + ('   ◆ background' if env is shown else ''))

  def selectedResults(self):
    """the results picked in the list (a folder row picks all of its results, an orbit row its result)"""
    out = []
    for item in self.list.selection():
      v = self.listItems.get(item)
      if isinstance(v, Orbit):
        v = v.result
      for r in (v if isinstance(v, list) else [v] if v else []):
        if r not in out:
          out.append(r)
    return out

  def selectedOrbits(self):
    return [self.listItems[i] for i in self.list.selection() if isinstance(self.listItems.get(i), Orbit)]

  def setOrbitsVisible(self, orbits, on):
    """show or hide orbits; showing one also shows its result"""
    results = []
    for o in orbits:
      o.visible.set(on)
      if on:
        o.result.visible.set(True)
      if o.result not in results:
        results.append(o.result)
    for r in results:
      self.updateOrbitMask(r)
    self.prepare()
    self.refreshList()
    self.showDetails()
    self.visibilityChanged()

  def select(self, result):
    self.selected = result
    if result is not None and getattr(result, 'listItem', None) in self.listItems:
      self.list.selection_set(result.listItem)
      self.list.see(result.listItem)
    self.showDetails()
    self.markBackground()

  def listSelected(self):
    picked = self.list.selection()
    v = self.listItems.get(picked[0]) if picked else None
    if isinstance(v, list):
      v = v[0]
    if isinstance(v, Orbit):
      v = v.result
    if v is not None and v is not self.selected:
      self.selected = v
      self.showDetails()
      self.markBackground()
      self.redraw()   #automatic backgrounds follow the selection

  def listClicked(self, event):
    """a click in the Shown column shows or hides that row"""
    item = self.list.identify_row(event.y)
    if item and self.list.identify_column(event.x) == '#1':
      v = self.listItems[item]
      if isinstance(v, Orbit):
        self.setOrbitsVisible([v], not (v.visible.get() and v.result.visible.get()))
        return 'break'
      results = v if isinstance(v, list) else [v]
      self.setVisible(results, not all(r.visible.get() for r in results))
      return 'break'

  def toggleSelected(self):
    orbits = self.selectedOrbits()
    if orbits:
      self.setOrbitsVisible(orbits, not all(o.visible.get() and o.result.visible.get() for o in orbits))
      return 'break'
    results = self.selectedResults()
    if results:
      self.setVisible(results, not all(r.visible.get() for r in results))
    return 'break'

  def setVisible(self, results, on):
    for r in results:
      r.visible.set(on)
    self.refreshList()
    if self.selected in results:
      self.showDetails()
    self.visibilityChanged()

  def showOnlySelected(self):
    orbits = self.selectedOrbits()
    if orbits:
      #just these orbits: their results only, and in them only the picked orbits
      owners = {o.result for o in orbits}
      for r in self.results:
        r.visible.set(r in owners)
        for o in r.orbits:
          o.visible.set(o in orbits or r not in owners)
        self.updateOrbitMask(r)
      self.prepare()
      self.refreshList()
      self.showDetails()
      self.visibilityChanged()
      return
    picked = self.selectedResults()
    if picked:
      for r in self.results:
        r.visible.set(r in picked)
      self.refreshList()
      self.showDetails()
      self.visibilityChanged()

  def closeSelected(self):
    picked = self.selectedResults() or ([self.selected] if self.selected else [])
    for r in picked:
      self.closeResult(r, redraw=False)
    self.redraw()

  def showDetails(self):
    """the selected result's options, file, path styles, summary and log under the list"""
    for frame in (self.detailOptions, self.detailPaths, self.summary):
      for child in frame.winfo_children():
        child.destroy()
    r = self.selected if self.selected in self.results else None
    text = self.logWidget
    text.config(state='normal')
    text.delete('1.0', 'end')
    if r is None:
      self.detailPath.config(text='')
      self.summary.pack_forget()
      text.config(state='disabled')
      return
    tk.Label(self.detailOptions, text=r.name, bg=PAGE, fg=INK, font=('Helvetica', 12, 'bold')).pack(side='left')
    tip(ttk.Checkbutton(self.detailOptions, text='Show', variable=r.visible,
                        command=lambda: (self.refreshList(), self.visibilityChanged())), TIPS['Show']).pack(side='left', padx=(10, 0))
    tip(ttk.Checkbutton(self.detailOptions, text='Straight line', variable=r.showStraight, command=self.redraw), TIPS['Straight line']).pack(side='left', padx=(8, 0))
    if self.endVectors(r.data):
      tip(ttk.Checkbutton(self.detailOptions, text='End arrows', variable=r.showEnds, command=self.redraw), TIPS['End arrows']).pack(side='left', padx=(8, 0))
    folder, base = os.path.split(r.path)
    self.detailPath.config(text='%s\n%s' % (base, folder))
    if r.orbits:
      row = tk.Frame(self.detailPaths, bg=PAGE)
      row.pack(fill='x', pady=(0, 4))
      tk.Label(row, text='%d orbits' % sum(o.name.startswith('orbit') for o in r.orbits), bg=PAGE, fg=INK2).pack(side='left')
      tip(ttk.Button(row, text='All', command=lambda: self.setOrbitsVisible(r.orbits, True)), 'Show every orbit').pack(side='left', padx=(8, 0))
      tip(ttk.Button(row, text='None', command=lambda: self.setOrbitsVisible(r.orbits, False)), 'Hide every orbit').pack(side='left', padx=(4, 0))
      tip(ttk.Checkbutton(row, text='Periapsis', variable=r.showPeri, command=self.redraw), TIPS['Periapsis']).pack(side='left', padx=(10, 0))
      tip(ttk.Checkbutton(row, text='Apoapsis', variable=r.showApo, command=self.redraw), TIPS['Apoapsis']).pack(side='left', padx=(6, 0))

    for p in r.paths:
      row = tk.Frame(self.detailPaths, bg=PAGE)
      row.pack(fill='x', pady=1)
      chip = tk.Label(row, bg=p.color, width=3, relief='flat', cursor='hand2')
      chip.pack(side='left', padx=(0, 2 if r.orbits else 6))
      chip.bind('<Button-1>', lambda e, p=p: self.pickColour(p))
      tip(chip, 'First orbit\'s colour (click to change)' if r.orbits else 'Line colour (click to change)')
      if r.orbits:
        #first and last shown orbits; those between are a mix of the two
        tk.Label(row, text='→', bg=PAGE, fg=INK2).pack(side='left')
        chip2 = tk.Label(row, bg=p.color2, width=3, relief='flat', cursor='hand2')
        chip2.pack(side='left', padx=(2, 6))
        chip2.bind('<Button-1>', lambda e, p=p: self.pickColour(p, last=True))
        tip(chip2, 'Last orbit\'s colour (click to change); the orbits between are a mix of the two')
      box = ttk.Combobox(row, state='readonly', width=8, values=[name for name, _ in LINE_STYLES])
      box.set(p.style)
      box.bind('<<ComboboxSelected>>', lambda e, p=p, box=box: self.setStyle(p, color=None, style=box.get()))
      box.pack(side='left')
      tip(box, 'Line style: solid, dashed or dotted')
      tk.Label(row, text=p.name, bg=PAGE, fg=INK2, anchor='w').pack(side='left', padx=(8, 0))

    self.summary.pack(fill='x', pady=(6, 0), before=self.logWidget.master)
    for i, (label, value) in enumerate(self.summaryRows(r)):
      tk.Label(self.summary, text=label, bg=SURFACE, fg=MUTED, anchor='nw', font=('Helvetica', 10)).grid(row=i, column=0, sticky='nw', padx=(8, 6), pady=1)
      tk.Label(self.summary, text=value, bg=SURFACE, fg=INK, anchor='w', justify='left', wraplength=330,
               font=('Helvetica', 11)).grid(row=i, column=1, sticky='w', padx=(0, 8), pady=1)
    self.summary.columnconfigure(1, weight=1)
    text.insert('1.0', r.logText)
    text.config(state='disabled')

  def pickColour(self, p, last=False):
    """choose a path's colour, or for an orbit run the last orbit's colour"""
    current = p.color2 if last else p.color
    title = '%s colour for %s' % ('Last orbit' if last else ('First orbit' if p.result.orbits else 'Line'), self.pathLabel(p))
    chosen = colorchooser.askcolor(color=current, title=title, parent=self.root)[1]
    if chosen:
      self.setStyle(p, color=None if last else chosen, style=None, color2=chosen if last else None)

  def setStyle(self, p, color, style, color2=None):
    """change a path's colour(s) or line style, remembered for that result through reloads"""
    p.color = color or p.color
    p.color2 = color2 or p.color2
    p.style = style or p.style
    p.result.styles[p.name] = (p.color, p.style, p.color2)
    self.refreshList()
    self.showDetails()
    self.redraw()

  def summaryRows(self, r):
    """(label, value) facts about a result, from its data and log"""
    rows = [('Environment', r.env.name)]
    if r.studyType:
      rows.append(('Study type', r.studyType))
    full = [o for o in r.orbits if o.name.startswith('orbit')]
    if full:
      periods = [(o.t1 - o.t0) / DAY for o in full]
      rows.append(('Orbits', '%d, mean period %s days (%s to %s)' % (len(full), formatShort(float('%.7g' % np.mean(periods))),
                  formatShort(float('%.7g' % min(periods))), formatShort(float('%.7g' % max(periods))))))
    log = r.logText
    m = re.search(r'^calc:\s*(.*)$', log, re.M)
    if m:
      old = re.search(r'<[\w.]*?(\w+) object', m.group(1))
      rows.append(('Calculator', (flow.calculatorName(m.group(1)) if flow else None) or (old.group(1) if old else m.group(1))))
    m = re.search(r'^dt:?\s+(\S+)', log, re.M)
    if m:
      rows.append(('dt', m.group(1) + ' s'))
    data = r.data
    rows.append(('Rows', '%d in %d path%s' % (data.nrows, len(r.paths), '' if len(r.paths) == 1 else 's')))
    for label, _ in TIME_COLUMNS:
      col = self.columnForTime(label, data)
      if col:
        v = data.values[col]
        v = v[np.isfinite(v)]
        if v.size:
          rows.append((col, '%s → %s s' % (formatValue(float(v[0])), formatValue(float(v[-1])))))
    if r.paths:
      p = r.paths[0]
      x, y = data.values[p.xcol][p.rows], data.values[p.ycol][p.rows]
      d = np.hypot(x, y)
      d = d[np.isfinite(d)]
      if d.size:
        fmt = lambda v: '%s m (%s AU)' % (formatValue(float(v)), formatShort(float('%.4g' % (v / AU))))
        rows.append(('Distance', '%s → %s' % (fmt(d[0]), fmt(d[-1]))))
        rows.append(('Closest', fmt(d.min())))
      velocity = velocityColumns(data)
      if velocity:
        speed = np.hypot(data.values[velocity[0]][p.rows], data.values[velocity[1]][p.rows])
        speed = speed[np.isfinite(speed)]
        if speed.size:
          rows.append(('Speed |v|', '%.4g → %.4g c' % (speed[0] / C, speed[-1] / C)))
    found = [line.strip() for line in log.splitlines() if re.search(r'accuracy|predicted', line, re.I)]
    for line in found[:6]:
      rows.append(('Result', line if len(line) <= 110 else line[:107] + '...'))
    return rows

  def updateFieldChoices(self):
    """the Background list: the selected result's environment, or any environment with bodies"""
    envs = [e for e in self.activeEnvironments() if e.hasField()]
    if self.fieldChoice not in envs:
      self.fieldChoice = None
    self.fieldBox.config(values=["Selected result's environment"] + [e.name for e in envs])
    self.fieldBox.set(self.fieldChoice.name if self.fieldChoice else "Selected result's environment")

  def fieldChoiceChanged(self):
    self.fieldChoice = next((e for e in self.activeEnvironments() if e.hasField() and e.name == self.fieldBox.get()), None)
    self.markBackground()
    self.redraw()

  def visibilityChanged(self):
    self.hover = None
    self.redraw()

  def toggleSidebar(self):
    self.showSidebar.set(not self.showSidebar.get())
    self.sidebarChanged()

  def sidebarChanged(self):
    """show the whole results panel, or fold it to just its button"""
    letters = '\n'.join('Results')
    self.root.update_idletasks()
    total = self.panes.winfo_width()
    if self.showSidebar.get():
      self.sidebarButton.config(text='\u25b6\n\n' + letters)
      self.sidebarContent.pack(side='left', fill='both', expand=True)
      if total > 1:
        self.panes.sashpos(0, max(200, total - self.sidebarWidth))
    else:
      if total > 1 and self.sidebarContent.winfo_ismapped():
        self.sidebarWidth = max(200, total - self.panes.sashpos(0))   #remember the width the user chose
      self.sidebarButton.config(text='\u25c0\n\n' + letters)
      self.sidebarContent.pack_forget()
      if total > 1:
        self.panes.sashpos(0, total - self.sidebarButton.winfo_reqwidth())
