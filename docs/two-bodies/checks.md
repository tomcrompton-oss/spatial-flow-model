# Two checks on every model

Two checks that every version of the model can be put through, whatever its rule for the bodies:

- **Conserved quantities.** A particle in a steady field keeps its energy, in one turned about a point its angular
  momentum, and in a field that is steady in a turning frame the Jacobi constant. GR keeps these whatever the bodies.
  Does each model keep them, in its own forms?
- **The flow against g.** Space moving with the flow should fall at Newton's g, so the flow's change along its own
  path, between two close points, should be g.

Each model gets a score out of 10 for each check.

## Scores

| Model | Conserved quantities | The flow against g |
| --- | --- | --- |
| One body | **10** | **10** |
| Vector addition | **10** | **1** |
| Along g | **10** (2 with the old velocity step) | **2** |
| The eikonal flow | **10** | **9** |
| Each body carrying its flow (turning) | **10** | **4** |
| Each body separately: Galilean or Lorentz frames | **2** | **10** |
| Each body separately: carried frames | **3** | **10** |
| Each body separately: the other frame rules (local, free-fall, heavier, heavier-only, heavier-centre) | **2** | **10** |

The two checks pull opposite ways. A model with one flow is one spacetime, ds² = −c²dt² + |dx − u dt|², and a particle
following its paths keeps whatever the symmetries say, whatever the flow. So with the momentum step every single-flow
model passes the first check, and the flow against g is what tells them apart. The split model has no one flow, so
each body's flow alone gives that body's g exactly, but there is no spacetime whose energy it keeps.

## Conserved quantities

A particle's conserved quantities, in the flow model's forms (per unit mass; engine/flow.py `Calculator.conserved`):
the metric has momentum $\mathbf p = \gamma\mathbf w$ and $-p_t = \gamma(c^2 + \mathbf u\cdot\mathbf w)$, so

- **E** $= \gamma(c^2 + \mathbf u\cdot\mathbf w) - c^2$, kept when the bodies are at rest;
- **L** $= \gamma\,\mathbf x\times\mathbf w$ about the body, kept with one body (a rotating hole adds
  $a\,\gamma(\mathbf u\cdot\mathbf w)/c$, from the twist in its metric; without it L drifts 130 times faster);
- **J** $= E - \Omega L$, the Jacobi constant, kept when the bodies turn together and the flow is steady in their
  turning frame;
- for light only the ratio, its impact parameter **b** $= cL/(E + c^2)$.

The split model has no metric, so its E is built as it builds everything, body by body: the energy each body's flow
alone gives the particle, added up, less the free particle's for each body after the first,
$E = \sum_k e(\mathbf v - \mathbf u_k, \mathbf u_k) - (N-1)\,e(\mathbf v, 0)$. For slow particles that is Newton's
$v^2/2 - \sum GM/d$. Newton's own calculator logs $v^2/2 - \sum GM/d$ and $\mathbf x\times\mathbf v$.

Every run now logs these as it goes – csv columns E, L, J and b ([File formats](../formats.md)) – and reports at its
end how far each moved. [studies/conserved_quantities.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/conserved_quantities.py)
puts each model through four orbits, all in strong fields so relativistic terms show:

| Case | Bodies | The particle | Kept |
| --- | --- | --- | --- |
| One body | 1 solar mass | 200–600 Schwarzschild radii | E, L |
| Pair | 1 and 0.1 solar masses at rest, 2 × 10⁷ m apart | round the lighter, 2–3 × 10⁵ m (0.027c) | E |
| Around | 1 and 0.5 solar masses at rest, 10⁶ m apart | round both, 1.5–2.5 × 10⁷ m, through the eikonal seam twice an orbit | E |
| Turning | the pair going round each other, the eikonal flow turning with them | round the lighter | J |

Each runs at three step sizes, and the drift per orbit (from its values at each periapsis, so the swing round an orbit
drops out) is taken to zero step, so what is left is the model's, not the step's. It is given as a fraction of the
quantity, and in "1PN units": over ε, the larger of v²/c² and ΣGM/dc² at the start. GR's first corrections to the
energy are about ε of it, so a model with no conserved energy at that order drifts or swings by about 1 of these.

| Model | Drift per orbit, taken to zero step (1PN units) | Score |
| --- | --- | --- |
| One body (E, L) | 10⁻⁸ | 10 |
| Vector addition | 10⁻⁶ round both; round the lighter its wrong pull drags the particle in within 4% of the run | 10 |
| Along g, momentum step | 10⁻⁷–10⁻⁶ | 10 |
| Along g, the old velocity step | −11 round the lighter, +0.12 round both: 1% of E an orbit, at every step size | 2 |
| The eikonal flow | 10⁻⁷–10⁻⁶, through the seam too | 10 |
| Turning (J) | 3 × 10⁻⁷ | 10 |
| Split, Galilean = Lorentz (the bodies are at rest) | −0.07 round the lighter, −9 round both | 2 |
| Split, free-fall, local, heavier, heavier-only, heavier-centre | ±0.004–0.008 round the lighter, −5 to −9.5 round both | 2 |
| Split, carried | +0.005 round the lighter, +0.0014 round both | 3 |

- **The single flows** keep everything to the floor. The eikonal flow keeps E through its seam because the jump there
  keeps the energy by design.
- **Along g** shows why the step mattered. Its flow has curl, so the old rule
  $d\mathbf w/dt = -(\mathbf w\cdot\nabla)\mathbf u$ is not the metric's path, and it lost 1% of the energy an orbit.
  With the momentum step it keeps it. Its failure is in the flow itself (the next check), not in the conservation.
