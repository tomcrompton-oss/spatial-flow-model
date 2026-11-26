# Viewers

There are two viewers. Both read the files a study writes ([File Formats](formats.md)), and neither does any physics
beyond drawing what those files hold. The one formula either uses is a horizon's radius, $2GM/c^2$.

| | Desktop viewer | Browser viewer |
| --- | --- | --- |
| Code | `viewer/` (Python, tkinter) | `web/` (static HTML and JavaScript) |
| Opens | any run in `logs/` | a run published to the website, or a folder from your own computer |
| Backgrounds | worked out live from the bodies | read from the run's backgrounds file |
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

### What it shows

- **Paths**, in the run's own colours and line styles, with a legend. Each result can be shown or hidden.
- **Bodies and horizons**, and spinning bodies turning the way they spin (not at their real speed).
- **Backgrounds** from the run's backgrounds file. The Background menu lists them; picking one draws its layers and
  shows its written description. A background can have:
    - $\mathbf u$ arrows, the flow of space;
    - $\mathbf g$ arrows, the acceleration of space;
    - a colour map of a field, such as a wave's strain;
    - twist arcs, how fast space turns things round a spinning hole;
    - lines, such as the seam where the bodies' regions of flow meet.
- **A background key** for the arrows' and colours' scale. Arrows are scaled from what is on screen.
- **Units**: metres, kilometres, astronomical units or light-seconds, with equal aspect and a grid if wanted.
- **Orbits**: the current orbit in full colour, each earlier one fainter.

Drag to pan, scroll to zoom at the pointer, and double-click to fit.

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

A run's `.prefs.json` sets how the player starts: which backgrounds are drawn, whether the legend shows, and so on.

## Backgrounds that change with time

A background can change through a run. A wave's arrows shrink, reverse and grow as it passes; two stars' flow turns
with them. A backgrounds file holds a field sampled at a run of times, or a pattern that only moves, kept once with
its motion as a few numbers a frame. The viewer draws it as it is at the replay time, interpolating between samples.

Older runs wrote their changing flow as frames on a fixed grid (`background_<name>.csv`). The desktop viewer still
draws those, and works a steady flow out exactly from the bodies instead.
