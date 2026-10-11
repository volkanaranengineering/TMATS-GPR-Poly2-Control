"""One declared midpoint refinement of the 0.1--0.3 weight bracket.
Run after the coarse 10% sweep, before frozen-policy validation.
"""
import json
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from pilco_smooth import OUT,load_gp,rollout
p=json.loads((OUT/'protocol.json').read_text())
if len(p['weights'])==7:
    (OUT/'coarse_protocol.json').write_text(json.dumps(p,indent=2))
p['refinement_weights']=[.15,.2,.25]
p['refinement_reason']='One midpoint refinement of the coarse 0.1--0.3 tradeoff bracket; no 5% data used.'
p['weights']=[0,.001,.003,.01,.03,.1,.3,.15,.2,.25]
(OUT/'protocol.json').write_text(json.dumps(p,indent=2))
gp=load_gp();table=pd.read_csv(OUT/'candidates.csv');history=[]
for idx,w in enumerate(p['refinement_weights'],7):
    if idx in table.candidate.values:continue
    nearest=table.iloc[(table.weight-w).abs().argmin()];g=np.array([nearest.Kp,nearest.Ki])
    def objective(logg):
        g=np.exp(logg);j,_,_=rollout(gp,g,w);history.append(dict(candidate=idx,weight=w,Kp=g[0],Ki=g[1],cost=j));return j
    opt=minimize(objective,np.log(g),method='L-BFGS-B',bounds=np.log(p['gain_bounds']),options={'maxiter':35,'ftol':1e-9})
    g=np.exp(opt.x);j,comp,rows=rollout(gp,g,w,True)
    row=dict(candidate=idx,weight=w,Kp=g[0],Ki=g[1],Kd=0,cost=j,optimizer_success=bool(opt.success),message=str(opt.message),**comp)
    table=pd.concat([table,pd.DataFrame([row])],ignore_index=True);table.to_csv(OUT/'candidates.csv',index=False)
    pd.DataFrame(rows,columns=['time_s','mean_error_rpm','std_speed_rpm','fuel_correction_lbm_s','expected_abs_fuel_increment','load']).to_csv(OUT/f'prediction_{idx:02d}.csv',index=False)
    pd.DataFrame(history).to_csv(OUT/'refinement_history.csv',index=False);print(row,flush=True)
