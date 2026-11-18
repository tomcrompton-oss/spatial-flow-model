# Each body separately

**The rule:** no single flow at all. Each body keeps its own one-body flow, straight in at $\sqrt{2GM/d}$ in its own
rest frame. A step works out what each body's flow alone would do to a particle, using the one-body model's own step,
and applies the changes one after the other: the Sun's, then the Earth's. The particle moves once, at its velocity.

**Verdict: ❌ fails.** With one body much heavier than the other it passes most tests – Newton's g, clocks, light
past Jupiter, causality, a moving system. With free-fall frames the Moon's orbit has only about half GR's de Sitter
precession, which lunar laser ranging measures to under 1%. With [each body's flow carried by the heavier body's
space where the particle is](#coupling-the-flows-carrying-a-bodys-flow-in-the-heavier-bodys-space), the Moon comes
right: GR's de Sitter precession, and lunar ranging within the test's floor. But then a bound pair falling towards the
Sun falls too slowly (the Nordtvedt effect, 10⁶ times what lunar ranging allows). And in a binary of comparable
masses the orbit turns 17% too slowly at equal masses and the pair's centre of mass accelerates by itself, which
binary pulsars rule out: the bodies' fields need to act on each other, and in this model they don't.

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
| **The Moon's own orbit, the Earth going round the Sun: lunar laser ranging** | GR's range, to millimetres | – | – | ❌ 2.2 m rms; 2.7 m at half the synodic period | ❓ 0.15 m rms, against the test's 8 cm with the Sun; 8 cm at half the synodic period, 3 cm at it. ✅ 0.063 m, within the floor, with [heavier-only frames](#coupling-the-flows-carrying-a-bodys-flow-in-the-heavier-bodys-space) |
| **A binary of comparable masses: the periastron advance** | GR's, for any mass ratio; the double pulsar to about 10⁻⁴ | – | – | ❌ 25% too much at equal masses | ❌ 17% too little at equal masses |
| A binary of comparable masses: the centre of mass | stays put (momentum is conserved) | – | – | ❌ accelerates | ❌ accelerates, 0.17 m/s² at a mass ratio of 0.1 |
| The binary's period (orbital decay) | shrinks only by gravitational waves: GR −2.5 × 10⁻¹⁰ s/s; Hulse–Taylor matches GR to 0.2% | – | – | ❌ −7.8 × 10⁻⁴ s/s | ❌ −1.4 × 10⁻³ s/s |
| Light past a moving Jupiter: GR's (1 − v·k/c) in the bending | VLBI (2003), to about 20% | – | – | ✅ to 3 × 10⁻⁷ | ✅ (one body: the same) |
| The Nordtvedt effect: a bound pair falling towards the Sun | falls as a single body; lunar laser ranging η < 10⁻⁴ | – | – | ❌ η = 1.00 | – (three bodies: see below); ❌ η = +99 with heavier-only frames |
| De Sitter precession of the Moon's orbit, over 90 days | GR's 19.2 mas a year; lunar laser ranging to under 1% | – | – | – | ❌ about half of it: k = 0.39 and 0.52 from two starts (0 = GR's, 1 = none). ✅ k = 0.01 with [heavier-only frames](#coupling-the-flows-carrying-a-bodys-flow-in-the-heavier-bodys-space) |

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
| GR's de Sitter precession of a frame falling round the Sun (19 mas a year) | a turning of GR's Moon's frame added to the fit | takes out 2% (the [de Sitter test](#four-more-tests) below finds the model has about half of GR's) |

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
Sun, as lunar laser ranging's own ephemerides are. The [de Sitter test](#four-more-tests) below does settle it: fitting
GR's orbit to the model's (rather than its range), in the same coordinates, the model's Moon has only about half GR's
de Sitter precession. (These ranges were run before the step was changed to work each body's changes as changes.)

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
- **De Sitter precession ❌: about half of it.** GR has a frame falling round the Sun turning 19.2 mas a year against
  the stars, and the Moon's orbit with it; lunar laser ranging measures that to under 1%. `studies/de_sitter.py` runs
  the Moon for 90 days and fits GR to the model's track with GR's start free and GR run in a frame turning at k times
  the de Sitter rate: k = 0 means the model has GR's precession, k = 1 none. Three things had to be got right first:
  - *The start.* A start 1 part in 10⁸ different moves the perigee's rate by 15–34 mas a year, so the perigee's rate
    from a common start shows nothing; the start has to be fitted.
  - *The step.* Each body's change is now worked as a change (of place, of flow, and of velocity carried back from the
    body's frame) instead of a difference of large numbers. Taking the Moon's whole 30 km/s into each body's frame and
    back lost a fixed part in 10¹⁶ each step, which built up as the step shrank. Now the model with c × 1000 matches
    Newton to 1–2 cm over 90 days.
  - *The coordinates.* The model's lab is the Sun's flowing-space coordinates (areal radius, the space's own time);
    GR's are harmonic. Between them the Earth–Moon line differs by 10⁻⁸ across and by a time shift of u/c² per metre
    from the Earth: about 4 m, which had looked like a 3 m failure. Mapped to harmonic coordinates (r − GM/c²,
    t = T − 2√(2GMr)/c², to first order), the Sun alone matches GR to 1 mm.

  | 90 days, steps 5 and 2.5 s, extrapolated | k | fit rms |
  | --- | --- | --- |
  | eccentric start (e ≈ 0.12) | +0.39 (+0.46 with GM_Earth free) | 0.56 m (0.35 m) |
  | lunar ranging start | +0.52 (+0.51) | 0.43 m (0.50 m) |
  | c × 1000 control | 0.003, 0.005 | 1–2 cm |
  | calibration: GR against GR turned | 1.00 (eccentric), 0.83 (lunar) | 1–13 cm |

  The two starts now agree: the model's Moon orbit turns at about half GR's de Sitter rate, so the model has some of
  the effect but not all of it. That fails lunar ranging by a long way. The eccentric start is the cleaner one (its
  calibration gives 1.00; the lunar start's orbit is nearly round, so the perigee is less sharp). The extrapolation is
  a large correction (k is 1.65 at 5 s and 0.64 at 2.5 s), so k is good to perhaps ± 0.2. And the fit still leaves
  0.4–0.6 m against the control's 1–2 cm: besides the turning, the model's orbit differs from GR's by half a metre over
  90 days, which a turning doesn't take out.


## Coupling the flows: carrying a body's flow in the heavier body's space

The split model gives each body its one-body flow and nothing else. GR's equations of motion for several bodies at
first post-Newtonian order (Einstein, Infeld and Hoffmann's) also have cross terms, where one body's pull on another
depends on a third body, or on the body pulled. `studies/cross_terms.py` runs GR with each kind switched off, to see
which ones the model is missing:

| GR with this left out | the binary's periastron advance (GR: no η in it) | de Sitter k for the Moon (0 = GR's) |
| --- | --- | --- |
| the place pulled sitting in a third body's potential (F) | – | +0.34 |
| the source sitting in a third body's potential (S) | – | 0.00 |
| the source sitting in the pulled body's potential (Sa) | +η/3 | – |
| the source accelerating: the ½ (x_b − x_a)·a_b term (C1) | +η/6 | −0.02 |
| the source accelerating: the 7/2 G m_b a_b/(c² r) term (C2) | +7η/6 | −0.49 |

The model's binary errors (+1.0 η with Lorentz frames, −0.66 η with free-fall frames) match no combination of these.
Its centre of mass accelerates at 0.17 m/s², four times as fast as GR with every cross term left out (0.046 m/s²). So
the binary's errors are not simply missing terms: they come with the model's coordinates and frames. For the Moon, the
place pulled sitting in the Sun's potential carries a third of GR's de Sitter precession (in harmonic coordinates: how
terms split between kinds depends on the coordinates).

In the model's own picture that term is the Sun's space not being the same at the Earth and at the Moon. Free-fall
frames take the Sun's flow at the Earth's centre. So the frame rule was changed to take it where the particle is.
Four versions were tried (`engine/split.py`'s boosts), with the de Sitter test as above (90 days, extrapolated, in
harmonic coordinates):

| Frame rule | de Sitter k, eccentric start | lunar start | GR's fit leaves |
| --- | --- | --- | --- |
| free-fall: the others' space at the body's centre | +0.39 | +0.52 | 0.56 m, 0.43 m |
| carried: every other body's space where the particle is | +0.25 | +21 | 5.7 m, 12.8 m |
| heavier: the heavier bodies' space where the particle is, the lighter ones' at the body's centre | +0.23 | +0.36 | 0.17 m, 0.22 m |
| heavier-centre: the heavier bodies' space at the body's centre, the lighter ones' left out | +0.19 | – | 0.37 m |
| **heavier-only: the heavier bodies' space where the particle is, the lighter ones' left out** | **+0.010** | **+0.10** | **0.08 m, 0.21 m** |

With heavier-only frames the Earth's flow is carried by the Sun's space round the Moon, and the Sun's flow is worked
in the Sun's own Lorentz frame. The model then has GR's de Sitter precession: k = 0.01 from the eccentric start, whose
calibration gives exactly 1. The lunar start's calibration is only 0.83, so its 0.10 is within its own error. 'Carried'
Both parts count: leaving out the lighter bodies' space (the Sun's step no longer shifted by the Earth's space at the
Sun) takes k from 0.39 to 0.19, and taking the Sun's space where the Moon is takes it to 0.01. 'Carried'
also shifts the Sun's flow by the Earth's space round the Moon (1.4 km/s), and that is far too much: a term in
$u_{\text{Earth}}\,u_{\text{Sun}}$, which goes as $\sqrt{M_{\text{Earth}} M_{\text{Sun}}}$, where GR's cross terms
go as $M_{\text{Earth}} M_{\text{Sun}}$.

The other checks, with heavier-only frames:

| Check | Result |
| --- | --- |
| The Earth going round the Sun the other way | k = −0.006 (calibration 0.97); GR's fit leaves 0.06 m |
| The Earth at 2 AU | GR's fit leaves 3.8 cm. (k can't be measured there: GR's rate is a fifth as large, and the calibration gives 0.19) |
| Lunar laser ranging, the Moon's own orbit (test 1 above) | **0.063 m rms, within the test's floor (0.077 m)**; 0.2 mm at the synodic angle D, 3 cm at 2D. (Free-fall frames, rerun: 0.151 m) |
| Newton's g, clocks, light past Jupiter, the system moving together, causality (`studies/frame_checks.py`) | the same as with free-fall frames |
| Each body's flow running out instead of in (`studies/flow_sign.py`: the same space, so GR's predictions don't change) | the Sun's out: k = 0.09 (0.12 with GM_Earth free), GR's fit leaving 1–4 cm; the Earth's out: k = 0.002. The part odd in the Sun's flow is 0.04–0.05 of the de Sitter rate, in the Earth's 0.002 |
| The binary of comparable masses | no change: with two bodies there is no third body's space, so heavier-only frames are Lorentz frames there (+1.0 η) |
| **The Nordtvedt effect** (a bound pair falling towards the Sun) | **❌ η = +99** (Lorentz frames 1.00, free-fall −62,000; lunar laser ranging 10⁻⁴) |

The Nordtvedt result shows what is still wrong. In GR a body's flow can as well run out of it as in: the same space,
in other coordinates. So no prediction can depend on which way a flow runs. With the Sun's flow running out instead of
in, the pair's η is −102 instead of +99: almost all of it reverses with the Sun's flow, so it comes from a term odd in
$u_{\text{Sun}}$, which GR doesn't have. (Its even part, η ≈ −1.7, is about as wrong as Lorentz frames' 1.0.) Two
attempts to remove it didn't work:

- averaging each body's step over the Sun's space flowing in and out (only the frame, not the Sun's own step or the
  coordinates, so not the same space described two ways): de Sitter fails by 3.7–5 m;
- building each body's frame where it is at the moment simultaneous, in its frame, with the particle (in case the
  odd term came from the pair's acceleration across a simultaneity the Sun's flow shifts): no change at all.

Taking the Sun's space at the body's centre instead ('heavier-centre') leaves it as it is (η = +104 in, −97 out). So
the odd term comes with shifting a body's frame by the Sun's flow at all. It grows with the pair's speed round each
other (8,000 km/s here): for the Moon, at 1 km/s round the Earth, it is the 4–5% of the de Sitter rate above.

So heavier-only frames fix the Moon: lunar ranging comes within the test's floor, and de Sitter precession agrees with
GR. They don't fix the Nordtvedt effect, and they can't fix the binary of comparable masses, where what is missing is
each body's field acting on its own source.
