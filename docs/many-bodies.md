# Many bodies

With one body, spatial flow is general relativity exactly ([1.4](part1/conclusion.md)). With more than one, it has
to say how the bodies' flows combine, and that is where it could part from GR. This page tests that in the
simulation, in four steps. Each runs the flow model itself: particles, clocks and light, not formulas.

| Question | Result |
| --- | --- |
| [How do the flows combine?](#1-how-the-flows-combine) | Not as vectors: that puts g at the Earth's surface out by 37–74 m/s². By their squares, $|\mathbf u|^2 = \sum 2GM/d$, it is Newton's |
| [Clocks](#2-clocks) | As vectors, a GPS clock would drift ±20 µs a day (5.9 km of range). By squares, none |
| [Moving bodies](#3-moving-bodies) | A moving body must carry its flow with it. If not, g is out by 26–52 m/s² |
| [Beyond Newton](#4-beyond-newton) | By squares, the Sun's potential stretches space round the Earth and Jupiter: ruled out by lunar laser ranging (27σ), and very likely by VLBI past Jupiter |

The simulation's rule for many bodies passes every Newtonian test and fails at the next order, through something new.
Round each body, the other bodies' potential speeds up its inflow. GR has no such effect, and it goes as
$\sqrt{M_1 M_2}$, which no post-Newtonian (PPN) theory can have. So in this form the model is ruled out, but it fails
in a specific way that points to the fix (see [What next](#what-next)).

## 1. How the flows combine

Part 3 of the original adds the bodies' flows as **vectors**: $\mathbf u = \sum \mathbf u_i$, each straight in at
$\sqrt{2GM_i/d_i}$. That is why it says the flow stops between the Earth and the Moon. The simulation instead takes
the **square root of the sum of their squares**, $|\mathbf u|^2 = \sum 2GM_i/d_i$, pointing down the eikonal flow
([Two bodies](two-bodies.md)).

The choice is not free. Space falling at $\mathbf u$ accelerates at $(\mathbf u\cdot\nabla)\mathbf u =
\nabla(u^2/2)$ when the flow has no curl, so the rule for $|\mathbf u|^2$ *is* the law of gravity. Squares give
Newton's g exactly. Vectors add $\nabla(\mathbf u_E\cdot\mathbf u_S)$, a cross term between the Sun's flow at the
Earth (42 km/s) and the Earth's own (11 km/s at its surface).

A particle let go from rest at the Earth's surface, with the Sun 1 AU away (`studies/multi_body_rules.py`):

| Rule | Error in g at the surface | at the Moon's distance |
| --- | --- | --- |
| vectors | 37–74 m/s² (the Earth's own g is 9.8) | 0.08–0.16 m/s² (the Earth's g there is 0.0027) |
| squares | under 10⁻⁶ m/s², the calculation's precision | under 2 × 10⁻⁶ m/s² |

Under vectors a ball dropped on the side facing the Sun is pushed 300 km *up* in 150 s. Others veer up to 800 km
sideways. Under squares they all fall straight down in 145 s, as Newton's do:

<iframe src="../viewer/index.html?run=../runs/multiBodyRules/multiBody_drops.full.json" width="100%" height="560" loading="lazy" title="Balls dropped round the Earth, the Sun to the left"></iframe>

*Balls let go 100 km above the Earth, the Sun 1 AU to the left: flows added as vectors (solid), by squares
(dashed).* [Open full screen](../viewer/index.html?run=../runs/multiBodyRules/multiBody_drops.full.json){ target=_blank }

!!! warning "Correction to Part 3"
    Part 3's argument needs the vector rule, and the vector rule fails Newtonian gravity by a factor of about 10⁸
    against the Sun's tide. Under the simulation's rule there is no point where space stops. At P, between the Earth
    and the Moon, a clock at rest ticks at GR's rate. The flow is 1.6 km/s there, and $\sqrt{1-u^2/c^2}$ is GR's
    $1 - U/c^2$ to first order everywhere on the line. So the "irreconcilable" difference in 3.2 does not arise.
    Even under vectors the flow would not stop at P: it would stop 4,700 km from the Moon, where
    $\sqrt{M_E/d_E} = \sqrt{M_M/d_M}$, not 38,000 km out where g = 0.

!!! tip "Suggestion"
    Replace 3.2–3.3 with this test. The theory's claim becomes: *the speeds of the flows add as squares*, because
    the potentials add, and the flow has no curl. Part 3's question can stay: does a theory with this flow differ
    from GR with more than one body? Section 4 answers it, and the answer is yes.

## 2. Clocks

A clock ticks at $\sqrt{1 - |\mathbf v - \mathbf u|^2/c^2}$. Under vectors the cross term $\mathbf u_E\cdot\mathbf u_S
/c^2$ changes round the Earth, so clocks would run fast at noon and slow at midnight. In `studies/multi_body_clocks.py`
the Sun is at rest 1 AU away, and the model's clock times are converted to GR's static time. Over a day, against GR:

| Clock | Rule | Rate swing | Time swing | As GPS range |
| --- | --- | --- | --- | --- |
| on the equator | vectors | ±5.2 × 10⁻⁹ | ±69 µs | ±21 km |
| GPS orbit | vectors | ±2.6 × 10⁻⁹ | ±20 µs | ±5.9 km |
| either | squares | below 2 × 10⁻¹⁶ (rounding) | 0 | 0 |

GPS keeps its clocks to nanoseconds. Light pulses between a clock at noon and one at dusk show that the swing could
be measured, not just a matter of setting clocks: the dusk clock counts 5.2 × 10⁻⁹ fewer seconds under vectors, and
GR's 4.2 × 10⁻¹³ under squares.

<iframe src="../viewer/index.html?run=../runs/multiBodyClocks/multiBody_clocks.full.json" width="100%" height="480" loading="lazy" title="Clock rates against GR over a day"></iframe>

*Each clock's rate against GR's over a day, in parts in 10⁹.* [Open full
screen](../viewer/index.html?run=../runs/multiBodyClocks/multiBody_clocks.full.json){ target=_blank }

## 3. Moving bodies

Bodies move, and their flows have to move with them. There are two ways (`Body.velocity`, `Calculator.carried`):

- **Taken along**: the flow's pattern moves with the body, but the space far from it stays at rest, so the body
  moves through space.
- **Carried**: the space round the body moves with it, $\mathbf u = \mathbf V + \mathbf u_{\text{body}}$. For one
  body this is only a change of frame, so it is exactly GR.

The Earth alone, moving at its orbital 29.8 km/s (`studies/moving_bodies.py`):

| Flow | Error in g round it | Clock ahead against the one at its side |
| --- | --- | --- |
| taken along | 26–52 m/s² | 3.7 × 10⁻⁹ (7.4 × 10⁻⁹ ahead against behind) |
| carried | 2 × 10⁻⁸ m/s² | 2 × 10⁻¹⁵ |

A flow taken along gives a preferred frame of the crudest kind. It fails Newton before clocks even come into it, since
in the body's frame the moving flow adds $\partial\mathbf u/\partial t = -(\mathbf V\cdot\nabla)\mathbf u$ to space's
fall. So **each body carries its flow**.

With the Sun as well, and only the Earth moving, the carried flow has to fade out away from the Earth.
(`Calculator.carry` gives each body its share of g, or of $g^n$ to fade faster.) With flows added as vectors, g at the
surface is still out by 0.005–0.01 m/s² however sharp the fade. That is the vectors' own cross term,
$\mathbf u_E\cdot(\mathbf u_S(\mathbf x)-\mathbf u_S(\text{Earth}))$, about $u_E u_S/\text{AU}$, and 10⁴ times the
Sun's real tide. The eikonal flow is built for bodies at rest, so carrying it is the open question below.

<iframe src="../viewer/index.html?run=../runs/movingBodies/multiBody_moving.full.json" width="100%" height="560" loading="lazy" title="Balls dropped beside the moving Earth"></iframe>

*Balls let go beside the Earth as it moves up the screen at 29.8 km/s, in the Earth's frame: flow taken along (solid),
carried (dashed).* [Open full screen](../viewer/index.html?run=../runs/movingBodies/multiBody_moving.full.json){ target=_blank }

## 4. Beyond Newton

The square-root rule passes every Newtonian test, so look at the next order. Round a body in another's field, the
other's potential $c_0 = GM'/D$ is in $|\mathbf u|^2$ as well:

$$
|\mathbf u| = \sqrt{\frac{2GM}{r} + 2c_0}
$$

Round the Earth, space falls in at 43.6 km/s at the surface, not 11.2. Within the Earth's region of the eikonal flow
(out to 260,000 km towards the Sun, 520,000 km to the side, and much further away from it), the flow is still straight
in. In the static form of the metric,

$$
ds^2 = -(c^2 - u^2)\,dT^2 + \frac{c^2\,dr^2}{c^2 - u^2} + r^2 d\phi^2
$$

$g_{rr}$ picks up $2c_0/c^2$ as well as GR's $2GM/rc^2$, so radial distances round the body are stretched by
$c_0/c^2$. In GR a uniform potential changes nothing that can be measured locally (the equivalence principle).

In GR's terms this flow is not empty space. With flat slices and no curl, Einstein's equations outside matter need
$(\nabla\cdot\mathbf u)^2 - \partial_i u_j\,\partial_j u_i = 0$ (the Hamiltonian constraint). For one body's
$\sqrt{2GM/r}$ it is 0. Computed from the simulation's flow round the Earth and round Jupiter, it is $4c_0/r^2$ to
0.4%, at 2–30 radii and at every angle (`studies/multi_body_pn.py`).

Two measurements show it (`studies/multi_body_pn.py`):

**Lunar laser ranging.** The test is radar from the Earth's surface to a mirror at the Moon's distance, with the Sun
1 AU away, against the Earth alone. It is measured against the size of the mirror's orbit, which the flow leaves
alone, as do Newton's dynamics. The round trip is worked out along the straight line, and light run in the model
agrees with it to 10⁻¹⁴ s.

| | Flow | GR | Measured |
| --- | --- | --- | --- |
| extra range | 3.44–3.74 m | the Sun's tide, 2.5 × 10⁻⁵ m | (a constant goes into the Earth's GM) |
| its cos D part (D the Moon's angle from the Sun) | 0.111 m | 0 | (2.8 ± 4.1) mm cos D ([Williams, Turyshev & Boggs 2004](https://arxiv.org/abs/gr-qc/0411113)) |
| swing over the year | ±6.2 cm | 0 | |

The range is smaller where the Moon is in the Sun's region (D within about 60° of the Sun), because there the flow
points at the Sun rather than the Earth. That puts a term of 11 cm at the Moon's synodic period into the range, 27
times LLR's uncertainty on exactly that term. The synodic term is how LLR tests the strong equivalence principle (the
Nordtvedt effect).

<iframe src="../viewer/index.html?run=../runs/multiBodyPN/multiBody_lunar.full.json" width="100%" height="440" loading="lazy" title="The extra lunar range by the Moon's angle from the Sun"></iframe>

*The extra lunar range (m) the Sun's potential makes in the flow, by the Moon's angle from the Sun (degrees).*
[Open full screen](../viewer/index.html?run=../runs/multiBodyPN/multiBody_lunar.full.json){ target=_blank }

**Light past Jupiter.** Light is run in the model past Jupiter, with the Sun 5.2 AU away, 10 AU either side. The
bending with both bodies, less the Sun's alone and Jupiter's alone, is 0 in GR to first order in G. The model's own
step and the geodesic stepper (`engine/geodesic.py`) agree to 0.001 µas:

| Impact parameter | Jupiter's bending | Both less each | As a share of Jupiter's |
| --- | --- | --- | --- |
| 1 R_J | 16,266 µas (GR: 16,266) | 408 µas | 2.5% |
| 10 R_J | 1,627 µas | 397 µas | 24% |
| 100 R_J | 163 µas | 312 µas | 190% |
| 1,000 R_J | 16 µas | 77 µas | 470% |

The excess hardly falls with distance, as a stretch of space round Jupiter should; a straight cone would give
$\pi c_0/c^2 = 1229$ µas. VLBI measured Jupiter's bending of 1190 µas at 3.7′ (b ≈ 14 R_J), with positions good to
under 10 µas ([Fomalont & Kopeikin 2003](https://arxiv.org/abs/astro-ph/0302294)). An extra 300–400 µas would almost
certainly have shown, though the real geometry (the ray running on past the Sun to the Earth) needs running to be sure.

!!! info "Not PPN"
    The effect goes as $c_0$ over distance, $G\sqrt{M_S M_J}$ in all, because the flow is the square root of the
    potential. The parametrized post-Newtonian framework builds the metric from potentials linear in each mass
    (β, γ and the preferred-frame parameters), so it cannot describe this: no choice of PPN parameters matches. For
    one body the model is GR (γ = β = 1); carried flows keep the preferred-frame parameters at 0 for one body.

## What next

Each failure points to the same missing piece. Round a body, the flow should be that body's own river, carried along
with it through the space it is falling in. The other bodies' potential should not be in it. In a body's freely
falling frame a uniform $c_0$ is then pure gauge (a uniform flow is flat spacetime), and the stretch disappears.
Clocks still need $|\mathbf u|^2 = 2\sum GM/d$ in the barycentric frame. Both can hold together only if each body
carries its flow (section 3), with the flow round the Earth moving at the Earth's velocity through the Sun's space,
not at rest. So the next model is an eikonal flow for moving bodies:

- each body's region filled by its own zero-energy paths in its own falling frame, carried at its velocity;
- seams where the regions meet;
- test it against LLR's synodic term and Jupiter's bending again.

Moving bodies are not in the eikonal flow yet. That is the open problem, and where the model could still match GR, or
fail more subtly in a way that would be new.

!!! tip "For Part 3"
    A revised Part 3 could say: with more than one body, the flows' speeds must add as squares (or Newtonian gravity
    fails), and the bodies must carry their flows (or there is a preferred frame). Done naively, by squares round
    bodies at rest, the theory departs from GR at the first post-Newtonian order, in a way no PPN theory can, and
    lunar laser ranging and VLBI rule that version out. Whether a moving-body version survives is the open question.
