# File Formats

What a study writes and a viewer reads. Both viewers follow this: the desktop viewer (`viewer/`) and the browser
viewer (`web/`). The physics lives only in `engine/`; a viewer draws what these files hold. Change a format here
first, and raise its `version` when a reader would misread the old one.

A run is a folder, usually `logs/<study>/<study>_<YYYY-MM-DD_HH-MM-SS>/`, holding:

| File | What it is |
| --- | --- |
| `<name>.csv` | One result: the rows of one or more paths. |
| `<name>.log` | The same result's log: its bodies, flow and notes (the same base name as the csv). |
| `summary.log` | The study's findings, in words and numbers. Read by people, not by the viewers. |
| `<view>.full.json` | Names a preferences file and a config file, to open the run as the study set it up. |
| `<view>.prefs.json` | How a viewer looks. |
| `<view>.config.json` | Which csvs to open, and how to draw each. |
| `<name>.backgrounds.json` | What is drawn behind the results, named in their logs. |
| `background_<name>.csv` | Older runs: frames of the flow on a grid, named in a log. |

All quantities are SI: metres, seconds, kilograms, m/s.

## Result csv

- Comma-separated, one header row, then one row per sample. Blank lines and lines starting `#` are skipped.
- A row whose cells are all empty ends a path. The next row starts a new one in the same file, so a ring of
  particles is one csv, a path per particle.
- Columns, all optional apart from a position pair:

| Column | Meaning |
| --- | --- |
| `t` | Coordinate time, s. Replay and time markers use it. |
| `pt` or `proper_t` | Proper time, s. |
| `d` | Distance travelled, m. |
| `pos_x`, `pos_y` | Position, m. |
| `v_x`, `v_y` | Velocity through the coordinates, m/s. |
| `w_x`, `w_y` | Velocity relative to space, m/s. |
| `u_x`, `u_y` | The flow of space at the particle, m/s. |
| `E` | Energy per unit mass, less the rest energy, J/kg, in the calculator's own form (the flow model's $\gamma(c^2 + \mathbf u\cdot\mathbf w) - c^2$). Only when the bodies are at rest. |
| `L` | Angular momentum per unit mass about the body, m²/s ($\gamma\,\mathbf x\times\mathbf w$). With one body at rest. |
| `J` | The Jacobi constant $E - \Omega L$, J/kg. For two bodies turning together (`combine='turning'`). |
| `b` | For light, its impact parameter $cL/(E + c^2)$, m. With one body at rest. |

`E`, `L`, `J` and `b` are the quantities the bodies' symmetries keep (`Calculator.conserved`). They are empty when the
run doesn't keep that one, so a run's drift can be plotted against `t`.

