# Part 2 in brief

For one body, space flowing in at the escape velocity through flat space, with clocks slowed only by their speed
through it, is general relativity exactly ([1.4](part1/conclusion.md)). Part 2 asks what the flow has to be for
several bodies. The answer, in one line: **one flow, clocks that keep its time, and space stretched across it, the
flow's corrections set by Einstein's equations.**

## What the flow needs, and the rule that showed it

Each rule tried fails somewhere, and where it fails says what the flow needs:

| The flow needs | The rule without it | What goes wrong |
| --- | --- | --- |
| speeds that add as squares, $\lvert\mathbf u\rvert^2 = \sum 2GM/d$ | [vector addition](two-bodies/vectors.md) | Newton's g out by 37–74 m/s² at the Earth's surface |
| no curl, $\mathbf u = \nabla\phi$, so space falls at g | [along g](two-bodies/along-g.md) | g out by up to 174% off the axes |
| each body's space moving with the body | the [eikonal flow](two-bodies/eikonal.md) with a moving Earth | g out by 26–52 m/s² |
| one flow shared by all the bodies | [each body separately](two-bodies/split.md) | a binary's orbit turns 17% too slowly, and the pair accelerates by itself |
| one potential across the whole plane | the [carried flow](lapse-curved-space.md#the-carried-flows-seams-one-time-or-many) | light past a moving Jupiter turns 1.7″ at the seams |
| a Jacobi constant of 0 | the [turning flow](two-bodies/turning.md) with the Earth's own | light past the Sun 9.6 mas off, 1000 × Cassini's limit |
| space stretched across the flow | every flow through flat space ([many bodies](many-bodies.md)) | lunar ranging 27σ; the Moon's orbit hundreds of metres off |
| the flow's first post-Newtonian corrections | the J = 0 flow with Einstein's space alone | the Moon 98 km off |
| … including each body's potential carried at its velocity, $4U_j/c^2$ | the J = 0 rules without it | a binary's periastron advance a third of GR's at equal masses |

## The flow that is GR

[Lapse and curved space](lapse-curved-space.md#one-potential-for-the-whole-plane-the-turning-flow-with-j-0) builds it,
for bodies on circles:

1. clocks keep the flow's time (N = 1): a clock's slowing is its speed through space;
2. the flow obeys Bernoulli's equation with Jacobi constant 0, $\partial_T\phi + |\nabla\phi|^2/2 = U$ – space falls at
   Newton's g, and the bodies' flows are one potential;
3. space is stretched by the potential and contracted along the flow,
   $\gamma = (1 + 2U/c^2)\delta - \mathbf u\mathbf u/c^2$ (Einstein's constraint);
4. the flow has first post-Newtonian corrections: slowed by $(U + u^2/2)/c^2$, each body's potential carried at its
   velocity ($4U_j/c^2$), and a gradient $\nabla\chi/c^2$ that keeps N = 1.

It passes every test run on it: the Moon's orbit (0.6 m, the floor of GR's own exact transform to this
time), light past a moving Jupiter as VLBI measures it (2–12 µas), and a circular binary of any masses, each body
moving with the regular part of its own space (exactly GR's). And rule 4 isn't put in by hand: with N = 1 and this
space, Einstein's momentum constraint fixes the correction's curl and the trace of his evolution equation fixes its
divergence. Only the bodies' kinetic and binding energy, which the field equations can't see from outside the bodies,
come from the bodies themselves – as a body's mass does in Newton's gravity.

So it is GR, written in the coordinates of observers falling freely with the flow – for several bodies what
Gullstrand–Painlevé's coordinates are for one. The picture of Part 1 keeps its clocks and its single flow; what it
gives up is flat space. The [scorecard](scorecard.md) scores every version against GR's tests and Part 1's premises.
