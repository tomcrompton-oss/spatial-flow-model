"""hover text for the viewer's tabs, buttons and checkboxes"""
import tkinter as tk

from viewer.settings import *


class Tooltip:
  """hover text for a widget: shown after a short pause over it, hidden on leaving or clicking"""
  DELAY = 600   #ms

  def __init__(self, widget, text):
    self.widget, self.text = widget, text
    self.job = self.window = None
    widget.bind('<Enter>', self.schedule, add='+')
    widget.bind('<Leave>', self.hide, add='+')
    widget.bind('<ButtonPress>', self.hide, add='+')

  def schedule(self, event=None):
    self.hide()
    if self.text:
      self.job = self.widget.after(self.DELAY, self.show)

  def show(self, x=None, y=None):
    self.job = None
    if not self.text:
      return
    x = self.widget.winfo_pointerx() + 12 if x is None else x
    y = self.widget.winfo_pointery() + 16 if y is None else y
    self.window = tk.Toplevel(self.widget)
    self.window.wm_overrideredirect(True)
    self.window.wm_geometry('+%d+%d' % (x, y))
    tk.Label(self.window, text=self.text, justify='left', wraplength=340, bg='#fffdf2', fg=INK,
             relief='solid', bd=1, padx=6, pady=4, font=('Helvetica', 11)).pack()

  def hide(self, event=None):
    if self.job:
      self.widget.after_cancel(self.job)
      self.job = None
    if self.window:
      self.window.destroy()
      self.window = None


class TabTips(Tooltip):
  """hover text for each tab of a notebook, by the tab under the pointer"""

  def __init__(self, notebook, tips):
    self.tips, self.current = tips, None
    super().__init__(notebook, '')
    notebook.bind('<Motion>', self.moved, add='+')

  def schedule(self, event=None):
    pass   #the pointer's motion picks the tab

  def moved(self, event):
    nb = self.widget
    try:
      tab = nb.tab(nb.index('@%d,%d' % (event.x, event.y)), 'text') if nb.identify(event.x, event.y) else None
    except tk.TclError:
      tab = None
    if tab != self.current:
      self.hide()
      self.current = tab
      self.text = self.tips.get(tab, '')
      if self.text:
        self.job = nb.after(self.DELAY, self.show)

  def hide(self, event=None):
    super().hide(event)
    if event is not None and event.type == tk.EventType.Leave:
      self.current = None


TAB_TIPS = {
  'Data': 'Open, reload and close csv files, and choose which columns make each path',
  'Mode': 'Plot paths in x / y, or distance from the origin against time',
  'Position': 'Zoom, pan and fit the view, or set an exact range',
  'Axis': 'Log axes, grid, units, and equal aspect (x / y) or ct (distance / time)',
  'Markers': 'Time markers along each path, and start / end markers',
  'Backgrounds': 'Fields drawn behind the paths for the selected environment: bodies, flow, gravity, cones and more',
  'Replay': 'Replay the shown runs, drawing each path as its data plays',
  'Legends': 'Show or hide the legends and labels on the plot',
  'Sim': 'Set up and run a new simulation; it opens here when it finishes',
  'Config': 'Save and load preferences (how things look), configs (the data open and its settings), or both',
}
TIPS = {
  'Open...': 'Open one or more csv files (each with its .log beside it)',
  'Reload all': 'Read every open file again from disk, keeping its settings',
  'Close result': 'Close the selected result',
  'Choose paths...': 'Pick which column pairs make the paths of the selected result, and how rows are grouped',
  'X / Y path': 'Plot each path\'s x against y',
  'Distance / time': 'Plot each path\'s distance from the origin against time',
  'Reverse distance (0 on the right)': 'Distance / time mode: run the distance axis right to left, so 0 is on the right',
  'Zoom in': 'Zoom in on the middle of the view (or use the scroll wheel over the plot)',
  'Zoom out': 'Zoom out from the middle of the view',
  'Fit': 'Fit the view to the shown paths',
  '\u2190': 'Pan left', '\u2192': 'Pan right', '\u2191': 'Pan up', '\u2193': 'Pan down',
  'Set range...': 'Type the exact axis ranges',
  'Log X': 'Logarithmic x axis', 'Log Y': 'Logarithmic y axis', 'Grid': 'Grid lines behind the plot',
  'Time markers': 'A dot along each path every interval of time',
  'Apply': 'Use the interval typed in the box', 'Auto': 'Pick a round interval giving about 10 markers',
  'Start / end markers': 'Open circle at each path\'s start, filled at its end',
  'Bodies': 'The bodies in the environment\'s log: filled black, open white',
  'u arrows': 'Arrows for the flow of space u at regular points',
  'g arrows': 'Arrows for the combined gravity g at regular points',
  'Lines of equal u': 'Contours of equal flow speed |u|',
  'Flow lines': 'x / y: lines out from each body at the escape speed under g. Distance / time: space moving at u, repeated',
  'Schwarzschild radius': 'Each body\'s 2GM/c\u00b2: a dotted circle (x / y) or a dotted line (distance / time)',
  'Light cones (distance / time)': 'The local speed of light out and in (u \u00b1 c) at regular points; needs global time t',
  '\u25b6 Play': 'Replay from here (from the start if at the end), drawing the paths as the data plays',
  '\u275a\u275a Pause': 'Hold the replay where it is', '\u23ee Rewind': 'Back to the start of the replay',
  '\u25a0 Stop': 'End the replay and show every path in full',
  'Clear trails': 'Remove the trails drawn so far; the replay carries on drawing from here',
  'Restore trails': 'Bring back the whole trail from the start to the replay time',
  'Path legend': 'Path names and colours, top right', 'Background key': 'What the backgrounds and arrows mean, bottom left',
  'Marker interval': 'The \u2018every N of t\u2019 note above the plot', 'Marker times': 'The time beside each time marker',
  'Body labels': 'Each body\'s mass',
  'Set up...': 'Open the sim setup: bodies, particle, steps and end condition',
  'From selected run': 'Fill the sim setup from the selected run',
  '\u25b6 Start': 'Estimate how long the sim will take, then run it after you confirm',
  'Equal aspect': 'The same scale on both axes (x / y mode)',
  'Only selected': 'Show only the selected rows (results, folders, environments or orbits)',
  'Close': 'Close the selected results',
  'Show': 'Show or hide this result\'s paths',
  'Straight line': 'A dashed line where each path would go with no gravity, from its first velocity',
  'End arrows': 'Arrows at each path end for its velocity columns (v and u)',
  'Periapsis': 'An open square at each whole orbit\'s periapsis', 'Apoapsis': 'An open diamond at each whole orbit\'s apoapsis',
  'Cancel': 'Stop the running sim; the files it has written so far are kept',
  'Save preferences...': 'Save how the viewer looks (mode, backgrounds, legends, units...) - not the data',
  'Load preferences...': 'Load saved preferences; the data open stays as it is',
  'Save config...': 'Save the files open and their settings (colours, shown orbits, view...)',
  'Load config...': 'Open the files in a saved config and their settings, instead of or as well as the data open now',
  'Save full...': 'Save a preferences file, a config file, and a full file that loads both',
  'Load full...': 'Load a full file: its preferences, then its config',
}


def tip(widget, text):
  """give a widget hover text (from TIPS by its label if text is None); returns the widget"""
  if text:
    widget.tooltip = Tooltip(widget, text)
  return widget
