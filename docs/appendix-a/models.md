# Models

Each model in the documentation, the Python that runs it, and the parameters it needs. The classes are described on
[The Simulator](simulator.md). Every example assumes these imports, and bodies made as `Body(mass, x, y, ...)`:

```python
from engine.flow import Body, Particle, NewtonianCalculator, SpecialFlowCalculator
from engine.kerr import KerrFlowCalculator
from engine.metric import MetricCalculator, FlowSpacetime, PostNewtonian
from engine.constants import G, MS, ME, AU, C
```

A flow calculator moves particles itself. A spacetime is moved through by `MetricCalculator(spacetime)`.

## Part 1: one body

| Model | Python | Parameters | Used in |
| --- | --- | --- | --- |
| Newton's gravity | `NewtonianCalculator(bodies)` | the bodies | [Newtonian Gravity](../part1/mechanics/newtonian.md), the four tests |
| The flow model: space flowing in at the escape speed | `SpecialFlowCalculator(bodies)` | `order=2`, `step='momentum'` (the defaults) | [the four tests](../part1/tests/index.md), [Black Holes](../part1/black-holes.md), [Part 6](../part6/index.md) |
| A white hole: space flowing out | `SpecialFlowCalculator([Body(M, black=False)])` | `black=False` on the body | [White Holes](../part1/white-holes.md) |
| A rotating black hole: the river model | `KerrFlowCalculator([Body(M, spin=a)])` | `spin`, $a/M$ from −1 to 1 (positive anticlockwise); `twist=1.0` (0 leaves the twist out) | [Rotating Black Holes](../part1/rotating-black-holes.md) |
| General relativity, exact | `engine/exact.py`: `grDeflectionExact`, `grPrecessionExact`, `grRayExact`, `shapiroDelay` | the body and the path | the four tests |

```python
calc = SpecialFlowCalculator([Body(MS)])                    #the Sun at the origin
hole = KerrFlowCalculator([Body(10*MS, spin=0.9)])          #a hole spinning at a = 0.9 M
```

The older steps are kept for comparison: `SpecialFlowCalculator(bodies, order=1)` is the first-order step, and
`order=2, step='velocity'` the second-order velocity step.

## Part 2: bodies at rest

| Model | Python | Parameters | Used in |
| --- | --- | --- | --- |
| Flows added as vectors | `SpecialFlowCalculator(bodies, 2, combine='vectors')` | | [The Two Body Problem](../part2/two-body-problem.md), the scorecard |
| Speed from the potential, along $g$ | `SpecialFlowCalculator(bodies, 2, direction='g')` | | the scorecard |
| The potential flow | `SpecialFlowCalculator(bodies, 2)` | `direction`: `'eikonal-exact'` (the default for two bodies) or `'eikonal'` (tables of paths, the default for more) | [Potential Flow](../part2/potential-flow.md), [Multiple Bodies](../part2/multiple-bodies.md) |
| The hollow sphere's four flows | `ShellFlow(option, smooth)` in `studies/hollow_sphere.py` | `option`: `'A'`–`'D'`, the flow's direction in each half; `smooth=False` for the boundary rule | [The Hollow Sphere](../part2/hollow-sphere.md) |
| The potential flow, space curved | `MetricCalculator(FlowSpacetime(flow, transverse='flow'))` | `transverse`: `'flow'`, stretched across the flow by $u^2/c^2$; `True`, by $2\Phi/c^2$ (the same for the potential flow) | [Curved Space](../part2/curved-space.md) |
| General relativity, first post-Newtonian | `MetricCalculator(PostNewtonian(bodies))` | the bodies (they may move on given paths) | the reference for Parts 2 and 3 |

```python
sun_earth = [Body(MS, -AU, 0.0), Body(ME)]
flow = SpecialFlowCalculator(sun_earth, 2)                       #the potential flow
curved = MetricCalculator(FlowSpacetime(flow, transverse='flow'))  #with space curved across it
gr = MetricCalculator(PostNewtonian(sun_earth))                  #general relativity, to compare
```

The hollow sphere with space curved is `studies/hollow_sphere_curved.py`'s own `Shell(option, curved)`, a
`Spacetime`, run by `MetricCalculator`.

`FlowSpacetime` also takes `share` and `curve`, $\lambda$ and $\kappa$: $\lambda$ of gravity moved into the clocks,
and space curved equally in every direction by $2\kappa\Phi/c^2$. With both at 1 it is general relativity's
post-Newtonian metric. The studies tried these and the pages don't use them.

## Part 3: bodies on given paths

| Model | Python | Parameters | Used in |
| --- | --- | --- | --- |
| The flow's pattern taken along | `SpecialFlowCalculator(bodies, 2, carried=False)` | each moving body's `velocity=(vx, vy)` | [Carrying the Flow](../part3/carrying-the-flow.md) |
| The space carried with the body | `SpecialFlowCalculator(bodies, 2, carried=True)` | as above | [Carrying the Flow](../part3/carrying-the-flow.md) |
| The turning flow | `SpecialFlowCalculator(bodies, 2, combine='turning')` | two bodies, each with `circling=Ω`; `calc.jacobi`, the paths' constant (by default chosen for the lighter body) | [Carrying the Flow](../part3/carrying-the-flow.md), [Curving the Turning Flow](../part3/curving-the-turning-flow.md) |
| The turning flow, space curved | `MetricCalculator(FlowSpacetime(flow, transverse='source'))` | `'source'`: stretched by the flow relative to the body it belongs to | [Curving the Turning Flow](../part3/curving-the-turning-flow.md), [One Potential](../part3/one-potential.md) |
| One potential, space curved | `flow.jacobi = 0.0`, then `MetricCalculator(FlowSpacetime(flow, transverse='constraint'))` | `'constraint'`: space from Einstein's constraint, $(2\Phi\,\delta - \mathbf u\mathbf u)/c^2$ | [One Potential](../part3/one-potential.md): light |
| One potential, with its first post-Newtonian corrections | `MetricCalculator(FreeFallTurning(bodies, lapse=False, chi=1, jacobi=0.0))` from `engine/carried.py` | `lapse=False`: clocks slowed only by their speed through space; `chi=1`: the flow's correction that makes that exact | [One Potential](../part3/one-potential.md): the Moon |

