# Two bodies

With more than one body the flow's speed is still fixed, $|\mathbf u|^2 = \sum 2GM_i/d_i$, but its direction has to
be chosen, and the obvious choice is wrong.

## Along g: speed right, direction wrong

Pointing the flow along the net gravity g gets the speed right everywhere, but space moving with that flow does not
fall at g: off the line through the bodies its direction drifts 1–27° from the flow it arrives at. The flow along g
has curl. `tests/test_flow_consistency.py` checks exactly this — start a piece of space at A with u(A), let it fall
at g, and see whether it arrives at B moving at u(B) — and the flow along g fails it.

## The eikonal flow: no curl

For space moving with the flow to fall at exactly g, the flow must be the gradient of something:

$$
\mathbf u = -\nabla S, \qquad |\nabla S|^2 = \sum_i \frac{2GM_i}{d_i}
$$

the zero-energy Hamilton–Jacobi (eikonal) equation. Its flow lines are the paths of things falling from rest at
infinity. No such flow can be smooth everywhere round two holes, so it has a **seam**: each body's region is filled
by paths running straight out of it, a point belongs to the body whose S there is smallest, and the seam passes
through the potential's saddle (where g = 0 between them). Crossing the seam, a particle's w takes the flow's jump,
added relativistically, so its velocity is kept.

Two versions, the default for two or more bodies:

- **`eikonal`** — tables of the paths, integrated out from each body; any number of bodies.
- **`eikonal-exact`** — for exactly two bodies, the zero-energy paths separate in elliptic coordinates (Euler's
  problem of two fixed centres), so each point's path is found from elliptic integrals and Jacobi functions with no
  tables. Its acceleration matches g to about 2 × 10⁻⁹, against 10⁻⁴ for the tables.

With either, the consistency test passes on every path that stays on one side of the seam, and the 33 two-body test
paths (falls, orbits round one hole and both, flybys, escapes, light) match Newtonian gravity.

<iframe src="../viewer/index.html?run=../runs/twoBodyFalls/twoBodyFalls.full.json" width="100%" height="560" loading="lazy" title="Falls towards two holes"></iframe>

*Thirty paths falling from 10 AU towards two 1-solar-mass holes 1 AU apart, with the eikonal flow behind them.*
[Open full screen](../viewer/index.html?run=../runs/twoBodyFalls/twoBodyFalls.full.json){ target=_blank }
