# Each body separately

**The rule:** no single flow at all. Each body keeps its own one-body flow, straight in at $\sqrt{2GM/d}$ in its own
rest frame. A step works out what each body's flow alone would do to a particle, using the one-body model's own step,
and applies the changes one after the other: the Sun's, then the Earth's. The particle moves once, at its velocity.

**Verdict: ❌ fails, with two bodies of comparable mass.** It passes every test with one body much heavier than the
other – Newton's g, clocks, light past Jupiter, causality, a moving system – and with free-fall frames comes within
twice the lunar test's floor. But in a binary of comparable masses its orbit turns 17% too slowly at equal masses, and
the pair's centre of mass accelerates by itself. Binary pulsars rule out both: the bodies' fields need to act on each
other, and in this model they don't.

## Why it might make sense

One body's flow is GR exactly, and to first order in G, GR's effects of several bodies simply add. So instead of
looking for one flow that serves every body – which is where each earlier approach failed – use each body's exact
one-body solution, and add their effects. Numerically it is operator splitting: the step for body A, then the step for
body B.

<figure markdown>
<svg viewBox="0 0 660 250" width="100%" style="max-width:660px" role="img" aria-label="Each body's flow taken alone, its change to the particle applied in turn">
  <defs>
    <marker id="sg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1baf7a"/></marker>
    <marker id="so" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#e8590c"/></marker>
    <marker id="sc" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
  </defs>
  <text x="105" y="22" text-anchor="middle" fill="currentColor" font-size="14">the Sun's flow alone</text>
  <circle cx="60" cy="140" r="22" fill="none" stroke="currentColor" stroke-width="2"/>
  <g stroke="#1baf7a" stroke-width="1.8" fill="none" marker-end="url(#sg)">
    <path d="M190,140 L88,140"/><path d="M170,60 L80,125"/><path d="M170,220 L80,155"/>
  </g>
  <circle cx="150" cy="105" r="4" fill="currentColor"/>
  <line x1="150" y1="105" x2="120" y2="110" stroke="#e8590c" stroke-width="2.5" marker-end="url(#so)"/>
  <text x="118" y="95" fill="#e8590c" font-size="13">Δv₁</text>
  <text x="225" y="145" fill="currentColor" font-size="22">+</text>
  <text x="345" y="22" text-anchor="middle" fill="currentColor" font-size="14">the Earth's flow alone</text>
  <circle cx="400" cy="140" r="12" fill="none" stroke="currentColor" stroke-width="2"/>
  <g stroke="#1baf7a" stroke-width="1.8" fill="none" marker-end="url(#sg)">
    <path d="M270,140 L384,140"/><path d="M300,60 L390,128"/><path d="M300,220 L390,152"/>
  </g>
  <circle cx="300" cy="105" r="4" fill="currentColor"/>
  <line x1="300" y1="105" x2="322" y2="118" stroke="#e8590c" stroke-width="2.5" marker-end="url(#so)"/>
  <text x="318" y="98" fill="#e8590c" font-size="13">Δv₂</text>
  <text x="450" y="145" fill="currentColor" font-size="22">→</text>
  <text x="565" y="22" text-anchor="middle" fill="currentColor" font-size="14">the particle</text>
  <circle cx="520" cy="105" r="4" fill="currentColor"/>
  <line x1="520" y1="105" x2="600" y2="80" stroke="currentColor" stroke-width="2" marker-end="url(#sc)"/>
  <text x="575" y="70" fill="currentColor" font-size="13">v</text>
  <line x1="600" y1="80" x2="570" y2="85" stroke="#e8590c" stroke-width="2.5" marker-end="url(#so)"/>
  <line x1="570" y1="85" x2="592" y2="98" stroke="#e8590c" stroke-width="2.5" marker-end="url(#so)"/>
  <text x="490" y="160" fill="currentColor" font-size="13">v + Δv₁ + Δv₂,</text>
  <text x="490" y="178" fill="currentColor" font-size="13">then it moves once</text>
  <text x="20" y="242" fill="currentColor" font-size="13">each change is the one-body model's step, worked out in that body's own rest frame</text>
