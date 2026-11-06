import math
import numpy as np
import time
from constants import *

class Scenario:
  initialPosition = np.array([0][0])
  initialVelocity = np.array([0][0])

class Config:
  dt = 0.0
  duration = 1
  SR1 = True
  SR2 = True

class Log:
  
  t=0.0
  
  orbit=0
  period=0.0
  max=1.0
  maxpos = np.array([0.0,0.0])
  min=np.linalg.norm(1000*AU)
  minpos = np.array([0.0,0.0])
  
  periods = []
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

  #frequency of printing position
  freq=0

  def start(this, maxn):
    this.starttime=time.time()
    print('Starting estimated duration:',"{:.2f}".format(maxn/N_PER_SECOND),'seconds (',"{:.2}".format(maxn/N_PER_HOUR),') hours')

  def updatePosition(this, pos, v, dt):
    this.t = this.t + dt
    this.period = this.period+dt
    d = np.linalg.norm(pos)
    if(d>this.max):
      this.maxpos = pos.copy()
      this.max=d
    if(d<this.min):
      this.minpos = pos.copy()
      this.min=d
    #display positions
##      print(this.t/dt)
##      print(int(dt*this.t))
##      print(this.freq)
##      print(int(this.t/dt)%this.freq==0)
      
    if((this.freq!=0) and (int(this.t/dt)%this.freq==0)):
      print(this.t,',',d,',',pos[0],',',pos[1],',',v[0],',',v[1])


  def logOrbit(this):
    this.orbit=this.orbit+1
    #print(orbit,','maxpos[0],',',maxpos[1],',',max,',',math.asin(maxpos[0]/max),math.acos(maxpos[1]/max),',',min,',',min+max)
    #print(orbit,',',n,',',time.time()-starttime,',',math.acos(maxpos[1]/max),',',math.pi-math.acos(minpos[1]/min))
    print("orbit ",this.t/DAY,"days","min:",this.min,"max:",this.max)
   
    #calculate values
    sma=(this.min+this.max)/2
    e=1-2/(this.max/this.min+1)
    minP = math.pi-math.acos(this.minpos[1]/this.min) #total precession
    maxP = math.acos(this.maxpos[1]/this.max)
   
    print(minP, maxP)
   
    #log.recordOrbit(orbit, period, min, max, sma, e, minP, maxP)
    this.periods.append(this.period)
    this.periapsis.append(this.min)
    this.apoapsis.append(this.max)
    this.semiMajorAxis.append(sma)
    this.eccentricity.append(e)
    this.periapsisAngle.append(minP)
    if(len(this.periapsisAngle)>1):
      this.periapsisPrecession.append(this.periapsisAngle[this.orbit-1]-this.periapsisAngle[this.orbit-2])
    this.apoapsisAngle.append(maxP)
    if(len(this.apoapsisAngle)>1):
      this.apoapsisPrecession.append(this.apoapsisAngle[this.orbit-1]-this.apoapsisAngle[this.orbit-2])
   
    #reset counters
    this.period=0
    this.max=0
    this.min=np.linalg.norm(scenario.initialPosition)    

   
    

  def finishOrbit(this):
    print()
    print('Simulation complete')
    print()

    if this.orbit == 0:
      print('No orbits completed')
    else:
      this.calcPeriod = sum(this.periods)/this.orbit
      this.calcPeriapsis = sum(this.periapsis)/this.orbit
      this.calcApoapsis = sum(this.apoapsis)/this.orbit
      this.calcSMA = (this.calcPeriapsis + this.calcApoapsis) / 2
      this.predictedPeriod = 2*math.pi*math.sqrt(this.calcSMA**3/GM)
      this.calcEccentricity = sum(this.eccentricity)/this.orbit

      print('orbits:',this.orbit,' average period',this.calcPeriod/DAY,' days          predicted period:',this.predictedPeriod/(24*60*60),' days')
      print()
      print('calculated')
      print('  Periapsis:\t',this.calcPeriapsis,"\t","{:0.2}".format(this.calcPeriapsis/AU),'AU')
      print('  Apoapsis:\t',this.calcApoapsis,"\t","{:0.2}".format(this.calcApoapsis/AU),'AU')
      print('  semi-major:\t', this.calcSMA,"\t","{:0.2}".format(this.calcSMA/AU),'AU')
      print('  eccentricity:\t', this.calcEccentricity)

      print()
      this.predictedPrecession = (24*math.pi**3)*(this.calcSMA**2)/(this.calcPeriod**2 * C**2 * (1-this.calcEccentricity**2)) 
      print('predicted precession: ',this.predictedPrecession)

      if this.orbit == 1:
        print('Need >1 orbits to calculte precession')
      else:
        this.calcPPrecession = sum(this.periapsisPrecession)/(this.orbit-1)
        print('calc periapsis precession:', this.calcPPrecession,'   accuracy=', 100-100*abs((this.predictedPrecession-this.calcPPrecession)/this.predictedPrecession),'%')
        this.calcAPrecession = sum(this.apoapsisPrecession)/(this.orbit-1)
        print('calc apoapsis precession:', this.calcAPrecession,'   accuracy=', 100-100*abs((this.predictedPrecession-this.calcAPrecession)/this.predictedPrecession),'%')

  def finishHyperbolic(this, v):
    print('finish hyperbolic:', this.t )
    print('closest distance:',this.min,' ',this.min/AU,'AU')
    print('Angle:',4*GM/(C**2*this.min))
    print('Calc angle:',math.acos(v[0]/math.sqrt(v[0]**2+v[1]**2)))
        
