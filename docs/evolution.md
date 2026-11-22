# The model, step by step

The model built up one feature at a time, from a Newtonian flow to the flow that is general relativity for several
bodies. This isn't the order the work went in. That order, with every rule that failed along the way, is in
[Part 2](part2.md) and the [scorecard](scorecard.md). Here each step adds one thing and keeps everything before it.
The steps fall into four groups: one body, several bodies at rest, bodies moving on given paths, and bodies moving
each other.

| No. | Model | Feature added | Where the feature comes from | New tests passed |
| --- | --- | --- | --- | --- |
| **1. One body** | | | | |
| 1.1 | Newtonian flow | space flows into a body at the escape velocity, through flat space | Newton: the speed of a body falling from rest far away | Newton's gravity for one body |
| 1.2 | Relativistic flow | motion through the flow is special relativity | Special relativity, and the identity that GR's clock rate is SR's at the escape velocity | GR's four classical tests, exactly (it is Schwarzschild in Gullstrand–Painlevé coordinates) |
| 1.3 | Spinning body | a spinning body's space twists as it flows | Hamilton and Lisle's river model of a Kerr black hole | light bending and orbits as exact Kerr, in the equatorial plane |
| **2. Several bodies at rest** | | | | |
| 2.1 | Potential flow | for several bodies, a flow with no curl and speed² = 2U | Newton's g: only a flow with no curl falls at g | Newton's gravity for several bodies at rest |
| 2.2 | Curved space | space stretched by the potential and contracted along the flow | Einstein's Hamiltonian constraint, with N = 1 | lunar ranging's synodic term, light past Jupiter (bodies at rest) |
| **3. Bodies moving on given paths** | | | | |
| 3.1 | Moving flow (J = 0) | the bodies move (on circles); the flow keeps Bernoulli's equation with Jacobi constant 0 | Hamilton–Jacobi for free fall in a changing field | Newton's g with the bodies moving; light past a moving Jupiter |
| 3.2 | Post-Newtonian flow | the flow slowed by (U + u²/2)/c², less ∇χ/c² | GR's first post-Newtonian metric in this time; Einstein's evolution equation (its trace) | the Moon's orbit, with de Sitter's precession |
| **4. Bodies moving each other** | | | | |
| 4.1 | Self-moving bodies | each body moves with the regular part of its own space | Hadamard regularization, as in post-Newtonian theory | none: it makes a binary runnable, and the binary fails |
| 4.2 | Moving potentials | the flow plus each body's potential carried at its velocity, 4U_j/c² | a body's static field Lorentz-boosted (the first post-Newtonian vector potential); Einstein's momentum constraint | a circular binary of any masses, exactly GR's |
| 4.3 | Spinning bodies | 1.3's spin for several bodies, through 4.2's 4U_j of each body's own rotation | GR's first post-Newtonian frame dragging; Einstein's momentum constraint | not yet run (Lense–Thirring round the Earth) |

Model 4.2 is GR's whole first post-Newtonian metric, written in the slicing whose observers fall freely with the flow.
Spin is built and tested for one body (1.3), and not yet for several (4.3). [Prior work](prior-work.md) compares each
piece with the published literature. [What comes from outside](from-outside.md) asks which of the
sources could come from the flow itself.

## 1. One body

For one body the flow is exact general relativity: Schwarzschild in 1.2, Kerr in 1.3.

### 1.1 Newtonian flow

**The model.** Space flows straight into a body through flat space, at the speed something falling from rest far away
would have, $u = \sqrt{2GM/r}$. A particle moves at $\mathbf v = \mathbf u + \mathbf w$, where $\mathbf w$ is its
velocity relative to the space it is in. As it crosses from one region of space into another, $\mathbf w$ changes by
the difference in the flow, $d\mathbf w/dt = -(\mathbf w\cdot\nabla)\mathbf u$. Velocities add as Galileo's do, and
time is absolute ([1.2.4](part1/mechanics.md)).

**Feature added.** Gravity as the flow of space: space falls, and things in it fall with it, without feeling a force.

