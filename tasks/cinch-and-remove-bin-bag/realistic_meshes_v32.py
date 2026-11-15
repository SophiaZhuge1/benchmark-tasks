"""Open loaded drawstring bag with an unfolded neck free of the bin rim.

Mesh positions are authored only at reset. Dimensions are metres; the extended neck supplies film length needed for closure.
"""
import numpy as np

SUBDIVISION=0

def dirty_mesh():
    n=80
    rings=[(.086*t/4,0.) for t in range(1,5)]
    rings += [(.086,.135*t/9) for t in range(1,10)]
    rings += [(float(r),float(z)) for r,z in zip(np.linspace(.086,.090,12)[1:],np.linspace(.135,.250,12)[1:])]
    v=[[0.,0.,0.]]
    for r,z in rings:
        v.extend([[r*np.cos(j*2*np.pi/n),r*np.sin(j*2*np.pi/n),z] for j in range(n)])
    f=[[0,1+(j+1)%n,1+j] for j in range(n)]
    for k in range(len(rings)-1):
        a=1+k*n;b=a+n
        for j in range(n):
            q=(j+1)%n;f.extend([[a+j,a+q,b+j],[a+q,b+q,b+j]])
    return np.array(v),np.array(f),np.arange(1+(len(rings)-1)*n,1+len(rings)*n)
