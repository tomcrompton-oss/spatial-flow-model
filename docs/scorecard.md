# Scorecard

Every model and variation so far, scored out of 10 on eight measures. These are judgements from the test results on
the other pages, not computed numbers. A dash means the model can't take that test (its bodies are at rest, or held
on their paths), not that it failed it.

- **Newton**: how well it gives Newton's gravity as c grows without limit.
- **GR**, in four parts, each a different thing GR adds to Newton (roughly PPN's parameters, in the same order):
    1. **One body**: a single body at rest – the orbits' precession, light's bending and delay, clocks (PPN γ and β).
    2. **Combined**: two or more bodies' fields together, with no effect of their motion – lunar ranging's synodic
       term, light past Jupiter less each body alone, light past the Sun with the Earth there, Einstein's constraints.
    3. **Moving sources**: what a body's motion does to its field, felt by a test body or light – the Moon's own orbit
       and its de Sitter precession, light past a moving Jupiter, the whole system moving together (PPN's
       preferred-frame terms).
    4. **Self-motion**: bodies moved by each other's fields – a binary of comparable masses (its periastron advance,
       and its centre of mass staying put), the Nordtvedt effect (PPN's conservation and strong-equivalence terms).
- **Conserved**: whether a particle keeps its energy, angular momentum or Jacobi constant where GR says it should
  ([Two checks on every model](two-bodies/checks.md)).
- **Flow = g**: whether space moving with the flow falls at Newton's g ([Two checks on every model](two-bodies/checks.md)).
- **Premise**: how close it stays to Part 1's hypothesis, which has four parts:
    1. gravity is space flowing through flat, Euclidean space;
    2. clocks slow only by their speed through the space around them (lapse N = 1);
    3. there is one flow, built from the bodies, and moving with it is free fall at g;
    4. particles move relative to the space they are in.

  10 keeps all four; each part dropped, or patched by a rule put in by hand, costs points.

## Scores

| Model | Newton | One body | Combined | Moving | Self-motion | Conserved | Flow = g | Premise | What it keeps, and gives up |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [One body](part1/conclusion.md) (Painlevé) | 10 | 10 | – | – | – | 10 | 10 | **10** | All four: it is the premise, and it is GR exactly. |
| [Vector addition](two-bodies/vectors.md) | 1 | 10 | 0 | 0 | – | 10 | 1 | **9** | The premise taken most simply. Adding the escape velocities as vectors gets g wrong by several times g; a moving Earth carrying its flow is 10⁴ × the Sun's tide off. |
| [Along g](two-bodies/along-g.md) | 3 | 10 | 1 | – | – | 10 | 2 | **8** | One flat flow, N = 1. Its direction is forced along g, and it has curl, so space doesn't fall at g. |
| [Eikonal flow](two-bodies/eikonal.md) | 9 | 10 | 2 | – | – | 10 | 9 | **8** | One flow, from the paths of free fall. It has a seam, and the bodies are at rest. Fails lunar ranging (27σ) and light past Jupiter (400 µas). |
| [Turning](two-bodies/turning.md) (each body carries its flow) | 7 | 10 | 3 | 4 | – | 10 | 4 | **7** | One flow, but only in a turning frame with one Jacobi constant, and 56% of the plane has none. Lunar ranging's synodic term passes; light past the Sun is 9.6 mas off. The Moon's own orbit 16 m off over 90 days (23 m in Newton's limit); with Newton's error taken out, half of de Sitter's precession. |
| [Split](two-bodies/split.md), Galilean frames, interval light | 10 | 10 | 4 | 1 | – | 2 | 10 | **5** | Each body's own Painlevé flow, applied one at a time. There is no single space (part 3 gone). Lunar range to a held mirror 0.45 m off; light can be outrun; the whole system moving changes radar to the Moon by 290 m. |
| Split, Galilean frames, static light | 10 | 10 | 10 | – | – | 2 | 10 | **5** | As above, with light's rule fixed: GR with the bodies at rest. That rule needs the bodies at rest, so nothing moving can be run. |
| Split, Lorentz frames | 10 | 10 | 10 | 4 | 1 | 2 | 10 | **5** | As above, the frames set by the bodies' velocities. The system moving and light past a moving Jupiter pass; the Moon's own orbit 2.2 m off. Binary advance +25%, the centre of mass accelerates, Nordtvedt η = 1. |
| Split, local frames | 10 | 10 | 10 | 0 | – | 2 | 10 | **4** | Frames shifted by the other bodies' flow: a rule added on top. The Moon's orbit 240 m off. |
| Split, free-fall frames | 10 | 10 | 10 | 5 | 1 | 2 | 10 | **4** | As above. Half of de Sitter's precession, the Moon 0.15 m off; binary advance −17%, η = −62,000. |
| Split, carried frames | 10 | 10 | 10 | 2 | – | 3 | 10 | **4** | As above; the nearest the split model comes to one shared space. De Sitter k +0.25 and +21 from two starts; GR's fit leaves 6–13 m. |
| Split, heavier / heavier-centre frames | 10 | 10 | 10 | 6 | – | 2 | 10 | **4** | As above. De Sitter k = 0.23 and 0.19, 0.2–0.4 m left. |
| Split, heavier-only frames | 10 | 10 | 10 | 8 | 1 | 2 | 10 | **4** | Passes every Solar System test run: the Moon within the test's floor, de Sitter k = 0.01. But a part flips with the flow's direction (k 0.09 with the Sun's flow out); the binary is Lorentz frames' (+25%), and Nordtvedt η = +99. |
| Split, 'potential' frames | 10 | 10 | 10 | – | 1 | 2 | 10 | **3** | Clocks and rulers set by the others' potential: gravity in the clocks and rulers, against parts 1 and 2. No odd part; η = +16. |
| … plus EIH's terms by hand | 10 | 10 | 10 | 2 | 2 | 2 | 10 | **2** | GR's equations of motion pasted in. η = −1; de Sitter's fit leaves 4.5 m and doesn't settle as the step is halved. |
| [Eikonal, λ = κ = 0.5](lapse-curved-space.md) | 9 | 10 | 5 | – | – | 10 | – | **5** | Half of gravity in the clocks and curved space; every failure halves. |
| Turning, λ = κ = 0.5 | 7 | 10 | 5 | – | – | 10 | – | **4** | Light past the Sun 4.8 mas off. |
| Eikonal or turning, λ = κ = 1 | 10 | 10 | 10 | 10 | – | 10 | – | **1** | No flow left: GR's first post-Newtonian metric, conventional GR. Its bodies are held on their paths. |
| [Eikonal, N = 1, space curved by 2Φ/c²](lapse-curved-space.md#the-clocks-left-alone-space-curved-across-the-flow) | 9 | 10 | 10 | – | – | 10 | 9 | **6** | Keeps parts 2–4, but space is shaped by Newton's potential, put in from outside the flow. Passes lunar ranging and the Jupiter bending, with the bodies at rest. |
| Turning, N = 1, space curved by 2Φ/c² | 7 | 10 | 3 | – | – | 10 | 4 | **5** | The turning flow's 9.6 mas past the Sun, unchanged. |
| Vectors, N = 1, [space from u](lapse-curved-space.md#space-decided-by-the-flow) | 1 | 10 | 0 | – | – | 10 | 1 | **8** | Space stretched across the flow by its own u²/c². The vectors' speed isn't 2Φ, so both tests fail. |
| Along g, N = 1, space from u | 3 | 10 | 4 | – | – | 10 | 2 | **7** | Lunar ranging exactly GR's (round trips see only the flow's speed); light past Jupiter 1000 µas off (its flow has curl). |
| **Eikonal, N = 1, space from u** | 9 | 10 | **10** | – | – | 10 | 9 | **7** | The same space as by 2Φ/c², now decided by the flow alone. The one flow it makes GR with the bodies at rest; it can't move them. |
| Turning, N = 1, space from the lab's u | 7 | 10 | 8 | 1 | – | 10 | 4 | **6** | Light past the Sun passes, but the Earth's 30 km/s gets into the space round it: the Moon's orbit 135 m off. Depends on the frame. |
| **Turning, N = 1, [space from u relative to its body](lapse-curved-space.md#which-frames-u)** | 7 | 10 | **8** | 4 | – | 10 | 4 | **6** | Light past the Sun 0.001 mas off (Cassini 0.02). The Moon's orbit 16 m off (Newton's error); with that taken out, half of de Sitter's precession and 0.25 m left. Its bodies are held on circles. |
| [Carried flow](lapse-curved-space.md#the-carried-flow-bodies-that-move-by-it), flat | 5 | 10 | 8 | 4 | 2 | 3 | 5 | **7** | Each body's river carried at its velocity, with the others' tides; the bodies moved by it. Light past the Sun passes; the Moon: half of de Sitter, 0.26 m; binary advance +17% (equal masses), centre of mass accelerates; Nordtvedt η −0.77. |
| Carried flow, flat, [tide transported](lapse-curved-space.md#checking-the-moon-test-with-gr-in-a-moving-time) | 7 | 10 | 8 | 4 | 2 | 3 | 7 | **7** | The same flow with the tide terms the first order left out: space falls at g to 0.016% of the tide at the Moon (was 4%). The Moon unchanged – half of de Sitter, 0.25 m – so that is the flow's own result. |
| Carried flow, space from u relative to its body | 5 | 10 | 8 | 4 | 1 | 3 | 5 | **6** | The same, light the same, the Moon the same; the bodies' errors doubled: advance +33%, η −1.5. |
| Carried flow, [space from Einstein's constraint](lapse-curved-space.md#einsteins-constraints-what-space-the-flow-needs) (2Φδ − uu) | 5 | 10 | 8 | 2 | 0 | 3 | 5 | **6** | Meets the constraint for any flow with no curl, and light passes; without the flow's matching corrections the Moon (1.8 m), binary (−0.25 of GR's advance) and Nordtvedt (η +589) all get worse. |

**Checks**: GR itself in the moving flows' time – not models, but what shows which of the results above to trust:

| Check | Newton | One body | Combined | Moving | Self-motion | Conserved | Flow = g | Premise | What it shows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [GR transformed exactly](lapse-curved-space.md#checking-the-moon-test-with-gr-in-a-moving-time) to the time of the Earth's carried river | 10 | 10 | 10 | 10 | – | 10 | 2 | **1** | GR with a 30 km/s flow: the Moon fits as GR does (k +0.017, 0.027 m), so the engine and the mapping are right. The flow is the Earth's river alone, the rest of gravity in the clocks. |
| GR in the carried flow's free-fall time, tide transported | 7 | 10 | 10 | 10 | 3 | 3 | 7 | **3** | The Moon is GR's (k +0.010, 0.018 m), so the carried flow's half of de Sitter is its own. Moved as the carried bodies are, the binary gets 0.83 of GR's advance at equal masses: each body feels only the others' field. |

Notes:

- **The four GR parts separate the models.** Every flow model has GR's one body; the flat flows fail when fields
  combine; space from u fixes that for the eikonal flow; every moving flow has half of de Sitter (Moving 4); and every
  model whose bodies move by the others' fields fails the binary and Nordtvedt (Self-motion 0–2) – including GR's own
  metric moved that way (the second check), so that part is about how the bodies are moved, not the flow.
- **A dash is not a pass.** The eikonal flow with space from u has 10 on both the parts it can take, and nothing on
  the two it can't: its bodies are at rest. The lapse family's λ = 1 holds its bodies on their paths.
- **The split frames' Combined scores** are the free-fall and heavier-only frames' static checks (Newton's g, clocks,
  light past Jupiter, causality, the lunar range to a held mirror), which are the same for every frame rule built on
  Lorentz frames.
- **Conserved, for the lapse and curved-space models**: each is one steady spacetime, and the engine keeps its energy
  (E and L to 3 × 10⁻⁸ in its checks). They have not been through the four-orbit study.
- **Flow = g, for the λ models**: the flow carries only 1 − λ of g, and the clocks the rest. The check as defined
  doesn't apply, though Newton's g comes out right.
- **Space curved across the flow**: every version keeps N = 1, so it loses one premise point for no longer being flat.
  Curving it by Newton's potential loses another, because the potential comes from outside the flow; curving it by
  u²/c² doesn't, because the flow decides it.
- **Space from u means u relative to its body.** Built from the lab's u, the space depends on the frame the flow is
  measured in; relative to the body whose flow it is, it doesn't. For bodies at rest the two are the same.
- **The turning flow's Newton score is 7**, on every turning row: it fails the Moon's own orbit at Newton's order.
- **The carried flow** is the moving-body flow with the bodies moved by it. Its Newton score is 5 with the first-order
  tide (right to a few % round each body), 7 with the tide transported (0.016% at the Moon, 1.4% at the edge of the
  Earth's region). Conserved 3: no particle quantity is kept with the bodies moving, and the binary's centre of mass
  accelerates.
- **The Moon test is checked**: GR transformed exactly to a time with a 30 km/s flow, and GR in the carried flow's
  own time once its tide is transported, both fit as GR does. So the moving flows' half of de Sitter is theirs, not
  the test's.

## What the scores show

- **The trade-off.** Every gain on GR has cost on the premise: the split model reaches Moving 8 by dropping the single
  flow, and the lapse family reaches 10 by dropping the flow altogether.
- **Where the flow model stands.** With space stretched across its own motion by u²/c², the flow model is GR for one
  body and for bodies at rest together (the eikonal flow: 10 and 10, premise 7). The gaps are the two moving parts.
  Every moving flow – turning or carried, flat or curved – has half of de Sitter's precession (Moving 4); and bodies
  moved by the others' flows fail the binary and Nordtvedt (Self-motion 2 at best), as GR's own metric does when its
  bodies are moved that way.
- **What would close them.** De Sitter needs the Sun's curved space carried round with the Earth; the binary and
  Nordtvedt need each body's field to act on its own source. Both point to the bodies' flows solved together – a
  field equation for the flow – not each one carried separately.
- **The two checks pull opposite ways.** Every single-flow model keeps its conserved quantities; every split model's
  flows give g exactly, and none keeps its energy.
