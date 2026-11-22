# Two bodies

With one body, spatial flow is general relativity exactly ([1.4](../part1/conclusion.md)): space falls into the body
at $\sqrt{2GM/r}$, clocks tick by their speed through that space, and light crosses it at c. With two bodies, each has
its own flow, and the picture has to say how they combine. Nothing in the one-body case fixes that rule. These pages
try each rule in turn, run it in the simulation, and check it against what is expected – the ways of building the
flow that don't give GR, and why, on the way to the one that does.

## What a rule has to do

**Expected** means general relativity's prediction, or the measurement where there is one. To first order in G, GR's
effects of two bodies simply add: each body's pull, each body's slowing of clocks, each body's bending of light.
Where they don't add, the difference is second order in G, far too small to matter in the solar system. So a rule
passes a test when it gives that sum, to within the measurement.

The tests, most of them with the Sun and the Earth:

| Test | Expected | How well it is measured |
| --- | --- | --- |
| **Newton's g**: particles let go near the Earth, the Sun 1 AU away | the sum of the two pulls | everyday mechanics |
| **Falling space**: does space moving with the flow fall at g? | yes, if the flow has no curl | needed for the model to make sense |
| **Clocks**: on the equator and in GPS orbit, over a day | GR's rates | GPS clocks agree to nanoseconds |
| **Lunar laser ranging**: radar from the Earth to the Moon | the Sun adds only its tide | millimetres; the term at the Moon's synodic period to (2.8 ± 4.1) mm |
| **Light past Jupiter**: the bending, both bodies less each alone | 0 | VLBI: positions to under 10 µas |
| **Light past the Sun** | GR's bending | Cassini: to 0.01 mas at 2 solar radii |
| **The system moving**: everything moving together at a steady speed | no change at all | lunar ranging, GPS, pulsars |
| **Einstein's constraint**: is the flow empty space, in GR's terms? | 0 outside matter | |

Each page explains why the rule might work, shows it in a diagram, lists its tests with a clear **pass** or **fail**,
and goes through one test in detail, with the simulation's runs in the viewer.

## The approaches

| Approach | The rule | Verdict |
| --- | --- | --- |
| [Vector addition](vectors.md) | add the bodies' flows as vectors, $\mathbf u = \sum \mathbf u_i$ | ❌ fails Newton's g by 37–74 m/s² at the Earth's surface |
| [Along g](along-g.md) | speed from the potential, $\lvert\mathbf u\rvert^2 = \sum 2GM_i/d_i$, pointing along g | ❌ space doesn't fall at g: off the axes g is out by up to 174% |
| [The eikonal flow](eikonal.md) | that speed, pointing down the paths of things falling from rest far away | ✅ Newton and clocks; ❌ lunar laser ranging (27σ) |
| [Each body carrying its flow](turning.md) | the eikonal flow turning with the bodies, the Earth carrying its own | ✅ lunar ranging; ❌ light past the Sun (1000 × Cassini's limit) |
| [Each body separately](split.md) | each body's own one-body flow, its effects on a particle applied one after the other | ✅ most tests with one body much heavier, and with each body's flow carried by the heavier body's space, lunar ranging and de Sitter precession; ❌ then the Nordtvedt effect, and a binary of comparable masses: the orbit turns 17% too slowly, and the pair accelerates by itself |
| [One potential, space curved](../lapse-curved-space.md#one-potential-for-the-whole-plane-the-turning-flow-with-j-0) | the turning flow with Jacobi constant 0, space stretched across it, its first post-Newtonian corrections from Einstein's equations | ✅ every test run on it: lunar ranging, the Moon's orbit and de Sitter, light past a moving Jupiter, the circular binary – GR |

The first two fail at the level of Newton's gravity. The next two pass Newton's tests and fail the first
relativistic one, each in a different place, because a single flow through flat space has to carry every body's space
at once. The fifth drops the single flow and treats each body by its own exact solution; it passes most tests with
one body much heavier than the other, but with comparable masses the bodies' fields have to act on each other, and
they don't. The last keeps one flow and lets space be curved across it, as Einstein's constraint requires: that is
GR, written as a flow.

[Two checks on every model](checks.md) scores each one on whether it keeps the energy and angular momentum its
symmetries say it should, and whether its flow's change along itself is Newton's g. Every single flow keeps its
conserved quantities (it is one spacetime), so the second check tells them apart; the split model passes the second
by construction and fails the first, keeping no energy at the first relativistic order.

[Many bodies](../many-bodies.md) works through the eikonal and turning flows at more length, and
[Lapse and curved space](../lapse-curved-space.md) builds the flow that is GR: clocks that keep the flow's time
(N = 1), one potential over the whole plane, and space stretched across the flow.
