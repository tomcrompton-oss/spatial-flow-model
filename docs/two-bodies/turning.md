# Each body carrying its flow

**The rule:** the eikonal flow again, but turning with the bodies as they go round each other, so that each body's
space moves with it. In the frame turning with them at Ω, the flow relative to that frame,
$\mathbf w = \mathbf u - \mathbf\Omega\times\mathbf x$, is steady and has

$$
|\mathbf w|^2 = 2\left(U + \tfrac12\Omega^2\rho^2 + J\right)
$$

with one constant J, chosen so that the Earth's flow is its own.

**Verdict: ❌ fails.** It fixes the Earth and breaks the Sun: light past the Sun bends 9.6 mas less, 1000 times what
Cassini allows.

## Why it might make sense

The [eikonal flow](eikonal.md) fails because the Sun's potential gets into the Earth's flow. Bodies move, and a moving
body must carry its flow with it anyway, or g goes wrong by tens of m/s². So let the Earth carry its own flow, with the
Sun's potential taken out of it, as it would be for the Earth alone. The two bodies go round their centre of mass, and
in the frame turning with them the flow is steady, so it is still an eikonal: Newton's g holds, and the flow lines are
the paths of the restricted three-body problem, all with Jacobi constant J.

<figure markdown>
<svg viewBox="0 0 640 300" width="100%" style="max-width:640px" role="img" aria-label="The flow turning with the Sun and the Earth">
  <defs>
    <marker id="tg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1baf7a"/></marker>
    <marker id="to" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#e8590c"/></marker>
    <marker id="tc" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
  </defs>
  <circle cx="230" cy="150" r="130" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="3 5" opacity="0.6"/>
  <circle cx="230" cy="150" r="87" fill="none" stroke="#e8590c" stroke-width="1.5" stroke-dasharray="6 4"/>
  <text x="255" y="58" fill="#e8590c" font-size="13">2/3 AU: the Sun's paths turn back</text>
  <circle cx="230" cy="150" r="24" fill="none" stroke="currentColor" stroke-width="2"/>
  <text x="230" y="155" text-anchor="middle" fill="currentColor" font-size="14">Sun</text>
  <g stroke="#e8590c" stroke-width="2" fill="none">
    <path d="M254,150 L310,150 C318,150 318,156 312,158"/>
    <path d="M230,126 L230,70 C230,62 224,62 222,68"/>
    <path d="M206,150 L150,150 C142,150 142,144 148,142"/>
    <path d="M230,174 L230,230 C230,238 236,238 238,232"/>
  </g>
  <circle cx="360" cy="150" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
  <text x="360" y="182" text-anchor="middle" fill="currentColor" font-size="14">Earth</text>
  <g stroke="#1baf7a" stroke-width="2" fill="none" marker-end="url(#tg)">
    <path d="M410,150 L372,150"/>
    <path d="M360,105 L360,138"/>
    <path d="M360,195 C360,180 360,170 360,162"/>
    <path d="M400,115 L368,142"/>
  </g>
  <text x="420" y="120" fill="#1baf7a" font-size="13">the Earth's own flow</text>
  <path d="M325,268 A130,130 0 0 0 357,212" fill="none" stroke="currentColor" stroke-width="2" marker-end="url(#tc)"/>
  <text x="350" y="265" fill="currentColor" font-size="15">Ω</text>
  <text x="440" y="235" fill="currentColor" font-size="14">one J for the whole flow:</text>
  <text x="440" y="255" fill="currentColor" font-size="14">right for the Earth,</text>
  <text x="440" y="275" fill="currentColor" font-size="14">wrong for the Sun</text>
</svg>
<figcaption>In the frame turning with the bodies, the Earth carries its own flow. The Jacobi constant that makes that so is the Sun's paths' energy too, and with it they can't get past 2/3 AU.</figcaption>
</figure>

**Where it goes wrong.** Where two regions of the flow meet at a seam, the metric is continuous only if both have the
same J, so the whole flow has one. The Earth's own flow needs J = −1.33 × 10⁹ m²/s² (minus the Sun's and the turning
frame's potential at the Earth). But the Sun's paths leave it with no angular momentum, so their energy is J, not 0: the
stretch that the eikonal flow put round the Earth is now round the Sun, as a squeeze. No single J suits both bodies.

## Tests

The Sun at the centre, the Earth on its orbit (`engine/turning.py`, `studies/turning_eikonal.py`, `curl_flows.py`):

| Test | Expected | Result | |
| --- | --- | --- | --- |
| One body alone | GR | GR exactly | ✅ Pass |
| g round the moving Earth | Newton's | Newton's, to the tables' 2 × 10⁻⁵ of g | ✅ Pass |
| Einstein's constraint round the Earth, over the eikonal flow's $4c_0/r^2$ | 0 | 10⁻⁵ (the Sun's tide) | ✅ Pass |
| Lunar laser ranging: the synodic term | (2.8 ± 4.1) mm | 2 × 10⁻⁸ m | ✅ Pass |
| **Light past the Sun at 2 solar radii** | GR's bending; Cassini: to 0.01 mas | 9.6 mas less (1.1%) | ❌ Fail |
| Einstein's constraint round the Sun | 0 | $4J/r^2$ | ❌ Fail |
| The flow in three dimensions, along the orbit's axis | a flow everywhere | none beyond 2/3 AU from the Sun ($|\mathbf w|^2 < 0$) | ❌ Fail |
| J = 0 instead, which suits the Sun | the Earth's flow its own | the stretch round the Earth, half as big again as the eikonal flow's | ❌ Fail |
| Letting the flow curl, so J can differ from line to line | empty space outside matter | needs matter streaming at 10²³–10²⁶ × the solar wind's flux, and pushes the Moon at 0.024 m/s², 9 × the Earth's pull | ❌ Fail |

## In detail: light past the Sun

The Cassini spacecraft measured the delay of radio signals passing the Sun, and fixed GR's light-bending parameter γ
to 2.3 × 10⁻⁵: at 2 solar radii, the bending is GR's 1.75″ to within about 0.01 mas.

In the turning flow the Sun's space falls in with energy J rather than 0, $|\mathbf u|^2 = 2GM/r + 2J$, with J below
zero. That is a squeeze of space round the Sun, the opposite of the eikonal flow's stretch round the Earth. Light run
in the model past the Sun loses a cone's worth of bending, $\pi J/c^2 = 9.6$ mas, at every impact parameter, 1.1% of
the total at 2 solar radii and 1000 times Cassini's limit. Einstein's constraint, which is 0 for empty space, is $4J/r^2$
there.

The same J also limits how far the Sun's space reaches: nothing let go from the Sun with energy J gets beyond
$GM/|J| = 2/3$ AU. The viewer shows the flow's paths, run out from each body as the tables are built: the Sun's turn
back at 2/3 AU, and the Earth's curl round past its Hill sphere. Beyond about 1.1 AU the only paths with this J are
ones swirling in from far away.

<iframe src="../../viewer/index.html?run=../runs/turningEikonal/turning_paths.full.json" width="100%" height="560" loading="lazy" title="Space paths in the frame turning with the Earth"></iframe>

*Space paths out of the Sun (turning back at 2/3 AU) and out of the Earth (curling round past its Hill sphere), in
the frame turning with the Earth.* [Open full
screen](../../viewer/index.html?run=../runs/turningEikonal/turning_paths.full.json){ target=_blank }
