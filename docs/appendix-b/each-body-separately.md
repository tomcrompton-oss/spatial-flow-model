# Each Body Separately

**The idea.** One body's flow is general relativity exactly, and to first order in $G$, general relativity's effects of
several bodies simply add. So instead of looking for one flow that serves every body, give each body its own exact
one-body flow, work out what each alone would do to a particle in a step, and apply the changes one after the other.
Numerically it is operator splitting: the step for one body, then the step for the next.

With no single flow, clocks and light need rules of their own (each body changes a clock's rate, and light's
slowness, by what it would alone), and a moving body needs a frame: the particle is Lorentz-boosted into the body's
free-fall frame in the space the other bodies' flows carry past it.

## With one body much heavier

It passes most tests: Newton's $g$, clocks on the Earth and in GPS orbit, light past Jupiter, radar to a mirror at the
Moon's distance, the whole system moving together, and particles near light's speed never outrunning light.

The Moon's own orbit is harder. With free-fall frames, its de Sitter precession comes out about half of GR's. Carrying
the Earth's flow in the Sun's space where the Moon is ("heavier-only" frames) fixes that: GR's precession, and lunar
ranging within the test's floor. But then a bound pair falling towards the Sun falls too slowly, the Nordtvedt effect,
a million times what lunar ranging allows.

## With comparable masses

In a binary each body moves in the other's flow. General relativity's orbit turning is exact for any mass ratio, and
the model drifts from it as the masses become comparable:

| Mass ratio | Free-fall frames: model / GR | Lorentz frames: model / GR | The pair's centre |
| --- | --- | --- | --- |
| 1 | 0.834 | 1.250 | still (by symmetry) |
| 0.1 | 0.946 | 1.083 | accelerates at 0.17 m/s² |
| 0.01 | 0.994 | 1.011 | accelerates at 0.07 m/s² |

The pair's centre accelerating by itself is the clearest sign: momentum isn't kept, and binary pulsars rule that out.

## Is there a better frame rule?

Running general relativity with each of its cross terms (one body's pull depending on a third, or on the body pulled)
switched off shows that the model's errors match no combination of missing terms: they come with its coordinates. No
rule built from the bodies' potentials alone gets the Nordtvedt effect right either; even with every cross term put in
by hand, it sits at $\eta = -1$ instead of 0.

**What it taught.** Cross terms between bodies only make sense once the bodies share one spacetime, solved together.
Separate one-body flows can't give that, however they are combined. That is the lesson Part 4's
[Each Body in the Others' Flow](../part4/each-body-in-the-others-flow.md) arrives at too, and the one potential of
[Part 3](../part3/one-potential.md) is what supplies the shared spacetime.

*The code: engine/split.py; studies/split_bodies.py, split_checks.py, split_more.py, binary_pulsar.py,
cross_terms.py, flow_sign.py, frame_checks.py.*
