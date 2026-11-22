"""
light: deflection past the Sun, light climbing out of and falling into a black hole, and its speed

run: python3 studies/light.py <study> [--option value ...]   (list: the studies and their defaults)
     e.g. python3 studies/light.py lightPastSun
"""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
import numpy as np
from engine.flow import *
from engine.logger import Log
from engine.constants import *
from engine.exact import grDeflectionExact, impactParameter
from studies.cli import main

LOG_TO_FILE = True #write each study's output to logs/<folder>/<study>_<datetime>.log
LOG_TO_CSV = True #write each study's positions to logs/<folder>/<study>_<datetime>.csv


def studyDeflectionOfLight(calc, dis, b, dt, name='studyDeflectionOfLight', freq=100, stepFraction=None):
  """
  light from x = -dis to x = +dis at height b above the body at the origin, with steps of dt or adaptive steps
  (stepFraction, at most dt); returns the log and the particle so runs can be compared
  """
  log = Log(name, LOG_TO_FILE, LOG_TO_CSV)
  config = Config()
  config.condition = Duration(2*dis/C)
  config.dt = dt
  config.stepFraction = stepFraction

  particle = Particle()
  particle.pos = np.array([-dis, b])
  calc.initPW(particle, np.array([C, 0.0]))
  log.impactParameter = impactParameter(particle.pos, particle.w, particle.u)   #GR's b, a little under the b set here
  #particle.v = np.array([C, 0.0])

  log.freq = freq

  log.print('initial pos', particle.pos)
  log.print('initial w', particle.w)
  log.print('initial u', particle.u)
  log.print('initial v', particle.v)

  calc.hyperbolicSim(particle, config, log)
  return log, particle

def lightPastSun(dis, fractions, dt, freq, order=1, stepFraction=None):
  """
  light passing a black solar mass, from dis out on one side to dis out on the other,
  passing at b = each fraction of the sun's radius (the sun is a point mass, so b < RSUN is allowed)
  compares the measured bend with the general relativity prediction 4GM/(c^2 b), and with GR's exact bending at the
  light's own impact parameter cL/E (engine/exact.py: starting where the flow is u, it is b/(1 + u/c), so the bend is
  u/c more than 4GM/c^2 b). the calculator is of the given order, with steps of dt or adaptive steps (stepFraction, at
  most dt)
  """
  runs = []
  for fraction in fractions:
    b = RSUN*fraction
    name = 'lightPastSun_%gpct' % (fraction*100)
    calc = SpecialFlowCalculator([Body(MS, 0.0, 0.0, black=True)], order=order)
    log, p = studyDeflectionOfLight(calc, dis, b, dt, name, freq, stepFraction)
    runs.append((fraction, b, log, p))

  log = Log('lightPastSun', LOG_TO_FILE)
  log.print()
  log.print('light past the sun: from', dis/AU, 'AU to', dis/AU, 'AU, dt =', dt, 's', ', step fraction %g' % stepFraction if stepFraction else '', ', order', order)
  #bend from w (light relative to space); v also carries the flow at the end point, which leans towards the sun
  log.print('%-10s %-16s %-18s %-16s %-16s %-20s %-9s %-9s %-16s' % ('b/RSUN', 'b (m)', 'closest (m)', 'bend w (rad)', 'bend v (rad)', 'predicted 4GM/c2b', 'w ratio', 'v ratio', 'w / exact GR - 1'))
  for fraction, b, l, p in runs:
    bendW = math.atan2(-p.w[1], p.w[0])   #towards the sun is -y
    bendV = math.atan2(-p.v[1], p.v[0])
    predicted = 4*G*MS/(C**2*b)
    exact = grDeflectionExact(l.impactParameter)   #at GR's impact parameter of the light as it starts
    log.print('%-10s %-16.6e %-18.6e %-16.6e %-16.6e %-20.6e %-9.5f %-9.5f %-16.3e' % ('%g%%' % (fraction*100), b, l.min, bendW, bendV, predicted, bendW/predicted, bendV/predicted, bendW/exact - 1))
  log.print('(%g rad = %.4f arcsec at the edge)' % (4*G*MS/(C**2*RSUN), 4*G*MS/(C**2*RSUN)*180/math.pi*3600))

