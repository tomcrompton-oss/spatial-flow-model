import math
import numpy as np
import time
from constants import *

#constants
APOAPSIS_MERCURY = 70000000000 #apoapsis of Mercury
SPEED_MERCURY = 38860 #initial speed of Mercury
APOAPSIS_CLOSE = APOAPSIS_MERCURY/9
SPEED_CLOSE = SPEED_MERCURY*3

class Scenario:
  initialPosition = np.array([0][0])
  initialVelocity = np.array([0][0])

class Config:
  dt = 0.0
  duration = 1

class Log:
  orbits=0
  period = []
  periapsis = []
  apoapsis = []
  semiMajorAxis = []
  eccentricity = []
  apoapsisAngle = []
  apoapsisPrecession = []
  periapsisAngle = []
  periapsisPrecession = []

  #predicted
  predictedPeriod = 0.0
  predictedPrecession = 0.0

  #calculated
  calcPeriod = 0.0
  calcSMA = 0.0
  calcAPrecession = 0.0
  calcPPrecession = 0.0

  def recordOrbit(this, orbit, period, min, max, sma, e, minP, maxP):
    this.orbits=orbit
    this.period.append(period)
    this.periapsis.append(min)
    this.apoapsis.append(max)
    this.semiMajorAxis.append(sma)
    this.eccentricity.append(e)
    this.periapsisAngle.append(minP)
    if(len(this.periapsisAngle)>1):
      this.periapsisPrecession.append(this.periapsisAngle[orbit-1]-this.periapsisAngle[orbit-2])
    this.apoapsisAngle.append(maxP)
    if(len(this.apoapsisAngle)>1):
      this.apoapsisPrecession.append(this.apoapsisAngle[orbit-1]-this.apoapsisAngle[orbit-2])
    

  def finish(this):
    print()
    print('Simulation complete')
    print()
    
    this.calcPeriod = sum(this.period)/this.orbits
    this.calcPeriapsis = sum(this.periapsis)/this.orbits
    this.calcApoapsis = sum(this.apoapsis)/this.orbits
    this.calcSMA = (this.calcPeriapsis + this.calcApoapsis) / 2
    this.predictedPeriod = 2*math.pi*math.sqrt(this.calcSMA**3/GM)
    this.calcEccentricity = sum(this.eccentricity)/this.orbits

    print('orbits:',this.orbits,' average period',this.calcPeriod/DAY,' days          predicted period:',this.predictedPeriod/(24*60*60),' days')
    print()
    print('calculated')
    print('  Periapsis:\t',this.calcPeriapsis,"\t","{:0.2}".format(this.calcPeriapsis/AU),'AU')
    print('  Apoapsis:\t',this.calcApoapsis,"\t","{:0.2}".format(this.calcApoapsis/AU),'AU')
    print('  semi-major:\t', this.calcSMA,"\t","{:0.2}".format(this.calcSMA/AU),'AU')
    print('  eccentricity:\t', this.calcEccentricity)

    print()
    this.predictedPrecession = (24*math.pi**3)*(this.calcSMA**2)/(this.calcPeriod**2 * C**2 * (1-this.calcEccentricity**2)) 
    print('predicted precession: ',this.predictedPrecession)

    this.calcPPrecession = sum(this.periapsisPrecession)/(this.orbits-1)
    print('calc periapsis precision:', this.calcPPrecession,'   accuracy=', 1-this.calcPPrecession/this.predictedPrecession)

    this.calcAPrecession = sum(this.apoapsisPrecession)/(this.orbits-1)
    print('calc apoapsis precision:', this.calcAPrecession,'   accuracy=', 1-this.calcAPrecession/this.predictedPrecession)
    
class LightLog:
  def recordPosition(this, n, d, pos, v):
    if(n%100000==0):
      print(n,',',d,',',pos[0],',',pos[1],',',v[0],',',v[1])
    
  def finish(this):
    print('finish')
  

