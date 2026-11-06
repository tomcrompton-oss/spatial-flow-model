"""
falling and climbing: an object dropped or thrown in, or climbing out, round a black or white hole or the Sun

run: python3 studies/descents.py <study> [--option value ...]   (list: the studies and their defaults)
     e.g. python3 studies/descents.py astroDescendBlack
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


def studyFreefallFromInfinity():
  log = Log('studyFreefallFromInfinity', LOG_TO_FILE, LOG_TO_CSV)
  
  p = Particle()
  config = Config()
  config.dt=0.01
  log.freq = 1000

  dis = AU/100.0  
  p.pos = np.array([-dis, 0.0])

  d = np.linalg.norm(p.pos)
  u = math.sqrt(2*GM/d) * p.pos/d
  
  p.v = -u
  config.durationDays = 100/DAY

  calc = NewtonianCalculator()

  log.print('initial pos', p.pos)
  log.print('initial v', p.v)
  
  calc.hyperbolicSim(p, config, log)

  log.print('final pos', p.pos)
  log.print('final v', p.v)
  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*GM/d) * p.pos/d
  log.print('expected v', u)

def studyEscapeFromSun():
  log = Log('studyEscapeFromSun', LOG_TO_FILE, LOG_TO_CSV)
  
  p = Particle()
  config = Config()
  config.dt=0.01
  log.freq = 100

  dis = 1.49464649e+10  
  p.pos = np.array([-dis, 0])

  d = np.linalg.norm(p.pos)
  u = math.sqrt(2*GM/d) * p.pos/d
  
  p.v = u
  config.durationDays = 11/DAY

  calc = NewtonianCalculator()

  log.print('initial pos', p.pos)
  log.print('initial v', p.v)
  
  calc.hyperbolicSim(p, config, log)

  log.print('final pos', p.pos)
  log.print('final v', p.v)

def astroAscend(m, a, b, dt, freq):
  log = Log('astroAscend', LOG_TO_FILE, LOG_TO_CSV)
  gm = G*m
  log.print("ascend")
  p = Particle()
  p.pos = np.array([0, a])

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*gm/d) * p.pos/d

  
  calc = SpecialFlowCalculator([Body(m)], order=1)
  w = calc.addSI(-u, -u)
  
  calc.initPW(p, w)
  

  config = Config()
  config.dt=dt
  log.freq = freq
  log.pfreq=0


  config.condition = MaxDistance(b)



  log.print('initial pos', p.pos)
  log.print('initial w', p.w)
  log.print('initial u', p.u)
  log.print('initial v', p.v)
    
  calc.hyperbolicSim(p, config, log)

  log.print('final pos', p.pos)
  log.print('final v', p.v)
  log.print('final pt', p.pt)

#astronaut descending
def astroDescend(m, a, b, dt, freq):
  log = Log('astroDescend', LOG_TO_FILE, LOG_TO_CSV)
  gm = G*m
  log.print("descend")
  p = Particle()
  p.pos = np.array([0.0, a])
  ##
  ##d = np.linalg.norm(p.pos)
  ##u = -math.sqrt(2*GM/d) * p.pos/d
  ##
  ### relative motion
  ##p.v = np.array([0.0, 0.81*C]) + u

  d = np.linalg.norm(p.pos)
  u = math.sqrt(2*gm/d) * p.pos/d    #reversed - not used?
  log.print('initial u', np.linalg.norm(math.sqrt(2*gm/d)))   
  calc = SpecialFlowCalculator([Body(m, black=False)], order=1)
  calc.initPAgainstFlow(p)

  config = Config()
  config.dt=dt
  log.freq = freq


  config.condition = MinDistance(b)



  log.print('initial pos', p.pos)
  log.print('initial v', p.v)
  log.print('initial u', p.u)
  log.print('initial w', p.w)
    
  calc.hyperbolicSim(p, config, log)

  log.print('final pos', p.pos)
  log.print('final v', p.v)
  d = np.linalg.norm(p.pos)
  log.print('final d', d)
  log.print('final u', p.u)
  log.print('final w', p.w)
  log.print('final pt', p.pt)
  return d

#astronaut descending into a black hole - astroDescend's twin, freefalling with the flow from rest at infinity
def astroDescendBlack(m, a, b, dt, freq):
  log = Log('astroDescendBlack', LOG_TO_FILE, LOG_TO_CSV)
  gm = G*m
  log.print("descend into a black hole")
  p = Particle()
  p.pos = np.array([0.0, a])

  d = np.linalg.norm(p.pos)
  log.print('initial u', math.sqrt(2*gm/d))
  calc = SpecialFlowCalculator([Body(m)], order=1)
  calc.initPFreefall(p)   #moving with the flow: v = u, w = 0

  config = Config()
  config.dt=dt
  log.freq = freq

  config.condition = MinDistance(b)

  log.print('initial pos', p.pos)
  log.print('initial v', p.v)
  log.print('initial u', p.u)
  log.print('initial w', p.w)

  calc.hyperbolicSim(p, config, log)

  log.print('final pos', p.pos)
  log.print('final v', p.v)
  d = np.linalg.norm(p.pos)
  log.print('final d', d)
  log.print('final u', p.u)
  log.print('final w', p.w)
  log.print('final pt', p.pt)
  #falling from rest at infinity, the time to fall from a to d is (2/3)(a^1.5 - d^1.5)/sqrt(2GM)
  predicted = (2/3)*(a**1.5 - d**1.5)/math.sqrt(2*gm)
  log.print('predicted fall time', predicted, ' sim time', log.t, ' accuracy=', 100-100*abs(log.t-predicted)/predicted, '%')
  return d


#---- notes from earlier runs (calls and results kept from tests.py)
#studyFreefallFromInfinity()
#studyEscapeFromSun()

#astroDescend(0.0)
#astroAscend(0.0)
#Descend(0.0)

#astroDescend(2*AU,AU)
#astroAscend(1*AU, 2*AU)

#section 3.4
#astroDescend(MS, AU, RSUN, 0.001, 1000)
#astroAscend(MS, RSUN, AU, 0.001, 1000)

#astroDescend(AU,700000000)
#astroAscend(4000000*MS, 0.08306561516120865*AU, 1.025*AU, 0.001, 50)


STUDIES = {
  'studyFreefallFromInfinity': (studyFreefallFromInfinity, {}),
  'studyEscapeFromSun': (studyEscapeFromSun, {}),
  'astroAscend': (astroAscend, {'m': 'MS', 'a': 'RSUN', 'b': 'AU', 'dt': '0.001', 'freq': '1000'}),
  'astroDescend': (astroDescend, {'m': '4000000*MS', 'a': '1.025*AU', 'b': '11816508000', 'dt': '0.01', 'freq': '100'}),
  'astroDescendBlack': (astroDescendBlack, {'m': '4000000*MS', 'a': '1.025*AU', 'b': '11816508000', 'dt': '0.01', 'freq': '100'}),
}

if __name__ == '__main__':
  main(STUDIES, __doc__.strip().split('\n')[0])
