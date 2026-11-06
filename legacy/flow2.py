import math
import numpy as np
import time
from constants import *   #legacy/constants.py, which gets engine/constants.py
from engine.logger import Log

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
  u = np.array([0.0,0.0])   #velocity of local space
  w = np.array([0.0,0.0])   #local velocity relative to space
  pt = 0.0 #proper time
  t = 0.0 #coord time
  d = 0.0 #distance travelled


class Body:
  """
  a mass that space flows into (black) or out of (white)
  Args:
    mass (float): mass in kg
    x, y (float): position in m
    black (bool): True - space flows in, False - space flows out (white)
  """
  def __init__(self, mass=MS, x=0.0, y=0.0, black=True):
    self.mass = mass
    self.pos = np.array([float(x), float(y)])
    self.black = black
    self.GM = G*mass

  @property
  def x(self):
    return self.pos[0]

  @property
  def y(self):
    return self.pos[1]


class Calculator:

  def __init__(self, bodies=None):
    """
    Args:
      bodies (list of Body): the masses; default one black solar mass at (0,0)
    """
    if bodies is None:
      bodies = [Body()]
    elif isinstance(bodies, Body):
      bodies = [bodies]
    elif not isinstance(bodies, (list, tuple)):
      raise TypeError('pass a list of Body objects, e.g. [Body(m)], not ' + repr(bodies))
    self.bodies = list(bodies)
    self.GM = G*sum(b.mass for b in self.bodies) #total, used by the log
    self.log = None #set by the sims so warnings go to the log

  def warn(self, message):
    if self.log is not None:
      self.log.print('WARNING:', message)
    else:
      print('WARNING:', message)

  def flow(self, pos):
    """
    velocity of space (u) at pos
      magnitude: square root of the sum of the squares of the flow to each body, sqrt(2GM/d)
      direction: towards black bodies and away from white ones, weighted by each body's GM/d^2
    """
    #magnitude of flow
    U = 0.0
    for b in self.bodies:
      d = np.linalg.norm(pos - b.pos)
      U = U + 2*b.GM/d   #square of the flow to this body
    U = math.sqrt(U)

    #direction of flow
    g = np.array([0.0, 0.0])
    for b in self.bodies:
      r = pos - b.pos
      d = np.linalg.norm(r)
      g_mag = b.GM/d**2
      if b.black:
        g -= g_mag * r/d   #towards the body
      else:
        g += g_mag * r/d   #away from the body

    gsize = np.linalg.norm(g)
    if gsize == 0:
      self.warn('g=0 at %s, the flow has no direction - using u=0' % pos)
      return np.array([0.0, 0.0])
    return U * g/gsize

  def gravity(self, pos):
    """newtonian acceleration at pos: the sum of each body's pull"""
    g = np.array([0.0, 0.0])
    for b in self.bodies:
      r = pos - b.pos
      d = np.linalg.norm(r)
      g = g + -(b.GM/d**2) * (r/d)
    return g
    
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
    self.log = log

    t=0
    starttime=time.time()  

    log.print('test type: orbit')   #csv_viewer.py splits orbit runs into their orbits
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
    self.log = log

    t=0
    starttime=time.time()  

    log.print('test type: hyperbolic')
    log.start(config.condition.limit, p, self, dt)
    
    while config.condition.check(p):
      t=t+dt

      oldpos = p.pos.copy()

      self.move(p, dt)
      #print(t,' ',p.pos)
      log.updatePosition(p, dt)

    #sim complete
    log.finishHyperbolic(p)
    log.print(p.pos)
    log.print(p.v)

class NewtonianCalculator(Calculator):
  runspeed = 200000

  def move(self, p, dt):
    #calc g in x and y
    g = self.gravity(p.pos)

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
    #calc g in x and y
    g = self.gravity(p.pos)

    #print('d:', d,' g',g,' gx',gx,' gy',gy)

    #accelerate v
    p.v = self.addSI(p.v, g*dt)

    #move v
    p.pos = p.pos + p.v*dt
    p.t += dt
    p.pt += dt / math.sqrt(1-p.v**2 / C**2)


class NewtonianFlowCalculator(Calculator):
  runspeed = 120000

  def initPV(self, p, v):
    p.v = v
    p.u = self.flow(p.pos)
    p.w = p.v - p.u

  def move(self, p, dt):

    #calc flow at current location 
    u1 = self.flow(p.pos)

    #calculate relative motion
    w = p.v-u1
    #print('w:',w)
    
    #print('u1:', self.u1)


    #print('0.5*g*dt**2:', gx, gy)
    #move with space and acceleration 
    p.pos = p.pos + u1*dt #+ 0.5*gx*dt**2
  
    #calc u at self location
    u2 = self.flow(p.pos)


    #print('u1:', self.u1)
          
    #move forward by relative w
    p.pos = p.pos + w*dt

    #calc flow at new location
    u3 = self.flow(p.pos)

    #change in rel velocity
    dw = u2-u3
    p.w = w + dw

    p.u=u3

    #calc new net velocity
    p.v = p.u + p.w
    p.t += dt
    p.pt += dt


