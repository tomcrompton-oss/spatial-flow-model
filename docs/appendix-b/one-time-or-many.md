# One Time or Many

[Seams](../part2/seams.md) found that a boundary between two ways of setting clocks works only where the two times
agree, once bodies move. An earlier model, the *carried flow*, ran into exactly this before that was understood.

In the carried flow each body's region has its own flow, the slope of its own potential, $\mathbf u = \nabla\phi_k$,
and that potential sets the region's time, $T + \phi_k/c^2$. Nothing made the potentials agree where two regions
meet, so the time jumped at the seam by $\Delta\phi/c^2$. Light going into a region and out again picks up a delay
that varies across the beam, and is turned by it, to first order in $u/c$:

$$
\delta\theta \approx \frac{1}{c}\,\frac{\partial}{\partial b}\Big[\Delta\phi(\text{in}) - \Delta\phi(\text{out})\Big]
$$

For a jump that is the same all over the seam, a jump across the ray cancels going in and coming out, and one along it
doesn't. A toy model of a circular seam gives 17″ for a 13 km/s jump along the ray. Light past a moving Jupiter showed
it on a huge scale:

| Light past Jupiter, the Sun 5.2 AU away: the cross term between the two bodies (µas) | 1 Jupiter radius | 10 | 100 |
| --- | --- | --- | --- |
| General relativity, Jupiter on its orbit | +0.34 | −0.05 | −0.11 |
| The carried flow, flat space, Jupiter on its orbit | +1,757,180 | +1,606,733 | +106,274 |

Seconds of arc where general relativity has fractions of a millionth.

**What it taught.** A model's regions have to share one time, or meet only where their times agree. Part 3's one
potential does the first: one $\phi$ for the whole plane, so the time can't jump. Seams does the second: a seam is
where two bodies' $S$ are equal up to a constant, so the times agree all along it.

*The code: engine/carried.py; studies/light_two_rays.py.*
