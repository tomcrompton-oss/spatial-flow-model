# Rotating Black Holes

!!! note "Reader's note"
    This page is taken from Andrew Hamilton and Jason Lisle's paper
    [*The river model of black holes*](https://arxiv.org/abs/gr-qc/0411060), American Journal of Physics 76, 519
    (2008). The summary below keeps to its main ideas; the paper has the mathematics.

## The river model

Hamilton and Lisle describe a black hole as space flowing, like a river, through a flat
background. For a hole that doesn't spin, the river flows straight in at the Newtonian escape speed,
$\sqrt{2GM/r}$. It reaches the speed of light at the horizon and goes faster inside it. Anything in the river moves
through it by the rules of special relativity, never faster than light relative to the space it is in. They picture
light as fish swimming hard against the current: outside the horizon they can make headway, but inside it the river
beats every fish and carries it in. This is the picture of
[Black Holes](black-holes.md), and it is general relativity's Schwarzschild geometry, written in
Gullstrand–Painlevé coordinates.

A fish doesn't feel the river's speed, only how it changes from place to place: one carried along with the river sees
no change at all. As a fish swims, the differences in the river's velocity between where it is and where it goes give it
a series of small relativistic boosts, and those boosts are its motion under gravity.

This is the same description of flowing space that we have produced.

## A spinning hole

The surprising part is a spinning hole, described by general relativity's Kerr geometry. It had been thought that a
spinning hole could have no river picture at all, because its space can't be sliced flat the way a non-spinning hole's
can. You might expect its river to
swirl, spiralling in like water down a plughole. It doesn't. Written in coordinates found by Chris Doran in 2000, the
Kerr river still flows straight in, with no swirl at all. What it has instead is a **twist**.

![A spinning hole seen from above its equator: the river's arrows point straight in, with no swirl; small green arcs show its twist, turning whatever it carries round with the spin, more strongly close in; a dashed circle marks the horizon, and a fainter dashed circle outside it the ergosphere](images/twister.svg)

At each point the river has not only a velocity but a rotation. A fish carried in it is boosted by changes in the
river's velocity, as before, and also turned by changes in its twist. Velocity and twist together make six numbers
at each point, three for the boost and three for the rotation, and that one field describes everything about the
spinning hole. Unlike the non-spinning case, space at one moment is no longer flat: it is sheared. The twist and the shear go
together, each needing the other, and between them they keep a small falling frame moving with the things around it.
The background the river flows through is still flat, but in a subtler sense: the river's whole effect on a fish
comes from the plain differences in its velocity and twist from place to place, as if measured with an ordinary ruler.
The authors suggest this is a special property of black holes that don't change with time.

Two surfaces mark a spinning hole:

- **The horizon**, where the river falls in at the speed of light, as before. It is smaller than a non-spinning
  hole's of the same mass.
- **The ergosphere**, outside the horizon. Inside it nothing can hold still as seen from far away: everything is
  dragged round with the spin, though it can still escape.

## The flow model's version

The simulations here use Hamilton and Lisle's river in the hole's equatorial plane (the code is `engine/kerr.py`).
Something moving through the river is boosted by the change in its velocity and turned by the change in its twist,
exactly as the paper describes. For a hole of 4 million solar masses spinning at 0.9 of the most it can, it matches
exact Kerr (distances in $r_s = 2GM/c^2$, the Schwarzschild radius of a hole of the same mass):

| Test | Going round with the spin | Against the spin | No spin |
| --- | --- | --- | --- |
| Light passing at 6 $r_s$: bend | 23.4° | 30.5° | 26.4° |
| An orbit from 20 $r_s$: its closest point moves on, each orbit | 37° | 74° | about 50° |
| The model against exact Kerr | 2 parts in 10⁵ (light), 2 in 10⁴ (orbits) | the same | |

Leave the twist out and the results are wrong: light bends a few per cent too much or too little, and the orbit
against the spin falls into the hole.

### Orbits

Three orbits, starting at the same place and speed: going round with the spin (blue), against it (red), and round a
hole with no spin (grey). The markers are each orbit's closest and furthest points.

<iframe src="../../viewer/index.html?player&run=../runs/kerrPaths/kerrPaths_orbits.full.json" width="100%" height="520" loading="lazy" title="Orbits round a spinning black hole"></iframe>

*The hole turns the way it spins (not at its real speed). Grey arrows: the river, flowing straight in. Green arcs: the
twist, how fast the river's twist turns something falling straight in through it, the way it is turned. Zoom in on the
hole to see its horizon (dotted circle) and ergosphere (dashed). In full screen, tick "colour map" to see the twist
itself.*
[Open full screen](../../viewer/index.html?run=../runs/kerrPaths/kerrPaths_orbits.full.json){ target=_blank }

Going round with the spin, the orbit's closest point moves on by less than round a hole with no spin; against it, by
more. The spinning hole drags the orbit round with it.

### Light

Light passing the hole at 6 and 15 $r_s$, on the side going round with the spin (blue) and against it (red), with
the same rays past a hole with no spin (grey, dashed).

<iframe src="../../viewer/index.html?player&run=../runs/kerrPaths/kerrPaths_light.full.json" width="100%" height="520" loading="lazy" title="Light passing a spinning black hole"></iframe>

*Light going round with the spin bends less than past a non-spinning hole; light going against it bends more.*
[Open full screen](../../viewer/index.html?run=../runs/kerrPaths/kerrPaths_light.full.json){ target=_blank }

*The code: studies/kerr_paths.py (the players) and studies/kerr_comparison.py (the comparison with exact Kerr).*
