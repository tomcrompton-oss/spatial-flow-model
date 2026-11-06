"""a loaded csv and what is made from it: datasets, results, paths, orbits, environments, and formatting helpers"""
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

from viewer.settings import *


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


def velocityColumns(data):
  """the x and y columns of a dataset's velocity (v_x / v_y, vel_x ...), or None"""
  return next(((vx, vy) for label, vx, vy in data.pairs() if re.match(r'^(v|vel|velocity)\d*$', label.lower())), None)


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
  one orbit of a run: the rows from one orbit boundary to the next (where engine/run.py's OrbitCounter
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

  def __init__(self, bodies, spins=None):
    self.bodies = bodies   #(mass kg, x m, y m, black)
    self.spins = list(spins or []) + [0.0]*(len(bodies) - len(spins or []))   #a/M of each body
    self.flowCalc = None
    self.flowLines = None  #worked out when first drawn
    if bodies and flow is not None:
      made = [flow.Body(mass, x, y, black, spin) for (mass, x, y, black), spin in zip(bodies, self.spins)]
      if len(made) == 1 and made[0].black and self.spins[0]:
        self.flowCalc = flow.KerrFlowCalculator(made)   #a rotating hole: its river (no swirl; r from the flat distance)
      else:
        self.flowCalc = flow.Calculator(made)
      self.flowCalc.warn = lambda message: None   #g=0 on a grid point just means no arrow
    self.name = self.describe(bodies, self.spins)

  def horizon(self, i):
    """
    body i's horizon, as a distance in the plot's flat coordinates (m): the Schwarzschild radius 2GM/c^2, or for a
    rotating hole the outer horizon r+ = M + sqrt(M^2 - a^2), at flat distance sqrt(r+^2 + a^2)
    """
    mass, spin = self.bodies[i][0], self.spins[i]
    M = G*mass/C**2
    a = spin*M
    rPlus = M + math.sqrt(max(M*M - a*a, 0.0))
    return math.sqrt(rPlus*rPlus + a*a)

  @staticmethod
  def key(bodies, spins=()):
    spins = list(spins) + [0.0]*(len(bodies) - len(spins))
    return tuple((float('%.6g' % m), float('%.6g' % x), float('%.6g' % y), black, float('%.6g' % s))
                 for (m, x, y, black), s in zip(bodies, spins))

  @staticmethod
  def describe(bodies, spins=()):
    """e.g. '4e6 MS black at origin', or '2 bodies: 1 MS white at (-0.5, 0) AU, 1 MS black at (0.5, 0) AU'"""
    if not bodies:
      return 'No bodies'
    ms = MS
    parts = []
    spins = list(spins) + [0.0]*(len(bodies) - len(spins))
    for (mass, x, y, black), spin in zip(bodies, spins):
      where = 'origin' if x == 0 and y == 0 else '(%s, %s) AU' % (formatShort(float('%.4g' % (x / AU))), formatShort(float('%.4g' % (y / AU))))
      parts.append('%s MS %s%s at %s' % (formatShort(float('%.4g' % (mass / ms))), 'black' if black else 'white',
                                        ', spin %g' % spin if spin else '', where))
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
