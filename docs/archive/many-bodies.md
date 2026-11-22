# Many bodies

With one body, spatial flow is general relativity exactly ([1.4](part1/conclusion.md)). With more than one, the
picture has to say how the bodies' flows combine. This page tries the simplest answers – a single flow through flat
space – in the simulation, in five steps. Each runs the flow model itself: particles, clocks and light, not formulas.

| Question | Result |
| --- | --- |
| [How do the flows combine?](#1-how-the-flows-combine) | By their squares, $\lvert\mathbf u\rvert^2 = \sum 2GM/d$: g is Newton's |
| [Clocks](#2-clocks) | Clocks on the Earth and in GPS orbit keep GR's rates |
| [Moving bodies](#3-moving-bodies) | A moving body must carry its flow with it. If not, g is out by 26–52 m/s² |
| [Beyond Newton](#4-beyond-newton) | By squares, the Sun's potential stretches space round the Earth and Jupiter: fails lunar laser ranging (27σ), and very likely VLBI past Jupiter |
| [Carrying the flow](#5-carrying-the-flow) | Each body carrying its own flow fixes the Earth but squeezes space round the Sun: 9.6 mas off its light bending, 1000 × Cassini's limit. Curl doesn't help |

The squares rule passes every Newtonian test and misses at the next order: round each body, the other bodies'
potential speeds up its inflow, and in flat space that stretches the space round it. GR has no such effect – it goes
as $\sqrt{M_1 M_2}$, which no post-Newtonian (PPN) theory can have. The obvious fix, each body carrying its own flow,
works round the Earth but moves the problem to the Sun ([5](#5-carrying-the-flow)). So a single flow through *flat*
space can't be GR with more than one body ([What it takes](#what-it-takes)); [Lapse and curved space](lapse-curved-space.md)
finds the flow that is.

## 1. How the flows combine

The simulation combines the bodies' flows by the **sum of their squares**, $|\mathbf u|^2 = \sum 2GM_i/d_i$, pointing
down the eikonal flow ([The eikonal flow](two-bodies/eikonal.md)).

The choice is not free. Space falling at $\mathbf u$ accelerates at $(\mathbf u\cdot\nabla)\mathbf u =
\nabla(u^2/2)$ when the flow has no curl, so the rule for $|\mathbf u|^2$ *is* the law of gravity. Because the
potentials add, the squares give Newton's g exactly.

A particle let go from rest with the Sun 1 AU away (`studies/multi_body_rules.py`) has Newton's g to under
10⁻⁶ m/s² at the Earth's surface, the calculation's precision, and to under 2 × 10⁻⁶ m/s² at the Moon's distance.
Balls dropped 100 km up all round the Earth fall straight down in 145 s, as Newton's do.

Space doesn't stop anywhere between the Earth and the Moon. At P, where their pulls cancel, the flow is 1.6 km/s, a
clock at rest there ticks at GR's rate, and $\sqrt{1-u^2/c^2}$ is GR's $1 - U/c^2$ to first order everywhere on the
line.

## 2. Clocks

A clock ticks at $\sqrt{1 - |\mathbf v - \mathbf u|^2/c^2}$. With $|\mathbf u|^2 = 2U$, that is GR's
$1 - (U + v^2/2)/c^2$ to first order. In `studies/multi_body_clocks.py` the Sun is at rest 1 AU away, and the model's
clock times are converted to GR's static time. Over a day, a clock on the equator and one in GPS orbit both keep GR's
rate to below 2 × 10⁻¹⁶, the rounding. Light pulses between a clock at noon and one at dusk show the same: the dusk
clock counts GR's 4.2 × 10⁻¹³ fewer seconds.

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
(`Calculator.carry` gives each body its share of g, or of $g^n$ to fade faster.) The eikonal flow is built for bodies
at rest, so carrying it properly is the question of [section 5](#5-carrying-the-flow).

<iframe src="../viewer/index.html?run=../runs/movingBodies/multiBody_moving.full.json" width="100%" height="560" loading="lazy" title="Balls dropped beside the moving Earth"></iframe>

*Balls let go beside the Earth as it moves up the screen at 29.8 km/s, in the Earth's frame: flow taken along (solid),
carried (dashed).* [Open full screen](../../viewer/index.html?run=../runs/movingBodies/multiBody_moving.full.json){ target=_blank }

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
[Open full screen](../../viewer/index.html?run=../runs/multiBodyPN/multiBody_lunar.full.json){ target=_blank }

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

## 5. Carrying the flow

The fix section 4 points to is for each body to carry its own flow. Round a body, the flow should be its own river,
with the other bodies' potential left out of it. This section builds that and tests it. It works round the Earth, but
the same step breaks the flow round the Sun, and allowing curl doesn't escape the trade-off.

**What any such flow needs.** The flow has no curl, $\mathbf u = \nabla\phi$. Space falls at g when $\phi$ keeps
Bernoulli's equation:

$$
\frac{\partial\phi}{\partial t} + \frac{|\mathbf u|^2}{2} = U + f(t)
$$

The same equation also gives clocks GR's first-order rates, moving bodies or not. In GR's static time
$T = t + \phi/c^2$, a clock's rate is $1 - (U + v^2/2)/c^2$ exactly. So Newton and the clocks come free, and only the
choice of space paths is left.

**The flow turning with the bodies** (`engine/turning.py`, Calculator `combine='turning'`). The Sun and the Earth go
round their centre of mass, and in the frame turning with them the flow is steady. Bernoulli's equation then becomes
an eikonal for the flow relative to that frame, $\mathbf w = \mathbf u - \mathbf\Omega\times\mathbf x$:

$$
|\mathbf w|^2 = 2\left(U + \tfrac12\Omega^2\rho^2 + J\right)
$$

Its paths are the restricted three-body problem's, with Jacobi constant J. A seam keeps the metric continuous only if
both sides have the same J, so the whole flow has one. $J = 0$ is section 4's stretch, half as big again. For the
Earth to carry its own flow, J must be minus the Roche potential at the Earth, less the Earth's own term
($J = -1.33\times10^9$ m²/s²).

Run in the model (`studies/turning_eikonal.py`), with the Earth on its orbit:

| Test | Bodies at rest (section 4) | Turning, Earth carries its flow | GR or measured |
| --- | --- | --- | --- |
| Einstein's constraint round the Earth, over $4c_0/r^2$ | 1 | 10⁻⁵ (the Sun's tide) | 0 |
| lunar range, cos D part | 0.111 m | 2 × 10⁻⁸ m | (2.8 ± 4.1) mm |
| g round the moving Earth | Newton's | Newton's, to the tables' 2 × 10⁻⁵ of g | |
| **the Sun's light bending at 2 R☉** | GR's | **9.6 mas less (1.1%)** | Cassini: γ to 2.3 × 10⁻⁵ (0.01 mas) |

The last row is the catch. The Sun's own paths leave it with no angular momentum, so their energy is J, not 0. The
stretch has moved from round the Earth to round the Sun, as a squeeze: Einstein's constraint there is $4J/r^2$, and the
Sun's light loses a cone's worth of bending, $\pi J/c^2 = 9.6$ mas, at every impact parameter. That is 1000 times
what Cassini allows. **One J cannot suit both bodies.** J = 0 suits the Sun and stretches space round the Earth; the
carried J suits the Earth and squeezes it round the Sun.

The Sun's paths also reach only 2/3 AU: nothing let go from the Sun with energy J gets further. Beyond about 1.1 AU,
the only paths with this J are ones swirling in from far away with angular momentum $L = -J/\Omega$. That swirl does
keep Einstein's constraint, which for paths of energy E is $2E/r^2$, so 0 for E = 0. Between 0.63 and 1.1 AU, though,
every possible family has E < 0.

<iframe src="../viewer/index.html?run=../runs/turningEikonal/turning_paths.full.json" width="100%" height="560" loading="lazy" title="Space paths in the frame turning with the Earth"></iframe>

*Space paths out of the Sun (turning back at 2/3 AU) and out of the Earth (curling round past its Hill sphere), in
the frame turning with the Earth, run back in time as the tables are built.*
[Open full screen](../../viewer/index.html?run=../runs/turningEikonal/turning_paths.full.json){ target=_blank }

**In 3D it is worse.** With J below zero, along the axis of the orbit beyond 2/3 AU from the Sun $|\mathbf w|^2$ would
have to be negative, so no flow can exist there. In 3D, J ≥ 0, and the stretch round the Earth is at least
$1.5\,GM_S/(ac^2) = 1.48\times10^{-8}$ (the same as GR's rate difference between Earth and barycentric clocks).

**Flows with curl.** With curl, Bernoulli's constant can differ from streamline to streamline (Crocco's theorem,
$\nabla B = \mathbf w\times\mathbf\omega$), so the Sun's space could have B = 0 and the Earth's B = J. The cost
is set by Einstein's momentum constraint, which for this kind of flow is
$\nabla\times\mathbf\omega = -16\pi G\rho\mathbf w_m/c^2$. Outside matter, vorticity that changes from place to
place is impossible; uniform vorticity is only a turning frame. Anything moving through space also feels
$-\mathbf w\times\mathbf\omega$ (`studies/curl_flows.py`):

| Layer B changes across | Vorticity needed | Matter streaming through it | Push at 1 km/s |
| --- | --- | --- | --- |
| round the Earth (its Hill sphere) | 2.4 × 10⁻⁵ /s | 10²⁶ × the solar wind | 0.024 m/s², 9 × the Earth's pull on the Moon |
| the gap, 0.63–1 AU | 6.3 × 10⁻⁷ /s | 10²³ × the solar wind | 6 × 10⁻⁴ m/s² |

GR's own curl, frame dragging, is of order $GMw_m/(c^2r^2)$: 3 × 10⁻¹² /s round the Earth. That's 10⁷ times too small
to help.

## What it takes

For two or more bodies, a flow through flat space can't be GR at first post-Newtonian order while also keeping clocks
that tick by the flow alone (unit lapse), space falling at g, and one connected flow. Without curl, one Bernoulli
constant must serve every body, and no value suits both the Sun and a planet. With curl, Einstein's constraints forbid
the vorticity outside matter. Each version tried here fails a measurement:

| Version | Fails |
| --- | --- |
| flows taken along by moving bodies | Newton (26–52 m/s²) |
| by squares, bodies at rest | lunar laser ranging (27σ); very likely VLBI past Jupiter |
| turning, the Earth carrying its flow | Cassini and VLBI on the Sun's light bending (1000×) |
| with curl | Einstein's momentum constraint; the Moon's orbit |

What gives way is flat space. [Lapse and curved space](lapse-curved-space.md) keeps the clocks (N = 1) and one flow –
the turning flow with Jacobi constant 0, one potential over the whole plane – and lets space be stretched across the
flow, as Einstein's constraint says it must be. With the flow's first post-Newtonian corrections, which come from
Einstein's equations too, that is GR for the Sun, the Earth, the Moon, light past Jupiter and a binary: a flow view of
GR for many bodies, as Gullstrand–Painlevé's is for one.
