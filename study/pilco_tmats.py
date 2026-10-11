"""PILCO-style exact Gaussian moment matching for the local T-MATS PI policy.
Run with the bundled Python and PYTHONPATH=tmp/pilco_deps. No plant surrogate
trace is reported as a T-MATS result. Frozen quadratic feedforward is reused.
"""
from pathlib import Path
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json
import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/pilco_quadratic_pi_20261010'
OLD=ROOT/'results/poly2_tune9250_20260915'
TS=.015

def load_data():
    xx=[]; yy=[]; tt=[]
    base=pd.read_csv(OLD/'candidate_00.csv')
    u0=float(base.loc[(base.time_s>55)&(base.time_s<60),'Wf'].mean())
    for k in [0,1,34]:
        d=pd.read_csv(OLD/f'candidate_{k:02d}.csv')
        n=(d.Nmech.to_numpy()-9250)/20
        lag=(d.Nmech.to_numpy()-d.DOB_sensed.to_numpy())/5
        x=np.column_stack([n,lag,(d.Wf.to_numpy()-u0)/.3,d.PTO_hp.to_numpy()/1537.67919457386])
        y=np.diff(x[:,:2],axis=0)
        t=d.time_s.to_numpy()[:-1]
        # Disjoint time windows; third pulse is held out before any policy fit.
        mask=((t>=69.9)&(t<=78))|((t>=89.9)&(t<=103))
        test=(t>=119.9)&(t<=138)
        xx.append(x[:-1][mask]); yy.append(y[mask]); tt.append((x[:-1][test],y[test]))
    return np.vstack(xx),np.vstack(yy),tt,u0

class GP:
    def fit(self,X,Y,n=40):
        self.lin=np.linalg.lstsq(np.c_[np.ones(len(X)),X],Y,rcond=None)[0]
        R=Y-np.c_[np.ones(len(X)),X]@self.lin
        self.scale=np.maximum(R.std(0),1e-5)
        # Deterministic farthest-point subset in physical standardized inputs.
        ids=[int(np.argmax(np.linalg.norm(X,axis=1)))]; dist=np.full(len(X),np.inf)
        for _ in range(n-1):
            dist=np.minimum(dist,np.sum((X-X[ids[-1]])**2,axis=1));ids.append(int(dist.argmax()))
        self.X=X[ids]; target=R[ids]/self.scale
        def kernel(h):
            ls=np.exp(h[:4]);sf=np.exp(2*h[4]);sn=np.exp(2*h[5])
            K=sf*np.exp(-.5*np.sum(((self.X[:,None]-self.X[None,:])/ls)**2,axis=2))
            return K+np.eye(n)*(sn+1e-9)
        def loss(h):
            try:
                c=cho_factor(kernel(h)); a=cho_solve(c,target)
                return .5*np.sum(target*a)+2*np.log(np.diag(c[0])).sum()
            except np.linalg.LinAlgError:return 1e10
        opt=minimize(loss,np.log([2,2,2,2,1,.1]),bounds=[(-1,4)]*4+[(-3,3),(-7,0)],method='L-BFGS-B')
        h=opt.x;self.L=np.diag(np.exp(2*h[:4]));self.sf=np.exp(2*h[4]);self.sn=np.exp(2*h[5])
        self.Ki=np.linalg.inv(kernel(h));self.beta=self.Ki@target
        self.mid=(self.X[:,None,:]+self.X[None,:,:])/2
        diff=self.X[:,None,:]-self.X[None,:,:]
        self.pair=np.exp(-.25*np.einsum('...i,ij,...j->...',diff,np.linalg.inv(self.L),diff))
        self.h=h
        return self

    def moments(self,m,S,Cxz):
        """Return mean, covariance, Cov(x,delta), for z Gaussian and Cov(x,z)."""
        R=np.linalg.inv(S+self.L);v=self.X-m
        q=self.sf*np.sqrt(np.linalg.det(self.L)/np.linalg.det(S+self.L))*np.exp(-.5*np.einsum('ni,ij,nj->n',v,R,v))
        R2=np.linalg.inv(S+self.L/2);w=self.mid-m
        Q=self.sf**2*np.sqrt(np.linalg.det(self.L/2)/np.linalg.det(S+self.L/2))*self.pair*np.exp(-.5*np.einsum('...i,ij,...j->...',w,R2,w))
        mg=q@self.beta
        Vg=self.beta.T@Q@self.beta-np.outer(mg,mg)
        Vg+=np.eye(2)*max(0,self.sf-np.sum(self.Ki*Q.T)+self.sn)
        grad=R@((v*q[:,None]).T@self.beta)*self.scale
        A=self.lin[1:].T
        Czg=S@grad
        mean=self.lin[0]+A@m+mg*self.scale
        cov=A@S@A.T+Vg*np.outer(self.scale,self.scale)+A@Czg+Czg.T@A.T
        return mean,(cov+cov.T)/2,Cxz@(A.T+grad)

    def predict(self,X):
        R=np.linalg.inv(self.L);v=X[:,None,:]-self.X
        k=self.sf*np.exp(-.5*np.einsum('...i,ij,...j->...',v,R,v))
        return np.c_[np.ones(len(X)),X]@self.lin+(k@self.beta)*self.scale