def add(u, v):
   """
   relativistic addition of two velocities
   Args:
     u (float): the first velocity as a fraction of c
     v (float): the second velocity as a fraction of c
   Returns:
     w (float): the sum of the two velocities as a fraction of c
   """
   upar = v * np.dot(u,v) / np.dot(v, v)
   uper = u-upar

   #print('u ',u)
   #print('v ',v)
   
   #print('upar ',upar)
   #print('uper ',uper)

   wpar = (upar+v) / (1+np.dot(v, upar))
   L = math.sqrt(1-np.linalg.norm(v)**2)
   #print('lagrangian', L)
   wper =  (L * uper)/ (1+np.dot(v, upar))
   
   w = wpar + wper
   #print('wpar',wpar)
   #print('wper',wper)
   #print('w',w)
   #print('mag w', np.linalg.norm(w))
   return w

def addSI(u, v):
   """
   relativistic addition of two velocities
   Args:
     u (float): the first velocity in m/s
     v (float): the second velocity in m/s
   Returns:
     w (float): the sum of the two velocities in m/s
   """
   return add(u/C, v/C)*C

#simulation
#TODO parameterise
def orbitalSim(scenario, config):
  """
  run a simulation
  """
  pos = scenario.initialPosition.copy()
  v = scenario.initialVelocity.copy()

  dt=config.dt
  maxn=int((config.durationDays*DAY)/dt)

  b = abs(pos[0])  #???

  u = np.array([0.0, 0.0])
  u2 = np.array([0.0, 0.0])
  du = np.array([0.0, 0.0])
  a = np.array([0.0, 0.0])
  
  orbit=0
  period=0
  max=0
  min=np.linalg.norm(scenario.initialPosition)

  log = Log()
  t=0
  starttime=time.time()
  print('Starting estimated duration:',"{:.2f}".format(maxn/N_PER_SECOND),'seconds (',"{:.2}".format(maxn/N_PER_HOUR),') hours')
  for n in range(0, maxn, 1):
    t=t+dt
    period=period+dt
    oldpos = pos.copy()
    d = np.linalg.norm(pos)
    #print(d)

    u2 = u.copy()
    #print('u2 ',u2[0],' ',u2[1])

    u[0] = -math.sqrt(2*GM/d) * pos[0]/d
    u[1] = -math.sqrt(2*GM/d) * pos[1]/d

    #print("ev",math.sqrt(u[0]**2+u[1]**2)," ",-math.sqrt(2*GM/d))
    du = u-u2
    v = addSI(v, -du)
    

    #print('du',du)
    #print('v',v)
    
    pos = pos + v*dt
    pos = pos + u*dt

    #print('pos',pos)
    d = np.linalg.norm(pos)
    if(d>max):
      maxpos = pos.copy()
      max=d
    if(d<min):
      minpos = pos.copy()
      min=d
    #g = GM/d**2
    g = GM/d**2 
    #print('g=',g,'d=',d)
    a = -g * pos/d
    v = addSI(v,a * dt)
    speed = np.linalg.norm(v)
    #print(a,' ',v)
    #print(t,' ',d,' ',pos,' ',v)
    if(oldpos[0]<0 and pos[0]>=0):
       #orbit completed
      orbit=orbit+1
      #print(orbit,','maxpos[0],',',maxpos[1],',',max,',',math.asin(maxpos[0]/max),math.acos(maxpos[1]/max),',',min,',',min+max)
      print(orbit,',',n,',',time.time()-starttime,',',math.acos(maxpos[1]/max),',',math.pi-math.acos(minpos[1]/min))

      #calculate values
      sma=(min+max)/2
      e=1-2/(max/min+1)
      minP = math.pi-math.acos(minpos[1]/min)
      maxP = math.acos(maxpos[1]/max)

      print(minP, maxP)

      log.recordOrbit(orbit, period, min, max, sma, e, minP, maxP)

      #reset counters
      period=0
      max=0
      min=np.linalg.norm(scenario.initialPosition)



  log.finish()

