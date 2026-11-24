# Along g

**The rule:** the flow's speed comes from the bodies' potentials added together, and it points the way gravity pulls:

$$
|\mathbf u|^2 = \sum_i \frac{2GM_i}{d_i}, \qquad \mathbf u \parallel \mathbf g .
$$

**Verdict: ❌ fails.** Space moving with this flow does not fall at g, so the model's particles don't either.

## Why it might make sense

The speed is the part clocks feel. With $|\mathbf u|^2 = 2U$, a clock at rest ticks at $\sqrt{1 - 2U/c^2}$, GR's rate
to first order, for any number of bodies. That fixes the speed. For the direction, the obvious choice is the way
things fall: in one body's flow, space falls straight in, along g, and this keeps that.

<figure markdown>
<svg viewBox="0 0 640 270" width="100%" style="max-width:640px" role="img" aria-label="The flow along g, and space falling off it">
  <defs>
    <marker id="ag" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1baf7a"/></marker>
    <marker id="ao" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#e8590c"/></marker>
  </defs>
  <circle cx="200" cy="200" r="22" fill="none" stroke="currentColor" stroke-width="2"/>
  <text x="200" y="245" text-anchor="middle" fill="currentColor" font-size="15">A</text>
  <circle cx="440" cy="200" r="22" fill="none" stroke="currentColor" stroke-width="2"/>
  <text x="440" y="245" text-anchor="middle" fill="currentColor" font-size="15">B</text>
  <path d="M330,30 C300,70 290,110 275,150 C268,168 240,185 222,195" fill="none" stroke="#1baf7a" stroke-width="2.5" stroke-dasharray="7 5" marker-end="url(#ag)"/>
  <text x="120" y="120" fill="#1baf7a" font-size="15">flow line, along g</text>
  <path d="M330,30 C318,80 330,130 370,160 C400,180 470,150 520,100" fill="none" stroke="#e8590c" stroke-width="2.5" marker-end="url(#ao)"/>
  <text x="430" y="85" fill="#e8590c" font-size="15">space falling at g</text>
  <circle cx="330" cy="30" r="4" fill="currentColor"/>
  <text x="342" y="28" fill="currentColor" font-size="14">start: v = u</text>
  <text x="20" y="262" fill="currentColor" font-size="14">|u|² = 2GM_A/d_A + 2GM_B/d_B   •   direction: along g</text>
</svg>
<figcaption>Space starts with the flow's velocity and falls at g (orange). If the flow made sense, it would stay on the flow line (green). Along g it doesn't.</figcaption>
</figure>

**Where it goes wrong.** For space moving with the flow to fall at exactly g, the flow must have no curl, $\mathbf u =
\nabla\phi$: then it speeds up at $(\mathbf u\cdot\nabla)\mathbf u = \nabla(u^2/2) = \mathbf g$. A flow pointing along g
with this speed does have curl wherever the two bodies' pulls are not in line, so it speeds up at $\mathbf g -
\mathbf u\times\omega$ instead. The particles in the model follow the flow's own rule, so they fall wrongly
too.

## Tests

Two black holes of one solar mass, 1 AU apart (`tests/test_flow_consistency.py`, `studies/two_body_along_g.py`):

| Test | Expected | Result | |
| --- | --- | --- | --- |
| One body alone | GR | GR exactly | ✅ Pass |
| Clocks at rest | GR's rate, $1 - U/c^2$ | GR's rate (the speed is the potential's) | ✅ Pass |
| g on the line through the holes, and across its middle | Newton's | Newton's (there the flow has no curl) | ✅ Pass |
| g anywhere else, e.g. at (0.3, 0.4) AU | Newton's 0.031 m/s² | out by 0.053 m/s² (174%), pointing 60° off | ❌ Fail |
| Space let go at A with the flow's velocity, falling at g: does it arrive at B moving at the flow's velocity? | yes | the speed matches; the direction is 1–27° off | ❌ Fail |
| Space falling from 2 AU at the flow's velocity, against the flow's own lines | the same paths | 8 of 12 miss both holes and fly back out | ❌ Fail |

## In detail: the flow lines and falling space

Twelve pieces of space start 2 AU out, moving at the flow's velocity there. Each is followed two ways: carried along
the flow's lines (green, dashed), and falling at g as Newton's gravity says it must (orange). In a flow that made
sense they would be the same path, and for [the eikonal flow](eikonal.md) they are.

Here they part as soon as the two holes' pulls stop lining up. The flow lines run into the holes. Falling space,
following g, swings round the holes, and 8 of the 12 pieces fly back out: what falls from rest far away
at zero total energy can do that round two bodies, and Newton's paths do it. The flow along g points the wrong way to
follow them.

<iframe src="../../viewer/index.html?run=../runs/twoBodyAlongG/twoBodyAlongG.full.json" width="100%" height="560" loading="lazy" title="Flow lines along g against space falling at g"></iframe>

*Two holes of one solar mass 1 AU apart: flow lines of the flow along g (green, dashed) and space falling at g from the
same starts (orange), with the flow behind them.* [Open full
screen](../../../viewer/index.html?run=../runs/twoBodyAlongG/twoBodyAlongG.full.json){ target=_blank }
