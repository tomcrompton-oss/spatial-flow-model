# Part 5 – Gravitational Waves

A gravitational wave is a ripple in spacetime, travelling at the speed of light. In flowing space it is space itself
that ripples: a wave is a flow of space that changes with time, and where it travels along the plane it also curves
space. This part asks four questions of the model:

1. Can it hold a gravitational wave at all, travelling in any direction?
2. Where do waves come from: what equation makes them, and what is their source?
3. How does a body lose the energy its waves carry away, if gravity is only space moving?
4. Does a binary moving by the model's own rules lose energy at GR's rate – the rate the Hulse–Taylor pulsar
   measures?

The answer to each is yes, to the order the model is built to: GR's leading-order (quadrupole) radiation, on top of
its first post-Newtonian motion. What lies beyond that is set out at the end.

## A wave is a flow of space

In GR a plane wave travelling along $z$, straight through the $(x, y)$ plane, stretches space along one direction while
squeezing it along the other, with a strain $h$. Measuring distances properly rather than in GR's usual (TT)
coordinates, it becomes, to first order in $h$,

$$
ds^2 = -c^2 dt^2 + |d\mathbf X - \mathbf u\,dt|^2, \qquad
\mathbf u = \tfrac12\left(\dot h_+ X + \dot h_\times Y,\; \dot h_\times X - \dot h_+ Y\right)
$$

which is the flow model's form exactly: flat space, flowing. The wave is a shear of space, with no curl and no
divergence. Free particles stay with the space, and a ring of them stretches and squeezes as the space does. Against
GR at $h = 10^{-6}$, free particles, particles started at rest, and light sent to a mirror and back all agree to about
$10^{-5}$ of the wave's own effect.

<iframe src="../viewer/index.html?player&run=../runs/gravWave/gravWave.full.json" width="100%" height="560" loading="lazy" title="Rings of free particles in a wave through the plane"></iframe>

*Three rings of free particles in a 100 Hz wave passing through the plane, exaggerated to $h = 0.2$: plus polarization
(left), cross (middle) and circular (right). Each moves with its space.*
[Open full screen](../viewer/index.html?run=../runs/gravWave/gravWave.full.json){ target=_blank }

## A wave travelling across the plane

A wave travelling *within* the plane, left to right, is harder. Written the same way, it is

$$
ds^2 = -c^2 dt^2 + dN^2 + \left(dM - \tfrac12 \dot h M\,dt + \tfrac{1}{2c} \dot h M\,dN\right)^2
$$

with $N$ along the wave and $M$ across it. The first two terms in the bracket are a flow,
$\mathbf u = \tfrac12 \dot h\,(\mathbf m\cdot\mathbf X)\,\mathbf m$. The last is not: it curves space, by how fast the
flow changes along the wave, and flat space cannot hold it. Flat space alone gets slow things right, but light at an
angle to the wave comes out wrong by up to half of the effect.

But in the model as it now stands space *is* curved (Einstein's constraint sets its shape round the bodies; [to be
written up](part2/curved-space.md)). With the clocks as before and the same flow, that last term is simply space's
metric:

$$
\gamma = \delta + a\,(\mathbf n\mathbf m + \mathbf m\mathbf n) + a^2\,\mathbf n\mathbf n, \qquad a = \frac{\dot h\,(\mathbf m\cdot\mathbf X)}{2c}
$$

and the wave is held exactly, as the one through the plane is:

| At $h = 10^{-6}$, against GR | Flat flow | Flow and curved space | GR's TT form (a check) |
| --- | --- | --- | --- |
| Light to a mirror and back, any angle, 0.01–1 wavelength (error / $hL/c$) | 0.46 | $9 \times 10^{-6}$ | $5 \times 10^{-6}$ |
| Particles moving along the wave at 0–0.99c (error / $h y_0$) | 2.9 | $1.2 \times 10^{-6}$ | 0 |

The wave is still a flow of space; space is curved by how that flow varies along the wave.

## Where waves come from

