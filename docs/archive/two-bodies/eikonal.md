# The eikonal flow

**The rule:** the flow's speed comes from the potentials added together, and it has no curl: it is the gradient of a
single function S,

$$
\mathbf u = -\nabla S, \qquad |\nabla S|^2 = \sum_i \frac{2GM_i}{d_i} .
$$

**Verdict: ❌ fails, but only beyond Newton.** It passes every Newtonian test and GR's clocks, and fails lunar laser
ranging by 27σ.

## Why it might make sense

It fixes both earlier problems at once. The speed is the potentials' sum, so clocks keep GR's rates. With no curl,
space moving with the flow speeds up at $(\mathbf u\cdot\nabla)\mathbf u = \nabla(u^2/2) = \mathbf g$, so it falls at
exactly Newton's g. The equation is the zero-energy Hamilton–Jacobi (eikonal) equation, and its flow lines are the
paths of things falling from rest far away. With one body that is just the flow straight in, so this is the one-body
flow's natural extension.

<figure markdown>
<svg viewBox="0 0 640 280" width="100%" style="max-width:640px" role="img" aria-label="The eikonal flow round two bodies, with its seam">
  <defs>
    <marker id="eg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1baf7a"/></marker>
  </defs>
  <circle cx="200" cy="150" r="26" fill="none" stroke="currentColor" stroke-width="2"/>
  <text x="200" y="155" text-anchor="middle" fill="currentColor" font-size="15">Sun</text>
  <circle cx="470" cy="150" r="12" fill="none" stroke="currentColor" stroke-width="2"/>
  <text x="470" y="185" text-anchor="middle" fill="currentColor" font-size="15">Earth</text>
  <path d="M405,10 C385,80 385,220 405,270" fill="none" stroke="#e8590c" stroke-width="2.5" stroke-dasharray="8 5"/>
  <text x="412" y="30" fill="#e8590c" font-size="15">seam</text>
  <circle cx="389" cy="150" r="4" fill="#e8590c"/>
  <text x="345" y="140" fill="#e8590c" font-size="12">g = 0</text>
  <g stroke="#1baf7a" stroke-width="2" fill="none" marker-end="url(#eg)">
    <path d="M30,150 L168,150"/>
    <path d="M60,40 C120,80 150,110 178,132"/>
    <path d="M60,260 C120,220 150,190 178,168"/>
    <path d="M220,15 C215,60 210,90 205,118"/>
    <path d="M220,285 C215,240 210,210 205,182"/>
    <path d="M360,40 C300,70 250,100 222,132"/>
    <path d="M360,260 C300,230 250,200 222,168"/>
    <path d="M610,150 L486,150"/>
    <path d="M590,60 C540,100 500,130 481,142"/>
    <path d="M590,240 C540,200 500,170 481,158"/>
    <path d="M440,40 C455,90 463,120 467,136"/>
    <path d="M440,260 C455,210 463,180 467,164"/>
  </g>
  <text x="20" y="25" fill="currentColor" font-size="14">u = −∇S, |∇S|² = Σ 2GM/d</text>
</svg>
<figcaption>The flow lines are the paths of things falling from rest far away. Each body's region is filled by its own; they meet at a seam through the point where g = 0.</figcaption>
</figure>

