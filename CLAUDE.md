# Working in this repository

## Sessions and branches

Several Claude sessions often work on this project at the same time, so each session that changes files works in its
own git worktree.

- Only one session works in the main folder, `/Users/tom/code`. Every other session that edits files works in its own
  worktree, with its own branch.
- In the main folder, don't switch branches, stash, reset or check out other files unless you are the only session
  working there. If a task needs a different branch, make a worktree for it:
  `git worktree add ../code-<task> <branch>`.
- A session that only reads files can share the main folder.
- Commit only the files you changed yourself.
- When a worktree's branch has been merged, remove the worktree with `git worktree remove`.

## Git

- Commit, merge and push only when asked. Never skip the hooks with `--no-verify`.

## Where things live

- The viewer's source is `web/`. `docs/viewer/` is a gitignored copy made when the site is built, so don't edit it.
- New viewer features go only in the web app, which comes in three forms: the player, the viewer and the studio.
  Display options belong in the viewer, and saving, loading and running studies belong in the studio. The Python
  viewer in `viewer/` is being replaced, so it gets no new features.
- Old drafts are in `notes/drafts/`. There is no `docs/archive/` any more.
- The to-do lists are four Claude Docs documents (Document, Model, Viewer and Reading list), not files in the
  repository. Don't create TODO files.

## Studies and numbers

- Pass settings to a study through environment variables or arguments, not module-level globals. Spawned
  multiprocessing workers don't inherit the main process's globals.
- Before quoting a number on a page, check that it has converged, for example by halving the step or by Richardson
  extrapolation. Record the step and the integrator in the run's summary.
- When a result changes, update every page that quotes it, including the scorecard in `docs/part3/conclusion.md`.
- Run anything likely to take more than a couple of minutes in the background, with its output in
  `notes/review/scratch/`. Afterwards, check for leftover worker processes and stop them.
- A study that is edited or rerun moves to the backgrounds-file format, with a written description of each
  background.

## Pages and diagrams

- Wording added to pages is written in full, plain sentences, without clipped phrasing.
- Diagrams are drawn by `scripts/draw_diagrams.py`, in its formal style.

## Checking the viewer

- After changing `web/viewer.js` or `web/index.html`, check that the site's embedded players look the same as
  before. Serve the project with the `web-viewer` launch configuration (port 8765), then compare each run in
  `/site/viewer/index.html?player&run=...` (the published viewer) with `/web/index.html?player&run=...`.