#simulation
def lightSim(scenario, config):
  """
  run an light simulation
  """
  pos = scenario.initialPosition.copy()
  min = np.linalg.norm(pos)
  v = scenario.initialVelocity.copy()

  dt=config.dt
  maxn=int((config.durationMinutes*60)/dt)

  u = np.array([0.0, 0.0])
  u2 = np.array([0.0, 0.0])
  du = np.array([0.0, 0.0])
  a = np.array([0.0, 0.0])

  maxv=1.0
  
  log = LightLog()
  t=0
  starttime=time.time()
  print('Starting estimated duration:',"{:.2f}".format(maxn/N_PER_SECOND),'seconds (',"{:.2}".format(maxn/N_PER_HOUR),') hours')
  for n in range(0, maxn, 1):
    t=t+dt
    oldpos = pos.copy()
    d = np.linalg.norm(pos)
    #print(d)

    u2 = u.copy()
    #print('u2 ',u2[0],' ',u2[1])

    u[0] = -math.sqrt(2*GM/d) * pos[0]/d
    u[1] = -math.sqrt(2*GM/d) * pos[1]/d

    #print("ev",math.sqrt(u[0]**2+u[1]**2)," ",-math.sqrt(2*GM/d))
    du = u-u2
    v = addSI(v, -du)
    

    #print('du',du)
    #print('v',v)
    
    pos = pos + v*dt
    pos = pos + u*dt
    #print('u:',np.linalg.norm(u)/C,'v:',np.linalg.norm(v)/C)
    if(np.linalg.norm(v)/C > maxv):
      maxv = np.linalg.norm(v)/C 
    d = np.linalg.norm(pos)
    if(d<min):
      min=d

    #print('pos',pos)

    #g = GM/d**2
    g = GM/d**2 
    #print('g=',g,'d=',d)
    a = -g * pos/d
    v = addSI(v,a * dt)
    #print('v:',v)
    v[0]=C*v[0]/np.linalg.norm(v)
    v[1]=C*v[1]/np.linalg.norm(v)
    speed = np.linalg.norm(v)
    #print('v2:',v)
    log.recordPosition(n,d,pos,v)
  log.finish()
  print('max v:',maxv)
  print('closest distance:',min,' ',min/AU,'AU')
  print('Angle:',4*GM/(C**2*min))
  print('vx:',v[0]/C)
  print('vy:',v[1]/C)
  print('Calc angle:',math.acos(v[0]/math.sqrt(v[0]**2+v[1]**2)))

#simulation
def lightSim2(scenario, config):
  """
  run an light simulation
  """
  pos = scenario.initialPosition.copy()
  min = np.linalg.norm(pos)
  v = scenario.initialVelocity.copy()

  dt=config.dt
  maxn=int((config.durationMinutes*60)/dt)

  u = np.array([0.0, 0.0])
  u2 = np.array([0.0, 0.0])
  du = np.array([0.0, 0.0])
  a = np.array([0.0, 0.0])

  maxv=1.0
  
  log = LightLog()
  t=0
  starttime=time.time()
  print('Starting estimated duration:',"{:.2f}".format(maxn/N_PER_SECOND),'seconds (',"{:.2}".format(maxn/N_PER_HOUR),') hours')
  for n in range(0, maxn, 1):
    t=t+dt
    oldpos = pos.copy()
    d = np.linalg.norm(pos)
    #print(d)

    u2 = u.copy()
    #print('u2 ',u2[0],' ',u2[1])

    u[0] = -math.sqrt(2*GM/d) * pos[0]/d
    u[1] = -math.sqrt(2*GM/d) * pos[1]/d

    #print("ev",math.sqrt(u[0]**2+u[1]**2)," ",-math.sqrt(2*GM/d))
    du = u-u2
    v = addSI(v, -du)
    

    #print('du',du)
    #print('v',v)
    

    #print('u:',np.linalg.norm(u)/C,'v:',np.linalg.norm(v)/C)
    if(np.linalg.norm(v)/C > maxv):
      maxv = np.linalg.norm(v)/C 
    d = np.linalg.norm(pos)
    if(d<min):
      min=d

    #print('pos',pos)

    #g = GM/d**2
    g = GM/d**2 
    #print('g=',g,'d=',d)
    a = -g * pos/d
    u = u + a*dt  #todo relativistic acceleration?

    pos = pos + v*dt
    pos = pos + u*dt
    #print('v:',v)
    v[0]=C*v[0]/np.linalg.norm(v)
    v[1]=C*v[1]/np.linalg.norm(v)
    speed = np.linalg.norm(v)
    #print('v2:',v)
    log.recordPosition(n,d,pos,v)
  log.finish()
  print('max v:',maxv)
  print('closest distance:',min,' ',min/AU,'AU')
  print('Angle:',4*GM/(C**2*min))
  tx = v[0]/C + u[0]/C
  ty = v[1]/C + u[1]/C
  print('tx:',v[0]/C)
  print('ty:',v[1]/C)
  print('Calc angle:',math.acos(tx/math.sqrt(tx**2+ty**2)))

