# Spatial Flow Model

Gravity as a flow of space: a view of general relativity in which space flows, clocks tick by their speed through it,
and particles and light move through it. For one body this is the "river model" picture – the Schwarzschild solution
in Gullstrand–Painlevé coordinates – and the simulation moves particles and light through it. For several bodies the
studies here find what the flow has to be like to stay GR: one flow, clocks that keep its time, and space stretched
across it.

<iframe src="viewer/index.html?run=../runs/gravWave/gravWave.full.json" width="100%" height="560" loading="lazy" title="Rings of free particles in a gravitational wave"></iframe>

*Rings of free particles in a gravitational wave passing through the screen: plus, cross and circular polarization.
Press Play; choose "All environments" under Background to see every ring's flow.*
[Open full screen](viewer/index.html?run=../runs/gravWave/gravWave.full.json){ target=_blank }

## What is here

| Part | Page | What it covers |
| --- | --- | --- |
| | [Preface](preface.md) | |
| Part 1 – The Flow of Space | [1.1 Hypothesis](part1/hypothesis.md) | space flows into a body at the escape velocity, and gravitational time dilation is the special relativistic dilation of swimming against it: GR in Gullstrand–Painlevé coordinates |
| | [1.2 Mechanics of spatial flow](part1/mechanics.md) | v = u + w, the step-by-step procedure, Newton's apple, and light crossing regions of moving space |
| | [1.3 The four tests](part1/tests.md) | redshift, light bending, Mercury's precession and the Shapiro delay, against general relativity |
| | [1.4 Conclusion](part1/conclusion.md) | for one body spatial flow is general relativity; the mechanics as the simulation has them |
| Part 2 – More than one body | [Part 2 in brief](part2.md) | the result in a page: what the flow needs for several bodies, and the flow that is GR |
| | [Two bodies](two-bodies/index.md) | ways to build two bodies' flow, each tested in the simulation against GR and measurement: those that don't give GR, and the one that does |
| | [Gravitational waves](waves.md) | a wave as a flow of space that changes with time: exact through the plane, approximate across it |
| | [Many bodies](many-bodies.md) | how bodies' flows combine, clocks, moving bodies, beyond Newton, and carrying the flow: why a flow through flat space can't be GR for several bodies |
| | [Lapse and curved space](lapse-curved-space.md) | clocks, curved space and one potential: the flow that is GR for the Sun, the Earth, the Moon, light and a binary, and where its pieces come from in Einstein's equations |
| | [Scorecard](scorecard.md) | every construction scored against GR's tests and the picture's premises |
| Simulations | [Viewers](viewers.md) | the desktop viewer and the browser viewer that runs these pages |
| | [Results](results.md) | the published study results, to open in the viewer or download |
| | [File formats](formats.md) | what a study writes and a viewer reads |
| | [References](references.md) | the papers, books and methods the model and its checks rest on |

## The code

The project is Python with numpy (sympy for two studies): `engine/` holds the physics, `studies/` the runnable experiments, `tests/` the
regression checks, `viewer/` the desktop viewer (tkinter) and `web/` the browser viewer. Everything a viewer draws
comes from files the studies write, so the physics lives in one place.

```bash
python3 studies/grav_wave.py
python3 viewer/csv_viewer.py logs/gravWave/<run>/gravWave.full.json
./run_regression.sh
```
