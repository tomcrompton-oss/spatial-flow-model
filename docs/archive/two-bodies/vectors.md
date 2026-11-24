# Vector addition

**The rule:** each body has its own flow, straight in at $\sqrt{2GM_i/d_i}$, and the flow of space is their sum,

$$
\mathbf u = \sum_i \mathbf u_i .
$$

**Verdict: ❌ fails.** It gets Newton's gravity wrong by several times g at the Earth's surface.

## Why it might make sense

It is how currents combine. Two rivers flowing into the same lake add as velocities, and one body's flow is already
exact GR, so adding them looks like the most direct way to put two bodies together. It is the rule Part 3 of the
original write-up uses: between the Earth and the Moon the two flows point opposite ways, so somewhere they cancel and
space stands still.

<figure markdown>
<svg viewBox="0 0 640 260" width="100%" style="max-width:640px" role="img" aria-label="Vector addition of two flows at a point">
  <defs>
    <marker id="vg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1baf7a"/></marker>
    <marker id="vo" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#e8590c"/></marker>
  </defs>
  <circle cx="90" cy="200" r="34" fill="none" stroke="currentColor" stroke-width="2"/>
  <text x="90" y="205" text-anchor="middle" fill="currentColor" font-size="15">Sun</text>
  <circle cx="540" cy="200" r="14" fill="none" stroke="currentColor" stroke-width="2"/>
  <text x="540" y="238" text-anchor="middle" fill="currentColor" font-size="15">Earth</text>
  <circle cx="380" cy="80" r="4" fill="currentColor"/>
  <text x="392" y="70" fill="currentColor" font-size="15">P</text>
  <line x1="380" y1="80" x2="250" y2="130" stroke="#1baf7a" stroke-width="2.5" marker-end="url(#vg)"/>
  <text x="270" y="105" fill="#1baf7a" font-size="15">u<tspan baseline-shift="sub" font-size="11">Sun</tspan></text>
  <line x1="380" y1="80" x2="450" y2="135" stroke="#1baf7a" stroke-width="2.5" marker-end="url(#vg)"/>
  <text x="430" y="100" fill="#1baf7a" font-size="15">u<tspan baseline-shift="sub" font-size="11">Earth</tspan></text>
  <line x1="250" y1="130" x2="320" y2="185" stroke="#1baf7a" stroke-width="1.5" stroke-dasharray="5 4"/>
  <line x1="450" y1="135" x2="320" y2="185" stroke="#1baf7a" stroke-width="1.5" stroke-dasharray="5 4"/>
  <line x1="380" y1="80" x2="320" y2="185" stroke="#e8590c" stroke-width="3" marker-end="url(#vo)"/>
  <text x="250" y="215" fill="#e8590c" font-size="15">u = u<tspan baseline-shift="sub" font-size="11">Sun</tspan> + u<tspan baseline-shift="sub" font-size="11">Earth</tspan></text>
  <text x="20" y="30" fill="currentColor" font-size="14">|u|² = u²<tspan baseline-shift="sub" font-size="10">Sun</tspan> + u²<tspan baseline-shift="sub" font-size="10">Earth</tspan> + 2 u<tspan baseline-shift="sub" font-size="10">Sun</tspan>·u<tspan baseline-shift="sub" font-size="10">Earth</tspan>   ← the last term is new</text>
</svg>
<figcaption>At each point the two bodies' flows are added head to tail. The speed squared picks up a cross term.</figcaption>
</figure>

**Where it goes wrong.** Space moving at $\mathbf u$ speeds up at $(\mathbf u\cdot\nabla)\mathbf u = \nabla(u^2/2)$
when the flow has no curl, so the rule for $|\mathbf u|^2$ *is* the law of gravity. With one body $u^2/2 = GM/r$ and
that is Newton. With two added as vectors, $u^2/2$ has the two potentials *and* the cross term
$\mathbf u_{\text{Sun}}\cdot\mathbf u_{\text{Earth}}$, which pulls as well. At the Earth the Sun's flow is 42 km/s and
the Earth's is 11 km/s at its surface, and their product changes by about $u_{\text{Sun}}u_{\text{Earth}}/2R \approx$
40 m/s² across the Earth.

