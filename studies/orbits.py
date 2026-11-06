"""
orbits: Mercury round the Sun (full size, 1/10 and 1/100,000 scale), precession, and the calculators compared

run: python3 studies/orbits.py <study> [--option value ...]   (list: the studies and their defaults)
     e.g. python3 studies/orbits.py compareSingleBodyOrbits
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


def studyPrecessionOfMercury(calc, per, v, dur, dt):
  log = Log('studyPrecessionOfMercury', LOG_TO_FILE, LOG_TO_CSV)
  particle = Particle()
  particle.pos = np.array([0.0, per])
  particle.v = np.array([v, 0.0])

  config = Config()
  config.dt=dt
  config.durationDays = dur

  calc.orbitalSim(particle, config, log)

def singleBodyOrbit(name, calc, r, v, days, dt, freq, stepFraction=None):
  """
  an orbit around the calculator's bodies, starting at (0, r) moving in +x at speed v, with steps of dt, or adaptive
  steps (stepFraction, at most dt); returns the log so runs can be compared
  """
  log = Log(name, LOG_TO_FILE, LOG_TO_CSV)
  log.print(name)
  p = Particle()
  p.pos = np.array([0.0, r])
  if hasattr(calc, 'initPV'):
    calc.initPV(p, np.array([v, 0.0]))   #flow calculators also need u and w
  else:
    p.v = np.array([v, 0.0])

  config = Config()
  config.dt = dt
  config.stepFraction = stepFraction
  config.durationDays = days
  log.freq = freq

  calc.orbitalSim(p, config, log)
  log.print('final pos', p.pos)
  log.print('final v', p.v)
  log.print('final pt', p.pt)
  return log

def mercuryOrbits(orbits, dt, freq, order=1, stepFraction=None):
  """
  Mercury round the Sun (a black body, flow calculator of the given order) for a number of measured orbits; the
  first orbit counter crossing comes about 3/4 of an orbit in and is the warmup, so the run is orbits + 0.75 periods
  long. steps of dt, or adaptive (stepFraction, at most dt)
  """
  period = 2*math.pi*math.sqrt(((MERCURY_MAX + 46000000000)/2)**3/(G*MS))   #from the semi-major axis (perihelion 46.0e9 m)
  days = (orbits + 0.8)*period/DAY
  return singleBodyOrbit('mercuryOrbits', SpecialFlowCalculator([Body(MS, 0.0, 0.0, black=True)], order=order),
                         MERCURY_MAX, MERCURY_SPEED_AT_MAX, days, dt, freq, stepFraction)

def closeOrbits(scale, orbits, stepsPerOrbit, rowsPerOrbit, order=1, stepFraction=None):
  """
  Mercury's orbit shrunk by scale round one solar mass (a black body, flow calculator): the same shape
  (eccentricity 0.2056), with the speed raised by sqrt(scale) to keep it an orbit. close in, the precession
  per orbit, 6 pi GM / (c^2 a (1 - e^2)), grows as 1/a, so at scale 1e5 (a = 5.8e5 m, about 196 Schwarzschild
  radii - a point mass, well inside the real Sun) it is about 3 degrees an orbit. with stepFraction the steps are
  adaptive, and stepsPerOrbit sets only the longest step
  """
  r, v = MERCURY_MAX/scale, MERCURY_SPEED_AT_MAX*math.sqrt(scale)
  a = (MERCURY_MAX + 46000000000)/2/scale
  period = 2*math.pi*math.sqrt(a**3/(G*MS))
  dt = period/stepsPerOrbit
  freq = dt*round(stepsPerOrbit/rowsPerOrbit) if stepFraction is None else period/rowsPerOrbit   #fixed: whole steps
  days = (orbits + 1.5)*period/DAY   #the precession makes each crossing a little later
  return singleBodyOrbit('closeOrbits', SpecialFlowCalculator([Body(MS, 0.0, 0.0, black=True)], order=order), r, v, days, dt, freq,
                         stepFraction)

def compareSingleBodyOrbits(r, v, days, dt, freq):
  """
  the same orbit around one solar mass three ways:
  flow into a black body, flow out of a white body, and newtonian gravity
  """
  runs = [
    ('orbitBlackFlow', SpecialFlowCalculator([Body(MS, 0.0, 0.0, black=True)], order=1)),
    ('orbitWhiteFlow', SpecialFlowCalculator([Body(MS, 0.0, 0.0, black=False)], order=1)),
    ('orbitNewtonian', NewtonianCalculator([Body(MS, 0.0, 0.0)])),
  ]
  logs = [(name, singleBodyOrbit(name, calc, r, v, days, dt, freq)) for name, calc in runs]

  log = Log('compareSingleBodyOrbits', LOG_TO_FILE)
  log.print()
  log.print('comparison: r =', r/AU, 'AU, v =', v, 'm/s, dt =', dt, 's,', days, 'days')
  columns = [
    ('orbits', lambda l: l.orbit, '%d'),
    ('period (days)', lambda l: l.calcPeriod/DAY, '%.6f'),
    ('periapsis (AU)', lambda l: l.calcPeriapsis/AU, '%.8f'),
    ('apoapsis (AU)', lambda l: l.calcApoapsis/AU, '%.8f'),
    ('eccentricity', lambda l: l.calcEccentricity, '%.8f'),
    ('periapsis precession (rad/orbit)', lambda l: l.calcPPrecession, '%.4e'),
    ('apoapsis precession (rad/orbit)', lambda l: l.calcAPrecession, '%.4e'),
    ('predicted GR precession (rad/orbit)', lambda l: l.predictedPrecession, '%.4e'),
  ]
  log.print('%-38s' % '' + ''.join('%-18s' % name for name, _ in logs))
  for label, value, fmt in columns:
    cells = []
    for _, l in logs:
      try:
        cells.append(fmt % value(l))
      except (AttributeError, ZeroDivisionError):
        cells.append('-')
    log.print('%-38s' % label + ''.join('%-18s' % c for c in cells))


#---- notes from earlier runs (calls and results kept from tests.py)
#section 1.3.2
##studyPrecessionOfMercury(SpecialFlowCalculator([Body(MS)], order=1), MERCURY_MAX/10, MERCURY_SPEED_AT_MAX/math.sqrt(10), 0.4, 0.001)
#studyPrecessionOfMercury(NewExtraSpecialFlowCalculator([Body(MS)]), MERCURY_MAX/10000, MERCURY_SPEED_AT_MAX*math.sqrt(10000), 0.001, 0.000001)
#mercuryOrbits(20, 6, DAY/2)   #about 10 minutes
#closeOrbits(1e5, 20, 50000, 200)   #about 30 seconds; the orbit turns about 3 degrees each time round


STUDIES = {
  'studyPrecessionOfMercury': (studyPrecessionOfMercury, {'calc': 'SpecialFlowCalculator([Body(MS)], order=1)', 'per': 'MERCURY_MAX/10', 'v': 'MERCURY_SPEED_AT_MAX/math.sqrt(10)', 'dur': '0.4', 'dt': '0.001'}),
  'singleBodyOrbit': (singleBodyOrbit, {'name': 'singleBodyOrbit', 'calc': 'SpecialFlowCalculator([Body(MS)])', 'r': 'MERCURY_MAX', 'v': 'MERCURY_SPEED_AT_MAX', 'days': '90', 'dt': '60', 'freq': 'DAY/2', 'stepFraction': 'None'}),
  'mercuryOrbits': (mercuryOrbits, {'orbits': '20', 'dt': '6', 'freq': 'DAY/2', 'order': '1', 'stepFraction': 'None'}),
  'closeOrbits': (closeOrbits, {'scale': '1e5', 'orbits': '20', 'stepsPerOrbit': '50000', 'rowsPerOrbit': '200', 'order': '1', 'stepFraction': 'None'}),
  'compareSingleBodyOrbits': (compareSingleBodyOrbits, {'r': 'MERCURY_MAX/10', 'v': 'MERCURY_SPEED_AT_MAX*math.sqrt(10)', 'days': '12', 'dt': '10', 'freq': 'DAY/100'}),
}

if __name__ == '__main__':
  main(STUDIES, __doc__.strip().split('\n')[0])
