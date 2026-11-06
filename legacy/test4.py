import math
import numpy as np
import time
from constants import *

class Config:
  dt = 0.0
  duration = 1

class Particle:
  pos = np.array([0.0,0.0])
  v = np.array([0.0,0.0])

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

  def start(this, maxn, p, calc, dt):
    this.starttime=time.time()
    this.startpos = p.pos
    print('Starting estimated duration:',"{:.2f}".format(maxn/calc.runspeed),'seconds (',"{:.2}".format(maxn/(calc.runspeed*3600)),') hours')
    print('calc: ', calc)
    print('dt: ',dt)
          

  def updatePosition(this, p, dt):
    this.t = this.t + dt
    this.period = this.period+dt
    d = np.linalg.norm(p.pos)
    if(d>this.max):
      this.maxpos = p.pos.copy()
      this.max=d
    if(d<this.min):
      this.minpos = p.pos.copy()
      this.min=d
    #display positions
##      print(this.t/dt)
##      print(int(dt*this.t))
##      print(this.freq)
##      print(int(this.t/dt)%this.freq==0)
      
    if((this.freq!=0) and (int(this.t/dt)%this.freq==0)):
      print(this.t,',',d,',',p.pos[0],',',p.pos[1],',',p.v[0],',',p.v[1])


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
    this.min=10000*AU #very large number    

   
    

  def finishOrbit(this):
    print()
    print('Simulation complete: ', time.time()-this.starttime,'seconds (',(time.time()-this.starttime)/3600,' hours)')
    print('sim time:', this.t )
    print()

    if this.orbit == 0:
      print('No orbits completed')
    elif this.orbit == 1:
      print('Only warmup orbit completed')
    else:
      #remove warmup orbit
      del this.periods[0]
      del this.periapsis[0]
      del this.apoapsis[0]
      del this.eccentricity[0]
      this.orbit-=1
      
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
      this.predictedPrecession = (24*math.pi**3)*(this.calcSMA**2)/(this.predictedPeriod**2 * C**2 * (1-this.calcEccentricity**2)) 
      print('predicted precession: ',this.predictedPrecession)

      if this.orbit == 1:
        print('Need >1 orbits to calculte precession')
      else:
        this.calcPPrecession = sum(this.periapsisPrecession)/this.orbit
        print('calc periapsis precession:', this.calcPPrecession,'   accuracy=', 100-100*abs((this.predictedPrecession-this.calcPPrecession)/this.predictedPrecession),'%')
        this.calcAPrecession = sum(this.apoapsisPrecession)/this.orbit
        print('calc apoapsis precession:', this.calcAPrecession,'   accuracy=', 100-100*abs((this.predictedPrecession-this.calcAPrecession)/this.predictedPrecession),'%')

  def finishHyperbolic(this, p):
    print('finish hyperbolic:', time.time()-this.starttime,'seconds (',(time.time()-this.starttime)/3600,' hours)')
    print('sim time:', this.t )
    print('closest distance:',this.min,' ',this.min/AU,'AU')
    print('Angle:',4*GM/(C**2*this.min))
    print('Calc angle:',math.acos(p.v[0]/math.sqrt(p.v[0]**2+p.v[1]**2)))
    print('')
    r = this.startpos - p.pos
    r = r / np.linalg.norm(r)
    x = -p.pos / np.linalg.norm(p.pos)
    a = np.dot(r, x)
    td = -(2*GM/C**2)*math.log(1-a)
    print('r:',r)
    print('x:',x)
    print('a:',a)
    print('td:',td)
    
    
  

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




class Calculator:
  def move(this, p, dt):
    runspeed = 30000

class NewtonianCalculator(Calculator):
  runspeed = 200000
  def move(this, p, dt):
    d = np.linalg.norm(p.pos)

    #calc magnitude of g in x and y
    g = -(GM/d**2) * (p.pos/d)

    #print('d:', d,' g',g,' gx',gx,' gy',gy)

    #accelerate v
    p.v = p.v+g*dt

    #move v
    p.pos = p.pos + p.v*dt

class SpecialCalculator(Calculator):
  runspeed = 120000
  def __init__(self):
    pass
  
  def move(this, p, dt):
    d = np.linalg.norm(p.pos)

    #calc magnitude of g in x and y
    g = -(GM/d**2) * (p.pos/d)

    #print('d:', d,' g',g,' gx',gx,' gy',gy)

    #accelerate v
    p.v = addSI(p.v, g*dt)

    #move v
    p.pos = p.pos + p.v*dt      


