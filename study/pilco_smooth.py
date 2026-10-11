"""Frozen GP policy learning with uncertainty-aware excess total variation.
Augments state with previous fuel and an event-start fuel anchor. Never uses
5% plant validation to optimize or select a controller.
"""
from pathlib import Path
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json
import numpy as np
import pandas as pd
from scipy.special import erf
from scipy.optimize import minimize
from pilco_tmats import GP,ROOT,TS
OUT=ROOT/'results/pilco_smooth_20261010'

def load_gp():
    s=np.load(ROOT/'results/pilco_quadratic_pi_20261010/dynamics_gp.npz')
    gp=GP()
    for k in ['X','lin','scale','h','beta','Ki']:setattr(gp,k,s[k])
    gp.L=np.diag(np.exp(2*gp.h[:4]));gp.sf=np.exp(2*gp.h[4]);gp.sn=np.exp(2*gp.h[5])
    gp.mid=(gp.X[:,None,:]+gp.X[None,:,:])/2
    delta=gp.X[:,None,:]-gp.X[None,:,:]
    gp.pair=np.exp(-.25*np.einsum('...i,ij,...j->...',delta,np.linalg.inv(gp.L),delta))
    return gp

def abs_gaussian(mu,var):
    if var<1e-16:return abs(mu)
    sd=np.sqrt(max(var,0))
    return sd*np.sqrt(2/np.pi)*np.exp(-mu*mu/(2*var))+mu*erf(mu/(np.sqrt(2)*sd))

def rollout(gp,gains,weight,save=False):
    kp,ki=gains
    b=np.array([-kp*20/.3,kp*5/.3,1.,0,0])
    B=np.vstack(([1,0,0,0,0],[0,1,0,0,0],b,[0,0,0,0,0]))
    D=np.eye(5);D[2]=[-TS*ki*20/.3,TS*ki*5/.3,1,0,0];D[3]=b
    E=np.zeros((5,2));E[:2]=np.eye(2)
    m=np.zeros(5);S=np.diag([1e-6,1e-6,1e-8,0,0])
    # Previous command and anchor equal initial policy output, including covariance.
    T=np.eye(5);T[3]=b;T[4]=b;S=T@S@T.T
    delta=b-np.eye(5)[3];net=b-np.eye(5)[4]
    tracking=0;effort=0;ring=0;tv=0;window=-1;rows=[]
    times=np.arange(0,5,TS)
    for j,t in enumerate(times):
        group=0 if 1<=t<2.5 else (1 if t>=2.5 else -1)
        if group!=window:
            if window>=0:ring+=tv-abs_gaussian(net@m,net@S@net)
            T=np.eye(5);T[4]=b;m=T@m;S=T@S@T.T
            tv=0;window=group
        load=float(1<=t<2.5)
        dm,V,C=gp.moments(B@m+np.array([0,0,0,load]),B@S@B.T,S@B.T)
        m=D@m+E@dm;S=D@S@D.T+E@V@E.T+D@C@E.T+E@C.T@D.T
        S=(S+S.T)/2
        if not np.isfinite(S).all() or np.max(np.diag(S))>1e4 or np.linalg.eigvalsh(S).min() < -1e-7:
            return 1e6,{},[]
        u=b@m;uv=b@S@b
        tracking+=TS*(m[0]**2+S[0,0]);effort+=TS*.01*(u*u+uv)
        dv=abs_gaussian(delta@m,delta@S@delta)
        if window>=0:tv+=dv
        if save:rows.append([t,m[0]*20,np.sqrt(max(0,S[0,0]))*20,u*.3,dv*.3,load])
    ring+=tv-abs_gaussian(net@m,net@S@net)
    # Moment closure can introduce a tiny nonphysical negative remainder.
    ring=max(0,ring)
    return tracking+effort+weight*ring,dict(tracking_cost=tracking,effort_cost=effort,expected_ringing_normalized=ring,expected_ringing_lbm_s=.3*ring),rows

def checks():
    rng=np.random.default_rng(401)
    tests=[]
    for mu,var in [(0,.2),(.3,.1),(-.4,.02),(1,0)]:
        z=rng.normal(mu,np.sqrt(var),250000)
        exact=abs_gaussian(mu,var);mc=np.abs(z).mean()
        assert abs(exact-mc)<.004
        tests.append(dict(mean=mu,variance=var,analytic=exact,monte_carlo=mc))
    # Deterministic event accounting: monotone motion has zero ringing,
    # while a 0->1->0->1 command path has 2 units of excess variation.
    for path,expected in [([0,.5,1],0),([0,1,0,1],2)]:
        assert abs(np.abs(np.diff(path)).sum()-abs(path[-1]-path[0])-expected)<1e-12
    return tests

def main():
    OUT.mkdir(exist_ok=True,parents=True);gp=load_gp()
    (OUT/'penalty_checks.json').write_text(json.dumps(checks(),indent=2))
    protocol=dict(weights=[0,.001,.003,.01,.03,.1,.3],gain_bounds=[[.005,.07],[.01,.25]],
                  selection='Minimum max(RMSE/base_PI_RMSE, ringing/base_PI_ringing) among valid 10% simulations; 5% data excluded.',
                  base_rmse=2.42090390645681,base_ringing=2.07022804171342,
                  GP='Unchanged frozen GP from preceding study',planning_horizon_s=5,Ts=TS)
    (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2))
    history=[];records=[]
    original=json.loads((ROOT/'results/pilco_quadratic_pi_20261010/policy.json').read_text())
    g=np.array([original['Kp'],original['Ki']])
    for idx,w in enumerate(protocol['weights']):
        def objective(logg):
            gains=np.exp(logg);cost,comp,_=rollout(gp,gains,w)
            history.append(dict(candidate=idx,weight=w,Kp=gains[0],Ki=gains[1],cost=cost))
            return cost
        if w==0:
            success=True;message='Frozen previous tracking-only policy'
        else:
            opt=minimize(objective,np.log(g),method='L-BFGS-B',bounds=np.log(protocol['gain_bounds']),options={'maxiter':35,'ftol':1e-9})
            g=np.exp(opt.x);success=bool(opt.success);message=str(opt.message)
        cost,parts,rows=rollout(gp,g,w,True)
        records.append(dict(candidate=idx,weight=w,Kp=g[0],Ki=g[1],Kd=0,cost=cost,optimizer_success=success,message=message,**parts))
        pd.DataFrame(rows,columns=['time_s','mean_error_rpm','std_speed_rpm','fuel_correction_lbm_s','expected_abs_fuel_increment','load']).to_csv(OUT/f'prediction_{idx:02d}.csv',index=False)
        pd.DataFrame(records).to_csv(OUT/'candidates.csv',index=False)
        pd.DataFrame(history).to_csv(OUT/'optimization_history.csv',index=False)
        print('SMOOTH_POLICY',records[-1],flush=True)
if __name__=='__main__':main()
