#!/usr/bin/env python3
"""
CSV path viewer - plots the xy paths of objects recorded in a csv file.

usage: python3 viewer/csv_viewer.py [file.csv ...]
  with no file, opens the newest csv in logs/ (or its study folders)
  several files open together, one tab each in the right panel

Handles different csv formats:
  - delimiter (comma, semicolon, tab, spaces) and header row are detected
  - x/y column pairs are found by name (x/y, pos_x/pos_y, x1/y1, earth.x/earth.y, posX/posY ...)
    and each pair is plotted as a path
  - a text column (e.g. 'object', 'id', 'name') can split rows into one path per object
  - any two columns can be plotted against each other with Data > Choose paths...

Controls:
  drag                pan
  shift + drag        zoom to box
  mouse wheel         zoom around cursor
  + / -               zoom in / out
  arrow keys          pan
  0 or f              fit to data
  hover a path        show the values of the nearest row

Modes:
  X / Y path          each object's path in the plane
  Distance / time     distance from the origin, sqrt(x^2 + y^2), against t or pt,
                      with markers along the line at intervals of the other time

Time markers: points along each path every N units of global time (t) or proper time (pt).
Results panel: a list of the loaded csvs, grouped first by environment (the bodies listed in their
logs - runs with the same bodies share one) and then by folder, with each one's path colours, rows
and last t. Click the Shown column (or press space) to show or hide a result, folder or environment;
All / None / Only selected / Close act on the picked rows, and a double click shows only that row.
Background picks the environment the backgrounds are drawn for (by default the selected result's),
marked ◆ in the list. Below the list, the selected result's colour and line style (solid, dashed,
dotted) for each path, a summary (environment, calculator, dt, times, distance, speed and any
accuracy lines from the log), then its .log file (same name), a Show checkbox, and a Straight line
checkbox that adds a dashed comparison for each path: where it would be with no gravity,
p0 + v0 (t - t0), from its initial velocity. File > Open adds more results.

Sim tab: run a new simulation (studies/run_study.py, in its own process). Pick Orbital or Hyperbolic, then Set up...
for the bodies (mass, black / white, position), the particle's start and velocity, the calculator, dt, how often
to write a csv row, and the end: elapsed time, min / max distance (to the nearest body), or a number of orbits.
The setup starts from the selected run (From selected run refills it). Start estimates the duration and asks
before running; a progress bar (with Cancel) shows under the plot, and the run's files open here when it finishes.
The run is its own process: closing the viewer doesn't stop it, and the next viewer opened follows it, or opens
its files if it has finished (logs/.sims keeps each run's status).

Config tab: save or load preferences (how the viewer looks - mode, axes, backgrounds, legends... - never the
data), a config (the files open and their settings - colours, shown orbits, selection, view; loading one asks
whether to open its files instead of or as well as those open), or full (a preferences file, a config file and
a full file naming both). Files go in configs/ by default.

Hover over a tab, button or checkbox for what it does.

Bodies and flow: in X / Y mode the bodies listed in the selected tab's log are drawn as circles
(black or white), with optional arrows for the flow of space (u) and for gravity (g) at regular points,
lines of equal flow speed |u|, the Schwarzschild radius 2GM/c^2 of each body (a dotted circle, or a dotted
line at that distance in distance / time mode), and flow lines: 20 from each body, starting one Sun radius out at the
escape speed |u| heading away from its centre and following the combined g (engine/flow_lines.py); in distance / time
mode, the path of space itself along the line from the origin, dd/dt = u, repeated at regular times.
"""
import csv
from datetime import datetime
import glob
import json
import math
import os
import queue
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   #the project folder
sys.path.insert(0, ROOT)   #for engine/ and studies/
from engine.constants import AU, C, DAY, G, MS, RSUN

#colours
SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
SURFACE = '#fcfcfb'   #plot area
PAGE = '#f9f9f7'      #around the plot
INK = '#0b0b0b'
INK2 = '#52514e'
MUTED = '#898781'
GRID = '#e1e0d9'
AXIS = '#c3c2b7'

