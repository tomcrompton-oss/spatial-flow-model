# Moving With Its Own Space

[Each body in the others' flow](each-body-in-the-others-flow.md) left each body's own flow out, and failed three tests
for comparable masses: the binary's orbit turned 17% too fast, its centre accelerated by itself, and a falling pair
fell differently from a single body. This page keeps each body's own flow.

## The model: a body moves with the space round it

![Left, a body moving at v, and its own inflow round it, the same from every side: the flow round the body is the two together. Right, the same averaged over a small circle round the body: the inflow, the same from every side, cancels, and what is left is the body's own velocity](images/ownspace.svg)

The flow is [one potential](../part3/one-potential.md) for the whole plane, as in Part 3, with each body's own flow in
it. Close to a body, the flow is the body's velocity plus its own inflow, the same from every side. Averaged over a
small sphere round the body, the inflow cancels, and what is left is the body's velocity and the other bodies'
pull. So the rule is: **a body moves with the space round it, averaged over a small sphere.**

!!! note "Reader's note"
    This isn't a new rule. It is how general relativity's own equations for two bodies are worked out: each body
    moves along the paths of the whole spacetime, with the parts of the field that blow up at the body itself averaged
    away over a small sphere round it. The averaging is called Hadamard's *partie finie* (finite part). For a body
    that is a sphere, its size and structure then drop out, at the first order beyond Newton, so a point mass is as
    good as a star. See, for example, L. Blanchet, *Gravitational radiation from post-Newtonian sources and inspiralling
    compact binaries*, Living Reviews in Relativity. Nothing later depends on the details.

A first check, with the Earth going round the Sun in Part 3's one potential: in the frame turning with them, where the
Earth is at rest, the flow round the Earth streams at about 52 km/s. Averaged round a circle about the Earth:

| Circle's radius | The flow's average round it |
| --- | --- |
| 1,000 km | 2 × 10⁻¹⁰ m/s |
| 10,000 km | 1 × 10⁻⁹ m/s |
| 100,000 km | 1 × 10⁻⁶ m/s |
| 300,000 km | 3 × 10⁻⁵ m/s, the Sun's tide |

So the Earth, at rest in that frame, moves with its own space.

## The test: a binary's orbit turning

For two bodies on circles the rule can be worked out exactly, by computer algebra rather than by running the orbit:
each body's acceleration in the model's spacetime, its own field averaged away. The simplest number to compare is
how fast the pair goes round, for a given separation $a$. Newton gives $\omega^2 = GM/a^3$, with $M$ the total mass.
The first order beyond Newton adds a small correction, set by one number, $A$:

$$
\omega^2 = \frac{GM}{a^3}\left(1 + A\,\frac{GM}{ac^2}\right)
$$

$A$ depends on how alike the masses are, through $\eta = m_1m_2/M^2$: 0 for a light body, ¼ for equal masses.
General relativity's own two-body equations (Einstein, Infeld and Hoffmann's) give $A = -3 + \eta$.

| Each body moving with its averaged space in | $A$ | Equal masses |
| --- | --- | --- |
| **One potential, with all its corrections** | $\mathbf{-3 + \eta}$ | **−2.75** |
| One potential, without each body's potential carried at its velocity | $-3 + 5\eta$ | −1.75 |
| The other body's field alone | $-3 + 3\eta$ | −2.25 |
| *General relativity's two-body equations* | $-3 + \eta$ | −2.75 |

What the first row computes is general relativity's first post-Newtonian spacetime, rearranged. With time kept by
clocks falling with space, one potential with all its corrections is that spacetime written another way: [Deriving
Curved Space](../part2/deriving-curved-space.md) showed it for bodies at rest, and the same steps give the
corrections of [One Potential](../part3/one-potential.md) with the bodies moving. The change of time doesn't change
the averaged motion, because the model's time runs at the same rate as general relativity's at each body, so averaging
in either gives the same pair. That step is argued, not computed. The rows below it are computed in the model's own
form.

Two rows show which parts matter:

- **The other body's field alone** is what [the last page](each-body-in-the-others-flow.md) did, and it misses: the
  term where a body's own field changes how the other's acts on it is exactly what averaging keeps.
- **Each body's potential carried at its velocity** is one of the small corrections to the flow that Part 3 brought
  in from general relativity. The Moon hardly needed it. The binary does: without it, the orbit's closest point turns
  by $2\pi(3 - 8\eta)\,GM/(c^2p)$ each orbit, with $p$ the orbit's size (its semi-latus rectum), where general
  relativity has $2\pi \cdot 3\,GM/(c^2p)$: a third as fast at equal masses. (This comes from the pair's equations of
  motion, worked out the same way, not from a run.)

| $\eta$ | The orbit's turning / general relativity's: one potential | Without the moving potentials |
| --- | --- | --- |
| 0 (a light body) | 1 | 1.00 |
| 0.1 | 1 | 0.73 |
| 0.2 | 1 | 0.47 |
| 0.25 (equal masses) | 1 | 0.33 |

## Off circles

With the bodies on circles the flow is steady in the frame turning with them. On an eccentric orbit there is no such
frame, so the flow is built step by step in time, keeping Bernoulli's equation. On it, each body's space was measured
the same way: averaged over rings round the body, at its closest and farthest points, for mass ratios 0.1 and 1 and
eccentricities 0 and 0.6.

| Ring nearest the body | The averaged flow, less the body's velocity / the body's speed |
| --- | --- |
| at every orbit, mass ratio and point tried | 1 to 3 × 10⁻⁸ |

<iframe src="../../viewer/index.html?player&run=../runs/eccentricBodies/ownSpace.full.json" width="100%" height="460" loading="lazy" title="How nearly each body's averaged space moves with it, against the ring's size"></iframe>

*How far each body's averaged space is from moving with the body, as a share of its speed (on a log scale, so −8 is
one part in 10⁸), against the size of the ring it is averaged over, in units of the separation (also log). Four of
the cases tried.*
[Open full screen](../../viewer/index.html?run=../runs/eccentricBodies/ownSpace.full.json){ target=_blank }