The model is GR in the time of observers falling freely with the flow: their clocks tick at the same rate
everywhere, and everything else is in the flow $\mathbf u$ and in space's metric $\gamma$. Einstein's equations then
say how space evolves:

$$
\frac{\partial\gamma_{ij}}{\partial t} = -2K_{ij} - (D_i u_j + D_j u_i)
$$

with $K_{ij}$ the rate space is being stretched, and a second equation for how $K$ changes. The model already uses
Einstein's constraints and part of the second equation. What is left – the trace-free part – is where waves live.

Far from the bodies, write $\gamma = \delta + h$ and keep what is first order in the wave; then take the part of $h$
that is transverse and trace-free (TT), the part a wave carries. Two things drop out:

- **The flow.** It enters only as $D_i u_j + D_j u_i$, a gradient, which has no TT part. However the flow moves near
  the bodies, the waves see only space.
- Anything proportional to $\delta_{ij}$.

What is left is a wave equation for space,

$$
\frac{1}{c^2}\frac{\partial^2 h^{TT}}{\partial t^2} - \nabla^2 h^{TT} = \frac{16\pi G}{c^4}\,\tau^{TT}
$$

travelling at $c$, its source $\tau$ the bodies' momentum flux and the gravitational field's own stress. Solved with
the delay light takes to arrive, $h_{ij} = (4G/c^4)\int \tau_{ij}(t - |\mathbf x - \mathbf x'|/c)/|\mathbf x - \mathbf
x'|\,d^3x'$, and far away this is the quadrupole formula,

$$
h^{TT} = \frac{2G}{c^4 D}\,\ddot Q^{TT}(t - D/c)
$$

with $Q$ the binary's quadrupole moment. Solving it numerically for a circular binary, the source integrated over all
space gives $\tfrac12\ddot Q$ (as conservation requires) to $10^{-6}$, and the solution far away gives the quadrupole
formula to its next order: $(v/c)^2$ seen along the binary's axis, and the octupole, at $v/c$, seen edge on for
unequal masses. Half the wave of a circular binary comes from the bodies' motion; **the other half from the stress in
the field between them.**

## Losing energy through the flow

Waves carry energy away, so the orbit must lose it. In GR this is the radiation reaction, at leading order the
Burke–Thorne potential, $\Phi_{RR} = \frac{G}{5c^5}\,x_i x_j\,Q^{(5)}_{ij}$: a tiny extra potential, changing with the
fifth time derivative of the quadrupole.

In flowing space nothing pushes on the bodies; they move with their space. But space itself accelerates by
Bernoulli's equation, $\partial\phi/\partial t + \tfrac12|\mathbf u|^2 = -\Phi$, with $\mathbf u = \nabla\phi$.
Anything moving through a flow without curl then accelerates at $-\nabla\Phi$, whatever its speed through the space.
So put the reaction's potential into $\Phi$ and the flow changes by a little,

$$
\delta\mathbf u = \nabla\delta\phi, \qquad \frac{\partial\,\delta\phi}{\partial t} + \mathbf u\cdot\nabla\delta\phi = -\Phi_{RR}
$$

and everything in the flow feels $-\nabla\Phi_{RR}$: **the energy the waves carry off leaves through space's own
motion**, with no force on the bodies. Round a heavy body, for a light one on a nearly circular orbit, the change is
one radial profile for every orbit, and at most about $6 \times 10^{-7}$ of the flow.

A 1 solar-mass body round a 10 solar-mass one, moving in the corrected flow by the model's own step and nothing else:

| $GM/c^2r$ | Energy lost, against the quadrupole formula's power | Radius shrinking, against Peters' rate |
| --- | --- | --- |
| 0.004 | +0.60% | +1.31% |
| 0.002 | +0.30% | +0.62% |

Both differences halve with $GM/c^2r$: they are the first post-Newtonian size, the orbit being GR's while the formulas
are Newton's.

## A binary: the Hulse–Taylor pulsar

With two bodies of similar mass, each moves with the regular part of its own space, and the model's two-body motion is
GR's first post-Newtonian motion (Einstein–Infeld–Hoffmann; see [Moving With Its Own Space](part4/moving-with-its-own-space.md)). Bernoulli's equation holds
for that flow too, so a body moving with its space feels $-\nabla\Phi_{RR}$ at itself, whatever the masses. The binary
then moves by EIH plus the reaction:

| Check | Result |
| --- | --- |
| PSR B1913+16, Hulse and Taylor's: the orbital period's rate | $-2.40343 \times 10^{-12}$, **0.999991 of GR's** (observed: 0.9983 ± 0.0016 of GR) |
| An eccentric orbit, $e = 0.6$: energy and angular momentum lost | within 1.5% and 2.9% of Peters and Mathews at $GM/c^2a$ = 0.001 and 0.002, the first post-Newtonian size |
| Circular orbits, $x$ = 0.001–0.01: how fast they shrink | Peters' rate × $(1 + kx)$, $k$ = 1.37–1.48, as this motion and reaction predict (1.5) |

The binary below spirals in from 150 km apart, two neutron stars in their last 0.4 seconds. Beside it, though really
far away along its axis, a ring of free particles in its waves, exaggerated so the strain reaches 0.3: the ring's
stretching grows and quickens – the chirp a detector hears.

<iframe src="../viewer/index.html?player&run=../runs/binaryWaves/binaryWaves.full.json" width="100%" height="560" loading="lazy" title="A binary's inspiral and a ring in its waves"></iframe>

*Press Play: two 1.4 solar-mass bodies spiralling in (blue and orange – the same spiral, so until it plays one hides
the other), and a ring of free particles in their waves (green, the strain scaled up). The binary here moves by
Newton plus the reaction; the model's own motion adds GR's first post-Newtonian corrections.*
[Open full screen](../viewer/index.html?run=../runs/binaryWaves/binaryWaves.full.json){ target=_blank }

## The waves travelling outward

Seen across the binary's own plane, its waves wind outward as two spiral arms: space stretched across the way the
wave travels (red) and squeezed (blue), each arm leaving the binary twice an orbit, moving out at $c$ and fading as
$1/r$. Rings of free particles sit at one and two wavelengths out, in two directions, each moved by the model in its
own patch of the outgoing wave (a plane wave there, held exactly with curved space, as above). The further rings
stretch half as much, and later; the rings at 135° stretch when the arms reach them.

<iframe src="../viewer/index.html?player&run=../runs/binaryOutgoing/binaryOutgoing.full.json" width="100%" height="600" loading="lazy" title="A binary's waves travelling outward across its plane"></iframe>

*Press Play: two 1.4 solar-mass bodies 100 km apart (the dot at the centre), their waves at 194 Hz (wavelength 1,545
km) over eight wave periods, with the strain scaled up so the nearer rings stretch by about a quarter. Within half
a wavelength of the binary the waves haven't fully formed (the near zone), so there the arms fade out towards the
centre.*
[Open full screen](../viewer/index.html?run=../runs/binaryOutgoing/binaryOutgoing.full.json){ target=_blank }

## What is left

- **The waves' next order.** For circular orbits GR's own rate is Peters' × $(1 - 2.9x)$, not $(1 + 1.5x)$. The
  difference is the waves' own first post-Newtonian corrections – from the source beyond its quadrupole (the
  octupole, the current quadrupole, the quadrupole's own corrections) and the reaction's next terms – which neither
  the model nor GR's leading-order reaction includes.
- **Space near the bodies.** The model's own second-order terms (from the flow) differ from Newton's field stress
  point by point. They cannot change the far wave, whose source integral conservation fixes, but they set space's TT
  part near the bodies, at second post-Newtonian order – beyond the model's space, built so far to first order.
- **Three dimensions.** The simulation works in a plane, so waves are followed only along the binary's axis and in
  its plane.

*The code: engine/radiation.py, engine/wave_source.py and engine/metric.py (WaveSpacetime); the studies
binary_waves.py, grav_wave_curved.py, wave_source.py, flow_reaction.py and binary_inspiral.py.*
