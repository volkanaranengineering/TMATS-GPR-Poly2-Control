from pathlib import Path
import sys,json
import pandas as pd
import numpy as np
root=Path(__file__).resolve().parent;run=root/'results/r3_static_ff_20260915';prior=root/'results/r3_covered_cycle_20260915_final'
poly=len(sys.argv)>1 and sys.argv[1]=='poly'
if poly:run=root/'results/r3_poly2_challenger_20260915'
m=pd.read_csv(run/'summary.csv').set_index('method');checks=[]
methods=['BasePI','R3','R3_GPRFF']+(['R3_Poly2FF'] if poly else [])
for name in methods:
 d=pd.read_csv(run/(name+'.csv'));t=d.time_s.to_numpy();q=t>=60;phase=np.mod(np.maximum(0,t-60),30)
 ref=9450+100*np.minimum(phase/5,1);ix=phase>=15;ref[ix]=9550-100*np.minimum((phase[ix]-15)/5,1)
 assert len(d)==12001 and d.valid.eq(1).all() and m.loc[name,'accepted']==1
 assert np.max(abs(d.DOB_request[q]-ref[q]))<1e-7
 e=d.Nmech-d.DOB_request;assert abs(np.sqrt(np.mean(e[q]**2))-m.loc[name,'rmse_rpm'])<1e-8
 p_error=np.nan;u_error=np.nan;i_error=np.nan;equivalence=np.nan
 if name!='BasePI':
  active=t>=45;static=d.VF_setpoint-d.VR_integrator_error*d.VR_speed_slope
  agp=(d.VF_feedback-static)/d.VR_accel_slope;agp=d.VF_acceleration.where(d.VR_fallback.eq(1),agp)
  p=.025*d.VR_integrator_error-.002*agp
  p_error=float((p[active]-d.VR_proportional_term[active]).abs().max());assert p_error<1e-7
  ff=d.VF_setpoint if name in ['R3_GPRFF','R3_Poly2FF'] else np.zeros(len(d))
  assert np.max(abs(d.FF_total-ff))<1e-9
  u_error=float((d.VF_unsaturated[active]-d.FF_total[active]-p[active]-d.VF_integral[active]).abs().max());assert u_error<1e-7
  assert np.max(abs(np.clip(d.VF_unsaturated[active],.2,4)-d.VF_command[active]))<1e-7
  gate=((d.VF_unsaturated<4)|(d.VR_integrator_error<0))&((d.VF_unsaturated>.2)|(d.VR_integrator_error>0))
  i_error=float(((d.VF_integral.shift(-1)-d.VF_integral)[active]-.015*.1*d.VR_integrator_error[active]*gate[active]).dropna().abs().max());assert i_error<1e-7
 if name in ['BasePI','R3_GPRFF']:
  old=pd.read_csv(prior/('BasePI.csv' if name=='BasePI' else 'R3.csv'))
  equivalence=float(np.max(abs(old.Nmech-d.Nmech)));assert equivalence<1e-7
 if poly and name=='R3':
  old=pd.read_csv(root/'results/r3_static_ff_20260915/R3.csv');equivalence=float(np.max(abs(old.Nmech-d.Nmech)));assert equivalence<1e-7
 if name=='R3_Poly2FF':
  model=json.loads((root/'results/poly2_inverse_20260915/poly2_model.json').read_text());mean=np.array(model['inputMean']);scale=np.array(model['inputScale']);coef=np.array(model['coefficients']);pairs=np.array(model['pairs'])-1
  temp=d.inlet_temperature_K.shift(1).fillna(288.15).to_numpy();pressure=d.inlet_pressure_kPa.shift(1).fillna(99.298).to_numpy()
  for speed,accel,logged in [(d.DOB_request,np.zeros(len(d)),d.VF_setpoint),(d.DOB_sensed,d.VF_acceleration,d.VF_feedback)]:
   z=(np.column_stack([speed,accel,temp,pressure])-mean)/scale;A=np.column_stack([np.ones(len(d)),z,z*z]+[z[:,i]*z[:,j] for i,j in pairs]);assert np.max(abs(A@coef-logged))<1e-9
 checks.append(dict(method=name,proportional_error=p_error,command_error=u_error,integrator_error=i_error,previous_speed_equivalence_rpm=equivalence))
pd.DataFrame(checks).to_csv(run/'verification.csv',index=False);print(pd.DataFrame(checks).to_string(index=False))
