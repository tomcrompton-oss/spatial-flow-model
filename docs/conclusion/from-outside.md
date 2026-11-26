# What Comes From Outside

Each step of [the model, step by step](step-by-step.md) brings something in from outside the flow: Newton's law,
special relativity, Einstein's equations, the post-Newtonian metric, Hadamard's averaging. This page asks which of them
can be derived from the flow of space instead.

The answer: all of them but three. One is special relativity, locally: the model's premise. One is the bodies'
masses, and with them $G$. The third is a single law about the flow: Einstein's equation, in a form that is a
statement about falling space. Everything else follows from the flow and those three.

## The ball law

Baez and Bunn ("The meaning of Einstein's equation", *American Journal of Physics* 73, 644, 2005) put Einstein's
equation as a statement about small balls of freely falling particles. A ball of test particles, at rest relative to
some observer, starts to shrink at a rate set by the energy and pressure inside it:

$$
\frac{\ddot V}{V}\Big|_{t=0} = -4\pi G\,(\rho + p_x + p_y + p_z)
$$

in that observer's frame, for a small ball and at the instant it starts. For one observer this is one equation
(Raychaudhuri's). Holding it for every observer, moving at every speed, is all of Einstein's equation.

"The ball law" is this site's short name for Baez and Bunn's form, not a term in general use: it isn't a law beside
Einstein's but his equation, stated another way.

In the flow picture the law is natural, because free fall is moving with space. A ball carried along with the flow is
a small piece of the flowing space itself, so the law says how falling space converges. A ball moving through the flow
is a cloud of particles crossing it, as light does.

The law isn't "space is conserved". Round one body the flow converges even where there is no mass, since
$\nabla\cdot\mathbf u \propto -r^{-3/2}$. Conserved space would need a flow falling off as $1/r^2$, and that is a
different gravity. The law sets how fast the convergence itself changes, which is the tide.

## What flat space gets right

`studies/ball_law.py` checks exactly, with computer algebra, the flow model with flat space: clocks keeping the flow's
time, and $\mathbf u = \nabla\phi$ for any $\phi(t, \mathbf x)$. The observers falling with the flow move along
$n = \partial_t + \mathbf u\cdot\nabla$.

| Check | Result |
| --- | --- |
| $R_{nn}$, the ball law for balls falling with the flow | exactly $-\nabla\cdot(D\mathbf u/Dt)$: minus the divergence of the flow's acceleration |
| $R_{ni}$, its mixed part (the momentum constraint) | exactly 0 |
| $G_{nn}$, the Hamiltonian constraint | exactly $\tfrac12(K^2 - K_{ij}K_{ij})$, $K_{ij} = \partial_i\partial_j\phi$ |
| one body, $\phi = -2\sqrt{2GMr}$ | every component of $R_{\mu\nu}$ is 0 (to 3 × 10⁻¹⁷³ of $GM/r^3$ at three points) |

With Bernoulli's equation, $\partial_t\phi + |\mathbf u|^2/2 = U$, the flow's acceleration is $\nabla U$, so
$R_{nn} = -\nabla^2 U = 4\pi G\rho$. That is the ball law for balls falling with the flow, to every order, not only
Newton's. So the flat flow of steps 1.1, 2.1 and 3.2 has no Newton in it: it is the ball law, exactly, for the
observers who move with space.

A ball moving through the flow at velocity $\mathbf w$ sees $R_{nn} + 2w^iR_{ni} + w^iw^jR_{ij}$. With flat space the
first two terms are already right, so only $w^iw^jR_{ij}$ can be wrong. For one body it isn't:
Gullstrand–Painlevé is exact Schwarzschild. For two bodies it is: the Hamiltonian constraint fails for the potential
flow with flat space by 13% typically and up to 82% (`studies/constraints.py`).

This explains the pattern of Part 2's scorecard. Every flat flow passes Newton and fails at the next order:

- the error a moving ball sees is of order $w^2/c^2$, which is the first order beyond Newton for bodies;
- light is the fastest ball, $w = c$, so it sees the error at full strength. That is why light past Jupiter failed by
  410 µas while every Newtonian test passed.

Curving space (step 2.2) is what the ball law needs for balls moving through the flow. With it the constraint holds
to 10⁻¹⁰. It isn't a fix brought in from elsewhere.

## Step by step

| Step | Brought in as | Can it come from the flow? |
| --- | --- | --- |
| 1.1: the flow's speed is the escape speed | Newton | **Yes.** It is the ball law for balls falling with the flow, with space at rest far away. Exact (above). |
| 1.2: motion through the flow is special relativity | special relativity | **No.** This is the premise: the equivalence principle, the local physics the flow picture assumes. |
| 1.2: clocks slowed only by their speed through space | the picture | **Yes.** If space's own observers fall freely, their acceleration, the slope of the clocks' rate, is zero, so the rate is the same everywhere and can be set to 1. It is the premise "moving with the flow is free fall". |
| 2.1: no swirl | Newton's $g$ | **Yes, two ways.** A flow defines one time only if its observers don't swirl (Frobenius's theorem). And free fall keeps swirl at zero if it starts at zero (Kelvin's theorem), so space at rest far away stays free of it. |
| 2.2: curved space | Einstein's Hamiltonian constraint | **Yes.** It is the ball law for balls moving through the flow: the $w^iw^jR_{ij}$ that flat space gets wrong. |
| 3.1: a moving body carries its space | a change of frame | **Yes.** A body moving steadily is a body at rest seen from a moving frame. |
| 3.2: Bernoulli's equation with no constant | Hamilton–Jacobi | **Yes.** It is the first integral of free fall for a flow with no swirl, and no constant is space at rest far away. $U$ isn't an input: it is the flow's head, and its Poisson equation is the ball law. |
| 3.3: the corrections that keep clocks slowed only by their speed | general relativity's first post-Newtonian metric | **Yes.** They are the ball law for balls falling with the flow, at the first order beyond Newton (Raychaudhuri's equation). |
| 3.3: the corrections' source, the bodies' kinetic and binding energy | general relativity's potentials | **Yes, from one body's field (checked, below).** The kinetic part is the body's static field boosted to its velocity; the binding part is its static field set in the others' clocks and rulers. |
| 3.3: each body's potential carried at its velocity | the first post-Newtonian vector potential | **Yes, by special relativity (checked, below).** It is a body's static field boosted to its velocity: half from its clocks and half from its curved space. It is also the momentum constraint, the ball law's mixed part. |
| 4.1: Hadamard's averaging | post-Newtonian theory | **Yes.** The finite part is the field averaged over a small sphere round the body, so the rule is step 1.1's for a body with size: it moves with the space it is in, averaged over the space round it. For a spherical body its structure drops out at this order. |
| 1.3 and 4.2: spin | the river model (Kerr) | **Yes.** At the first order beyond Newton it is the momentum constraint with the bodies' spin as the source: the same part of the ball law as the moving potentials. Run: the swirl alone, with no twist, gives exact Kerr's frame dragging in the equatorial plane (step 4.2). |
| 5.1: the radiation reaction | the Burke–Thorne potential | **Partly.** The waves themselves come from Einstein's evolution equation for space, the part of the ball law the earlier steps didn't need. The reaction's potential is taken from general relativity here, not derived from the flow. |
| the seam rule | a choice | **Nothing to derive.** It chooses how time is sliced where regions meet, and leaves the spacetime as it is. |

