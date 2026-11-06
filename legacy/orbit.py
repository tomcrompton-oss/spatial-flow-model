import math
from constants import *

##x=0.0
##y=AU
##vx=30000.0
##vy=0.0
##for i in range(365*24*60*60):
##   x = x + vx
##   y = y + vy
##   d = math.sqrt(x**2+y**2)
##   g = GM/(d**2)
##   gx = -g*x/d
##   gy = -g*y/d
##   vx = vx + gx
##   vy = vy + gy
##   if(i%(7*24*60*60)==0):
##     print('x:',x/AU,'y:',y/AU, 'v:', int(math.sqrt(vx**2+vy**2)), 'vx:', int(vx), 'vy:', int(vy))


x=0.0
y=AU
vx=38000.0
vy=0.0
k = 100.0

for i in range(5*365*24*60*60):
   x = x + vx
   y = y + vy
   d = math.sqrt(x**2+y**2)

   ##kx = -k*x/d
   ##ky = -k*y/d
   
   ##x = x + kx
   ##y = y + ky
   

   g = GM/(d**2)
   gx = -g*x/d
   gy = -g*y/d
   vx = vx + gx
   vy = vy + gy
   if(i%(30*24*60*60)==0):
     #print('x:',x/AU,'y:',y/AU, 'v:', int(math.sqrt(vx**2+vy**2)), 'vx:', int(vx), 'vy:', int(vy))
    #print('d:', d/AU, "v:", int(math.sqrt(vx**2+vy**2)))
    print(x,',',y)
