"""
two bodies: an orbit round a pair of black holes

run: python3 studies/two_bodies.py <study> [--option value ...]   (list: the studies and their defaults)
     e.g. python3 studies/two_bodies.py twoBlackBodies
"""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import *
from engine.logger import Log
from engine.constants import *
from studies.cli import main

LOG_TO_FILE = True #write each study's output to logs/<folder>/<study>_<datetime>.log
LOG_TO_CSV = True #write each study's positions to logs/<folder>/<study>_<datetime>.csv


def twoBlackBodies(r, dt, freq, days):
  """
  a particle orbiting two black solar masses 1 AU apart, at x = -0.5 AU and x = +0.5 AU
  it starts at (0, r) moving in +x at the circular speed for the combined mass
  """
  log = Log('twoBlackBodies', LOG_TO_FILE, LOG_TO_CSV)
  log.print("two black bodies")
  bodies = [Body(MS, -AU/2, 0.0, black=True), Body(MS, AU/2, 0.0, black=True)]
  calc = SpecialFlowCalculator(bodies, order=1)

  p = Particle()
  p.pos = np.array([0.0, r])
  calc.initPV(p, np.array([math.sqrt(G*2*MS/r), 0.0]))

  config = Config()
  config.dt = dt
  config.condition = Duration(days*DAY)
  log.freq = freq

  log.print('initial pos', p.pos)
  log.print('initial v', p.v)
  log.print('initial u', p.u)
  log.print('initial w', p.w)

  calc.hyperbolicSim(p, config, log)

  log.print('final pos', p.pos)
  log.print('final v', p.v)
  log.print('final d', np.linalg.norm(p.pos))
  log.print('final pt', p.pt)


STUDIES = {
  'twoBlackBodies': (twoBlackBodies, {'r': '1.5*AU', 'dt': '1000', 'freq': 'DAY', 'days': '480'}),
}

if __name__ == '__main__':
  main(STUDIES, __doc__.strip().split('\n')[0])
