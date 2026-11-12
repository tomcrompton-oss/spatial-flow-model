# Run file formats

What a study writes and a viewer reads. Both viewers follow this: the desktop viewer (`viewer/`) and the
browser viewer (`web/`). The physics lives only in `engine/`; a viewer draws what these files hold. Change a format
here first, and bump its `version` when a reader would misread the old one.

A run is a folder, usually `logs/<study>/<study>_<YYYY-MM-DD_HH-MM-SS>/`, holding:

| File | What it is |
| --- | --- |
| `<name>.csv` | one result: the rows of one or more paths |
| `<name>.log` | the same result's log: its bodies, flow and notes (same base name as the csv) |
| `<view>.full.json` | names a preferences file and a config file, to open the run as the study set it up |
| `<view>.prefs.json` | how a viewer looks |
| `<view>.config.json` | which csvs to open, and how to draw each |
| `background_<name>.csv` | frames of a flow that changes with time, named in a log |

All quantities are SI: metres, seconds, kilograms, m/s.

## Result csv

- Comma-separated, one header row, then one row per sample. Blank lines and lines starting `#` are skipped.
- A row whose cells are all empty ends a path: the next row starts a new one in the same file (a ring of
  particles is one csv, a path per particle).
- Columns, all optional apart from a position pair:

| Column | Meaning |
| --- | --- |
| `t` | global (coordinate) time, s; replay and time markers use it |
| `pt` or `proper_t` | proper time, s |
| `pos_x`, `pos_y` | position, m |
| `v_x`, `v_y` | velocity through the background, m/s |
| `w_x`, `w_y` | velocity relative to space, m/s |
| `u_x`, `u_y` | the flow of space at the particle, m/s |

- Pairs are found by name: a column with `x` as its own token (`pos_x`, `x`, `earth.x`) or ending `X` (`posX`)
  pairs with the same name with `y`. The pair's label is the name without the `x` (`pos_x` -> `pos`); styles in a
  config are keyed by it.

## Log

Plain text, one statement per line. A viewer reads these lines; it ignores the rest.

| Line | Meaning |
| --- | --- |
| `bodies: N` | how many bodies follow |
| `body i: mass M kg (... MS)  x X m  y Y m  black` | a body: `black` (space flows in) or `white` (out), then optionally `  spin S` (a/M) |
| `flow direction: <words>` | the flow's direction; starting `down zero-energy paths` it is the eikonal flow, and `exact two-body solution` in it means the exact version |
| `gravitational wave: <words>` | a wave's flow is added (engine/waves.py) |
| `background frames: <file>` | the run's flow changes with time; its frames are in `<file>`, next to the log |

## Background frames csv

Written by `engine/background_frames.writeFrames`. Header `t,x,y,u_x,u_y,a_x,a_y`, then one row per grid point per
frame: frames in time order, and within a frame `y` then `x` ascending. `u` is the flow of space and `a` its
acceleration, du/dt + (u . grad) u. The grid is regular and the same in every frame. Between frames, interpolate in
time; within one, bilinearly; outside the grid there is no value. Draw a whole run to one scale (the 90th percentile
of |u|, or of |a|, over every frame, leaving out zeros), so arrows grow and shrink with the flow.

## full.json

```json
{"kind": "full", "version": 1, "preferences": "<view>.prefs.json", "config": "<view>.config.json"}
```

File names are relative to the full.json.

## config.json

```json
{"kind": "config", "version": 1,
 "results": [{"path": "/abs/path/a.csv", "relative": "a.csv", "visible": true,
              "selection": [["pos_x", "pos_y"]], "group": null,
              "styles": {"pos": ["#2a78d6", "solid", "#2a78d6"]},
              "straight": false, "ends": false, "periapsis": false, "apoapsis": false, "hiddenOrbits": []}],
 "selected": "/abs/path/a.csv", "background": null, "timeInterval": ""}
```

- `relative` is tried first, against the config's folder, then `path`.
- `selection`: the column pairs drawn, x then y. `styles`: pair label -> `[colour, line style, second colour]`,
  line style `solid`, `dashed` or `dotted`.
- `background`: the environment the backgrounds are drawn for, by name; `"All environments"` for all; `null` for
  the selected result's.
- A viewer may ignore keys it does not support.

## prefs.json

```json
{"kind": "preferences", "version": 1, "preferences": {"mode": "xy", "equalAspect": true, "showFlow": true}}
```

Keys a viewer does not know are ignored; missing keys keep the viewer's default. Those in use: `mode` (`xy` or
`time`), `unit`, `equalAspect`, `showGrid`, `showMarkers`, `showTimeMarks`, `showBodies`, `showFlow`,
`showGravity`, `showContours`, `showFlowLines`, `showSchwarzschild`, `showPathLegend`, `showFieldKey`,
`replaySpeed`.

## Environments

Results share an environment when they have the same bodies, flow direction and frames file. A viewer draws
backgrounds (bodies, horizons, arrows) for one environment or for all of them.
