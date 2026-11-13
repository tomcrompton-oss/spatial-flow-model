# The model

Space flows through a flat background at a velocity **u**. A particle moves at

$$
\mathbf v = \mathbf w + \mathbf u
$$

where **w** is its velocity relative to the space it is in. As it moves, w changes by the difference between the flow
where space goes and the flow where the particle goes, added relativistically:

$$
\frac{d\mathbf x}{dt} = \mathbf w + \mathbf u(\mathbf x), \qquad \frac{d\mathbf w}{dt} = -(\mathbf w \cdot \nabla)\,\mathbf u
$$

and its proper time runs at $\sqrt{1 - w^2/c^2}$. Light is anything with $|\mathbf w| = c$.

## One hole

Round a body of mass M the flow is the speed of a fall from rest at infinity, straight in:

$$
|\mathbf u| = \sqrt{2GM/r}
$$

That is the Gullstrand–Painlevé form of the Schwarzschild metric, $ds^2 = -c^2dt^2 + |d\mathbf x - \mathbf u\,dt|^2$:
flat space, flowing. The studies compare the model with exact GR:

- **Light** bends as exact GR does, to parts in 10⁷, at distances of 1–1000 AU and impact parameters of 0.025–1 solar
  radii (studies/gr_comparison.py), once its impact parameter is taken as GR defines it.
- **Orbits** precess as exact GR does for the orbit's own apsides, to 1.6 × 10⁻⁴, falling with the step size, at
  65–19,600 Schwarzschild radii.

## A spinning hole

A rotating (Kerr) hole is the river model of Hamilton & Lisle (2008): the river flows straight in and also twists.
In the equatorial plane, light bends as exact Kerr does to 2 × 10⁻⁵ at spins up to 0.99, with and against the spin,
and orbits precess as exact Kerr to 2 × 10⁻⁴ (studies/kerr_comparison.py).

## The step

Each step goes half way the first-order way, then takes the whole step at the middle's rates (second order); light
is kept at exactly c. Close to a hole, within about 10 Schwarzschild radii, the step is effectively first order and
orbits decay; a step on the particle's momentum is the planned fix.
