"""Independent particle check of the Gaussian-closure ringing prediction.
Samples the same GP's per-step conditional residual uncertainty; does not
sample a temporally coherent GP function or claim plant confidence coverage.
"""
import json
import numpy as np
from pilco_smooth import load_gp,rollout,OUT,TS
gp=load_gp();sel=json.loads((OUT/'selected_policy.json').read_text());g=[sel['Kp'],sel['Ki']]
_,analytic,_=rollout(gp,g,sel['weight'])
rng=np.random.default_rng(712);n=5000
x=rng.normal(size=(n,3))*np.sqrt([1e-6,1e-6,1e-8]);b=np.array([-g[0]*20/.3,g[0]*5/.3,1])
prev=x@b;anchor=prev.copy();tv=np.zeros(n);ring=np.zeros(n);group=-1
for t in np.arange(0,5,TS):
    window=0 if 1<=t<2.5 else (1 if t>=2.5 else -1)
    if window!=group:
        if group>=0:ring+=tv-abs(prev-anchor)
        tv=np.zeros(n);anchor=prev.copy();group=window
    u=x@b;z=np.column_stack([x[:,:2],u,np.full(n,float(1<=t<2.5))])
    diff=z[:,None]-gp.X
    k=gp.sf*np.exp(-.5*np.einsum('...i,ij,...j->...',diff,np.linalg.inv(gp.L),diff))
    mu=np.c_[np.ones(n),z]@gp.lin+(k@gp.beta)*gp.scale
    var=np.maximum(0,gp.sf-np.einsum('ni,ij,nj->n',k,gp.Ki,k)+gp.sn)
    inc=mu+rng.normal(size=(n,2))*np.sqrt(var[:,None])*gp.scale
    x[:,2]+=TS*g[1]*(-20*x[:,0]+5*x[:,1])/.3
    x[:,:2]+=inc;new=x@b
    if group>=0:tv+=abs(new-prev)
    prev=new
ring+=tv-abs(prev-anchor)
result=dict(particles=n,analytic_normalized=analytic['expected_ringing_normalized'],
            particle_mean_normalized=float(ring.mean()),particle_standard_error=float(ring.std(ddof=1)/np.sqrt(n)),
            relative_difference=float(abs(ring.mean()/analytic['expected_ringing_normalized']-1)),
            interpretation='Gaussian-closure cross-check on the same GP, not independent plant validation')
(OUT/'particle_check.json').write_text(json.dumps(result,indent=2));print(result)