class LightLog:
  freq = 100000
  
  def recordPosition(this, n, d, pos, v):
    if(n%this.freq==0):
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
  maxPos = pos.copy()

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
    u = u + a * dt

    pos = pos + v*dt
    pos = pos + u*dt
    
    
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


class Calculator:
  def move(this, pos, v, dt):
    pass

class NewtonianCalculator(Calculator):
  
  def move(this, pos, v, dt):
    d = np.linalg.norm(pos)

    g = -GM/d**2
    #calc magnitude of g in x and y
    gx = g * pos[0]/d
    gy = g * pos[1]/d

    #print('d:', d,' g',g,' gx',gx,' gy',gy)

    #accelerate v
    v[0] = v[0]+gx*dt
    v[1] = v[1]+gy*dt

    #move v
    pos[0] = pos[0] + v[0]*dt
    pos[1] = pos[1] + v[1]*dt


class ComplexNewtonianFlowCalculator(Calculator):
  u1 = np.array([0.0,0.0])
  u2 = np.array([0.0,0.0])
  u3 = np.array([0.0,0.0])
  du = np.array([0.0,0.0])
  v = np.array([0.0,0.0])

  def move(this, p, vel, dt):
    pos = p.copy()
    v = vel.copy()
    #print('vz:',v)

    #calc flow at current location 
    d = np.linalg.norm(pos)
    this.u1 = -math.sqrt(2*GM/d) * pos/d

    #calculate relative motion
    w = v-this.u1
    #print('w:',w)
    
    #print('u1:', this.u1)

    g = -GM*pos/d**3    #gravity magnitude * unit vector
 

    #print('0.5*g*dt**2:', gx, gy)
    #move with space and acceleration 
    pos = pos + this.u1*dt #+ 0.5*gx*dt**2
  
    #calc u at this location
    d = np.linalg.norm(pos)
    this.u2 = -math.sqrt(2*GM/d) * pos/d

    #incremental move
    pos = pos + 0.5*(this.u2-this.u1)*dt

    dw = g*dt - (this.u2-this.u1)

    #print('u1:', this.u1)
          
    #move forward by relative w
    pos = pos + w*dt + 0.5*dw*dt
    w = w + dw
 

    #calc flow at new location
    d = np.linalg.norm(pos)
    this.u3 = -math.sqrt(2*GM/d) * pos/d

    #calc new net velocity
    v = this.u2 + w

    p[0] = pos[0]
    p[1] = pos[1]
    vel[0] = v[0]
    vel[1] = v[1]

##    print("pos:",pos)
##    print("pos:",this.u2)
##    print("pos:",w)
##    print("pos:",v)

