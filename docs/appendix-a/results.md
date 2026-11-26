# Results

The runs published with the site. Each opens full screen in the browser viewer. The files are plain csv, logs and
json ([File Formats](formats.md)), and can be downloaded from the
[repository](https://github.com/tomcrompton-oss/spatial-flow-model/tree/main/docs/runs).

## Runs in the pages

### Part 1: one body

| Run | Page | Study | Open |
| --- | --- | --- | --- |
| Newton's apple | [Newtonian Gravity](../part1/mechanics/newtonian.md) | `newtonian_flow.py` | [viewer](../../viewer/index.html?run=../runs/newtonianFlow/newtonian_apple.full.json){ target=_blank } |
| An orbit of the Earth | [Newtonian Gravity](../part1/mechanics/newtonian.md) | `newtonian_flow.py` | [viewer](../../viewer/index.html?run=../runs/newtonianFlow/newtonian_orbit.full.json){ target=_blank } |
| Light crossing regions of moving space | [Special Relativity](../part1/mechanics/special-relativistic.md) | `special_flow.py` | [viewer](../../viewer/index.html?run=../runs/specialFlow/special_regions.full.json){ target=_blank } |
| Light pulses climbing from a neutron star | [Redshift](../part1/tests/redshift.md) | `redshift_pulses.py` | [viewer](../../viewer/index.html?run=../runs/redshift/redshift_star.full.json){ target=_blank } |
| Mercury's perihelion over a century | [Precession](../part1/tests/precession.md) | `four_tests.py` | [viewer](../../viewer/index.html?run=../runs/mercuryCentury/mercuryCentury.full.json){ target=_blank } |
| A precessing orbit | [Precession](../part1/tests/precession.md) | `four_tests.py` | [viewer](../../viewer/index.html?run=../runs/strongOrbit/orbit.full.json){ target=_blank } |
| Falling into a black hole | [Black Holes](../part1/black-holes.md) | `black_holes.py` | [viewer](../../viewer/index.html?run=../runs/blackHoles/blackHoles_fall.full.json){ target=_blank } |
| Flashes of light falling into a black hole | [Black Holes](../part1/black-holes.md) | `black_holes.py` | [viewer](../../viewer/index.html?run=../runs/blackHoles/blackHoles_flashes.full.json){ target=_blank } |
| A probe close to a black hole and back | [Black Holes](../part1/black-holes.md) | `black_holes.py` | [viewer](../../viewer/index.html?run=../runs/blackHoles/blackHoles_probe.full.json){ target=_blank } |
| Falling into a white hole | [White Holes](../part1/white-holes.md) | `white_holes.py` | [viewer](../../viewer/index.html?run=../runs/whiteHoles/whiteHoles_fall.full.json){ target=_blank } |
| Flashes of light near a white hole | [White Holes](../part1/white-holes.md) | `white_holes.py` | [viewer](../../viewer/index.html?run=../runs/whiteHoles/whiteHoles_flashes.full.json){ target=_blank } |
| Light passing a spinning black hole | [Rotating Black Holes](../part1/rotating-black-holes.md) | `kerr_paths.py` | [viewer](../../viewer/index.html?run=../runs/kerrPaths/kerrPaths_light.full.json){ target=_blank } |
| Orbits round a spinning black hole | [Rotating Black Holes](../part1/rotating-black-holes.md) | `kerr_paths.py` | [viewer](../../viewer/index.html?run=../runs/kerrPaths/kerrPaths_orbits.full.json){ target=_blank } |

### Part 2: bodies at rest

| Run | Page | Study | Open |
| --- | --- | --- | --- |
| Falling into a hollow sphere, carried with the space | [The Hollow Sphere](../part2/hollow-sphere.md) | `hollow_sphere.py` | [viewer](../../viewer/index.html?run=../runs/hollowSphere/hollowSphere_smooth.full.json){ target=_blank } |
| Falling through a hollow sphere, changing reference frame | [The Hollow Sphere](../part2/hollow-sphere.md) | `hollow_sphere.py` | [viewer](../../viewer/index.html?run=../runs/hollowSphere/hollowSphere_boundary.full.json){ target=_blank } |
| Orbits round two holes in the potential flow | [Potential Flow](../part2/potential-flow.md) | `two_body_tests.py` | [viewer](../../viewer/index.html?run=../runs/twoBodyTests/twoBodyTests_bothHoles.full.json){ target=_blank } |
| Clocks on the Earth and in GPS orbit | [Potential Flow](../part2/potential-flow.md) | `multi_body_clocks.py` | [viewer](../../viewer/index.html?run=../runs/multiBodyClocks/multiBody_clocks.full.json){ target=_blank } |
| The extra lunar range by the Moon's angle from the Sun | [Curved Space](../part2/curved-space.md) | `multi_body_pn.py` | [viewer](../../viewer/index.html?run=../runs/multiBodyPN/multiBody_lunar.full.json){ target=_blank } |
| Lunar range: flat space, curved space and general relativity | [Curved Space](../part2/curved-space.md) | `lapse_two_bodies.py` | [viewer](../../viewer/index.html?run=../runs/lapseTwoBodies/lapseTwoBodies_lunar.full.json){ target=_blank } |
| Paths among three bodies in the potential flow | [Multiple Bodies](../part2/multiple-bodies.md) | `three_bodies.py` | [viewer](../../viewer/index.html?run=../runs/threeBodies/threeBodies.full.json){ target=_blank } |

### Part 3: bodies on given paths

| Run | Page | Study | Open |
| --- | --- | --- | --- |
| Balls let go beside the moving Earth | [Carrying the Flow](../part3/carrying-the-flow.md) | `moving_bodies.py` | [viewer](../../viewer/index.html?run=../runs/movingBodies/multiBody_moving.full.json){ target=_blank } |
| The turning flow's paths out of the Sun and the Earth | [Curving the Turning Flow](../part3/curving-the-turning-flow.md) | `turning_eikonal.py` | [viewer](../../viewer/index.html?run=../runs/turningEikonal/turning_paths.full.json){ target=_blank } |
| The Moon in each model against general relativity's | [One Potential](../part3/one-potential.md) | `lapse_moon.py residuals` | [viewer](../../viewer/index.html?run=../runs/lapseMoonResiduals/lapseMoon_residuals.full.json){ target=_blank } |

### Part 4: bodies moved by the flow

| Run | Page | Study | Open |
| --- | --- | --- | --- |
| An equal-mass binary's periastron turning, against general relativity | [Each Body in the Others' Flow](../part4/each-body-in-the-others-flow.md) | `carried_bodies.py plots` | [viewer](../../viewer/index.html?run=../runs/carriedBodies/binary_periastron.full.json){ target=_blank } |
| A binary's centre of mass drifting off | [Each Body in the Others' Flow](../part4/each-body-in-the-others-flow.md) | `carried_bodies.py plots` | [viewer](../../viewer/index.html?run=../runs/carriedBodies/binary_centre.full.json){ target=_blank } |
| How nearly each body's averaged space moves with it, off circles | [Moving With Its Own Space](../part4/moving-with-its-own-space.md) | `eccentric_bodies.py` | [viewer](../../viewer/index.html?run=../runs/eccentricBodies/ownSpace.full.json){ target=_blank } |