#distance units, assuming the csv is in metres: (menu label, metres per unit, axis suffix)
UNITS = [
  ('Raw values', 1.0, ''),
  ('Metres', 1.0, 'm'),
  ('Kilometres', 1e3, 'km'),
  ('Astronomical units', AU, 'AU'),
  ('Light-seconds', C, 'ls'),
]

MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, MARGIN_BOTTOM = 90, 24, 44, 56
ZOOM_STEP = 1.5
PAN_STEP = 0.2   #fraction of the view per arrow press
GROUP_NAMES = ('id', 'object', 'obj', 'name', 'body', 'particle', 'label', 'series')
#time columns that markers can follow: (menu label, column names it matches)
TIME_COLUMNS = [
  ('Global time (t)', ('t', 'time', 'coord_time')),
  ('Proper time (pt)', ('pt', 'tau', 'proper_time')),
]
MODES = [('xy', 'X / Y path'), ('time', 'Distance / time')]
MAX_TIME_MARKS = 5000
FLOW_SPACING = 46   #pixels between flow arrows
CONTOUR_SPACING = 10   #pixels between the points the equal-u lines are traced from
G_ARROW = INK2      #gravity arrows, darker than the flow arrows
CONE = '#8a7fd0'    #light cones
FLOW_LINE = '#c4a46e'   #flow lines
SCHWARZ = INK       #Schwarzschild radius, dotted
PERIAPSIS, APOAPSIS = 'periapsis', 'apoapsis'   #key entries for the apsis markers (drawn in each orbit's colour)
SCHWARZ_DASH = (2, 3)
FLOW_LINES = 20     #flow lines from each body
FLOW_LINE_STEP = 0.01   #each step of a flow line moves about this fraction of the distance to the nearest body
FLOW_LINE_REACH = 4*AU  #flow lines stop this far from the origin
FLOW_LINE_POINTS = 1000 #distance / time mode: points across the screen the flow line is traced through
FLOW_LINE_COPIES = 8    #distance / time mode: about this many copies of the flow line up the time axis
END_COLORS = ['#c2410c', '#0f766e', '#7c3aed', '#a16207']   #velocity arrows at path ends, one per velocity pair
END_LENGTH = 30     #pixels for the largest velocity arrow at a path end
CONE_SIZE = 12      #pixels from a cone's point to the edge of its light circle (x/y), or to its cap (distance / time)
BODY_RADIUS = 9     #pixels
REPLAY_SECONDS = 20   #at 1x a replay runs the whole time span in this many seconds
REPLAY_SPEEDS = ['0.1×', '0.25×', '0.5×', '1×', '2×', '5×', '10×', '20×']
REPLAY_FRAME = 40     #milliseconds between replay frames
LINE_STYLES = [('solid', ()), ('dashed', (8, 5)), ('dotted', (2, 4))]   #path line styles: name, tk dash pattern
BODY_LINE = re.compile(r'^body \d+: mass (\S+) kg .*?x (\S+) m\s+y (\S+) m\s+(black|white)', re.M)

try:
  import engine.flow as flow   #the simulation's own flow calculation
except Exception:
  flow = None

try:
  import engine.flow_lines as flowlines   #the outward lines from each body
except Exception:
  flowlines = None

try:
  import studies.run_study as simrun   #runs a sim from the Sim tab
except Exception:
  simrun = None

CONFIG_DIR = os.path.join(ROOT, 'configs')   #where saved preferences and configs go
CONFIG_VERSION = 1
PREFS_EXT, CONFIG_EXT, FULL_EXT = '.prefs.json', '.config.json', '.full.json'
#the viewer's look, saved as preferences: none of it depends on the data open
PREF_VARS = ['mode', 'unit', 'logX', 'logY', 'equalAspect', 'ctTime', 'reverseX', 'showGrid', 'showMarkers',
             'showTimeMarks', 'timeColumn', 'showBodies', 'showFlow', 'showGravity', 'showContours', 'showFlowLines',
             'showSchwarzschild', 'showCones', 'showPathLegend', 'showFieldKey', 'showMarkNote', 'showMarkLabels',
             'showBodyLabels', 'showSidebar', 'replaySpeed']