</svg>
<figcaption>Each body's flow is taken alone, as if the other weren't there. What it does to the particle in a step is added to the particle's velocity, one body at a time.</figcaption>
</figure>

**What else it needs.** With no single flow, clocks and light need rules of their own, and moving bodies need a rule
for "the body's own frame". The ones that pass, after trying others:

- **Clocks:** each body changes a clock's rate by what it would change it by alone.
- **Light's speed:** each body changes light's slowness (1/speed) by what it would alone, Schwarzschild's change in that
  body's static time, converted to the model's time. (The first rule tried, from a combined interval, left a cross
  term between the bodies.)
- **A moving body's frame:** a Lorentz boost of the particle's place, time and velocity, not a Galilean shift. (With a
  Galilean shift, orbits round a moving body don't contract while light does, and radar to the Moon changes with
  direction by $LV^2/2c^2$.)
- **...relative to the other bodies' space:** the body's free-fall frame in the space the other bodies' flows carry
  past it – shifted to their flow at the body's centre, then Lorentz-boosted by the body's velocity through it. (Boosted
  from the lab instead, the lunar range is out by 2.2 m; from the other bodies' static frame, which is held up against
  their pull rather than falling, by 240 m.) This is the one place where the bodies' flows meet: each body's frame
  depends on the others' flow at its centre.

## Tests

The Sun and the Earth, or the Sun and Jupiter (`engine/split.py`, `studies/split_bodies.py`, `split_checks.py`,
`lunar_orbit.py`). The four versions: the first rules tried (Galilean frames, light from a combined interval), then
light's rule fixed, then Lorentz frames, then free-fall frames.

| Test | Expected | Galilean, interval light | Galilean, static light | Lorentz | Free-fall |
| --- | --- | --- | --- | --- | --- |
| One body alone | the one-body flow model (GR) | ✅ to rounding | ✅ | ✅ | ✅ |
| g at the Earth's surface and the Moon's distance; a moving Earth | Newton's | ✅ to 10⁻⁷ m/s² | ✅ | ✅ | ✅ |
| A term in the steps that would move the Moon against the Earth, the Earth held at rest | none | ✅ none, to 7 × 10⁻¹³ m/s² | ✅ | ✅ | – 10⁻¹⁰ m/s²: a held Earth isn't falling, so the next-but-one row is the test |
| Clocks on the equator and in GPS orbit; light pulses noon to dusk | GR's | ✅ to 2 × 10⁻¹⁶; 1.6 × 10⁻¹⁵ | ✅ | ✅ | ✅ |
| Light past Jupiter: both bodies less each alone | 0 (the eikonal flow: 408 µas) | ✅ 0.26 µas at 1 R_J | ✅ | ✅ | ✅ |
| Lunar range to a mirror held still: both bodies less each alone | 0 | ❌ 0.45 m | ✅ 0 | ✅ 6 × 10⁻⁷ m | ✅ 0 |
| Particles at γ up to 10⁶: can matter outrun light? | never | ❌ by 3.6 × 10⁻⁹ c | ✅ never | ✅ never | ✅ never |
| The whole system moving together: radar to the Moon | no change | ❌ 1.9 m at 29.8 km/s, 290 m at 370 km/s | – (light's rule needs bodies at rest) | ✅ 0.0000 m | ✅ 0.0000 m |
| **The Moon's own orbit, the Earth going round the Sun: lunar laser ranging** | GR's range, to millimetres | – | – | ❌ 2.2 m rms; 2.7 m at half the synodic period | ❓ 0.15 m rms, against the test's 8 cm with the Sun; 8 cm at half the synodic period, 3 cm at it |
| **A binary of comparable masses: the periastron advance** | GR's, for any mass ratio; the double pulsar to about 10⁻⁴ | – | – | ❌ 25% too much at equal masses | ❌ 17% too little at equal masses |
| A binary of comparable masses: the centre of mass | stays put (momentum is conserved) | – | – | ❌ accelerates | ❌ accelerates, 0.17 m/s² at a mass ratio of 0.1 |
| The binary's period (orbital decay) | shrinks only by gravitational waves: GR −2.5 × 10⁻¹⁰ s/s; Hulse–Taylor matches GR to 0.2% | – | – | ❌ −7.8 × 10⁻⁴ s/s | ❌ −1.4 × 10⁻³ s/s |
| Light past a moving Jupiter: GR's (1 − v·k/c) in the bending | VLBI (2003), to about 20% | – | – | ✅ to 3 × 10⁻⁷ | ✅ (one body: the same) |
| The Nordtvedt effect: a bound pair falling towards the Sun | falls as a single body; lunar laser ranging η < 10⁻⁴ | – | – | ❌ η = 1.00 | – (three bodies: see below) |
| De Sitter precession of the Moon's orbit, over a year | GR's 19.2 mas a year; lunar laser ranging to 0.3% | – | – | – | ❌ the Moon's orbit departs from GR's by 3 m rms over 90 days in a way no turning takes out; k (0 = GR, 1 = none) +0.8 or −3.0 by start |

## In detail: lunar laser ranging with the Moon's own orbit

Every other test holds the geometry still: a mirror placed at the Moon's distance, bodies at rest or moving together.
The real test lets the Moon move. The Sun is at rest, the Earth goes round it on its orbit, and the Moon goes round
the Earth, run in the model for two synodic months (59 days), with every pull and relativistic effect the model has.
Every two hours, light goes from a station on the Earth's surface to the Moon and back, and the round trip, timed by
the station's clock, gives the range.

GR's prediction is run the same way, from the Einstein–Infeld–Hoffmann equations (GR's equations of motion to first
post-Newtonian order) and Shapiro's delay for light. The two run in different coordinates, so GR's Moon starts where a
fit puts it – its starting place and velocity, and a constant in the range – to match the model's range as closely as
possible. That is what lunar laser ranging does with the real Moon. Whatever is left is what the model predicts and GR
doesn't.

