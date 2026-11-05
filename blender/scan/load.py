import numpy as np
def load_ply(p):
    with open(p,'rb') as f:
        n=0
        while True:
            l=f.readline()
            if l.startswith(b'element vertex'): n=int(l.split()[2])
            if l.startswith(b'end_header'): break
        dt=np.dtype([('x','<f4'),('y','<f4'),('z','<f4'),('r','u1'),('g','u1'),('b','u1')])
        a=np.fromfile(f,dtype=dt,count=n)
    xyz=np.stack([a['x'],a['y'],a['z']],1).astype(np.float64)
    rgb=np.stack([a['r'],a['g'],a['b']],1)
    return xyz,rgb
