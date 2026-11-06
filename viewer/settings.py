"""the viewer's settings: colours, sizes, units, folders, and the engine and studies modules it uses"""
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
STEP_MODES = ['Fixed dt', 'Adaptive']   #the Sim tab's step choice
NO_END = '(nothing else)'   #the Sim tab's second end condition, left out
END_KINDS = [('time', 'Elapsed time'), ('properTime', 'Proper time'), ('min', 'Min distance to a body'), ('max', 'Max distance from every body'),
             ('orbits', 'Number of orbits')]
DIST_UNITS = [('m', 1.0), ('km', 1e3), ('AU', AU), ('RSUN', RSUN)]
VEL_UNITS = [('m/s', 1.0), ('km/s', 1e3), ('c', C)]


# ---------------------------------------------------------------- data