Two checks show the test can see centimetres. With the Earth alone (moving at 29.8 km/s, no Sun) the model is GR
exactly, and the fit leaves 5 cm rms, with every term at the Moon's synodic angle under 5 mm. The model's own step error
goes as the step squared (4 m at 20 s steps), so its ranges are run at 10 s and 20 s steps and extrapolated to zero.

With the Sun and Lorentz frames, the fit leaves 2.2 m rms, 4.1 m at most, almost all of it at twice the Moon's synodic
angle D. With free-fall frames it leaves 0.15 m:

| Residual after the fit | the Earth alone (the floor) | the Sun, Lorentz frames | the Sun, free-fall frames | LLR's limit |
| --- | --- | --- | --- | --- |
| rms | 0.05 m | 2.16 m | 0.15 m | millimetres |
| at the synodic angle D | 0.004 m | 0.27 m | 0.03 m | (2.8 ± 4.1) mm |
| at 2D | 0.006 m | 2.64 m | 0.09 m | millimetres |

<iframe src="../../viewer/index.html?run=../runs/lunarOrbit/lunarOrbit.full.json" width="100%" height="460" loading="lazy" title="Lunar range, the split model less GR"></iframe>

*The lunar range in the split model less GR's, after the fit (m), over two synodic months (days): Lorentz frames,
free-fall frames, and the Earth alone (the test's floor).* [Open full
screen](../../viewer/index.html?run=../runs/lunarOrbit/lunarOrbit.full.json){ target=_blank }

**Why the Lorentz frames fail.** The Earth moves at V = 29.8 km/s through the Sun's flow, which is 42 km/s at the
Earth. With Lorentz frames the split model works out the Earth's effects in a frame boosted from the lab, and nothing
ties it to the Sun's space round the Earth. Two terms follow, both from light crossing the Sun's space while the
Moon's orbit ignores it: from simultaneity, $-(\mathbf n\cdot\mathbf V)(\mathbf n\cdot\mathbf u_{\text{Sun}})L/c^2$
(2.6 m at 2D), and from the Sun's space making light's speed depend on direction, $(\mathbf n\cdot
\mathbf u_{\text{Sun}})^2 L/2c^2$ (1.9 m at 2D), with L the Earth–Moon distance and n the direction to the Moon. Put
through the same fit, the two account for the residual: they leave 0.62 m of the 2.18 m, and 0.21 m of 1.24 m with the
Earth at 2 AU. The checks agree. Fitting the Sun's mass as well doesn't absorb it; with the Earth going round the other
way, or at 2 AU, it changes as those terms do.