Pairs are found by name: a column with `x` as its own token (`pos_x`, `x`, `earth.x`) or ending `X` (`posX`) pairs
with the same name with `y`. The pair's label is the name without the `x` (`pos_x` → `pos`); styles in a config are
keyed by it. A study can also write other columns against time (a clock's rate, a range), plotted with `mode` set to
`time`.

## Log

Plain text, one statement per line. A viewer reads these lines and ignores the rest.

| Line | Meaning |
| --- | --- |
| `bodies: N` | How many bodies follow. |
| `body i: mass M kg (... MS)  x X m  y Y m  black` | A body: `black` (space flows in) or `white` (out), then optionally `  spin S` ($a/M$). |
| `flow direction: <words>` | The flow's direction. Starting `down zero-energy paths`, it is the potential flow; `exact two-body solution` in it means the exact version. |
| `gravitational wave: <words>` | A wave's flow is added (`engine/waves.py`). |
| `backgrounds: <file>` | The run's backgrounds file, next to the log. |
| `background frames: <file>` | Older runs: the flow changes with time, and its frames are in `<file>`, next to the log. |
| `  E: start ...  end ...  change ...  largest ...` | Under `conserved quantities`, at the end of a run: each conserved quantity's start and end values, its change, and its largest change either way, each also as a fraction of its start. |

## Backgrounds file

Written by `engine/backgrounds.py`: one file a run, tens or hundreds of kilobytes, that covers the screen at any zoom.
It holds one or more backgrounds, each listed in the browser viewer's Background menu with its description.

```json
{"kind": "backgrounds", "version": 1,
 "shared": [layer, ...],
 "backgrounds": [{"name": "...", "description": "...",
                  "reference": {"u": ..., "a": ..., "s": ..., "t": ...},
                  "layers": [layer, {"shared": k}, ...]}]}
```

A layer used by several backgrounds is kept once in `shared` and named by its index. Each background's `reference`
scales are a fallback: the viewer scales arrows and colour maps from what is on screen.

### Layers

| Type | Holds |
| --- | --- |
| `field` | Values on a grid at a run of times: the flow and its acceleration (`components` `u_x`, `u_y`, `a_x`, `a_y`), a colour map (`s`), or twist arcs (`t`, a rate of turning, rad/s, positive anticlockwise). |
| `lines` | Lines at each time, such as a seam: `"lines": [[[x, y, x, y, ...], ...] per time]`. |
| `linear` | A flow straight in space about a centre, $\mathbf u = M(t)(\mathbf x - \mathbf c)$, such as a plane wave through the plane: two matrices a time (`u` and `a`, each `[mxx, mxy, myx, myy]`), within `radius`. |

A field's grid is one of:

- `{"kind": "polar", "r0", "r1", "nr", "nt"}`: `nr` rings spaced evenly in $\log r$ from `r0` to `r1`, `nt` angles,
  fine near the centre and coarse far out. The data runs ring by ring outwards, each from angle 0.
- `{"kind": "box", "x0", "x1", "y0", "y1", "nx", "ny"}`: an even grid. The data runs row by row from `y0`, each from
  `x0`.

A field's `data` is base64 of little-endian 16-bit integers, per component, per point, per time. A value $v$, in its
quantity's scale, is stored as $\text{sign}(v)\,(1 + \text{round}(800(\log_{10}|v| + 20)))$: to 0.3%, from $10^{-20}$
to $10^{20}$ of the scale. 0 is 0, and −32768 means no value there (inside a body, say). Between times, interpolate
linearly.

### Frames: patterns that move

A pattern that only moves (turning with two stars, or growing and shrinking with their orbit) is kept once, with a
`frame`:

```json
{"times": [...], "x": [...], "y": [...], "angle": [...], "scale": [...], "u": [...], "a": [...], "s": [...]}
```

At time $t$ the pattern's point $\mathbf p$ is at $(x, y) + \text{scale}\cdot R(\text{angle})\,\mathbf p$. Its vectors
are turned by the angle and multiplied by their own quantity's scale. Values between `times` are linear. A field with
no frame is in metres, where it is.

## Background frames csv (older runs)

Written by `engine/background_frames.writeFrames`. Header `t,x,y,u_x,u_y,a_x,a_y`, then one row per grid point per
frame: frames in time order, and within a frame `y` then `x` ascending. `u` is the flow of space and `a` its
acceleration, $\partial\mathbf u/\partial t + (\mathbf u\cdot\nabla)\mathbf u$. The grid is regular and the same in
every frame. Between frames, interpolate in time; within one, bilinearly; outside the grid there is no value.

A steady flow is one frame at `t = 0`. The desktop viewer ignores a steady frame when the log lists bodies, and works
the flow out exactly instead. Each study moves to a backgrounds file when it is next changed or rerun, and
`publish_run.py` leaves these frames out of a run that has one.

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

- `relative` is tried first, against the config's folder, then `path`. In a published run, `publish_run.py` leaves the
  absolute paths out: no `path`, and `selected` is `null`.
- `selection`: the column pairs drawn, x then y. `styles`: pair label → `[colour, line style, second colour]`, line
  style `solid`, `dashed` or `dotted`.
- `background`: the environment the older backgrounds are drawn for, by name; `"All environments"` for all; `null`
  for the selected result's.
- A viewer may ignore keys it does not support.

## prefs.json

```json
{"kind": "preferences", "version": 1, "preferences": {"mode": "xy", "equalAspect": true, "showFlow": true}}
```

Keys a viewer does not know are ignored; missing keys keep the viewer's default.

| Key | Sets |
| --- | --- |
| `mode` | `xy`, or `time` (columns against time). |
| `unit` | The distance unit, by the desktop viewer's list: 0 raw values, 1 metres, 2 kilometres, 3 astronomical units, 4 light-seconds (the browser viewer shows raw values as metres). |
| `equalAspect`, `showGrid` | Equal scales on both axes; a grid. |
| `showFlow`, `showGravity` | The background's $\mathbf u$ and $\mathbf g$ arrows. |
| `showScalar`, `showTwist`, `showSeam` | The background's colour map, twist arcs and lines. |
| `showBodies`, `showSchwarzschild`, `showSpin` | Bodies, horizons, and spinning bodies turning. |
| `showPathLegend`, `showFieldKey` | The paths' legend; the background's key. |
| `graduateOrbits` | Each earlier orbit drawn fainter than the current one. |
| `replaySpeed`, `replayLoop` | The replay's speed (`"0.1"` to `"10"`) and whether it loops. |
| `showMarkers`, `showTimeMarks`, `showContours`, `showFlowLines` | The desktop viewer's markers, time marks, lines of equal $|u|$ and flow lines. |

## Environments

Results share an environment when they have the same bodies, flow direction and background file. A viewer draws
backgrounds (bodies, horizons, arrows) for one environment or for all of them.
