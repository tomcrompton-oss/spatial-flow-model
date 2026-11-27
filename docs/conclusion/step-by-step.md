# The Model, Step by Step

The model was built up one feature at a time, from a Newtonian flow to the flow that is general relativity for bodies
moving each other. Parts 1 to 5 tell that story with every rule that failed along the way. Here only the steps that
stay are listed: each adds one thing and keeps everything before it.

| No. | Model | Feature added | Where it comes from | New tests passed |
| --- | --- | --- | --- | --- |
| **1. One body** | | | | |
| 1.1 | Newtonian flow | space flows into a body at the escape speed, through flat space | Newton: the speed of a body falling from rest far away | Newton's gravity for one body |
| 1.2 | Relativistic flow | motion through the flow is special relativity; clocks are slowed only by their speed through space | special relativity, and the identity that general relativity's clock rate is special relativity's at the escape speed | the four classical tests, exactly: it is Schwarzschild in Gullstrand–Painlevé coordinates |
| 1.3 | Spinning body | a spinning body's space twists as it flows | Hamilton and Lisle's river model of a rotating hole | light and orbits as exact Kerr, in the equatorial plane |
| **2. Bodies at rest** | | | | |
| 2.1 | Potential flow | for several bodies, a flow with no swirl, its speed the escape speed from them all; seams crossed keeping energy and momentum along the seam | Newton's $g$: only a flow with no swirl falls at $g$ | Newton's gravity and clocks for several bodies at rest |
| 2.2 | Curved space | space stretched across the flow by $u^2/c^2$ | Einstein's Hamiltonian constraint, with clocks slowed only by their speed | lunar ranging's Sun term, light past Jupiter, with the bodies at rest |
| **3. Bodies on given paths** | | | | |
| 3.1 | Carried space | a moving body carries its space, not just the pattern of its flow | a steady motion is only a change of frame | Newton's gravity and clocks round a moving body |
| 3.2 | One potential | the bodies' flows solved together, keeping Bernoulli's equation with no constant | free fall in a field that changes with time; space at rest far away | light past the Sun and past a moving Jupiter |
| 3.3 | Corrections | the flow's first post-Newtonian corrections, including each body's potential carried at its velocity | general relativity's first post-Newtonian metric in this time; Einstein's momentum constraint and Raychaudhuri's equation | the Moon's orbit, de Sitter's turn included |
| **4. Bodies moving each other** | | | | |
| 4.1 | Moving with its own space | each body moves with the space round it, averaged over a small sphere | Hadamard's finite part, as in post-Newtonian theory | a circular binary of any masses, exactly general relativity's |
| 4.2 | Spinning bodies | spin for several bodies, through 3.3's moving potentials of each body's own rotating matter | general relativity's first post-Newtonian frame dragging | orbits with and against the spin, as exact Kerr's (equatorial) |
| **5. Waves** | | | | |
| 5.1 | Radiation reaction | the waves' reaction put into the flow, through Bernoulli's equation | the Burke–Thorne potential; space's own evolution equation | the Hulse–Taylor pulsar's orbital decay |

With step 3.3 the model is general relativity's whole first post-Newtonian metric, written in the time of observers
falling freely with the flow. [Prior Work](../appendix-c/prior-work.md) compares each piece with the published
literature. [What Comes From Outside](from-outside.md) asks which of the sources in the fourth column could come from
the flow itself.

## 1. One body

For one body the flow is exact general relativity: Schwarzschild in 1.2, Kerr in 1.3.

**1.1 Newtonian flow** ([Newtonian](../part1/mechanics/newtonian.md)). Space flows straight into a body through flat
space at $u = \sqrt{2GM/r}$, the speed of something falling from rest far away. A particle moves at
$\mathbf v = \mathbf u + \mathbf w$, $\mathbf w$ its velocity through the space it is in. A flow straight in at that
speed speeds up at $(\mathbf u\cdot\nabla)\mathbf u = \nabla(u^2/2)$, which is Newton's $g$. Newton's apple falls 10 m
in 1.4272 s, against Newton's 1.4271 s, and orbits are Kepler's fixed ellipses.

**1.2 Relativistic flow** ([Special Relativistic](../part1/mechanics/special-relativistic.md),
[The Four Clocks](../part1/mechanics/four-clocks.md), [The Four Tests](../part1/tests/index.md)). Motion through the
flow is special relativity: velocities add relativistically, light moves at $c$ through space, and a clock is slowed
only by its speed through space. A clock held still moves through space at the escape speed, and special relativity's
rate there, $\sqrt{1 - 2GM/rc^2}$, is general relativity's. The four classical tests come out exactly: the
redshift, light's bending to 1.5 parts in 10⁸, Mercury's 43.01″ a century, and the Shapiro delay.

**1.3 Spinning body** ([Rotating Black Holes](../part1/rotating-black-holes.md)). Round a spinning body, space also
twists as it falls. Light and orbits match exact Kerr in the equatorial plane, to 2 parts in 10⁵ for light and 2 in
10⁴ for orbits.

## 2. Bodies at rest