class ComplexFlowCalculator(Calculator):
  u1 = np.array([0.0,0.0])
  u2 = np.array([0.0,0.0])
  u3 = np.array([0.0,0.0])
  du = np.array([0.0,0.0])
  v = np.array([0.0,0.0])

  def move(this, p, vel, dt):
    pos = p.copy()
    v = vel.copy()
    #print('vz:',v)

    #calc flow at current location 
    d = np.linalg.norm(pos)
    this.u1 = -math.sqrt(2*GM/d) * pos/d

    #calculate relative motion
    w = v-this.u1
    #print('w:',w)
    
    #print('u1:', this.u1)

    g = -(GM/d**2)*(pos/d)    #gravity magnitude * unit vector
 

    #print('0.5*g*dt**2:', gx, gy)
    #move with space and acceleration 
    pos = pos + this.u1*dt #+ 0.5*gx*dt**2
  
    #calc u at this location
    d = np.linalg.norm(pos)
    this.u2 = -math.sqrt(2*GM/d) * pos/d

    #incremental move
    pos = pos + 0.5*(this.u2-this.u1)*dt

    dw = g*dt - (this.u2-this.u1)

    #print('u1:', this.u1)
          
    #move forward by relative w (before and after)
    pos = pos + w*dt +0.5*dw*dt**2 
    
    #pos = pos + 0.5*w*dt 

    #calc flow at new location
    d = np.linalg.norm(pos)
    this.u3 = -math.sqrt(2*GM/d) * pos/d

    dw = this.u3 - this.u1
    w = addSI(w,dw)

    #calc new net velocity
    v = this.u2 + w

    p[0] = pos[0]
    p[1] = pos[1]
    vel[0] = v[0]
    vel[1] = v[1]

##    print("pos:",pos)
##    print("pos:",this.u2)
##    print("pos:",w)
##    print("pos:",v)


class FlowCalculator(Calculator):


  def move(this, p, vel, dt):
    #print('vz:',v)
    pos = p.copy()
    v = vel.copy()

    #calc flow at current location 
    d = np.linalg.norm(pos)
    u = -math.sqrt(2*GM/d) * pos/d

    #calc relative velocity
    w = v-u
    #print('v:',this.v)
    
    #print('u1:', this.u1)

    g = -(GM/d**2)*(pos/d)

    #print('0.5*g*dt**2:', gx, gy)
    #move with space and acceleration 
    pos = pos + u*dt


    #calc u at this new location
    d = np.linalg.norm(pos)
    u1 = -math.sqrt(2*GM/d) * pos/d

    #print('u1:', this.u1)
          
    #move forward by relative w
    pos = pos + w*dt

    #calc flow at new location
    d = np.linalg.norm(pos)
    u2 = -math.sqrt(2*GM/d) * pos/d

    #print('u2:', this.u2)
    #difference in flow
    du = u1 - u2


    #print('du:', this.du)

    #change relative velocity
    w = addSI(w, du)
    #print('v:', this.v)

    v = w+u2
    #calculate new net velocity
    vel[0] = v[0]
    vel[1] = v[1]
    p[0] = pos[0]
    p[1] = pos[1]
    #print('vz:', v)    
    
class RotationCalculator(Calculator):
  #thomas rotation, no gravitational attraction
  u1 = np.array([0.0,0.0])
  u2 = np.array([0.0,0.0])
  du = np.array([0.0,0.0])
  v = np.array([0.0,0.0])

  def move(this, pos, v, dt):
    #calc flow at current location 
    d = np.linalg.norm(pos)
    this.u1[0] = -math.sqrt(2*GM/d) * pos[0]/d
    this.u1[1] = -math.sqrt(2*GM/d) * pos[1]/d

    #calc relative velocity
    this.v = v-this.u1

    #move with space and acceleration 
    pos[0] = pos[0] + this.u1[0]*dt 
    pos[1] = pos[1] + this.u1[1]*dt 

    #calc u at this location
    d = np.linalg.norm(pos)
    this.u1[0] = -math.sqrt(2*GM/d) * pos[0]/d
    this.u1[1] = -math.sqrt(2*GM/d) * pos[1]/d
          
    #move forward by relative v
    pos[0] = pos[0] + this.v[0]*dt
    pos[1] = pos[1] + this.v[1]*dt 

    #calc flow at new location
    d = np.linalg.norm(pos)
    this.u2[0] = -math.sqrt(2*GM/d) * pos[0]/d
    this.u2[1] = -math.sqrt(2*GM/d) * pos[1]/d

    #print('u2:', this.u2)
    #difference in flow
    this.du[0] = this.u1[0] - this.u2[0]
    this.du[1] = this.u1[1] - this.u2[1]

    #print('du:', this.du)

    #change relative velocity
    this.v = addSI(this.v, this.du)
    #print('v:', this.v)
    
    #calculate new net velocity
    v[0] = this.v[0] + this.u2[0]
    v[1] = this.v[1] + this.u2[1]
    #print('vz:', v)      
 
