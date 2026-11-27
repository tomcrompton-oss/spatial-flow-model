# Viewers

There are two viewers. Both read the files a study writes ([File Formats](formats.md)), and neither does any physics
beyond drawing what those files hold. The formulas they use are a few closed forms: a horizon's radius, $2GM/c^2$
(Kerr's $r_+$ for a spinning hole), the escape speed $\sqrt{2GM/r}$ where a run has no flow of its own to draw from,
and a spinning hole's photon orbits and innermost stable orbits.

The browser viewer is the one being developed. It is to come in three forms of the same page: the **player**, which
replays a run as its page set it up; the **viewer**, the player full screen with every display option; and later a
**studio**, which also saves and loads settings and sets up and runs new simulations. The desktop viewer stays for
now for what only it does: working backgrounds out live from the engine, and its Sim tab.

| | Desktop viewer | Browser viewer |
| --- | --- | --- |
| Code | `viewer/` (Python, tkinter) | `web/` (static HTML and JavaScript) |
| Opens | any run in `logs/` | a run published to the website, or folders from your own computer |
| Backgrounds | worked out live from the bodies | read from the run's backgrounds file |
| Saves settings | yes: preferences and configs | no, it reads a run's |
| Runs simulations | yes, from its Sim tab | no |

## Desktop viewer

```bash
python3 viewer/csv_viewer.py logs/<study>/<run>/<view>.full.json
```

With no file it opens the newest csv in `logs/`. Several files open together, one tab each. It reads a csv in most
layouts: it detects the delimiter and header row, and pairs columns by name.

It can:

- plot paths in x and y, or any column against time;
- replay runs;
- split orbits and mark their closest and farthest points;
- draw backgrounds worked out live from the bodies in each result's log: flow and gravity arrows, lines of equal
  $|u|$, flow lines, horizons, photon orbits and the innermost stable orbits, and a rotating hole's ergosphere and
  twist.

Its **Sim tab** sets up and runs a single simulation: bodies, a calculator, a start and an end condition. It runs
`studies/run_study.py` from a json config, in its own process, so the run carries on if the viewer is closed.

The desktop viewer doesn't yet read backgrounds files. It works backgrounds out from the bodies a log lists, or reads
an older run's background frames.

## Browser viewer

The viewer embedded in these pages. It needs no server and nothing to install. The website copies `web/` to `viewer/`
when it is built.

### Opening a run

- `viewer/index.html?run=<path to a .full.json>` opens a run full screen.
- **Open run folder…** chooses a run folder on your own computer, and dropping a folder on the plot does the same.
- To open runs straight from `logs/`, serve the project folder (`python3 -m http.server` from it), then open
  `http://localhost:8000/web/index.html?run=../logs/<study>/<run>/<view>.full.json`.

### The panel

The panel beside the plot has three tabs: **Results** (which results are shown, how each is drawn, and the
markers), **View** (what is plotted, units, axes, zoom and legends) and **Background** (the background and
the flow, bodies and horizons). Drag its edge to make it wider or narrower; a double-click puts it back. Every control
has hover help, and one greyed out says why it isn't available.

The Results tab lists the results as a tree: each environment (the bodies results share), its results, and each
result's orbits, every level folding open and shut, with a box to show or hide all of it. Under the tree, the selected
result has three tabs of its own: **Appearance** (with the markers), **Details** (its summary and log) and
**Choose paths**. The list and the selected result scroll separately, and the line between them can be dragged to
give either more room.

### What it shows

- **Paths**, in the run's own colours and line styles, with a legend. Each result can be shown or hidden, and has
  its own options:
    - each path's **colour**, one of three ways: a **single colour**; a **transition** from a first colour to a last
      through its orbits; or **shade**, the current orbit in full colour and each earlier one fainter. And its
      **line style**;
    - a **tangent**: the straight line along the path at a chosen moment (dragged to, or typed in), where it would go
      with no gravity from then, in its own colour and style;
    - **end arrows**: each velocity-like pair (v, u, a) as an arrow where a path ends;
    - **orbits**: a run that goes round is split into orbits where its log says each ended. Each can be shown or
      hidden, or every Nth shown;
    - **Choose paths**: which column pairs are plotted, any two columns as a pair, and one path per value of a
      column;
    - a **summary** of the run (calculator, step, orbits, distances, speeds) and its **log**.
- **Two views**: x / y, or **distance / time**, each path's distance from the origin against t or pt (as ct, with
  light at 45°, if wanted; distance can run right to left). Either axis can be **logarithmic**.
