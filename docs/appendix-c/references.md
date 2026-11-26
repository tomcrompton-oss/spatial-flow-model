# References

The sources the model, the results it is checked against, the measurements and the numerical methods rest on. Each
entry says where on the site it is used.

## The model: space as a flowing river

**A. J. S. Hamilton and J. P. Lisle, "The river model of black holes", *American Journal of Physics* 76, 519–532
(2008).** [arXiv:gr-qc/0411060](https://arxiv.org/abs/gr-qc/0411060) ·
[doi:10.1119/1.2830526](https://doi.org/10.1119/1.2830526)
The picture this site simulates: space flows through a flat background like a river, and objects move through the
river by the rules of special relativity. For a rotating hole the river also twists, a rotation as well as a boost;
`engine/kerr.py` follows the paper's equations for that, including its equation 77.
[Black Holes](../part1/black-holes.md), [Rotating Black Holes](../part1/rotating-black-holes.md).

**Gullstrand–Painlevé coordinates** (P. Painlevé, 1921; A. Gullstrand, 1922).
[Overview](https://en.wikipedia.org/wiki/Gullstrand%E2%80%93Painlev%C3%A9_coordinates)
The form of the Schwarzschild metric, $ds^2 = -c^2dt^2 + |d\mathbf x - \mathbf u\,dt|^2$ with
$|\mathbf u| = \sqrt{2GM/r}$, that makes space flat and flowing. The one-body model is this metric, and the time the
simulation runs on is its time. Part 1 throughout.

**A. J. S. Hamilton, *Inside Black Holes*.** [jila.colorado.edu/~ajsh/insidebh](https://jila.colorado.edu/~ajsh/insidebh/)
General-relativistic black hole visualizations and explanations, by one of the river model's two authors.

## Rotating holes

**C. Doran, "A new form of the Kerr solution", *Physical Review D* 61, 067503 (2000).**
[arXiv:gr-qc/9910099](https://arxiv.org/abs/gr-qc/9910099)
The Kerr metric in coordinates where space flows in, the rotating counterpart of Gullstrand–Painlevé, on which the
river model of a rotating hole is built. `engine/kerr.py` uses its radius $r = \sqrt{R^2 - a^2}$ from the flat
distance $R$. [Rotating Black Holes](../part1/rotating-black-holes.md).

**R. H. Boyer and R. W. Lindquist, "Maximal analytic extension of the Kerr metric", *Journal of Mathematical
Physics* 8, 265–281 (1967).** [doi:10.1063/1.1705193](https://doi.org/10.1063/1.1705193) ·
[overview of the coordinates](https://en.wikipedia.org/wiki/Boyer%E2%80%93Lindquist_coordinates)
The standard coordinates for the Kerr metric; their $r$ is Doran's, which is how the exact Kerr results in
`engine/exact.py` are compared with the simulation.

**S. Chandrasekhar, *The Mathematical Theory of Black Holes* (Oxford University Press, 1983; Oxford Classic Texts,
1998).** [Publisher](https://academic.oup.com/book/52805)
Geodesics in the Kerr metric: the equations of motion for light and particles in the equatorial plane that
`engine/exact.py` integrates for exact Kerr light bending and orbital precession.

**J. M. Bardeen, W. H. Press and S. A. Teukolsky, "Rotating black holes: locally nonrotating frames, energy
extraction, and scalar synchrotron radiation", *The Astrophysical Journal* 178, 347–369 (1972).**
[doi:10.1086/151796](https://doi.org/10.1086/151796)
Formulae for orbits round a Kerr hole, including the innermost stable circular orbit and the circular photon orbit
that the viewers draw, and that a regression test checks.

**The Kerr metric.** [Overview](https://en.wikipedia.org/wiki/Kerr_metric)
Background on the rotating-hole solution: horizons, the ergosphere and the ring singularity that the viewers mark.

## One body: the exact results it is checked against

**Schwarzschild geodesics.** [Overview](https://en.wikipedia.org/wiki/Schwarzschild_geodesics)
The orbit equation in $u = 1/r$, from which come the exact light deflection,
$\alpha = 2\int_0^{u_0} du/\sqrt{1/b^2 - u^2 + r_s u^3} - \pi$, and the exact periapsis precession of a bound orbit
from its apsides, both in `engine/exact.py`, and the leading-order precession $6\pi GM/c^2a(1-e^2)$.
[The Bending of Light](../part1/tests/bending.md), [The Precession of Mercury](../part1/tests/precession.md).

**I. I. Shapiro, "Fourth test of general relativity", *Physical Review Letters* 13, 789–791 (1964).**
[doi:10.1103/PhysRevLett.13.789](https://doi.org/10.1103/PhysRevLett.13.789)
The delay of radar echoes passing the Sun, and the formula the simulation's round trips are compared with.
[The Shapiro Time Delay](../part1/tests/shapiro.md).

## Several bodies, and bodies moving

**The Hamilton–Jacobi equation.** [Overview](https://en.wikipedia.org/wiki/Hamilton%E2%80%93Jacobi_equation)
At zero energy it is the eikonal equation $|\nabla S|^2 = \sum 2GM_i/d_i$ that the potential flow solves: a flow
$\mathbf u = -\nabla S$ has no curl, its lines are the paths of things falling from rest far away, and space moving
with it falls at exactly $g$. With the bodies moving, it becomes Bernoulli's equation.
[Potential Flow](../part2/potential-flow.md), [One Potential](../part3/one-potential.md).

**Euler's problem of two fixed centres.** [Overview](https://en.wikipedia.org/wiki/Euler%27s_three-body_problem)
Motion under two fixed Newtonian centres is integrable: its Hamilton–Jacobi equation separates in elliptic
coordinates. That separation is what lets `engine/two_centre.py` find the exact two-body flow with no tables.

**The Poincaré–Hopf theorem.** [Overview](https://en.wikipedia.org/wiki/Poincar%C3%A9%E2%80%93Hopf_theorem)
Why the flow round two bodies must have a seam: a smooth flow that never stops can't run into two points and out to
infinity. [Potential Flow](../part2/potential-flow.md).

**The restricted three-body problem and Jacobi's constant.**
[Overview](https://en.wikipedia.org/wiki/Jacobi_integral)
Paths in the frame turning with two bodies on circles keep one constant, Jacobi's. The turning flow's paths are
these, all with one value of it. [Carrying the Flow](../part3/carrying-the-flow.md),
[Curving the Turning Flow](../part3/curving-the-turning-flow.md).

**R. Arnowitt, S. Deser and C. W. Misner, "The dynamics of general relativity", in *Gravitation: An Introduction to
Current Research*, ed. L. Witten (Wiley, 1962).** [arXiv:gr-qc/0405109](https://arxiv.org/abs/gr-qc/0405109)
The 3+1 (ADM) form of general relativity, $ds^2 = -N^2c^2dt^2 + \gamma_{ij}(dx^i - u^i dt)(dx^j - u^j dt)$: the lapse,
the flow (general relativity's shift, with the sign changed) and the metric of space, with Einstein's equations as
constraints and evolution. [Deriving Curved Space](../part2/deriving-curved-space.md), `engine/metric.py`.

## General relativity beyond Newton: the references the models are checked against

**C. M. Will, *Theory and Experiment in Gravitational Physics* (Cambridge University Press, 2nd edition 2018).**
[Publisher](https://doi.org/10.1017/9781316338612)
General relativity's first post-Newtonian metric for several bodies, which `engine/metric.py`'s `PostNewtonian` is,
and the framework for its tests. [Deriving Curved Space](../part2/deriving-curved-space.md), Parts 2 and 3.

**C. M. Will, "The confrontation between general relativity and experiment", *Living Reviews in Relativity* 17, 4
(2014).** [arXiv:1403.7377](https://arxiv.org/abs/1403.7377) ·
[doi:10.12942/lrr-2014-4](https://doi.org/10.12942/lrr-2014-4)
The measurements the site's tests quote, and their precision: Cassini, lunar laser ranging, binary pulsars.

**A. Einstein, L. Infeld and B. Hoffmann, "The gravitational equations and the problem of motion", *Annals of
Mathematics* 39, 65–100 (1938).** [doi:10.2307/1968714](https://doi.org/10.2307/1968714)
General relativity's equations of motion for several bodies to the first order beyond Newton (EIH): what the Moon's
orbit is fitted with, and what a binary of comparable masses is compared with.
[One Potential](../part3/one-potential.md), [Part 4](../part4/bodies-moved-by-the-flow.md).

**L. Blanchet, "Gravitational radiation from post-Newtonian sources and inspiralling compact binaries", *Living
Reviews in Relativity* 17, 2 (2014).** [arXiv:1310.1528](https://arxiv.org/abs/1310.1528) ·
[doi:10.12942/lrr-2014-2](https://doi.org/10.12942/lrr-2014-2)
How point masses are moved in post-Newtonian theory, with Hadamard's finite part averaging away each body's own
field, and the radiation that follows. [Moving With Its Own Space](../part4/moving-with-its-own-space.md),
[Part 5](../part5.md).

## Measurements

**R. V. Pound and G. A. Rebka, "Apparent weight of photons", *Physical Review Letters* 4, 337–341 (1960).**
[doi:10.1103/PhysRevLett.4.337](https://doi.org/10.1103/PhysRevLett.4.337)
The gravitational redshift measured over 22.5 m of height. [The Gravitational Redshift](../part1/tests/redshift.md).

**B. Bertotti, L. Iess and P. Tortora, "A test of general relativity using radio links with the Cassini
spacecraft", *Nature* 425, 374–376 (2003).** [doi:10.1038/nature01997](https://doi.org/10.1038/nature01997)
Light's bending and delay past the Sun, to 2 parts in 10⁵. [Curving the Turning Flow](../part3/curving-the-turning-flow.md).

**J. G. Williams, S. G. Turyshev and D. H. Boggs, "Progress in lunar laser ranging tests of relativistic gravity",
*Physical Review Letters* 93, 261101 (2004).** [arXiv:gr-qc/0411113](https://arxiv.org/abs/gr-qc/0411113)
De Sitter's precession of the Moon's orbit, the Nordtvedt effect, and the lunar range terms the site's tests compare
with. [Curved Space](../part2/curved-space.md), [One Potential](../part3/one-potential.md),
[Each Body in the Others' Flow](../part4/each-body-in-the-others-flow.md).

**E. B. Fomalont and S. M. Kopeikin, "The measurement of the light deflection from Jupiter: experimental results",
*The Astrophysical Journal* 598, 704–711 (2003).** [arXiv:astro-ph/0302294](https://arxiv.org/abs/astro-ph/0302294)
Jupiter passing a quasar on 8 September 2002: the bending's part that comes from Jupiter's motion.
[One Potential](../part3/one-potential.md).

**W. de Sitter, "On Einstein's theory of gravitation and its astronomical consequences", *Monthly Notices of the
Royal Astronomical Society* 77, 155–184 (1916).** [doi:10.1093/mnras/77.2.155](https://doi.org/10.1093/mnras/77.2.155)
The precession of a gyroscope, or an orbit, carried round the Sun. [One Potential](../part3/one-potential.md).

**K. Nordtvedt, "Equivalence principle for massive bodies. II. Theory", *Physical Review* 169, 1017–1025 (1968).**
[doi:10.1103/PhysRev.169.1017](https://doi.org/10.1103/PhysRev.169.1017)
Whether a body bound by its own gravity falls as a single body of its mass does: 0 in general relativity.
[Each Body in the Others' Flow](../part4/each-body-in-the-others-flow.md).

**R. A. Hulse and J. H. Taylor, "Discovery of a pulsar in a binary system", *The Astrophysical Journal* 195,
L51–L53 (1975).** [doi:10.1086/181708](https://doi.org/10.1086/181708) ·
**J. M. Weisberg and Y. Huang, "Relativistic measurements from timing the binary pulsar PSR B1913+16",
*The Astrophysical Journal* 829, 55 (2016).** [arXiv:1606.02744](https://arxiv.org/abs/1606.02744)
The binary pulsar, and the shrinking of its orbit as it loses energy to gravitational waves. [Part 5](../part5.md).

**M. Kramer et al., "Strong-field gravity tests with the double pulsar", *Physical Review X* 11, 041050 (2021).**
[arXiv:2112.06795](https://arxiv.org/abs/2112.06795)
Two pulsars of nearly equal mass: their orbit's turning and decay, and general relativity's other timing effects.
[Each Body in the Others' Flow](../part4/each-body-in-the-others-flow.md).

## Gravitational waves

**M. Maggiore, *Gravitational Waves, Volume 1: Theory and Experiments* (Oxford University Press, 2007).**
[Publisher](https://global.oup.com/academic/product/gravitational-waves-9780198570745)
The transverse-traceless (TT) gauge, the proper detector frame and geodesic deviation: the general relativity results
the wave studies check against, and the change to proper distance that turns a wave through the plane into a flow of
space. [Part 5](../part5.md).

**P. C. Peters and J. Mathews, "Gravitational radiation from point masses in a Keplerian orbit", *Physical Review*
131, 435–440 (1963)** · **P. C. Peters, "Gravitational radiation and the motion of two point masses", *Physical
Review* 136, B1224–B1232 (1964).** [doi:10.1103/PhysRev.131.435](https://doi.org/10.1103/PhysRev.131.435) ·
[doi:10.1103/PhysRev.136.B1224](https://doi.org/10.1103/PhysRev.136.B1224)
The energy and angular momentum a binary loses to waves, and how fast its orbit shrinks. [Part 5](../part5.md).

**W. L. Burke, "Gravitational radiation damping of slowly moving systems calculated using matched asymptotic
expansions", *Journal of Mathematical Physics* 12, 401–418 (1971).** [doi:10.1063/1.1665603](https://doi.org/10.1063/1.1665603)
The radiation-reaction potential (Burke–Thorne) that the model puts into its flow. [Part 5](../part5.md).

## Hawking and Unruh radiation

**S. W. Hawking, "Particle creation by black holes", *Communications in Mathematical Physics* 43, 199–220
(1975).** [doi:10.1007/BF02345020](https://doi.org/10.1007/BF02345020)
A black hole glows, at a temperature set by its surface gravity. [Part 6](../part6/index.md).

**W. G. Unruh, "Notes on black-hole evaporation", *Physical Review D* 14, 870–892 (1976)** ·
**W. G. Unruh, "Experimental black-hole evaporation?", *Physical Review Letters* 46, 1351–1353 (1981).**
[doi:10.1103/PhysRevD.14.870](https://doi.org/10.1103/PhysRevD.14.870) ·
[doi:10.1103/PhysRevLett.46.1351](https://doi.org/10.1103/PhysRevLett.46.1351)
An accelerating observer sees empty space as warm; and a fluid flowing faster than sound should give off sound the
same way a hole gives off light. [Part 6](../part6/index.md).

**M. Visser, "Acoustic black holes: horizons, ergospheres and Hawking radiation", *Classical and Quantum Gravity*
15, 1767–1791 (1998).** [arXiv:gr-qc/9712010](https://arxiv.org/abs/gr-qc/9712010)
Sound in a moving fluid sees a metric of the Gullstrand–Painlevé form, and its horizon's temperature is set by the
flow's gradient there. [Part 6](../part6/index.md).

## Where the model's rules come from

**J. C. Baez and E. F. Bunn, "The meaning of Einstein's equation", *American Journal of Physics* 73, 644–652
(2005).** [arXiv:gr-qc/0103044](https://arxiv.org/abs/gr-qc/0103044)
Einstein's equation as a statement about small balls of freely falling particles: the "ball law" of
[What Comes From Outside](../conclusion/from-outside.md).

**T. Jacobson, "Thermodynamics of spacetime: the Einstein equation of state", *Physical Review Letters* 75,
1260–1263 (1995).** [arXiv:gr-qc/9504004](https://arxiv.org/abs/gr-qc/9504004)
Einstein's equation derived from light rays converging and the thermodynamics of horizons.
[What Comes From Outside](../conclusion/from-outside.md).

## Numerical methods

**B. C. Carlson, "Numerical computation of real or complex elliptic integrals", *Numerical Algorithms* 10, 13–26
(1995).** [arXiv:math/9409227](https://arxiv.org/abs/math/9409227) ·
[doi:10.1007/BF02198293](https://doi.org/10.1007/BF02198293)
The duplication algorithms for the symmetric integrals $R_F$ and $R_D$ that `engine/two_centre.py` uses for the
incomplete elliptic integrals.

**NIST Digital Library of Mathematical Functions, chapters 19 and 22.**
[Elliptic integrals](https://dlmf.nist.gov/19) · [Jacobi elliptic functions](https://dlmf.nist.gov/22)
Elliptic integrals in Carlson's symmetric form, and the Jacobi functions sn, cn, dn and the amplitude, computed in
`engine/two_centre.py` by the arithmetic–geometric mean.

## Tools

**Material for MkDocs.** [squidfunk.github.io/mkdocs-material](https://squidfunk.github.io/mkdocs-material/)
The theme this site is built with, from the Markdown pages in `docs/`.

**GitHub Pages.** [Documentation](https://docs.github.com/en/pages)
Where the site is hosted; `.github/workflows/pages.yml` builds and publishes it on every push.