class SpecialFlowCalculator(Calculator):
  runspeed = 60000

  def initPOld(self, p, w):
    p.w = w
    p.u = self.flow(p.pos)
    p.v = p.u+p.w

  def initP(self, p, v):
    p.v = v
    p.u = self.flow(p.pos)
    p.w = p.v-p.u
    
  def move(self, p, dt):
    #move with space  
    p.pos = p.pos + p.u*dt
    p.d += np.linalg.norm(p.u*dt)
  
    #calc u at this location
    u2 = self.flow(p.pos)
          
    #move forward by relative w 
    p.pos = p.pos + p.w*dt
    p.d += np.linalg.norm(p.w*dt)

    #calc flow at new location
    u3 = self.flow(p.pos)

    p.u = u3

    dw = u2 - u3
    p.w = self.addSI(p.w, dw)

    #calc new net velocity
    p.v = p.u + p.w

    p.t += dt
    if (1-(np.linalg.norm(p.w)**2)/C**2)<0.0:
      p.pt += 0.0
    else:
      p.pt += dt * math.sqrt(1-(np.linalg.norm(p.w)**2)/C**2)



class ExtraSpecialFlowCalculator(Calculator):
  runspeed = 60000

  def initPV(self, p, v):
    p.v = v
    p.u = self.flow(p.pos)
    p.w = self.addSI(-p.u, p.v)

  def initPW(self, p, w):
    p.w = w
    p.u = self.flow(p.pos)
    p.v = self.addSI(p.u, p.w)    
  
  def move(self, p, dt):
    debug=False
    
    if debug==True:
      print('pos:',p.pos)
      print('u:',p.u)
      print('w:',p.w)
      print('v:',p.v)
      print('')

    #move with space  
    p2 = p.pos + p.u*dt

  
    #calc u at this location
    u2 = self.flow(p2)

    if debug==True:
      print('pos2:', p2)
      print('u2',u2)
      print('')
          
    #move forward by  v 
    p.pos = p.pos + p.v*dt
    p.d += np.linalg.norm(p.v)*dt
    
    #pos = pos + 0.5*w*dt 

    #calc flow at new location
    u3 = self.flow(p.pos)

    if debug==True:
      print('pos3',p.pos)
      print('u3',u3)
      print('')

    #calc new velocities
    dw = u2 - u3
    p.w = self.addSI(p.w,dw)

    p.u = u3

    p.v = self.addSI(p.u, p.w)

    if debug==True:
      print('pos:',p.pos)
      print('u:',p.u)
      print('w:',p.w)
      print('v:',p.v)
    
    #update time and proper time
    p.t += dt
    if (1-(np.linalg.norm(p.w)**2)/C**2)<0.0:
      p.pt += 0.0
    else:
      p.pt += dt * math.sqrt(1-(np.linalg.norm(p.w)**2)/C**2)
   

class NewNewtonianFlowCalculator(Calculator):
  runspeed = 60000

  def initP(self, p, v):
    p.v = v
    p.u = self.flow(p.pos)
    p.w = p.v-p.u

  def initPFreefall(self, p):
    p.u = self.flow(p.pos)
    p.v = p.u
    p.w = 0.0   
    
class NewNewtonianFlowCalculator(Calculator):
  runspeed = 60000

  def initPV(self, p, v):
    p.v = v
    p.u = self.flow(p.pos)
    p.w = p.v-p.u

  def initPW(self, p, w):
    p.w = w
    p.u = self.flow(p.pos)
    p.v = p.w+p.u  

  def initPFreefall(self, p):
    p.u = self.flow(p.pos)
    p.v = p.u
    p.w = np.array([0.0, 0.0])   
    
  def move(self, p, dt):
##    print('initial pos', p.pos)
##    print('initial w', p.w)
##    print('initial u', p.u)
##    print('initial v', p.v)
    
    #move the space
    p2 = p.pos+p.u*dt
    

##    print('***',p2)
    
    #calc u at this location
    u2 = self.flow(p2)

    #move th particle
    p.pos = p.pos + p.v*dt
    p.d += np.linalg.norm(p.v*dt)
  
    #calc u at this location
    u3 = self.flow(p.pos)


    du = u2 - p.u
##    print(' u1', p.u, 'u2', u2, 'u3:', u3)
##    print(' du', du)      

    dw = u2 - u3
##    print(' dw', dw)
    p.w = p.w + dw  #this provides the rotation

    #calc new local velocities
    p.u = u3
    p.v = p.w + p.u


