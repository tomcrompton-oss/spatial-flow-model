# Spatial Flow Model

Gravity as a flow of space: a simulation that moves particles and light through flat space that is itself flowing,
the "river model" picture of general relativity, and the studies that test it against GR and Newtonian gravity.

<iframe src="viewer/index.html?run=../runs/gravWave/gravWave.full.json" width="100%" height="560" loading="lazy" title="Rings of free particles in a gravitational wave"></iframe>

*Rings of free particles in a gravitational wave passing through the screen: plus, cross and circular polarization.
Press Play; choose "All environments" under Background to see every ring's flow.*
[Open full screen](viewer/index.html?run=../runs/gravWave/gravWave.full.json){ target=_blank }

## What is here

| Part | Page | What it covers |
| --- | --- | --- |
| | [Preface](preface.md) | |
| Part 1 – The Flow of Space | [1.1 Hypothesis](part1/hypothesis.md) | space flows into a body at the escape velocity, and gravitational time dilation is the special relativistic dilation of swimming against it |
| | [1.2 Mechanics of spatial flow](part1/mechanics.md) | v = u + w, the step-by-step procedure, Newton's apple, and light crossing regions of moving space |
| | [1.3 The four tests](part1/tests.md) | redshift, light bending, Mercury's precession and the Shapiro delay, against general relativity |
| | [1.4 Conclusion](part1/conclusion.md) | for one body spatial flow is general relativity in Gullstrand–Painlevé coordinates; the model as it is now |
| Part 2 – Placeholder | [Two bodies](two-bodies.md) | why the flow round two holes needs care, the eikonal flow with no curl, its seam, and an exact solution |
| | [Gravitational waves](waves.md) | a wave as a flow of space that changes with time: exact through the plane, approximate across it |
| Simulations | [Viewers](viewers.md) | the desktop viewer and the browser viewer that runs these pages |
| | [Results](results.md) | the published study results, to open in the viewer or download |
| | [File formats](formats.md) | what a study writes and a viewer reads |
| | [References](references.md) | the papers, books and methods the model and its checks rest on |

## The code

The project is Python with numpy only: `engine/` holds the physics, `studies/` the runnable experiments, `tests/` the
regression checks, `viewer/` the desktop viewer (tkinter) and `web/` the browser viewer. Everything a viewer draws
comes from files the studies write, so the physics lives in one place.

```bash
python3 studies/grav_wave.py
python3 viewer/csv_viewer.py logs/gravWave/<run>/gravWave.full.json
./run_regression.sh
```
