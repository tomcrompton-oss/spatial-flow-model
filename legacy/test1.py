import math
import numpy as np
import time

pos = np.array([-1000.0, 100.0])
v = np.array([0.1, 0.0])
a = np.array([0.0, 0.0])



def add(u, v):
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
   C=3e8
   u = u/C
   v = v/C
   upar = v * np.dot(u,v) / np.dot(v, v)
   uper = u-upar

   wpar = (upar+v) / (1+np.dot(v, upar))
   L = math.sqrt(1-np.linalg.norm(v)**2)
   wper =  (L * uper)/ (1+np.dot(v, upar))
   
   w = wpar + wper
   return w*C

#pure newtonian
#TODO parameterise
def newtonianSI():
  G = 6.6743E-11
  M = 1.989E30
  GM = G*M
  R = 70000000000 #70M km at furthest point
  V = 38860 #38.86 km/s at slowest speed
  pos = np.array([0, R])
  b = abs(pos[0])
  v = np.array([V, 0.0])
  a = np.array([0.0, 0.0])
  dt=60*60
  for t in range(0, (100*24*60*60), dt):
    pos = pos + v*dt
    d = np.linalg.norm(pos)
    #g = GM/d**2
    g = GM/d**2 
    #print('g=',g,'d=',d)
    a = -g * pos/d
    v = v + a * dt
    speed = np.linalg.norm(v)
    #print(a,' ',v)
    #print(t,' ',d,' ',pos,' ',v)
    if(t%(24*60*60)==0):
      #print(t,',',pos[0],',',pos[1],' g=',g, 'speed=',speed)
      print(pos[0],',',pos[1])
  #TODO calculate deflection

#pure newtonian
#SI Units
def newtonianSIMercury():
  G = 6.6743E-11
  M = 1.989E30
  GM = G*M
  R = 70000000000 #mercury
  V = 38860 #mercury
  pos = np.array([0, R])
  oldpos = np.array([0, R])
  b = abs(pos[0])
  v = np.array([V, 0.0])
  a = np.array([0.0, 0.0])
  orbit=0
  max=0
  dt=1
  for t in range(0, (1000*24*60*60), dt):
    oldpos = pos.copy()
    pos = pos + v*dt
    d = np.linalg.norm(pos)
    if(d>max):
      maxpos = pos.copy()
      max=d
    #g = GM/d**2
    g = GM/d**2 
    #print('g=',g,'d=',d)
    a = -g * pos/d
    v = v + a * dt
    speed = np.linalg.norm(v)
    #print(a,' ',v)
    #print(t,' ',d,' ',pos,' ',v)
    if(oldpos[0]<0 and pos[0]>=0):
       #orbit completed
      orbit=orbit+1
      print('orbit',orbit,'maxpos',maxpos)
      max=0
    #if(t%(24*60*60)==0):
      #print(t,',',pos[0],',',pos[1],' g=',g, 'speed=',speed)
      #print(pos[0],',',pos[1])
  #TODO calculate deflection

#pure newtonian
#TODO parameterise
def specialSIExagerated():
  G = 6.6743E-11
  M = 1.989E30
  GM = G*M
  R = 70000000000/4 #4x closer than mercury
  V = 38860*2 #2x speed of mercury
  pos = np.array([0, R])
  oldpos = np.array([0, R])
  b = abs(pos[0])
  v = np.array([V, 0.0])
  u = np.array([0.0, 0.0])
  u2 = np.array([0.0, 0.0])
  du = np.array([0.0, 0.0])
  a = np.array([0.0, 0.0])
  orbit=0
  max=0
  dt=60*60
  for t in range(0, (50000*24*60*60), dt):
    oldpos = pos.copy()
    d = np.linalg.norm(pos)
    #print(d)

    u2 = u.copy()
    #print('u2 ',u2[0],' ',u2[1])

    u[0] = -(1/math.sqrt(d)) * pos[0]/d
    u[1] = -(1/math.sqrt(d)) * pos[1]/d
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
      print('orbit',orbit,'maxpos',maxpos)
      max=0
    #if(t%(24*60*60)==0):
      #print(t,',',pos[0],',',pos[1],' g=',g, 'speed=',speed)
      #print(pos[0],',',pos[1])
  #TODO calculate deflection

#pure newtonian
#TODO parameterise
def specialSIMercury():
  C=3E8
  G = 6.6743E-11
  M = 1.989E30
  GM = G*M
  R = 70000000000/9 #mercury
  V = 38860*3 #mercury
  pos = np.array([0, R])
  d = np.linalg.norm(pos)

  oldpos = np.array([0, R])
  b = abs(pos[0])
  v = np.array([V, 0.0])
  u = np.array([0.0, 0.0])
  #u[0] = -math.sqrt(2*GM/d) * pos[0]/d
  #u[1] = -math.sqrt(2*GM/d) * pos[1]/d
  u2 = np.array([0.0, 0.0])
  du = np.array([0.0, 0.0])
  a = np.array([0.0, 0.0])

  perihelion=[]
  aphelion=[]
  
  orbit=0
  max=0
  min=R
  dt=0.01
  maxn=int((30*24*60*60)/dt)
  t=0
  starttime=time.time()
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
      total=math.acos(maxpos[1]/max)
      total2=math.pi-math.acos(minpos[1]/min)
      sma=(min+max)/2
      e=1-2/(max/min+1)
      max=0
      min=R
    #if(t%(24*60*60)==0):
      #print(t,',',pos[0],',',pos[1],' g=',g, 'speed=',speed)
      #print(pos[0],',',pos[1])
  print('t', t, 'orbits:',orbit,' av',t/(24*60*60*orbit),' days')
  period = 2*math.pi*math.sqrt(sma**3/GM)
  print('period', period,' ',period/(24*60*60),' days')

  print('eccentricity', e)
  p = (24*math.pi**3)*(sma**2)/(period**2 * C**2 * (1-e**2)) #todo calc ecentricity
  print('precession: ',p)
  print('total precision:', p*orbit, 'sim(max)',total,'sim(min)',total2)
                      
   
  #TODO calculate deflection



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


a = np.array([1.0, 0.0])
b = np.array([0.0, 0.5])
add(a,b)




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
    
  print(t,' pos: ',pos,' v ',v,' b ',b)
  #TODO calculate deflection

    
#TODO SR + crompton affect



#print(math.sqrt(0.99596**2 + 0.0897775**2))
#cromptonian()
specialSIMercury()
#newtonianSIMercury()
