# The Bending of Light


Newtonian gravity also predicts that starlight bends round a massive body — Cavendish and Soldner both pointed this
out around 1800 — and Einstein's first, 1911, calculation from the equivalence principle gave the same value. In
1915, completing general relativity, he found it was only half the correct value: 1.75 arcseconds for light grazing
the Sun.

![Starlight grazing the Sun bends towards it, through space flowing in towards the Sun, so from the Earth the star is seen a small angle δφ away from its true direction; b is the closest approach (the angle much exaggerated)](images/bending.svg)

The simulation can use different calculators:

- **Newtonian** — Newton's law of gravitation. The particle's mass doesn't enter, so light is bent, but $c$ is no
  limit: photons speed up and slow down.
- **Newtonian flow** — the mechanics of flowing space from [Newtonian](../mechanics/newtonian.md). Should match Newtonian.
- **Special relativistic** — standard special relativity: light is bent and keeps to $c$. We expect half the
  deflection.
- **Special flow** — the mechanics of flowing space with special relativity, from [Special Relativistic](../mechanics/special-relativistic.md).

The simulation sends light from 1 AU on the far side of the Sun to the Earth (2 AU in all), on a path grazing the
Sun at $7\times10^8$ m from its centre, with $dt = 0.001$ s. The general relativity approximation is $\delta\phi \approx 4GM/c^2b$,
with $b$ the closest approach.

| Calculator | Simulated deflection (rad) | Deflection (arcsec) | GR approximation (rad) |
| --- | --- | --- | --- |
| Newtonian | 4.2201 × 10⁻⁶ | 0.87 | 8.4403 × 10⁻⁶ |
| Newtonian flow | 4.2201 × 10⁻⁶ | 0.87 | 8.4403 × 10⁻⁶ |
| Special relativistic | 4.2201 × 10⁻⁶ | 0.87 | 8.4403 × 10⁻⁶ |
| Special flow | 8.4416 × 10⁻⁶ | 1.74 | 8.4403 × 10⁻⁶ |

The first three give half the observed deflection, as anything short of general relativity does. Special flow gives
the full deflection: 99.99% of the approximation, and 99% of the observed 1.75″. The last 0.015% (8.4416 against
8.4404 × 10⁻⁶) is the start of the light, not an error: light started off the axis where space is flowing in at $u$
has general relativity's impact parameter $b/(1 + u/c)$, not $b$, and at 1 AU $u/c \approx 1.4\times10^{-4}$. Allowing
for that, the simulation matches exact general relativity to parts in $10^7$, from 1 to 1000 AU
(`studies/gr_comparison.py`).

Replacing the Sun with a black hole of one solar mass, we can send light closer, by factors of ten:

| Closest approach (m) | dt (s) | Simulated (rad) | Approximation $4GM/c^2r_0$ (rad) | Exact GR (rad) |
| --- | --- | --- | --- | --- |
| 699,998,534 | 0.001 | 8.4416 × 10⁻⁶ | 8.4403 × 10⁻⁶ | 8.4404 × 10⁻⁶ |
| 69,998,542 | 0.001 | 8.4421 × 10⁻⁵ | 8.4405 × 10⁻⁵ | 8.4409 × 10⁻⁵ |
| 6,998,828 | 0.001 | 0.0008448 | 0.0008442 | 0.00084452 |
| 701,476 | 0.001 | 0.008447 | 0.008423 | 0.0084573 |
| 698,629 | 0.0001 | 0.008500 | 0.008457 | 0.0084919 |
| 68,579 | 0.00001 | 0.09023 | 0.08615 | 0.089942 |

The simulation agrees with **exact** general relativity (last column, from the full deflection integral; see
[References](../../appendix-c.md)) to within 0.12% at 238 Schwarzschild radii and 0.3% at 24, while the weak-field
approximation is 4% off at 24: close to the hole it is the approximation that fails.

**Test — passed**

<iframe src="../../../viewer/index.html?run=../runs/part1/part1_bending.full.json" width="100%" height="520" loading="lazy" title="Light bending round a black hole"></iframe>

*Light passing a black hole of one solar mass at 4, 6, 10, 20 and 30 Schwarzschild radii, in the flow model (solid)
and under Newtonian gravity starting at $c$ (dashed); the arrows are the flow of space. Close to the hole the flow
model bends light several times as much — 57° against 14° at 4 Schwarzschild radii — and further out the ratio falls
towards the factor of two in the table (2.8 at 30 Schwarzschild radii, from 150 out on either side).* [Open full screen](../../../viewer/index.html?run=../runs/part1/part1_bending.full.json){ target=_blank }
