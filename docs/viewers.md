# Viewers

Both viewers read the files the studies write ([file formats](formats.md)); neither does any physics of its own
beyond drawing it.

## Desktop viewer

`python3 viewer/csv_viewer.py <run>/<view>.full.json` — tkinter, part of the project. It plots paths in x / y or
distance against time, replays runs, splits orbits and marks their apsides, and draws backgrounds worked out live from
the bodies: flow and gravity arrows, lines of equal |u|, flow lines, horizons, photon orbits and ISCOs, and a rotating
hole's ergosphere and twist. Its Sim tab runs studies.

## Browser viewer

The viewer embedded in these pages (`web/`): static HTML and JavaScript, with no server and nothing to install. Open a
run folder with **Open run folder…**, drop one on the plot, or pass `?run=<path to a .full.json>`.

- paths with the run's own colours and styles, a legend, pan and zoom, units
- replay with trails, at 0.25–4× speed
- bodies and horizons
- u and g arrows from the run's background frames, to one scale for the whole run, for one environment or all of them

## Backgrounds that change with time

A study can write its flow on a grid at a run of times (`engine/background_frames.py`) and name the file in its log.
Both viewers then draw the arrows as they are at the replay time, so a wave's arrows shrink, reverse and grow as it
passes. A steady flow is written as one frame, for the browser viewer; the desktop viewer works a steady flow out
exactly instead.
