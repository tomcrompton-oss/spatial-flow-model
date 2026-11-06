import math
import numpy as np
import time
from constants import *

class Config:
  dt = 0.0

class Condition:
  def __init__(self, limit):
    self.limit = limit

class Duration(Condition):
  def check(self, p):
    if p.t>self.limit:
      return False
    else:
      return True

class ProperDuration(Condition):
  def check(self, p):
    if p.pt>self.limit:
      return False
    else:
      return True    

class MinDistance(Condition):
  def check(self, p):
    if np.linalg.norm(p.pos)<self.limit:
      return False
    else:
      return True

class MaxDistance(Condition):
  def check(self, p):
    if np.linalg.norm(p.pos)>self.limit:
      return False
    else:
      return True

class MaxDistanceAndBelow(Condition):
  def check(self, p):
    if np.linalg.norm(p.pos)>self.limit and p.pos[1]<0:
      return False
    else:
      return True      

class Particle:
  pos = np.array([0.0,0.0])
  v = np.array([0.0,0.0])
  pt = 0.0 #proper time
  t = 0.0 #coord time
  d = 0.0 #distance travelled

class Log:

  t=0.0

  GM=G*MS
  
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
  pfreq=0 #proper time freq
  counter=0

  def start(self, maxn, p, calc, dt):
    self.starttime=time.time()
    self.startpos = p.pos
    GM = calc.GM
    print('Starting estimated duration:',"{:.2f}".format(maxn/calc.runspeed),'seconds (',"{:.2}".format(maxn/(calc.runspeed*3600)),') hours')
    print('calc: ', calc)
    print('dt: ',dt)
          

  def updatePosition(self, p, dt):
    self.t = self.t + dt
    self.period = self.period+dt
    d = np.linalg.norm(p.pos)
    if(d>self.max):
      self.maxpos = p.pos.copy()
      self.max=d
    if(d<self.min):
      self.minpos = p.pos.copy()
      self.min=d
    #display positions
##      print(self.t/dt)
##      print(int(dt*self.t))
##      print(self.freq)
##      print(int(self.t/dt)%self.freq==0)
      
    if((self.freq!=0) and ((round(self.t/dt))%(round(self.freq/dt))==0)):
      #print(self.t,',',p.pt,',',d,',',p.pos[0],',',p.pos[1],',',p.v[0],',',p.v[1])
      print('t:', self.t,', pt:',p.pt,', d(AU):',d/AU, ', v(c):', np.linalg.norm(p.v)/C)
      #print(d/AU)  



  def logOrbit(self):
    self.orbit=self.orbit+1
    #print(orbit,','maxpos[0],',',maxpos[1],',',max,',',math.asin(maxpos[0]/max),math.acos(maxpos[1]/max),',',min,',',min+max)
    #print(orbit,',',n,',',time.time()-starttime,',',math.acos(maxpos[1]/max),',',math.pi-math.acos(minpos[1]/min))
    print("orbit ",self.t/DAY,"days","min:",self.min,"max:",self.max)
   
    #calculate values
    sma=(self.min+self.max)/2
    e=1-2/(self.max/self.min+1)
    minP = math.pi-math.acos(self.minpos[1]/self.min) #total precession
    maxP = math.acos(self.maxpos[1]/self.max)
   
    print(minP, maxP)
   
    #log.recordOrbit(orbit, period, min, max, sma, e, minP, maxP)
    self.periods.append(self.period)
    self.periapsis.append(self.min)
    self.apoapsis.append(self.max)
    self.semiMajorAxis.append(sma)
    self.eccentricity.append(e)
    self.periapsisAngle.append(minP)
    if(len(self.periapsisAngle)>1):
      self.periapsisPrecession.append(self.periapsisAngle[self.orbit-1]-self.periapsisAngle[self.orbit-2])
    self.apoapsisAngle.append(maxP)
    if(len(self.apoapsisAngle)>1):
      self.apoapsisPrecession.append(self.apoapsisAngle[self.orbit-1]-self.apoapsisAngle[self.orbit-2])
   
    #reset counters
    self.period=0
    self.max=0
    self.min=10000*AU #very large number    

   
    

  def finishOrbit(self):
    print()
    print('Simulation complete: ', time.time()-self.starttime,'seconds (',(time.time()-self.starttime)/3600,' hours)')
    print('sim time:', self.t )
    print()

    if self.orbit == 0:
      print('No orbits completed')
    elif self.orbit == 1:
      print('Only warmup orbit completed')
    else:
      #remove warmup orbit
      del self.periods[0]
      del self.periapsis[0]
      del self.apoapsis[0]
      del self.eccentricity[0]
      self.orbit-=1
      
      self.calcPeriod = sum(self.periods)/self.orbit
      self.calcPeriapsis = sum(self.periapsis)/self.orbit
      self.calcApoapsis = sum(self.apoapsis)/self.orbit
      self.calcSMA = (self.calcPeriapsis + self.calcApoapsis) / 2
      self.predictedPeriod = 2*math.pi*math.sqrt(self.calcSMA**3/self.GM)
      self.calcEccentricity = sum(self.eccentricity)/self.orbit

      print('orbits:',self.orbit,' average period',self.calcPeriod/DAY,' days          predicted period:',self.predictedPeriod/(24*60*60),' days')
      print()
      print('calculated')
      print('  Periapsis:\t',self.calcPeriapsis,"\t","{:0.2}".format(self.calcPeriapsis/AU),'AU')
      print('  Apoapsis:\t',self.calcApoapsis,"\t","{:0.2}".format(self.calcApoapsis/AU),'AU')
      print('  semi-major:\t', self.calcSMA,"\t","{:0.2}".format(self.calcSMA/AU),'AU')
      print('  eccentricity:\t', self.calcEccentricity)

      print()
      self.predictedPrecession = (24*math.pi**3)*(self.calcSMA**2)/(self.predictedPeriod**2 * C**2 * (1-self.calcEccentricity**2)) 
      print('predicted precession: ',self.predictedPrecession)

      if self.orbit == 1:
        print('Need >1 orbits to calculte precession')
      else:
        self.calcPPrecession = sum(self.periapsisPrecession)/self.orbit
        print('calc periapsis precession:', self.calcPPrecession,'   accuracy=', 100-100*abs((self.predictedPrecession-self.calcPPrecession)/self.predictedPrecession),'%')
        self.calcAPrecession = sum(self.apoapsisPrecession)/self.orbit
        print('calc apoapsis precession:', self.calcAPrecession,'   accuracy=', 100-100*abs((self.predictedPrecession-self.calcAPrecession)/self.predictedPrecession),'%')

  def finishHyperbolic(self, p):
    print('finish hyperbolic:', time.time()-self.starttime,'seconds (',(time.time()-self.starttime)/3600,' hours)')
    print('sim time:', self.t )
    print('closest distance:',self.min,' ',self.min/AU,'AU')
    print('Angle:',4*self.GM/(C**2*self.min))
    print('Calc angle:',math.acos(p.v[0]/math.sqrt(p.v[0]**2+p.v[1]**2)))
    print('')