### Parts 5 and 6

| Run | Page | Study | Open |
| --- | --- | --- | --- |
| Rings of free particles in a wave through the plane | [Part 5](../part5.md) | `grav_wave.py` | [viewer](../../viewer/index.html?run=../runs/gravWave/gravWave.full.json){ target=_blank } |
| A binary's inspiral and a ring in its waves | [Part 5](../part5.md) | `binary_waves.py` | [viewer](../../viewer/index.html?run=../runs/binaryWaves/binaryWaves.full.json){ target=_blank } |
| A binary's waves travelling outward across its plane | [Part 5](../part5.md) | `binary_outgoing.py` | [viewer](../../viewer/index.html?run=../runs/binaryOutgoing/binaryOutgoing.full.json){ target=_blank } |
| Light peeling off a black hole's horizon | [Part 6](../part6/index.md) | `horizon_peeling.py` | [viewer](../../viewer/index.html?run=../runs/horizonPeeling/horizonPeeling.full.json){ target=_blank } |

## Other published runs

Runs from earlier versions of the write-up, still published but not in the current pages. They were made with
earlier versions of the code, so their numbers may differ from the pages'.

| Run | Study | Open |
| --- | --- | --- |
| A wave sweeping across the plane, with its front | `grav_wave_across.py` | [viewer](../../viewer/index.html?run=../runs/gravWaveAcross/gravWaveAcross.full.json){ target=_blank } |
| Thirty falls towards two holes, under Newton's gravity | `two_body_falls.py` | [viewer](../../viewer/index.html?run=../runs/twoBodyFalls/twoBodyFalls.full.json){ target=_blank } |
| Space moving with a flow along $g$, round two holes, against Newton's fall | `two_body_along_g.py` | [viewer](../../viewer/index.html?run=../runs/twoBodyAlongG/twoBodyAlongG.full.json){ target=_blank } |
| Balls dropped near the Earth, the flows added as vectors and by their squares | `multi_body_rules.py` | [viewer](../../viewer/index.html?run=../runs/multiBodyRules/multiBody_drops.full.json){ target=_blank } |
| Lunar laser ranging with the Moon's own orbit, in an earlier model | `lunar_orbit.py` | [viewer](../../viewer/index.html?run=../runs/lunarOrbit/lunarOrbit.full.json){ target=_blank } |
| Part 1's examples: an apple, an orbit, bending, radar, regions | `part1_examples.py` | [viewer](../../viewer/index.html?run=../runs/part1/part1_orbit.full.json){ target=_blank } |

## Publishing a run

```bash
python3 scripts/publish_run.py logs/<study>/<run> [name]
```

This copies the run to `docs/runs/<name>/` (the name defaults to the study's, such as `gravWave`). It leaves out the
absolute paths in the viewer config, which would show where the project lives on the computer that ran it. If the
run has a backgrounds file, it also leaves out the older background frames its logs name. Then embed the run in a
page (see [Viewers](viewers.md)) and add a row here.
