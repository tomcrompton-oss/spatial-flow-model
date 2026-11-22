# To do

Work that isn't on the site's "Not yet tested" lists (those are on
[The model, step by step](docs/evolution.md#not-yet-tested)).

## An independent review by a second model

Everything since the reframing (the step-by-step page, What comes from outside, Prior work, the lapse page's later
sections, and the sympy studies) was derived, written and checked in one model's sessions. A cold read by another
model would catch overclaims, physics slips and numbers that disagree between pages. It is a first check, not a
substitute for a GR physicist reading it.

**How:** a new Claude Code session on Claude Fable 5.2 (the app's model selector), with no memory of earlier sessions,
given the brief below. Rough cost on the API: $10–20 for an agentic review (it reads files and reruns studies), $2–4 for
a single read of the docs and key studies; on a subscription plan it counts against the plan's usage instead.

**Brief to give it:**

> Review this repository's physics write-up. Don't edit anything; report findings with file and line, ranked by
> severity (wrong, overclaimed, unclear, nit), each with what would fix it.
>
> 1. Check every claim on `docs/from-outside.md`, `docs/evolution.md` and `docs/prior-work.md` against the study it
>    cites. Flag any sentence that says more than its study shows (for example "derived" or "exact" where the work
>    only argues).
> 2. Run `studies/ball_law.py`, `studies/field_from_bodies.py`, `studies/frame_dragging.py` and
>    `studies/eccentric_bodies.py` (sympy is needed for the first two). For each, judge whether it really tests what
>    the pages say it does: assumptions, sign conventions, post-Newtonian order counting, and whether a check could
>    pass for the wrong reason.
> 3. Check the physics in `docs/lapse-curved-space.md`, sections "Where rules 3–5 come from" and "Off circles: the
>    J = 0 flow for an eccentric binary".
> 4. Check that numbers quoted in more than one place (`docs/scorecard.md`, `docs/part2.md`, `docs/evolution.md`,
>    `docs/lapse-curved-space.md`) agree.
> 5. Say whether the novelty claims on `docs/prior-work.md` are fair, and name any prior work they miss.

## Smaller items

- `archive/` (28 MB, gitignored, local only): dated safety copies from before git. Delete when no longer wanted.
