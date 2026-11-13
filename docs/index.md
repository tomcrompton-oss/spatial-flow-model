# Spatial Flow Model

Gravity as a flow of space: a simulation that moves particles and light through flat space that is itself flowing,
the "river model" picture of general relativity, and the studies that test it against GR and Newtonian gravity.

<iframe src="viewer/index.html?run=../runs/gravWave/gravWave.full.json" width="100%" height="560" loading="lazy" title="Rings of free particles in a gravitational wave"></iframe>

*Rings of free particles in a gravitational wave passing through the screen: plus, cross and circular polarization.
Press Play; choose "All environments" under Background to see every ring's flow.*
[Open full screen](viewer/index.html?run=../runs/gravWave/gravWave.full.json){ target=_blank }

## What is here

| Page | What it covers |
| --- | --- |
| [The model](model.md) | space flowing at u, particles moving at v = w + u, and how one hole (still or spinning) matches GR |
| [Two bodies](two-bodies.md) | why the flow round two holes needs care, the eikonal flow with no curl, its seam, and an exact solution |
| [Gravitational waves](waves.md) | a wave as a flow of space that changes with time: exact through the plane, approximate across it |
| [Viewers](viewers.md) | the desktop viewer and the browser viewer that runs these pages |
| [Results](results.md) | the published study results, to open in the viewer or download |
| [File formats](formats.md) | what a study writes and a viewer reads |

## The code

The project is Python with numpy only: `engine/` holds the physics, `studies/` the runnable experiments, `tests/` the
regression checks, `viewer/` the desktop viewer (tkinter) and `web/` the browser viewer. Everything a viewer draws
comes from files the studies write, so the physics lives in one place.

```bash
python3 studies/grav_wave.py
python3 viewer/csv_viewer.py logs/gravWave/<run>/gravWave.full.json
./run_regression.sh
```