##    r = self.startpos - p.pos
##    r = r / np.linalg.norm(r)
##    x = -p.pos / np.linalg.norm(p.pos)
##    a = np.dot(r, x)
##    td = -(2*GM/C**2)*math.log(1-a)
##    print('r:',r)
##    print('x:',x)
##    print('a:',a)
##    print('td:',td)
    



class Calculator:

  def __init__(self):
    self.GM = G*MS #default to solar mass
    
  def __init__(self, m):
    self.GM = G*m
    
  def add(self, u, v):
     """
     relativistic addition of two velocities
     Args:
       u (float): the first velocity as a fraction of c
       v (float): the second velocity as a fraction of c
     Returns:
       w (float): the sum of the two velocities as a fraction of c
     """
     if np.dot(v,v) == 0:
       return u.copy()
     
     upar = v * np.dot(u,v) / np.dot(v, v)
     uper = u-upar

     wpar = (upar+v) / (1+np.dot(v, upar))
     x = 1-np.linalg.norm(v)**2
     #using fp numbers it is possible to get a negative number here
     if x<0:
       v = v / np.linalg.norm(v)
       L = 0
     else:
       L = math.sqrt(1-np.linalg.norm(v)**2)

     wper =  (L * uper)/ (1+np.dot(v, upar))
     
     w = wpar + wper
     return w

  def addSI(self, u, v):
     """
     relativistic addition of two velocities
     Args:
       u (float): the first velocity in m/s
       v (float): the second velocity in m/s
     Returns:
       w (float): the sum of the two velocities in m/s
     """
     return self.add(u/C, v/C)*C
  
  def move(self, p, dt):
    runspeed = 30000

  def orbitalSim(self, p, config, log):
    """
    run an orbital simulation
    """
    dt=config.dt
    maxn=int((config.durationDays*DAY)/dt)  

    t=0
    starttime=time.time()  
    log = Log()

    log.start(maxn, p, self, dt)
    
    for n in range(0, maxn, 1):
      t=t+dt

      oldpos = p.pos.copy()

      self.move(p, dt)

      log.updatePosition(p, dt)

      if(oldpos[1]<0 and p.pos[1]>=0):
         #orbit completed
        log.logOrbit()
    #sim complete
    log.finishOrbit()

  def hyperbolicSim(self, p, config, log):
    """
    run a hyperbolic simulation
    """

    dt=config.dt

    t=0
    starttime=time.time()  

    log.start(config.condition.limit, p, self, dt)
    
    while config.condition.check(p):
      t=t+dt

      oldpos = p.pos.copy()

      self.move(p, dt)

      log.updatePosition(p, dt)

    #sim complete
    log.finishHyperbolic(p)
    print(p.pos)
    print(p.v)