##    print('final pos', p.pos)
##    print('final w', p.w)
##    print('final u', p.u)
##    print('final v', p.v)    

    #calc time increment
    p.t += dt
    if (1-(np.linalg.norm(p.w)**2)/C**2)<0.0:
      p.pt += 0.0
    else:
      p.pt += dt * math.sqrt(1-(np.linalg.norm(p.w)**2)/C**2)  


class NewSpecialFlowCalculator(Calculator):
  runspeed = 60000

  def initPV(self, p, v):
    p.v = v
    p.u = self.flow(p.pos)
    p.w = p.v-p.u

  def initPW(self, p, w):
    p.w = w
    p.u = self.flow(p.pos)
    p.v = p.w+p.u  

  def initPFreefall(self, p):
    p.u = self.flow(p.pos)
    p.v = p.u
    p.w = np.array([0.0, 0.0])   
    
  def move(self, p, dt):
##    print('initial pos', p.pos)
##    print('initial w', p.w)
##    print('initial u', p.u)
##    print('initial v', p.v)
    
    #move the space
    p2 = p.pos+p.u*dt
    

##    print('***',p2)
    
    #calc u at this location
    u2 = self.flow(p2)

    #move th particle
    p.pos = p.pos + p.v*dt
    p.d += np.linalg.norm(p.v*dt)
  
    #calc u at this location
    u3 = self.flow(p.pos)


    du = u2 - p.u
##    print(' u1', p.u, 'u2', u2, 'u3:', u3)
##    print(' du', du)      

    dw = u2 - u3
##    print(' dw', dw)
    p.w = self.addSI(p.w, dw)  #this provides the rotation

    #calc new local velocities
    p.u = u3
    p.v = p.w + p.u


##    print('final pos', p.pos)
##    print('final w', p.w)
##    print('final u', p.u)
##    print('final v', p.v)    

    #calc time increment
    p.t += dt
    if (1-(np.linalg.norm(p.w)**2)/C**2)<0.0:
      p.pt += 0.0
    else:
      p.pt += dt * math.sqrt(1-(np.linalg.norm(p.w)**2)/C**2)


class SecondOrderSpecialFlowCalculator(NewSpecialFlowCalculator):
  """
  NewSpecialFlowCalculator's model with a second-order (midpoint) move step

  NewSpecialFlowCalculator.move changes w by u(x + u dt) - u(x + v dt) - the flow where space moves to less the flow
  where the particle moves to - with everything taken at the start of the step. as dt -> 0 that is
    dx/dt = v = w + u(x),   dw/dt = -(w . grad) u(x)   (the change added to w relativistically, addSI)
  but taking it all from the start of the step leaves an error of order dt in a whole run, so orbits drift outward
  (in compareSingleBodyOrbits, about 27,000 km an orbit at dt = 10 s, halving with dt)

  here each step first takes NewSpecialFlowCalculator's step for half of dt to reach the middle of the step, then
  takes the whole step from the start using the rates there: the particle moves at the middle velocity, and the
  change in w is the flow difference across the middle point, u(xm - wm dt/2) - u(xm + wm dt/2) (a centred
  difference). the change is worked out with addSI at the middle w and then added on, and proper time uses the
  middle w. the error in a whole run is then of order dt^2. light (|w| = c) is kept at exactly c

  a step costs 5 flow evaluations to NewSpecialFlowCalculator's 2
  """
  runspeed = 25000

  def move(self, p, dt):
    light = abs(np.linalg.norm(p.w) - C) < 1e-9*C

    #half a step the first-order way, to the middle of the step
    xm = p.pos + p.v*dt/2
    um = self.flow(xm)
    wm = self.addSI(p.w, self.flow(p.pos + p.u*dt/2) - um)
    vm = wm + um

    #the whole step from the start, at the middle's rates
    dw = self.flow(xm - wm*dt/2) - self.flow(xm + wm*dt/2)
    p.w = p.w + (self.addSI(wm, dw) - wm)   #the relativistic change at the middle w
    if light:
      p.w = p.w*C/np.linalg.norm(p.w)
    p.pos = p.pos + vm*dt
    p.d += np.linalg.norm(vm*dt)
    p.u = self.flow(p.pos)
    p.v = p.w + p.u

    p.t += dt
    s = 1 - (np.linalg.norm(wm)**2)/C**2
    if s > 0.0:
      p.pt += dt*math.sqrt(s)


class NewSpecialWhiteFlowCalculator(Calculator):
  runspeed = 60000

  def initPV(self, p, v):
    p.v = v
    p.u = self.flow(p.pos)
    p.w = p.v-p.u

  def initPW(self, p, w):
    p.w = w
    p.u = self.flow(p.pos)
    p.v = p.w+p.u  

  def initPFreefall(self, p):
    p.u = self.flow(p.pos)
    p.v = -2*p.u                              #changed for freefall
    p.w = p.v-p.u             #changed for freefall
    
  def move(self, p, dt):
