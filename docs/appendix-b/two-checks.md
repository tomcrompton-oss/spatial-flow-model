# Two Checks on Every Model

Two quick checks tell a lot about a candidate model before any measurement is simulated.

1. **Conserved quantities.** A particle in a field that doesn't change with time keeps its energy; in a field the same
   all round a point, its angular momentum; in a field steady in a turning frame, the Jacobi constant. Does the model
   keep them?
2. **The flow against $g$.** Space moving with the flow should speed up at Newton's $g$, so the flow's change along
   itself should be $g$. Is it?

Scored out of 10 for the models of Part 2 and the [split model](each-body-separately.md):

| Model | Conserved quantities | The flow against $g$ |
| --- | --- | --- |
| One body | 10 | 10 |
| Flows added as vectors | 10 | 1 |
| Speed from the potential, along $g$ | 10 | 2 |
| The potential flow | 10 | 9 |
| Each body carrying its flow (turning) | 10 | 4 |
| Each body separately, any frame rule | 2–3 | 10 |

The two checks pull opposite ways. A model with one flow is one spacetime, $ds^2 = -c^2dt^2 + |d\mathbf x - \mathbf u\,dt|^2$,
and anything following its paths keeps whatever its symmetries say, whatever the flow. So every single-flow model
passes the first check, and the second is what tells them apart: only a flow with no swirl and the escape speed falls
at $g$, which is how [Potential Flow](../part2/potential-flow.md) chooses its flow. The split model has no one flow, so
each body's flow gives that body's $g$ exactly, but there is no spacetime whose energy it keeps.

*The code: studies/conserved_quantities.py, studies/flow_gravity.py; every run logs E, L, J and b as it goes (see
[File Formats](../appendix-a/formats.md)).*