**2.1 Potential flow** ([The Hollow Sphere](../part2/hollow-sphere.md), [Potential Flow](../part2/potential-flow.md)).
For several bodies the flow is the slope of one potential, $\mathbf u = -\nabla S$ with $|\nabla S|^2 = \sum
2GM_i/d_i$: no swirl, and the paths of things falling from rest far away. Each body has a region, and something
crossing a seam between regions keeps its energy and its momentum along the seam. Only a flow with no swirl falls at
$g$; the flows added as vectors, or pointed along $g$, don't. Newton's gravity and the clocks hold, but with flat
space lunar ranging fails by 11 cm.

**2.2 Curved space** ([Curved Space](../part2/curved-space.md), [Deriving Curved
Space](../part2/deriving-curved-space.md)). Space is stretched across the flow by $u^2/c^2$:
$\gamma = \delta + (u^2\delta - \mathbf u\mathbf u)/c^2$. It is what general relativity gives for bodies at rest,
with time kept by clocks falling with space, and it is what Einstein's Hamiltonian constraint asks of a flow with no
swirl: with flat space that constraint fails by 13% typically and up to 82% between two bodies; with this space it
holds to 10⁻¹⁰. Lunar ranging and light past Jupiter, with the bodies at rest, then pass.

## 3. Bodies on given paths

**3.1 Carried space** ([Carrying the Flow](../part3/carrying-the-flow.md)). A moving body carries its space:
$\mathbf u = \mathbf V + \mathbf u_\text{body}$. Taking only the flow's pattern along fails Newton's $g$ by
26–52 m/s².

**3.2 One potential** ([One Potential](../part3/one-potential.md)). With the bodies moving, the flow keeps
Bernoulli's equation, $\partial\phi/\partial t + u^2/2 = \Phi$, with no constant added: one potential over the
whole plane. The turning flow, which chose a constant so that the Earth's flow was its own, failed light past the Sun
by 9.6 mas, and with space curved still failed the Moon and light past a moving Jupiter.

**3.3 Corrections** ([One Potential](../part3/one-potential.md)). The flow's first post-Newtonian corrections, from
general relativity in this time: the flow slowed slightly, a correction that keeps clocks slowed only by their speed,
and each body's potential carried at its velocity. Einstein's momentum constraint and Raychaudhuri's equation are
what fix them. The Moon then turns as general relativity's does, $k = +0.01$, with 3.6 cm left over 90 days, at
the method's floor.

## 4. Bodies moving each other

**4.1 Moving with its own space** ([Moving With Its Own Space](../part4/moving-with-its-own-space.md)). Each body
moves with the space round it, averaged over a small sphere: Hadamard's finite part. Moving each body in the others'
flow alone instead fails a binary of comparable masses three ways. With this rule a circular binary's orbit is
general relativity's exactly; without step 3.3's moving potentials it turns a third as fast at equal masses.

**4.2 Spinning bodies** ([Spinning Bodies](../part4/spinning-bodies.md)). Spin for bodies that move each other
enters through step 3.3's moving potentials: each body's
own rotating matter, which far from it is a swirl in the flow, $2G\,\mathbf J\times\mathbf x/c^2r^3$. Run round one
spinning body with this swirl alone, no twist, clocks slowed only by their speed and flat space
(`studies/frame_dragging.py`), orbits going with the spin and against it differ by exact Kerr's amount:

| Orbit | Spin | Part odd in the spin, per orbit (rad) | / exact Kerr's |
| --- | --- | --- | --- |
| 55–100 M | 0.1 | −4.974 × 10⁻³ | 1.0000 |
| 55–100 M | 0.5 | −2.488 × 10⁻² | 0.9997 |
| 233–400 M | 0.1 | −5.164 × 10⁻⁴ | 1.0000 |

With no spin the orbits precess as exact Schwarzschild's, to 10⁻⁶. Step 1.3's twist and the many-body model agree for
one body.

## 5. Waves

**5.1 Radiation reaction** ([Part 5](../part5.md)). Far from the bodies, Einstein's evolution equation for space is a
wave equation, and the flow drops out of it: waves are space alone. The energy they carry off leaves through the
flow: the radiation-reaction potential, put into Bernoulli's equation, changes the flow slightly, and the bodies,
moving with their space, feel it. The Hulse–Taylor pulsar's orbital period then shrinks at 0.999991 of general
relativity's rate.

## And Part 6

Hawking and Unruh radiation add nothing to the model. A hole's temperature is set by how steeply the flow speeds up
at its horizon, and [Part 6](../part6/index.md) follows that from the flow as it already is.

## Not yet run

- **Bodies off circles.** For an eccentric binary the flow is built in time, and each body moves with its own space to
  about 10⁻⁸ of its speed. So by step 4.1 the bodies move by general relativity's two-body equations, with its orbit's
  turning, a centre that stays put and no Nordtvedt effect: argued, not run as orbits.
- **Spin off the plane.** The engine is planar, so frame dragging's tilt of an orbit (LAGEOS, Gravity Probe B) isn't
  run; step 4.2's equatorial orbits are exact Kerr's.
