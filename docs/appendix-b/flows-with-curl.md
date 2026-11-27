# Flows With Curl

[Part 3](../part3/one-potential.md) found that a moving flow with no swirl has one constant for the whole plane,
Bernoulli's: $\partial\phi/\partial t + u^2/2 = \Phi + J$. No value of $J$ suits both the Sun, whose space falls from
rest far away ($J = 0$), and the Earth, whose space it carries. Part 3 chose $J = 0$ and curved space.

The other way out is to let the flow swirl. With curl, Bernoulli's constant can differ from one streamline to the next
(Crocco's theorem, $\nabla B = \mathbf w\times\boldsymbol\omega$), so the Sun's space could have $B = 0$ and the
Earth's $B = J$. The cost is set by Einstein's momentum constraint, which for such a flow is
$\nabla\times\boldsymbol\omega = -16\pi G\rho\,\mathbf w_m/c^2$: outside matter, the vorticity can have no curl of
its own, so it can't be gathered into a layer where $B$ changes unless matter streams through that layer. And anything moving through space also feels $-\mathbf w\times\boldsymbol\omega$:

| Layer where $B$ changes | Vorticity needed | Matter that would have to stream through it | Push on something at 1 km/s |
| --- | --- | --- | --- |
| round the Earth (its Hill sphere) | 2.4 × 10⁻⁵ /s | 10²⁶ × the solar wind | 0.024 m/s², 9 × the Earth's pull on the Moon |
| the gap, 0.63–1 AU from the Sun | 6.3 × 10⁻⁷ /s | 10²³ × the solar wind | 6 × 10⁻⁴ m/s² |

General relativity's own curl, frame dragging, is of order $GMw_m/c^2r^2$: 3 × 10⁻¹² /s round the Earth, ten million
times too small to help.

**Why it is a rabbit hole.** The swirl needed is forbidden by Einstein's equations and would push the Moon off its
orbit. The model keeps its flow free of swirl, which it needs anyway for a single time: a flow defines one time only if
its observers don't swirl (Frobenius's theorem), and free fall keeps a flow that starts with no swirl free of it
(Kelvin's). The one swirl it does have is a spinning body's, small and allowed,
in [Spinning Bodies](../part4/spinning-bodies.md).

*The code: studies/curl_flows.py.*