def lightAscend(m, a, b, dt, freq):
  log = Log('lightAscend', LOG_TO_FILE, LOG_TO_CSV)
  gm = G*m
  log.print("light ascend")
  p = Particle()
  p.pos = np.array([0, a])

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*gm/d) * p.pos/d


  #calculate relative motion
  calc = SpecialFlowCalculator([Body(m)], order=1)
  calc.initPW(p, np.array([0, C]))
  

  config = Config()
  config.dt=dt
  log.freq=freq


  config.condition = MaxDistance(b)

  log.print('initial pos', p.pos)
  log.print('initial w', p.w)
  log.print('initial u', p.u)
  log.print('initial v', p.v)
    
  calc.hyperbolicSim(p, config, log)

  log.print('final pos', p.pos)
  log.print('final v', p.v)
  log.print('final pt', p.pt)

  return np.linalg.norm(p.pos)

def lightDescend(m, a, b, dt, freq):
  log = Log('lightDescend', LOG_TO_FILE, LOG_TO_CSV)
  gm = G*m
  log.print("light descend")
  p = Particle()
  p.pos = np.array([0, a])

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*gm/d) * p.pos/d 

  #calculate relative motion
  calc = SpecialFlowCalculator([Body(m)], order=1)
  calc.initPW(p, np.array([0, -C]))
  

  config = Config()
  config.dt=dt
  log.freq = freq


  config.condition = MinDistance(b)


  log.print('initial pos', p.pos)
  log.print('initial w', p.w)
  log.print('initial u', p.u)
  log.print('initial v', p.v)
    
  calc.hyperbolicSim(p, config, log)

  log.print('final pos', p.pos)
  log.print('final v', p.v)
  log.print('final pt', p.pt)

  return np.linalg.norm(p.pos)

def speedOfLight(a, b, d0):
  log = Log('speedOfLight', LOG_TO_FILE, LOG_TO_CSV)
  m = MS
  gm = G*m

  log.print("speed of light", a, b, d0)
  p = Particle()
  x = math.sqrt(a**2 - d0**2)
  p.pos = np.array([d0, x])

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*gm/d) * p.pos/d

  
  calc = SpecialFlowCalculator([Body(m)], order=1)

  calc.initPW(p, np.array([0, -C]))

  start = p.pos.copy()

  config = Config()
  config.dt=0.001
  log.freq = 1000
 
  config.condition = MaxDistanceAndBelow(b)


  log.print('initial pos', p.pos)
  log.print('initial w', p.w)
  log.print('initial u', p.u)
  log.print('initial v', p.v)
    
  calc.hyperbolicSim(p, config, log)

  log.print('final pos', p.pos)
  log.print('final v', p.v)
  log.print('final pt', p.pt)

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*gm/d) * p.pos/d
  log.print('initial u', 0.1*u) 

  #straight line time
  st = np.linalg.norm(p.pos-start)/C
  log.print('staright time', st)

  #time to sun
  inward = np.array([d0, 0]) - start
  inwardD = np.linalg.norm(inward)
  outward = p.pos - np.array([d0, 0])
  outwardD = np.linalg.norm(outward)
  total = inwardD+outwardD
  time = total/C

  log.print(log.t, p.t)
  log.print('inward:',inwardD/AU,'outward:',outwardD/AU,'total:',total/AU, 'time:', time)
  log.print('dt (a):',log.t - time)
  log.print('particle d:',p.d/AU,'time:', p.d/C)
  log.print('dt: (b)',log.t - p.d/C)

  log.print('delta from straight', log.t-st)

  #calc value
  R = (p.pos - start)/np.linalg.norm(p.pos-start)
  x = p.pos/np.linalg.norm(p.pos)
  delta = -(2*gm/C**3)*math.log(1-np.dot(R,x))
  log.print("delta", delta)

  #different formula
  #delta2 = (4*MS/C)*math.log(4*AU*0.72*AU/d0**2)
  #print("delta2", delta2)
  return delta