## Tests

Run in the model with the Sun 1 AU from the Earth (`studies/multi_body_rules.py`, `multi_body_clocks.py`,
`moving_bodies.py`):

| Test | Expected | Result | |
| --- | --- | --- | --- |
| One body alone | GR | GR exactly | ✅ Pass |
| g at the Earth's surface | Newton's 9.8 m/s² | out by 37–74 m/s² | ❌ Fail |
| g at the Moon's distance | the Earth's 0.0027 m/s² plus the Sun's tide | out by 0.08–0.16 m/s² | ❌ Fail |
| Balls let go 100 km up | fall straight down in 145 s | the ball facing the Sun is pushed 300 km *up*; others veer 800 km sideways | ❌ Fail |
| A clock on the equator, over a day | GR's rate | swings ±5.2 × 10⁻⁹: ±69 µs a day | ❌ Fail |
| A GPS clock, over a day | GR's rate | swings ±2.6 × 10⁻⁹: ±20 µs a day, 5.9 km of range | ❌ Fail |
| Light pulses from a clock at noon to one at dusk | GR: 4.2 × 10⁻¹³ fewer seconds at dusk | 5.2 × 10⁻⁹ | ❌ Fail |
| The Earth moving, carrying its flow | Newton's g | out by 0.005–0.01 m/s², 10⁴ × the Sun's tide | ❌ Fail |
| Where space stands still between the Earth and the Moon | Part 3's P, where g = 0, 38,000 km from the Moon | 4,700 km from the Moon | ❌ Fail |

## In detail: balls dropped round the Earth

Eight balls are let go from rest 100 km above the Earth, evenly round it, with the Sun 1 AU to the left, and run for
150 s in the model. Under Newton (and GR) each falls straight down, reaching the ground in 145 s; the Sun's pull on a
ball and on the Earth is the same to a few parts in 10⁸.

With the flows added as vectors (solid lines), the ball on the side facing the Sun goes *up*, 300 km in 150 s: there
the cross term's push outwards beats the Earth's own pull. The balls at the sides are thrown 800 km sideways, along the
cross term's gradient. With the flows added by their squares (dashed), the rule of the next pages, every ball falls
straight down, as Newton's do.

<iframe src="../../../viewer/index.html?run=../runs/multiBodyRules/multiBody_drops.full.json" width="100%" height="560" loading="lazy" title="Balls dropped round the Earth, the Sun to the left"></iframe>

*Balls let go 100 km above the Earth, the Sun 1 AU to the left: flows added as vectors (solid), by their squares
(dashed).* [Open full screen](../../../viewer/index.html?run=../runs/multiBodyRules/multiBody_drops.full.json){ target=_blank }

The same cross term shows in clocks. A clock ticks at $\sqrt{1-|\mathbf v-\mathbf u|^2/c^2}$, so the cross term
$\mathbf u_{\text{Sun}}\cdot\mathbf u_{\text{Earth}}/c^2$ makes clocks run fast on the side facing the Sun and slow on
the far side. As the Earth turns, a clock on the equator swings by ±69 µs a day against GR, where GPS keeps time to
nanoseconds:

<iframe src="../../../viewer/index.html?run=../runs/multiBodyClocks/multiBody_clocks.full.json" width="100%" height="480" loading="lazy" title="Clock rates against GR over a day"></iframe>

*Each clock's rate against GR's over a day, in parts in 10⁹: flows added as vectors and by their squares.*
[Open full screen](../../../viewer/index.html?run=../runs/multiBodyClocks/multiBody_clocks.full.json){ target=_blank }
