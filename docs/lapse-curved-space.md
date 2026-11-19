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
- Writing that space with the flow alone, stretched across its motion by $u^2/c^2$, makes the flow decide the
  geometry as well as the motion. It keeps the eikonal flow's results, and it fixes the turning flow's light past the
  Sun (9.6 mas to 0.001), because light then doesn't feel the turning flow's Jacobi constant.
- Still to do: the moving-body tests for the turning flow with this space – the Moon's own orbit, de Sitter
  precession, Nordtvedt and the binary pulsars – and its conserved quantities.

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