def speedOfLightLowOutput(a, b, d0):
  log = Log('speedOfLightLowOutput', LOG_TO_FILE, LOG_TO_CSV)
  m = MS
  gm = G*m

  log.print("speed of light ", a, b, d0)
  p = Particle()
  p.pos = np.array([d0, a])

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*gm/d) * p.pos/d

  
  calc = SpecialFlowCalculator([Body(m)], order=1)

  calc.initPW(p, np.array([0, -C]))

  start = p.pos.copy()

  config = Config()
  config.dt=0.0001
  log.freq = 1000000
 
  config.condition = MaxDistanceAndBelow(b)
    
  calc.hyperbolicSim(p, config, log)

  d = np.linalg.norm(p.pos)
  u = -math.sqrt(2*gm/d) * p.pos/d

  #straight line time
  st = np.linalg.norm(p.pos-start)/C

  #time to sun
  inward = np.array([d0, 0]) - start
  inwardD = np.linalg.norm(inward)
  outward = p.pos - np.array([d0, 0])
  outwardD = np.linalg.norm(outward)
  total = inwardD+outwardD
  time = total/C

  log.print('**********', d0)
  log.print('******    sim delta:',log.t - p.d/C)

  #calc value
  R = (p.pos - start)/np.linalg.norm(p.pos-start)
  x = p.pos/np.linalg.norm(p.pos)
  delta = -(2*gm/C**3)*math.log(1-np.dot(R,x))
  log.print("******       delta:", delta)


#---- notes from earlier runs (calls and results kept from tests.py)
#(SpecialFlowCalculator here meant the class later kept as OldSpecialFlowCalculator in legacy/, removed after af11f8d)
#section 1.3.1
##studyDeflectionOfLight(NewtonianCalculator(), AU, 7.0E8, 0.001)
##studyDeflectionOfLight(SpecialCalculator(), AU, 7.0E8, 0.001)
##studyDeflectionOfLight(NewtonianFlowCalculator(), AU, 7.0E8, 0.001)
##studyDeflectionOfLight(SpecialFlowCalculator(), AU, 7.0E8, 0.001)

##studyDeflectionOfLight(SpecialFlowCalculator(), AU, 7.0E8, 0.001)
##studyDeflectionOfLight(SpecialFlowCalculator(), AU, 7.0E7, 0.001)
##studyDeflectionOfLight(SpecialFlowCalculator(), AU, 7.0E6, 0.001)
##studyDeflectionOfLight(SpecialFlowCalculator([Body(MS)]), AU, 7.0E5, 0.001)
##studyDeflectionOfLight(SpecialFlowCalculator(), AU, 7.0E5, 0.0001)
##studyDeflectionOfLight(SpecialFlowCalculator(), AU, 7.0E4, 0.00001)

##studyDeflectionOfLight(SpecialFlowCalculator(), AU, 7.0E8, 0.001)
##studyDeflectionOfLight(ExtraSpecialFlowCalculator(), AU, 7.0E8, 0.001)

#light escaping
#lightAscend(0.0)

#speedOfLight(2000000000, AU)
#speedOfLight(AU, 2000000000)
#x = lightDescend(0.1*AU, 10000)
#print('')
#print(x)
#print('')

#lightAscend(AU, 2*AU)
#lightDescend(2*AU, AU)

#studyDeflectionOfLight(NewExtraSpecialFlowCalculator([Body(MS)]), 10*AU, 7.0E8, 0.001)
#print('************************')
#studyDeflectionOfLight(WhiteFlowCalculator([Body(MS, black=False)]), 10*AU, 7.0E8, 0.001)

#studyDeflectionOfLight(NewExtraSpecialFlowCalculator([Body(MS)]), AU, 7.0E8, 0.001)

######### shapiro effect
##resultsA = []
##resultsB = []
##
##for i in range(30):
##  d0 = 700000000 + i*700000000
##  print(d0)
##  resultsA.append(speedOfLight(AU, 0.72*AU, d0))
##  resultsB.append(speedOfLight(0.72*AU, AU, d0))
##
##print("results A:")
##for i in resultsA:
##  print(i)
##
##print("results B:")
##for i in resultsB:
##  print(i)
########## end of shapiro effect

##speedOfLight(AU, 0.72*AU, 7000000000)
##speedOfLight(0.72*AU, AU, 7000000000)
#escaping light every 200 seconds (pt)

#199.99999999996308 , 199.99999999996308 , 132232515821.99324 , 0.0 , 132232515821.99324 , 0.0 , -89618179.30715446
## 1.025
## 0.969
## 0.910
## 0.850
## 0.788
## 0.723
## 0.655
## 0.584
## 0.508
## 0.425
## 0.334
## 0.227
## 0.083

