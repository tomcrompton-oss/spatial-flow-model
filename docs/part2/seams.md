# Seams

[Potential Flow](potential-flow.md) gave each body a region of its own, and a seam where the regions meet. Across the
seam the flow's direction jumps, and something crossing it changes reference frame, as at the
[Hollow Sphere](hollow-sphere.md)'s boundaries. This page looks at seams closely: why there has to be one, where it
is and where else it could be, what happens to paths that cross it, with and without the crossing rule, what happens to
it in other frames of reference, and what it means.

!!! note "Reader's note"
    This is conceptually the hardest part of the whole Spatial Flow model. Everywhere else, flowing space can be
    pictured directly: space moves, and things move with it or through it. At a seam the picture has to give way to
    something less intuitive, the choice of whose clocks set the time. It is also the part that matters most for what
    the model says about the real world. If space really flows, a seam would be a place where space is created; this
    page finds instead that a seam is a feature of how the clocks are set, with no effect that any measurement could
    find. That shapes how the rest of the model should be read: the flow is a faithful way of describing gravity, but
    not every feature of it is a physical thing. It is worth taking this page slowly, and coming back to it.

Some of the comparisons here use the curved space of the [next page](curved-space.md). With it, the model *is* general
relativity to the first order beyond Newton, only with its clocks set differently, so a path's shape in space should
be general relativity's exactly, seam or no seam. That makes it the sharpest test of what a seam does to a path.

## Why there is a seam

Round a single body, space flows down the paths of things falling from rest far away, and every point is on exactly
one such path. Round two bodies, every point is on two: one that ends at the left body, and one that ends at the right,
each falling in the pull of both.

