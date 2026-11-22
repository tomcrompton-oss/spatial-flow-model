# What comes from outside

Each step of [the model, step by step](evolution.md) brings something in from outside the flow: Newton's law,
special relativity, Einstein's equations, the post-Newtonian metric, Hadamard's regularization. This page asks which of
them can be derived from the flow of space instead.

The answer: all of them but three. One is local special relativity, the model's premise. One is the bodies' masses,
and with them G. The third is a single law about the flow: Einstein's equation, in a form that is a statement about
falling space. Everything else follows from the flow and those three.

## The ball law

Baez and Bunn ("The meaning of Einstein's equation", *Am. J. Phys.* **73**, 644, 2005) put Einstein's equation as a
statement about small balls of freely falling particles. A ball of test particles, at rest relative to some observer,
starts to shrink at a rate set by the energy and pressure inside it:

$$
\frac{\ddot V}{V}\Big|_{t=0} = -4\pi G\,(\rho + p_x + p_y + p_z),
$$

in that observer's frame. For one observer this is one equation (Raychaudhuri's). Holding it for every observer, moving
at every speed, is all of Einstein's equation.

In the flow picture the law is natural, because free fall is moving with space. A ball carried along with the flow is a
small piece of the flowing space itself, so the law says how falling space converges. A ball moving through the flow
is a cloud of particles crossing it, as light does.

The law isn't "space is conserved". Round one body the flow converges even where there is no mass, since
$\nabla\cdot\mathbf u \propto -r^{-3/2}$. Conserved space would need a flow falling off as $1/r^2$, and that is a
different gravity. The law sets how fast the convergence itself changes, which is the tide.

## What flat space gets right

`studies/ball_law.py` checks exactly (with sympy) the flow model with flat space: $ds^2 = -dt^2 + |d\mathbf x -
\mathbf u\,dt|^2$, clocks keeping the flow's time (N = 1), and $\mathbf u = \nabla\phi$ for an arbitrary $\phi(t,
\mathbf x)$. The observers falling with the flow have $n = \partial_t + \mathbf u\cdot\nabla$.

| Check | Result |
| --- | --- |
| $R_{nn}$, the ball law for balls falling with the flow | exactly $-\nabla\cdot(D\mathbf u/Dt)$, minus the divergence of the flow's acceleration |
| $R_{ni}$, its mixed part (the momentum constraint) | exactly 0 |
| $G_{nn}$, the Hamiltonian constraint | exactly $\tfrac12(K^2 - K_{ij}K_{ij})$, $K_{ij} = \partial_i\partial_j\phi$ |
| one body, $\phi = -2\sqrt{2GMr}$ | every component of $R_{\mu\nu}$ is 0 (to 10⁻¹⁷³ of $GM/r^3$ at three points) |

With Bernoulli's equation, $\partial_t\phi + |\mathbf u|^2/2 = U$, the flow's acceleration is $\nabla U$, so
$R_{nn} = -\nabla^2 U = 4\pi G\rho$. That is the ball law for balls falling with the flow, holding to every order, not
only Newton's. So the flat flow of steps 1.1, 2.1 and 3.1 has no Newton in it: it is the ball law, exactly, for the
observers who move with space.

