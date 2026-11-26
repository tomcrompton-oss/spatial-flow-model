# Appendix A – Simulations

Every number on these pages comes from a simulation: light, clocks and test particles moved through a model's
flowing space, and compared with general relativity or with a measurement. This appendix describes how the
simulations work, for anyone who wants to run them, check them, or add to them.

- This page: how a simulation runs, what it writes, and how the results are viewed.
- [The Simulator](simulator.md): how the code is built, its core classes and the step that moves a particle.
- [Models](models.md): each model in the documentation, and the Python that runs it.
- [Viewers](viewers.md): the desktop and browser viewers, and the player embedded in the pages.
- [Results](results.md): every published run, with its page and study.
- [File Formats](formats.md): what a study writes and a viewer reads.

The code is in the [repository](https://github.com/tomcrompton-oss/spatial-flow-model). It needs Python 3.9 or later
and numpy; the desktop viewer also needs tkinter.

## How a simulation runs

![A flow chart. A study (studies/*.py) sets up the bodies, starts and models, and makes a calculator (engine/), which gives the flow or a spacetime and its step. The run loop steps until an end condition and writes a log folder (logs/<study>/<run>/, with .log, .csv, summary.log and .backgrounds.json files), and viewer files (.full.json, .prefs.json, .config.json). The desktop viewer reads any run in logs/. publish_run.py copies a run to docs/runs, where the browser viewer reads it, and a page embeds it as a player](images/pipeline.svg)

The code is in three parts, kept apart on purpose:

| Folder | What it holds |
| --- | --- |
| `engine/` | The physics, and only the physics: bodies, the flow of space, spacetimes, and the steps that move particles and light. |
| `studies/` | Experiments. Each sets up bodies and starting points, runs one or more models, compares them with general relativity, and writes a run folder. |
| `viewer/`, `web/` | The two viewers. They draw what a run wrote, and work nothing out beyond drawing it. |

A study is a Python script, run from the project folder:

```bash
python3 studies/four_tests.py
```

Most take options on the command line. Each study's opening notes (its docstring) say what it tests, how, and how to
run it, for example `python3 studies/lapse_moon.py 90 differenced`. Studies with many independent runs share them out
over eight processes, and the long ones write a `progress.log` as they go, with the time left.

A run has four parts:

1. **Bodies.** Each has a mass and a place. A body can be black (space flows in) or white (out), spin, move in a
   straight line, or go round the origin on a circle.
2. **A calculator.** It gives the flow of space at any place and time, and moves a particle through it. A flow
   calculator (for the flow model) or a spacetime (for curved space and for general relativity's metric) both work
   this way: see [The Simulator](simulator.md).
3. **A particle, or light.** It starts at a place, with a velocity through the coordinates, through space, or moving
   with the space.
4. **Steps.** The calculator moves the particle one step at a time, fixed or adaptive (each step a fraction of the
   distance to the nearest body), until an end condition: a time, a proper time, a distance from a body, or a number
   of orbits.

Most studies then compare: the same start in the model and in general relativity, exact (one body) or to the first
order beyond Newton (several).

## What a run writes

A run's files go in `logs/<study>/<study>_<date>_<time>/`, a new folder each time, so earlier runs are kept.

| File | What it is |
| --- | --- |
| `<name>.csv` | One result: the rows of one or more paths, one row per sample. |
| `<name>.log` | The same result's log: its bodies, calculator, flow, and notes, plus the conserved quantities' drift. |
| `summary.log` | The study's findings, the numbers the pages quote. |
| `<view>.full.json` | Opens the run in a viewer as the study set it up. Names a `.prefs.json` and a `.config.json`. |
| `<name>.backgrounds.json` | What a viewer draws behind the paths: the flow's arrows, its acceleration, a seam, a colour map. |

The numbers on the pages come from the `summary.log`s. Each page's footnote names the studies behind it.

Checks of the code itself, rather than of a model, go in `logs/modelChecks/`. The regression tests (`tests/`,
`./run_regression.sh`, about 20 seconds) check the engine against exact results and earlier runs.

## Backgrounds

A run's paths are drawn over a background: what the space is doing. Backgrounds are written by `engine/backgrounds.py`
into one small file per run, `<name>.backgrounds.json`. Each result's log names it with a `backgrounds:` line.

A file can hold several backgrounds. The browser viewer lists them in its Background menu, each with a written
description. A background is built from layers:

- **field**: the flow $\mathbf u$ and its acceleration $\mathbf g$ (drawn as arrows), sampled on a grid that is fine
  near the bodies and coarse far out;
- **scalar**: a colour map, such as a wave's strain;
- **twist**: arcs showing how fast space turns, round a spinning hole;
- **lines**: a seam between bodies' regions of the flow;
- **linear**: a flow that is straight in space, such as a plane wave through the plane.

Backgrounds are pictures, not results: values are kept to 0.3%. A pattern that only moves (turning with two stars, or
shrinking with their orbit) is kept once, with the motion as a few numbers a frame. So a file is tens or hundreds of
kilobytes, and covers the screen at any zoom.

Older runs wrote their flow as frames on a fixed grid (`background_<name>.csv`, from `engine/background_frames.py`).
The desktop viewer still reads those. Each study moves to backgrounds files when it is next changed or rerun.

## The viewers

There are two viewers, and both read the same files. The **desktop viewer** (`viewer/`, tkinter) opens any run in
`logs/`, works backgrounds out live from the bodies, and runs single simulations from its Sim tab:

```bash
python3 viewer/csv_viewer.py logs/<study>/<run>/<view>.full.json
```

The **browser viewer** (`web/`) is the one embedded in these pages: static HTML and JavaScript, with no server. It
shows a run's paths, replays them, and draws its backgrounds file. With `?player` it is the cut-down player the pages
embed. See [Viewers](viewers.md).

## Publishing a run

A page shows a run once it is copied into the website, without the absolute paths in its viewer config:

```bash
python3 scripts/publish_run.py logs/<study>/<run> [name]
```

The run goes to `docs/runs/<name>/`, and a page embeds it as a player. [Results](results.md) lists every published
run, and [File Formats](formats.md) describes each file.
