from pathlib import Path
import pandas as pd
import numpy as np
root=Path(__file__).resolve().parent;run=root/'results/poly2_tune9250_20260915';m=pd.read_csv(run/'summary.csv').set_index('candidate');checks=[]
for path in sorted(run.glob('candidate_*.csv')):
 idx=int(path.stem.split('_')[1]);d=pd.read_csv(path);z=m.loc[idx]
 if not z.accepted:continue
 q=d.time_s>=60;e=d.Nmech[q]-9250;assert abs(np.sqrt(np.mean(e*e))-z.rmse_rpm)<1e-8
 ring=0
 for edge in [70.005,75,90,100.005,120,135]:
  fuel=d.Wf[(d.time_s>=edge-1e-8)&(d.time_s<=edge+2+1e-8)].to_numpy();ring+=max(0,np.abs(np.diff(fuel)).sum()-abs(fuel[-1]-fuel[0]))
 assert abs(ring-z.ringing_excess_TV_lbm_s)<1e-8
 pe=ue=ie=np.nan
 if idx>0:
  active=d.time_s>=45;static=d.VF_setpoint-d.VR_integrator_error*d.VR_speed_slope;accel=(d.VF_feedback-static)/d.VR_accel_slope;accel=d.VF_acceleration.where(d.VR_fallback.eq(1),accel)
  p=z.Kp*d.VR_integrator_error-z.Kd*accel;pe=float((p[active]-d.VR_proportional_term[active]).abs().max());ue=float((d.VF_unsaturated[active]-d.VF_setpoint[active]-p[active]-d.VF_integral[active]).abs().max())
  gate=((d.VF_unsaturated<4)|(d.VR_integrator_error<0))&((d.VF_unsaturated>.2)|(d.VR_integrator_error>0));ie=float(((d.VF_integral.shift(-1)-d.VF_integral)[active]-.015*z.Ki*d.VR_integrator_error[active]*gate[active]).dropna().abs().max())
  assert max(pe,ue,ie)<1e-7;assert (np.clip(d.VF_unsaturated[active],.2,4)-d.VF_command[active]).abs().max()<1e-7
 checks.append(dict(candidate=idx,proportional_error=pe,command_error=ue,integrator_error=ie))
pd.DataFrame(checks).to_csv(run/'verification.csv',index=False);print('Verified',len(checks),'accepted trajectories; maxima:',pd.DataFrame(checks).drop(columns='candidate').max().to_dict())