**Source.** Newton. The flow speed is the escape velocity
([1.1](part1/hypothesis.md)), and a flow straight in at that speed accelerates at
$(\mathbf u\cdot\nabla)\mathbf u = \nabla(u^2/2) = -GM\hat{\mathbf r}/r^2$, Newton's g.

**New tests passed.** Newton's gravity for one body. Newton's apple falls 10 m in 1.4272 s, as Newton has it, and
orbits are Kepler's fixed ellipses. Light bends 0.87″ past the Sun, which is Newton's value, half of what is observed.

### 1.2 Relativistic flow

**The model.** Model 1.1, with special relativity for motion through the flow. The change in $\mathbf w$ adds
relativistically, a clock ticks at $\sqrt{1 - w^2/c^2}$, and light is anything with $|\mathbf w| = c$
([1.2.5](part1/mechanics.md)).

**Feature added.** Clocks are slowed only by their speed through the space around them (lapse N = 1), and light moves
at c through that space.

**Source.** Special relativity, together with an identity: GR's rate for a clock held still in a gravity well,
$\sqrt{1 - 2GM/rc^2}$, is SR's rate for a clock moving at the escape velocity. A clock held still against the flow is
moving through space at exactly that speed. The model is the Schwarzschild solution in Gullstrand–Painlevé coordinates
(1921–22), the "river model" of black holes.

**New tests passed** ([1.3](part1/tests.md)):

- the gravitational redshift, exactly;
- the bending of light, 1.74″ past the Sun, exact GR to parts in 10⁷;
- Mercury's precession, exact GR to 1.6 × 10⁻⁴;
- the Shapiro delay, round trips as GR's.

The same model also holds a gravitational wave passing through the plane exactly ([waves](waves.md)).

### 1.3 Spinning body

**The model.** Model 1.2, for a body that spins. Round it, space flows straight in as before, and also twists: each
small piece of space rotates about the spin axis as it falls. A particle's velocity through space is boosted by changes in the flow, and
turned by changes in the twist ([1.2.3](part1/mechanics.md), `engine/kerr.py`).

**Feature added.** A body's spin, as a twist of the flowing space. The twist drags frames round the body.

**Source.** Hamilton and Lisle's river model of a rotating (Kerr) black hole (2008), built on Doran's coordinates.
In the river model the twist is what keeps the flow through flat space for a spinning hole, whose spacetime has no
flat slicing.

**New tests passed.** For one spinning hole, in its equatorial plane (`studies/kerr_comparison.py`):

- light bending, passing with the spin and against it, is exact Kerr to 2 × 10⁻⁵ at spins up to 0.99;
- orbits precess as exact Kerr does, to 2 × 10⁻⁴.

From here to 4.2 the bodies are points with no spin, so the twist is zero; 4.3 brings spin back.

## 2. Several bodies at rest

The bodies are held still. The question is how their flows combine.

### 2.1 Potential flow

**The model.** Model 1.2, for several bodies. The flow is the gradient of one potential, and its speed comes from the
bodies' potentials added:

$$
\mathbf u = \nabla\phi, \qquad |\nabla\phi|^2 = 2U = \sum_i \frac{2GM_i}{d_i}.
$$

Its flow lines are the paths of things falling from rest far away (the [eikonal flow](two-bodies/eikonal.md)). The
bodies are at rest.

**Feature added.** No curl. The flows' speeds add as squares, not as vectors.

**Source.** Newton's g. Space moving with a flow speeds up at $(\mathbf u\cdot\nabla)\mathbf u$, which equals
$\nabla(u^2/2) = \mathbf g$ only when the flow has no curl. The squared speeds have to add so that clocks keep GR's
rates. The equation is the zero-energy Hamilton–Jacobi equation. The simpler rules both fail:

- adding the flows as [vectors](two-bodies/vectors.md) gets g wrong by 37–74 m/s² at the Earth's surface;
- a flow pointed [along g](two-bodies/along-g.md) has curl, and gets g wrong by up to 174%.

