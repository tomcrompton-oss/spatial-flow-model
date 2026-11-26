# The seam: an investigation

Branch `seam-investigation`, 26–27 November 2026. Studies in `studies/seam_*.py`, runs in `logs/modelChecks/seam*`.
Nothing on the site was changed.

## Short answers

1. **Does crossing the seam break physics?** No, with the crossing rule and curved space. Light crossing the seam
   follows general relativity's path to 3–130 m over 600,000–1,000,000 km (a few parts in 10⁸). It turns at the seam
   by 10⁻⁷ rad, no more than in any ordinary step. Particles follow general relativity as closely as the comparison
   itself can tell. Energy changes across a crossing by under 10⁻⁹, no more than in an ordinary step. Without the
   rule (keeping the momentum as it is), light kinks by 10⁻⁵–10⁻² rad and particles by up to 0.3 rad.
2. **Is the seam always in the same place?** No. It belongs to the choice of time, not to the spacetime. Moving the
   whole system with its space (Part 3's rule) carries the seam along unchanged. But other equally valid choices of
   free-falling observers put it elsewhere, or give a single body a seam. The radial observers the model uses have
   none.
3. **Is the seam rule only for seams?** No. It is how a particle's momentum changes when the clock it is measured by
   changes, and it works on any boundary between two time-slicings. Two conditions: it must use the direction in
   which the two times differ (the flow's jump), not the boundary's own shape; and with bodies moving, the boundary
   must be where the two times agree.
4. **What fixes where the seam is?** Where the two bodies' $S$ are equal, up to a constant: $S_0 = S_1 + c$. The engine
   picks $c$ so the seam passes through the saddle, where $g = 0$. Any $c$ gives a valid seam: moved 23,000 km off
   centre, light still follows general relativity to the same precision. Its limits: it must be a curve where the
   two times agree, it must stay between the bodies, and each region must be the one whose $S$ is the smaller, so
   that the seam is a source of space, never a sink.
5. **Is space created at the seam, and does that break conservation?** In the flow's bookkeeping, yes. The flow on
   each side points away from the seam, so the seam makes space: for two equal bodies 200,000 km apart, 3 × 10²³ m³/s
   within 200,000 km of the middle, a third of what the flow loses in that volume. For the Sun and the Earth it is
   about 0.2%. But the amount changes by 6% when the seam is moved, with no change to any path, and a single body has
   a seam under other observers. So the space made is bookkeeping of the chosen time, not something physical. No
   conservation law of the matter or light is broken: their energy is kept across it, and their paths are general
   relativity's. Space itself was never conserved in the model: the flow converges everywhere and disappears into
   nothing ($\nabla\cdot\mathbf u < 0$, and point bodies take none in).

## 1. Paths crossing the seam

`studies/seam_crossing.py`. Two solar masses 200,000 km apart, at rest, so that the flow at the seam's middle is 0.8%
of c and any kink would be large. With space curved across the flow, the model is general relativity's first
post-Newtonian metric re-sliced in time, $T = t + S(\mathbf x)/c^2$, with the same spatial coordinates. A re-slicing
can't change a path's shape in space, only how fast it is traced. So each path is started at the same place in the
model and in general relativity (`PostNewtonian`), and the two paths are compared point by point.

| Path | The engine's rule, space curved | Keep p (no rule) | Keep v | The rule, flat space |
| --- | --- | --- | --- | --- |
| light across the middle, 30,000 km off the line | 32 m (turn at the seam 9 × 10⁻⁸ rad) | 15 km (2.5 × 10⁻⁵) | 33 m | 15 km |
| light across, 100,000 km off | 9 m | 24 km | 9 m | 1.8 km |
| light across, 300,000 km off | 3 m | 7.6 km | 3 m | 1.2 km |
| light at 45° to the seam | 81 m | 5,300 km (9.4 × 10⁻³) | 81 m | 22 km |
| light along the seam, 1,000 km beside it (no crossing) | 34 m | — | — | 33 km |
| light crossing near a body | 15 m | 617 km (10⁻³) | 16 m | 6.8 km |
| a particle at 3,000 km/s, across | 19 km | 35,500 km (0.31 rad) | 69 km | 96 km |
| a particle at 3,000 km/s that never crosses (the comparison's noise) | 8.7 km | — | — | 42 km |
| a particle at 10,000 km/s, across, near a body | 24 km | 88,000 km | 184 km | 186 km |

- **The rule is right.** For light it matches general relativity as well as a path that never crosses. For
  particles it is within a few times the comparison's own noise, which comes from converting the starting velocity
  between the two times.
- **"Keep v" (keep the coordinate velocity) is the same as the rule for light**, whose direction a re-slicing
  doesn't change, **but worse for particles.**
- **Flat space's errors** (1–30 km for light) are there whether the path crosses or not: they are flat space's own,
  first order beyond Newton, not the seam's.
- **Energy** (`studies/seam_energy.py`, orbits round both bodies, up to 27 crossings): the change across a crossing step,
  3–9 × 10⁻¹⁰ of the energy, is no larger than an ordinary step's (typically 4 × 10⁻¹⁰ to 10⁻⁹).

## 2. The seam in other frames

`studies/seam_frames.py`, and an exact check.

- **The bodies and their space moving together** (Part 3's carried space): the whole flow is $\mathbf u + \mathbf V$,
  a change of frame, and the seam goes with the bodies unchanged.
- **The bodies moving through space at rest far away**: in the bodies' frame space streams past, and the free-fall
  observers arrive from one direction rather than from every direction. Their flow is a different solution of the
  same equation, a different slicing of the same spacetime, and its seams are elsewhere. Even one body gets one.

  For one body, zero-energy free fall has, exactly:

  | Observers | $S$ | Seam |
  | --- | --- | --- |
  | falling straight in from every direction (the model's) | $2\sqrt{2GMr}$ | none |
  | arriving from rest far away along $\hat{\mathbf n}$, on parabolas | $2\sqrt{GM(r + \hat{\mathbf n}\cdot\mathbf x)}$ | the half-line from the body in direction $-\hat{\mathbf n}$ |

  Both satisfy $|\nabla S|^2 = 2GM/r$ exactly (sympy), and across the half-line the second's flow reverses its
  sideways part. The traced paths put a seam on that line too. With two bodies and space streaming past, the paths
  cross many times and the seams are complicated; the grid study doesn't resolve them cleanly, so only this much is
  claimed: they are not the rest frame's seam.

## 3. The crossing rule away from seams

`studies/seam_rules.py` and `studies/seam_moving.py`. One body, the model's time inside a boundary and general
relativity's own time outside it, and light crossing the boundary, compared with general relativity all the way.

Bodies at rest:

| Boundary | Normal from the flow's jump (the engine's) | The boundary's own normal |
| --- | --- | --- |
| a circle round the body (the two times meet, up to a constant) | 8–26 m | the same |
| a straight line (the times don't meet) | 4 m | 2,500 km, kinks of 4.6 × 10⁻³ rad |

A body moving at 0.1 c, with general relativity re-sliced exactly by the body's carried flow (`SlicedPN`) inside:

| Boundary, moving with the body | Light vs general relativity |
| --- | --- |
| a level set of the time difference (the times agree all along it) | 0.7–2 km |
| a circle (they don't) | 58,000–67,000 km, kinks of 0.1 rad |
| a circle held fixed in space | 77,000 km |

So the rule is the change of momentum that comes with changing the clock: the momentum along the surfaces of equal
time difference is kept, the energy in the boundary's frame is kept, and the rest follows. It works on any boundary
when it uses the flow's jump for the direction. With the bodies still, it works even where the times don't agree,
because nothing depends on time; with a body moving, the boundary must be where they agree, or the light comes out at
the wrong moment. (The 1 km left on the level set at 0.1 c is still a hundred-thousandth of the failures; it may be
the next order, and wasn't chased.)

## 4. Where the seam can go

`studies/seam_rules.py`. The engine's seam is $S_0 = S_1 + c$, $c$ set so it passes through the saddle. Changing $c$:

| $c$ (in units of $S$ at the saddle) | Where the seam crosses the line between the bodies | Light vs general relativity |
| --- | --- | --- |
| −0.3 | 23,000 km towards body 0 | 19–132 m |
| −0.1 | 7,800 km towards body 0 | 5–99 m |
| 0 (the saddle) | the middle | 9–81 m |
| +0.1 | 7,800 km towards body 1 | 20–62 m |
| +0.3 | 23,000 km towards body 1 | 20–48 m |

The constraints, from the construction rather than from these runs:
- **The two times must agree on it.** Each region's time is $t + S_k/c^2$, so the seam must be a level set of
  $S_0 - S_1$. That is what makes $c$ the only freedom.
- **It must be a source.** With the smaller $S$ chosen, the flow points away from the seam on both sides, and each
  body's region contains the body. Choosing the larger would need each body's flow on the far side of the other body,
  where its paths don't reach.
- **It can't reach a body.**

## 5. Space made at the seam

`studies/seam_space.py`. In 3D (the flow turned about the line through the bodies), flat space, within a sphere of
radius $R$ about the middle: space flows in through the sphere, is made at the seam, and is lost through the volume
(the flow converges everywhere; point bodies take in none).

| | $R$ | Made at the seam | Lost in the volume | Seam's share |
| --- | --- | --- | --- | --- |
| two solar masses, $D$ = 200,000 km | 0.6 D | 1.5 × 10²³ m³/s | 3.8 × 10²³ | 40% |
| | 1 D | 3.2 × 10²³ | 1.0 × 10²⁴ | 32% |
| | 10 D | 3.7 × 10²⁴ | 2.9 × 10²⁵ | 13% |
| the Sun and the Earth | 1 AU | 2.1 × 10²⁵ | 1.1 × 10²⁸ | 0.2% |

The largest jump across the seam is twice the flow there: 4.6 × 10⁶ m/s between the equal bodies, 84 km/s at the
Earth's seam. Moving the seam ($c$ = ±0.3) changes what it makes within 1 D from 3.24 to 3.05 × 10²³ m³/s, with no
change to any path.

What it means:
- **It's bookkeeping of the time chosen.** The observers who define the time come from infinity, two families; at the
  seam the model hands from one family to the other. Seen as space, that is space appearing. It depends on where the
  seam is put and on which observers are chosen, and neither changes anything measured.
- **Nothing physical is created.** Light and matter keep their energy across the seam, and follow general
  relativity's paths.
- **Space was never conserved in the model**, seam or no seam. The one-body flow already loses space throughout the
  volume, $\nabla\cdot\mathbf u = -\tfrac32|\mathbf u|/r$. This matches what Part 6's stretching investigation found:
  the "extra space" was coordinate bookkeeping.
- **The time slices have a crease.** $T = t + \min(S_0, S_1)/c^2$ has a ridge at the seam, so the surfaces of
  constant $T$ have a fold there: a jump in their extrinsic curvature, of size the jump in the flow. That fold is the
  seam, as geometry. The spacetime itself is smooth there.

## Also found

- **The engine already uses the right normal.** `MetricCalculator.crossSeam` takes the direction of the flow's jump,
  which for a seam is the normal to $S_0 - S_1$'s level sets, the one that works. A boundary-shaped normal would fail
  wherever the boundary isn't a level set.
- **Flat space is the bigger error.** Part 2's flat potential flow is off by kilometres for light whether or not it
  crosses the seam; the seam adds nothing visible on top.
- **The seam rule and the hollow sphere's rule are the same rule.** Part 2's "change reference frame at the
  boundary" is this rule, and its 0.27% hollow-sphere result fits.

## Not done

- Two bodies with space streaming past: the seam pattern is complicated (paths cross many times) and the grid study
  doesn't resolve it cleanly.
- A moving seam's crossing (the turning flow's, Part 3) wasn't tested here, though Part 3's tests pass through it.
- The ~1 km left on the moving level set at 0.1 c.

## Run it

```bash
python3 studies/seam_crossing.py
```

```bash
python3 studies/seam_rules.py
```

```bash
python3 studies/seam_moving.py
```

```bash
python3 studies/seam_space.py
```

```bash
python3 studies/seam_frames.py
```

```bash
python3 studies/seam_energy.py
```
