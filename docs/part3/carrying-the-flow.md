# Carrying the Flow

Part 2 built its flow for bodies held still. The first question with the bodies moving is the simplest: what happens
to a body's flow when the body moves?

## The test: a ball beside the moving Earth

The obvious answer is that the flow's pattern goes with the body: wherever the Earth is now, space falls straight in
towards it, as round the Earth at rest. The pattern is *taken along*, but the space itself doesn't move with the Earth.

That fails at once. Let a ball go at rest beside the Earth, 100 km up, and follow it as the Earth moves at its
orbital speed, 29.8 km/s. Seen from the Earth, the ball should fall straight down, as it does round an Earth at rest:
motion at a steady speed changes nothing that can be measured nearby. Instead the balls drift sideways, by up to 575 km
in two and a half minutes, and Newton's $g$ beside the Earth is out by 26–52 m/s², several times $g$ itself.

## The model: the space moves with the body

![Two panels, each seen from the Earth, which moves up the page at V. Left, the flow's pattern taken along: the space streams down past the Earth, bent in towards it, and a ball let go at rest beside the Earth is thrown forward and over the top. Right, the space carried: from the Earth, space falls straight in from every side, and the ball falls straight down](images/carrying.svg)

The fix is that a body carries its space with it, not just the pattern. The space round the Earth moves at the
Earth's velocity, $\mathbf V$, plus its fall towards the Earth:

$$
\mathbf u = \mathbf V + \mathbf u_\text{Earth}
$$

Seen from the Earth, that is exactly the flow round an Earth at rest, as it has to be: moving at a steady speed is
only a change of frame.

<iframe src="../../viewer/index.html?player&run=../runs/movingBodies/multiBody_moving.full.json" width="100%" height="600" loading="lazy" title="Balls let go beside the moving Earth"></iframe>

*Balls let go at rest one Earth radius above the moving Earth, from eight places round it, seen from the Earth, until
they land. Orange: the flow's pattern taken along; the balls are thrown off, some forward over the top, some away
altogether. Blue (dashed): the space carried with the Earth; every ball falls straight down and lands after 35
minutes. The background is the space as the Earth sees it (the Background menu has both).*
[Open full screen](../../viewer/index.html?run=../runs/movingBodies/multiBody_moving.full.json){ target=_blank }

| Test, the Earth moving at 29.8 km/s | Pattern taken along | Space carried |
| --- | --- | --- |
| A ball let go 100 km up | drifts up to 575 km sideways | falls 100.6 km straight down in 145 s, from every side |
| Newton's $g$ beside the Earth | out by 26–52 m/s² | to 2 × 10⁻⁸ m/s² |
| Clocks at rest on the Earth, one pulsing to another | out by 3.7 parts in 10⁹ | to 2 parts in 10¹⁵ |

## Two bodies going round each other

With the Sun as well, each body has to carry its own flow. The Earth goes round the Sun on a circle, so there is one
frame where the pair are both still: a frame turning with them, once a year. In that frame the flow doesn't change
with time, and the potential flow of Part 2 can be built in it: the *turning flow*. Each body's region of space now
goes round with it.

There is one thing to choose. In the turning frame, the paths that the flow follows all share one constant, the energy
they have in that frame, called $J$ (Jacobi's constant, after the mathematician who found it for the same paths). It
is chosen so that the Earth's own flow is just its own, as if the Sun weren't there.

| Test | Expected | The turning flow |
| --- | --- | --- |
| Newton's $g$ at the moving Earth's surface | Newton's | to 9 × 10⁻⁵ m/s², the accuracy of the flow's tables |
| Lunar laser ranging: the term following the Moon's angle from the Sun | (2.8 ± 4.1) mm | 1.8 × 10⁻⁸ m |

The second line is worth noticing. Part 2's potential flow, with the bodies held still, failed lunar laser ranging by
11 cm: the Sun's potential got into the speed of the Earth's flow. The turning flow passes it without curving space,
because the Earth's flow is now the Earth's own.

## Where it stops

The constant chosen for the Earth is wrong for the Sun. It fails the next test, light grazing the Sun, which is where
[Curving the Turning Flow](curving-the-turning-flow.md) begins.

*The code: studies/moving_bodies.py (the ball and the clocks beside the moving Earth), studies/turning_eikonal.py (the
turning flow); the flow: engine/turning.py.*
