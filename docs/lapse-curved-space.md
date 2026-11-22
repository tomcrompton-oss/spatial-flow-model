# Lapse and curved space

The flow model is a special case of the way general relativity writes any spacetime, its 3+1 form:

$$ds^2 = -N^2c^2\,dt^2 + \gamma_{ij}\,(dx^i - u^i dt)(dx^j - u^j dt)$$

- **N, the lapse**: how fast the clocks of observers moving with the flow tick, per unit of t.
- **u, the flow**: those observers' velocity through the coordinates (GR's shift, turned round).
- **γ, the metric of space**: lengths within each moment.

The flow model is N = 1 and γ flat. Those two choices are the hypothesis of Part 1. With N = 1, observers moving with
space are in free fall, and every clock's slowing is its speed through space. With flat γ, space is Euclidean and all
of gravity is motion. For one body both hold exactly (Painlevé). With two or more, every rule tried has failed
somewhere, so this page relaxes them, one or both, to see what that does.

## What was built

[engine/metric.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/engine/metric.py):

- **A spacetime** gives N − 1, u and γ − δ at each place and time. Each is kept as its difference from the flat,
  unflowing value, so nothing is lost in rounding against c².
- **One mover for all of them** (`MetricCalculator`) takes particles and light along the spacetime's paths, by
  Hamilton's equations on the momentum $p_i$:

  $$H = N c\sqrt{c^2 + |p|^2} + \mathbf u\cdot\mathbf p,\qquad \frac{d\mathbf x}{dt} = \frac{\partial H}{\partial \mathbf p},
  \qquad \frac{d\mathbf p}{dt} = -\frac{\partial H}{\partial \mathbf x},\qquad \frac{d\tau}{dt} = \frac{Nc}{\sqrt{c^2 + |p|^2}}$$

  ($|p|^2 = \gamma^{ij}p_ip_j$; for light $H = Nc|p| + \mathbf u\cdot\mathbf p$). It is the flow model's momentum step
  with N and γ added. H is the energy, kept when the spacetime is steady, and seams are crossed keeping it.
- **The lapse and curved space on every flow model** (`FlowSpacetime`): any flow calculator – one body, vectors, along
  g, eikonal, turning, a wave – with a lapse and a spatial metric of its own, or set by two shares of Newton's
  potential Φ = ΣGM/d:
    - λ, the share of gravity in the clocks: $N^2 = 1 - 2\lambda\Phi/c^2 + \dots$, the flow scaled by $\sqrt{1 - \lambda}$,
      so that $-g_{tt} = N^2c^2 - |\mathbf u|^2$ is unchanged and Newton's g is kept;
    - κ, curved space: $\gamma = (1 + 2\kappa\Phi/c^2)\,\delta$, as GR's harmonic coordinates have it at κ = 1.
- **Two spacetimes to check it against**: one body in isotropic coordinates (no flow at all, the lapse and curved space
  carrying everything), and GR's first post-Newtonian metric of bodies on given paths, which is the reference the
  multi-body models can now be measured against within the same engine.

## Checks of the engine

[studies/metric_checks.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/metric_checks.py):

| Check | Result |
| --- | --- |
| The one-body flow through the new engine against the flow model's momentum step, 2 orbits from 200 to 600 Schwarzschild radii | end points 2 × 10⁻¹⁰ of the distance apart |
| The same spacetime in isotropic coordinates: the orbit with the same energy and angular momentum | precession within 1.7 × 10⁻⁶ of exact GR; E and L kept to 3 × 10⁻⁸ |
| … light passing at 20, 300 and 10,000 Schwarzschild radii | bending within 1–2 × 10⁻⁸ of exact GR |
| … a fall from rest far away | proper time within 4 × 10⁻⁷ of the exact fall time |
| GR's first post-Newtonian metric, the Sun and the Earth going round each other: a Moon-like orbit for 5 days | ends 1 mm from EIH's equations of motion, which end 35 m from Newton's: 3 × 10⁻⁵ of the relativistic part |

The first and second rows are the same spacetime in two sets of coordinates – one all flow, one all lapse and curved
space – and the engine gives the same physics in both.

## One body: how much of gravity can go in the clocks?

The one-body flow with λ of gravity moved into the lapse and space curved by κ, on the close orbit and light at
300 Schwarzschild radii:

| λ | κ | Precession / GR's | Bending / GR's |
| --- | --- | --- | --- |
| 0 | 0 | 1.0000 | 1.0000 |
| 1 | 0 | 0.667 | 0.500 |
| 0.5 | 0 | 0.834 | 0.750 |
| 0 | 1 | 2.35 | 1.51 |
| 0.25 | 0.25 | 0.9996 | 1.0003 |
| 0.5 | 0.5 | 0.9986 | 1.0002 |
| 0.75 | 0.75 | 0.9968 | 0.9998 |
| 1 | 1 | 0.9945 | 0.9990 |

(Those with κ = λ have the lapse's $\Phi^2$ term below; the 0.1–0.5% left grows with λ, as second post-Newtonian
order at 200 Schwarzschild radii should.)

These are GR's post-Newtonian (PPN) parameters at work. A potential in the clocks alone (λ = 1, κ = 0) is PPN γ = 0,
β = 0, and PPN says light then bends half as much and orbits precess two thirds as much: so they do. Curving space to
match (κ = λ) gives the light back; the orbits also need the lapse's $\Phi^2$ term, PPN's β. Written out, $g_{tt}$'s
$\Phi^2$ coefficient has to be $2\lambda$, which with part of gravity still in the flow makes the lapse
$N^2 = 1 - 2\lambda\Phi/c^2 + 2(\lambda + 2\kappa(1 - \lambda))\Phi^2/c^4$. With that, **κ = λ is GR at first order
for any λ**: a one-parameter family, from the flow model (λ = 0, all of gravity in the flow) to conventional
post-Newtonian GR (λ = 1, none). Curved space alone (λ = 0, κ = 1) bends light 1.5 times too much.

## Two bodies at rest

The two tests that ruled out the eikonal flow with the bodies at rest ([Many bodies](many-bodies.md)), now along the
family ([studies/lapse_two_bodies.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/lapse_two_bodies.py)):