- **Bodies and horizons**, with a spinning hole's ergosphere and ring singularity, labels with each body's mass and
  spin, and spinning bodies turning the way they spin (not at their real speed).
- **Backgrounds** from the run's backgrounds file. The Background menu lists them; picking one draws its layers and
  shows its written description. A background can have:
    - $\mathbf u$ arrows, the flow of space;
    - $\mathbf g$ arrows, the acceleration of space;
    - a colour map of a field, such as a wave's strain;
    - twist arcs, how fast space turns things round a spinning hole;
    - lines, such as the seam where the bodies' regions of flow meet.
- **Drawn from the flow**: lines of equal $|u|$, and flow lines, the paths of space out of each body. Against time,
  the flow line repeated up the time axis, and **light cones**, light's speed $u \pm c$ outwards and inwards. They
  use the background's $u$, or the bodies' escape speed where a run has none.
- **One hole's circular photon orbits and innermost stable circular orbits**, with the spin and against it.
- **A background key** for the arrows' and colours' scale. Arrows are scaled from what is on screen.
- **Markers**: where each path starts and ends; **time markers**, dots at every interval of t or pt (a round
  interval, or one typed in), labelled where there is room; and each whole orbit's **periapsis** and **apoapsis**,
  on every orbit or every Nth.
- **Legends**: the paths' legend, the background key, the markers' interval and times, and body labels, each of
  which can be turned off.
- **Units**: metres, kilometres, astronomical units or light-seconds, with equal aspect and a grid if wanted.

Drag to pan, scroll to zoom at the pointer, shift-drag to zoom to a box, and double-click to fit; the arrow keys pan
and + and − zoom. **Range…** takes each axis's range typed in, and the status line gives the point under the pointer.
Hovering on a path shows the nearest row's values.

**Add…** adds another run folder's results to those open, to compare them, and **Reload** reads everything again,
keeping each result's settings.

### Replay

A run replays over 20 seconds at ×1, at speeds from ×0.1 to ×10. **Play** runs the shown results together; **play in
turn** runs them one after another, each drawn over the last. The replay can pause, restart, loop, and be dragged to
any moment.

### The player

Adding `&player` to the address gives the cut-down player embedded in the pages: the plot, the replay controls, and a
button to open the run full screen. It stays fitted to the run and doesn't pan or zoom.

```html
<iframe src="../viewer/index.html?player&run=../runs/<name>/<view>.full.json" width="100%" height="520"
        loading="lazy" title="What the run shows"></iframe>
```

A run's `.prefs.json` sets how the player starts: which backgrounds are drawn, whether the legend shows, the view
(x / y or distance / time, log axes), markers, and so on; its config sets each result's options (tangent, end
arrows, apsides, hidden orbits, colours). The player shows only what these ask for: the desktop viewer's markers and
time markers, on there by default, are off here unless a run's preferences turn them on.

## Backgrounds that change with time

A background can change through a run. A wave's arrows shrink, reverse and grow as it passes; two stars' flow turns
with them. A backgrounds file holds a field sampled at a run of times, or a pattern that only moves, kept once with
its motion as a few numbers a frame. The viewer draws it as it is at the replay time, interpolating between samples.

Older runs wrote their changing flow as frames on a fixed grid (`background_<name>.csv`). The desktop viewer still
draws those, and works a steady flow out exactly from the bodies instead.
