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
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/, studies/ and viewer/

from viewer.common import *   #so `import csv_viewer` still gives Dataset, studyName, flow, simrun ...
from viewer.app import Viewer


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
