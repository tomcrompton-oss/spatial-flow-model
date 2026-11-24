# The Precession of Mercury


In Newtonian gravity an isolated planet traces a fixed ellipse round the Sun, its closest point (perihelion) staying
put. In reality the other planets, and to a much lesser degree the Sun's oblateness, make the perihelia precess
slowly round the Sun. Mercury's precesses faster than these effects explain: Le Verrier found the discrepancy in
1859, about 38″ per century, later revised by Newcomb to 43″.

![An orbit whose perihelion, its closest point to the Sun, moves on a little each time round (much exaggerated), against the Newtonian ellipse, which stays fixed](images/precession.svg)

From here, "the precession of Mercury" means only the part Newtonian mechanics can't explain. 43″ per century is:

- 0.000208 radians per century
- 5.7 × 10⁻⁹ radians per day
- 5 × 10⁻⁷ radians per orbit

The simulation is harder than for light. Light crossing 2 AU takes about 15 minutes of simulated time; Mercury needs
at least two orbits, preferably more, of about 88 days each — at least 10,000 times as long — which forces larger time
steps, and less accuracy. Three orbits with $dt = 0.01$ s:

| | Perihelion | Precession (rad/orbit) | Aphelion | Precession (rad/orbit) |
| --- | --- | --- | --- | --- |
| dt = 0.01 s | 0.31 AU | 7.4842 × 10⁻⁷ | 0.47 AU | 7.5306 × 10⁻⁷ |

This took 10 hours to run, and is 50% above the expected 5 × 10⁻⁷: the first simulation's step was first order, and
orbits drifted outward by an amount that halved with $dt$, swamping the precession. There is a formula for the
precession in general relativity:

$$
\sigma = \frac{24\pi^3 a^2}{T^2c^2(1 - e^2)}
$$

with $\sigma$ the shift in radians per orbit, $a$ the semi-major axis, $T$ the orbital period and $e$ the
eccentricity. Scaling the orbit down by 10,000:

| Scaling factor | Perihelion precession | Aphelion precession | Predicted | Accuracy |
| --- | --- | --- | --- | --- |
| 10,000 | 0.0050320777 | 0.0050321204 | 0.0050216151 | 99.79% |

About half of that 0.2% is the formula itself: it is only the first term of general relativity's result, and for
Mercury's orbit scaled down 10,000 times exact general relativity gives 0.12% more. With the second-order step and
steps that shrink near the Sun, the scaled orbits take seconds, and their precession matches **exact** general
relativity to 1.6 × 10⁻⁴, falling with the step size (`studies/gr_comparison.py`).

**Test — passed**

<iframe src="../../../viewer/index.html?run=../runs/part1/part1_orbit.full.json" width="100%" height="520" loading="lazy" title="A precessing orbit"></iframe>

*An orbit between about 20 and 60 Schwarzschild radii of a one-solar-mass hole, six times round. The flow model's orbit
(solid) precesses about 20° an orbit — exact general relativity gives 19.5° for those apsides — while the Newtonian
ellipse (dashed) stays closed.* [Open full screen](../../../viewer/index.html?run=../runs/part1/part1_orbit.full.json){ target=_blank }
