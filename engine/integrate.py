"""
integrating a path under newtonian gravity, for the studies and tests that follow space or a test mass through the
bodies' combined g (rather than moving a particle with a calculator)
"""


def rk4Gravity(calc, pos, v, dt):
  """one RK4 step of x'' = g(x), g from calc.gravity; returns the new position and velocity"""
  k1x, k1v = v, calc.gravity(pos)
  k2x, k2v = v + k1v*dt/2, calc.gravity(pos + k1x*dt/2)
  k3x, k3v = v + k2v*dt/2, calc.gravity(pos + k2x*dt/2)
  k4x, k4v = v + k3v*dt, calc.gravity(pos + k3x*dt)
  return pos + (k1x + 2*k2x + 2*k3x + k4x)*dt/6, v + (k1v + 2*k2v + 2*k3v + k4v)*dt/6
