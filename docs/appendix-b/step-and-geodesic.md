# The Step and the Geodesic

Part 1's [procedure](../part1/mechanics/newtonian.md#the-procedure) moves a particle with its space, then through it,
then changes its velocity through space by the difference in the flow between the two places. For every flow in the
main text that is exactly the path a particle takes through flowing space, the geodesic of
$ds^2 = -c^2dt^2 + |d\mathbf x - \mathbf u\,dt|^2$. But only because those flows have no swirl.

Light crossing [regions of space flowing ever faster](../part1/mechanics/special-relativistic.md#movement-through-regions-of-space)
is a flow with swirl: space flows downwards, faster to the right. Three ways of moving light through it:

<iframe src="../../viewer/index.html?player&run=../runs/curlRegions/part1_regions.full.json" width="100%" height="480" loading="lazy" title="Light crossing a flow with curl: the step and the geodesic"></iframe>

*Light crossing space that flows downwards ever faster to the right, up to 0.8 c. Dashed: the procedure with the change
in the flow added as plain vectors. Solid: added relativistically. Dotted: the true geodesic of the flow's metric.*
[Open full screen](../../viewer/index.html?run=../runs/curlRegions/part1_regions.full.json){ target=_blank }

| Method | Its velocity through space turns by | Its velocity at the end | Its speed through space |
| --- | --- | --- | --- |
| the procedure, plain vectors | 38.7° | (1.00 c, 0) | 1.28 c |
| the procedure, relativistic | 41.6° | (0.75 c, −0.14 c) | c |
| the geodesic | 0° | (1.00 c, −0.80 c) | c |

The geodesic keeps its velocity through space and is simply carried down with the space; the procedure turns it. The
difference is the swirl: the procedure's rule, $d\mathbf w/dt = -(\mathbf w\cdot\nabla)\mathbf u$, is the geodesic's
only when $\nabla\mathbf u$ is symmetric, which is what having no swirl means. The geodesic's own rule acts on the
momentum, $d\mathbf p/dt = -(\nabla\mathbf u)\cdot\mathbf p$, and that is why the simulator steps on the momentum
$\mathbf p = \gamma\mathbf w$ rather than on $\mathbf w$ ([The Simulator](../appendix-a/simulator.md)).

**Why it is a rabbit hole.** Gravity's flows in the main text have no swirl, apart from a spinning body's, so Part 1's
procedure is exact for them, and is the easier picture. Flows with swirl turn up in a spinning body's space and a
gravitational wave crossing the plane, and there the simulator's momentum step is what is used.

*The code: studies/part1_examples.py (regions); engine/flow.py (the momentum step).*
