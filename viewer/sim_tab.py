"""the Sim tab: setting up a study, estimating it, running it in its own process (studies/run_study.py) and following it"""
from viewer.common import *


class SimTab:
  """mixed into Viewer (viewer/app.py)"""

  def simInit(self):
    """the sim settings, shared by the Sim tab and its setup window"""
    self.simType = tk.StringVar(value='Orbital')
    self.simVars = {k: tk.StringVar() for k in ('name', 'calculator', 'distUnit', 'velUnit', 'dt', 'every',
                                                  'endKind', 'endValue', 'px', 'py', 'vx', 'vy', 'stepMode', 'stepFraction')}
    self.simBodies = []    #per body: dict of mass (MS), colour, x, y (StringVars, in the distance unit)
    self.simReady = False  #filled in from a run (or the defaults) yet
    self.simWindow = None
    self.simProc = None
    self.simUnits = {'distUnit': 'AU', 'velUnit': 'km/s'}   #the units the entries are in now

  def simTab(self, tab, button, label, gap):
    tk.Label(tab, text='Type', bg=PAGE, fg=INK2).pack(side='left', padx=(4, 2))
    box = ttk.Combobox(tab, state='readonly', width=11, values=[t for t, _ in SIM_TYPES], textvariable=self.simType)
    box.bind('<<ComboboxSelected>>', lambda e: self.simTypeChanged())
    box.pack(side='left')
    tip(box, 'Orbital runs count orbits and can end after a number of them; hyperbolic runs end on time or distance')
    button(tab, 'Set up...', self.simSetup)
    button(tab, 'From selected run', self.simFromSelected)
    gap(tab)
    self.simStartButton = button(tab, '▶ Start', self.simStart)
    self.simLabel = label(tab, 'set up a run, or start from the selected one')

  def simStrip(self):
    """the progress bar under the plot while a sim runs"""
    self.simBar = tk.Frame(self.root, bg=PAGE)
    self.simBarLabel = tk.Label(self.simBar, text='', bg=PAGE, fg=INK2, anchor='w')
    self.simBarLabel.pack(side='left', padx=(8, 6))
    self.simProgress = ttk.Progressbar(self.simBar, orient='horizontal', length=300, mode='determinate', maximum=1.0)
    self.simProgress.pack(side='left', padx=4, pady=3)
    tip(ttk.Button(self.simBar, text='Cancel', command=self.simCancel), TIPS['Cancel']).pack(side='left', padx=6)

  def simTypeChanged(self):
    """number of orbits is only an end condition for orbit runs"""
    orbit = self.simTypeKey() == 'orbit'
    if not orbit and self.simVars['endKind'].get() == dict(END_KINDS)['orbits']:
      self.simVars['endKind'].set(dict(END_KINDS)['time'])
    if self.simWindow is not None and self.simWindow.winfo_exists():
      self.simEndBox.config(values=[label for kind, label in END_KINDS if orbit or kind != 'orbits'])
      self.simEndChanged()

  def simTypeKey(self):
    return dict(SIM_TYPES)[self.simType.get()]

  @staticmethod
  def simNumber(v):
    return '%.10g' % v

  def simFill(self, cfg):
    """put a config (SI units) into the entries, choosing units that suit its sizes"""
    scale = max([abs(v) for v in cfg['position']] + [abs(b[k]) for b in cfg['bodies'] for k in ('x', 'y')] +
                ([cfg['end']['value']] if cfg['end']['kind'] in ('min', 'max') else []) + [1.0])
    dist = 'AU' if scale >= 0.01 * AU else ('km' if scale >= 1e6 else 'm')
    speed = max(abs(v) for v in cfg['velocity'])
    vel = 'c' if speed >= 0.1 * C else ('km/s' if speed >= 100 else 'm/s')
    du, vu = dict(DIST_UNITS)[dist], dict(VEL_UNITS)[vel]
    v = self.simVars
    self.simType.set(next(t for t, k in SIM_TYPES if k == cfg['type']))
    v['name'].set(cfg['name'])
    v['calculator'].set((flow.calculatorName(cfg['calculator']) if flow else None) or cfg['calculator'])
    v['distUnit'].set(dist)
    v['velUnit'].set(vel)
    self.simUnits = {'distUnit': dist, 'velUnit': vel}
    v['dt'].set(self.simNumber(cfg['dt']))
    v['stepMode'].set(STEP_MODES[1] if cfg.get('stepFraction') else STEP_MODES[0])
    v['stepFraction'].set(self.simNumber(cfg['stepFraction']) if cfg.get('stepFraction') else '0.001')
    v['every'].set(self.simNumber(cfg['every']))
    v['px'].set(self.simNumber(cfg['position'][0] / du))
    v['py'].set(self.simNumber(cfg['position'][1] / du))
    v['vx'].set(self.simNumber(cfg['velocity'][0] / vu))
    v['vy'].set(self.simNumber(cfg['velocity'][1] / vu))
    kind, value = cfg['end']['kind'], cfg['end']['value']
    v['endKind'].set(dict(END_KINDS)[kind])
    v['endValue'].set(self.simNumber(value / du if kind in ('min', 'max') else value))
    ms = MS
    self.simBodies = [{'mass': tk.StringVar(value=self.simNumber(b['mass'] / ms)), 'colour': tk.StringVar(value='black' if b['black'] else 'white'),
                       'x': tk.StringVar(value=self.simNumber(b['x'] / du)), 'y': tk.StringVar(value=self.simNumber(b['y'] / du))}
                      for b in cfg['bodies']]
    self.simReady = True
    self.simBuildBodies()
    self.simTypeChanged()

  def simDefaults(self, r=None):
    """a config to start from: the selected run's setup, or Mercury round the Sun"""
    ms = MS
    cfg = {'name': 'sim', 'type': 'orbit', 'calculator': 'SpecialFlowCalculator, second order',
           'bodies': [{'mass': ms, 'x': 0.0, 'y': 0.0, 'black': True}],
           'position': [0.0, 69820000000.0], 'velocity': [38860.0, 0.0], 'dt': 60.0, 'every': DAY / 2,
           'end': {'kind': 'orbits', 'value': 3}}
    if r is None:
      return cfg
    data, log = r.data, r.logText
    m = re.search(r'^sim from (?:csv_viewer.py|the viewer):\s*(\{.*\})\s*$', log, re.M)
    if m:
      try:
        return json.loads(m.group(1))   #a run from this tab: its exact setup
      except ValueError:
        pass
    cfg['name'] = 'sim_' + r.name
    if r.env and r.env.bodies:
      cfg['bodies'] = [{'mass': m, 'x': x, 'y': y, 'black': black} for m, x, y, black in r.env.bodies]
    m = re.search(r'^calc:\s*(.*)$', log, re.M)
    name = flow.calculatorName(m.group(1)) if m and flow else None
    if name:
      cfg['calculator'] = name
    cfg['type'] = 'orbit' if (r.studyType == 'orbit' or r.orbits) else 'hyperbolic'
    if r.selection:
      xcol, ycol = r.selection[0]
      x, y = data.values[xcol], data.values[ycol]
      ok = np.nonzero(np.isfinite(x) & np.isfinite(y))[0]
      if ok.size:
        cfg['position'] = [float(x[ok[0]]), float(y[ok[0]])]
        velocity = velocityColumns(data)
        if velocity:
          cfg['velocity'] = [float(data.values[velocity[0]][ok[0]]), float(data.values[velocity[1]][ok[0]])]
    #the log's starting values, where it has them, are exact; the csv's first row may be a step or more in
    for key, label in (('position', 'pos'), ('velocity', 'v')):
      m = re.search(r'^initial %s\s*\[\s*([^\]]+?)\s*\]' % label, log, re.M)
      if m:
        try:
          cfg[key] = [float(x) for x in m.group(1).split()[:2]]
        except ValueError:
          pass
    tcol = self.columnForTime(TIME_COLUMNS[0][0], data)
    t = data.values[tcol][np.isfinite(data.values[tcol])] if tcol else np.array([])
    m = re.search(r'^dt:?\s+(\S+)', log, re.M)
    try:
      cfg['dt'] = float(m.group(1)) if m else float(np.median(np.diff(t)) / 10)
    except (ValueError, TypeError):
      pass
    m = re.search(r'^step fraction:\s*(\S+)', log, re.M)
    if m:
      cfg['stepFraction'] = float(m.group(1))
    if t.size >= 2:
      cfg['every'] = float(np.median(np.diff(t)))
    full = [o for o in r.orbits if o.full]
    if cfg['type'] == 'orbit':
      cfg['end'] = {'kind': 'orbits', 'value': max(1, len(full))}
    elif t.size:
      cfg['end'] = {'kind': 'time', 'value': float(t[-1])}
    return cfg

  def simFromSelected(self):
    self.simFill(self.simDefaults(self.current()))
    self.simLabel.config(text='set up from %s' % (self.current().name if self.current() else 'the defaults'))

  def simUnitChanged(self, which):
    """convert the entries to a newly chosen unit"""
    units = DIST_UNITS if which == 'distUnit' else VEL_UNITS
    old, new = dict(units)[self.simUnits[which]], dict(units)[self.simVars[which].get()]
    if which == 'distUnit':
      targets = [self.simVars['px'], self.simVars['py']] + [b[k] for b in self.simBodies for k in ('x', 'y')]
      if self.simEndKey() in ('min', 'max'):
        targets.append(self.simVars['endValue'])
    else:
      targets = [self.simVars['vx'], self.simVars['vy']]
    for var in targets:
      try:
        var.set(self.simNumber(float(var.get()) * old / new))
      except ValueError:
        pass
    self.simUnits[which] = self.simVars[which].get()

  def simEndKey(self):
    return next(k for k, label in END_KINDS if label == self.simVars['endKind'].get())

  def simEndChanged(self):
    if self.simWindow is not None and self.simWindow.winfo_exists():
      kind = self.simEndKey()
      unit = {'time': 's', 'orbits': 'orbits'}.get(kind, self.simVars['distUnit'].get())
      self.simEndUnit.config(text=unit)

  def simSetup(self):
    """the setup window: bodies, particle, steps and end condition"""
    if not self.simReady:
      self.simFill(self.simDefaults(self.current()))
    if self.simWindow is not None and self.simWindow.winfo_exists():
      self.simWindow.lift()
      return
    w = self.simWindow = tk.Toplevel(self.root)
    w.title('Sim setup')
    w.configure(bg=PAGE)
    v = self.simVars
    pad = {'padx': 6, 'pady': 3}

    def section(text, row):
      tk.Label(w, text=text, bg=PAGE, fg=INK, font=('Helvetica', 12, 'bold')).grid(row=row, column=0, columnspan=6, sticky='w', padx=8, pady=(10, 2))

    def entry(parent, var, row, col, width=12):
      e = ttk.Entry(parent, textvariable=var, width=width)
      e.grid(row=row, column=col, sticky='w', **pad)
      return e

    def text(parent, s, row, col, **kw):
      tk.Label(parent, text=s, bg=PAGE, fg=INK2).grid(row=row, column=col, sticky='w', **pad, **kw)

    section('Run', 0)
    text(w, 'Type', 1, 0)
    typeBox = ttk.Combobox(w, state='readonly', width=11, values=[t for t, _ in SIM_TYPES], textvariable=self.simType)
    typeBox.bind('<<ComboboxSelected>>', lambda e: self.simTypeChanged())
    typeBox.grid(row=1, column=1, sticky='w', **pad)
    text(w, 'Name', 1, 2)
    entry(w, v['name'], 1, 3, 18)
    text(w, 'Calculator', 2, 0)
    ttk.Combobox(w, state='readonly', width=28, values=simrun.calculators() if simrun else [],
                 textvariable=v['calculator']).grid(row=2, column=1, columnspan=3, sticky='w', **pad)
    text(w, 'Distances in', 3, 0)
    du = ttk.Combobox(w, state='readonly', width=6, values=[u for u, _ in DIST_UNITS], textvariable=v['distUnit'])
    du.bind('<<ComboboxSelected>>', lambda e: (self.simUnitChanged('distUnit'), self.simEndChanged()))
    du.grid(row=3, column=1, sticky='w', **pad)
    text(w, 'Velocities in', 3, 2)
    vu = ttk.Combobox(w, state='readonly', width=6, values=[u for u, _ in VEL_UNITS], textvariable=v['velUnit'])
    vu.bind('<<ComboboxSelected>>', lambda e: self.simUnitChanged('velUnit'))
    vu.grid(row=3, column=3, sticky='w', **pad)

    section('Bodies', 4)
    countRow = tk.Frame(w, bg=PAGE)
    countRow.grid(row=5, column=0, columnspan=6, sticky='w', padx=2)
    tk.Label(countRow, text='Number of bodies', bg=PAGE, fg=INK2).pack(side='left', padx=6)
    self.simCount = tk.StringVar(value=str(len(self.simBodies)))
    ttk.Spinbox(countRow, from_=1, to=8, width=4, textvariable=self.simCount, command=self.simCountChanged).pack(side='left')
    self.simBodyFrame = tk.Frame(w, bg=PAGE)
    self.simBodyFrame.grid(row=6, column=0, columnspan=6, sticky='w', padx=2)
    self.simBuildBodies()

    section('Particle', 7)
    text(w, 'Start x', 8, 0); entry(w, v['px'], 8, 1)
    text(w, 'y', 8, 2); entry(w, v['py'], 8, 3)
    text(w, 'Velocity x', 9, 0); entry(w, v['vx'], 9, 1)
    text(w, 'y', 9, 2); entry(w, v['vy'], 9, 3)

    section('Steps and end', 10)
    text(w, 'Steps', 11, 0)
    modeBox = ttk.Combobox(w, state='readonly', width=11, values=STEP_MODES, textvariable=v['stepMode'])
    modeBox.grid(row=11, column=1, sticky='w', **pad)
    tip(modeBox, 'Fixed: every step is dt. Adaptive: each step moves at most the step fraction of the distance to the '
                 'nearest body, so close passes get short steps and the far-out parts long ones (dt is then the longest)')
    text(w, 'step fraction', 11, 2); tip(entry(w, v['stepFraction'], 11, 3), 'Adaptive steps: the fraction of the distance to the nearest body each step moves (0.001 is a good start)')
    text(w, 'dt (s)', 12, 0); tip(entry(w, v['dt'], 12, 1), 'Fixed steps: every step. Adaptive steps: the longest step')
    text(w, 'csv row every (s)', 12, 2); entry(w, v['every'], 12, 3)
    text(w, 'End when', 13, 0)
    self.simEndBox = ttk.Combobox(w, state='readonly', width=26, textvariable=v['endKind'])
    self.simEndBox.bind('<<ComboboxSelected>>', lambda e: self.simEndChanged())
    self.simEndBox.grid(row=13, column=1, columnspan=2, sticky='w', **pad)
    entry(w, v['endValue'], 13, 3)
    self.simEndUnit = tk.Label(w, text='', bg=PAGE, fg=INK2)
    self.simEndUnit.grid(row=13, column=4, sticky='w')
    tk.Label(w, text='min / max distance: from the nearest body (any body). Orbits are counted round the origin.',
             bg=PAGE, fg=MUTED, font=('Helvetica', 10)).grid(row=14, column=0, columnspan=6, sticky='w', padx=8)

    buttons = tk.Frame(w, bg=PAGE)
    buttons.grid(row=15, column=0, columnspan=6, sticky='e', padx=8, pady=10)
    tip(ttk.Button(buttons, text='From selected run', command=self.simFromSelected), TIPS['From selected run']).pack(side='left', padx=4)
    tip(ttk.Button(buttons, text='▶ Start', command=self.simStart), TIPS['\u25b6 Start']).pack(side='left', padx=4)
    tip(ttk.Button(buttons, text='Close', command=w.destroy), 'Close this window; the settings are kept').pack(side='left', padx=4)
    self.simTypeChanged()

  def simCountChanged(self):
    try:
      n = max(1, min(8, int(self.simCount.get())))
    except ValueError:
      return
    ms = MS
    while len(self.simBodies) < n:
      self.simBodies.append({'mass': tk.StringVar(value='1'), 'colour': tk.StringVar(value='black'),
                             'x': tk.StringVar(value='0'), 'y': tk.StringVar(value='0')})
    del self.simBodies[n:]
    self.simBuildBodies()

  def simBuildBodies(self):
    """one row per body: mass, black / white, x, y"""
    frame = getattr(self, 'simBodyFrame', None)
    if frame is None or not frame.winfo_exists():
      return
    for child in frame.winfo_children():
      child.destroy()
    for col, head in enumerate(('', 'mass (MS)', 'black / white', 'x', 'y')):
      tk.Label(frame, text=head, bg=PAGE, fg=MUTED, font=('Helvetica', 10)).grid(row=0, column=col, sticky='w', padx=6)
    for i, b in enumerate(self.simBodies, 1):
      tk.Label(frame, text='body %d' % i, bg=PAGE, fg=INK2).grid(row=i, column=0, sticky='w', padx=6)
      ttk.Entry(frame, textvariable=b['mass'], width=12).grid(row=i, column=1, padx=6, pady=2)
      ttk.Combobox(frame, state='readonly', width=7, values=['black', 'white'], textvariable=b['colour']).grid(row=i, column=2, padx=6)
      ttk.Entry(frame, textvariable=b['x'], width=12).grid(row=i, column=3, padx=6)
      ttk.Entry(frame, textvariable=b['y'], width=12).grid(row=i, column=4, padx=6)
    if hasattr(self, 'simCount'):
      self.simCount.set(str(len(self.simBodies)))

  def simConfig(self):
    """the entries as a config in SI units; raises ValueError naming a bad entry"""
    v = self.simVars
    du, vu = dict(DIST_UNITS)[v['distUnit'].get()], dict(VEL_UNITS)[v['velUnit'].get()]

    def number(var, what, positive=False):
      try:
        x = float(var.get())
      except ValueError:
        raise ValueError('%s is not a number: %r' % (what, var.get()))
      if positive and not x > 0:
        raise ValueError('%s must be above 0' % what)
      return x
    ms = MS
    bodies = [{'mass': number(b['mass'], 'body %d mass' % i, True) * ms, 'black': b['colour'].get() == 'black',
               'x': number(b['x'], 'body %d x' % i) * du, 'y': number(b['y'], 'body %d y' % i) * du}
              for i, b in enumerate(self.simBodies, 1)]
    kind = self.simEndKey()
    value = number(v['endValue'], 'the end value', True)
    if kind in ('min', 'max'):
      value *= du
    if kind == 'orbits':
      value = int(round(value))
    name = re.sub(r'[^\w.-]+', '_', v['name'].get().strip()) or 'sim'
    return {'name': name, 'type': self.simTypeKey(), 'calculator': v['calculator'].get(), 'bodies': bodies,
            'position': [number(v['px'], 'start x') * du, number(v['py'], 'start y') * du],
            'velocity': [number(v['vx'], 'velocity x') * vu, number(v['vy'], 'velocity y') * vu],
            'dt': number(v['dt'], 'dt', True), 'every': number(v['every'], 'the csv row interval', True),
            'stepFraction': number(v['stepFraction'], 'the step fraction', True) if v['stepMode'].get() == STEP_MODES[1] else None,
            'end': {'kind': kind, 'value': value}}

  @staticmethod
  def duration(seconds):
    if seconds < 90:
      return '%d seconds' % max(1, round(seconds))
    if seconds < 90 * 60:
      return '%.1f minutes' % (seconds / 60)
    return '%.1f hours' % (seconds / 3600)

  def simStart(self):
    """estimate how long the run will take, ask, then run it in its own process"""
    if simrun is None:
      messagebox.showerror('Sim', 'studies/run_study.py could not be imported')
      return
    if getattr(self, 'simBase', None) is not None:
      messagebox.showinfo('Sim', 'A sim is already running')
      return
    if not self.simReady:
      self.simFill(self.simDefaults(self.current()))
    try:
      cfg = self.simConfig()
    except ValueError as e:
      messagebox.showerror('Sim setup', str(e), parent=self.simWindow if self.simWindow and self.simWindow.winfo_exists() else self.root)
      return
    self.root.config(cursor='watch')
    self.root.update()
    try:
      steps, seconds, how = simrun.estimate(cfg)
    except Exception as e:
      steps, seconds, how = None, None, 'could not estimate: %s' % e
    finally:
      self.root.config(cursor='')
    if steps is None:
      text = 'Estimated duration: unknown (%s).' % how
    else:
      stepText = 'adaptive steps, fraction %g' % cfg['stepFraction'] if cfg.get('stepFraction') else 'steps of %g s' % cfg['dt']
      text = 'Estimated duration: about %s\n(%.3g %s; %s).' % (self.duration(seconds), steps, stepText, how)
    end = cfg['end']
    text += '\n\n%s run, %d bod%s, ends: %s %s.\n\nProceed?' % (self.simType.get(), len(cfg['bodies']), 'y' if len(cfg['bodies']) == 1 else 'ies',
                                                              self.simVars['endKind'].get().lower(), self.simVars['endValue'].get())
    parent = self.simWindow if self.simWindow and self.simWindow.winfo_exists() else self.root
    if not messagebox.askokcancel('Run sim', text, parent=parent):
      return
    os.makedirs(SIM_DIR, exist_ok=True)
    run = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    base = os.path.join(SIM_DIR, run)
    with open(base + '.config.json', 'w') as f:
      json.dump(cfg, f)
    status = {'id': run, 'name': cfg['name'], 'state': 'starting', 'progress': 0.0, 'started': time.time(),
              'estimate': seconds, 'collected': False}
    with open(base + '.status.json', 'w') as f:
      json.dump(status, f)
    here = ROOT
    with open(base + '.out.txt', 'w') as out:
      #its own session and no pipes back to the viewer, so closing the viewer doesn't stop it
      proc = subprocess.Popen([sys.executable, '-u', os.path.join(ROOT, 'studies', 'run_study.py'), base + '.config.json',
                               '--status', base + '.status.json'], cwd=here, stdout=out, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL, start_new_session=True)
    self.simFollow(base, proc)

  def simFollow(self, base, proc=None):
    """show a run's progress under the plot, from its status file"""
    self.simProc = proc
    self.simBase = base
    self.simCancelled = False
    self.simProgress['value'] = 0
    status = self.simStatus(base)
    self.simBarLabel.config(text='Sim %s: starting' % status.get('name', ''))
    self.simBar.pack(side='bottom', fill='x', before=self.status)
    self.simLabel.config(text='running %s' % status.get('name', ''))
    self.simStartButton.config(state='disabled')
    self.root.after(300, self.simPoll)

  @staticmethod
  def simStatus(base):
    try:
      with open(base + '.status.json') as f:
        return json.load(f)
    except (OSError, ValueError):
      return {}

  @staticmethod
  def simMark(base, **fields):
    """update a run's status file (the viewer marks a finished run collected once it has opened it)"""
    if simrun:
      simrun.writeStatus(base + '.status.json', **fields)

  @staticmethod
  def pidAlive(pid):
    try:
      os.kill(pid, 0)
      return True
    except (OSError, TypeError):
      return False

  def simPoll(self):
    base = getattr(self, 'simBase', None)
    if base is None:
      return
    status = self.simStatus(base)
    state = status.get('state')
    if state in ('starting', 'running'):
      exited = self.simProc.poll() is not None if self.simProc is not None else (state == 'running' and not self.pidAlive(status.get('pid')))
      if not exited:
        f = float(status.get('progress', 0.0))
        self.simProgress['value'] = f
        elapsed = time.time() - status.get('started', time.time())
        estimate = status.get('estimate')
        left = elapsed / f * (1 - f) if f > 0.01 else (estimate - elapsed if estimate else None)
        self.simBarLabel.config(text='Sim %s: %d%%%s' % (status.get('name', ''), round(100 * f),
                                                       '  about %s left' % self.duration(left) if left and left > 0 else ''))
        self.root.after(300, self.simPoll)
        return
      time.sleep(0.2)
      status = self.simStatus(base)   #it may have written its last state as it exited
      state = status.get('state')
      if state in ('starting', 'running'):
        state = 'cancelled' if self.simCancelled else 'failed'
    self.simBase = self.simProc = None
    self.simBar.pack_forget()
    self.simStartButton.config(state='normal')
    self.simCollect(base, status, state)

  def simCollect(self, base, status, state):
    """deal with a run that has ended: open its files, or say why there are none"""
    self.simMark(base, collected=True)
    name = status.get('name', '')
    if state == 'done' and status.get('file') and os.path.exists(status['file']):
      took = status.get('finished', time.time()) - status.get('started', time.time())
      self.simLabel.config(text='finished in %s: %s' % (self.duration(took), os.path.basename(status['file'])))
      self.loadMany([status['file']])
    elif state == 'cancelled':
      self.simLabel.config(text='%s cancelled (its files so far are kept in logs)' % name)
    else:
      self.simLabel.config(text='%s failed' % name)
      error = status.get('error')
      if not error:
        try:
          with open(base + '.out.txt') as f:
            error = ''.join(f.readlines()[-15:])
        except OSError:
          error = 'the run stopped without saying why'
      messagebox.showerror('Sim failed', error)

  def simPickUp(self):
    """
    on opening: runs started from an earlier viewer - open those that finished since, follow one still running;
    old bookkeeping files of collected runs are tidied away after a week
    """
    if not os.path.isdir(SIM_DIR):
      return
    for path in sorted(glob.glob(os.path.join(SIM_DIR, '*.status.json'))):
      base = path[:-len('.status.json')]
      status = self.simStatus(base)
      if status.get('collected'):
        if time.time() - status.get('started', 0) > 7 * DAY:
          for suffix in ('.status.json', '.config.json', '.out.txt'):
            try:
              os.remove(base + suffix)
            except OSError:
              pass
        continue
      state = status.get('state')
      alive = self.pidAlive(status.get('pid'))
      if state in ('starting', 'running') and alive:
        if getattr(self, 'simBase', None) is None:
          self.simFollow(base)
      elif state in ('starting', 'running'):
        self.simCollect(base, status, 'failed')   #it stopped without finishing
      else:
        self.simCollect(base, status, state)

  def simCancel(self):
    """stop the running sim; the files it has written so far are kept"""
    base = getattr(self, 'simBase', None)
    if base is None:
      return
    self.simCancelled = True
    pid = self.simStatus(base).get('pid') or (self.simProc.pid if self.simProc is not None else None)
    if pid and self.pidAlive(pid):
      os.kill(pid, signal.SIGTERM)