SIM_DIR = os.path.join(ROOT, 'logs', '.sims')   #status files of sims run from the viewer
SIM_TYPES = [('Orbital', 'orbit'), ('Hyperbolic', 'hyperbolic')]
END_KINDS = [('time', 'Elapsed time'), ('min', 'Min distance to a body'), ('max', 'Max distance from every body'),
             ('orbits', 'Number of orbits')]
DIST_UNITS = [('m', 1.0), ('km', 1e3), ('AU', AU), ('RSUN', RSUN)]
VEL_UNITS = [('m/s', 1.0), ('km/s', 1e3), ('c', C)]


# ---------------------------------------------------------------- data

class Dataset:
  """a csv file read into columns"""

  def __init__(self, path):
    self.path = path
    with open(path, newline='') as f:
      text = f.read()
    lines = [l for l in text.splitlines() if l.strip() and not l.lstrip().startswith('#')]
    if not lines:
      raise ValueError('file is empty')

    try:
      dialect = csv.Sniffer().sniff('\n'.join(lines[:50]), delimiters=',;\t ')
      delimiter = dialect.delimiter
    except csv.Error:
      delimiter = ','
    if delimiter == ' ':
      rows = [l.split() for l in lines]
    else:
      rows = [[c.strip() for c in r] for r in csv.reader(lines, delimiter=delimiter)]

    width = max(len(r) for r in rows)
    rows = [r + [''] * (width - len(r)) for r in rows]

    #header if the first row has text where the second row has numbers
    first = rows[0]
    hasHeader = any(not isNumber(c) for c in first) and (len(rows) == 1 or sum(isNumber(c) for c in rows[1]) >= sum(isNumber(c) for c in first))
    if hasHeader:
      names, rows = first, rows[1:]
    else:
      names = ['col%d' % i for i in range(width)]
    self.names = uniqueNames(names)
    self.nrows = len(rows)

    self.text = {}
    self.values = {}
    self.numeric = []
    for i, name in enumerate(self.names):
      raw = [r[i] for r in rows]
      vals = np.array([toFloat(c) for c in raw])
      self.text[name] = raw
      self.values[name] = vals
      filled = sum(1 for c in raw if c != '')
      if filled and np.count_nonzero(~np.isnan(vals)) >= 0.9 * filled:
        self.numeric.append(name)

  def pairs(self):
    """x/y column pairs found by name, as (label, xcol, ycol)"""
    found = []
    for name in self.numeric:
      for yname, label in yPartners(name):
        if yname in self.numeric and yname != name:
          found.append((label, name, yname))
          break
    return found

  def groupColumns(self):
    """columns that could split the rows into separate objects"""
    out = []
    for name in self.names:
      unique = len(set(self.text[name]))
      isText = name not in self.numeric
      if (isText and 1 < unique <= 100) or (name.lower() in GROUP_NAMES and 1 < unique <= 100):
        out.append(name)
    return out

  def defaultSelection(self):
    """pairs and group column to show when a file is first opened"""
    pairs = self.pairs()
    positions = [p for p in pairs if isPositionLabel(p[0])]
    if positions:
      chosen = [(x, y) for _, x, y in positions]
    elif pairs:
      chosen = [(pairs[0][1], pairs[0][2])]
    elif len(self.numeric) >= 2:
      chosen = [(self.numeric[0], self.numeric[1])]
    else:
      chosen = []
    groups = self.groupColumns()
    named = [g for g in groups if g.lower() in GROUP_NAMES]
    group = (named or groups or [None])[0]
    return chosen, group


def isNumber(s):
  try:
    float(s)
    return True
  except ValueError:
    return False