#pure newtonian
#TODO parameterise
def newtonian():
  pos = np.array([0, 150.0])
  b = abs(pos[0])
  v = np.array([0.000158, 0.0])
  a = np.array([0.0, 0.0])
  orbit=0
  max=0
  dt=60*60
  for t in range(0, (88*24*60*60), dt):
    oldpos = pos.copy
    pos = pos + v*dt
    d = np.linalg.norm(pos)
    if(d>max):
      maxpos = pos.copy()
    #g = GM/d**2
    g = (1/148000)/d**2 #TODO factor of 100???
    #print('g=',g)
    a = -g * pos/d
    v = v + a * dt
    speed = np.linalg.norm(v)
    #print(a,' ',v)
    #print(t,' ',d,' ',pos,' ',v)
    if(oldpos[0]<0 and pos[0]>=0):
      orbit=orbit+1
      print('orbit',orbit,'maxpos',maxpos)
      max=0
      
    #if(t%(24*60*60)==0):
      #print(t,',',pos[0],',',pos[1],' g=',g, 'speed=',speed)
      #print(pos[0],',',pos[1])
  #TODO calculate deflection


#pure newtonian+special
#TODO parameterise
def special():
  dt=10
  for t in range(-100.0, 100.0, dt):
    pos = pos + v*dt
    d = np.linalg.norm(pos)
    g = 1/d**2 #TODO add G , M and c later
    a = -dt * g * pos/d
    v = add(v, a)
    #print(t,' ',v[0],' ',v[1])
    print(t,' ',d,' ',pos[0],' ',pos[1])
  #TODO calculate deflection






#TODO special relativity

#TODO crompton effect
#pure newtonian
#TODO parameterise
def cromptonian():
  pos = np.array([-50000.0, 2.0])
  b = abs(pos[0])
  v = np.array([1.0, 0.0])
  a = np.array([0.0, 0.0])
  dt=1
  u = np.array([0.0, 0.0])
  for t in range(0, 1000000, dt):
    
    d = np.linalg.norm(pos)
    if(d<b):
      b=d
    #print('d ',d)

    u2 = u.copy()
    #print('u2 ',u2[0],' ',u2[1])

    u[0] = -(1/math.sqrt(d)) * pos[0]/d
    u[1] = -(1/math.sqrt(d)) * pos[1]/d
    #print('u ',u[0],' ',u[1])
    #print('u2 ',u2[0],' ',u2[1])

    du = u-u2
    #print('du ',du[0],' ',du[1])
    #print('v ',v,' ',du)
    v = add(v, -du)
    pos = pos + v*dt
    pos = pos + u*dt
    #pos = pos + v * dt
    
    log.print(t,' pos: ',pos,' v ',v,' b ',b)
  #TODO calculate deflection

    
#TODO SR + crompton affect


scenario = Scenario()
scenario.initialPosition = np.array([0.0, APOAPSIS_CLOSE])
scenario.initialVelocity = np.array([SPEED_CLOSE, 0.0])

config = Config()
config.dt=0.01
config.durationMinutes = 16
  
#orbitalSim(scenario, config)

dis = 10*AU

scenario.initialPosition = np.array([-dis, 70000000])
scenario.initialVelocity = np.array([C, 0.0])

config.durationMinutes = 2*dis/(60*C)

print(config.duration)

lightSim2(scenario, config)

#traversing moving frames of reference
#v = np.array([1.0, 0.0])
#du = np.array([0, 0.1])
#print(v)
#v = add(v, -du)
#print(v)
#v = add(v, -du)
#print(v)
#v = add(v, -du)
#print(v)
#v = add(v, -du)
#print(v)
#v = add(v, -du)
#print(v)
#v = add(v, -du)
#print(v)
#v = add(v, -du)
#print(v)
#v = add(v, -du)
#print(v)
#v = add(v, -du)
#print(v)

#traversing moving frames of reference


#v = np.array([1.0, 0.0])
#print(v)
#du = np.array([0, 0.01])
#for i in range(0,90,1):
#  v = add(v, -du)
#  print(v)