| Model | Lunar range, cos D term (radar to the Moon's distance, the Sun 1 AU away) | Light past Jupiter, both less each alone (1 / 10 / 100 Jupiter radii) |
| --- | --- | --- |
| Eikonal flow, λ = 0 (the flow model) | −0.111 m | +408 / +397 / +312 µas |
| Eikonal flow, λ = κ = 0.5 | −0.051 m | +204 / +198 / +156 µas |
| Eikonal flow, λ = κ = 1 | +0.0096 m | +0.25 / −0.01 / −0.08 µas |
| GR's first post-Newtonian metric | +0.0096 m | +0.25 / −0.01 / −0.08 µas |
| Measured | lunar laser ranging: (2.8 ± 4.1) mm | VLBI: positions to under 10 µas |

(GR's own +9.6 mm is the Sun's potential across a mirror held at a fixed coordinate distance; what the test measures is
each model's difference from it.)

Both failures fall exactly as 1 − λ: they are all in the share of gravity the flow carries. To pass, the flow would
have to carry under about 3% of gravity. At λ = 1 there is no flow left, every flow rule becomes the same spacetime,
and it is GR's first post-Newtonian metric for bodies at rest.

## Moving bodies along the family

With the bodies moving, λ also brings in λ of GR's moving-body terms – its vector potential $4U_j/c^2$ in the flow and
the velocity, acceleration and cross terms of its lapse – so that λ = κ = 1 is GR's first post-Newtonian metric of the
moving bodies exactly. The turning flow (the Sun and the Earth going round each other, each carrying its flow) failed
on light passing the Sun, where its single Jacobi constant squeezes the Sun's space
([studies/lapse_moving.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/lapse_moving.py);
each model's bending less its own with the Sun alone, so the flow's part of light's direction at the ends drops out):

| Model | Bending past the Sun, less GR's (2 / 10 / 50 solar radii) |
| --- | --- |
| Turning flow, λ = 0 | −9.60 / −9.59 / −9.25 mas |
| Turning flow, λ = κ = 0.5 | −4.80 / −4.80 / −4.62 mas |
| Turning flow, λ = κ = 1 | 0.0000 |
| Cassini | 0.02 mas at 2 solar radii |

The same 1 − λ. (Radar to a mirror held at a fixed distance in the turning frame is not a fair test across the family:
in GR's coordinates such a mirror is Lorentz-contracted by the Earth's 30 km/s, a 0.93 m cos 2D term, where the
turning flow carries the Earth's space with it. Lunar ranging with moving bodies needs the Moon's own orbit.)

## The clocks left alone, space curved across the flow

The one version of curved space that keeps Part 1's mechanism – N = 1, so every clock is slowed only by its speed
through space – can be derived rather than guessed. Take GR's static metric of bodies at rest, and slice it by the
proper time of observers falling from rest far away, $T = t + S(\mathbf x)/c^2$. To first post-Newtonian order this
gives

$$ds^2 = -c^2dT^2 + \gamma_{ij}(dx^i - u^i dT)(dx^j - u^j dT),\qquad
\gamma = \Big(1 + \frac{2\Phi}{c^2}\Big)\delta - \frac{2\Phi}{c^2}\,\hat{\mathbf n}\hat{\mathbf n},\qquad
|\mathbf u|^2 = 2\Phi\Big(1 - \frac{\Phi}{c^2}\Big)$$

with $\hat{\mathbf n}$ along the flow: the lapse exactly 1, the flow the eikonal flow (the paths of things falling
from rest far away), slowed by $\sqrt{1 - \Phi/c^2}$ (GR's β), and space stretched across the flow by $2\Phi/c^2$
but not along it. For one body that is flat space in other coordinates – the flow model itself, relabelled – and it
checks so: precession 0.9951 of GR's and bending 0.9997 at 200 and 300 Schwarzschild radii (without the slowing the
precession is 4/3). With two bodies it is not flat: the stretch across the flow is where the bodies' cross terms go.

| Model | Lunar range, cos D | Light past Jupiter, both less each alone (1 / 10 / 100 Jupiter radii) |
| --- | --- | --- |
| Eikonal flow, flat space (the flow model) | −0.111 m | +408 / +397 / +312 µas |
| **Eikonal flow, N = 1, space curved across it** | **+0.0096 m** | **+0.35 / −0.04 / −0.09 µas** |
| GR's first post-Newtonian metric | +0.0096 m | +0.25 / −0.01 / −0.08 µas |

With the bodies at rest it is GR: both tests that ruled out the eikonal flow pass, and nothing has been put in the
clocks. Space moves as the eikonal flow says, and is curved across that motion by the potential.

## Space decided by the flow

The eikonal flow is free fall from rest far away, so $|\mathbf u|^2 = 2\Phi$, and the curved space above can be
written with the flow alone:

$$\gamma = \delta + \frac{|\mathbf u|^2\,\delta - \mathbf u\,\mathbf u}{c^2}$$

Space is stretched across its own motion by $u^2/c^2$: the flow's speed says how much, its direction which way, and
nothing else goes in (`FlowSpacetime(..., transverse='flow')`, the flow slowed by $\sqrt{1 - u^2/2c^2}$). For the
eikonal flow this is the same space. For any other flow it is a different one, so it can be tried on all of them:

| Model | Lunar range, cos D | Light past Jupiter, both less each alone (1 / 10 / 100 R_J) | Light past the Sun, less the Sun alone (2 / 10 / 50 R_sun) |
| --- | --- | --- | --- |
| Vectors, flat | +1.084 m | −6418 / −1888 / −440 µas | |
| Vectors, space from u | +1.087 m | −12941 / −3885 / −1003 µas | |
| Along g, flat | −0.587 m | +759 / +1032 / −8 µas | |
| **Along g, space from u** | **+0.0096 m** | −1129 / −788 / −1072 µas | |
| **Eikonal, space from u** | **+0.0096 m** | **+0.35 / −0.04 / −0.09 µas** | |
| Turning, flat | | | −9.60 / −9.59 / −9.25 mas |
| Turning, space curved by 2Φ/c² | | | −9.60 / −9.59 / −9.25 mas |
| **Turning, space from u** | | | **+0.0012 / +0.0019 / +0.014 mas** |
| GR's first post-Newtonian metric | +0.0096 m | +0.25 / −0.01 / −0.08 µas | 0 |
| Measured | (2.8 ± 4.1) mm | under 10 µas | Cassini: 0.02 mas at 2 R_sun |

(The Sun results are the same at half and double the step.)

What light sees shows why. With this space, light's round trips are set by
$\gamma + \mathbf u\mathbf u/c^2 = (1 + u^2/c^2)\,\delta$ to first order: space looks the same in every direction,
and only the flow's speed counts, not its direction. Its paths also feel the flow's curl, which a flow with none
(a gradient) can't give.

- **Round trips need only $|\mathbf u|^2 = 2\Phi$.** Along g has that speed, and its lunar range is GR's exactly,
  wherever the flow points. The vectors' flow doesn't have it, so it fails.
- **Bending also needs no curl.** Along g's flow has curl, and its light past Jupiter is off by about 1000 µas. A flow
  with $|\mathbf u|^2 = 2\Phi$ and no curl is the gradient of an S with $|\nabla S|^2 = 2\Phi$: the eikonal
  equation. So with the bodies at rest, the eikonal flow is the only flow this space makes into GR.
- **Light doesn't mind a constant in $u^2$.** The turning flow's one Jacobi constant makes $|\mathbf u|^2 = 2\Phi$
  less a constant across the Sun's region ($3 \times 10^{-8}c^2$, as large as the Sun's own potential 0.3 AU out).
  In flat space that bent light by 9.6 mas. In this space it only changes the scale of the light-speed factor
  $1 + u^2/c^2$ evenly, which bends nothing. What's left, 0.001 mas at 2 solar radii, is under Cassini's limit.
  Space curved by 2Φ/c² instead of by $u^2$ doesn't take up the constant, and leaves all 9.6 mas.

So with space decided by the flow, the turning flow – the moving-body model – passes the test that ruled it out, with
N = 1 and no potential put in anywhere.

### Which frame's u

Round the Earth the turning flow is the Earth's own river carried at the Earth's 30 km/s. Space built from that u
picks up the 30 km/s: a stretch $V^2/c^2$ across the Earth's motion, and a cross term $2\mathbf V\cdot\mathbf u/c^2$
that couples the Moon's motion to the Earth's. GR has nothing like it, and it depends on the frame the flow is
measured in, where flat flowing space doesn't (adding a uniform V to the flow is only a change of coordinates). Built
instead from the flow relative to the body whose flow it is, $\mathbf u - \mathbf V_{\rm body}$
(`transverse='source'`), it is the same in every frame, and is the same as before wherever the bodies are slow: past
the Sun, which moves at 9 cm/s, it gives the same +0.0012 mas.

### The Moon's own orbit and de Sitter

[studies/lapse_moon.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/lapse_moon.py), as
[studies/de_sitter.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/de_sitter.py) does for
the split model: the Moon (eccentricity 0.12) round the Earth for 90 days, the Sun and the Earth going round each
other, run at 60 and 30 s steps and taken to zero step; taken to GR's harmonic coordinates (GR's time at the Moon is
the flow's T plus $\int\mathbf u\cdot d\mathbf x/c^2$ from the Earth); then GR's Moon (EIH, the Earth falling freely
on its circle) fitted to it, with its start, k (GR's track turned by −k times the de Sitter rate, 19.2 mas a year: 0
has GR's precession, 1 none) and the coordinates' stretch along and across the Earth's motion free:

| Model | k | rms left by the fit |
| --- | --- | --- |
| GR's first post-Newtonian metric, through the same engine (the floor) | +0.03 | 0.033 m |
| Turning flow, flat space | −17 | 15.6 m |
| Turning flow, space from u (the lab's) | −188 | 135 m |
| **Turning flow, space from u relative to its body** | −17 | **15.6 m** |
| Turning flow, flat space, c × 1000 (Newton's) | | 23 m |
| Lunar laser ranging | | about 0.01 m |

- **Space from the lab's u fails** by 135 m: the cross term with the Earth's 30 km/s. Taken relative to the Earth, the
  curved space changes the Moon's orbit by under 3 m and the fit not at all.
- **The turning flow fails the Moon's orbit on its own**, by 15.6 m, and by 23 m with c a thousand times larger: its
  failure is Newton's, not relativity's. The flow round the Earth carries the Sun's tide only approximately (the flow
  against g, [Two checks](two-bodies/checks.md): off by up to 10⁻⁵ of the pulls near the bodies), and the Moon's orbit
  sums that over three months. With metres left over, k – a 0.2 m effect – can't be read.
- **Nordtvedt and the binary pulsars can't be run on it.** Both need the bodies to move by the model's own field (a
  self-gravitating pair falling towards the Sun; an eccentric binary of comparable masses), and the turning flow puts
  its bodies on fixed circles at one angular speed. (A circular binary can be worked out: see
  [its bodies](#one-potential-for-the-whole-plane-the-turning-flow-with-j-0), for the J = 0 flow.)

(A first fit held GR's Earth at 1 AU, off its free-fall circle by GM/c² = 1.5 km, and the Moon drifting from it
left 200 m in every model; the GR row, whose metric holds the Earth at 1 AU, is fitted that way too.)

**Relativity alone.** To see past the Newtonian error, each model is also run with c a thousand times larger, and
what the fit gets is Newton's Moon (EIH at c × 1000) plus the model's run at c less its run at c × 1000: its
relativistic part, its Newtonian errors taken out (`lapse_moon.py 90 differenced`):

| Model | k | rms left by the fit |
| --- | --- | --- |
| GR's metric, through the same engine (the floor) | +0.02 | 0.035 m |
| Turning flow, flat space | +0.48 | 0.26 m |
| Turning flow, space from u relative to its body | +0.49 | 0.25 m |
| Carried flow (below), flat space | +0.48 | 0.26 m |
| Carried flow, space from u relative to its body | +0.48 | 0.26 m |

Every moving-body flow has half of GR's de Sitter precession (k = 0.48; lunar laser ranging measures it to 0.6%) and
leaves a quarter of a metre that GR doesn't. Curving space across the flow relative to its body changes neither: round
the Earth that space is the Earth's own, and the Sun's part of it – which in GR is half of de Sitter's precession, the
curvature of the Sun's space carried round by the Earth – isn't there.

## The carried flow: bodies that move by it

[engine/carried.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/engine/carried.py) is a flow for
any number of bodies moving any way:

- **Regions:** a place belongs to the body whose GM/d³ is largest there – where its own pull beats the others' tides
  (round the Earth, out to 2.2 × 10⁹ m, past its Hill sphere; between equal masses, the nearer one).
- **The flow in a region:** the body's river carried at the body's velocity, plus the others' tide carried in along the
  river, so that space falls at g: $\mathbf u = \mathbf V_k + \mathbf s_k + \nabla\sigma$, with
  $\mathbf s_k\cdot\nabla\sigma = \Phi_T$ (the others' potential less its value and slope at the body). It has no curl
  and no Jacobi constant. To first order in the tide only, so space round the Earth at the Moon's distance falls at g
  to 4% of the Sun's tide.
- **The bodies:** each moves as a test particle in the carried flow of the others, its own left out, the flows
  carried at the bodies' velocities over the step and accelerating only by the pull of the bodies in that spacetime (a
  flow carried by a body's whole acceleration would make the body left out feel its own pull on the others). For two
  bodies, each moves in the other's river carried with it: Schwarzschild in a frame moving with that body, so Newton
  exactly.

[studies/carried_bodies.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/carried_bodies.py),
[studies/lapse_moving.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/lapse_moving.py),
[studies/lapse_two_bodies.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/lapse_two_bodies.py):

| Test | Carried, flat space | Carried, space from u relative to its body | GR |
| --- | --- | --- | --- |
| Light past the Sun, the Sun and the Earth moving (2 solar radii) | 0.0000 mas | 0.0000 mas | 0 |
| The Moon's own orbit, relativity alone (above) | k = 0.48, 0.26 m | k = 0.48, 0.26 m | k = 0 |
| Binary periastron advance / GR's, equal masses | 1.166 | 1.333 | 1 |
| … mass ratio 0.1 | 1.055 | 1.110 | 1 |
| … mass ratio 0.01 | 1.007 | 1.013 | 1 |
| Binary's centre of mass (mass ratio 0.1) | accelerates at 0.17 m/s² | 0.18 m/s² | doesn't |
| Nordtvedt η (a pair falling towards the Sun, held still) | −0.77 | −1.53 | 0 (lunar laser ranging: 10⁻⁴) |

- **Light passes** with the bodies moving, even in flat space: with no Jacobi constant there is nothing to squeeze the
  Sun's region.
- **The bodies' own motion fails** as the split model's did ([Each body separately](two-bodies/split.md)): the binary's
  advance is too large by an amount that grows with the lighter body's mass (right in the test-body limit), its centre
  of mass accelerates by itself, and Nordtvedt's η is of order 1. The reason is the same: each body moves in the
  others' fields alone, and nothing has a body's own field act on the others'. Curving space across the flow doubles
  each error.
- **Bodies held at rest don't fit it.** The carried flow has each body's region falling with the body, at the
  others' pull there; a body held still isn't falling, so its region loses the others' uniform pull. On the two
  bodies-at-rest tests above it gives a lunar cos D term of exactly 0 (the Sun is only a tide round the Earth; GR's
  +9.6 mm is the Sun's potential across the fixed mirror) and light past a Jupiter held still 238 µas off (most of
  it the Sun's uniform pull, missing in Jupiter's region). The Jupiter test needs Jupiter on its orbit, and there it
  fails for a different reason: [the regions' times don't meet at the seams](#the-carried-flows-seams-one-time-or-many).
- **A close pair seen from far off** isn't one of the pair's rivers with the other's tide: 1000 times their separation
  away, that tide's expansion is no flow at all. So in the Nordtvedt test the Sun is held still. A hierarchy of
  regions (the pair as one body from far off) would be needed for systems like that.

## Einstein's constraints: what space the flow needs

GR's 3+1 form has field equations that space and its flow must meet at each moment, the constraints. With the lapse
N = 1 and space $\gamma = \delta + h/c^2$, to the first order they come in
([studies/constraints.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/constraints.py)):

$$\tilde R + (\nabla\cdot\mathbf u)^2 - \tilde K_{ij}\tilde K_{ij} = 16\pi G\rho,\qquad
\partial_j\tilde K_{ij} - \partial_i\nabla\cdot\mathbf u = 0,\qquad
\tilde R = \partial_i\partial_j h_{ij} - \nabla^2 h_{kk},\quad \tilde K_{ij} = \tfrac12(\partial_iu_j + \partial_ju_i)$$

For any flow with no curl, the curvature of $h = -\mathbf u\mathbf u$ is exactly $-[(\nabla\cdot\mathbf u)^2 -
\tilde K_{ij}\tilde K_{ij}]$: it cancels the flow's own term, whatever the flow. So

$$\gamma = \delta + \frac{2\Phi\,\delta - \mathbf u\,\mathbf u}{c^2}$$

– space stretched by Newton's potential and contracted along the flow by $u^2/c^2$ – meets the Hamiltonian constraint
for every such flow, the rest being Poisson's equation for Φ; and the momentum constraint is met by any flow with no
curl. It is GR's space sliced by free fall. Space from u, $|\mathbf u|^2\delta - \mathbf u\mathbf u$, misses it by
$-2\nabla^2(|\mathbf u|^2 - 2\Phi)$: nothing for the eikonal flow, where $|\mathbf u|^2 = 2\Phi$. Measured, in 3D,
as a fraction of the flow's own term, at points round 1 and 0.3 solar masses:

| Flow | Flat space | Space from u (its body's) | $2\Phi\delta - \mathbf u\mathbf u$ |
| --- | --- | --- | --- |
| One body | 10⁻¹² | 10⁻¹⁰ | 10⁻¹⁰ |
| Vectors | 2% (up to 54%) | 57% | 10⁻¹⁰ |
| Along g (it has curl) | 7% | 6% | 6%; the momentum constraint 2% |
| Eikonal, at rest | 13% (up to 82%) | 10⁻¹⁰ | 10⁻¹⁰ |
| Carried, at rest or moving | 0.5% (up to 34%) | 4 × 10⁻⁵ (up to 12%) | 10⁻¹⁰ |

So the constraints settle the space once the flow is given: they don't choose the flow (even the vectors' flow meets
them with this space); Newton's "space falls at g" does that. Every flat-space version breaks them with two bodies,
which is why every flat rule failed somewhere.

**But space alone isn't enough.** Given the carried flow with this space (`transverse='gr'`), light past the Sun still
passes, but the Moon is worse (k = −0.29 with 1.77 m left, Newton's error taken out), the binary's advance comes out
−0.25 of GR's for equal masses, and Nordtvedt's η +589. Taking GR's first post-Newtonian metric to a free-fall slicing,
$t = T + \phi/c^2 + \chi/c^4$, shows why: this space comes with first-order corrections to the flow itself,

$$\mathbf u = \nabla\phi\Big[1 + \frac{v^2/2 - 3\Phi}{c^2}\Big] + \frac{\nabla\chi + 4\mathbf U}{c^2},\qquad
\frac{D\chi}{DT} = Q,\qquad \mathbf U = \sum\frac{GM\mathbf v}{d}$$

(v the flow's speed in the lab; Q a combination of Φ, v², $\mathbf u\cdot\mathbf U$ and GR's ψ), keeping N = 1 – for
one body at rest they come to the $\sqrt{1 - \Phi/c^2}$ already used. The space and the flow's corrections only work
together: the space with the flow uncorrected is half of GR's metric.

## Checking the Moon test with GR in a moving time

The moving-body flows' Moon results – half of de Sitter, 0.26 m left – come from runs whose flow is 30 km/s (the
Earth's velocity is in it), and from a mapping of their time to GR's. Two versions of GR in such a time check both.

**GR transformed exactly** (`engine/metric.py` `SlicedPN`): GR's first post-Newtonian metric taken to
$t = T + \phi/c^2$, with $\phi = \mathbf V\cdot\mathbf d - 2\sqrt{2GMr}$, the Earth's river carried at its velocity.
Nothing is assumed of φ: the metric is transformed and put back in the 3+1 form, each part kept as its offset from
flat so that nothing rounds against $c^2$. The flow is then the Earth's river at 30 km/s, and the rest of Newton's
gravity is in the lapse (the Earth's clock runs slow by $1.5\,GM_\odot/(\mathrm{AU}\,c^2)$ against harmonic
time). It fits as GR does: k = +0.017, 0.027 m (GR's own +0.022, 0.035 m). So the engine and the mapping are right
with a flow the models' size.

**GR in the carried flow's free-fall time** (`engine/carried.py` `FreeFallPN`): the carried flow as GR's Newtonian
flow, with the space $2\Phi\delta - \mathbf u\mathbf u$ and the 1PN lapse that slicing has. Two things had to be
right for it to be GR:

- GR's potential must be taken where the bodies are at the point's own harmonic time, $T + \phi/c^2$, not at T.
  Near the Earth these differ by $\mathbf V\cdot\mathbf d/c^2$, which moves the Earth's field by a 1PN amount: left
  out, the Moon is 1.94 m off.
- The flow must meet Newton's equation exactly, so that there is a φ at all. The carried flow's first-order tide
  misses it by 4% of the Sun's tide at the Moon (it leaves out the tide's change while space falls in, and its
  square). Differencing takes that out at Newton's order but not its product with the 1PN terms: it leaves 0.71 m and
  moves k by 0.3.

The tide's change is a transport along the river: $\mathbf s\cdot\nabla\sigma + \partial_T\sigma = \Phi_T$ is
solved exactly by taking the tide at each radius where the falling space will be when it passes it,

$$\sigma(\mathbf d, T) = -\int_0^r \frac{\Phi_T\big(r'\hat n,\ T + f(r) - f(r')\big)}{s(r')}\,dr',\qquad
f(r) = \frac{2}{3}\frac{r^{3/2}}{\sqrt{2GM}}$$

(f the time to fall to the body), with the square added from the first order's gradient (`tides='transported'`). The
flow then meets Newton's equation to 0.016% of the tide at the Moon's distance (1.4% at 10⁹ m, near the edge of the
Earth's region). The differenced Moon test, 90 days:

| Model | k | rms left |
| --- | --- | --- |
| GR (the floor) | +0.022 | 0.035 m |
| GR transformed exactly to the carried river's time | +0.017 | 0.027 m |
| GR in free-fall time, first-order tide | +0.28 | 0.71 m |
| GR in free-fall time, transported tide | **+0.010** | **0.018 m** |
| Carried, flat, transported tide | +0.49 | 0.25 m |
| Carried, space from u relative to its body, transported tide | +0.49 | 0.27 m |

So the check is GR, and the carried flow's result stands: with the tide right, it still has half of de Sitter's
precession and leaves 0.26 m. That is the flow's own first post-Newtonian behaviour, not its Newtonian error.

The binaries are a separate matter. GR in free-fall time, run as the carried bodies are (each body a test particle in
the others' spacetime), gives 0.83, 0.945 and 0.994 of GR's periastron advance for mass ratios 1, 0.1 and 0.01, and
the centre of mass accelerates when the masses differ: GR's two-body equations have terms in each body's own mass,
which a body moved only by the others' field never feels.

## The carried flow's seams: one time or many

Light past Jupiter tests what happens where two regions meet. Two things came out of it.

**An engine fix.** Crossing a seam, light keeps its momentum along the seam and its energy, and its momentum across
the seam changes. The engine took "across" to be the direction of the flow's jump. That holds for the flows whose
seams are where the two sides' speeds are equal, but not for the carried flow, whose seam is where the pulls are
equal: there the Sun's river points at the Sun, not across the seam. With the seam's own normal (`seamNormal`),
light past Jupiter held still goes from 38,000 µas of cross term to 238. Bodies on their orbits don't cross seams, so
the Moon and binary results above are unchanged.

**A flaw in the model.** Each region's flow is the gradient of its own potential, $\mathbf u = \nabla\phi_k$, and
that potential sets the region's time (its free-fall time, $T + \phi_k/c^2$). Nothing makes the potentials agree
where two regions meet, so the time jumps at the seam by $\Delta\phi/c^2$. Light going into a region and out again
picks up a delay that varies across the beam, and is turned by it, to first order in $u/c$:

$$\delta\theta \approx \frac{1}{c}\,\frac{\partial}{\partial b}\Big[\Delta\phi(\text{in}) - \Delta\phi(\text{out})\Big]$$

For a jump $\Delta\mathbf U$ that is the same all over the seam, $\Delta\phi = \Delta\mathbf U\cdot\mathbf x$, and
the turn is $2\,\Delta U_\parallel\, b/(c\,y)$, with $\Delta U_\parallel$ the jump's part along the ray and y half
the ray's chord through the region. A jump across the ray cancels going in and out; one along it doesn't. A toy
model of a circular seam gives exactly this: 17″ for a 13 km/s jump along the ray.

| Light past Jupiter, the Sun 5.2 AU away: cross term (µas) | 1 R_J | 10 R_J | 100 R_J |
| --- | --- | --- | --- |
| GR, Jupiter held still | +0.25 | −0.01 | −0.08 |
| GR, Jupiter on its orbit | +0.34 | −0.05 | −0.11 |
| Carried, flat, Jupiter held still | −1,224 | −238 | −349 |
| Carried, flat, Jupiter on its orbit | +1,757,180 | +1,606,733 | +106,274 |
| Carried, space from u relative to its body, on its orbit | +1,757,181 | +1,606,727 | +106,205 |
| VLBI's limit | 10 | 10 | 10 |

Held still, Jupiter's region doesn't move, the jump is the Sun's river across the ray, and it nearly cancels. On its
orbit, Jupiter's region is carried at 13 km/s along the ray, and the light is turned by 1.7″. GR has no such
term: a moving body's frame has $t' = t - \mathbf V\cdot\mathbf x/c^2$, the relativity of simultaneity, and the
carried flow, carrying each river by a Galilean shift, leaves it out.

So the carried flow needs **one time**: a single potential for the whole flow, continuous across the seams (its
part along each seam the same on both sides). The eikonal flows have this; it was what their seam rule assumed. The
lunar range doesn't see it (the Moon and the light stay in the Earth's region), and nor does the Moon's orbit.

**GR's pieces with the clocks left alone.** GR in the carried flow's time differs from the carried flow in three
pieces – Einstein's space, a first post-Newtonian rescaling of the flow, and the moving bodies' $4U_j$ – and in its
lapse. `FreeFallPN` can now drop each (`keep`). With the lapse held at 1, the Moon is 1.3 km off (k = −1685), and
dropping any one piece leaves it 0.5–1.3 km off. The lapse's first post-Newtonian part, of order $V^2/c^2$, is
needed before any of the pieces can be judged; keeping N = 1 means moving it into the flow (a term $\chi/c^4$ in the
time).

**χ: the lapse moved into the flow.** Shifting the time by $\chi/c^4$ changes the lapse and the flow together,

$$N'^2 = N^2 - \frac{2}{c^4}\frac{D\chi}{DT},\qquad \mathbf u' = \mathbf u - \frac{\nabla\chi}{c^2},\qquad
\frac{D}{DT} = \partial_T + \mathbf u\cdot\nabla,$$

so N′ = 1 when $D\chi/DT = Q = c^4(N^2 - 1)/2$: χ is Q carried along the flow, as the tide is. Round the Earth on its
circle the setup is steady in the frame turning with it, so `ChiTable` works χ out once – each path followed out from
1000 km along that frame's flow $\mathbf w = \mathbf u - \boldsymbol\Omega\times\mathbf x$, χ = 0 at its start – and
turns the table with the Earth. (Q has a part ∝ $r^{-3/2}$ at the body, so χ has a logarithm there; the start fixes
it.) The flow's correction $-\nabla\chi/c^2$ is about 1 cm/s at the Moon. What the lapse's gradient did – what moves
the Moon – is left at 0.1% on average (0.2% at most) along its orbit. Carrying χ along the radial infall only left
10%: the turning frame's swirl (80 m/s at the Moon, against 1.4 km/s of infall) and the tide's flow matter.

| GR in the carried flow's free-fall time, tide transported | k | rms |
|---|---|---|
| with χ, lapse kept (a change of time: GR) | +0.017 | 0.024 m |
| with χ, **N = 1** | +0.11 | 0.15 m |
| with χ, N = 1, space flat | +599 | 580 m |
| without χ, N = 1 | −1685 | 1.3 km |

With N = 1 the Moon is GR's to 0.15 m, and de Sitter's precession is whole (stretched 2.03 and 2.00 of $V^2/2c^2$,
GR's 2). So GR's first post-Newtonian metric for the Sun, the Earth and the Moon is a flow with Part 1's clocks:
clocks tick by their speed through the space around them, and moving with the flow is free fall. But only in GR's
space, $(1 + 2U/c^2)\delta - \mathbf u_0\mathbf u_0/c^2$: with space flat the Moon is 580 m off. The shift in time
can take the lapse into the flow; nothing takes the space's curvature there.

## Light past a moving Jupiter, as VLBI measures it

A ray's direction through the coordinates depends on how time is sliced: re-slicing by a flow's potential turns it
by $u_\perp/c$, which is about 20″ for the 25–40 km/s the turning flow has far from the bodies. The cross term (both
bodies less each alone) cancels that, but needs a flow that can be run for one body, which the turning flow can't.
[studies/light_two_rays.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/light_two_rays.py)
measures what VLBI does instead: the angle at one observer between a ray passing Jupiter at b and one at 100 R_J,
each shot from a fixed emitter H before Jupiter to an observer H beyond it. The observer moves with the model's space
there, and measures angles with its metric; GR is given the same observer (its directions aberrated exactly by that
velocity). That angle is the same in any slicing and any coordinates.

| The angle, off GR's (µas) | H = 2 AU, 1 R_J | 10 R_J | H = 0.6 AU, 1 R_J | 10 R_J |
| --- | --- | --- | --- | --- |
| Eikonal, space from u, bodies at rest (the floor) | +0.5 | +0.4 | +2.1 | +1.6 |
| Eikonal, flat, bodies at rest | +41 | +36 | +22 | +19 |
| Carried, Jupiter alone, moving at 13 km/s along the ray | +5.0 | +4.5 | | |
| Turning (one potential), Jupiter on its orbit | +611,861 | +583,322 | **−2.9** | **+22** |
| Carried (a potential per region), Jupiter on its orbit | +782,950 | +710,218 | +200,096 | +182,123 |

Curving space across the flow changes none of the moving rows by more than 0.04 µas: these are first order in
$u/c$. Three things follow:

- **A body's river carried at its velocity is right**: Jupiter alone, moving, is within 5 µas of GR. What fails needs
  two bodies.
- **One potential is what light needs.** A flow that is the gradient of one continuous potential has no first-order
  effect on this angle at all: re-slicing time by the potential removes it. A first-order turn needs curl, and the
  ray is turned by $(1/c)\int \nabla\times\mathbf u\,dy$ along it. The carried flow has its curl in the seams (each
  region's potential jumping there): 0.2″ even with light only 0.6 AU either side of Jupiter. The turning flow, one
  potential, is within 3–22 µas of GR there, against VLBI's 10.
- **The turning flow's tables fail beyond 0.7 AU of Jupiter.** Its curl, measured along the rays' line, is 0 to six
  places within 0.65 AU of Jupiter, and about $2\Omega$ (noisy, 0.4–1.8 times) from 0.7 AU to 1.5–2 AU. There
  Jupiter's paths, run back in time with the Coriolis force, have curved round and cross, and the table's direction
  is a blend of different branches: no potential. $(1/c)\,2\Omega L$ over the 2 AU of each ray is about 9″, and the
  patch's edges move between the two rays: the 0.6″. That is the turning flow's construction, not its idea: where
  its paths cross, a single-valued flow would take one branch (the larger potential) and have a seam with the
  potential continuous across it, as the static eikonal flow's does.

So for moving bodies the flow needs what the static eikonal flow has: one potential over all of space, its seams
where the bodies' potentials are equal. The carried flow has a potential for each region; the turning flow has one,
but only near the bodies.

## One potential for the whole plane: the turning flow with J = 0

A flow steady in the frame turning with the bodies has $\phi = \Phi(\mathbf y) - JT$; for its potential to be
continuous across the seams, J must be one number everywhere. The turning flow's J, chosen so that the Earth's (or
Jupiter's) flow is its own river alone, is $-\tfrac32 GM_\odot/a$: then the Sun's paths stop at 2a/3, and beyond about
0.65 AU from Jupiter the table has no flow, or one that isn't a gradient. With **J = 0**,
$|\mathbf w|^2 = 2(U + \Omega^2\rho^2/2)$ is positive everywhere: the Sun's paths reach every point, and the bodies'
flows are solved together as one potential – the moving eikonal for bodies on circles. Its table is a gradient to
0.02–0.1° out to ±1.8 AU (with the carried J, 18–99° off beyond 1 AU).

Its space, from Einstein's constraint for a flow with no curl, is stretched by the flow's head,
$\partial\phi/\partial T + |\mathbf u|^2/2$, which is Φ when the flow keeps Bernoulli's equation:
$\gamma = \delta + (2\Phi\,\delta - \mathbf u\mathbf u)/c^2$ (`FlowSpacetime(transverse='constraint')`).

| Light past Jupiter on its orbit, as VLBI measures it (µas off GR, at 1 / 10 R_J) | 2 AU | 0.6 AU |
|---|---|---|
| Turning, J = 0, Einstein's space | −12 / −2 | +4 / +2.5 |
| Turning, J = 0, flat | +5 / +14 | +64 / +58 |
| Turning, carried J | +611,861 / +583,322 | −3 / +22 |
| Carried | +782,950 / +710,218 | +200,096 / +182,123 |

One potential is what light needs: the J = 0 flow is the first moving-body flow within VLBI's 10 µas at 2 AU.

But the Moon fails: with J = 0 and Einstein's space it is 98 km off (k ≈ −10⁵); flat, 197 m off; with the carried J
and Einstein's space, 260 m. (An earlier fit had the flat J = 0 flow at 2.8 m: it put GR's Earth at AU − GM☉/c², the
place for the carried times, where the J = 0 time needs AU – see below.) Round the Earth the J = 0 flow
moves at about 50 km/s through the turning frame – it carries the Sun's potential and the orbit's speed,
$|\mathbf w|^2 = 2GM/r + 3GM_\odot/a$ – and Einstein's space is right only together with the flow's first
post-Newtonian corrections and the lapse's (χ). Without them the error grows with the flow's speed, and the Earth,
held on its circle, doesn't share it. Every flow obeying Newton's equation is a slicing of GR's time at Newton's order
(N = 1 + O(c⁻⁴)), so with those pieces any of them – the carried flow's, or this one – gives GR; the flow then decides
only the slicing. What the flow itself decides is the Newtonian order and, through one potential, light; the moving
bodies' first post-Newtonian dynamics still come from GR's pieces.

**GR in this flow's time.** `FreeFallTurning` puts GR's first post-Newtonian metric in the turning flow's time (its
potential is −S), as `FreeFallPN` does in the carried flow's, with χ to take the lapse to 1. χ for the J = 0 flow
leaves 0.04% of the lapse's gradient at the Moon. The Moon fits as GR both ways:

| Time | Moon, rms | k |
|---|---|---|
| Turning flow, carried J | 0.03 m | +0.0005 |
| Turning flow, J = 0, with the lapse | 0.53 m | +0.30 |
| Turning flow, J = 0, χ and N = 1 | 0.60 m | −0.18 |
| GR transformed exactly to the J = 0 time (`SlicedPN` with this potential; the check) | 0.63 m | +0.25 |

So with J = 0 – one potential over the whole plane – GR has Part 1's clocks (N = 1) and passes the Moon as well as
light, to the half metre the exact transform itself leaves (the J = 0 flow is fast, and its time is far from
harmonic, so the fit's floor is higher than the carried time's).

Which of GR's pieces the J = 0 time needs, each dropped in turn (χ and N = 1 kept):

| Dropped | Moon, rms | k |
|---|---|---|
| nothing | 0.60 m | −0.18 |
| the moving bodies' 4U_j/c² | 0.49 m | +0.77 |
| curved space | 23 km | +3×10⁴ |
| the flow's rescaling, $(\varphi_T - 2U)/c^2 = -(U + u^2/2)/c^2$ | 105 km | −1.2×10⁵ |

The moving bodies' term isn't needed; space and the rescaling both are, by tens of kilometres, because the flow is
fast. The flow model with Einstein's space and J = 0 (98 km) is the row without the rescaling. So what a flow of its
own must supply beyond Einstein's space is a flow slowed by $(U + u^2/2)/c^2$ and the lapse's part moved into it,
$-\nabla\chi/c^2$.

**The J = 0 flow as a model of its own.** Without the moving bodies' term, what is left is a flow model with these
rules, each built from Newton's U, the bodies' Newtonian motion, and the flow (u = ∇φ, J = 0):

1. clocks keep T (N = 1);
2. space stretched by the potential and contracted along the flow, $\gamma = (1 + 2U/c^2)\delta - \mathbf u\mathbf u/c^2$
   (Einstein's constraint);
3. the flow slowed by $(U + u^2/2)/c^2$;
4. the flow less $\nabla\chi/c^2$, χ carried along the flow (in the turning frame) from the source
   $Q = c^4(N^2 - 1)/2$ that rules 1–3 would leave in the clocks – the flow's and the potential's terms, the shift of
   U to harmonic time ($\partial_T U\,\varphi/c^2$), and the bodies' first post-Newtonian potential ψ (their kinetic
   and binding energy and their field's motion).

The Moon is GR's to 0.49 m. Taking parts out of χ's source shows what each is worth: without ψ, 1.6 m (k +1.0); without
the shift to harmonic time, 14.5 m (k −15.6). Every part of the source is Newtonian – U, its rate, the bodies'
velocities and accelerations, and φ – but ψ is a correction to the source the flow comes from, not something the flow
makes. And the rules are GR's 1PN metric rearranged: they say GR can be written as a flow with Part 1's clocks, not
that the flow model derives it.

Two things had to be right for this. GR's time at the Earth runs at $dt/dT = 1 + \kappa/c^2$, κ = dφ/dT along the
Earth: for the carried flow (and the carried J) κ = −J = 1.5 GM☉/a, and the Earth held at Ω in T is GR's free fall at
harmonic r = AU − GM☉/c²; for J = 0 the potential is steady at the Earth, κ = 0, and GR's Earth is at AU. Fitted at
AU − GM☉/c², every J = 0 time is off by the same 195–197 m (k −225), the exact transform included. And the study
maps T to GR's time with the integral of the model's own flow from the Earth to the Moon – the turning flow's, about
10¹³ m²/s there with J = 0. The flow round the Earth (`LocalTurningFlow`: the Earth's paths followed out with fine
steps and fitted smoothly in angle and ln r) falls at g to 5×10⁻¹² m/s² at the Moon; the ray table's does to 10⁻⁹
(a check with too wide a finite difference had made that look like 10⁻⁶), and the Moon is the same with either.

**Its bodies: a circular binary** (`studies/binary_regularized.py`). To move the bodies by the J = 0 flow, each
needs a rule for how it moves in a flow that holds its own field. Round the Earth the flow moves through the turning
frame at about 51 km/s, but it streams out from the Earth equally every way: its average round a circle about the
Earth is under 10⁻⁹ m/s at 1,000 and 10,000 km and 3×10⁻⁵ m/s at 300,000 km (the Sun's tide). So the flow's regular
part at a body is the body's own velocity, and a body at rest in the turning frame moves with its space. The rule
that says this is the one GR's two-body motion is derived with: each body a geodesic of the whole metric with its
own singular terms removed (Hadamard's finite part, the r⁰ part of its acceleration on a small sphere round it,
averaged over the sphere).

The J = 0 rules are GR's first post-Newtonian metric in another time, less the moving bodies' 4U_j/c² – which,
taken back to harmonic time, is GR's $g_{ti}$ and nothing else at this order. That time runs at rate 1 at each body
(κ = 0), and its singular parts leave nothing in the finite part (half powers of r, or odd in the direction), so
the J = 0 rules' bodies move as GR's harmonic metric less 4U_j moves them. That is worked out exactly (sympy), for
two bodies on circles at a, η = m₁m₂/M²:

| Each body a regularized geodesic of | k in ω² = (GM/a³)(1 + k GM/(ac²)) | equal masses |
|---|---|---|
| GR's whole metric (the check) | −3 + η | −2.75 |
| the J = 0 rules (GR less 4U_j) | −3 + 5η | −1.75 |
| the other body's field alone | −3 + 3η | −2.25 |
| … with its binding term (−GM_A/r_AB in the other's ψ) | −3 + η | −2.75 |
| … less 4U_j | −3 + 7η | −1.25 |

Nothing pushes along the orbit in any of them. The periastron advance follows from the two-body Lagrangian each
gives (first-order perturbation; it is 3 GM/(c²p) per orbit over 2π for a test body and for GR at any η). Leaving
out 4U_j takes $-4Gm_1m_2\,\mathbf v_1\cdot\mathbf v_2/(rc^2)$ out of GR's (EIH's), and the advance becomes
(3 − 8η) GM/(c²p): a third of GR's at equal masses, which the double pulsar measures to about 10⁻⁴.

- **The rule works.** GR's own metric moved this way is GR's binary exactly. At this order removing a body's own
  terms leaves the other body's field together with its binding term – the one place a body's field acts on the
  other's source. That is what "each body in the others' fields alone" leaves out – the rule the carried flow's
  bodies were moved by, which with GR's own metric gave 0.83 of GR's advance (the scorecard's second check). So that
  check's failure is the missing binding term; the carried flow's own errors haven't been split up this way.
- **The J = 0 rules fail it by 4η**, the moving bodies' term they left out. The Moon didn't need it (0.49 m
  without, 0.60 m with); the binary does: it is one body's velocity in its field felt by the other's velocity.
- **With 4U_j back** – the flow plus each body's potential carried at its velocity, $4U_j/c^2$ – the J = 0 time is GR
  in it, and the binary is GR's. That term is Newtonian, like the rest (U and the bodies' velocities), but with it
  the rules are GR's whole first post-Newtonian metric, rearranged.
- This is the circular binary only; eccentric orbits can't be run in the turning flow, whose bodies go round on
  circles. The advance comes from the Lagrangian, not a run, and Nordtvedt hasn't been worked out.

## What it means

The lapse and curved space are now in the engine for every model, and it reproduces GR in any of its coordinates.
What they show about the flow model:

- One body doesn't mind how gravity is split: any share can go into the clocks, with space curved to match.
- With two bodies, putting gravity into the clocks fixes the flow model's failures only in proportion – by taking
  gravity out of the flow, which ends at conventional GR.
- Keeping the clocks as Part 1 has them (N = 1) and curving space across the flow fixes them outright for bodies at
  rest. This is the first multi-body version that passes lunar ranging's synodic term and the
  Jupiter bending while keeping "clocks tick by their speed through space". Part 1's hypothesis then changes from
  "space flows and is flat" to "space flows, and is stretched across its flow by the potential".
- Writing that space with the flow alone, stretched across its motion by $u^2/c^2$ (u relative to its body, so that
  it is the same in every frame), makes the flow decide the geometry as well as the motion. It keeps the eikonal
  flow's results, and it fixes the turning flow's light past the Sun (9.6 mas to 0.001), because light then doesn't
  feel the turning flow's Jacobi constant.
- For moving bodies, the turning flow and the carried flow (each body's river carried at its velocity, the bodies
  moved by it) both pass light past the Sun. With their Newtonian errors taken out, both have half of de Sitter's
  precession and leave 0.26 m on the Moon's orbit. And the carried flow's bodies fail the binary and Nordtvedt as the
  split model's did: each body moves in the others' fields alone.
- Einstein's constraints give the space the flow needs: stretched by the potential, contracted along the lab's flow by
  $u^2/c^2$, for any flow with no curl. On its own it makes the moving-body tests worse; it needs the flow's own
  first-order corrections with it, which are GR's.
- GR itself, put in the carried flow's time, passes the Moon test once the flow meets Newton's equation exactly (its
  tide transported along the river). The carried flow with the same tide still has half of de Sitter's precession:
  the shortfall is the flow's, not the test's.
- The carried flow's regions each keep their own time, and it jumps at the seams: light past a Jupiter on its orbit
  is turned by 1.7″. A flow made of separate regions needs one potential across all of them. Measured as VLBI does,
  the turning flow – one potential – is within 3–22 µas of GR near Jupiter, and the carried flow 0.2″ off.
- With a further shift of time (χ, carried along the flow), GR for the Sun, the Earth and the Moon has N = 1 exactly
  and the Moon's whole de Sitter precession (0.15 m left): GR is a flow with Part 1's clocks. Its space must still be
  curved – flat, the Moon is 580 m off.
- The turning flow with Jacobi constant 0 is one potential over the whole plane (the bodies' flows solved together,
  for bodies on circles). With Einstein's space, light past a moving Jupiter is within 2–12 µas of GR. The Moon fails
  (98 km; flat, 197 m): Einstein's space needs the flow's first post-Newtonian corrections with it, and with J = 0 the
  flow round the Earth is 50 km/s. With those corrections – GR in this flow's time, the lapse taken to 1 by χ – the
  Moon passes (0.6 m) as well as light: one potential, Part 1's clocks, and GR's curved space and moving-body pieces.
- Its bodies, each moving with the regular part of its space (its own singular terms removed), make a circular
  binary. With GR's pieces in the J = 0 time that is GR's binary exactly; the J = 0 rules, which leave out the moving
  bodies' 4U_j/c², get ω's first post-Newtonian coefficient −3 + 5η for GR's −3 + η, and a third of GR's periastron
  advance at equal masses. The Moon doesn't need that term; the binary does. And "each body in the others' fields
  alone" fails by the binding term in the others' source, which removing a body's own terms keeps.
- So the next step isn't another rule for carrying flows. GR's de Sitter precession needs the Sun's curved space carried
  round with the Earth, and the binary and Nordtvedt need each body's field to act on the others'. Both point to the
  bodies' flows solved together – a field equation for the flow – not each one carried separately.

## Run it

```bash
python3 studies/metric_checks.py
```

```bash
python3 studies/lapse_two_bodies.py
```

```bash
python3 studies/lapse_moving.py
```

```bash
python3 studies/light_two_rays.py 0.6
```

```bash
python3 studies/lapse_moon.py 90 differenced
```

```bash
python3 studies/carried_bodies.py
```

```bash
python3 studies/constraints.py
```

```bash
python3 studies/binary_regularized.py
```
