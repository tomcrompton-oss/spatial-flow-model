import numpy as np
from flow_original import *
from constants import *

#constants
GM = G*MS#*4300000          #Convenience          

def freefallDescend(start, end):
  print("light descend")
  p = Particle()
  p.pos = np.array([0, start])

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*GM/d) * p.pos/d


  w = u

  #calculate relative motion
  p.v = w + u
  

  config = Config()
  config.dt=0.1
  log = Log()
  log.freq = 10000


  config.condition = MinDistance(end)

  calc = SpecialFlowCalculator(MS*1000)

  print('initial pos', p.pos)
  print('initial w', w)
  print('initial u', u)
  print('initial v', p.v)
    
  calc.hyperbolicSim(p, config, log)

  print('final pos', p.pos)
  print('final v', p.v)
  print('final pt', p.pt)

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*GM/d) * p.pos/d
  print('initial u', u)  



def lightDescend(start, end):
  print("light descend")
  p = Particle()
  p.pos = np.array([0, start])

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*GM/d) * p.pos/d


  w = np.array([0, -C])

  #calculate relative motion
  p.v = w + u
  

  config = Config()
  config.dt=0.09
  log = Log()
  log.freq = 10


  config.condition = MinDistance(end)

  calc = SpecialFlowCalculator()

  print('initial pos', p.pos)
  print('initial w', w)
  print('initial u', u)
  print('initial v', p.v)
    
  calc.hyperbolicSim(p, config, log)

  print('final pos', p.pos)
  print('final v', p.v)
  print('final pt', p.pt)

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*GM/d) * p.pos/d
  print('initial u', u)  

#astroDescend(0.0)
#astroAscend(0.0)
#lightAscend(0.0)
freefallDescend(AU, 0.01*AU)

#print(2*GM/C**2)

