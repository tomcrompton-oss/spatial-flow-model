# Deriving Curved Space

[Curved Space](curved-space.md) said that its curved space isn't a guess: that general relativity, with time measured
by clocks falling from rest far away, gives it. This page shows the steps, for bodies held still, to the first order
beyond Newton.

!!! note "Reader's note"
    This page is mathematical, and nothing later depends on following it. The result is the one on the Curved Space
    page: clocks slowed only by their speed through space, space flowing as the potential flow, and space stretched
    across the flow by $u^2/c^2$.

## Three ingredients

Any spacetime in general relativity can be written in a form that matches flowing space:

$$
ds^2 = -N^2c^2\,dt^2 + \gamma_{ij}\,(dx^i - u^i\,dt)(dx^j - u^j\,dt)
$$

- $N$, the **lapse**: how fast clocks moving with the space tick, per unit of $t$.
- $u^i$, the **flow**: how fast those clocks move through the coordinates. (General relativity calls $-u^i$ the
  shift.)
- $\gamma_{ij}$, the **metric of space**: the rule that turns small steps in the coordinates into lengths, at one
  moment.

$\delta_{ij}$ is the metric of flat space, Pythagoras' rule: 1 when $i = j$, 0 otherwise, the same in every direction.
Repeated indices are summed. The flow model of Part 1 is $N = 1$, every clock slowed only by its speed through space,
and $\gamma_{ij} = \delta_{ij}$, space flat.

## General relativity for bodies at rest

For bodies held still, general relativity's spacetime, to the first order beyond Newton (first post-Newtonian
order), is

$$
ds^2 = -\left(1 - \frac{2\Phi}{c^2} + \frac{2\Phi^2}{c^4}\right)c^2\,dt^2 + \left(1 + \frac{2\Phi}{c^2}\right)\delta_{ij}\,dx^i\,dx^j,
\qquad \Phi = \sum_k \frac{GM_k}{d_k}
$$

Its clocks are held still, and slowed by the potential; there is no flow; and space is curved, stretched equally in
every direction by $2\Phi/c^2$.

## Changing the clocks

Now measure time by clocks falling from rest far away instead, as the flow model does. Their time is the old time plus
a function of place, $T = t + S(\mathbf x)/c^2$, so $dt = dT - \partial_i S\,dx^i/c^2$. Putting this in and keeping
terms to the same order:

$$
ds^2 = -\left(1 - \frac{2\Phi}{c^2} + \frac{2\Phi^2}{c^4}\right)c^2\,dT^2
     + 2\left(1 - \frac{2\Phi}{c^2}\right)\partial_i S\,dx^i\,dT
     + \left[\left(1 + \frac{2\Phi}{c^2}\right)\delta_{ij} - \frac{\partial_i S\,\partial_j S}{c^2}\right]dx^i\,dx^j
$$

Each kind of term has to match the flowing-space form above.

- **The $dx\,dT$ term** gives the flow: $\mathbf u = -\nabla S$, to leading order. The flow is the slope of a single
  function, so it has no swirl: a potential flow.
- **The $dT^2$ term** gives the lapse. For it to be exactly 1, clocks falling with space must keep the time $T$, which
  needs $|\nabla S|^2 = 2\Phi$: the flow's speed is the escape speed from all the bodies together. That is the
  potential flow's equation, the eikonal equation. At the next order, the $\Phi^2$ term makes the flow very slightly
  slower: $u^2 = 2\Phi(1 - \Phi/c^2)$.
- **The $dx\,dx$ term** gives the metric of space:

$$
\gamma_{ij} = \left(1 + \frac{2\Phi}{c^2}\right)\delta_{ij} - \frac{u_i u_j}{c^2}
= \delta_{ij} + \frac{u^2\,\delta_{ij} - u_i u_j}{c^2}
$$

using $u^2 = 2\Phi$. Across the flow, the second term is $u^2/c^2$: space is stretched by that. Along the flow,
$u^2 - u^2 = 0$: lengths are as in flat space.

So general relativity for bodies at rest, with time kept by clocks falling from rest far away, is exactly the
potential flow with clocks slowed only by their speed through space, and space stretched across the flow by
$u^2/c^2$. Nothing is chosen: the flow fixes everything.

## One body: flat after all

Round a single body the flow is straight in, so the stretch is across the radial direction only. Space is then

$$
dr^2 + \left(1 + \frac{r_s}{r}\right)r^2\,d\Omega^2
$$

where $d\Omega$ is the angle round the body. Measure distance from the body by the circumference instead,
$R = r\sqrt{1 + r_s/r}$. Then $dR/dr = 1$ to this order, and space is $dR^2 + R^2\,d\Omega^2$: flat, in the
coordinate $R$. That is why Part 1, which used flat space, is unchanged. With two or more bodies, no relabelling makes
the stretch go away: there, it is a real curvature, and it carries the bodies' effects on each other.

*The first post-Newtonian metric of bodies at rest is the standard one: see, for example, C. M. Will, Theory and
Experiment in Gravitational Physics.*