- **The split model** keeps no energy at the first relativistic order: round both bodies it drifts by several times
  the 1PN size every orbit, whatever the frame rule. 'carried' – every body's flow carried by the others' space where
  the particle is, the nearest the split model comes to one shared space – drifts the least, 20–2000 times less than
  the others, but still not to the floor. The binaries of the [split page](split.md) show the same thing for the
  bodies themselves: their centre of mass accelerates by itself (momentum), and their period shrinks 10⁶ times faster
  than gravitational waves allow (energy).

## The flow against g

Space at x moves at the flow u, so after a short time h it is at x + u h, and if it falls at g it moves there at
u + g h. So the flow's change along itself is g:

$$\mathbf a = (\mathbf u\cdot\nabla)\mathbf u + \frac{\partial \mathbf u}{\partial t}
\approx \frac{\mathbf u(\mathbf x + \mathbf u h/2,\ t + h/2) - \mathbf u(\mathbf x - \mathbf u h/2,\ t - h/2)}{h}$$

([studies/flow_gravity.py](https://github.com/tomcrompton-oss/spatial-flow-model/blob/main/studies/flow_gravity.py))
takes the two points 10⁻⁴ of the distance to the nearest body either side of x, both from x's side of any seam, and
again at half that, the two combined to take out the difference's own h² error. a is compared with Newton's g from
the bodies where they are at t, over a grid across the bodies (a tenth of their separation apart) and rings round each
(at 0.01–0.3 of their separation). The error is |a − g| as a fraction of the sum of the bodies' pulls there,
Σ GM/d²: the size a cross term between them would have (g itself is 0 at the saddle between them).

For the curl-free flows this is exact in principle: $(\mathbf u\cdot\nabla)\mathbf u = \nabla(u^2/2)$, and
$u^2/2 = \sum GM/d$. The split model has no single flow, so it is checked as its steps use the flows: each body's
flow alone, in that body's frame, the difference mapped back to the lab, the bodies' parts added. The sum of its flows,
which no step uses, is the vectors' flow.

| Model | Error (median, max) | At the Earth's surface, the Sun 1 AU away | Score |
| --- | --- | --- | --- |
| One body | 3 × 10⁻¹², 2 × 10⁻¹¹ | | **10** |
| Vectors | 0.4–1.2, up to 3.3 | 74 m/s² | **1** |
| Along g | 7–17% with comparable masses; 3 × 10⁻⁶ Sun–Earth | 0.54 m/s² | **2** |
| Eikonal, exact two-body | 10⁻¹¹, ≤ 7 × 10⁻⁸ | 1 × 10⁻⁷ m/s² | **9** |
| Eikonal, ray tables (three bodies) | 8 × 10⁻⁷, 7 × 10⁻⁵ | | (the same model) |
| Turning | near the bodies 10⁻¹¹–10⁻⁵; 56% of the plane has no flow, and much of the rest is off by 8–40% | 4 × 10⁻⁶ m/s² | **4** |
| Split, Galilean or Lorentz frames | 10⁻¹⁵–10⁻¹², ≤ 4 × 10⁻¹⁰ | 3 × 10⁻¹¹ m/s² | **10** |
| Split, frames moved by the others' flow (local, free-fall, carried, heavier, heavier-only) | 10⁻¹³–5 × 10⁻⁸, ≤ 7 × 10⁻⁷ | 6 × 10⁻⁷ m/s² | **10** |

For scale: the Sun's tide at the Earth's surface is 1.0 × 10⁻⁶ m/s².

- **One body**: the floor, set by rounding.
- **Vectors**: the cross term $\nabla(\mathbf u_1\cdot\mathbf u_2)$ is as big as the pulls themselves, so not one
  point matches with comparable masses. At the Earth's surface it is the 37–74 m/s² of the
  [vectors page](vectors.md).
- **Along g**: the flow has curl, so $(\mathbf u\cdot\nabla)\mathbf u = \nabla(u^2/2) - \mathbf u\times(\nabla\times
  \mathbf u)$, and the curl term is Newtonian in size. Close to the Earth it is half a m/s², half a million times the
  Sun's tide.
- **Eikonal**: matches everywhere, each side of its seam. Across the seam the flow jumps by design, so there it has no
  difference to take; that is the one point off 10. The ray tables (needed for three bodies) match to their
  interpolation, 10⁻⁶–10⁻⁴.
- **Turning**: inside each body's region it matches – round the Sun out to 0.1 AU to 10⁻¹¹–10⁻⁹, round the Earth to
  10⁻⁶ at 0.01 AU, but 2% at 0.1 AU. Most of the plane has no flow at all (the Sun's paths with this Jacobi constant
  turn back at 2/3 AU), and past the Earth's Hill sphere its paths cross, where the flow is off by order 1. These are
  the limits found on [its page](turning.md); this check measures them.
- **Split**: each body's flow alone is its own one-body flow, so each part is that body's g exactly, and the parts add
  to Newton's. The rules that move a body's frame at another body's flow U (local, free-fall, carried, heavier) change
  a by order (U/c)², 10⁻⁸–10⁻⁷ of the pulls: a relativistic term, not a Newtonian error, and GR has terms of that
  size too. It scores 10 because it never adds its flows: their sum would score the vectors' 1, and having no single
  flow is what costs it the binary tests.
