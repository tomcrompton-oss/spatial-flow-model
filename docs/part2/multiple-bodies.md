# Multiple Bodies

Nothing in the potential flow, or in curved space, is special to two bodies. The flow's speed comes from all the
bodies' potentials added together, and it has no swirl:

$$
\mathbf u = -\nabla S, \qquad |\nabla S|^2 = \sum_k \frac{2GM_k}{d_k}
$$

and space is stretched across it by $u^2/c^2$, whatever the number of bodies. Each body has a region of its own,
filled by the flow that runs into it, and the regions meet at seams.

For two bodies the flow can be worked out exactly. For more, the simulation builds it numerically: it follows the
paths running out of each body, and where two bodies' paths both reach a point, gives the point to the body whose
$S$ there is smaller.

!!! note "Reader's note"
    The potential flow's equation has names in other parts of physics, and these are good further reading. None of it
    is needed to follow this page.

    - [The eikonal equation](https://en.wikipedia.org/wiki/Eikonal_equation): the same equation describes wavefronts
      in optics, with the flow's paths as the light rays.
    - [The Hamilton–Jacobi equation](https://en.wikipedia.org/wiki/Hamilton%E2%80%93Jacobi_equation): with zero
      energy, it describes the paths of things that fall from rest far away, which is what the flow follows.
    - [Potential flow](https://en.wikipedia.org/wiki/Potential_flow): the fluid-dynamics name for a flow with no
      swirl.
    - [Euler's three-body problem](https://en.wikipedia.org/wiki/Euler%27s_three-body_problem): motion round two fixed
      centres, which is why the two-body flow can be worked out exactly.

## Three bodies

Take three black holes of one solar mass each, held at the corners of a triangle 1 AU across:

![The potential flow round three equal bodies at the corners of a triangle: the flow comes in from far away and falls into each body; three dashed seams run out from the centre, between each pair of bodies, and meet at the centre; between the bodies, the flow leaves the seams on both sides and runs to each body](images/threebodies.svg)

The three seams run out between each pair of bodies and meet at the centre, where the three pulls cancel and $g$ is
zero. Between the bodies, as with two, space flows out of the seams on both sides, towards each body.

## Paths among three bodies

The simulation runs five paths round and through the three, in the potential flow and under Newton's gravity from the
same starts:

<iframe src="../../viewer/index.html?player&run=../runs/threeBodies/threeBodies.full.json" width="100%" height="520" loading="lazy" title="Paths among three bodies in the potential flow"></iframe>

*The potential flow (solid) and Newton's gravity (dashed), over the flow and its seams: circles round all three at
2 AU (blue) and 4 AU (orange), an ellipse (green), a path through the middle (amber), and a fall from rest (violet).*
[Open full screen](../../viewer/index.html?run=../runs/threeBodies/threeBodies.full.json){ target=_blank }

| Path | Seams crossed | Potential flow | Newton's gravity |
| --- | --- | --- | --- |
| A circle 2 AU from the centre, ten times round | 3 an orbit | closest approach moves on 32.8775° an orbit | 32.8781° |
| A circle 4 AU from the centre, nine times round | 3 an orbit | 7.3013° an orbit | 7.3024° |
| An ellipse, 1.4 to 3.3 AU, eight times round | 3 an orbit | 33.6168° an orbit | 33.6161° |
| From 5 AU out at 40 km/s, through the middle | 2 | after 1.2 years, 7.5 AU out and 0.00005 AU from Newton's path | |
| From rest 3 AU out, beside a seam | several | separates from Newton's path after passing close to a hole | |

*(The three bodies' pull isn't that of one body at the centre, so even Newton's orbits precess.)* The orbits and the
path through the middle match Newton's gravity, the orbits crossing the seams three times each time round. The fall
passes close to one of the holes (Newton's path comes within 75,000 km of it, about 25,000 Schwarzschild radii): close enough that relativity's own corrections, which the flow
model has and Newton's gravity doesn't, start to matter. After that, the two paths separate, as paths among three
bodies do. (Newton's own path is the same at half the step, to 5 × 10⁻⁸ AU, so the difference is not the step.)

## Curved space with three

The curved space is built from the flow alone, so it carries over unchanged: stretched across the flow by $u^2/c^2$,
round three bodies as round two. The tests that needed it, lunar laser ranging and light past Jupiter, were run with
two bodies, where the third body of the solar system adds only small corrections.

*The code: studies/three_bodies.py; the flow for any number of bodies: engine/eikonal.py.*