**The free-fall frame.** In GR the Earth–Moon system falls freely in the Sun's field, and its local physics is the
same as if the Sun weren't there, apart from the tide. So the Earth's frame should be its free-fall frame in the Sun's
space: shifted to the Sun's flow at the Earth, then boosted by the Earth's velocity through it, $\mathbf V - \mathbf
u_{\text{Sun}}$. That takes out almost all of the residual, 0.15 m left of 2.16 m, and keeps every other test passed.

**What is left.** Three candidates were tested:

| Candidate | Test | Result |
| --- | --- | --- |
| The test's own step error | the frames are taken at each step's middle, and the run repeated at half the step | 0.149 m and 0.150 m: converged. (An earlier version took the frames at each step's start, which gave 0.49 m) |
| The Sun's tide across the Earth–Moon system, which the frame leaves out | the two frame terms worked out with the Sun's flow's change along the path, put through the fit | under 6 mm |
| GR's de Sitter precession of a frame falling round the Sun (19 mas a year) | a turning of GR's Moon's frame added to the fit | takes out 2% |

None of them accounts for the 0.15 m. Two more checks are about the test itself:

| Check | Result |
| --- | --- |
| The Earth's mass fitted as well (lunar laser ranging fits it) | moves by 3 × 10⁻⁸; the residual stays 0.15 m |
| **The test's floor with the Sun**: the Earth given a mass of 1 kg, so the split model is exactly GR, and the Moon on an epicycle round the Earth's place | **0.077 m rms**, 5 cm at the synodic angle |

The test's floor with the Earth alone was 5 cm; with the Sun it is 8 cm, from the GR side's Sun terms or the way the
two codes are matched, even where the model is exactly GR. Against that, free-fall frames leave twice the floor. Their
term at the synodic period (3 cm) is within it, and their term at half the synodic period (8 cm) is the only part
clearly above it. Lorentz frames, at 2.2 m, fail by far more than the test's floor.

So this test can't settle the free-fall version. Doing that would take a GR reference good to millimetres with the
Sun, as lunar laser ranging's own ephemerides are.

The free-fall frame also gives up part of the idea: each body's frame now depends on the other bodies' flow at its
centre, so the flows are not wholly separate any more.

## Comparable masses: a binary

The tests above all have one body much heavier than the other. There the split model is close to the one-body flow,
and the one-body flow is GR. The thing it leaves out by design is the bodies' fields acting on each other: in GR's
equations of motion for two bodies (Einstein, Infeld and Hoffmann's) there are terms in $m_1 m_2$, largest when the
masses are equal. Binary pulsars are such systems, and they measure the orbit's turning with the masses known from
other effects.

In `studies/binary_pulsar.py` each body moves in the other's flow by the model's own step, 2 solar masses in all,
1 × 10⁸ m apart, eccentricity 0.3. GR's periastron advance at first post-Newtonian order is exact for any mass ratio:
3(GMn)^(2/3)/(c²(1−e²)) per 2π, with M the total mass and n the orbit's frequency.

| Mass ratio m₂/m₁ | η = m₁m₂/M² | Free-fall frames: model / GR | Lorentz frames: model / GR | Centre of mass (free-fall) |
| --- | --- | --- | --- | --- |
| 1 | 0.25 | 0.834 | 1.250 | still (by symmetry) |
| 0.1 | 0.083 | 0.946 | 1.083 | accelerates at 0.17 m/s² |
| 0.01 | 0.0098 | 0.994 | 1.011 | accelerates at 0.07 m/s² |

With one body light the model is GR, as it must be. The gap grows with η: by −0.66 η with free-fall frames and +1.0 η
with Lorentz frames, 17% and 25% at equal masses. The double pulsar, whose masses are nearly equal, checks GR's
advance to about 10⁻⁴.

The centre of mass shows the same thing another way. Each body's step uses only the other's flow, so the
relativistic parts of the two pulls don't balance, and the pair accelerates by itself – 0.17 m/s² here, about 6 × 10⁻⁶
of the pull between them, where the first-order relativistic forces are about 10⁻⁵ of it. It goes as 1/c²: with c
a thousand times larger it falls to the scheme's own 0.002 m/s². In GR momentum is conserved and the centre of mass
only swings, by metres here. A binary pulsar that accelerated like this would change its observed period, which the
pulsars rule out.

## Four more tests

`studies/split_more.py`:

- **Light past a moving Jupiter ✅.** GR's bending past a body moving at v along the light's way carries a factor
  $1 - \mathbf v\cdot\mathbf k/c$, the velocity-dependent part VLBI measured past Jupiter. Each body's Lorentz frame
  gives it: to 3 × 10⁻⁷ at Jupiter's 13 km/s and at 0.001c, and to the expected second-order 5 × 10⁻⁵ at 0.01c.
- **Orbital decay ❌.** GR's binary loses energy only to gravitational waves, and its period shrinks by
  2.5 × 10⁻¹⁰ s/s here. The split model's equal-mass binary shrinks by 1.4 × 10⁻³ s/s with free-fall frames (7.8 × 10⁻⁴
  with Lorentz frames) – the same at both step sizes, and going away with c a thousand times larger. Like momentum,
  energy is not conserved: the relativistic parts of the two bodies' pulls don't match.
- **The Nordtvedt effect ❌.** A pair of bodies orbiting each other, let fall towards the Sun beside a single body of the
  same mass, falls slower by exactly g E/Mc², E the pair's binding energy: Nordtvedt's η = 1.00, where lunar laser
  ranging has η below 10⁻⁴. In GR the binding energy weighs through the bodies' fields acting on each other, which
  the split model leaves out. (With free-fall frames this test has three bodies, and the frame then adds the other
  bodies' moving spaces together, counting their orbital motion as flow: the pair falls 2.3% too fast, a fault of the
  frame rule, not a measurement.)
- **De Sitter precession ❌ (not as de Sitter).** The effect is 19.2 mas a year in a perigee the Sun's tide turns by
  1.1 rad a year, and a start 1 part in 10⁸ different (the size of the model's and GR's coordinate differences) moves
  the perigee's rate by 15 to 34 mas a year, so perigee rates from one start can't show it, nor with GR's start fitted
  (−12 to −329 mas a year, by start and span). `studies/de_sitter.py` fits GR to the model's track with its start and a
  turning of k times the de Sitter rate free (k = 0: the model has GR's precession; k = 1: none). Getting the model's
  side clean took two fixes to its step (`engine/split.py`): each body's change is now worked as a change (of place, of
  flow and of velocity, carried back from the body's frame by `backChange`) rather than as a difference of large
  numbers. Before, the Moon's whole 30 km/s was taken into each body's frame and back at every step, which lost a fixed
  part in 10¹⁶ each time; that built up step on step, so the error grew as the step shrank. Now, with c × 1000, the
  model matches Newton to 1–3 cm over 90 days (k = 0.004), and the calibration (GR against turned GR) gives k = 0.98.

  | 90 days, steps 5 and 2.5 s, extrapolated | k | fit rms |
  | --- | --- | --- |
  | eccentric start (e ≈ 0.12) | +0.78 | 3.2 m |
  | lunar ranging start | −2.97 | 2.7 m |
  | c × 1000 control (either start) | 0.00 | 1–3 cm |

  The two starts disagree and the fit leaves 3 m, against centimetres for the control: the model's Moon departs
  from GR's by metres over 90 days in a way a turning frame can't take out, and k only picks up some of that. So the
  model doesn't just lack (or have) de Sitter precession: its Moon orbit differs from GR's at a level lunar laser
  ranging (centimetres) would see. The fit itself isn't perfect (it leaves 0.15 m on the eccentric
  calibration and 0.57 m on the lunar one, with k 0.81 there), and test 1 saw only 0.15 m in the range over 59 days;
  the range is the Earth–Moon distance alone, where this is the Moon's whole place, along its orbit too. What the 3 m
  is made of is not yet worked out.