def toFloat(s):
  try:
    return float(s)
  except ValueError:
    return np.nan


def uniqueNames(names):
  out, seen = [], {}
  for i, n in enumerate(names):
    n = n.strip() or 'col%d' % i
    if n in seen:
      seen[n] += 1
      n = '%s_%d' % (n, seen[n])
    else:
      seen[n] = 0
    out.append(n)
  return out


def yPartners(name):
  """possible y column names for an x column name, with a label for the pair"""
  out = []
  #x as its own token: x, pos_x, x1, earth.x
  for m in re.finditer(r'(?<![A-Za-z])([xX])(?![A-Za-z])', name):
    y = 'y' if m.group(1) == 'x' else 'Y'
    yname = name[:m.start(1)] + y + name[m.end(1):]
    label = (name[:m.start(1)] + name[m.end(1):]).strip(' _-.:')
    out.append((yname, label))
  #camel case: posX
  if re.search(r'[a-z]X$', name):
    out.append((name[:-1] + 'Y', name[:-1]))
  return out


def isPositionLabel(label):
  """treat a pair as a position unless its label looks like velocity, acceleration or force"""
  return not re.match(r'^(v|u|w|a|vel|velocity|acc|accel|f|force)\d*$', label.lower())


# ---------------------------------------------------------------- axes

def niceStep(span, count):
  raw = span / max(count, 1)
  mag = 10 ** math.floor(math.log10(raw))
  for m in (1, 2, 2.5, 5, 10):
    if raw <= m * mag:
      return m * mag
  return 10 * mag


def linearTicks(v0, v1, count):
  if not (v1 > v0):
    return [], 1.0
  step = niceStep(v1 - v0, count)
  start = math.ceil(v0 / step) * step
  ticks = []
  t = start
  while t <= v1 + step * 1e-9:
    ticks.append(0.0 if abs(t) < step * 1e-9 else t)
    t += step
  return ticks, step


def formatTicks(vals, step):
  """labels for one axis, all in the same style: plain decimals, or one shared exponent"""
  biggest = max([abs(v) for v in vals] + [step])
  stepExp = math.floor(math.log10(step) + 1e-9)
  #2.5 style steps need one more digit than the step's exponent suggests
  extra = 0 if abs(step / 10 ** stepExp - round(step / 10 ** stepExp)) < 1e-9 else 1
  if 1e-3 <= biggest < 1e6:
    decimals = max(0, -stepExp + extra)
    return ['%.*f' % (decimals, v) for v in vals]
  exp = math.floor(math.log10(biggest) + 1e-9)
  decimals = max(0, exp - stepExp + extra)
  return ['0' if v == 0 else '%.*fe%d' % (decimals, v / 10 ** exp, exp) for v in vals]


def formatTick(v, step):
  return formatTicks([v], step)[0]


def formatShort(v):
  """compact number: 250, 0.5, 5e7"""
  return re.sub(r'e([+-])0*(\d)', lambda m: 'e' + ('-' if m.group(1) == '-' else '') + m.group(2), '%g' % v)


def formatValue(v):
  if isinstance(v, float) and np.isnan(v):
    return ''
  return '%.6g' % v


# ---------------------------------------------------------------- viewer

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


def mixColour(c1, c2, f):
  """the colour a fraction f of the way from c1 to c2 ('#rrggbb'), mixed in RGB"""
  a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
  b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
  return '#%02x%02x%02x' % tuple(round(x + (y - x) * f) for x, y in zip(a, b))


class Path:
  def __init__(self, result, name, xcol, ycol, rows):
    self.result = result
    self.name = name
    self.xcol = xcol
    self.ycol = ycol
    self.rows = rows   #row indices into the result's dataset
    self.color = SERIES[0]
    self.color2 = None     #orbit runs: the last shown orbit's colour (the first is color, those between a mix)
    self.style = 'solid'   #one of LINE_STYLES

  @property
  def dash(self):
    return dict(LINE_STYLES)[self.style]


