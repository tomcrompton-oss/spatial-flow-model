"""the Config tab: saving and loading preferences (how the viewer looks), configs (the data and its settings), or both"""
from viewer.common import *


class ConfigTab:
  """mixed into Viewer (viewer/app.py)"""

  def configTab(self, tab, button, label, gap):
    button(tab, 'Save preferences...', self.savePreferences)
    button(tab, 'Load preferences...', self.loadPreferences)
    gap(tab)
    button(tab, 'Save config...', self.saveConfig)
    button(tab, 'Load config...', self.loadConfig)
    gap(tab)
    button(tab, 'Save full...', self.saveFull)
    button(tab, 'Load full...', self.loadFull)
    self.configLabel = label(tab, 'files go in configs/ by default')

  def preferences(self):
    """the viewer's look, apart from any data"""
    prefs = {name: getattr(self, name).get() for name in PREF_VARS}
    self.root.update_idletasks()
    prefs['geometry'] = self.root.winfo_geometry()
    if self.showSidebar.get() and self.panes.winfo_width() > 1:
      self.sidebarWidth = max(200, self.panes.winfo_width() - self.panes.sashpos(0))
    prefs['sidebarWidth'] = self.sidebarWidth
    return {'kind': 'preferences', 'version': CONFIG_VERSION, 'preferences': prefs}

  def applyPreferences(self, doc):
    """use saved preferences; the data open stays as it is"""
    prefs = doc.get('preferences', {})
    for name in PREF_VARS:
      if name in prefs:
        try:
          getattr(self, name).set(prefs[name])
        except tk.TclError:
          pass
    if 'geometry' in prefs:
      self.root.geometry(prefs['geometry'])
    if 'sidebarWidth' in prefs:
      self.sidebarWidth = prefs['sidebarWidth']
    self.unitBox.current(self.unit.get())
    self.sidebarChanged()
    if self.results:
      self.updateTimeChoices(resetInterval=False)
    self.modeChanged()   #redoes the plotted values and fits the view

  def dataConfig(self, where):
    """the files open and their settings; file paths are also kept relative to where the config is saved"""
    results = []
    for r in self.results:
      results.append({
        'path': os.path.abspath(r.path), 'relative': os.path.relpath(os.path.abspath(r.path), where),
        'visible': r.visible.get(), 'straight': r.showStraight.get(), 'ends': r.showEnds.get(),
        'periapsis': r.showPeri.get(), 'apoapsis': r.showApo.get(),
        'styles': {p.name: [p.color, p.style, p.color2] for p in r.paths},
        'selection': [list(pair) for pair in r.selection], 'group': r.group,
        'hiddenOrbits': [o.name.split('  ')[0] for o in r.orbits if not o.visible.get()]})
    return {'kind': 'config', 'version': CONFIG_VERSION, 'results': results,
            'selected': os.path.abspath(self.selected.path) if self.selected in self.results else None,
            'background': self.fieldChoice.name if self.fieldChoice else None,
            'timeInterval': self.timeInterval.get(),
            'view': {'range': list(self.view), 'mode': self.mode.get(), 'unit': self.unit.get(),
                     'logX': self.logX.get(), 'logY': self.logY.get()}}

  def applyConfig(self, doc, where, replace):
    """open a config's files (instead of, or as well as, those open now) and set them up as saved"""
    if replace:
      for r in list(self.results):
        self.closeResult(r, redraw=False)
    missing, loaded = [], []
    for entry in doc.get('results', []):
      path = next((p for p in (os.path.join(where, entry.get('relative', '')), entry.get('path', '')) if p and os.path.isfile(p)), None)
      if path is None:
        missing.append(entry.get('path') or entry.get('relative'))
        continue
      self.load(path, refit=False)
      r = next((x for x in self.results if os.path.abspath(x.path) == os.path.abspath(path)), None)
      if r is None:
        continue
      loaded.append(r)
      names = set(r.data.names)
      selection = [tuple(pair) for pair in entry.get('selection', []) if all(c in names for c in pair)]
      if selection:
        r.selection = selection
      r.group = entry.get('group') if entry.get('group') in names else None
      r.styles = {name: tuple(style) for name, style in entry.get('styles', {}).items()}
      for var, key in ((r.visible, 'visible'), (r.showStraight, 'straight'), (r.showEnds, 'ends'),
                       (r.showPeri, 'periapsis'), (r.showApo, 'apoapsis')):
        if key in entry:
          var.set(entry[key])
      hidden = set(entry.get('hiddenOrbits', []))
      for o in r.orbits:
        o.visible.set(o.name.split('  ')[0] not in hidden)
      self.updateOrbitMask(r)
      self.buildPaths(r)
    if doc.get('timeInterval'):
      self.timeInterval.set(doc['timeInterval'])
    selected = next((r for r in self.results if os.path.abspath(r.path) == doc.get('selected')), loaded[0] if loaded else None)
    if selected:
      self.select(selected)
    self.refreshList()
    self.fieldChoice = next((e for e in self.activeEnvironments() if e.name == doc.get('background')), None)
    self.updateFieldChoices()
    self.prepare()
    view = doc.get('view', {})
    same = view.get('mode') == self.mode.get() and view.get('unit') == self.unit.get() and \
           view.get('logX') == self.logX.get() and view.get('logY') == self.logY.get()
    if replace and same and len(view.get('range', [])) == 4:
      self.view = list(view['range'])   #the saved view, if it was saved with the same axes
      self.redraw()
    else:
      self.fit()
    self.showDetails()
    if missing:
      messagebox.showwarning('Load config', 'These files could not be found:\n\n' + '\n'.join(missing))
    return loaded, missing

  def askReplace(self):
    """'replace', 'add' or None: what to do with the data open when a config is loaded"""
    if not self.results:
      return 'replace'
    answer = {'value': None}
    dlg = tk.Toplevel(self.root)
    dlg.title('Load config')
    dlg.configure(bg=PAGE)
    dlg.transient(self.root)
    tk.Label(dlg, text='%d result%s are open. Load the config\'s files instead of them, or as well?' %
             (len(self.results), '' if len(self.results) == 1 else 's'), bg=PAGE, fg=INK, wraplength=360,
             justify='left').pack(padx=16, pady=(16, 10))
    row = tk.Frame(dlg, bg=PAGE)
    row.pack(padx=16, pady=(0, 14), anchor='e')
    for text, value, hover in (('Instead', 'replace', 'Close the results open now, then load the config'),
                               ('As well', 'add', 'Keep the results open now and add the config\'s files'),
                               ('Cancel', None, 'Load nothing')):
      tip(ttk.Button(row, text=text, command=lambda v=value: (answer.update(value=v), dlg.destroy())), hover).pack(side='left', padx=4)
    dlg.grab_set()
    self.root.wait_window(dlg)
    return answer['value']

  @staticmethod
  def readDoc(path, kind):
    with open(path) as f:
      doc = json.load(f)
    if doc.get('kind') != kind:
      raise ValueError('%s is a %s file, not a %s file' % (os.path.basename(path), doc.get('kind', 'unknown'), kind))
    return doc

  @staticmethod
  def writeDoc(path, doc):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w') as f:
      json.dump(doc, f, indent=2)

  def askSave(self, kind, ext):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    return filedialog.asksaveasfilename(title='Save %s' % kind, initialdir=CONFIG_DIR, initialfile='viewer' + ext,
                                        defaultextension=ext, filetypes=[(kind.capitalize(), '*' + ext), ('JSON', '*.json')])

  def askOpen(self, kind, ext):
    return filedialog.askopenfilename(title='Load %s' % kind, initialdir=CONFIG_DIR if os.path.isdir(CONFIG_DIR) else None,
                                      filetypes=[(kind.capitalize(), '*' + ext), ('JSON', '*.json'), ('All files', '*')])

  def savePreferences(self, path=None):
    path = path or self.askSave('preferences', PREFS_EXT)
    if path:
      self.writeDoc(path, self.preferences())
      self.configLabel.config(text='saved preferences to %s' % os.path.basename(path))
    return path

  def loadPreferences(self, path=None):
    path = path or self.askOpen('preferences', PREFS_EXT)
    if not path:
      return
    try:
      self.applyPreferences(self.readDoc(path, 'preferences'))
    except (OSError, ValueError) as e:
      messagebox.showerror('Load preferences', str(e))
      return
    self.configLabel.config(text='loaded preferences from %s' % os.path.basename(path))

  def saveConfig(self, path=None):
    path = path or self.askSave('config', CONFIG_EXT)
    if path:
      self.writeDoc(path, self.dataConfig(os.path.dirname(os.path.abspath(path))))
      self.configLabel.config(text='saved config (%d files) to %s' % (len(self.results), os.path.basename(path)))
    return path

  def loadConfig(self, path=None, replace=None):
    path = path or self.askOpen('config', CONFIG_EXT)
    if not path:
      return
    try:
      doc = self.readDoc(path, 'config')
    except (OSError, ValueError) as e:
      messagebox.showerror('Load config', str(e))
      return
    replace = replace or self.askReplace()
    if replace is None:
      return
    loaded, missing = self.applyConfig(doc, os.path.dirname(os.path.abspath(path)), replace == 'replace')
    self.configLabel.config(text='loaded config %s: %d files%s' % (os.path.basename(path), len(loaded),
                            ', %d missing' % len(missing) if missing else ''))

  def saveFull(self, path=None):
    """a preferences file, a config file, and a full file naming the two"""
    path = path or self.askSave('full', FULL_EXT)
    if not path:
      return
    base = path[:-len(FULL_EXT)] if path.endswith(FULL_EXT) else os.path.splitext(path)[0]
    prefs, config = base + PREFS_EXT, base + CONFIG_EXT
    self.savePreferences(prefs)
    self.saveConfig(config)
    self.writeDoc(path, {'kind': 'full', 'version': CONFIG_VERSION,
                         'preferences': os.path.basename(prefs), 'config': os.path.basename(config)})
    self.configLabel.config(text='saved %s, with %s and %s' % (os.path.basename(path), os.path.basename(prefs), os.path.basename(config)))
    return path

  def loadFull(self, path=None, replace=None):
    path = path or self.askOpen('full', FULL_EXT)
    if not path:
      return
    try:
      doc = self.readDoc(path, 'full')
    except (OSError, ValueError) as e:
      messagebox.showerror('Load full', str(e))
      return
    where = os.path.dirname(os.path.abspath(path))
    replace = replace or self.askReplace()
    if replace is None:
      return
    if doc.get('preferences'):
      self.loadPreferences(os.path.join(where, doc['preferences']))
    if doc.get('config'):
      self.loadConfig(os.path.join(where, doc['config']), replace)
    self.configLabel.config(text='loaded %s' % os.path.basename(path))
