"""
old tests moved out of tests.py: they use calculators that are now in legacy_calculators.py, or that no longer
exist at all (ComplexFlowCalculator, ComplexNewtonianFlowCalculator - from an earlier flow.py), so several will not run
"""
import math
import numpy as np
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
from engine.flow import *
from legacy_calculators import *
from engine.logger import Log
from engine.constants import *

LOG_TO_FILE = True
LOG_TO_CSV = True

def testFreefallToEarth():  
  log = Log('testFreefallToEarth', LOG_TO_FILE, LOG_TO_CSV)
  ME = 5.972E24     #Earth mass
  global GM
  GM = G*ME 

  p = Particle()
  config = Config()
  config.dt=0.01
  log.freq = 100
  
  dis = 6371000
  
  p.pos = np.array([dis, 0])
  p.v = np.array([0.0, 0.0])
  config.durationDays = 11/DAY

  calc = ComplexFlowCalculator()

  calc.hyperbolicSim(p, config, log)

def testCalc():
  ME = 5.972E24     #Earth mass
  global GM
  GM = G*ME
  dis = 6371000.0

  p=Particle()
  p.pos = np.array([0.0, dis])
  p.vel = np.array([0.0, 0.0])

  calc = ComplexNewtonianFlowCalculator()

  for i in range(1):
    calc.move(pos, vel, 10)

  print(' pos:',dis-pos[1])
  print(' vel:',vel[1])

def testOrbitalSim():
  particle = Particle()
  particle.pos = np.array([0.0, MERCURY_MAX/9])
  particle.v = np.array([MERCURY_SPEED_AT_MAX*3, 0.0])

  config = Config()
  config.dt=0.001
  config.durationDays = 20

  calc = ComplexFlowCalculator()
  
  calc.orbitalSim(particle, config)

def testOrbitalSim2():
  log = Log('testOrbitalSim2', LOG_TO_FILE, LOG_TO_CSV)
  particle = Particle()
  particle.pos = np.array([0.0, 0.01*AU])
  particle.v = np.array([243191.0, 0.0])

  config = Config()
  config.dt=0.001
  config.durationDays = 0.9

  calc = NewtonianFlowCalculator()
  
  calc.orbitalSim(particle, config, log)

def testOrbitalSim3():
  log = Log('testOrbitalSim3', LOG_TO_FILE, LOG_TO_CSV)
  particle = Particle()
  particle.pos = np.array([0.0, 0.0001*AU])
  particle.v = np.array([2431909.9, 0.0])

  config = Config()
  config.dt=0.0000001
  config.durationDays = 0.001
  
  calc = ComplexFlowCalculator()
  
  calc.orbitalSim(particle, config, log)

def compareCalculators():
  p = Particle()
  dt= 0.00001
  n = int(10/dt)
  p.pos = np.array([-5*C, 7E8])
  p.v = np.array([C, 0.0])

  print("before:",p.pos, p.v)
  calc = NewtonianCalculator()
  for i in range(n):
    calc.move(p, dt)
    print("i:",i,p.pos, p.v)

  print("after:",p.pos, p.v)

  p.pos = np.array([-5*C, 7E8])
  p.v = np.array([C, 0.0])

  print("before:",p.pos, p.v)
  calc = NewtonianFlowCalculator()
  for i in range(n):
    calc.move(p, dt)
    print("i:",i,p.pos, p.v)

  print("after:",p.pos, p.v)

def testMercury():
  log = Log('testMercury', LOG_TO_FILE, LOG_TO_CSV)
  particle = Particle()
  particle.pos = np.array([0.0, MERCURY_MAX])
  particle.v = np.array([MERCURY_SPEED_AT_MAX, 0.0])

  config = Config()
  config.dt=0.01
  config.durationDays = 350

  calc = ComplexFlowCalculator()
  calc.orbitalSim(particle, config, log)  

#astronaut descending
def fallingApple(m, a, b, dt, freq):
  log = Log('fallingApple', LOG_TO_FILE, LOG_TO_CSV)
  gm = G*m
  log.print("falling apple")
  p = Particle()
  p.pos = np.array([0.0, a])
  ##
  ##d = np.linalg.norm(p.pos)
  ##u = -math.sqrt(2*GM/d) * p.pos/d
  ##
  ### relative motion
  ##p.v = np.array([0.0, 0.81*C]) + u

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*gm/d) * p.pos/d
  log.print('initial u', np.linalg.norm(math.sqrt(2*gm/d)))
  calc = NewNewtonianFlowCalculator([Body(m)])
  calc.initPV(p, np.array([0.0, 0.0])) #initially stationary

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

  d = np.linalg.norm(p.pos)
  log.print('final d', d)
  log.print('distance fell', a-d)
  log.print('final u', p.u)
  log.print('final w', p.w)
  log.print('final v', p.v)
  log.print('final pt', p.pt)
  return d