A ball moving through the flow at velocity w sees $R_{nn} + 2w^iR_{ni} + w^iw^jR_{ij}$. With flat space the first two
terms are already right, so only $w^iw^jR_{ij}$ can be wrong. For one body it isn't: Painlevé–Gullstrand is exact
Schwarzschild. For two bodies it is: the Hamiltonian constraint, $\tfrac12(K^2 - K_{ij}K_{ij}) = 8\pi G\rho$, fails by
13% for the eikonal flow, and by up to 82% ([Einstein's constraints](lapse-curved-space.md#einsteins-constraints-what-space-the-flow-needs)).

This explains the pattern on the [scorecard](scorecard.md). Every flat flow passes Newton and fails at post-Newtonian
order:

- the error a moving ball sees is of order $w^2/c^2$, which is post-Newtonian for bodies;
- light is the fastest ball, $w = c$, so it sees the error at full strength. That is why light past Jupiter failed by
  400 µas while every Newtonian test passed.

Curving space (step 2.2) is what the ball law needs for balls moving through the flow. It isn't a fix brought in from
elsewhere.

## Step by step

| Step | Brought in as | Can it come from the flow? |
| --- | --- | --- |
| 1.1: the flow's speed is the escape velocity | Newton | **Yes.** It is the ball law for balls falling with the flow, with space at rest far away. Exact (above). |
| 1.2: motion through the flow is special relativity | special relativity | **No.** This is the premise: the equivalence principle, the local physics that the flow picture assumes. |
| 1.2: clocks keep the flow's time, N = 1 | the picture | **Yes.** If space's own observers fall freely, their acceleration $\nabla\ln N$ is zero, so N is constant and can be set to 1. It is the premise "moving with the flow is free fall". |
| 2.1: no curl | Newton's g | **Yes, two ways.** A flow defines one time only if its observers have no vorticity (Frobenius's theorem); the [carried flow's seams](lapse-curved-space.md#the-carried-flows-seams-one-time-or-many) showed what goes wrong without one. And free fall keeps vorticity at zero if it starts at zero (Kelvin's theorem), so space at rest far away stays free of it. |
| 3.1: Bernoulli's equation with J = 0 | Hamilton–Jacobi | **Yes.** It is the first integral of free fall for a flow with no curl, and J = 0 is space at rest far away. U isn't an input: it is the flow's head, and its Poisson equation is the ball law. |
| 2.2: curved space | Einstein's Hamiltonian constraint | **Yes.** It is the ball law for balls moving through the flow: the $w^iw^jR_{ij}$ that flat space gets wrong. |
| 3.2: the flow slowed by $(U + u^2/2)/c^2$, and χ | GR's first post-Newtonian metric | **Yes.** χ is the ball law for balls falling with the flow, at first post-Newtonian order (Raychaudhuri's equation, the trace of the evolution equation). The slowing, with 4.2's term, is the momentum constraint: the ball law's mixed part. ([Where the rules come from](lapse-curved-space.md#one-potential-for-the-whole-plane-the-turning-flow-with-j-0).) |
| 3.2: χ's source, the bodies' kinetic and binding energy | GR's ψ | **Yes, from one body's field (checked, below).** The kinetic part, $\tfrac32v^2$, is the body's static field Lorentz-boosted to its velocity. The binding part, $-U_\text{others}$, is its static field set in the others' clocks and rulers. |
| 4.1: Hadamard regularization | post-Newtonian theory | **Yes.** The partie finie is the field averaged over a small sphere round the body. So the rule is premise 4 for an extended body: a body moves with the space it is in, averaged over the space round it. At first post-Newtonian order a spherical body's structure drops out, so this is the real bodies' result. The J = 0 flow's own part averages to about zero round the Earth (`studies/binary_regularized.py`). |
| 4.2: $4\mathbf U_j/c^2$ | the first post-Newtonian vector potential | **Yes, by special relativity (checked, below).** It is a body's static field, Lorentz-boosted to its velocity: 2U from its clocks and 2U from its curved space. Rule 5 isn't a separate rule. |
| 1.3 and 4.3: spin | the river model (Kerr) | **Yes.** At first post-Newtonian order it is the momentum constraint with the bodies' angular momentum as the source: the same part of the ball law as 4U_j. Kerr is a vacuum solution of the whole law. Hamilton's twist is what keeps space flat; once space is curved it isn't needed as a separate rule. |
| the seam rule, and the bodies' offset in J | choices | **Nothing to derive.** They choose how time is sliced and leave the spacetime as it is. (The [eccentric binary](lapse-curved-space.md#off-circles-the-j-0-flow-for-an-eccentric-binary) shows the offset can't keep the seam on the saddle.) |

## What is left

- **Special relativity, locally.** The flow picture assumes it; nothing in the flow gives it.
- **The bodies' masses**, and G.
- **The ball law itself**, for what the bodies' own fields don't give: the nonlinearity between them. It is
  Einstein's equation, so none of this derives GR from the flow without GR's content. What it shows is that GR's content fits in one sentence about the flow, and that Newton, the post-Newtonian rules
  and curved space all follow from it. The flow describes how space moves; a law about what moves it has to come from
  somewhere. Jacobson ("Thermodynamics of spacetime: the Einstein equation of state", *Phys. Rev. Lett.* **75**,
  1260, 1995) derived the law from Raychaudhuri's equation for light rays and horizon thermodynamics, with entropy
  proportional to area. That brings thermodynamics in from outside instead.

## A body's own field, moving and among others

`studies/field_from_bodies.py` checks, exactly, where the rules' moving-body terms come from. The rules take three
things from GR's first post-Newtonian metric in harmonic coordinates, before the J = 0 slicing: the space
$(1 + 2U)\,\delta$, the vector potential $g_{0i} = -4U_i$, and χ's source
$\psi = \sum_b (m_b/r_b)(\tfrac32 v_b^2 - U_\text{others}) + \tfrac12\partial_t^2\sum_b m_br_b$. Each is rebuilt from
one body's static field, $g_{00} = -1 + 2m/R - 2m^2/R^2$, $g_{ij} = (1 + 2m/R)\,\delta$, which is Part 1's one-body
flow in these coordinates.

| Built from one body's static field | Against GR's first post-Newtonian metric | Result |
| --- | --- | --- |
| **Boosted** to velocity v (special relativity) | one body moving at v: $g_{00}$ with ψ's $\tfrac32 v^2$ and $\tfrac12\partial_t^2(mr)$, $g_{0i} = -4mv_i/r$, $g_{ij} = (1 + 2U)\delta$ | exactly equal, every component, to first post-Newtonian order |
| **Set in another body's clocks and rulers** ($dt_\text{local} = \sqrt{-g_{00}}\,dt$, $dx_\text{local} = \sqrt{1 + 2U_1}\,dx$) | two bodies at rest, near body 2: $g_{00}$ with ψ's $-U_1$, and $g_{ij}$ | exactly equal. The $m_2U_1/r_2$ term is −6: −4 from $-2U^2$, −2 from ψ |

The check can fail: with $-2U_i$ in place of $-4U_i$, and $v^2$ in place of $\tfrac32 v^2$, the boosted field
misses by 0.53 in $g_{0x}$ and 0.075 in $g_{00}$ at the test points.

So:

- **Rule 5 is a moving body's field.** $4\mathbf U_j$ is what Lorentz-boosting a body's static field puts into
  $g_{0i}$: 2U from its clocks and 2U from its curved space. Boosted with flat space (Painlevé–Gullstrand's) it gets
  only the clocks' 2U. The J = 0 slicing carries $-4U_i$ into the flow unchanged, as $+4\mathbf U_j$.
- **χ's source comes from the bodies' own fields.** Its kinetic part is the same boost. Its binding part is a body's
  field set in the clocks and rulers of the others' field where the body is: its clocks slowed by the others'
  potential, which in the flow picture is its speed through the others' flowing space (Part 1's clock rule), and its
  rulers stretched by step 2.2's space. Nothing about the bodies is needed beyond their masses and velocities.
- **What stays for the ball law** is what makes the fields more than their sum: the $-2U^2$ in $g_{00}$, which for
  bodies at rest says that their clock rates multiply. Near a body the check above fixes its cross term. Between the
  bodies it comes from the vacuum ball law for observers at rest.

## Run it

```bash
python3 studies/ball_law.py
```

```bash
python3 studies/field_from_bodies.py
```