class Orbit:
  """
  one orbit of an orbit run: the rows from one crossing of the +y axis to the next (as Calculator.orbitalSim
  counts them), with its periapsis and apoapsis; the part before the first crossing and after the last are kept
  as partial orbits
  """

  def __init__(self, result, name, rows, t0, t1, peri, apo):
    self.result = result
    self.name = name
    self.rows = rows      #data rows, plus the first row of the next orbit so the line joins up
    self.t0, self.t1 = t0, t1
    self.peri = peri      #(x m, y m, t s) or None
    self.apo = apo
    self.visible = tk.BooleanVar(value=True)
    self.listItem = None

  @property
  def full(self):
    """a whole orbit, not the part before the first crossing or after the last"""
    return self.name.startswith('orbit')


class Environment:
  """
  the gravitational bodies a run happens in; results with the same bodies share one, and so share their
  backgrounds (flow, gravity, cones, flow lines, Schwarzschild radius)
  """

  def __init__(self, bodies):
    self.bodies = bodies   #(mass kg, x m, y m, black)
    self.flowCalc = None
    self.flowLines = None  #worked out when first drawn
    if bodies and flow is not None:
      self.flowCalc = flow.Calculator([flow.Body(mass, x, y, black) for mass, x, y, black in bodies])
      self.flowCalc.warn = lambda message: None   #g=0 on a grid point just means no arrow
    self.name = self.describe(bodies)

  @staticmethod
  def key(bodies):
    return tuple((float('%.6g' % m), float('%.6g' % x), float('%.6g' % y), black) for m, x, y, black in bodies)

  @staticmethod
  def describe(bodies):
    """e.g. '4e6 MS black at origin', or '2 bodies: 1 MS white at (-0.5, 0) AU, 1 MS black at (0.5, 0) AU'"""
    if not bodies:
      return 'No bodies'
    ms = MS
    parts = []
    for mass, x, y, black in bodies:
      where = 'origin' if x == 0 and y == 0 else '(%s, %s) AU' % (formatShort(float('%.4g' % (x / AU))), formatShort(float('%.4g' % (y / AU))))
      parts.append('%s MS %s at %s' % (formatShort(float('%.4g' % (mass / ms))), 'black' if black else 'white', where))
    return parts[0] if len(parts) == 1 else '%d bodies: %s' % (len(parts), ', '.join(parts))


class Result:
  """one loaded csv: its data, log, bodies, paths and tab"""

  def __init__(self, data, colorStart):
    self.data = data
    self.path = data.path
    self.name = studyName(data.path)
    self.selection, self.group = data.defaultSelection()
    self.colorStart = colorStart   #index into SERIES for this result's first path
    self.paths = []
    self.logText = ''
    self.bodies = []      #(mass kg, x m, y m, black) from the log
    self.env = None       #the Environment of those bodies
    self.styles = {}      #path name -> (colour, line style) the user picked, kept through a reload
    self.studyType = None  #'orbit' or 'hyperbolic', from the log's study type line
    self.orbits = []      #Orbit for each orbit of an orbit run
    self.orbitMask = None #rows of the shown orbits, or None to show every row
    self.showPeri = tk.BooleanVar(value=False)   #periapsis markers (open squares) for each shown orbit
    self.showApo = tk.BooleanVar(value=False)    #apoapsis markers (open diamonds)
    self.visible = tk.BooleanVar(value=True)
    self.showStraight = tk.BooleanVar(value=False)   #dashed straight-line comparison for each path
    self.showEnds = tk.BooleanVar(value=True)   #arrows for the velocity columns at the end of each path
    self.listItem = None   #its row in the results list


def studyName(path):
  """file name without the extension or the _YYYY-MM-DD_HH-MM-SS the logger adds"""
  name = os.path.splitext(os.path.basename(path))[0]
  return re.sub(r'_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$', '', name)