##0.0002516224892300668 0.01 0.0830661068210658
##100.00278650502965 443.9699999997412 0.2272784385573931
##200.0018549663045 623.469999999578 0.33362241504370155
##300.00002983825914 776.2099999994391 0.42493366431396506
##400.00496218137266 917.009999999311 0.5072456463718883
##500.00592670825716 1050.8299999991893 0.5833002834668952
##600.0078445900668 1180.0099999990719 0.654649777741498
##700.0043151914201 1305.8399999989574 0.7222700317288198
##800.0004833699243 1429.1299999988453 0.7868349460523493
##900.0006125161622 1550.419999998735 0.8488308407548777
##1000.0000138946109 1670.0799999986261 0.9086183199372828
##1100.0028577561084 1788.3899999985185 0.9664818941738774
##1200.0024073114973 1905.549999998412 1.022642072754497
##
#lightAscend(4000000*MS, 0.966*AU, 1.130*AU, 0.001, 50)

#399.9999999997812 , 399.9999999997812 , 113639115757.59775 , 0.0 , 113639115757.59775 , 0.0 , -96672138.10190354
#lightAscend(4000000*MS, 113639115757.59775, AU, 0.01, 10)
#599.9999999995994 , 599.9999999995994 , 93372285416.68437 , 0.0 , 93372285416.68437 , 0.0 , -106648868.57635167
#lightAscend(4000000*MS, 93372285416.68437, AU, 0.01, 10)
#799.9999999994175 , 799.9999999994175 , 70590551709.28233 , 0.0 , 70590551709.28233 , 0.0 , -122656892.81271298
#lightAscend(4000000*MS, 70590551709.28233, AU, 0.01, 10)
#999.9999999992356 , 999.9999999992356 , 43198908307.83655 , 0.0 , 43198908307.83655 , 0.0 , -156793791.10084757
#lightAscend(4000000*MS, 43198908307.83655, AU, 0.01, 10)

#lightAscend(4000000*MS, 0.079*AU, AU, 0.01, 10)

#2102.999999999483 , 975.421833862824 , 132692754875.6488 , 0.0 , 132692754875.6488 , 0.0 , 73478617.16786544
#lightAscend(4000000*MS, 132692754875.6488, AU, 0.01, 10)
#1860.9999999984525 , 775.0031065192817 , 114482413563.1563 , 0.0 , 114482413563.1563 , 0.0 , 77107669.01340358
#lightAscend(4000000*MS, 114482413563.1563, AU, 0.01, 10)
#1610.9999999986799 , 575.1621789494847 , 94677941427.6674 , 0.0 , 94677941427.6674 , 0.0 , 81421643.25115967
#lightAscend(4000000*MS, 94677941427.6674, AU, 0.01, 10)
#1345.9999999989209 , 375.3821614388468 , 72443959582.24318 , 0.0 , 72443959582.24318 , 0.0 , 86382581.77811752
#lightAscend(4000000*MS, 72443959582.24318, AU, 0.01, 10)
#1044.9999999991946 , 175.10943014141287 , 45803605085.5435 , 0.0 , 45803605085.5435 , 0.0 , 89424654.20725265
#t=2455
#lightAscend(4000000*MS, 45803605085.5435, AU, 0.01, 10)

#lightDescend(4000000*MS, AU, 0.1*AU, 0.001, 1000)
#lightAscend(4000000*MS, 0.1*AU, AU, 0.001, 1000)


STUDIES = {
  'studyDeflectionOfLight': (studyDeflectionOfLight, {'calc': 'SpecialFlowCalculator([Body(MS)], order=1)', 'dis': 'AU', 'b': '7.0E8', 'dt': '0.001', 'name': 'studyDeflectionOfLight', 'freq': '100', 'stepFraction': 'None'}),
  'lightPastSun': (lightPastSun, {'dis': '10*AU', 'fractions': '[0.2, 0.1, 0.05, 0.025]', 'dt': '0.0001', 'freq': '1', 'order': '1', 'stepFraction': 'None'}),
  'lightAscend': (lightAscend, {'m': '4000000*MS', 'a': '0.1*AU', 'b': 'AU', 'dt': '0.001', 'freq': '1000'}),
  'lightDescend': (lightDescend, {'m': '4000000*MS', 'a': 'AU', 'b': '0.1*AU', 'dt': '0.001', 'freq': '1000'}),
  'speedOfLight': (speedOfLight, {'a': 'AU', 'b': '0.72*AU', 'd0': '7000000000'}),
  'speedOfLightLowOutput': (speedOfLightLowOutput, {'a': 'AU', 'b': '0.72*AU', 'd0': '7000000000'}),
}

if __name__ == '__main__':
  main(STUDIES, __doc__.strip().split('\n')[0])
