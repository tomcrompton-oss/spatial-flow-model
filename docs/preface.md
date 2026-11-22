# Preface

This site is about one way of seeing gravity: as space flowing. Space falls into a body at the speed something would
fall from rest far away, clocks tick slower only because of their speed through the space around them, and particles
and light move through that space as they would through still space. It is not a new theory. It is general
relativity, described in the coordinates of its free-falling observers, and the aim here is to find out how far that
picture can be taken, and what it has to give up along the way.

For one body the picture is exact. Space flowing in at the escape velocity through flat space is the Schwarzschild
solution in Gullstrand–Painlevé coordinates, the "river model" of black holes, and Part 1 works it through from first
principles: the mechanics of moving through flowing space, and GR's four classical tests – the redshift, the bending
of light, Mercury's precession and the Shapiro delay – run in a simulation and matched to exact GR.

For more than one body nothing in the one-body picture says how the bodies' flows combine, and Part 2 is the search
for the rule. Most of the natural rules fail, and the pages keep them, because each failure shows something the flow
must have: a flow without curl (or space doesn't fall at Newton's g), one potential across all the bodies (or light
past a moving planet bends by arcseconds), space stretched across the flow (or the Moon's orbit is hundreds of metres
off), and first post-Newtonian corrections to the flow (or a binary star's orbit turns too slowly). The flow that has
all of them is GR for the Sun, the Earth, the Moon, light past Jupiter and a binary; and its corrections turn out to
be Einstein's own equations in this way of slicing time. So the picture survives with one change: clocks still tick
by their speed through space alone, but space is curved as well as flowing.

Most of it is run, not just derived (the binary and the field equations are worked out exactly, symbolically). The
simulation (Python, in the [repository](https://github.com/tomcrompton-oss/spatial-flow-model)) moves particles and
light step by step through each version of the flow, and the studies compare the results with exact GR, GR's
post-Newtonian equations, and measurement – lunar laser ranging, Cassini, VLBI and the binary pulsars.
The viewers on these pages replay the runs.

**How to read it.** Part 1 stands on its own. For Part 2, [Part 2 in brief](part2.md) gives the result in a page; the
[two-body pages](two-bodies/index.md) go through the rules one at a time; [Lapse and curved space](lapse-curved-space.md)
builds the flow that works; and the [scorecard](scorecard.md) puts every version side by side.