##    print('initial pos', p.pos)
##    print('initial w', p.w)
##    print('initial u', p.u)
##    print('initial v', p.v)
    
    #move the space
    p2 = p.pos+p.u*dt
    

##    print('***',p2)
    
    #calc u at this location
    u2 = self.flow(p2)

    #move th particle
    p.pos = p.pos + p.v*dt
    p.d += np.linalg.norm(p.v*dt)
  
    #calc u at this location
    u3 = self.flow(p.pos)


    du = u2 - p.u
##    print(' u1', p.u, 'u2', u2, 'u3:', u3)
##    print(' du', du)      

    dw = u2 - u3
##    print(' dw', dw)
    p.w = self.addSI(p.w, dw)  #this provides the rotation

    #calc new local velocities
    p.u = u3
    p.v = p.w + p.u


##    print('final pos', p.pos)
##    print('final w', p.w)
##    print('final u', p.u)
##    print('final v', p.v)    

    #calc time increment
    p.t += dt
    if (1-(np.linalg.norm(p.w)**2)/C**2)<0.0:
      p.pt += 0.0
    else:
      p.pt += dt * math.sqrt(1-(np.linalg.norm(p.w)**2)/C**2)        

class NewExtraSpecialFlowCalculator(Calculator):
  runspeed = 60000

  def initPV(self, p, v):
    p.v = v
    p.u = self.flow(p.pos)
    p.w = self.addSI(p.v,p.u)

  def initPW(self, p, w):
    p.w = w
    p.u = self.flow(p.pos)
    p.v = self.addSI(p.w,p.u)  

  def initPFreefall(self, p):
    p.u = self.flow(p.pos)
    p.v = p.u
    p.w = np.array([0.0, 0.0])   
    
  def move(self, p, dt):
##    print('initial pos', p.pos)
##    print('initial w', p.w)
##    print('initial u', p.u)
##    print('initial v', p.v)
    
    #move the space
    p2 = p.pos+p.u*dt
    

##    print('***',p2)
    
    #calc u at this location
    u2 = self.flow(p2)

    #move th particle
    p.pos = p.pos + p.v*dt
    p.d += np.linalg.norm(p.v*dt)
  
    #calc u at this location
    u3 = self.flow(p.pos)


    du = u2 - p.u
##    print(' u1', p.u, 'u2', u2, 'u3:', u3)
##    print(' du', du)      

    dw = u2 - u3
##    print(' dw', dw)
    p.w = self.addSI(p.w, dw)  #this provides the rotation

    #calc new local velocities
    p.u = u3
    p.v = self.addSI(p.w,p.u)


##    print('final pos', p.pos)
##    print('final w', p.w)
##    print('final u', p.u)
##    print('final v', p.v)    

    #calc time increment
    p.t += dt
    if (1-(np.linalg.norm(p.w)**2)/C**2)<0.0:
      p.pt += 0.0
    else:
      p.pt += dt * math.sqrt(1-(np.linalg.norm(p.w)**2)/C**2)      

       
class WhiteFlowCalculator(Calculator):
  runspeed = 60000

  def initPV(self, p, v):
    p.v = v
    p.u = self.flow(p.pos)
    p.w = self.addSI(p.v,p.u)

  def initPW(self, p, w):
    p.w = w
    p.u = self.flow(p.pos)
    p.v = self.addSI(p.w,p.u)  

  def initPFreefall(self, p):
    p.u = self.flow(p.pos)
    p.v = p.u
    p.w = np.array([0.0, 0.0])   
    
  def move(self, p, dt):
##    print('initial pos', p.pos)
##    print('initial w', p.w)
##    print('initial u', p.u)
##    print('initial v', p.v)
    
    #move the space
    p2 = p.pos+p.u*dt
    

##    print('***',p2)
    
    #calc u at this location
    u2 = self.flow(p2)

    #move th particle
    p.pos = p.pos + p.v*dt
    p.d += np.linalg.norm(p.v*dt)
  
    #calc u at this location
    u3 = self.flow(p.pos)


    du = u2 - p.u
##    print(' u1', p.u, 'u2', u2, 'u3:', u3)
##    print(' du', du)      

    dw = u2 - u3
##    print(' dw', dw)
    p.w = self.addSI(p.w, dw)  #this provides the rotation

    #calc new local velocities
    p.u = u3
    p.v = self.addSI(p.w,p.u)


##    print('final pos', p.pos)
##    print('final w', p.w)
##    print('final u', p.u)
##    print('final v', p.v)    

    #calc time increment
    p.t += dt
    if (1-(np.linalg.norm(p.w)**2)/C**2)<0.0:
      p.pt += 0.0
    else:
      p.pt += dt * math.sqrt(1-(np.linalg.norm(p.w)**2)/C**2)      

       


