# 1.4 Conclusion of Part 1

In Part 1 we set out a hypothesis for an alternative theory of gravity, based on the motion of space.

It passes the four original tests of general relativity. We didn't look at time dilation in much detail, but the
other tests passed with a very high degree of accuracy — over 99% agreement with general relativity's approximations
for the bending of light and the precession of Mercury, although less for the Shapiro effect.

The Shapiro effect raised some interesting questions: although the round trip agrees with general relativity, the
time delay is not symmetrical. Part 2 looks at time dilation more closely, including that asymmetry.

!!! info "Since this was written"
    With the simulation as it is now, all four tests pass outright:

    | Test | Spatial flow against general relativity |
    | --- | --- |
    | gravitational redshift | exact: a clock holding still against the flow ticks at GR's static rate, $\sqrt{1 - r_s/r}$ (1.3.1) |
    | bending of light | exact GR deflection to parts in $10^7$, 1–1000 AU out, 0.025–1 solar radii from the Sun |
    | precession | exact GR for the orbit's own apsides to 1.6 × 10⁻⁴, at 65–19,600 Schwarzschild radii |
    | Shapiro delay | round trips as GR; each leg differs only by the clock offset between its ends (1.3.4) |

    The reason is that, for a single body, spatial flow *is* general relativity: the flowing-space metric
    $ds^2 = -c^2dt^2 + |d\mathbf x - \mathbf u\,dt|^2$ with $|\mathbf u| = \sqrt{2GM/r}$ is the Schwarzschild solution
    in Gullstrand–Painlevé coordinates, and the procedure of 1.2 is its geodesic equation, because the flow has no
    curl. The time spatial flow runs on — a distant observer's, and anything falling with the space — is
    Gullstrand–Painlevé time. That answers the question the original asks in Part 2, of whether this is "just
    another coordinate system": for one body, yes. Whether it stays so with more than one body is where it gets
    interesting ([Two bodies](../two-bodies.md)).

## The model as it is now

Space flows through a flat background at a velocity $\mathbf u$, and a particle moves at $\mathbf v = \mathbf w +
\mathbf u$, with $\mathbf w$ its velocity relative to the space it is in. As it moves, $\mathbf w$ changes by the
difference between the flow where space goes and the flow where the particle goes, added relativistically:

$$
\frac{d\mathbf x}{dt} = \mathbf w + \mathbf u(\mathbf x), \qquad \frac{d\mathbf w}{dt} = -(\mathbf w \cdot \nabla)\,\mathbf u
$$

Its proper time runs at $\sqrt{1 - w^2/c^2}$, and light is anything with $|\mathbf w| = c$. Round one body the flow is
$\sqrt{2GM/r}$, straight in. Each step goes half way the first-order way, then takes the whole step at the middle's
rates (second order), with light kept at exactly $c$, and steps shrink close to a body.

A rotating (Kerr) hole is the river model of Hamilton and Lisle (2008): the river flows straight in and also twists.
In the equatorial plane, light bends as exact Kerr does to 2 × 10⁻⁵ at spins up to 0.99, with and against the spin,
and orbits precess as exact Kerr to 2 × 10⁻⁴ (`studies/kerr_comparison.py`).

Close to a hole, within about 10 Schwarzschild radii, the step is effectively first order and orbits decay. A step on
the particle's momentum, $d\mathbf p/dt = -(\nabla\mathbf u)\cdot\mathbf p$, is the planned fix; it is also the
geodesic step for flows with curl (1.2.5.1).

The examples on these pages come from `studies/part1_examples.py`.