class NewtonianFlowCalculator(Calculator):
  runspeed = 120000

  def move(this, p, dt):

    #calc flow at current location 
    d = np.linalg.norm(p.pos)
    u1 = -math.sqrt(2*GM/d) * p.pos/d

    #calculate relative motion
    w = p.v-u1
    #print('w:',w)
    
    #print('u1:', this.u1)


    #print('0.5*g*dt**2:', gx, gy)
    #move with space and acceleration 
    p.pos = p.pos + u1*dt #+ 0.5*gx*dt**2
  
    #calc u at this location
    d = np.linalg.norm(p.pos)
    u2 = -math.sqrt(2*GM/d) * (p.pos/d)


    #print('u1:', this.u1)
          
    #move forward by relative w
    p.pos = p.pos + w*dt

    #calc flow at new location
    d = np.linalg.norm(p.pos)
    u3 = -math.sqrt(2*GM/d) * (p.pos/d)

    #change in rel velocity
    dw = u2-u3
    w = w + dw

    #calc new net velocity
    p.v = u3 + w


class ComplexFlowCalculator(Calculator):
  runspeed = 60000
  def move(this, p, dt):

    #calc flow at current location 
    d = np.linalg.norm(p.pos)
    u1 = -math.sqrt(2*GM/d) * p.pos/d

    #calculate relative motion
    w = p.v-u1
    #print('w:',w)
    
    #print('u1:', this.u1)

    g = -(GM/d**2)*(p.pos/d)    #gravity magnitude * unit vector
 

    #print('0.5*g*dt**2:', gx, gy)
    #move with space and acceleration 
    p.pos = p.pos + u1*dt #+ 0.5*gx*dt**2
  
    #calc u at this location
    d = np.linalg.norm(p.pos)
    u2 = -math.sqrt(2*GM/d) * p.pos/d


    #print('u1:', this.u1)
          
    #move forward by relative w 
    p.pos = p.pos + w*dt 
    
    #pos = pos + 0.5*w*dt 

    #calc flow at new location
    d = np.linalg.norm(p.pos)
    u3 = -math.sqrt(2*GM/d) * p.pos/d

    dw = u2 - u3
    w = addSI(w,dw)

    #calc new net velocity
    p.v = u3 + w


class FlowCalculator(Calculator):


  def move(this, p, dt):

    #calc flow at current location 
    d = np.linalg.norm(p.pos)
    u = -math.sqrt(2*GM/d) * p.pos/d

    #calc relative velocity
    w = p.v-u
    #print('v:',this.v)
    
    #print('u1:', this.u1)

    g = -(GM/d**2)*(p.pos/d)

    #print('0.5*g*dt**2:', gx, gy)
    #move with space and acceleration 
    p.pos = p.pos + u*dt


    #calc u at this new location
    d = np.linalg.norm(p.pos)
    u1 = -math.sqrt(2*GM/d) * p.pos/d

    #print('u1:', this.u1)
          
    #move forward by relative w
    p.pos = p.pos + w*dt

    #calc flow at new location
    d = np.linalg.norm(p.pos)
    u2 = -math.sqrt(2*GM/d) * p.pos/d

    #print('u2:', this.u2)
    #difference in flow
    du = u1 - u2
    #print('du:', this.du)

    #change relative velocity
    w = addSI(w, du)
    #print('v:', this.v)

    #calculate new net velocity
    p.v = w+u2
    
   
        
 
#simulation
#TODO parameterise
def orbitalSim(p, config, calc):
  """
  run a simulation
  """

  dt=config.dt
  maxn=int((config.durationDays*DAY)/dt)  

  t=0
  starttime=time.time()  
  log = Log()

  log.start(maxn, p, calc, dt)
  
  for n in range(0, maxn, 1):
    t=t+dt

    oldpos = p.pos.copy()

    calc.move(p, dt)

    log.updatePosition(p, dt)

    if(oldpos[1]<0 and p.pos[1]>=0):
       #orbit completed
      log.logOrbit()
  #sim complete
  log.finishOrbit()