```python
V = 29780.0                                                       #the Earth's orbital speed
moving = SpecialFlowCalculator([Body(ME, velocity=(0.0, V))], 2, carried=True)

W = (G*(MS + ME)/AU**3)**0.5                                      #once a year
mu = ME/(MS + ME)
pair = [Body(MS, -mu*AU, 0.0, circling=W), Body(ME, (1 - mu)*AU, 0.0, circling=W)]
turning = SpecialFlowCalculator(pair, 2, combine='turning')       #the constant chosen for the Earth
one = SpecialFlowCalculator(pair, 2, combine='turning')
one.jacobi = 0.0                                                  #one potential
light = MetricCalculator(FlowSpacetime(one, transverse='constraint'))
```

The `combine='turning'` flow is only for two bodies going round their centre of mass on circles, both with the same
`circling`. The flows with `combine='squares'` (the potential flow) are only for bodies at rest.

## Part 4: bodies moved by the flow

| Model | Python | Parameters | Used in |
| --- | --- | --- | --- |
| Each body in the others' flow | `CarriedBodies(masses, places, velocities, transverse=False)` from `engine/carried.py`, stepped with `sim.step(dt)` | `transverse`: `False` for flat space, `'source'` for space curved by the flow relative to its body | [Each Body in the Others' Flow](../part4/each-body-in-the-others-flow.md) |
| Moving with its own space | worked out exactly, not stepped: `studies/binary_regularized.py` (sympy), each body a geodesic of the one potential's metric with its own singular terms averaged away | which of the flow's corrections to keep | [Moving With Its Own Space](../part4/moving-with-its-own-space.md) |

```python
import math
from engine.carried import CarriedBodies
a = 1e8                                                    #two suns 100,000 km apart, on a circle
v = 0.5*math.sqrt(G*2*MS/a)
sim = CarriedBodies([MS, MS], [[a/2, 0.0], [-a/2, 0.0]], [[0.0, v], [0.0, -v]])
period = 2*math.pi*math.sqrt(a**3/(G*2*MS))                #386 s
for _ in range(4000):
  sim.step(period/4000)                                    #one orbit
print(sim.places())
```

## Part 5: gravitational waves

| Model | Python | Parameters | Used in |
| --- | --- | --- | --- |
| A plane wave through the plane | `SpecialFlowCalculator([], 2, wave=PlaneWave(...))` | `plus`, `cross`: the strains; `frequency`; `phasePlus`, `phaseCross`; `start`; `centre`; `along`, a direction in the plane for a wave crossing it (none: through it) | [Part 5](../part5.md) |
| A wave with space curved, or in general relativity's form | `MetricCalculator(WaveSpacetime(wave, form))` | `form='flow'` or `'tt'` | [Part 5](../part5.md) |

```python
from engine.waves import PlaneWave
calc = SpecialFlowCalculator([], 2, wave=PlaneWave(plus=1e-3, frequency=1.0))   #no bodies, the wave alone
```

A binary's waves (`engine/radiation.py`: `Binary`, `BinaryWave`, `OutgoingWave`) are built from its orbit and give a
wave's flow at each place and time.

## Which study runs which

| Page | Studies |
| --- | --- |
| The four tests | `four_tests.py`, `redshift_pulses.py` |
| Black and white holes | `black_holes.py`, `white_holes.py` |
| Rotating black holes | `kerr_paths.py`, `kerr_comparison.py` |
| Potential Flow | `two_body_tests.py` (its direction on the command line: `g`, `eikonal`, `eikonal-exact`), `multi_body_clocks.py` |
| The Hollow Sphere | `hollow_sphere.py`, `hollow_sphere_curved.py` |
| Curved Space | `lapse_two_bodies.py`, `hollow_sphere_curved.py` |
| Multiple Bodies | `three_bodies.py` |
| Carrying the Flow | `moving_bodies.py`, `turning_eikonal.py` |
| Curving the Turning Flow | `lapse_moving.py`, `turning_eikonal.py` |
| One Potential | `lapse_moon.py`, `light_two_rays.py`, `lapse_moving.py` |
| Part 5 | `grav_wave.py`, `grav_wave_across.py`, `binary_waves.py`, `binary_outgoing.py` |
| Each Body in the Others' Flow | `carried_bodies.py` (its tests on the command line: `binary`, `nordtvedt`, `plots`) |
| Moving With Its Own Space | `binary_regularized.py`, `eccentric_bodies.py` (on `eccentric_flow.py`'s flow) |
| Part 6 | `horizon_peeling.py` |

Studies that compare several models name them in a `MODELS` list at the top, and build each with a `spacetime(model)`
function: the names in the pages' tables are those names, written out. Several take a chosen set on the command line,
for example:

```bash
python3 studies/lapse_moon.py 90 differenced "models=GR|turning, flat"
```
