# How Much Gravity Can Go in the Clocks?

The flow model puts all of gravity into the motion of space: clocks are slowed only by their speed through it, and
space is flat. Conventional post-Newtonian general relativity does the opposite: nothing flows, clocks held still run
slow by the potential, and space is curved. Are there models in between?

Take the one-body flow and move a fraction $\lambda$ of gravity into the clocks, the lapse, and curve space by a
fraction $\kappa$. Run an orbit 200–600 Schwarzschild radii out, and light passing at 300:

| $\lambda$ | $\kappa$ | Precession / GR's | Bending / GR's |
| --- | --- | --- | --- |
| 0 | 0 | 1.0000 | 1.0000 |
| 1 | 0 | 0.667 | 0.500 |
| 0.5 | 0 | 0.834 | 0.750 |
| 0 | 1 | 2.35 | 1.51 |
| 0.25 | 0.25 | 0.9996 | 1.0003 |
| 0.5 | 0.5 | 0.9986 | 1.0002 |
| 0.75 | 0.75 | 0.9968 | 0.9998 |
| 1 | 1 | 0.9945 | 0.9990 |

*(The rows with $\kappa = \lambda$ also have the lapse's $\Phi^2$ term below. The 0.1–0.5% left grows with $\lambda$,
as the next order at 200 Schwarzschild radii should.)*

These are the parametrized post-Newtonian parameters at work. A potential in the clocks alone ($\lambda = 1$,
$\kappa = 0$) has PPN $\gamma = 0$, and light then bends half as much and orbits precess two thirds as much: so they do.
Curving space to match ($\kappa = \lambda$) gives the light back, and the orbits need the lapse's $\Phi^2$ term too.
With it,

$$
N^2 = 1 - \frac{2\lambda\Phi}{c^2} + \frac{2\big(\lambda + 2\kappa(1 - \lambda)\big)\Phi^2}{c^4}
$$

and **$\kappa = \lambda$ is general relativity at first order for any $\lambda$**: a one-parameter family, from the
flow model ($\lambda = 0$, all of gravity in the flow) to conventional post-Newtonian GR ($\lambda = 1$, none). Curved
space alone ($\lambda = 0$, $\kappa = 1$) bends light half as much again as it should.

**Why it is a rabbit hole.** Every member of the family is the same spacetime with its clocks set differently, which is
what [Deriving Curved Space](../part2/deriving-curved-space.md) shows for bodies at rest. The flow model is the end of
the family where clocks falling with space keep the time, and that is the picture the main text follows.

*The code: engine/metric.py (the lapse and curved-space engine), studies/metric_checks.py (shares).*
