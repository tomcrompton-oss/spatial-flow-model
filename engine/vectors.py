"""
small helpers for the 2D vectors (numpy arrays of x, y) the engine works with
"""
import math


def length(v):
  """the length of a 2D vector - as np.linalg.norm, at least as accurate, and much quicker for two numbers"""
  return math.hypot(v[0], v[1])