## What is left

- **Special relativity, locally.** The flow picture assumes it; nothing in the flow gives it.
- **The bodies' masses**, and $G$.
- **The ball law itself**, for what the bodies' own fields don't give: the nonlinearity between them (checked below
  for bodies at rest). It is Einstein's equation, so none of this derives general relativity from the flow without
  general relativity's content. What it shows is that the content fits in one sentence about the flow, and that
  Newton, the post-Newtonian rules and curved space all follow from it. The flow describes how space moves; a law
  about what moves it has to come from somewhere. Jacobson ("Thermodynamics of spacetime: the Einstein equation of
  state", *Physical Review Letters* 75, 1260, 1995) derived the law from Raychaudhuri's equation for light rays and
  the thermodynamics of horizons. That brings thermodynamics in from outside instead.

## A body's own field, moving and among others

`studies/field_from_bodies.py` checks, exactly, where the moving-body terms come from. They are three things in
general relativity's first post-Newtonian metric in its usual (harmonic) coordinates: the curved space
$(1 + 2U)\,\delta$, the vector potential $g_{0i} = -4U_i$, and the potential $\psi$ in the clocks' rate, with the
bodies' kinetic and binding energy. Each is rebuilt from one body's static field, which is Part 1's one-body flow in
these coordinates.

| Built from one body's static field | Against general relativity's first post-Newtonian metric | Result |
| --- | --- | --- |
| **Boosted** to a velocity $v$ (special relativity) | one body moving at $v$ | exactly equal, every component |
| **Set in another body's clocks and rulers** | two bodies at rest, near body 2 | exactly equal. The term in both bodies' masses is −6: −4 from $-2U^2$, −2 from the binding energy |
| **Between the bodies:** the vacuum ball law for observers at rest, with step 2.2's space | two bodies at rest, away from them: $g_{00} = -(1 - 2U + 2U^2 - 2\psi)$ | met exactly. With $-U^2$ or $-3U^2$ in place of $-2U^2$ it isn't (0.28 off) |

So:

- **The moving potentials are a moving body's field.** $4\mathbf U_j$ is what boosting a body's static field puts
  into $g_{0i}$: $2U$ from its clocks and $2U$ from its curved space. Boosted with flat space, as Gullstrand–Painlevé's,
  it gets only the clocks' half.
- **The corrections' source comes from the bodies' own fields.** Its kinetic part is the same boost. Its binding part
  is a body's field set in the clocks and rulers of the others' field where the body is: its clocks slowed by its
  speed through the others' flowing space, Part 1's clock rule, and its rulers stretched by step 2.2's space.
- **The ball law supplies the rest:** what makes the fields more than their sum, the $-2U^2$ in $g_{00}$. For bodies
  at rest, their clock rates multiply.

## Run it

```bash
python3 studies/ball_law.py
```

```bash
python3 studies/field_from_bodies.py
```

```bash
python3 studies/constraints.py
```
