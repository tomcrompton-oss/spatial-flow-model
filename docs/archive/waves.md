# Gravitational waves

A plane gravitational wave is a flow of space that changes with time. How well the model holds one depends on which
way it travels.

## Through the plane: exact

For a wave travelling along z, straight through the (x, y) plane, GR's metric in TT coordinates becomes, measuring
distances properly and to first order in the strain h,

$$
ds^2 = -c^2dt^2 + |d\mathbf X - \mathbf u\,dt|^2, \qquad
\mathbf u = \tfrac12\left(\dot h_+ X + \dot h_\times Y,\; \dot h_\times X - \dot h_+ Y\right)
$$

which is the model's form exactly: flat space, flowing. The flow is a shear with no curl and no divergence.
Checked against GR at h = 10⁻⁶ (studies/grav_wave.py), each error as a fraction of the wave's own effect:

| Check | Worst error |
| --- | --- |
| free particles keep their TT coordinates | 2.8 × 10⁻⁶ |
| particles starting at rest follow geodesic deviation | 1.1 × 10⁻⁵ |
| light round trips to a free mirror, arms 0.01–1.3 wavelengths, any direction | 5.5 × 10⁻⁶ |

<iframe src="../../viewer/index.html?run=../runs/gravWave/gravWave.full.json" width="100%" height="560" loading="lazy" title="Rings in a wave through the plane"></iframe>

[Open full screen](../../viewer/index.html?run=../runs/gravWave/gravWave.full.json){ target=_blank }

## Across the plane: approximate

A wave travelling within the plane, left to right, also curves space itself (curvature about $-\ddot h/2c^2$), which
the model's flat space cannot hold. Its nearest version is the flow $u_y = \tfrac12\dot h(t - x/c)\,y$: vertical
stretching in bands that sweep across at c. Checked against GR (studies/grav_wave_across.py), with the true geodesics
of that flow alongside to tell flat space from the model's step:

| Check | The model | Geodesics of the flow |
| --- | --- | --- |
| slow things; light along or across the wave, any distance | right | right |
| light at 30–60°, arms 0.25–1 wavelength | off by 0.08–0.46 of h L/c | the same |
| particles at 0.5–0.9c along the wave | off by 9–27 h y₀ | off by about 3 h y₀ |

So the light error is all flat space. For fast particles the model's step adds more: it takes
$\dot{\mathbf w} = -(\mathbf w\cdot\nabla)\mathbf u$, which is the true geodesic only where the flow has no curl,
and this flow has curl. A wave through the plane has neither problem. (These runs used that step; the simulation's
default is now the momentum step, the metric's own path, which leaves only the flat-space part.)

<iframe src="../../viewer/index.html?run=../runs/gravWaveAcross/gravWaveAcross.full.json" width="100%" height="560" loading="lazy" title="A wave sweeping across the plane"></iframe>

*The front enters at t = 0 and sweeps right at c; the large ring ripples as the wave's phase changes across it.*
[Open full screen](../../viewer/index.html?run=../runs/gravWaveAcross/gravWaveAcross.full.json){ target=_blank }