**How it works.** No flow like this can be smooth everywhere round two bodies, so it has a **seam**. Each body's region
is filled by paths running straight out of it; a point belongs to the body whose S there is smallest, and the seam
passes through the potential's saddle, where g = 0 between them. The flow jumps only across the seam, and only in the
direction across it, so the metric is continuous there. A particle crossing the seam keeps its energy and its momentum
along the seam, as the metric's own paths do. There are two versions: **`eikonal`**, tables of the paths integrated
out from each body, for any number of bodies; and **`eikonal-exact`**, for exactly two, where the paths separate in
elliptic coordinates (Euler's problem of two fixed centres) and each point's path comes from elliptic integrals. Its
acceleration matches g to about 2 × 10⁻⁹.

<iframe src="../../viewer/index.html?run=../runs/twoBodyFalls/twoBodyFalls.full.json" width="100%" height="560" loading="lazy" title="Falls towards two holes"></iframe>

*Thirty paths falling from 10 AU towards two 1-solar-mass holes 1 AU apart, with the eikonal flow behind them.*
[Open full screen](../../../viewer/index.html?run=../runs/twoBodyFalls/twoBodyFalls.full.json){ target=_blank }

**Where it goes wrong.** Round a body in another's field, the other's potential is in $|\mathbf u|^2$ too: round the
Earth space falls in at $\sqrt{2GM/r + 2c_0}$, where $c_0 = GM_{\text{Sun}}/\text{AU}$ – 43.6 km/s at the surface, not
11.2. In GR a uniform potential changes nothing that can be measured locally. In the flow it stretches distances
round the Earth by $c_0/c^2 \approx 10^{-8}$.

## Tests

The Sun and the Earth at rest (`studies/multi_body_rules.py`, `multi_body_clocks.py`, `moving_bodies.py`,
`multi_body_pn.py`), and two holes 1 AU apart (`tests/`):

| Test | Expected | Result | |
| --- | --- | --- | --- |
| One body alone | GR | GR exactly | ✅ Pass |
| Space falling at g stays with the flow | yes | yes, on every path that stays on one side of the seam | ✅ Pass |
| 33 two-body paths: falls, orbits round one hole and both, flybys, escapes, light | Newton's | Newton's | ✅ Pass |
| g at the Earth's surface and the Moon's distance | Newton's | to under 2 × 10⁻⁶ m/s² | ✅ Pass |
| Balls let go 100 km up | straight down in 145 s | straight down in 145 s | ✅ Pass |
| Clocks on the equator and in GPS orbit, over a day | GR's rates | to 2 × 10⁻¹⁶ (rounding) | ✅ Pass |
| Light pulses from a clock at noon to one at dusk | GR: 4.2 × 10⁻¹³ | 4.2 × 10⁻¹³ | ✅ Pass |
| A moving Earth, its flow only taken along (the space round it not moving) | Newton's g | out by 26–52 m/s²: each body must carry its flow | ❌ Fail |
| Einstein's constraint round the Earth | 0 (empty space) | $4c_0/r^2$ | ❌ Fail |
| **Lunar laser ranging**: the range's term at the Moon's synodic period | (2.8 ± 4.1) mm | 111 mm, 27σ | ❌ Fail |
| Light past Jupiter: both bodies less each alone | 0; VLBI positions to under 10 µas | 300–400 µas from 1 to 100 Jupiter radii | ❌ Very likely fails |

## In detail: lunar laser ranging

Lunar laser ranging times laser pulses from the Earth to reflectors on the Moon, to millimetres. In GR the Sun changes
the Earth–Moon range only through its tide, below a micrometre on top of the Newtonian orbit. Any term at the Moon's
synodic period (as the Moon goes from the Sun's side of the Earth to the far side) is tightly fitted: (2.8 ± 4.1) mm,
the strong equivalence principle's test (Williams, Turyshev & Boggs 2004).

In the model, radar runs from the Earth's surface to a mirror at the Moon's distance and back, with the Sun 1 AU away,
at each angle D of the Moon from the Sun, against the same with the Earth alone. Light run in the model agrees with the
straight-line round trip to 10⁻¹⁴ s. The range comes out 3.4–3.7 m longer. Most of that is a constant (it would go
into the Earth's measured mass), but where the Moon is in the Sun's region of the flow (D within about 60° of the
Sun), the flow points at the Sun instead of the Earth, and the range is shorter. That puts an 11 cm term at the
synodic period into the range, 27 times LLR's uncertainty on it. The range also swings by ±6 cm over the year, as the
Earth's distance from the Sun changes.

<iframe src="../../viewer/index.html?run=../runs/multiBodyPN/multiBody_lunar.full.json" width="100%" height="440" loading="lazy" title="The extra lunar range by the Moon's angle from the Sun"></iframe>

*The extra lunar range (m) the Sun's potential makes in the eikonal flow, by the Moon's angle from the Sun (degrees).*
[Open full screen](../../../viewer/index.html?run=../runs/multiBodyPN/multiBody_lunar.full.json){ target=_blank }

The effect goes as $c_0$, so as $G\sqrt{M_{\text{Sun}}M_{\text{Earth}}}$ in all, because the flow is the square root
of the potential. No post-Newtonian (PPN) theory has a term like that, so no choice of PPN parameters describes it.

**What fixes it.** The stretch is in the flow; the fix is in space. With space stretched across the flow by
Einstein's constraint, $\gamma = \delta + (2U\delta - \mathbf u\mathbf u)/c^2$, the eikonal flow passes lunar
ranging's synodic term and the Jupiter bending with the bodies at rest ([Lapse and curved
space](../lapse-curved-space.md#the-clocks-left-alone-space-curved-across-the-flow)).
