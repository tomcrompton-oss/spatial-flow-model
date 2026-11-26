# Curving the Turning Flow

The [turning flow](carrying-the-flow.md) carries each body's space with it, and passes Newton's gravity round the moving
Earth and lunar laser ranging. This page starts with the test it fails.

## The test: light grazing the Sun

The Cassini spacecraft, on its way to Saturn, measured how much radio signals passing close to the Sun were delayed
and bent. It confirmed general relativity's bending to 2 parts in 10⁵: for light grazing the Sun at 2 solar radii, to
about 0.01 milliarcseconds.

![A radio signal from a spacecraft passes 2 solar radii from the Sun's centre on its way to the Earth. Undeflected it would go straight on; general relativity bends it towards the Sun by 870 milliarcseconds; the turning flow bends it 9.6 milliarcseconds less. The bends are exaggerated](images/grazing.svg)

The simulation sends light past the Sun in the turning flow, with the Earth going round, and compares its bending
with general relativity's:

| Light passing the Sun at | General relativity | The turning flow | Short by |
| --- | --- | --- | --- |
| 2 solar radii | 870.48 mas | 860.88 mas | 9.60 mas |
| 10 solar radii | 174.09 mas | 164.50 mas | 9.59 mas |
| 50 solar radii | 34.37 mas | 25.11 mas | 9.25 mas |

At 2 solar radii it is 1% short: a thousand times what Cassini allows.

## Why: the constant chosen for the Earth

The turning flow's paths share one constant, chosen so that the Earth's flow is its own. But the Sun's flow follows
paths with the same constant. Round the Sun they leave it with no spin, so their energy is that constant, not zero, and
space round the Sun falls a little slower than its escape speed: $u^2 = 2GM/r + 2J$, with $J$ below zero. The Sun's
space is squeezed, and light passing through it is bent less, by the same amount at every distance.

![A graph of the speed of space squared against distance from the Sun. A dashed curve shows the escape speed squared, 2GM/r; a solid curve, the turning flow's, lies below it by the same amount, 2J, everywhere, and reaches zero at two thirds of an astronomical unit, where the Sun's flow stops](images/squeeze.svg)

The constant also limits how far the Sun's flow reaches. A path leaving the Sun with that energy can't get further
than two thirds of an astronomical unit. The flow's own paths show it, traced out from each body in the frame turning
with them:

<iframe src="../../viewer/index.html?player&run=../runs/turningEikonal/turning_paths.full.json" width="100%" height="520" loading="lazy" title="The turning flow's paths out of the Sun and the Earth"></iframe>

*The turning flow's paths traced out from each body, in the frame turning with them: from the Sun (blue), turning
back two thirds of the way to the Earth; from the Earth (orange), reaching well past the region the Earth's gravity
rules. The arrows are the flow in that frame.*
[Open full screen](../../viewer/index.html?run=../runs/turningEikonal/turning_paths.full.json){ target=_blank }

## The model: curved space again

Part 2 met the same kind of trouble with bodies at rest, and fixed it with [curved space](../part2/curved-space.md):
space stretched across the flow by $u^2/c^2$. The same fix works here, applied to the turning flow. The stretch is
measured from the flow relative to the body it belongs to, so that it is the same in every frame.

| Light passing the Sun at | The turning flow, flat | The turning flow, space curved | Cassini allows |
| --- | --- | --- | --- |
| 2 solar radii | 9.60 mas short | 0.0012 mas over | 0.01 mas |
| 10 solar radii | 9.59 mas short | 0.0019 mas over | |
| 50 solar radii | 9.25 mas short | 0.014 mas over | |

Light, in curved space, sees only the flow's speed, not which way it points, and the constant in $u^2$ then changes
the speed of light round the Sun evenly, which bends nothing. What is left at 2 solar radii is a tenth of Cassini's
limit.

## Where it stops

Light now passes, and so does Newton's gravity round the moving Earth. Every test so far has looked at light, or at
things held near the Earth. The next looks at something that goes round the Earth for months: the Moon. That is where
[One Potential](one-potential.md) begins.

*The code: studies/lapse_moving.py (light past the Sun, flat and curved, against general relativity's first
post-Newtonian metric), studies/turning_eikonal.py (the flow's paths).*
