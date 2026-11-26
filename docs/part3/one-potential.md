# One Potential

The [turning flow](carrying-the-flow.md) passes Newton's gravity round the moving Earth and lunar laser ranging's Sun
term, and [with space curved](curving-the-turning-flow.md), light grazing the Sun. Every one of those tests looked at light, or
at something held still near the Earth. This page starts with something that moves through the flow for months.

## The test: the Moon's slow turn

A spinning gyroscope carried round the Sun doesn't keep pointing the same way. General relativity says it turns,
slowly, by an amount that depends on its speed through the Sun's field: de Sitter's precession. The Earth and Moon
together are such a gyroscope, and the Moon's orbit is its spin. Going round the Sun once a year, the Moon's orbit
turns by 19.2 milliarcseconds a year more than Newton says. Lunar laser ranging, timing laser pulses to the Moon
and back for fifty years, measures that to better than 1%.

![The Sun with the Earth's orbit round it, and the Earth at four places a quarter of a year apart. At each, the Moon's orbit is drawn as an ellipse with its long axis marked, against a fixed direction; the axis has turned a little further at each place: de Sitter's precession, hugely exaggerated](images/desitter.svg)

The simulation runs the Moon round the Earth for 90 days, with the Earth going round the Sun, through each model's
flow. General relativity's Moon is then fitted to the model's: its start is free, and its orbit is turned by a
fraction $k$ of de Sitter's rate, also free.

- $k = 0$: the model's Moon turns as general relativity's does.
- $k = 1$: it doesn't turn at all.

What the fit can't take up is left over, in metres. To see the relativistic part alone, each model is run twice, with
the speed of light as it is and a thousand times larger, and the difference is added to Newton's Moon: any error in
the model's Newtonian part cancels. General relativity run through the same pipeline gives $k = 0.02$ and 2.9 cm left:
that is the floor of the method.

| The Moon over 90 days | $k$ (0 = general relativity) | Left after the fit |
| --- | --- | --- |
| General relativity (the check) | +0.02 | 0.029 m |
| The turning flow, flat | +0.49 | 0.26 m |
| The turning flow, space curved | +0.49 | 0.26 m |

The turning flow's Moon turns about half as much as it should, and curving space doesn't change that. Lunar laser
ranging would see it at once.

## A second test: light past a moving Jupiter

On 8 September 2002, Jupiter passed within a few of its own radii of a distant quasar. Radio telescopes across the
Earth timed the quasar's signal and measured how far Jupiter bent it, including the small part that comes from
Jupiter's motion, about 50 microarcseconds, with positions good to about 10.

![A quasar far away on the left and radio telescopes on the right. Two rays travel between them: one passing close to Jupiter, which moves across at 13 km/s, bent towards it; and a reference ray passing 100 Jupiter radii out. The telescopes measure the angle between the two rays where they arrive](images/jupiterrays.svg)

The simulation sends two rays from far away past Jupiter, on its orbit round the Sun, to one observer: one close to
Jupiter and one 100 Jupiter radii out. It compares the angle between them with general relativity's.

| Light passing Jupiter at | Jupiter held still, space curved | Jupiter moving, the turning flow, space curved |
| --- | --- | --- |
| 1 Jupiter radius | 2.1 µas off | 2.7 µas off |
| 10 Jupiter radii | 1.6 µas off | 22.0 µas off |

With Jupiter held still, Part 2's flow passes. With Jupiter moving, the turning flow is off by twice the radio
telescopes' precision at 10 Jupiter radii.

## Why: the constant

Both tests point back to the constant the turning flow chose. In Parts 1 and 2 the flow's speed was set by one rule:
$u^2/2 = \Phi$, the potential from all the bodies. With the bodies moving, the flow at each place changes with time,
and the rule takes that in. With $\phi$ the flow's potential ($\mathbf u$ is its slope),

$$
\frac{\partial\phi}{\partial t} + \frac{u^2}{2} = \Phi + J
$$

which is Bernoulli's equation for a flow with no swirl. With the bodies still, the first term is zero and this is Part
2's rule, with $J = 0$. The turning flow chose $J$ below zero, so that the Earth's flow is its own, and that constant
reshapes the whole flow: the Sun's flow stops two thirds of the way to the Earth, and the Earth's region reaches out to
meet it. Curved space hid that from light past the Sun, which sees only the flow's speed. The Moon, and light past a
moving Jupiter, still see it.

## The model: one potential

![Two panels, the Sun and the Earth. Left, the turning flow with its constant: space flows in towards the Sun only out to a dashed circle two thirds of the way to the Earth, where the Sun's flow stops, and the Earth's region of flow reaches out to meet it. Right, one potential with no constant: space flows in towards the Sun from everywhere, and the Earth's region is only its own small neighbourhood](images/onepotential.svg)

The fix is to go back to Parts 1 and 2: $J = 0$. The flow, steady in the frame turning with the bodies, is then one
potential over the whole plane. No flow stops, and the Sun's paths reach everywhere. Space is curved across the flow,
as in Part 2.

That isn't a guess either. [Deriving Curved Space](../part2/deriving-curved-space.md) took general relativity for
bodies at rest and measured its time by clocks falling with space, and found the flow model: clocks slowed only by
their speed through space, a potential flow keeping $u^2/2 = \Phi$, and space stretched across it. The same steps
work with the bodies going round each other. They give Bernoulli's equation above with $J = 0$, the same clocks and
the same curved space, plus small corrections to the flow, of the first order beyond Newton, from the bodies' motion.
For light those corrections are too small to matter; for the Moon's orbit over months, they are kept.

## The tests it passes

| Test | Measured to | The turning flow, space curved | One potential |
| --- | --- | --- | --- |
| Light grazing the Sun, at 2 solar radii | 0.01 mas | ✅ 0.0012 mas over | ✅ 0.0000 mas |
| Light past moving Jupiter, at 1 Jupiter radius | about 10 µas | ✅ 2.7 µas off | ✅ 4.1 µas off |
| Light past moving Jupiter, at 10 Jupiter radii | about 10 µas | ❌ 22.0 µas off | ✅ 2.5 µas off |
| The Moon's de Sitter turn, $k$ | under 0.01 (the method resolves about 0.02) | ❌ +0.49 | ✅ +0.01 |
| The Moon over 90 days, left after the fit | the method's floor, 0.029 m | ❌ 0.26 m | ✅ 0.036 m |

One potential passes everything the turning flow passed, and the two tests it failed. The Moon turns as general
relativity's does: $k = +0.01$, within the method's own check ($+0.02$ for general relativity itself), against the
turning flow's half. That is a pass to the method's resolution, about ±0.02 over 90 days, which is coarser than lunar
laser ranging's 1% over fifty years: the simulation shows the turn is general relativity's to a couple of per cent,
not to the measurement's full precision. And what the fit leaves over, 3.6 cm over 90 days, is at the method's floor: general relativity,
run the same way, leaves 2.9 cm. Over the months the simulation covers, the model's Moon is general relativity's.

The difference shows plainly if general relativity's Moon, with its full de Sitter turn, is fitted to each model's
Moon, its start free, and the distance between them is followed day by day:

<iframe src="../../viewer/index.html?player&run=../runs/lapseMoonResiduals/lapseMoon_residuals.full.json" width="100%" height="480" loading="lazy" title="The Moon in each model against general relativity's"></iframe>

*How far each model's Moon is from general relativity's, with its de Sitter turn, over 90 days. The turning flow, flat
or with space curved (orange), is up to 1.9 m off: no start can make up for the turn it lacks. One potential (blue)
stays within 10 cm, as close as general relativity itself run the same way (grey, dotted).*
[Open full screen](../../viewer/index.html?run=../runs/lapseMoonResiduals/lapseMoon_residuals.full.json){ target=_blank }

## Where it stops

Every test so far gave the bodies their paths: the Earth on its circle round the Sun, Jupiter on its orbit. Only the
Moon, a test body, moved by the flow. [Part 4](../part4/bodies-moved-by-the-flow.md) lets the bodies themselves move by each other's flow.

*The code: studies/lapse_moon.py (the Moon's orbit, fitted as studies/de_sitter.py does; run with order=4, the
Runge–Kutta rule, at 120 and 60 second steps; the plot from its residuals command), studies/light_two_rays.py
(light past Jupiter), studies/lapse_moving.py (light past the Sun); the flows: engine/turning.py, and
engine/carried.py's FreeFallTurning (general relativity in the one potential's time).*
