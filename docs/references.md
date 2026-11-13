# References

The sources the model, the exact results it is checked against, and the numerical methods rest on. Each entry says
where in the project it is used.

## The model: space as a flowing river

**A. J. S. Hamilton and J. P. Lisle, "The river model of black holes", *American Journal of Physics* 76, 519–532
(2008).** [arXiv:gr-qc/0411060](https://arxiv.org/abs/gr-qc/0411060) ·
[doi:10.1119/1.2830526](https://doi.org/10.1119/1.2830526)
The picture this project simulates: space flows through a flat background like a river, and objects move through
the river by the rules of special relativity. For a rotating hole the river also twists (a Lorentz rotation as well
as a boost); `engine/kerr.py` follows the paper's equations for that, including its equation 77.

**Gullstrand–Painlevé coordinates** (P. Painlevé, 1921; A. Gullstrand, 1922).
[Overview](https://en.wikipedia.org/wiki/Gullstrand%E2%80%93Painlev%C3%A9_coordinates)
The form of the Schwarzschild metric, $ds^2 = -c^2dt^2 + |d\mathbf x - \mathbf u\,dt|^2$ with
$|\mathbf u| = \sqrt{2GM/r}$, that makes space flat and flowing: the one-hole model is this metric, and the time the
simulation runs on is its time.

**A. J. S. Hamilton, *Inside Black Holes*.** [jila.colorado.edu/~ajsh/insidebh](https://jila.colorado.edu/~ajsh/insidebh/)
Andrew Hamilton's site of general-relativistic black hole visualizations and explanations, by one of the river
model's two authors.

## Rotating holes

**C. Doran, "A new form of the Kerr solution", *Physical Review D* 61, 067503 (2000).**
[arXiv:gr-qc/9910099](https://arxiv.org/abs/gr-qc/9910099)
The Kerr metric in coordinates where space flows in, the rotating counterpart of Gullstrand–Painlevé, on which the
river model of a rotating hole is built. `engine/kerr.py` uses its radius $r = \sqrt{R^2 - a^2}$ from the flat
distance R.

**R. H. Boyer and R. W. Lindquist, "Maximal analytic extension of the Kerr metric", *Journal of Mathematical
Physics* 8, 265–281 (1967).** [doi:10.1063/1.1705193](https://doi.org/10.1063/1.1705193) ·
[overview of the coordinates](https://en.wikipedia.org/wiki/Boyer%E2%80%93Lindquist_coordinates)
The standard coordinates for the Kerr metric; their r is Doran's, which is how the exact Kerr results in
`engine/exact.py` are compared with the simulation.

**S. Chandrasekhar, *The Mathematical Theory of Black Holes* (Oxford University Press, 1983; Oxford Classic Texts,
1998).** [Publisher](https://academic.oup.com/book/52805)
Geodesics in the Kerr metric: the equations of motion for light and particles in the equatorial plane that
`engine/exact.py` integrates for exact Kerr light bending and orbital precession.

**J. M. Bardeen, W. H. Press and S. A. Teukolsky, "Rotating black holes: locally nonrotating frames, energy
extraction, and scalar synchrotron radiation", *The Astrophysical Journal* 178, 347–369 (1972).**
[doi:10.1086/151796](https://doi.org/10.1086/151796) ·
[ADS](https://ui.adsabs.harvard.edu/abs/1972ApJ...178..347B/abstract)
Formulae for orbits round a Kerr hole, including the innermost stable circular orbit and the circular photon orbit
that the viewers draw, and that a regression test checks ($r = 2.32088\,M$ for spin 0.9, with the spin).

**The Kerr metric.** [Overview](https://en.wikipedia.org/wiki/Kerr_metric)
Background on the rotating-hole solution: horizons, the ergosphere ($r = 2M$ in the equatorial plane) and the ring
singularity that the viewers mark.

## One hole: the exact results it is checked against

**Schwarzschild geodesics.** [Overview](https://en.wikipedia.org/wiki/Schwarzschild_geodesics)
The orbit equation in $u = 1/r$, from which come the exact light deflection,
$\alpha = 2\int_0^{u_0} du/\sqrt{1/b^2 - u^2 + r_s u^3} - \pi$, and the exact periapsis precession of a bound orbit
from its apsides, both in `engine/exact.py`, and the leading-order precession $6\pi GM/c^2a(1-e^2)$.

## Two bodies

**The Hamilton–Jacobi equation.** [Overview](https://en.wikipedia.org/wiki/Hamilton%E2%80%93Jacobi_equation)
At zero energy it is the eikonal equation $|\nabla S|^2 = \sum 2GM_i/d_i$ that the two-body flow solves: a flow
$\mathbf u = -\nabla S$ has no curl, its lines are zero-energy paths, and space moving with it falls at exactly g.

**Euler's problem of two fixed centres.** [Overview](https://en.wikipedia.org/wiki/Euler%27s_three-body_problem)
Motion under two fixed Newtonian centres is integrable: its Hamilton–Jacobi equation separates in elliptic
coordinates. That separation is what lets `engine/two_centre.py` find the exact two-body flow with no tables.

**The Poincaré–Hopf theorem.** [Overview](https://en.wikipedia.org/wiki/Poincar%C3%A9%E2%80%93Hopf_theorem)
Why the flow round two holes must have a seam: a smooth flow that never stops cannot run into two points and out to
infinity.

## Numerical methods

**B. C. Carlson, "Numerical computation of real or complex elliptic integrals", *Numerical Algorithms* 10, 13–26
(1995).** [arXiv:math/9409227](https://arxiv.org/abs/math/9409227) ·
[doi:10.1007/BF02198293](https://doi.org/10.1007/BF02198293)
The duplication algorithms for the symmetric integrals $R_F$ and $R_D$ that `engine/two_centre.py` uses for the
incomplete elliptic integrals, which stay accurate even where the paths start out along the line between the holes.

**NIST Digital Library of Mathematical Functions, chapters 19 and 22.**
[Elliptic integrals](https://dlmf.nist.gov/19) · [Jacobi elliptic functions](https://dlmf.nist.gov/22)
Elliptic integrals in Carlson's symmetric form, and the Jacobi functions sn, cn, dn and the amplitude, computed in
`engine/two_centre.py` by the arithmetic–geometric mean.

## Gravitational waves

**M. Maggiore, *Gravitational Waves, Volume 1: Theory and Experiments* (Oxford University Press, 2007).**
[Publisher](https://global.oup.com/academic/product/gravitational-waves-9780198570745)
The transverse-traceless (TT) gauge, the proper detector frame and geodesic deviation: the GR results the wave studies
check against, and the change to proper distance that turns a wave through the plane into a flow of space.

**Gravitational waves.** [Overview](https://en.wikipedia.org/wiki/Gravitational_wave)
Background: plus and cross polarizations, and how a passing wave stretches and squeezes a ring of free particles.

## Tools

**Material for MkDocs.** [squidfunk.github.io/mkdocs-material](https://squidfunk.github.io/mkdocs-material/)
The theme this site is built with, from the Markdown pages in `docs/`.

**GitHub Pages.** [Documentation](https://docs.github.com/en/pages)
Where the site is hosted; `.github/workflows/pages.yml` builds and publishes it on every push.
