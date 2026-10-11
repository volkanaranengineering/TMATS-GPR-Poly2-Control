"""Independent filter replay and selected-loop validity checks."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.signal import lfilter
P=Path(__file__).resolve().parent/'results/dob98_pi_20261010'

def main():
    c=json.loads((P/'identified_model.json').read_text());s=json.loads((P/'selected_policy.json').read_text())
    p=np.exp(-c['Ts']/.05);r=np.exp(-2*np.pi*c['fc_Hz']*c['Ts'])
    den=np.array([1,-2*r,r*r]);num=np.convolve([1,-c['a']],[1,-p])*(1-r)**2/(c['b']*(1-p));qn=[0,0,(1-r)**2]
    # Exact frequency-domain identity for the implemented nominal plant and sensor.
    q=np.exp(-1j*np.linspace(.001,np.pi,1000));pn=c['b']*q/(1-c['a']*q);h=q*(1-p)/(1-p*q)
    poly=lambda coef:sum(x*q**i for i,x in enumerate(coef))
    identity=float(np.max(abs(poly(num)/poly(den)*pn*h-poly(qn)/poly(den))))
    assert identity<1e-10
    checks=[]
    for filename in ['dobpi.csv','case_100.csv']:
        d=pd.read_csv(P/filename);t=d.time_s.to_numpy();mask=t>=60
        raw=lfilter(num,den,d.DOB_sensed-c['N0'])-lfilter(qn,den,d.DOB_command-c['u0'])
        baseline=raw[np.flatnonzero(t<45)[-1]];estimate=raw-baseline
        # Trim latch stores the last pre-engagement estimate.
        replay=float(np.max(abs(estimate[mask]-d.DOB_estimate[mask])))
        assert replay<1e-6,replay
        comp=np.clip(.7*estimate[mask],-1,1)
        assert np.max(abs(comp-d.DOB_compensation[mask]))<1e-6
        assert d.valid.eq(1).all() and t[-1]>=85
        assert abs(d.Nmech[(t>=55)&(t<60)]-9000).max()<.1
        assert abs(d.DOB_compensation[mask]).max()<=1+1e-10
        checks.append(dict(trace=filename,all_valid=True,max_inverse_replay_error_lbm_s=replay,peak_compensation=float(abs(d.DOB_compensation[mask]).max())))
    result=dict(nominal_pole=c['a'],filter_pole=float(r),inverse_identity_max_error=identity,cases=checks)
    (P/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