Further out it grows, as the other body's tide does, and close in it goes to zero: each body moves with its own space
on any orbit. A body moving that way is a body moving by general relativity's two-body equations, which give the
orbit's turning for every eccentricity, keep the pair's centre still, and have no Nordtvedt effect. Those three are
argued from the equations here, not run as orbits.

## The tests it passes

| Test | Each body in the others' flow | Moving with its own space |
| --- | --- | --- |
| A binary's orbit turning, equal masses (general relativity: 1) | ❌ 1.166 | ✅ 1, worked out exactly for circles |
| The pair's centre (general relativity: stays put) | ❌ 0.17 m/s² at mass ratio 0.1 | ✅ stays put: general relativity's equations, argued |
| Nordtvedt's $\eta$ (lunar laser ranging: under 10⁻⁴) | ❌ −0.76 | ✅ 0: general relativity's equations, argued |
| A light body: the Moon's de Sitter turn, $k$ (Part 3) | ❌ +0.47 | ✅ +0.01 |

## Where it stops

A pair of bodies moving round each other this way is general relativity's binary to the first order beyond Newton.
Real bodies also spin, which [Spinning Bodies](spinning-bodies.md) takes up. And a real binary also loses energy, slowly, to gravitational waves: the Hulse–Taylor pulsar's orbit shrinks by 3.5
metres a year. [Part 5](../part5.md) asks whether flowing space can carry those waves.

*The code: studies/binary_regularized.py (the flow round the Earth, the circular binary worked out exactly, and the
orbit's turning); studies/eccentric_bodies.py (each body's space off circles, on the flow of
studies/eccentric_flow.py).*
