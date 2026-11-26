# Hollow Sphere

Two bodies are hard to think about all at once. A simpler case has the same problem at its heart: a hollow sphere, a
thin shell of matter with nothing inside it. It has a place where nothing pulls but the potential is deep, just like
the point midway between two bodies, and it is simple enough to work through. So we will use it as a way into the two
body problem.

![A hollow shell of mass M and radius R. Outside, space falls in towards it, as round a single body. Inside, there is no pull (g = 0), and the escape speed is the surface's, but which way space should flow is a question mark. On the right, the potential along a line through the centre: −GM/r outside, and flat at −GM/R everywhere inside](images/hollowsphere.svg)

## No pull inside

Outside the shell, gravity is exactly as if all its mass were at the centre. Inside, there is no gravitational pull at
all, anywhere: the pulls of the near side and the far side of the shell cancel exactly, wherever you are. Newton proved
both in the *Principia* (1687, Book I, Propositions 70 and 71).

So the potential inside is the same everywhere, $-GM/R$, the value at the surface. Something let go at rest anywhere
inside stays where it is.

## So, no flow?

With no pull inside, one might expect no gravitational effects there at all. No pull would mean no time dilation, and
in flowing space, clocks are slowed only by their speed through space, so no time dilation would mean no flow: space
inside the sphere simply at rest.

## But there is an escape speed

Yet something inside the sphere still has to work to get away. Reaching the surface costs nothing, because nothing
pulls inside. But from the surface it still needs the surface's escape speed, $\sqrt{2GM/R}$. So the escape speed is
the same everywhere inside the sphere as at its surface.

In flowing space, the escape speed *is* the speed of space. So space inside the sphere should be moving, at
$\sqrt{2GM/R}$, everywhere. That gives a speed, but not a direction. Nothing inside the sphere pulls any way, and
every direction is the same as every other.

## What general relativity says

General relativity agrees with Newton that nothing pulls inside the shell; space inside is not curved. But clocks
inside run slow, all at the same rate as a clock held still on the surface,

$$
\frac{d\tau}{dt} = \sqrt{1 - \frac{r_s}{R}}, \qquad r_s = \frac{2GM}{c^2}
$$

So in flowing space, space inside the sphere can't be at rest. It must be moving at the surface's escape speed, even
though nothing pulls.

## Falling through

Take something let go from rest far away, falling straight towards the sphere and through a small hole in its shell.
Outside, it falls with the space, speeding up as it goes, just like [clock 2](../part1/mechanics/four-clocks.md#clock-2-falling-in-from-far-away)
of Part 1. It reaches the shell at the surface's escape speed. Inside, nothing pulls, so it crosses at that same speed.
It leaves through a hole on the far side, slows as it climbs away, and comes to rest far away on the other side.

The question is what the space inside the sphere is doing as it crosses. To keep it simple, look only along the
faller's line, so that space can only flow one way or the other along it. Inside, it must move at the surface's
escape speed, for the clocks. It must also move at the *same* speed throughout each part of its path, because space
moving steadily has no acceleration, and there is no pull inside.

That leaves four possibilities:

![Five rows along the line through the sphere. The faller moves left to right: speeding up towards the sphere, crossing it at a constant speed, slowing beyond it. In each of the four options space outside flows in towards the sphere from both sides. A: inside, space flows the way it came in, left to right, and meets the space coming in from the far side head on at the far surface. B: inside, it flows right to left, as on the far side, and meets the incoming space head on at the near surface. C: inside, it flows towards the centre from both sides, and the two halves meet head on at the centre. D: inside, it flows out from the centre in both directions, splitting apart at the centre and meeting the incoming space head on at both surfaces](images/shelloptions.svg)

- **A: inside, space carries on as it came in.** The faller moves with its space all the way across. But at the far
  surface, the space crossing the sphere meets the space flowing in from that side head on.
- **B: inside, space flows as it does on the far side**, against the faller. It matches the far side, but meets the
  incoming space head on at the near surface.
- **C: space flows towards the centre**, from both sides. Each half matches the space outside it, but the two halves
  meet head on at the centre.
- **D: space flows out from the centre**, both ways. The two halves split apart at the centre, and meet the incoming
  space head on at both surfaces.

Each one has space moving at the right speed everywhere inside, so the clocks run as general relativity says, and each
has no acceleration inside, so nothing pulls. None of them is picked out by the symmetry of the sphere. And the sphere
has no special line at all: the same choice faces every line through it.

## Following the faller through

The simulation follows the faller through a shell of one solar mass with a radius of 10 Schwarzschild radii, about
30 km, where space inside flows at $0.316c$. The faller arrives moving with its space, as something that has fallen
from rest far away does, and each of the four options is tried in turn.

### Carried with the space

At first, none of them gets the faller through.

<iframe src="../../viewer/index.html?player&run=../runs/hollowSphere/hollowSphere_smooth.full.json" width="100%" height="480" loading="lazy" title="Falling into a hollow sphere: carried with the space"></iframe>

*Distance across, the flow's time up; the grey lines are the shell's walls. A (blue) crosses the inside and stops at
the far wall; B (red) and D (amber) stop at the near wall; C (green) stops at the centre.*
[Open full screen](../../viewer/index.html?run=../runs/hollowSphere/hollowSphere_smooth.full.json){ target=_blank }

The faller arrives at rest in its space, so it simply goes wherever its space goes. Wherever space meets itself head
on, the flow has to slow to a stop and turn round, and the faller is carried into that point and stays there. It
doesn't help to make the shell sharp, or to take larger steps: the faller is never moving *through* the boundary, only
being carried up to it, and once past it, the space on the other side carries it back.

### Changing reference frame

The boundaries where space meets itself are a special case. Crossing one isn't the ordinary step of moving between
regions of space: the faller changes reference frame. It passes through the boundary keeping its velocity relative to
the boundary, which is at rest, and carries on in the space on the other side. At the far wall in option A, it has been
moving with the space inside; beyond it, the space flows back in towards the sphere, so the faller is now moving
outward *against* the flow, just like [clock 4](../part1/mechanics/four-clocks.md#clock-4-escaping), and it climbs away
and slows.

Its reference clock changes too. Falling in from far away on the left, its time was measured against a clock far away
on the left. Heading out to the right, it is measured against a clock far away on the right. Both are at rest in still
space, and nothing about the shell changes with time, so both keep the same time: the flow's time.

(Strictly, it keeps its velocity relative to the boundary, added relativistically to the space on each side. At the
far wall in A that makes its speed through the space outside $2u_R/(1 + u_R^2/c^2)$, the same as an escaping clock
thrown up from the surface.)

<iframe src="../../viewer/index.html?player&run=../runs/hollowSphere/hollowSphere_boundary.full.json" width="100%" height="480" loading="lazy" title="Falling through a hollow sphere: changing reference frame"></iframe>

*The same four options, the faller changing reference frame wherever space meets itself. All four now pass straight
through and climb away on the far side.*
[Open full screen](../../viewer/index.html?run=../runs/hollowSphere/hollowSphere_boundary.full.json){ target=_blank }

| Option | In to the shell (s) | Across the inside: its clock (s) | Across the inside: the flow's time (s) | Out to the same distance (s) | The whole trip: its clock (s) |
| --- | --- | --- | --- | --- | --- |
| A | 0.002845382 | 0.000623216 | 0.000623216 | 0.002845382 | 0.006313980 |
| B | 0.002845382 | 0.000623216 | 0.000761708 | 0.002845382 | 0.006313980 |
| C | 0.002845382 | 0.000623216 | 0.000692462 | 0.002845382 | 0.006313980 |
| D | 0.002845382 | 0.000623216 | 0.000692462 | 0.002845382 | 0.006313980 |
| General relativity | 0.002845382 | 0.000591234 | | 0.002845382 | 0.006281999 |

*(From 6 shell radii out on one side to 6 on the other. The legs in and out agree with general relativity to a few
parts in 10⁹.)*

As seen from outside, the faller takes longer to cross the inside where space flows against it: it moves more slowly
through the coordinates. But there it is moving faster through its space, so its clock runs slower, by exactly the same
factor. Its own clock reads the same in all four, and the whole trip is the same in all four. The faller can't tell
them apart.

### A clock held still inside

What about a clock held still inside the sphere? All we know directly is about the faller. In option A it moves with
its space all the way in, so, like [clock 2](../part1/mechanics/four-clocks.md#clock-2-falling-in-from-far-away), it
keeps the same time as the clock far away it fell from. Inside, it passes the stationary clock at the escape speed,
$u_R$. By special relativity, the faller sees the stationary clock running slow, at $\sqrt{1 - u_R^2/c^2} =
\sqrt{1 - r_s/R}$ of its own rate, and so of the remote clock's. So the stationary clock is time dilated just as
special relativity predicts for that speed, which is general relativity's time dilation inside the shell.

Inside the sphere space is flat, so there is no preferred frame of reference there: nothing inside says which clock is
"really" at rest. But frames inside can be connected to frames outside. The faller's frame is the one it carried in
from far away, and the stationary clock's is the shell's, at rest relative to clocks far away. Through those
connections, a clock inside is compared with a clock outside.

!!! note "Reader's note"
    The faller's clock across the inside, 0.000623216 s, is 5.4% more than general relativity's 0.000591234 s. That
    is a small additional complication, the same in all four options, and we will return to it in
    [Curved Space](curved-space.md).

*The code: studies/hollow_sphere.py.*