![Left: two families of paths of things falling from rest far away, in the pull of two equal bodies. Blue paths end at the left body, red ones at the right body, and they cross everywhere; at a point P, one blue and one red path pass through, pointing in different directions. Right: the flow following one path at each point. Each body's region is filled by the paths into it, and a dashed seam runs up between the bodies, where the flow switches from one family to the other; between the bodies the flow leaves the seam on both sides](images/seamwhy.svg)

The flow can only go one way at a point, so it has to pick one. Each body's path has its own $S$, the flow's speed
added up along the path from that body out to the point; it grows with distance from the body. The flow takes the
path with the smaller $S$. That keeps each body in a region of its own, filled by the paths that run into it, and the
seam is where the choice changes.

There is no way round it. On the line between two equal bodies, the flow must run towards the left body near the left
body, and towards the right body near the right. By symmetry it can't turn sideways on that line, and it can't slow to
a stop, because its speed has to be the escape speed, $\sqrt{2GM_1/r_1 + 2GM_2/r_2}$, which is never zero. So
somewhere it must reverse, all at once. A flow with no swirl and the right speed round two bodies has a seam.

## Where the seam is

Along the line through two equal bodies, each body's $S$ rises away from it. The flow's $S$ is the smaller of the two,
which makes a ridge where they cross, and the flow runs down $S$, away from the ridge on both sides:

![S along the line through two equal bodies. The left body's S rises from zero at the left body; the right body's S rises from zero at the right body. The flow's S, a thick line, is the smaller of the two: it rises from each body and peaks where they cross, half way between, which is the seam. A copy of the right body's S raised by a constant c crosses the left body's further to the right: the seam moved. Arrows below show the flow running down S, away from the seam on both sides](images/seamprofile.svg)

The seam is where the two bodies' $S$ are equal. In the engine, one body's $S$ carries a constant, chosen so that the
seam passes through the point between the bodies where their pulls cancel and $g = 0$.

- **Two equal bodies:** the plane half way between them.
- **Unequal bodies:** a curve round the lighter body, through the point where $g = 0$. For the Sun and the Earth, it
  is a bowl round the Earth about 260,000 km out on the Sun's side, opening away from the Sun; it crosses the Moon's
  orbit, as [Curved Space](curved-space.md) shows.
- **Three or more bodies:** a seam between each pair, meeting where all the pulls cancel, as
  [Multiple Bodies](multiple-bodies.md) shows.

### Somewhere else?

Nothing in the flow requires the constant to be that one. Adding any constant $c$ to one body's $S$ moves the seam,
and the flow is still a flow with no swirl and the right speed everywhere: the seam is any curve where
$S_0 = S_1 + c$.

![Seams for two equal bodies (left) and for one body four times the other (right). The engine's seam, thick and dashed, passes through a dot between the bodies where g is zero. Either side of it, thinner dashed curves are other seams, each where the two bodies' S differ by another constant, bending round one body or the other. On the left, a grey circle round the right body, which crosses these curves, is marked as not a seam](images/seamlevels.svg)

The simulation moves the seam between two solar masses 200,000 km apart, shifting the constant by up to 0.3 of $S$ at
the point where $g = 0$, which moves the seam 23,000 km towards one body or the other. Light crosses each, with space
curved:

<iframe src="../../viewer/index.html?player&run=../runs/seams/placement.full.json" width="100%" height="520" loading="lazy" title="Light crossing seams in different places"></iframe>

*The seam in three places (dotted): moved towards the left body (blue), the engine's (grey) and moved towards the
right body (orange); light crossing each, in the same colour, and general relativity's path (dashed). They lie on top
of each other.*
[Open full screen](../../viewer/index.html?run=../runs/seams/placement.full.json){ target=_blank }

| The constant (of $S$ at $g = 0$) | Where the seam crosses the line between the bodies | Light, furthest from general relativity's path |
| --- | --- | --- |
| −0.3 | 23,000 km towards the left body | 19–132 m |
| −0.1 | 7,800 km towards the left body | 5–99 m |
| 0, the engine's | half way | 9–81 m |
| +0.1 | 7,800 km towards the right body | 20–62 m |
| +0.3 | 23,000 km towards the right body | 20–48 m |

*(Each over a path of about a million kilometres: a few parts in 10⁸, the model's own error at this order.)* Where the
seam is put makes no difference to any path.

## Crossing the seam

Something crossing the seam changes reference frame, as at the hollow sphere's boundaries. The seam is at rest and
doesn't change with time, so the crosser's energy should be the same on both sides; and nothing changes along the
seam, so its momentum along the seam should be too. The engine keeps both, and that fixes its momentum across the
seam.

![Two panels, each a dashed seam with region 0 on the left and region 1 on the right; faint arrows show the flow running away from the seam on both sides, at the same speed and with the same part along it. A path crosses the seam. Left, with the rule: the path goes straight on; before the seam, its velocity v (red) is the flow u (blue) plus its velocity through space w (green); after it, v is the same, and w has changed by the jump in the flow. Right, without the rule: w is kept, so v jumps by the jump in the flow, and the path kinks away from general relativity's path (dashed)](images/seamrule.svg)

To the first order, this keeps the crosser's velocity $v$ as a distant observer sees it. Its energy is
$\tfrac12|\mathbf v|^2 - \tfrac12|\mathbf u|^2$, and the flow's speed is the same on both sides of the seam, so the
energy keeps the size of $\mathbf v$; the flow's part along the seam is the same on both sides too, so keeping the
momentum along it keeps that part of $\mathbf v$. The path goes straight on. What changes is the crosser's velocity
*through space*, $\mathbf w = \mathbf v - \mathbf u$: it changes by the jump in the flow, because the space it is in
has changed. That is the hollow sphere's rule: keep the velocity relative to the boundary.

Its clock carries on too. The flow's time on each side is $T = t + S/c^2$, with that side's $S$, and on the seam the
two are equal, so the crosser carries the same moment across.

### Paths crossing

Two solar masses 200,000 km apart, at rest, so that the flow at the seam is 0.8% of the speed of light and any kink at
the seam would be large. Light crosses at several places and angles, and particles at 3,000 km per second, each
against general relativity from the same start:

<iframe src="../../viewer/index.html?player&run=../runs/seams/crossing.full.json" width="100%" height="560" loading="lazy" title="Light crossing the seam"></iframe>

*Light crossing the seam: the model, space curved (solid), and general relativity (dashed), over the flow and its seam,
across the middle (blue), at 45° to the seam (orange), close to a body (green) and well clear of both (purple). The
model's paths lie on general relativity's. (The particles are in the player under [Without the rule](#without-the-rule).)*
[Open full screen](../../viewer/index.html?run=../runs/seams/crossing.full.json){ target=_blank }

| Path | Furthest from general relativity's path | Its turn at the seam |
| --- | --- | --- |
| light across the middle, 30,000 km off the line | 32 m | 9 × 10⁻⁸ rad |
| light across, 100,000 km off | 9 m | 1.2 × 10⁻⁷ rad |
| light across, 300,000 km off | 3 m | 3 × 10⁻⁸ rad |
| light at 45° to the seam | 81 m | 9 × 10⁻⁸ rad |
| light crossing close to a body | 15 m | 1.3 × 10⁻⁷ rad |
| light along the seam, 1,000 km beside it (never crossing) | 34 m | |
| a particle at 3,000 km/s, across | 19 km | 5.5 × 10⁻⁵ rad |
| a particle at 3,000 km/s, never crossing | 8.7 km | |

For light, a path that crosses the seam follows general relativity as closely as one that never does, to a few parts in
10⁸, and its turn at the seam is no bigger than an ordinary step's. For the particles, the comparison itself has
kilometres of noise, from converting the starting velocity between the two ways of setting clocks; the one that crosses
is within a few times the one that doesn't.

### Round and round

An orbit round both bodies crosses the seam twice a time round. Over 20,000 seconds it crosses 27 times:

<iframe src="../../viewer/index.html?player&run=../runs/seams/orbit.full.json" width="100%" height="560" loading="lazy" title="An orbit round both bodies, crossing the seam"></iframe>

*An orbit round both bodies: the model, space curved (blue), and general relativity (dashed).*
[Open full screen](../../viewer/index.html?run=../runs/seams/orbit.full.json){ target=_blank }

The seam should take nothing from the orbit and give it nothing, so its energy should stay the same at every crossing:

<iframe src="../../viewer/index.html?player&run=../runs/seams/orbitEnergy.full.json" width="100%" height="400" loading="lazy" title="The orbit's energy over the run"></iframe>

*The orbit's energy, its change from the start in parts in a million, over the run. It wanders by a few parts in 10⁷
as the orbit goes round, and drifts by 16 parts in a million over the run, from the arithmetic's steps.*
[Open full screen](../../viewer/index.html?run=../runs/seams/orbitEnergy.full.json){ target=_blank }

Some of its wiggles fall at crossings, so the steps were measured one by one:

| Steps taken | How many | Change in energy per step, on average |
| --- | --- | --- |
| across the seam (the crossing step itself) | 27 | at most 3.5 parts in 10¹⁰ |
| within 1,000 km of the seam | 204 | 3.5 parts in 10¹⁰ |
| 1,000–5,000 km from it | 791 | 4.2 parts in 10¹⁰ |
| 5,000–20,000 km | 3,048 | 4.4 parts in 10¹⁰ |
| 20,000–50,000 km | 6,432 | 4.9 parts in 10¹⁰ |
| further away, nearer the bodies | 53,997 | 6.6 parts in 10¹⁰ |

The energy changes no more at the seam, or near it, than anywhere else in the orbit; less, if anything, since the seam
is far from both bodies, where the steps are easiest.

## Without the rule

What if nothing changed at the seam: the crosser simply kept its velocity through space, $\mathbf w$, and found itself
in the other side's flow? Then its velocity $\mathbf v = \mathbf u + \mathbf w$ would jump by the jump in the flow,
which between two bodies is up to twice the flow's speed. The path would kink.

<iframe src="../../viewer/index.html?player&run=../runs/seams/without.full.json" width="100%" height="560" loading="lazy" title="Crossing the seam without the rule"></iframe>

*Two particles crossing the seam: with the crossing rule (blue, green), without it (pink, amber), and general
relativity (grey, dashed). Without the rule, each kinks at the seam and leaves general relativity's path.*
[Open full screen](../../viewer/index.html?run=../runs/seams/without.full.json){ target=_blank }

| Path | With the rule: furthest from general relativity | Without: furthest | Without: its kink at the seam |
| --- | --- | --- | --- |
| light across the middle | 32 m | 15 km | 2.5 × 10⁻⁵ rad |
| light at 45° to the seam | 81 m | 5,300 km | 9.4 × 10⁻³ rad |
| light close to a body | 15 m | 617 km | 1.0 × 10⁻³ rad |
| a particle at 3,000 km/s | 19 km | 35,500 km | 0.31 rad |
| a particle at 10,000 km/s, close to a body | 24 km | 88,000 km | 0.04 rad |

Light kinks a little, because the flow is a small part of its speed; a particle moving at about the flow's own speed is
turned through 18°. And at the hollow sphere's walls, where space meets itself head on, something carried by its space
couldn't cross at all.

## What makes a seam

So the seam can be moved. What can't change? Each body's region has its own time, $T = t + S_k/c^2$ with its own $S$,
and something crossing carries its moment across. Three conditions follow.

- **The two times must agree on it.** That makes it a curve where $S_0 - S_1$ is constant, like the seams drawn
  above for different constants. A circle round one body is not one of them: the two times would differ along it.
- **The rule must use the direction in which the two times differ**, the direction of the flow's jump, which is
  across the curves where $S_0 - S_1$ is constant. On a seam that is the seam's own direction across; on any other
  boundary it isn't.
- **Each body must be in its own region.** The flow on each side comes from its own body's paths, so the seam stays
  between the bodies, never reaching either. Taking the smaller $S$ does this; taking the larger would need each
  body's paths on the far side of the other body, where they don't go. It also makes the seam a place space flows
  away from, never into, so nothing carried by its space is carried into it.

### The rule away from seams

The rule isn't special to seams. It is what happens to a particle's momentum when the clock it is timed by changes, and
it works on any boundary between two ways of setting clocks. To test this, the simulation joins two: the model's flow
round one body inside a boundary, and general relativity's own coordinates outside it. With the body at rest, light
crossing either way matches general relativity all the way, if the rule uses the direction of the jump:

| Boundary, the body at rest | The rule, across the jump | The rule, across the boundary |
| --- | --- | --- |
| a circle round the body (the two times agree, up to a constant) | 8–26 m | the same |
| a straight line beside it (they don't) | 4 m | 2,500 km, kinks of 4.6 × 10⁻³ rad |

With the body at rest, nothing depends on time, so even a boundary where the times disagree works. With the body
moving, it doesn't. Here a body moves at a tenth of the speed of light, its flow carried with it; inside, the model's
time, and outside, general relativity's; light passes it, crossing a boundary that moves with the body:

<iframe src="../../viewer/index.html?player&run=../runs/seams/moving.full.json" width="100%" height="560" loading="lazy" title="Light past a moving body, crossing a boundary between two times"></iframe>

*Light passing a body moving up the page at 0.1 c (black): general relativity (dashed), crossing a boundary where the two
times agree (green), and crossing a circle where they don't (pink). Each boundary is drawn dotted where it is as the
light passes.*
[Open full screen](../../viewer/index.html?run=../runs/seams/moving.full.json){ target=_blank }

| Boundary, the body moving at 0.1 c | Light, furthest from general relativity | Its kink at the boundary |
| --- | --- | --- |
| where the two times agree | 0.7–2 km | 4 × 10⁻⁸ rad |
| a circle round the body | 58,000–67,000 km | 0.1 rad |
| a circle fixed in space | 77,000 km | 0.05–0.09 rad |

Where the times disagree, the light carries the wrong moment across, and meets the body where it isn't. Where they
agree, the light follows general relativity to a few millionths of its path. An earlier model ran into this at its
own seams, with light past a moving Jupiter off by seconds of arc ([One Time or Many](../appendix-b/one-time-or-many.md)). (The kilometre or so left is tens of
thousands of times smaller than the failures; it may be the next order, and wasn't chased.)

## In other frames of reference

Is the seam always in the same place? It depends on what moves.

**The bodies and their space moving together.** This is how [Part 3](../part3/dynamic-models.md) moves bodies: each
carries its flow with it. Seen from a frame in which the pair moves at a steady velocity, the whole flow is the flow at
rest plus that velocity. Nothing changes but the frame, and the seam moves with the bodies, unchanged.

**The bodies moving through space that is at rest far away.** Now, in the bodies' frame, space streams past. The
observers whose paths the flow follows, falling from rest far away, now arrive from one direction rather than from
every direction. That is a different family of observers, a different way of setting clocks in the same spacetime, and
its seams are elsewhere. Even a single body has one.

![Left: one body with observers falling straight in from every direction, along straight lines; there is no seam. Right: one body with observers arriving from rest far away on the left, on parabolas that come round the body; blue ones come round above it and red ones below, and they meet on a dashed half-line running from the body directly away from where they came from: their seam](images/seamframes.svg)

For one body, observers arriving from rest far away along one direction travel on parabolas round it. With
$\hat{\mathbf n}$ pointing the way they come from, their $S$ is $2\sqrt{GM(r + \hat{\mathbf n}\cdot\mathbf x)}$, against the model's $2\sqrt{2GMr}$; both give space the escape speed
everywhere, and both have no swirl. But for these observers, every point behind the body is passed by one that came
round above it and one that came round below, and the time switches from one to the other on the half-line behind the
body. Across it, the flow's sideways part reverses: a seam, round a single body.

<iframe src="../../viewer/index.html?player&run=../runs/seams/observers.full.json" width="100%" height="520" loading="lazy" title="Observers arriving from one side, round one body"></iframe>

*Observers arriving from rest far away on the left, on parabolas round one solar mass: coming round above it (blue) and
below it (orange). They cross on the half-line behind the body (pink, dashed), where the time switches from one family
to the other.*
[Open full screen](../../viewer/index.html?run=../runs/seams/observers.full.json){ target=_blank }

So a seam belongs to the observers chosen to set the clocks, not to the bodies. The model's single body has none only
because its observers fall straight in from every direction. (For two bodies with space streaming past, the observers'
paths cross many times, and the seams are too tangled for the simulation to map cleanly. All that can be said is that
they aren't the seam of the bodies at rest.)

## What a seam means

### Space made at the seam

Between two bodies, the flow runs away from the seam on both sides. So, read as a flow of space, the seam is a sheet
where space appears. How much? Round two solar masses 200,000 km apart, at rest, in flat space, with the flow turned
round the line through the bodies into three dimensions:

| | Within a sphere of radius | Space made at the seam (m³/s) | Space lost through the volume (m³/s) | The seam's share |
| --- | --- | --- | --- | --- |
| two solar masses, $D$ = 200,000 km | 0.6 $D$ | 1.5 × 10²³ | 3.8 × 10²³ | 40% |
| | 1 $D$ | 3.2 × 10²³ | 1.0 × 10²⁴ | 32% |
| | 10 $D$ | 3.7 × 10²⁴ | 2.9 × 10²⁵ | 13% |
| the Sun and the Earth | 1 AU | 2.1 × 10²⁵ | 1.1 × 10²⁸ | 0.2% |

Space is lost through the volume because the flow converges everywhere: even round a single body, space flowing in
squeezes together, $\nabla\cdot\mathbf u = -\tfrac32|\mathbf u|/r$, and the body, a point, takes in none of it. So
space was never conserved in the model, seam or no seam. The seam adds a source to a flow that already has sinks
everywhere.

But the amount isn't a property of anything measurable. Moving the seam (by the constant of the last section) changes
what it makes within one $D$ from 3.24 to 3.05 × 10²³ m³/s, by 6%, and no path changes at all. A different family of
observers gives even a single body a seam, with space appearing on it. Nothing that light or matter does can tell how
much space a seam makes, or whether it makes any.

### No conservation law broken

What crosses the seam keeps its energy, to the arithmetic's precision, and follows general relativity's path. Nothing
is created or lost that a measurement could find. The space made at the seam is in the flow's bookkeeping, not in
the world.

### A fold in time

What the seam is, then, is a fold in the flow's time. The flow's moments, its surfaces of constant $T = t + S/c^2$, take
$S$ from one body on one side of the seam and from the other on the other side, so each moment has a crease along the
seam:

![Space across, time up. Two bodies are still, so their world lines are vertical. The flow's moments, surfaces of constant T, are drawn as curves across: each rises towards each body, and dips to a sharp crease at the seam, half way between, where it switches from one body's S to the other's](images/seamfold.svg)

The spacetime itself is smooth at the seam: nothing there is different from anywhere else. Only the way the clocks are
set has a crease in it. The flow is the motion of the observers who set those clocks, two families of them, one falling
towards each body, and at the seam the model hands over from one family to the other. Seen as space, that handover
looks like space appearing; seen as clocks, it is a change of reference clock, and the crossing rule is what that
change does to a moving thing's momentum.

This answers the question the [Hollow Sphere](hollow-sphere.md) left open, of where the space at such a boundary comes
from or goes: it is the flow's account of a change of observers, and it has no effect that could be measured.

## In brief

| Question | Answer |
| --- | --- |
| Why is there a seam? | Every point is on two paths of things falling from rest far away, one into each body; the flow must follow one, and can't turn round smoothly between the bodies |
| Where is it? | Where the two bodies' $S$ are equal, up to a constant; the engine's constant puts it through the point where $g = 0$ |
| Could it be elsewhere? | Yes: any constant works, and moving it 23,000 km changes no path |
| What happens crossing it? | The crosser keeps its energy and its momentum along the seam, which to first order keeps its velocity; paths match general relativity's to a few parts in 10⁸ |
| Without the rule? | Paths kink, light by up to 10⁻², particles by up to 0.3 rad |
| What makes a seam? | The two times must agree on it, the rule must use the direction of the flow's jump, and each body must stay in its own region |
| Only at seams? | No: the rule works on any boundary between two ways of setting clocks, under the same conditions |
| In other frames? | It moves with bodies that carry their space; observers arriving from one direction put seams elsewhere, even round one body |
| What is it? | A fold in the flow's time, where it hands over from one body's observers to the other's; the space it appears to make is bookkeeping, and no conservation law is broken |

*The code: studies/seam_crossing.py (paths crossing), studies/seam_energy.py (energy), studies/seam_rules.py
(placement, and the rule away from seams), studies/seam_moving.py (a moving body), studies/seam_frames.py (other
observers), studies/seam_space.py (space made at the seam), studies/seam_players.py (the players on this page).*
