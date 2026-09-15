"""Independent profile, metric and R3 command replay checks."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
root=Path(__file__).resolve().parent
covered=len(sys.argv)>1 and sys.argv[1]=='covered'
run=root/('results/r3_covered_cycle_20260915_final' if covered else 'results/r3_ambient_cycle_20260915')
low,high=(9450,9550) if covered else (9025,9975)
m=pd.read_csv(run/'summary.csv').set_index('method');checks=[]
for name in ['BasePI','R3']:
 d=pd.read_csv(run/(name+'.csv'));t=d.time_s.to_numpy();q=t>=60
 assert len(d)==12001 and abs(t[-1]-180)<1e-9 and d.valid.eq(1).all()
 phase=np.mod(np.maximum(0,t-60),30)
 ref=low+(high-low)*np.minimum(phase/5,1)
 dec=phase>=15;ref[dec]=high-(high-low)*np.minimum((phase[dec]-15)/5,1)
 assert np.max(abs(d.DOB_request[q]-ref[q]))<1e-7
 assert np.max(abs(d.PTO_hp))==0
 e=d.Nmech-d.DOB_request
 rmse=np.sqrt(np.mean(e[q]**2));assert abs(rmse-m.loc[name,'rmse_rpm'])<1e-8
 ring=0
 for cycle in range(4):
  edges=np.array([0,5,15,20,30])+30*cycle
  for a,b in zip(edges[:-1],edges[1:]):
   seg=d[(t>=60+a-1e-8)&(t<60+b-1e-8)];fuel=seg.Wf.to_numpy()
   ring+=max(0,np.sum(np.abs(np.diff(fuel)))-abs(fuel[-1]-fuel[0]))
 assert abs(ring-m.loc[name,'segment_excess_TV_lbm_s'])<1e-8
 command_error=np.nan;integrator_error=np.nan
 if name=='R3':
  active=t>=45
  static=d.VF_setpoint-d.VR_integrator_error*d.VR_speed_slope
  accel=(d.VF_feedback-static)/d.VR_accel_slope
  accel=d.VF_acceleration.where(d.VR_fallback.eq(1),accel)
  p=.025*d.VR_integrator_error-.002*accel
  command_error=float((p[active]-d.VR_proportional_term[active]).abs().max())
  assert command_error<1e-7
  assert (d.VF_unsaturated[active]-d.VF_setpoint[active]-p[active]-d.VF_integral[active]).abs().max()<1e-7
  assert (np.clip(d.VF_unsaturated[active],.2,4)-d.VF_command[active]).abs().max()<1e-7
  gate=((d.VF_unsaturated<4)|(d.VR_integrator_error<0))&((d.VF_unsaturated>.2)|(d.VR_integrator_error>0))
  delta=d.VF_integral.shift(-1)-d.VF_integral
  integrator_error=float((delta[active]-.015*.1*d.VR_integrator_error[active]*gate[active]).dropna().abs().max())
  assert integrator_error<1e-7
 checks.append(dict(method=name,profile_error=float(np.max(abs(d.DOB_request[q]-ref[q]))),rmse_replay=rmse,ringing_replay=ring,proportional_error=command_error,integrator_error=integrator_error))
pd.DataFrame(checks).to_csv(run/'verification.csv',index=False)
print(pd.DataFrame(checks).to_string(index=False))
