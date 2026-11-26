# The Gravitational Redshift of Light


General relativity predicts that light climbing out of a gravitational well is redshifted, because of time dilation:
an oscillator driving a transmitter deep in the well runs slower, so it produces waves of lower frequency.

![Light emitted by a clock deep in a gravitational well, where clocks run slow, and received by a clock far out: the same crests arrive further apart, at a lower frequency](images/redshift.svg)

## The clocks

As [clock 3 of The Four Clocks](../mechanics/four-clocks.md#clock-3-held-still-on-the-surface) shows, a clock
held still at distance $r$ from a body is moving up through its space at the escape speed $u$, and so runs at
$\sqrt{1 - u^2/c^2} = \sqrt{1 - r_s/r}$ of the flow's time, where $r_s = 2GM/c^2$. Deeper in the well space falls faster, so a clock held still there runs
slower. A clock held still further out runs faster, and one far away keeps the flow's time.

## The light

The emitter sends out a pulse, or a wave crest, every so often by its own clock. The flow doesn't change with time, so
every pulse climbs out along the same path through the same flowing space, and takes the same time to do it. The
pulses arrive as far apart in the flow's time as they were sent. But the receiver's clock runs faster than the
emitter's, so by its own clock it counts more time between arrivals, and sees a lower frequency. The two frequencies
are in the ratio of the two clocks' rates:

$$
\frac{f_\text{received}}{f_\text{emitted}} = \sqrt{\frac{1 - r_s/r_\text{emitter}}{1 - r_s/r_\text{receiver}}}
$$

which is general relativity's gravitational redshift, exactly.

## The simulation

The simulation holds an emitter still on a body's surface and a receiver still further out, and sends eight pulses of
light straight up between them. The light is followed step by step through the flowing space by the mechanics of
[Special Relativistic](../mechanics/special-relativistic.md); each clock runs at the rate above, as in
[The Four Clocks](../mechanics/four-clocks.md). The redshift is
largest for the densest bodies, so the player shows a neutron star: 1.4 solar masses within 12 km, with a receiver
240 km out.

<iframe src="../../../viewer/index.html?player&run=../runs/redshift/redshift_star.full.json" width="100%" height="480" loading="lazy" title="Light pulses climbing from a neutron star"></iframe>

*Distance from the star's centre across, the flow's time up. Blue: the emitter, held still on the surface. Grey: the
receiver, 240 km out. Orange: a pulse sent every 0.1 ms of the emitter's clock. Each pulse takes the same time to
climb, 0.986 ms, so they arrive as far apart as they were sent: 0.1235 ms of the flow's time. The emitter's clock
counts 0.1 ms of that, the receiver's 0.1225 ms.*
[Open full screen](../../../viewer/index.html?run=../runs/redshift/redshift_star.full.json){ target=_blank }

The same simulation for a white dwarf and for the Sun, each received at the Earth's distance, 1 AU:

| Body | Sent every (emitter's clock) | Received every (receiver's clock) | $f_\text{received}/f_\text{emitted}$, simulated | General relativity |
| --- | --- | --- | --- | --- |
| Neutron star: 1.4 solar masses, 12 km | 0.1 ms | 0.122458 ms | 0.816604686605 | 0.816604686605 |
| White dwarf: 1 solar mass, 6,000 km | 1 s | 1.00024626 s | 0.999753802349 | 0.999753802349 |
| The Sun | 1 s | 1.0000021 s | 0.999997899781 | 0.999997899781 |

In each case the pulses arrive exactly as far apart as they were sent,
to the precision of the arithmetic, and each pulse's climb agrees with general relativity's light travel time. The
simulated ratio matches general relativity's to 1 part in 10¹³ or better. For the neutron star, the light arrives with
82% of the frequency it left with; for the Sun, the shift is two parts in a million.

**Test — passed**

*The code: studies/redshift_pulses.py.*
