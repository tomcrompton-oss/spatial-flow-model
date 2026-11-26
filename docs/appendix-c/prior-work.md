# Prior Work

How much of the model has been done before? Its physics is general relativity, by construction, so the question is
which descriptions and constructions are already in the literature. This page compares each piece, numbered as in
[The Model, Step by Step](../conclusion/step-by-step.md), with the published work found. It comes from a targeted
search, not a full review: where nothing turned up, that only means nothing was found.

## Piece by piece

| Piece of the model | Already published | How new here |
| --- | --- | --- |
| One body: space flows in at the escape speed through flat space, and motion through it is special relativity (steps 1.1–1.2) | Painlevé (1921) and Gullstrand (1922); Hamilton and Lisle's [river model of black holes](https://arxiv.org/abs/gr-qc/0411060); Braeck and Grøn, [A river model of space](https://arxiv.org/abs/1204.0419) | Known. Part 1's step-by-step simulation is a way to show it, not new physics. |
| A spinning body's twist (step 1.3) | Hamilton and Lisle; Doran (2000); Natário, [Painlevé–Gullstrand coordinates for the Kerr solution](https://arxiv.org/abs/0805.0206). Kerr has no flat slicing at all, not even a conformally flat one ([review](https://arxiv.org/abs/2210.11057)). | Known. The no-flat-slicing result is the literature's form of what step 2.2 found: with more than one body, space can't stay flat. |
| Clocks keep free-fall time, the flow has no curl, and time is the action of free fall from rest (steps 1.2, 2.1, 3.2) | Bini, Geralico and Jantzen, [Separable geodesic action slicing in stationary spacetimes](https://arxiv.org/abs/1408.5259): unit lapse, observers falling freely from rest at infinity, Painlevé–Gullstrand and Doran as cases. Only for stationary spacetimes whose geodesics separate. | The idea is known. Using it for several moving bodies, one potential for the whole plane (step 3.2), wasn't found. |
| The same slicing at the first order beyond Newton (step 3.3) | Matarrese and Terranova, [Post-Newtonian cosmological dynamics in Lagrangian coordinates](https://arxiv.org/abs/astro-ph/9511093): dust with no vorticity, coordinates moving with the matter, Raychaudhuri's equation central | The closest match to step 3.3's corrections: the same slicing, but in coordinates moving with the matter, and for cosmology, not point masses. |
| Gullstrand–Painlevé coordinates for the Solar System at the first order beyond Newton | Xie and Kopeikin, [Reference frames, gauge transformations and gravitomagnetism in the post-Newtonian theory of the lunar motion](https://arxiv.org/abs/0905.2424), and Kopeikin and Xie, [Post-Newtonian reference frames for advanced theory of the lunar motion](https://arxiv.org/abs/0902.2416): a family of gauges for the Sun, Earth and Moon, one case of which they call Gullstrand–Painlevé | Not the same thing. Their Gullstrand–Painlevé case is a choice of spatial coordinates within the usual slicing: their clocks are slowed by the potential, as in general relativity's usual form, and there is no flow of the size $\sqrt{2GM/r}$. Nothing in it is built from observers falling freely. They show that the gravitomagnetic force depends on the gauge, for lunar ranging. |
| Space from Einstein's Hamiltonian constraint (step 2.2); the flow's corrections from the momentum constraint and Raychaudhuri's equation (step 3.3) | The 3+1 (ADM) formalism; general relativity's first post-Newtonian metric (Einstein, Infeld and Hoffmann; Blanchet and Damour; Will's framework), whose vector potential is step 3.3's moving potentials | The equations are standard. The many-body metric written out in this slicing may be new, as presentation. |
| Bodies moved with their own singular terms averaged away (step 4.1) | Hadamard's finite part; Blanchet and Faye's post-Newtonian point masses | Known. |
| The radiation reaction, entering through the flow (step 5.1) | The Burke–Thorne potential (Burke, 1971) | The potential is known. Putting it into the flow through Bernoulli's equation, so that the bodies feel it by moving with their space, wasn't searched for separately. |
| Seams and folds | Unit-lapse (geodesic) slicing is known in numerical relativity to fail as free-fall paths focus into caustics ([e.g.](https://arxiv.org/abs/gr-qc/0211028)) | Known. The folds an eccentric binary's flow has are a property of the slicing, not of the flow picture. |
| Flowing space as a fluid, and Hawking's temperature from the flow (Part 6) | Unruh (1981) and Visser, [Acoustic black holes](https://arxiv.org/abs/gr-qc/9712010): the acoustic metric has the Painlevé–Gullstrand form, needs a flow with no curl, and its horizon's temperature is set by the flow's gradient | Known. Part 6 restates it for this model's flow. |

## What looks new

- **One free-falling flow for several moving bodies.** The free-fall slicing is published for one body, for
  stationary spacetimes that separate, and for cosmological dust. A zero-energy flow for moving point masses, solved
  as one potential with seams between the bodies' regions, wasn't found. The mathematics is standard; this use of it
  seems not to be.
- **General relativity's many-body first post-Newtonian metric with clocks slowed only by their speed through space
  and Einstein's curved space, written out**, with the flow's corrections shown to be the momentum constraint and
  Raychaudhuri's equation in this slicing. New in presentation, if at all. Kopeikin and Xie's gauge family, the
  likeliest place for an equivalent, turns out not to be one.
- **The catalogue of rules that fail.** Flows added as vectors, the flow along $g$, the potential flow with flat
  space, the flow's pattern taken along, the turning flow, flat and curved, and each body in the others' flow: each
  run against lunar ranging, Cassini, radio telescopes past Jupiter, binary pulsars and the Nordtvedt test, with what
  each failure says the flow needs. Each Part's conclusion has its scorecard
  ([Part 2](../part2/conclusion.md), [Part 3](../part3/conclusion.md), [Part 4](../part4/conclusion.md)). Nothing like
  it was found. It is the most distinctive part of this work.
- **The simulation.** Particles and light stepped through each version of the flow, and compared with exact general
  relativity, its post-Newtonian equations and measurement. Useful as a test bed; code, not a claim.

## What isn't new

- The physics: the model is general relativity.
- Each equation taken alone.
- The river picture of one body, spinning or not.
- Hawking and Unruh radiation from a flow, and the analogy with sound in a moving fluid.

## A different flowing-space theory

Cahill's "dynamical 3-space" ([review](https://arxiv.org/abs/0705.4146)) also describes gravity as flowing space, but
as an alternative to general relativity that predicts differences from it, and it is not accepted in mainstream
physics. The model here is not that theory: every version that survives the tests is general relativity, described in
the time of its free-falling observers.

## In short

| | How new |
| --- | --- |
| Physics | Nothing: it is general relativity |
| Formalism | A little: the many-body, free-fall, first post-Newtonian flow, not found in the literature searched |
| Presentation and computation | Moderately: the step-by-step construction, the catalogue of failing rules, and the tests run in the flow picture |
