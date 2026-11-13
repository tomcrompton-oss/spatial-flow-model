# Results

Study results published with the site. Each opens in the browser viewer; the files are plain csv, logs and json (see
[file formats](formats.md)) and can be downloaded from the [repository](https://github.com/tomcrompton-oss/spatial-flow-model/tree/main/docs/runs).

| Run | Study | Open |
| --- | --- | --- |
| Rings in a wave through the plane (plus, cross, circular) | `studies/grav_wave.py` | [viewer](../viewer/index.html?run=../runs/gravWave/gravWave.full.json){ target=_blank } |
| A wave sweeping across the plane, with its front | `studies/grav_wave_across.py` | [viewer](../viewer/index.html?run=../runs/gravWaveAcross/gravWaveAcross.full.json){ target=_blank } |
| Thirty falls towards two holes, eikonal flow | `studies/two_body_falls.py` | [viewer](../viewer/index.html?run=../runs/twoBodyFalls/twoBodyFalls.full.json){ target=_blank } |

To publish another run: `python3 scripts/publish_run.py logs/<study>/<run>`, which copies it to `docs/runs/<study>/`
without the absolute paths in its viewer config, then add a row here.
