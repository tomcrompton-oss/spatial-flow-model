# Prior work

How much of the final model ([model 8, with model 9's spin](evolution.md)) has been done before? Its physics is
general relativity, by construction, so the question is which descriptions and constructions are already in the
literature. This page compares each piece with the published work found so far. It comes from a targeted search, not a
full review. Where nothing turned up, that only means nothing was found.

## Piece by piece

| Piece of the model | Already published | How new here |
| --- | --- | --- |
| One body: space flows in at the escape velocity through flat space, and motion through it is special relativity (models 1–2) | Painlevé (1921) and Gullstrand (1922); Hamilton and Lisle's [river model of black holes](https://arxiv.org/abs/gr-qc/0411060); Braeck and Grøn, [A river model of space](https://arxiv.org/abs/1204.0419) | Known. Part 1's step-by-step simulation is a way to show it, not new physics. |
| A spinning body's twist (model 9) | Hamilton and Lisle; Doran (2000); Natário, [Painlevé–Gullstrand coordinates for the Kerr solution](https://arxiv.org/abs/0805.0206). Kerr has no flat slicing at all, not even a conformally flat one ([review](https://arxiv.org/abs/2210.11057)). | Known. The no-flat-slicing result is the literature's form of model 4's step: space can't stay flat. |
| Clocks keep free-fall time (N = 1), the flow has no curl, and time is the Hamilton–Jacobi action of free fall from rest | Bini, Geralico and Jantzen, [Separable geodesic action slicing in stationary spacetimes](https://arxiv.org/abs/1408.5259): unit lapse, observers falling freely from rest at infinity, Painlevé–Gullstrand and Doran as cases. Only for stationary spacetimes whose geodesics separate. | The idea is known. Using it for several moving bodies, the J = 0 flow of model 5, wasn't found. |
| The same slicing at post-Newtonian order | Matarrese and Terranova, [Post-Newtonian cosmological dynamics in Lagrangian coordinates](https://arxiv.org/abs/astro-ph/9511093): dust with no vorticity, synchronous comoving coordinates, Raychaudhuri's equation central | The closest match to the corrections of models 6 and 8: the same slicing, but in coordinates moving with the matter, and for cosmology, not point masses. |
| Gullstrand–Painlevé coordinates for the Solar System at first post-Newtonian order | Xie and Kopeikin, [Reference frames, gauge transformations and gravitomagnetism in the post-Newtonian theory of the lunar motion](https://arxiv.org/abs/0905.2424): a family of first post-Newtonian gauges for the Sun, Earth and Moon, one of which they identify as Gullstrand–Painlevé; they note it hadn't then been used in the Solar System's relativistic celestial mechanics | The nearest prior art for model 8. Their gauge is a coordinate change per body; whether its N-body metric has N = 1 and a flow with no curl wasn't confirmed. They also show that the gravitomagnetic force depends on the gauge, for lunar ranging. |
| Space from Einstein's Hamiltonian constraint (model 4); the flow's corrections from the momentum constraint and Raychaudhuri's equation (models 6, 8) | The ADM formalism; GR's first post-Newtonian metric (Einstein, Infeld and Hoffmann; Blanchet and Damour; Will's PPN), whose $g_{0i}$ is model 8's $4\mathbf U_j$ | The equations are standard. The N-body metric written out in this slicing may be new, as presentation. |
| Bodies moved with their own singular terms removed (model 7) | Hadamard's partie finie; Blanchet and Faye's post-Newtonian point masses | Known. |
| Seams and folds | Unit-lapse (geodesic) slicing is known in numerical relativity to fail as free-fall paths focus into caustics ([e.g.](https://arxiv.org/abs/gr-qc/0211028)) | Known. The folds the eccentric study looks for are a property of the slicing, not of the flow picture. |
| Flowing space as a fluid | Unruh (1981) and Visser, [Acoustic black holes](https://arxiv.org/abs/gr-qc/9712010): the acoustic metric has the Painlevé–Gullstrand form, needs a flow with no curl, and can't be exactly Schwarzschild | An analogy, known. |

## What looks new

- **One free-falling flow for several moving bodies.** The free-fall slicing is published for one body, for stationary
  spacetimes that separate, and for cosmological dust. A J = 0 Hamilton–Jacobi flow for moving point masses, solved
  as one potential with seams between the bodies' regions, wasn't found. The mathematics is standard; this use of it
  seems not to be.
- **GR's N-body first post-Newtonian metric with N = 1 and Einstein's space, written out**, with the flow's corrections
  shown to be the momentum constraint and Raychaudhuri's equation in this slicing. New in presentation, if at all.
  Xie and Kopeikin's gauge family is where an equivalent would most likely be, and it should be checked in full
  before this is claimed.
- **The catalogue of rules that fail.** Vector addition, the flow along g, the eikonal, turning, split and carried
  flows, each run against lunar ranging, Cassini, VLBI and the binary pulsars, with what each failure says the flow
  needs ([scorecard](scorecard.md)). Nothing like it was found. It is the most distinctive part of this work.
- **The simulation.** Particles and light stepped through each version of the flow, and compared with exact GR, GR's
  post-Newtonian equations and measurement. Useful as a test bed; code, not a claim.

## What isn't new

- The physics: the model is GR.
- Each equation taken alone.
- The river picture of one body, spinning or not.

## A different flowing-space theory

Cahill's "dynamical 3-space" ([review](https://arxiv.org/abs/0705.4146)) also describes gravity as flowing space, but
as an alternative to general relativity that predicts differences from it, and it is not accepted in mainstream
physics. The model here is not that theory: every version that survives the tests is general relativity, described in
the coordinates of its free-falling observers.

## In short

| | How new |
| --- | --- |
| Physics | Nothing: it is GR |
| Formalism | A little: the many-body free-fall first post-Newtonian flow, if not already in Kopeikin's gauge family |
| Presentation and computation | Moderately: the step-by-step construction, the catalogue of failing rules, and the tests run in the flow picture |
