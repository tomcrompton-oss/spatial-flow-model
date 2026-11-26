# Curved Space

The [potential flow](potential-flow.md) passes every test at Newton's level, and keeps clocks at general relativity's
rates. This page starts with the first test it fails, and the change that fixes it: space that is no longer flat.

## The test: lunar laser ranging

Lunar laser ranging measures the distance to the Moon to millimetres, by timing laser pulses to reflectors left on its
surface. In general relativity, the Sun changes the Earth–Moon distance only through its tide, by less than a
micrometre. Any effect that follows the Moon's angle from the Sun as it goes round each month is tightly measured: it
is (2.8 ± 4.1) mm (Williams, Turyshev and Boggs, 2004).

![Lunar laser ranging: laser pulses from the Earth to the Moon and back, the Moon at angle D from the direction of the Sun, 1 AU away. A dashed seam between the Earth's region of the flow and the Sun's crosses the Moon's orbit about 60 degrees either side of the Sun's direction; on the Sun's side of it, in flat flowing space, the range comes out shorter](images/lunarranging.svg)

The simulation runs the same measurement in the potential flow: radar from the Earth's surface to a mirror at the
Moon's distance and back, with the Sun held 1 AU away, at each angle of the Moon from the Sun, against the same with
the Earth alone.

<iframe src="../../viewer/index.html?player&run=../runs/multiBodyPN/multiBody_lunar.full.json" width="100%" height="440" loading="lazy" title="The extra lunar range by the Moon's angle from the Sun"></iframe>

*The extra lunar range (m) the Sun's potential makes in the potential flow, by the Moon's angle from the Sun.*
[Open full screen](../../viewer/index.html?run=../runs/multiBodyPN/multiBody_lunar.full.json){ target=_blank }

Most of the extra 3.6 m is constant, and would disappear into the Earth's measured mass. But part of it follows the
Moon's angle from the Sun: an 11 cm term, shorter when the Moon is on the Sun's side. That is 27 times lunar laser
ranging's uncertainty.

The cause is the Sun's potential. It goes into the speed of space round the Earth as well as the Earth's own: at the
Earth's surface space falls at 43.6 km/s, not 11.2. In general relativity a uniform potential like the Sun's changes
nothing that can be measured nearby. In flat flowing space it stretches distances round the Earth by about 1 part in
10⁸, and by a different amount depending on which way the flow points, which changes as the Moon goes round.

## Space stretched across the flow

The fix keeps everything that works. Clocks are still slowed only by their speed through space, so Part 1's
mechanism is untouched; space still flows as the potential flow. What changes is that space is no longer flat.
Across the flow it is stretched, by $u^2/c^2$; along the flow, lengths are as before:

$$
\gamma = \delta + \frac{u^2\,\delta - \mathbf u\,\mathbf u}{c^2}
$$

![Small circles of space round two bodies at rest, each stretched across the potential flow and not along it, more strongly where the flow is faster, close to the bodies. A key enlarges one: the dashed circle of flat space, and the ellipse it becomes, stretched across the flow by u squared over c squared and unchanged along it; the stretch is much exaggerated](images/stretched.svg)

Compared with across the flow, space along it is shorter by $u^2/c^2$: the same amount as special relativity's
length contraction for something moving at the flow's speed, to this order. Moving space is contracted along its
motion, compared with across it.

This isn't a guess. Take general relativity's description of bodies at rest, and measure time by clocks falling from
rest far away, as the flow model does. To the first order beyond Newton (first post-Newtonian order), what comes out
is exactly this: clocks slowed only by their speed through space, space flowing as the potential flow (very slightly
slower, by a quarter of $u^2/c^2$), and space stretched across the flow by $u^2/c^2$. The flow's speed says how much, its direction which way, and nothing else goes
in.

For a single body, this curved space is flat space in other coordinates. Part 1 is unchanged: every result there
still stands. With two bodies it isn't flat, and the stretch is where the bodies' effects on each other go.

Light sees why it works. For light, the stretch across the flow and the flow itself combine so that space looks the
same in every direction: only the flow's speed counts, not which way it points. The Sun's potential then changes the
speed of light round the Earth evenly, in every direction, which changes no distance that can be measured nearby.

## Lunar laser ranging again

The same radar to the Moon's distance, in flat flowing space, in the potential flow with space stretched across it,
and in general relativity:

<iframe src="../../viewer/index.html?player&run=../runs/lapseTwoBodies/lapseTwoBodies_lunar.full.json" width="100%" height="440" loading="lazy" title="Lunar range: flat space, curved space and general relativity"></iframe>

*The extra lunar range (m) by the Moon's angle from the Sun: flat space (red), space stretched across the flow
(blue), and general relativity (grey, dashed), which lies exactly on the blue.*
[Open full screen](../../viewer/index.html?run=../runs/lapseTwoBodies/lapseTwoBodies_lunar.full.json){ target=_blank }

| Model | The term following the Moon's angle | Its difference from general relativity |
| --- | --- | --- |
| Potential flow, flat space | −0.1112 m | −0.1208 m |
| Potential flow, space stretched across it | +0.0096 m | 0.0000 m |
| General relativity (first post-Newtonian) | +0.0096 m | |
| Measured | | (2.8 ± 4.1) mm |

*(General relativity's own +9.6 mm comes from the mirror being held at a fixed distance in these coordinates; what the
measurement tests is each model's difference from it.)* With space stretched across the flow, the range is general
relativity's.

## Light past Jupiter

A second test fails in flat space for the same reason. Radio telescopes measure the positions of distant sources
near Jupiter to better than 10 microarcseconds. In general relativity, light passing Jupiter, with the Sun 5.2 AU
away, bends by the Sun's bending plus Jupiter's: the two simply add, to first order. In flat flowing space they
don't.

![Light from a distant source passing close to Jupiter, bent slightly towards it, and light from a reference source far from Jupiter, both reaching radio telescopes on the Earth, which measure the angle between them; the Sun is 5.2 AU away. In general relativity the bending with the Sun and Jupiter together is each one's bending added; in flat flowing space it is 300 to 400 microarcseconds more](images/jupiterlight.svg)

Each model's bending with both bodies, less its bending with each alone:

| Model | Light passing 1 Jupiter radius out | 10 radii | 100 radii |
| --- | --- | --- | --- |
| Potential flow, flat space | +408 µas | +397 µas | +312 µas |
| Potential flow, space stretched across it | +0.35 µas | −0.04 µas | −0.09 µas |
| General relativity (first post-Newtonian) | +0.25 µas | −0.01 µas | −0.08 µas |
| Measured | | positions to under 10 µas | |

In flat space the mismatch is 40 times what radio telescopes would see. With space stretched across the flow, it
matches general relativity to a fraction of a microarcsecond.

## Back to the hollow sphere

The [Hollow Sphere](hollow-sphere.md) left a small complication: the faller's clock across the inside read 5.4% more
than general relativity says, whichever way space flowed. That came from flat flowing space too. Observers held still
in space flowing past them measure distances along the flow stretched, by $1/\sqrt{1 - u^2/c^2}$, so the inside of the
shell measures longer than its true diameter.

Curved space removes it. Give the space inside the shell the same shape as above, shorter along the flow than across
it by $u^2/c^2$, so that observers held still inside measure the shell's true diameter, $2R$. The simulation's faller
then crosses the inside in 0.000591234 s of its own time: general relativity's figure, to 7 parts in 10⁸, against
flat space's 0.000623216 s.

## Where it stops

With the bodies held still, the potential flow with space stretched across it passes every test so far: Newton's
gravity, the clocks, lunar laser ranging and light past Jupiter, all as general relativity has them at first
post-Newtonian order. Every test so far has held the bodies still, though. Real bodies move, and the next tests need
them to.

*The code: studies/lapse_two_bodies.py (lunar ranging and light past Jupiter, flat and curved, against general
relativity's first post-Newtonian metric), studies/hollow_sphere_curved.py (the hollow sphere); the curved-space
engine: engine/metric.py.*
