# 1.4 Conclusion of Part 1

Part 1 set out gravity as the motion of space: space flowing into a body at the escape velocity, through flat space,
with clocks slowed only by their speed through it. With the simulation as it is now, all four tests come out as
general relativity:

| Test | Spatial flow against general relativity |
| --- | --- |
| gravitational redshift | exact: a clock holding still against the flow ticks at GR's static rate, $\sqrt{1 - r_s/r}$ (1.3.1) |
| bending of light | exact GR deflection to parts in $10^7$, 1–1000 AU out, 0.025–1 solar radii from the Sun |
| precession | exact GR for the orbit's own apsides to 1.6 × 10⁻⁴, at 65–19,600 Schwarzschild radii |
| Shapiro delay | round trips as GR; each leg differs only by the clock offset between its ends (1.3.4) |

The reason is that, for a single body, spatial flow *is* general relativity: the flowing-space metric
$ds^2 = -c^2dt^2 + |d\mathbf x - \mathbf u\,dt|^2$ with $|\mathbf u| = \sqrt{2GM/r}$ is the Schwarzschild solution in
Gullstrand–Painlevé coordinates, and the procedure of 1.2 is its geodesic equation, because the flow has no curl. The
time spatial flow runs on – a distant observer's, and anything falling with the space – is Gullstrand–Painlevé time.
So spatial flow is a way of seeing general relativity, and the question for more than one body is what the flow has
to be like to stay so ([Two bodies](../two-bodies/index.md), [Lapse and curved space](../lapse-curved-space.md)).

## The model as it is now

Space flows through a flat background at a velocity $\mathbf u$, and a particle moves at $\mathbf v = \mathbf w +
\mathbf u$, with $\mathbf w$ its velocity relative to the space it is in. As it moves, $\mathbf w$ changes by the
difference between the flow where space goes and the flow where the particle goes, added relativistically:

$$
\frac{d\mathbf x}{dt} = \mathbf w + \mathbf u(\mathbf x), \qquad \frac{d\mathbf w}{dt} = -(\mathbf w \cdot \nabla)\,\mathbf u
$$

Its proper time runs at $\sqrt{1 - w^2/c^2}$, and light is anything with $|\mathbf w| = c$. Round one body the flow is
$\sqrt{2GM/r}$, straight in. The simulation takes these equations on the particle's momentum,
$\mathbf p = \gamma\mathbf w$ – $d\mathbf x/dt = \mathbf u + \mathbf w$, $d\mathbf p/dt = -\nabla(\mathbf u\cdot
\mathbf p)$ – by the midpoint rule (second order), and steps shrink close to a body.

A rotating (Kerr) hole is the river model of Hamilton and Lisle (2008): the river flows straight in and also twists.
In the equatorial plane, light bends as exact Kerr does to 2 × 10⁻⁵ at spins up to 0.99, with and against the spin,
and orbits precess as exact Kerr to 2 × 10⁻⁴ (`studies/kerr_comparison.py`).

The earlier step, on w (half a step the first-order way, then the whole step at the middle's rates), was effectively
first order close to a hole, and was not the metric's path where the flow has curl (1.2.5.1). The momentum step fixes
both: an orbit from 200 to 600 Schwarzschild radii keeps its energy and angular momentum to 10⁻⁷ where the old step
left 3 × 10⁻⁵, the falls into black and white holes match GR to 10⁻⁷, and in a flow with curl it follows the
metric's own path and keeps the energy to 3 × 10⁻⁹ (`studies/momentum_step.py`). Far from a hole both are second
order, the new one's error about twice the old one's at the same step.

The examples on these pages come from `studies/part1_examples.py`.