#simulation
#TODO parameterise
def hyperbolicSim(p, config, calc, log):
  """
  run a simulation
  """


  dt=config.dt
  maxn=int((config.durationDays*DAY)/dt)  

  t=0
  starttime=time.time()  

  log.start(maxn, p, calc, dt)
  for n in range(0, maxn, 1):
    t=t+dt

    oldpos = p.pos.copy()

    calc.move(p, dt)

    log.updatePosition(p, dt)

  #sim complete
  log.finishHyperbolic(p)




def testFreefallFromInfinity():
  ME = 5.972E24     #Earth mass
  global GM
  GM = G*ME 

  
  p = Particle()
  config = Config()
  config.dt=0.01
  log = Log()
  log.freq = 100

  
  dis = 6371000


  
  p.pos = np.array([-dis, 0])

  d = np.linalg.norm(p.pos)
  u = math.sqrt(2*GM/d) * p.pos/d
  
  p.v = -u
  config.durationDays = 11/DAY

  hyperbolicSim(p, config, NewtonianFlowCalculator(), log)
  
def testFreefallFromEarth():  
  ME = 5.972E24     #Earth mass
  global GM
  GM = G*ME 

  
  p = Particle()
  config = Config()
  config.dt=0.01
  log = Log()
  log.freq = 100

  
  dis = 6371000
  
  p.pos = np.array([dis, 0])
  p.v = np.array([0.0, 0.0])
  config.durationDays = 11/DAY

  hyperbolicSim(p, config, NewtonianCalculator(), log)



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
  

#testCalc()

def testOrbitalSim():
  particle = Particle()
  particle.pos = np.array([0.0, MERCURY_MAX/9])
  particle.v = np.array([MERCURY_SPEED_AT_MAX*3, 0.0])

  config = Config()
  config.dt=0.001
  config.durationDays = 20
  
  orbitalSim(particle, config, ComplexFlowCalculator())

def testOrbitalSim2():
  particle = Particle()
  particle.pos = np.array([0.0, 0.01*AU])
  particle.v = np.array([243191.0, 0.0])

  config = Config()
  config.dt=0.001
  config.durationDays = 0.9
  
  orbitalSim(particle, config, NewtonianFlowCalculator())

def testOrbitalSim3():
  particle = Particle()
  particle.pos = np.array([0.0, 0.0001*AU])
  particle.v = np.array([2431909.9, 0.0])

  config = Config()
  config.dt=0.0000001
  config.durationDays = 0.001
  
  orbitalSim(particle, config, ComplexFlowCalculator())    

def testDeflectionOfLight():

  config = Config()
  dis = AU
  particle = Particle()
  particle.pos = np.array([-dis, 7E8])
  particle.v = np.array([C, 0.0])
  config.durationDays = 2*dis/(C*DAY)

  config.dt=10.0
  hyperbolicSim(particle, config, SpecialCalculator(), Log())





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
  particle = Particle()
  particle.pos = np.array([0.0, MERCURY_MAX])
  particle.v = np.array([MERCURY_SPEED_AT_MAX, 0.0])

  config = Config()
  config.dt=0.01
  config.durationDays = 350
  
  orbitalSim(particle, config, ComplexFlowCalculator())  


#testDeflectionOfLight()
#compareCalculators()
#testFreefallFromInfinity()

#testOrbitalSim3()
  
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

##t=0.0
##total=0.0
##dt=0.000000000001
##r=1.0
##dr=AU
###GM=G*1.5e12*MS
##print(GM)
##v = math.sqrt(2*GM/r)
##print(v)
##for i in range(10):
##  t=t+dt
##  vol1 = (4/3) * math.pi * r**3
##  v = math.sqrt(2*GM/r)
##  a = GM/r**2
##  r = r + v*dt #- 0.5*a*dt**2 
##  vol2 = (4/3) * math.pi * r**3
##  volA = vol2-vol1
##  
##  a = GM/r**2
##  v = math.sqrt(2*GM/r)
##  r = r + v*dt #- 0.5*a*dt**2 
##  vol3 = (4/3) * math.pi * r**3
##  volB = vol3-vol2
##  if i%1==0:
##    #print(i,',',t,',',r,',',volA,',',volB,',',(volB-volA)/dt**2,',',12*math.pi*GM)
##    print(r,',',volA,',',(volB-volA)/dt**2,',',12*math.pi*GM)
##  d = (volB-volA)/dt**2 - 12*math.pi*GM
##  total += d
##  av = total/(i+1)
##  print(av)

testMercury()
