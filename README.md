# Spatial Flow Model

Gravity as a flow of space, as a view of general relativity: a simulation that moves particles and light through
flowing space (for one body the "river model", GR in Gullstrand–Painlevé coordinates), with studies that find what the
flow has to be like to stay GR for several bodies, tested against exact GR, post-Newtonian GR and measurement.

**Website, with live viewers of the results: https://tomcrompton-oss.github.io/spatial-flow-model/**

- `engine/` — the physics: the flow of space round bodies (one hole, a spinning hole, two or more bodies with the
  eikonal flow), gravitational waves, and the steps that move particles and light through it
- `studies/` — runnable experiments, each writing a run folder under `logs/`
- `tests/` — regression checks (`./run_regression.sh`, about 20 s)
- `viewer/` — the desktop viewer (tkinter): `python3 viewer/csv_viewer.py logs/<study>/<run>/<view>.full.json`
- `web/` — the browser viewer: static HTML and JavaScript
- `docs/` — the website's pages, the file formats both viewers follow, and the published runs

Python 3.9 or later with numpy (`requirements.txt`; sympy for two studies); tkinter for the desktop viewer.

```bash
python3 studies/grav_wave.py
./run_regression.sh
```