**New tests passed.** Newton's gravity for several bodies at rest: space falls at g everywhere, and every Newtonian
test passes. GR's clock rates hold to first order. Lunar ranging (27σ) and light past Jupiter (400 µas) still fail.
Flat space can't take them.

### 2.2 Curved space

**The model.** Model 2.1, with space no longer flat. Space is stretched by the potential and contracted along the
flow:

$$
\gamma = (1 + 2U/c^2)\,\delta - \mathbf u\mathbf u/c^2,
$$

with the clocks still Part 1's, N = 1 ([lapse and curved space](lapse-curved-space.md#space-decided-by-the-flow)).

**Feature added.** Curved space, decided by the flow alone (its potential and its velocity).

**Source.** Einstein's Hamiltonian constraint. For any flow with no curl and N = 1, this is the space it requires
([Einstein's constraints](lapse-curved-space.md#einsteins-constraints-what-space-the-flow-needs)). One body's tests
stay GR's.

**New tests passed.** With the bodies at rest, the fields combine as GR's: lunar laser ranging's synodic term, light
past Jupiter (GR's less each body alone), and light past the Sun with the Earth nearby.

## 3. Bodies moving on given paths

The bodies move, on paths set in advance (circles), and the flow has to move with them.

### 3.1 Moving flow (J = 0)

**The model.** Model 2.2, with the bodies moving on given paths (here circles). The flow moves with them. It is still
one potential, now changing in time, and it keeps Bernoulli's equation with Jacobi constant 0:

$$
\partial_t\phi + \tfrac12|\nabla\phi|^2 = U.
$$

For bodies on circles the flow is steady in the frame turning with them
([the J = 0 flow](lapse-curved-space.md#one-potential-for-the-whole-plane-the-turning-flow-with-j-0)). Each point
belongs to the body whose flow arrives there with the largest φ, so the potential is continuous across the seam
between them.

**Feature added.** Moving bodies, with every body's flow solved together as one potential over the whole plane.

**Source.** The Hamilton–Jacobi equation of free fall in a field that changes with time. Its paths are free fall, so
space falls at g with the bodies moving. J = 0 is the constant of space falling from rest far away, the one value that
reaches every point. The alternatives fail:

- the [eikonal flow with a moving Earth](two-bodies/eikonal.md) gets g wrong by 26–52 m/s²;
- [each body's flow carried separately](lapse-curved-space.md#the-carried-flows-seams-one-time-or-many) keeps a
  separate time in each region, and light past a moving Jupiter turns 1.7″ at the seams;
- the [turning flow with the Earth's own J](two-bodies/turning.md) gets light past the Sun 9.6 mas wrong.

**New tests passed.** Newton's g with the bodies moving. Light past Jupiter on its orbit, as VLBI measures it, is
2–12 µas from GR, within VLBI's 10 µas. The Moon's orbit fails, 98 km off: Einstein's space is post-Newtonian, and a
flow of 50 km/s round the Earth needs post-Newtonian corrections to match it.

### 3.2 Post-Newtonian flow

**The model.** Model 3.1, with the flow's first post-Newtonian corrections:

- the flow is slowed by $(U + u^2/2)/c^2$;
- the flow has $\nabla\chi/c^2$ taken off it, where χ is carried along the flow from $Q = c^4(N^2 - 1)/2$. This moves
  the lapse's first post-Newtonian part into the flow, so that clocks keep N = 1.

**Feature added.** The flow's first post-Newtonian order.

**Source.** GR's first post-Newtonian metric, transformed to the J = 0 time. The trace of Einstein's evolution equation
(Raychaudhuri's equation for the observers falling with the flow) fixes the correction's divergence, and with N = 1
that equation is exactly χ's rule ([where the rules come from](lapse-curved-space.md#one-potential-for-the-whole-plane-the-turning-flow-with-j-0)).
The source of χ needs the bodies' own kinetic and binding energy, which the field equations can't see from outside
the bodies.

**New tests passed.** The Moon's own orbit, de Sitter's precession included. It is 0.49 m from GR, within the 0.6 m
floor of GR's own exact transform to this time. Light still passes.

## 4. Bodies moving each other

The bodies are no longer held on their paths: each moves in the flow the others and it make.

### 4.1 Self-moving bodies

**The model.** Model 3.2, with the bodies no longer held on their paths: each one moves through the flow as a particle,
in the regular part of its own space, with its own singular terms removed.

**Feature added.** Bodies moved by the flow they make.

**Source.** Hadamard's partie finie, the regularization post-Newtonian theory uses for point masses. It leads to
Einstein–Infeld–Hoffmann's equations of motion. Moving each body in the others' fields alone, as the earlier flows
did, leaves out the binding term in the others' source.

**New tests passed.** None. The circular binary can now be run, and it fails. Its orbital frequency has $-3 + 5\eta$
where GR has $-3 + \eta$, and its periastron advance is a third of GR's at equal masses. The Moon didn't show it,
because the Moon's own field is too weak. The failure says what is still missing.

### 4.2 Moving potentials

**The model.** Model 4.1, with each body's potential carried at its velocity added to the flow, $4\mathbf U_j/c^2$,
where $\mathbf U_j = \sum_b G m_b\mathbf v_b/d_b$ is the potential of the bodies' momentum.

**Feature added.** The field of a moving source: a body's motion moves its space.

**Source.** The vector potential of GR's first post-Newtonian metric (its $g_{0i}$, gravitomagnetism), which is a
body's static field Lorentz-boosted to its velocity ([what comes from outside](from-outside.md#a-bodys-own-field-moving-and-among-others)). It is also
Einstein's momentum constraint. With 3.2's slowing of the flow and this term together the constraint is met exactly, and without $4\mathbf U_j$
it misses by the moving potential's term $2\nabla\partial_t U$.

**New tests passed.**

- A circular binary of any masses: exactly GR's orbital frequency and periastron advance.
- Einstein's momentum constraint, exactly.
- The Moon (0.60 m) and light are unchanged.

With this, the corrections of 3.2 and 4.2 are Einstein's equations in the free-fall slicing, and the model is GR's
first post-Newtonian metric: one flow, clocks that tick by their speed through it, and space curved across it.

### 4.3 Spinning bodies

**The model.** Model 4.2, with the bodies spinning: 1.3's spin, for several bodies that move each other.

**Feature added.** Spin in the many-body flow. It enters through 4.2's term: the $4\mathbf U_j/c^2$ of each body's own
rotating matter, which far from the body is a curl in the flow, $2G\,\mathbf J\times\mathbf x/c^2r^3$.

**Source.** GR's first post-Newtonian frame dragging, and Einstein's momentum constraint with the bodies' angular
momentum as its source. For one body this curl should be the first post-Newtonian form of 1.3's twist – the link
isn't checked.

**New tests passed.** None yet: it hasn't been run. The test would be Lense–Thirring frame dragging round the Earth:
LAGEOS's nodes, and Gravity Probe B's 37 mas/yr.

## Not yet tested

- **Bodies off circles.** 3.1's flow is built for bodies on circles, in the frame turning with them. For an
  eccentric binary there is no such frame, and the flow has to be built in time. Built at Newton's order, it is still
  one potential reaching the whole plane, smooth near the bodies, with kinks far out at periastron
  ([off circles](lapse-curved-space.md#off-circles-the-j-0-flow-for-an-eccentric-binary)); nothing has been run in it
  yet, and 3.2–4.2 haven't been built on it. The other tests of a binary's general motion wait on that:
  its centre of mass staying put, and the Nordtvedt effect. GR's first post-Newtonian equations already give both
  (η = 0), so for 4.2 they would check the simulation, not the model.
- **Spin with several bodies (4.3).** Lense–Thirring frame dragging round the Earth (LAGEOS, Gravity Probe B).
  4.2's 4U_j already holds it, as GR's first post-Newtonian frame dragging, so a run would check the engine's curl
  term.