#simulation
#TODO parameterise
def orbitalSim2(scenario, config, calc):
  """
  run a simulation
  """
  pos = scenario.initialPosition.copy()
  v = scenario.initialVelocity.copy()

  dt=config.dt
  maxn=int((config.durationDays*DAY)/dt)  

  t=0
  starttime=time.time()  
  log = Log()

  log.start(maxn)
  
  for n in range(0, maxn, 1):
    t=t+dt

    oldpos = pos.copy()

    calc.move(pos, v, dt)

    log.updatePosition(pos, v, dt)

    if(oldpos[1]<0 and pos[1]>=0):
       #orbit completed
      log.logOrbit()
  #sim complete
  log.finishOrbit()

#simulation
#TODO parameterise
def hyperbolicSim(scenario, config, calc, log):
  """
  run a simulation
  """
  pos = scenario.initialPosition.copy()
  v = scenario.initialVelocity.copy()

  dt=config.dt
  maxn=int((config.durationDays*DAY)/dt)  

  t=0
  starttime=time.time()  

  log.start(maxn)
  for n in range(0, maxn, 1):
    t=t+dt

    oldpos = pos.copy()

    calc.move(pos, v, dt)

    log.updatePosition(pos, v, dt)

  #sim complete
  log.finishHyperbolic(v)

  

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
    if(config.SR1):
      #relativistic addition of velocities
      v = addSI(v, -du)
    else:
      #simple addition
      v = v-du
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



def testFreefallFromInfinity():
  scenario = Scenario()
  config = Config()
  config.dt=1
  log = Log()
  log.freq = 100000

  
  dis = AU
  vg = math.sqrt(2*GM/dis**2)
  scenario.initialPosition = np.array([dis, 0])
  scenario.initialVelocity = np.array([0.0, 0.0])
  config.durationDays = 60/DAY

  hyperbolicSim(scenario, config, NewtonianCalculator(), log)
  
def testFreefallFromEarth():  
  ME = 5.972E24     #Earth mass
  global GM
  GM = G*ME 

  
  scenario = Scenario()
  config = Config()
  config.dt=0.01
  log = Log()
  log.freq = 100

  
  dis = 6371000
  
  scenario.initialPosition = np.array([dis, 0])
  scenario.initialVelocity = np.array([0.0, 0.0])
  config.durationDays = 11/DAY

  hyperbolicSim(scenario, config, NewtonianFlowCalculator(), log)



def testCalc():
  ME = 5.972E24     #Earth mass
  global GM
  GM = G*ME
  dis = 6371000.0

  pos = np.array([0.0, dis])
  vel = np.array([0.0, 0.0])

  calc = ComplexNewtonianFlowCalculator()

  for i in range(1):
    calc.move(pos, vel, 10)

  print(' pos:',dis-pos[1])
  print(' vel:',vel[1])
  

#testCalc()

def testOrbitalSim():
  scenario = Scenario()
  scenario.initialPosition = np.array([0.0, MERCURY_MAX/9])
  scenario.initialVelocity = np.array([MERCURY_SPEED_AT_MAX*3, 0.0])

  config = Config()
  config.dt=0.01
  config.durationDays = 10
  
  orbitalSim2(scenario, config, ComplexNewtonianFlowCalculator())

def testDeflectionOfLight():

  scenario = Scenario()
  config = Config()
  dis = 2*AU
  scenario.initialPosition = np.array([-dis, 7E8])
  scenario.initialVelocity = np.array([C, 0.0])
  config.durationDays = 2*dis/(C*DAY)

  config.dt=0.01
  hyperbolicSim(scenario, config, FlowCalculator(), Log())





def compareCalculators():
  dt= 0.010
  n = int(10/dt)
  pos = np.array([-5*C, 7E8])
  v = np.array([C, 0.0])

  print("before:",pos, v)
  calc = FlowCalculator()
  for i in range(n):
    calc.move(pos,v, dt)

  print("after:",pos, v)

  pos = np.array([-5*C, 7E8])
  v = np.array([C, 0.0])

  print("before:",pos, v)
  calc = ComplexFlowCalculator()
  for i in range(n):
    calc.move(pos,v, dt)

  print("after:",pos, v)
  
  


testDeflectionOfLight()
#compareCalculators()
  
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