class Viewer:

  def __init__(self, root, paths=None):
    self.root = root
    self.results = []
    self.environments = {}   #Environment.key(bodies) -> Environment, shared by results with the same bodies
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

  # ---- ui construction

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
    viewMenu.add_checkbutton(label='Schwarzschild radius', variable=self.showSchwarzschild, command=self.redraw)
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
    check(backgrounds, 'Schwarzschild radius', self.showSchwarzschild, self.redraw)
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

  # ---- config: save and load preferences (how things look), configs (the data and its settings), or both

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

  # ---- sim: run a new simulation from the viewer (studies/run_study.py, in its own process)

  def simInit(self):
    """the sim settings, shared by the Sim tab and its setup window"""
    self.simType = tk.StringVar(value='Orbital')
    self.simVars = {k: tk.StringVar() for k in ('name', 'calculator', 'distUnit', 'velUnit', 'dt', 'every',
                                                  'endKind', 'endValue', 'px', 'py', 'vx', 'vy')}
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
        velocity = next(((vx, vy) for label, vx, vy in data.pairs() if re.match(r'^(v|vel|velocity)\d*$', label.lower())), None)
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
    text(w, 'dt (s)', 11, 0); entry(w, v['dt'], 11, 1)
    text(w, 'csv row every (s)', 11, 2); entry(w, v['every'], 11, 3)
    text(w, 'End when', 12, 0)
    self.simEndBox = ttk.Combobox(w, state='readonly', width=26, textvariable=v['endKind'])
    self.simEndBox.bind('<<ComboboxSelected>>', lambda e: self.simEndChanged())
    self.simEndBox.grid(row=12, column=1, columnspan=2, sticky='w', **pad)
    entry(w, v['endValue'], 12, 3)
    self.simEndUnit = tk.Label(w, text='', bg=PAGE, fg=INK2)
    self.simEndUnit.grid(row=12, column=4, sticky='w')
    tk.Label(w, text='min / max distance: from the nearest body (any body). Orbits are counted round the origin.',
             bg=PAGE, fg=MUTED, font=('Helvetica', 10)).grid(row=13, column=0, columnspan=6, sticky='w', padx=8)

    buttons = tk.Frame(w, bg=PAGE)
    buttons.grid(row=14, column=0, columnspan=6, sticky='e', padx=8, pady=10)
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
      text = 'Estimated duration: about %s\n(%.3g steps of %g s; %s).' % (self.duration(seconds), steps, cfg['dt'], how)
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

  # ---- replay

  def replayRange(self):
    """the global time span of the shown paths, or None"""
    ts = [p.tvals[np.isfinite(p.tvals)] for p in self.paths if p.tvals is not None]
    ts = [t for t in ts if t.size]
    if not ts:
      return None
    return min(float(t.min()) for t in ts), max(float(t.max()) for t in ts)

  def replayPlay(self):
    span = self.replayRange()
    if span is None:
      return
    start, end = span
    if self.replayState == 'stopped' or self.replayT is None or self.replayT >= end:
      #from the beginning, with the trail from there (a cleared trail stays cleared until it is restored)
      cleared = self.replayState != 'stopped' and self.trailStart is not None and self.trailStart > start
      self.replayT = start
      self.trailStart = self.replayT if cleared else start
    self.replayState = 'playing'
    self.replayLast = time.time()
    self.replayTick()

  def replayTick(self):
    self.replayJob = None
    if self.replayState != 'playing':
      return
    span = self.replayRange()
    if span is None:
      self.replayStop()
      return
    start, end = span
    now = time.time()
    speed = float(self.replaySpeed.get().rstrip('×'))
    self.replayT += speed * (end - start) / REPLAY_SECONDS * (now - self.replayLast)
    self.replayLast = now
    if self.replayT >= end:
      self.replayT = end
      self.replayState = 'paused'   #at the end: Play starts again from the beginning
    self.replayShow()
    if self.replayState == 'playing':
      self.replayJob = self.root.after(REPLAY_FRAME, self.replayTick)

  def replayPause(self):
    if self.replayState == 'playing':
      self.replayState = 'paused'
      if self.replayJob:
        self.root.after_cancel(self.replayJob)
        self.replayJob = None
      self.replayShow()

  def replayRewind(self):
    span = self.replayRange()
    if span is None:
      return
    self.replayT = self.trailStart = span[0]
    if self.replayState == 'stopped':
      self.replayState = 'paused'
    self.replayLast = time.time()
    self.replayShow()

  def replayStop(self):
    """back to showing every path in full"""
    if self.replayJob:
      self.root.after_cancel(self.replayJob)
      self.replayJob = None
    self.replayState = 'stopped'
    self.replayT = self.trailStart = None
    self.replayShow()

  def replayClear(self):
    """remove the trails drawn so far; the replay carries on drawing from here"""
    span = self.replayRange()
    if span is None:
      return
    if self.replayState == 'stopped':
      self.replayState = 'paused'
      self.replayT = span[1]   #everything cleared, at the end
    self.trailStart = self.replayT
    self.replayShow()

  def replayRestore(self):
    """bring back the whole trail, from the start up to the replay time"""
    span = self.replayRange()
    if span is None or self.replayState == 'stopped':
      return
    self.trailStart = span[0]
    self.replayShow()

  def replaySeek(self, f):
    """the slider: jump to a fraction f of the way through the time span"""
    if getattr(self, 'replaySetting', False):
      return
    span = self.replayRange()
    if span is None:
      return
    start, end = span
    if self.replayState == 'stopped':
      self.replayState = 'paused'
      self.trailStart = start
    self.replayT = start + f * (end - start)
    self.trailStart = min(self.trailStart, self.replayT)
    self.replayLast = time.time()
    self.replayShow()

  def replayShow(self):
    """redraw, and move the slider and label to the replay time"""
    span = self.replayRange()
    self.replaySetting = True
    if self.replayState == 'stopped' or span is None:
      self.replayPos.set(0.0)
      self.replayLabel.config(text='stopped - 1× plays the whole run in %d s' % REPLAY_SECONDS)
    else:
      start, end = span
      self.replayPos.set((self.replayT - start) / (end - start) if end > start else 1.0)
      self.replayLabel.config(text='%s  t = %s of %s s' % (self.replayState, formatValue(self.replayT), formatValue(end)))
    self.replaySetting = False
    self.redraw()

  def legendOptions(self):
    return [('Path legend', self.showPathLegend), ('Background key', self.showFieldKey),
            ('Marker interval', self.showMarkNote), ('Marker times', self.showMarkLabels), ('Body labels', self.showBodyLabels)]

  def setLegends(self, on):
    for _, var in self.legendOptions():
      var.set(on)
    self.redraw()

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
      velocity = next(((vx, vy) for label, vx, vy in data.pairs() if re.match(r'^(v|vel|velocity)\d*$', label.lower())), None)
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
    envs = [e for e in self.activeEnvironments() if e.bodies]
    if self.fieldChoice not in envs:
      self.fieldChoice = None
    self.fieldBox.config(values=["Selected result's environment"] + [e.name for e in envs])
    self.fieldBox.set(self.fieldChoice.name if self.fieldChoice else "Selected result's environment")

  def fieldChoiceChanged(self):
    self.fieldChoice = next((e for e in self.activeEnvironments() if e.bodies and e.name == self.fieldBox.get()), None)
    self.markBackground()
    self.redraw()

  def readLog(self, result):
    """the .log file with the same name as the csv, and the bodies it lists"""
    logPath = os.path.splitext(result.path)[0] + '.log'
    result.bodies = []
    if not os.path.exists(logPath):
      result.logText = 'No log file - expected one at\n%s' % logPath
      self.setEnvironment(result)
      return
    with open(logPath) as f:
      result.logText = f.read()
    for m in BODY_LINE.finditer(result.logText):
      result.bodies.append((float(m.group(1)), float(m.group(2)), float(m.group(3)), m.group(4) == 'black'))
    self.setEnvironment(result)
    self.findOrbits(result)

  def findOrbits(self, result):
    """
    split an orbit run into its orbits, at the times its log says each orbit ended
    the full 'orbit N: t ... s  periapsis ...  apoapsis ...' lines give the apsides too; older logs only have
    'orbit <days> days', and the apsides are then the closest and farthest rows of each orbit
    """
    log, data = re.sub(r'np\.float64\(([^()]*)\)', r'\1', result.logText), result.data   #numbers printed by numpy's repr
    old = result.orbits
    result.orbits, result.orbitMask = [], None
    m = re.search(r'^(?:study|test) type:\s*(\w+)', log, re.M)   #'test type' in older logs
    result.studyType = m.group(1) if m else ('orbit' if re.search(r'^orbit\s+\S+ days', log, re.M) else None)
    tcol = self.columnForTime(TIME_COLUMNS[0][0], data)
    if result.studyType != 'orbit' or not tcol or not result.selection:
      return
    full = re.findall(r'^orbit \d+: t (\S+) s\s+periapsis \S+ m at \((\S+), (\S+)\)\s+apoapsis \S+ m at \((\S+), (\S+)\)', log, re.M)
    if full:
      ends = [float(f[0]) for f in full]
      apsides = [((float(f[1]), float(f[2])), (float(f[3]), float(f[4]))) for f in full]
    else:
      ends = [float(d) * DAY for d in re.findall(r'^orbit\s+(\S+) days', log, re.M)]
      apsides = [None] * len(ends)
    if not ends:
      return
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
    key = Environment.key(result.bodies)
    if key not in self.environments:
      self.environments[key] = Environment(result.bodies)
    result.env = self.environments[key]

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

  # ---- loading

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

    velocity = next(((vx, vy) for label, vx, vy in data.pairs()
                     if re.match(r'^(v|vel|velocity)\d*$', label.lower())), None)
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

  # ---- time markers

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

  @staticmethod
  def toPlot(v, log):
    if not log:
      return v
    with np.errstate(divide='ignore', invalid='ignore'):
      return np.where(v > 0, np.log10(np.where(v > 0, v, 1)), np.nan)

  # ---- view changes

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

  # ---- coordinate conversion

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

  # ---- drawing

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

  def replayWindow(self, p):
    """the rows of p inside the replay's trail, or None when not replaying (or p has no global t)"""
    if self.replayState == 'stopped' or p.tvals is None:
      return None
    return (p.tvals >= self.trailStart) & (p.tvals <= self.replayT)

  def replayHead(self, p):
    """where p is at the replay time, in plotted space, and the row just before it; or None"""
    if self.replayState == 'stopped' or p.tvals is None:
      return None
    t = p.tvals
    j = np.searchsorted(t, self.replayT, side='right') - 1
    if j < 0 or self.replayT < self.trailStart:
      return None
    if j + 1 < t.size and t[j + 1] > t[j] and np.isfinite(p.x[j + 1]) and np.isfinite(p.y[j + 1]):
      f = (self.replayT - t[j]) / (t[j + 1] - t[j])
      return p.x[j] + f * (p.x[j + 1] - p.x[j]), p.y[j] + f * (p.y[j + 1] - p.y[j]), j
    return p.x[j], p.y[j], j

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

  # ---- hover

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

  # ---- events

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

  # ---- dialogs

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


def newestCsv():
  logs = os.path.join(ROOT, 'logs')
  files = [f for f in glob.glob(os.path.join(logs, '**', '*.csv'), recursive=True) if '.sims' not in f]   #a folder per test
  return max(files, key=os.path.getmtime) if files else None


def main():
  paths = sys.argv[1:] or [p for p in [newestCsv()] if p]
  root = tk.Tk()
  Viewer(root, paths)
  root.mainloop()


if __name__ == '__main__':
  main()
