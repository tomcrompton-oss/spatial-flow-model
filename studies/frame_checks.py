"""
the split model's checks with one body much heavier (studies/split_bodies.py and split_checks.py) run with a given
frame rule (engine/split.py's boost), 'static' light: Newton's g, clocks on the Earth and in GPS orbit, light past
Jupiter (both bodies less each alone), radar to a mirror held at the Moon's distance (the same), the whole system
moving together (radar to the Moon), and particles near light's speed (causality)

run: python3 studies/frame_checks.py [boost ...]      (default freefall heavier heavier-only; prints, and writes
     logs/multiBody/frameChecks_<boosts>_<datetime>/summary.log)
"""
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
from engine.logger import LOG_DIR
import engine.split as split
import split_bodies as sb
import split_checks as sc

REAL = split.SplitFlowCalculator


def using(boost):
  """the checks' calculators made with boost and 'static' light, whatever they ask for"""
  class Calc(REAL):
    def __init__(self, bodies=None, light='static', kind=None):
      super().__init__(bodies, 'static', boost)
  sb.SplitFlowCalculator = Calc
  sc.SplitFlowCalculator = Calc
  sc.MODELS = (('static', boost),)


def main():
  boosts = sys.argv[1:] or ['freefall', 'heavier', 'heavier-only']
  folder = os.path.join(LOG_DIR, 'multiBody', 'frameChecks_%s_%s' % ('-'.join(boosts),
                        datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
  os.makedirs(folder, exist_ok=True)
  lines = []
  for boost in boosts:
    using(boost)
    lines.append('=== frames %r' % boost)
    for section in (sb.newton, sb.clocks, lambda: sb.jupiter('static'), lambda: sb.lunar('static'), sc.boost,
                    sc.causal):
      out = section()
      out = out[0] if isinstance(out, tuple) else out
      print('\n'.join(out), flush=True)
      lines += out + ['']
  with open(os.path.join(folder, 'summary.log'), 'w') as f:
    f.write('\n'.join(lines))
  print('written to', folder)


if __name__ == '__main__':
  main()
