"""Local speed ARX identification at 9800 rpm; independent free-run validation."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.signal import lfilter
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/dob98_pi_20261010'

def main():
    train=pd.read_csv(OUT/'identification_1.csv');val=pd.read_csv(OUT/'identification_2.csv')
    trim=train[(train.time_s>=55)&(train.time_s<60)]
    n0=float(trim.Nmech.mean());u0=float(trim.Wf.mean());ts=.015
    q=(train.time_s>=60)&(train.time_s<=90);d=train[q]
    y=d.Nmech.to_numpy()-n0;u=d.Wf.to_numpy()-u0
    # Minimum-phase one-pole model: y[k+1] = a*y[k] + b*u[k].
    a,b=np.linalg.lstsq(np.column_stack([y[:-1],u[:-1]]),y[1:],rcond=None)[0]
    assert 0<a<1 and b>0,(a,b)
    scores=[]
    for name,df in [('train',train),('validation',val)]:
        d=df[(df.time_s>=60)&(df.time_s<=100.005)].copy()
        yy=d.Nmech.to_numpy()-n0;uu=d.Wf.to_numpy()-u0;pred=np.empty_like(yy);pred[0]=yy[0]
        for k in range(1,len(yy)):pred[k]=a*pred[k-1]+b*uu[k-1]
        one=a*yy[:-1]+b*uu[:-1]
        fit=100*(1-np.linalg.norm(yy-pred)/np.linalg.norm(yy-yy.mean()))
        scores.append(dict(dataset=name,free_run_fit_pct=float(fit),free_run_rmse_rpm=float(np.sqrt(np.mean((yy-pred)**2))),one_step_rmse_rpm=float(np.sqrt(np.mean((yy[1:]-one)**2)))))
        pd.DataFrame(dict(time_s=d.time_s,actual_rpm=yy+n0,predicted_rpm=pred+n0,fuel_lbm_s=uu+u0)).to_csv(OUT/f'{name}_prediction.csv',index=False)
    # A poor inverse must not silently proceed to controller tuning.
    assert scores[1]['free_run_fit_pct']>85,scores
    excited=train[(train.time_s>=60)&(train.time_s<90)]
    model=dict(N0=n0,u0=u0,Ts=ts,A=[1.,float(-a)],B=[0.,float(b)],a=float(a),b=float(b),sensor_tau_s=.05,fc_Hz=1.,dob_gain=.7,compensation_limit_lbm_s=1.,structure='local one-pole speed model, one-sample fuel delay; identified using actual shaft speed and applied fuel',scores=scores,identification_speed_range_rpm=[float(excited.Nmech.min()),float(excited.Nmech.max())])
    (OUT/'identified_model.json').write_text(json.dumps(model,indent=2));print(json.dumps(model,indent=2))

if __name__=='__main__':main()
