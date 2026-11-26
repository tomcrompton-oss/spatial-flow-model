# Potential Flow

[The Two Body Problem](two-body-problem.md) left us with a speed for space but no direction: the two bodies'
potentials added say how fast space must flow, but nothing says which way. The [Hollow Sphere](hollow-sphere.md)
showed two things. A flow can change direction abruptly at a boundary, and something crossing it changes reference
frame, keeping its velocity relative to the boundary. And whatever the direction, it has to be chosen, because
the speed alone doesn't give one.

This page chooses it the way the single body already does.

## A flow with no swirl

Round a single body, space flows straight in at $\sqrt{2GM/r}$. Two things make that flow work:

- **Its speed** is the escape speed, so clocks held still are slowed as general relativity says.
- **It has no swirl.** Space doesn't spiral in, so space moving with the flow speeds up at exactly Newton's $g$.
  This is why the [Newtonian](../part1/mechanics/newtonian.md#why-this-is-newtons-gravity) mechanics give Newton's
  law.

A flow with no swirl is what fluid dynamics calls a *potential flow*: its velocity is the slope of a single function,
$S$, the way a ball rolls down the slope of a hill. For two bodies, keep both properties: the speed from the two
potentials added, and no swirl,

$$
\mathbf u = -\nabla S, \qquad |\nabla S|^2 = \frac{2GM_1}{r_1} + \frac{2GM_2}{r_2}
$$

Then space moving with the flow falls at exactly Newton's $g$ for both bodies together, and clocks held still keep
general relativity's rates. Nothing here depends on there being two bodies: the same rule works for any number, which
[Multiple Bodies](multiple-bodies.md) shows. The flow's lines are the paths of things falling from rest far away, as they are round
one body. (This is the eikonal, or zero-energy Hamilton–Jacobi, equation; for two bodies it can be solved exactly.)

## The flow round two bodies

![The potential flow round two bodies. Left, two equal bodies: the flow comes in from far away and falls straight into each body; a dashed seam runs up the line half way between them; between the bodies, the flow leaves the seam on both sides and runs to each body. Right, one body four times the other: the seam curves round the lighter body](images/potentialflow.svg)

No flow like this can be smooth everywhere round two bodies. Each body has a region of its own, filled by the flow
that runs into it, and the two regions meet at a **seam**. The seam passes through the point between the bodies
where their pulls cancel and $g$ is zero. For equal bodies it is the line half way between them; for unequal ones it
curves round the lighter body.

Far from the pair, space falls straight in towards it, as round one body of the combined mass. Close to either body,
the flow is nearly that body's own. Between them, space flows *out* of the seam on both sides, towards each body.
Across the seam, the flow's direction jumps; along it, the flow is the same on both sides, and its speed is the same.

## The seam and the hollow sphere

The seam is the hollow sphere's boundary again: a place where space flows two ways at once, one on each side.

![Two rows along a line. Top, the hollow sphere in option D: space flows in towards the shell from outside, and inside it flows out from the centre both ways, so space splits at the centre. Bottom, two bodies in the potential flow: space flows in towards each body from outside, and between them it flows away from the seam towards each body, so space splits at the seam, where g is zero](images/watershed.svg)

Along the line between two bodies, the potential flow looks just like the hollow sphere's option D at its centre:
space splits, flowing away on both sides. And the seam is crossed the same way. Something reaching the seam changes
reference frame, keeping its velocity relative to the seam, and carries on in the space on the other side. (The
simulation keeps its energy and its momentum along the seam, which for a seam at rest comes to the same thing.)

Unlike the hollow sphere's head-on meetings, the seam never traps anything. Space flows *away* from it on both sides,
so nothing carried with the space is carried into it. Only something moving through space crosses it, and then it
passes straight through.

What the seam doesn't say is where the space flowing away from it comes from. That is the same open question as
the hollow sphere's meeting points. [Seams](seams.md) takes both up, along with where a seam can be and what crossing it does.

## Does it work?

### Orbits round both bodies

Each orbit round the pair crosses the seam twice. The simulation runs orbits round two black holes of one solar mass
each, 1 AU apart, in the potential flow and under Newton's gravity from the same starts:

<iframe src="../../viewer/index.html?player&run=../runs/twoBodyTests/twoBodyTests_bothHoles.full.json" width="100%" height="520" loading="lazy" title="Orbits round two holes in the potential flow"></iframe>

*Orbits round both holes: the potential flow (solid) and Newton's gravity (dashed), over the flow and its seam. Each
crosses the seam twice an orbit.*
[Open full screen](../../viewer/index.html?run=../runs/twoBodyTests/twoBodyTests_bothHoles.full.json){ target=_blank }

| Orbit (round the centre of the pair) | Times round | Precession, potential flow | Precession, Newton |
| --- | --- | --- | --- |
| circular, 1.2 AU | 9 | 34.6594° an orbit | 34.6595° |
| circular, 2 AU | 15 | −0.18505° | −0.18500° |
| circular, 2 AU, the other way round | 15 | −0.18505° | −0.18500° |
| circular, 3 AU | 14 | −2.5338° | −2.5334° |
| circular, 5 AU | 18 | −1.4016° | −1.4012° |
| elliptical, 1.5 to 2.5 AU | 17 | 19.5511° | 19.5507° |

*(The pair's pull isn't quite that of one body at the centre, so even Newton's orbits precess.)* Crossing the seam
twice an orbit, every one of them matches Newton's orbit, its precession to within 0.0005° an orbit. Close to
the bodies, general relativity's own corrections would add to these; here, far from both, Newton's gravity is the
test.

### Clocks

The flow's speed comes from both potentials, so clocks held still should keep general relativity's rates. Here the
Sun is held 1 AU from the Earth, and a clock on the Earth's equator and one in GPS orbit are compared with general
relativity over a day, in the potential flow and with the two bodies' flows simply added as vectors:

<iframe src="../../viewer/index.html?player&run=../runs/multiBodyClocks/multiBody_clocks.full.json" width="100%" height="440" loading="lazy" title="Clocks on the Earth and in GPS orbit"></iframe>

*Each clock's rate less general relativity's, over a day, in parts in 10⁹: the flows added as vectors, on the equator
(blue) and in GPS orbit (green); the potential flow, on the equator (orange) and in GPS orbit (yellow), both flat at
zero.*
[Open full screen](../../viewer/index.html?run=../runs/multiBodyClocks/multiBody_clocks.full.json){ target=_blank }

| Clock | Flows added as vectors | Potential flow |
| --- | --- | --- |
| On the equator | rate out by 5.2 parts in 10⁹: 69 µs a day | agrees, to the rounding of the arithmetic |
| In GPS orbit | rate out by 2.6 parts in 10⁹: 20 µs a day | agrees, to the rounding of the arithmetic |

Added as vectors, the two flows' cross term puts the clocks out by microseconds a day; GPS would notice within
seconds. The potential flow keeps them exactly.

## Where it stops

The potential flow passes every test at Newton's level, and the clocks. It fails the first test beyond them: lunar
laser ranging, the distance to the Moon measured to millimetres. That is where [Curved Space](curved-space.md) begins.

*The code: studies/two_body_tests.py (orbits round both holes), studies/multi_body_clocks.py (clocks); the flow
itself: engine/two_centre.py.*
