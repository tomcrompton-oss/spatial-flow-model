# Spinning Bodies

Real bodies spin. [Rotating Black Holes](../part1/rotating-black-holes.md) in Part 1 handled one spinning hole with
Hamilton and Lisle's river model, in which a spinning hole's space twists as it flows. That was built for a single hole
at rest. The model of Parts 2 to 4 has no twist: it has one potential for every body, space curved across the flow,
and the flow's small corrections. Does it give a spinning body's effects too, and do they agree with Part 1's?

## The model: spin is moving matter

A spinning body is matter going round. [Part 3](../part3/one-potential.md) found that the flow needs each body's
potential carried at its velocity: moving matter drags the flow a little along with it. Apply that to the body's own
rotating matter, piece by piece, and far from the body the pieces add up to a swirl round it,

$$
\mathbf u = -\sqrt{\frac{2GM}{r}}\,\hat{\mathbf r} \;+\; \frac{2G\,\mathbf J\times\mathbf r}{c^2r^3}
$$

where $\mathbf J$ is the body's angular momentum. Space still falls in as in Part 1, and also goes round, the way the
body spins.

![Three panels. Left, the inflow round a body as in Part 1: arrows straight in, longer close in. Middle, the swirl from the body's spin: arrows going round it anticlockwise, the way a red arrow shows it spinning, long close in and dwindling quickly further out. Right, the two together: space spiralling in, the spiral tighter close to the body](images/spinswirl.svg)

The swirl falls off as $1/r^2$, much faster than the inflow, so it matters only close in. Clocks are slowed only by
their speed through space, and space is flat, as in Part 1: for one body at rest, the model's curved space and
corrections reduce to Part 1's flat river in other coordinates. Nothing else is added: no twist.

This is general relativity's frame dragging, sometimes called gravitomagnetism. It is the same term in Einstein's
equations as the moving potentials: the momentum constraint, with the body's angular momentum as its source.

## The test: orbits with and against the spin

Frame dragging shows in orbits. Going round the same way as the body spins, an orbit's closest point moves on by less
than round a body with no spin; going round against the spin, by more. Half the difference is the part that comes
from the spin, and exact Kerr, general relativity's spinning hole, gives it exactly.

The simulation runs orbits round a body of 4 million solar masses, like the hole at the centre of the Galaxy,
spinning at 0.1 and 0.5 of the most a black hole can, close enough in for the spin to show. Distances are in
$M = GM/c^2$, half the Schwarzschild radius:

| Orbit | Spin | The spin's part of the turning, each orbit (rad) | Exact Kerr's | Model / exact Kerr |
| --- | --- | --- | --- | --- |
| 55–100 M | 0.1 | −4.974 × 10⁻³ | −4.974 × 10⁻³ | 1.0000 |
| 55–100 M | 0.5 | −2.488 × 10⁻² | −2.488 × 10⁻² | 0.9997 |
| 233–400 M | 0.1 | −5.164 × 10⁻⁴ | −5.164 × 10⁻⁴ | 1.0000 |
| 233–400 M | 0.5 | −2.582 × 10⁻³ | −2.582 × 10⁻³ | 1.0000 |

With no spin, the same orbits turn as exact Schwarzschild's, to a part in a million.

*(The textbook formula, Lense and Thirring's, is only the first term: it gives 4% less at 233–400 M and 19% less at
55–100 M. Exact Kerr, for each orbit's own closest and furthest points, is the right comparison.)*

<iframe src="../../viewer/index.html?player&run=../runs/frameDragging/frameDragging.full.json" width="100%" height="560" loading="lazy" title="Orbits with and against a body's spin"></iframe>

*Orbits from 100 M round a body spinning at half the most it can, anticlockwise: going round with the spin (blue),
against it (pink), and round the same body with no spin (grey, dashed), over the flow. Against the spin the orbit's
closest point moves on further each time round; with it, less.*
[Open full screen](../../viewer/index.html?run=../runs/frameDragging/frameDragging.full.json){ target=_blank }

## Two ways to the same spin

Part 1's river model and this one reach exact Kerr's frame dragging by different routes. Hamilton and Lisle's twist
keeps space flat for a spinning hole, all the way in to its horizon; here the swirl is the moving potential the
many-body model already has, and once space may be curved the twist isn't needed as a separate rule. In the plane,
for the orbits run, the two agree.

The swirl is the one place the model's flow has curl. That is allowed: outside matter Einstein's equations require
the curl to have no curl of its own, which this swirl's hasn't, and it is far too small to matter anywhere but close
to a spinning body ([Flows With Curl](../appendix-b/flows-with-curl.md)). With curl, the simulator steps on the particle's
momentum, which is the true path through the flow ([The Step and the Geodesic](../appendix-b/step-and-geodesic.md)).

## Where it stops

- **Off the plane.** The engine is planar, so only orbits in the body's equator are run. Frame dragging also tilts an
  orbit out of its plane, which the LAGEOS satellites measure round the Earth, and turns a gyroscope, which Gravity
  Probe B measured. Neither is run.
- **Spinning bodies moving each other.** The run is one spinning body at rest. In a binary, each body's spin also
  couples to the orbit; by the same moving potentials it should be general relativity's, but that isn't run.

*The code: studies/frame_dragging.py (the orbits, the comparison with exact Kerr in engine/exact.py, and the player).*