def rollout(gp,gains,save=False):
    kp,ki=gains
    # x = [speed deviation/20, sensor lag/5, integral correction/0.3].
    b=np.array([-kp*20/.3,kp*5/.3,1.])
    B=np.vstack(([1,0,0],[0,1,0],b,[0,0,0]))
    D=np.eye(3);D[2]=[-TS*ki*20/.3,TS*ki*5/.3,1]
    E=np.array([[1,0],[0,1],[0,0]])
    m=np.zeros(3);S=np.diag([1e-6,1e-6,1e-8]);cost=0;rows=[]
    for t in np.arange(0,5,TS):
        load=float(1<=t<2.5)
        mz=B@m+np.array([0,0,0,load]);Sz=B@S@B.T
        dm,V,C=gp.moments(mz,Sz,S@B.T)
        m=D@m+E@dm;S=D@S@D.T+E@V@E.T+D@C@E.T+E@C.T@D.T
        S=(S+S.T)/2
        if np.min(np.linalg.eigvalsh(S))< -1e-7 or np.max(np.diag(S))>1e4 or not np.isfinite(S).all():return 1e6,[]
        u=b@m;uv=b@S@b
        # Expected quadratic tracking + modest fuel correction penalty.
        cost+=TS*(m[0]**2+S[0,0]+.01*(u*u+uv))
        if save:rows.append([t,m[0]*20,np.sqrt(max(S[0,0],0))*20,u*.3,load])
    return cost,rows

def checks(gp):
    # Verify closed-form uncertain-input moments against Monte Carlo integration.
    rng=np.random.default_rng(20261010);m=gp.X[3];S=np.diag([.003,.002,.004,.001])
    mu,V,C=gp.moments(m,S,S)
    z=rng.multivariate_normal(m,S,50000);pred=gp.predict(z)
    v=z[:,None,:]-gp.X
    k=gp.sf*np.exp(-.5*np.einsum('...i,ij,...j->...',v,np.linalg.inv(gp.L),v))
    conditional=np.maximum(0,gp.sf-np.einsum('ni,ij,nj->n',k,gp.Ki,k)+gp.sn)
    mcV=np.cov(pred,rowvar=False)+np.diag(conditional.mean()*gp.scale**2)
    mcC=((z-z.mean(0)).T@(pred-pred.mean(0)))/(len(z)-1)
    result={'mean_max_abs_error':float(np.max(abs(mu-pred.mean(0)))),
            'covariance_relative_error':float(np.linalg.norm(V-mcV)/np.linalg.norm(V)),
            'cross_covariance_relative_error':float(np.linalg.norm(C-mcC)/np.linalg.norm(C))}
    assert result['covariance_relative_error']<.06 and result['cross_covariance_relative_error']<.06,result
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    X,Y,test,u0=load_data();gp=GP().fit(X,Y)
    np.savez(OUT/'dynamics_gp.npz',X=gp.X,lin=gp.lin,scale=gp.scale,h=gp.h,beta=gp.beta,Ki=gp.Ki)
    validation=[]
    for name,(x,y) in zip(['Base PI','Original Poly2','Retuned Poly2'],test):
        e=(gp.predict(x)-y)*[20,5]
        validation.append(dict(method=name,speed_increment_rmse_rpm=float(np.sqrt(np.mean(e[:,0]**2))),lag_increment_rmse_rpm=float(np.sqrt(np.mean(e[:,1]**2)))))
    pd.DataFrame(validation).to_csv(OUT/'gp_holdout.csv',index=False)
    check=checks(gp);(OUT/'moment_checks.json').write_text(json.dumps(check,indent=2))
    history=[]
    def objective(logg):
        g=np.exp(logg);j,_=rollout(gp,g);history.append([len(history),*g,j])
        if len(history)%10==0:print('POLICY',len(history),g,j,flush=True)
        return j
    initial=[.025,.05];initial_cost=objective(np.log(initial))
    opt=minimize(objective,np.log(initial),method='L-BFGS-B',bounds=np.log([[.005,.07],[.01,.25]]),options={'maxiter':35,'ftol':1e-9,'finite_diff_rel_step':1e-4})
    gains=np.exp(opt.x);cost,rows=rollout(gp,gains,True)
    pd.DataFrame(history,columns=['evaluation','Kp','Ki','expected_cost']).to_csv(OUT/'policy_search.csv',index=False)
    pd.DataFrame(rows,columns=['time_s','mean_speed_error_rpm','std_speed_rpm','fuel_correction_lbm_s','load_fraction_of_training']).to_csv(OUT/'predicted_rollout.csv',index=False)
    result=dict(Kp=float(gains[0]),Ki=float(gains[1]),Kd=0,initial_cost=float(initial_cost),selected_cost=float(cost),optimizer_success=bool(opt.success),optimizer_message=str(opt.message),u0=u0,training_transitions=len(X),gp_subset=len(gp.X),Ts=TS,method='PILCO-style analytic moment matching; numerical policy gradients; frozen quadratic feedforward')
    (OUT/'policy.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
