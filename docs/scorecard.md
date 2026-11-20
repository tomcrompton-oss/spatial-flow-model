# Scorecard

Every model and variation so far, scored out of 10 on five measures. These are judgements from the test results on
the other pages, not computed numbers.

- **Newton**: how well it gives Newton's gravity as c grows without limit.
- **GR**: how many of the relativistic tests it passes, weighted by how badly it fails the rest.
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

| Model | Newton | GR | Conserved | Flow = g | Premise | What it keeps, and gives up |
| --- | --- | --- | --- | --- | --- | --- |
| [One body](part1/conclusion.md) (Painlevé) | 10 | 10 | 10 | 10 | **10** | All four: it is the premise, and it is GR exactly. |
| [Vector addition](two-bodies/vectors.md) | 1 | 1 | 10 | 1 | **9** | The premise taken most simply. Adding the escape velocities as vectors gets g wrong by several times g. |
| [Along g](two-bodies/along-g.md) | 3 | 1 | 10 | 2 | **8** | One flat flow, N = 1. Its direction is forced along g, and it has curl, so space doesn't fall at g. |
| [Eikonal flow](two-bodies/eikonal.md) | 9 | 3 | 10 | 9 | **8** | One flow, from the paths of free fall. It has a seam, and the bodies are at rest. Fails lunar ranging. |
| [Turning](two-bodies/turning.md) (each body carries its flow) | 7 | 4 | 10 | 4 | **7** | One flow, but only in a turning frame with one Jacobi constant, and 56% of the plane has none. Light past the Sun is 9.6 mas off; the Moon's own orbit 16 m off over 90 days, 23 m in Newton's limit; with Newton's error taken out, half of de Sitter's precession. |
| [Split](two-bodies/split.md), Galilean frames, interval light | 10 | 2 | 2 | 10 | **5** | Each body's own Painlevé flow, applied one at a time. There is no single space (part 3 gone). |
| Split, Galilean frames, static light | 10 | 4 | 2 | 10 | **5** | As above. GR with the bodies at rest; fails once the system moves. |
| Split, Lorentz frames | 10 | 5 | 2 | 10 | **5** | As above, the frames set by the bodies' velocities. Lunar ranging 2.2 m, Nordtvedt η = 1. |
| Split, local frames | 10 | 3 | 2 | 10 | **4** | Frames shifted by the other bodies' flow: a rule added on top. Lunar ranging 240 m. |
| Split, free-fall frames | 10 | 5 | 2 | 10 | **4** | As above. Half the de Sitter precession; η = −62,000. |
| Split, carried frames | 10 | 3 | 3 | 10 | **4** | As above; the nearest the split model comes to one shared space. GR's fit leaves 6–13 m. |
| Split, heavier / heavier-centre frames | 10 | 5 | 2 | 10 | **4** | As above. De Sitter k = 0.23 and 0.19. |
| Split, heavier-only frames | 10 | 6 | 2 | 10 | **4** | Passes every Solar System test run. Fails Nordtvedt (η = +99) and has a term that flips with the flow's direction. |
| Split, 'potential' frames | 10 | 4 | 2 | 10 | **3** | Clocks and rulers set by the others' potential: gravity in the clocks and rulers, against parts 1 and 2. η = +16. |
| … plus EIH's terms by hand | 10 | 3 | 2 | 10 | **2** | GR's equations of motion pasted in. η = −1; de Sitter leaves 4.5 m. |
| [Eikonal, λ = κ = 0.5](lapse-curved-space.md) | 9 | 4 | 10 | — | **5** | Half of gravity in the clocks and curved space; every failure halves. |
| Turning, λ = κ = 0.5 | 7 | 4 | 10 | — | **4** | Light past the Sun 4.8 mas off. |
| Eikonal or turning, λ = κ = 1 | 10 | 9 | 10 | — | **1** | No flow left: GR's first post-Newtonian metric, conventional GR. |
| [Eikonal, N = 1, space curved by 2Φ/c²](lapse-curved-space.md#the-clocks-left-alone-space-curved-across-the-flow) | 9 | 6 | 10 | 9 | **6** | Keeps parts 2–4, but space is shaped by Newton's potential, put in from outside the flow. Passes lunar ranging and the Jupiter bending with the bodies at rest. |
| Turning, N = 1, space curved by 2Φ/c² | 7 | 4 | 10 | 4 | **5** | The turning flow's 9.6 mas past the Sun, unchanged. |
| Vectors, N = 1, [space from u](lapse-curved-space.md#space-decided-by-the-flow) | 1 | 1 | 10 | 1 | **8** | Space stretched across the flow by its own u²/c². The vectors' speed isn't 2Φ, so both tests fail. |
| Along g, N = 1, space from u | 3 | 2 | 10 | 2 | **7** | Lunar ranging exactly GR's (round trips see only the flow's speed); light past Jupiter 1000 µas off (its flow has curl). |
| **Eikonal, N = 1, space from u** | 9 | **6** | 10 | 9 | **7** | The same space as by 2Φ/c², now decided by the flow alone. The one flow it makes GR with the bodies at rest. |
| Turning, N = 1, space from the lab's u | 7 | 3 | 10 | 4 | **6** | Light past the Sun passes, but the Earth's 30 km/s gets into the space round it: the Moon's orbit 135 m off. Depends on the frame. |
| **Turning, N = 1, [space from u relative to its body](lapse-curved-space.md#which-frames-u)** | 7 | **4** | 10 | 4 | **6** | Light past the Sun 0.001 mas off (Cassini 0.02). The Moon's orbit 16 m off (Newton's error); with that taken out, half of de Sitter's precession and 0.25 m left. Nordtvedt and the binaries can't run: its bodies are held on circles. |
| [Carried flow](lapse-curved-space.md#the-carried-flow-bodies-that-move-by-it), flat | 5 | 4 | 3 | 5 | **7** | Each body's river carried at its velocity, with the others' tides; the bodies moved by it. Light past the Sun passes; the Moon: half of de Sitter, 0.26 m; binary advance +17% (equal masses), centre of mass accelerates; Nordtvedt η −0.77. |
| Carried flow, flat, [tide transported](lapse-curved-space.md#checking-the-moon-test-with-gr-in-a-moving-time) | 7 | 4 | 3 | 7 | **7** | The same flow with the tide terms the first order left out: space falls at g to 0.016% of the tide at the Moon (was 4%). The Moon unchanged – half of de Sitter, 0.25 m – so that is the flow's own result. GR put in the same time passes (k +0.01, 0.018 m). |
| Carried flow, space from u relative to its body | 5 | 3 | 3 | 5 | **6** | The same, light the same; the bodies' errors doubled: advance +33%, η −1.5. |
| Carried flow, [space from Einstein's constraint](lapse-curved-space.md#einsteins-constraints-what-space-the-flow-needs) (2Φδ − uu) | 5 | 2 | 3 | 5 | **6** | Meets the constraint for any flow with no curl, and light passes; without the flow's matching corrections the Moon (1.8 m), binary (−0.25 of GR's advance) and Nordtvedt (η +589) all get worse. |

Notes:

- **Conserved, for the lapse and curved-space models**: each is one steady spacetime, and the engine keeps its energy
  (E and L to 3 × 10⁻⁸ in its checks). They have not been through the four-orbit study.
- **Flow = g, for the λ models**: the flow carries only 1 − λ of g, and the clocks the rest. The check as defined
  doesn't apply, though Newton's g comes out right.
- **Space curved across the flow**: every version keeps N = 1, so it loses one premise point for no longer being flat.
  Curving it by Newton's potential loses another, because the potential comes from outside the flow; curving it by
  u²/c² doesn't, because the flow decides it.
- **Space from u means u relative to its body.** Built from the lab's u, the space depends on the frame the flow is
  measured in; relative to the body whose flow it is, it doesn't. For bodies at rest the two are the same.
- **The eikonal version's GR score of 6 is provisional**: it is tested only with the bodies at rest. The turning
  version passes light past the Sun but fails the Moon's own orbit at Newton's order (so its Newton score drops from 9
  to 7, on every turning row), and with that taken out still has only half of de Sitter's precession.
- **The Moon test is checked**: GR transformed exactly to a time with a 30 km/s flow, and GR in the carried flow's
  own time once its tide is transported, both fit as GR does (k +0.017 and +0.010, 0.03 and 0.02 m). So the moving
  flows' half of de Sitter is theirs, not the test's.
- **The carried flow** is the moving-body flow with the bodies moved by it. Its Newton score is 5: the tides round each
  body are right only to a few % (fine for the binary, where each body sees only the other's river). Conserved 3: no
  particle quantity is kept with the bodies moving, and the binary's centre of mass accelerates. It passes light, and
  fails the Moon, the binary and Nordtvedt as the split model does.

## What the scores show

- **The trade-off.** Every gain on GR has cost on the premise: the split model reaches 6 by dropping the single flow,
  and the lapse family reaches 9 by dropping the flow altogether.
- **The exception, and its limit.** Space curved across the flow, by the flow's own speed, is off that line for
  bodies at rest: 6 on GR and 7 on the premise. With the bodies moving, every flow tried – turning or carried, flat or
  curved – passes light but has half of de Sitter's precession, and the carried flow's bodies fail the binary and
  Nordtvedt. What is missing is the same each time: each body's flow (and the Sun's curved space) acting on the
  others', which needs the flows solved together, not carried separately. It keeps "clocks tick by their speed through
  space", and changes "space is flat" to "space is stretched across its own motion by u²/c²".
- **The two checks pull opposite ways.** Every single-flow model keeps its conserved quantities; every split model's
  flows give g exactly, and none keeps its energy.