class NewtonianCalculator(Calculator):
  runspeed = 200000

  def move(self, p, dt):
    d = np.linalg.norm(p.pos)

    #calc magnitude of g in x and y
    g = -(self.GM/d**2) * (p.pos/d)

    #print('d:', d,' g',g,' gx',gx,' gy',gy)

    #accelerate v
    p.v = p.v+g*dt

    #move v
    p.pos = p.pos + p.v*dt
    p.pt += dt
    p.t += dt

class SpecialCalculator(Calculator):
  runspeed = 120000
  
  def move(self, p, dt):
    d = np.linalg.norm(p.pos)

    #calc magnitude of g in x and y
    g = -(self.GM/d**2) * (p.pos/d)

    #print('d:', d,' g',g,' gx',gx,' gy',gy)

    #accelerate v
    p.v = self.addSI(p.v, g*dt)

    #move v
    p.pos = p.pos + p.v*dt
    p.t += dt
    p.pt += dt / math.sqrt(1-p.v**2 / C**2)


class NewtonianFlowCalculator(Calculator):
  runspeed = 120000

  def move(self, p, dt):

    #calc flow at current location 
    d = np.linalg.norm(p.pos)
    u1 = -math.sqrt(2*self.GM/d) * p.pos/d

    #calculate relative motion
    w = p.v-u1
    #print('w:',w)
    
    #print('u1:', self.u1)


    #print('0.5*g*dt**2:', gx, gy)
    #move with space and acceleration 
    p.pos = p.pos + u1*dt #+ 0.5*gx*dt**2
  
    #calc u at self location
    d = np.linalg.norm(p.pos)
    u2 = -math.sqrt(2*self.GM/d) * (p.pos/d)


    #print('u1:', self.u1)
          
    #move forward by relative w
    p.pos = p.pos + w*dt

    #calc flow at new location
    d = np.linalg.norm(p.pos)
    u3 = -math.sqrt(2*self.GM/d) * (p.pos/d)

    #change in rel velocity
    dw = u2-u3
    w = w + dw

    #calc new net velocity
    p.v = u3 + w
    p.t += dt
    p.pt += dt


class SpecialFlowCalculator(Calculator):
  runspeed = 60000
  def move(self, p, dt):

    #calc flow at current location 
    d = np.linalg.norm(p.pos)
    u1 = -math.sqrt(2*self.GM/d) * p.pos/d

    #calculate relative motion
    w = p.v-u1


    #move with space  
    p.pos = p.pos + u1*dt
    p.d += np.linalg.norm(u1*dt)
  
    #calc u at self location
    d = np.linalg.norm(p.pos)
    u2 = -math.sqrt(2*self.GM/d) * p.pos/d
          
    #move forward by relative w 
    p.pos = p.pos + w*dt
    p.d += np.linalg.norm(w*dt)

    #calc flow at new location
    d = np.linalg.norm(p.pos)
    u3 = -math.sqrt(2*self.GM/d) * p.pos/d

    dw = u2 - u3
    w = self.addSI(w,dw)


    #calc new net velocity
    p.v = u3 + w

    p.t += dt
    if (1-(np.linalg.norm(w)**2)/C**2)<0.0:
      p.pt += 0.0
    else:
      p.pt += dt * math.sqrt(1-(np.linalg.norm(w)**2)/C**2)


class ExtraSpecialFlowCalculator(Calculator):
  runspeed = 60000
  def move(self, p, dt):
    oldPos = p.pos

    #calc flow at current location 
    d = np.linalg.norm(p.pos)
    u1 = -math.sqrt(2*self.GM/d) * p.pos/d

    #calculate relative motion
    w = self.addSI(-u1, p.v)

    #move with space  
    p.pos = p.pos + u1*dt
    #p.d += np.linalg.norm(u1*dt)
  
    #calc u at this location
    d = np.linalg.norm(p.pos)
    u2 = -math.sqrt(2*self.GM/d) * p.pos/d
          
    #move forward by relative w 
    p.pos = p.pos + w*dt
    #p.d += np.linalg.norm(w*dt)
    
    #pos = pos + 0.5*w*dt 

    #calc flow at new location
    d = np.linalg.norm(p.pos)
    u3 = -math.sqrt(2*self.GM/d) * p.pos/d

    dw = u2 - u3
    w = self.addSI(w,dw)

    


    #calc new net velocity
    p.v = self.addSI(u3,w)

    #move with this velocity
    p.pos = oldPos + p.v*dt
    p.d += np.linalg.norm(p.v)*dt

    p.t += dt
    if (1-(np.linalg.norm(w)**2)/C**2)<0.0:
      p.pt += 0.0
    else:
      p.pt += dt * math.sqrt(1-(np.linalg.norm(w)**2)/C**2)
   




       
 


