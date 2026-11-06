import math
from constants import *

GM = G*MS*4000000          #Convenience
rs = 2*GM/C**2

def descentAndSignal(r1, r2):
    #descent
    cta = (1/C)*( (-2/(3*rs**0.5)) * (r2**1.5 - r1**1.5 + 3*rs*r2**0.5 -3*rs*r1**0.5))
    ctb = (rs/C)*math.log( ((r2**0.5+rs**0.5)*(r1**0.5-rs**0.5)) / ((r1**0.5+rs**0.5)*(r2**0.5-rs**0.5)) )
    ct = cta+ctb

    #signal
    lt = (r1-r2)/C
    dlt = (rs/C)*math.log((r1-rs)/(r2-rs))
    
    return ct+lt+dlt

def ascentAndSignal(r1, r2):
    #ascent - mirror of descent time
    cta = (1/C)*( (-2/(3*rs**0.5)) * (r2**1.5 - r1**1.5 + 3*rs*r2**0.5 -3*rs*r1**0.5))
    ctb = (rs/C)*math.log( ((r2**0.5+rs**0.5)*(r1**0.5-rs**0.5)) / ((r1**0.5+rs**0.5)*(r2**0.5-rs**0.5)) )
    ct = cta+ctb

    #signal
    lt = (r1-r2)/C
    dlt = (rs/C)*math.log((r1-rs)/(r2-rs))
    
    return ct+lt+dlt


def example():
    print("descent")
    print(descentAndSignal(AU, 0.8839195992857737*AU))
    print(descentAndSignal(AU, 0.7596304209992102*AU))
    print(descentAndSignal(AU, 0.6241550544271302*AU))
    print(descentAndSignal(AU, 0.47186860049026313*AU))
    print(descentAndSignal(AU, 0.2887668096132135*AU))

    print("closest point")
    r1 = AU
    r2 = 0.079*AU
    cta = (1/C)*( (-2/(3*rs**0.5)) * (r2**1.5 - r1**1.5 + 3*rs*r2**0.5 -3*rs*r1**0.5))
    ctb = (rs/C)*math.log( ((r2**0.5+rs**0.5)*(r1**0.5-rs**0.5)) / ((r1**0.5+rs**0.5)*(r2**0.5-rs**0.5)) )
    ct = cta+ctb
    print(ct)
    print(descentAndSignal(AU, 0.079*AU))
          
    print("ascent")
    print(ct+ascentAndSignal(45803605085.5435, 0.079*AU) )
    print(ct+ascentAndSignal(72443959582.24318, 0.079*AU) )
    print(ct+ascentAndSignal(94677941427.6674, 0.079*AU) )
    print(ct+ascentAndSignal(114482413563.1563, 0.079*AU) )
    print(ct+ascentAndSignal(132692754875.6488, 0.079*AU) )
    
    
    



    #0.8839195992857737
##    0.7596304209992102
##    0.6241550544271302
##    0.47186860049026313
##    0.2887668096132135
##    0.079




example()




r1 = 1.025 * AU
r2 = 0.227*AU

print("rs", rs, rs/AU, 'AU')
print("r2-rs", r2-rs)

#proper time calculation
pt = (2/(3*C*math.sqrt(rs))) * (r1**1.5 - r2**1.5)
print("proper time:", pt)



#time for light message
lt = (r1-r2)/C
dlt = (rs/C)*math.log((r1-rs)/(r2-rs))

print("light time (non-GR)", lt)
print('***********************')
print("light time", lt+dlt)
print('delta', dlt)


#coordinate time
cta = (1/C)*( (-2/(3*rs**0.5)) * (r2**1.5 - r1**1.5 + 3*rs*r2**0.5 -3*rs*r1**0.5))
ctb = (rs/C)*math.log( ((r2**0.5+rs**0.5)*(r1**0.5-rs**0.5)) / ((r1**0.5+rs**0.5)*(r2**0.5-rs**0.5)) )
ct = cta+ctb
print('***********************')
print("coord time:", ct)
print("coord time+light:", ct+lt+dlt)

#print("coord time:", pt+lt)

#new coord calc
r=r2
r0=r1
coordtA = -2/(3*C*rs**0.5) * (r**1.5 - r0**1.5 +3*rs*r**0.5 - 3*rs*r0**0.5)
coordtB = (rs/C)*math.log( ( (r**0.5+rs**0.5)*(r0**0.5-rs**0.5) / ((r0**0.5+rs**0.5)*(r**0.5-rs**0.5)) ))
print("new coord time:", coordtA+coordtB)                          


u1 = math.sqrt(2*GM/r1)
u2 = math.sqrt(2*GM/r2)


L1 = math.sqrt(1-u1**2/C**2)
L2 = math.sqrt(1-u2**2/C**2)


print("coord time:", ct, ct/L1)

print("coord time light received:", pt+lt, (pt+lt)/L1)
print('location 1: r:', r1,r1/AU, 'u:', u1,u1/C, 'L', L1)
print('location 2: r:', r2,r2/AU, 'u:', u2,u2/C, 'L', L2)


print('w', 299792458/C)
print('u', -2.76252827e+08/C)
print('v', 23539631.35379308/C)
print('u+w', -2.76252827e+08/C + 299792458/C)


print(0.24790915896960541-0.24791618379254032)

print(AU/C)


