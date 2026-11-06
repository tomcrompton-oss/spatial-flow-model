"""
calculators no longer in use, kept from flow2.py when it became flow.py (see archive/ for the file as it was):
SpecialCalculator, NewtonianFlowCalculator, OldSpecialFlowCalculator (was SpecialFlowCalculator),
ExtraSpecialFlowCalculator, NewNewtonianFlowCalculator (two definitions; the second is the one Python used),
NewExtraSpecialFlowCalculator, WhiteFlowCalculator
"""
import math
import numpy as np
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
from engine.flow import Calculator
from engine.constants import *


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


class OldSpecialFlowCalculator(Calculator):   #was SpecialFlowCalculator, a name the new flow.py now uses
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
