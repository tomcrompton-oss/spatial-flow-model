# The Shapiro Time Delay


Irwin Shapiro proposed a further test that could be done within the solar system, sometimes called the fourth
classical test: a delay in the round-trip time of radar signals bounced off other planets. The situation is like the
bending of light, and the effect is usually put down to time dilation, like the redshift. In flowing space it also
shows which clocks the flow's time is.

![A radar pulse from the Earth to Venus, on the far side of the Sun, and its echo back, both passing close to the Sun through space flowing in towards it: the round trip takes about 200 µs longer than at c in flat space](images/shapiro.svg)

The delay was first seen by bouncing radio waves off Mercury and Venus when they were on the far side of the Sun. We
use Venus, but compare with the approximation

$$
\Delta t = -\frac{2GM}{c^3}\ln(1 - \mathbf R\cdot\mathbf x)
$$

with $\mathbf R$ the unit vector from the observer to the source and $\mathbf x$ the unit vector from the observer to
the mass $M$. The formula lets us ignore the many other factors in the experiments — where each planet is in its
orbit, time dilation on Earth, and so on. It predicts a delay of about 100 µs for a signal from Earth to Venus that
just grazes the Sun (about 700,000 km).

The simulation gives the travel time, and we can work out the time light would take to cover the same route at $c$.
The difference is **0.0213 s** – not the one-way 100 µs, because that formula uses different clocks (below). The
experiment had no observer on Venus: the signal was echoed back to Earth, and it measured the round trip. The return
journey comes out at **−0.0211 s**: the light returns *faster* than if it had travelled at $c$. That shouldn't be
surprising: the speed of light is only a local limit. Light's local velocity $w$
is always $c$, but seen from a distance it can be more or less than $c$, depending on whether it travels with or
against the flow of space. The round trip's difference, +0.0213 − 0.0211 s, is about 200 µs — the Shapiro delay
there and back.

The experiment couldn't know the exact distance between Earth and Venus, so it took readings before and after Venus
passed behind the Sun and looked at the pattern. We can do the same:

| Closest approach (solar radii) | Outbound (s) | Return (s) | Round trip (s) | GR round trip (s) | Agreement |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.021349 | −0.021137 | 0.000212 | 0.000219 | 97.14% |
| 2 | 0.021336 | −0.021151 | 0.000185 | 0.000191 | 96.77% |
| 5 | 0.021318 | −0.021169 | 0.000149 | 0.000155 | 96.04% |
| 10 | 0.021304 | −0.021182 | 0.000122 | 0.000128 | 95.20% |
| 20 | 0.021290 | −0.021196 | 0.000094 | 0.000101 | 93.78% |
| 30 | 0.021282 | −0.021204 | 0.000078 | 0.000084 | 92.69% |

*(Selected rows of the original's table, from 1 to 30 solar radii.)*

The ±0.021 s on each leg is the difference between two ways of setting clocks. Spatial flow's time – the time of a
distant observer, and of anything falling with the space – is general relativity's Gullstrand–Painlevé time. The
one-way formula, and the experiment's analysis, use Schwarzschild time. The two differ by an amount that depends only
on the distance from the Sun:

$$
t_\text{GP} - t_\text{S} = \frac{r_s}{c}\left[2\sqrt{\frac{r}{r_s}} + \ln\frac{\sqrt{r/r_s} - 1}{\sqrt{r/r_s} + 1}\right]
$$

That is 0.14024 s at the Earth and 0.11925 s at Venus: a difference of **0.0210 s**. So the outbound leg is 0.0210 s
plus its share of the Shapiro delay, and the return leg is −0.0210 s plus its share. The offsets cancel over any round
trip, which is the only thing that can be measured. The table's 92–97% is looser than the bending or the precession,
which points to these early runs' setup – how the endpoints and the closest approach are defined, and the one-way
formula used for each leg – rather than the physics. The run below, with the current simulation, measures each leg
between the same two points.

**Test — passed**

<iframe src="../../../viewer/index.html?run=../runs/part1/part1_radar.full.json" width="100%" height="480" loading="lazy" title="A radar echo past a black hole"></iframe>

*A radar echo past a one-solar-mass hole: from an "Earth" 150 Schwarzschild radii on one side, passing 15 from the
hole, to a mirror 60 on the other side, and back — distance along the line against time. Out takes 2.032 ms, back
2.220 ms (2.069 ms each way in flat space). The legs differ by 189 µs, of which 176 µs is the clock offset between the
two ends; the rest comes from the light taking slightly different paths out and back. The round trip is 113 µs longer
than in flat space: the Shapiro delay, close to the weak-field estimate of about 100 µs even this near the hole.*
[Open full screen](../../../viewer/index.html?run=../runs/part1/part1_radar.full.json){ target=_blank }
