"""Replay command algebra and discrete anti-windup integration from saved traces."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
r=Path(Path('tmp/remedies_directory.txt').read_text().strip())
phase=sys.argv[1] if len(sys.argv)>1 else 'tune'
files=sorted(r.glob(phase+'_e*_c*.csv'))
if phase=='tune':params=pd.read_csv(r/'tuning_summary.csv').set_index('candidate')
else:params=pd.concat([pd.read_csv(f) for f in r.glob(phase+'_worker_*.csv')]).drop_duplicates(['environment','candidate']).set_index(['environment','candidate'])
stats=[]
for f in files:
 env=int(f.stem.split('_e')[1][:2]);candidate=int(f.stem.split('_c')[1]);z=params.loc[candidate] if phase=='tune' else params.loc[(env,candidate)]
 d=pd.read_csv(f);a=(d.time_s>=45)&d.valid.eq(1);kp=z.Kp;ki=z.Ki;mode=z['mode'];beta=z.get('accelWeight',1)
 if pd.isna(beta):beta=1
 if mode==1:pred=kp*d.VF_error
 elif mode==2:pred=kp*((1-beta)*d.VR_integrator_error+beta*d.VF_error)
 else:
  static=d.VF_setpoint-d.VR_integrator_error*d.VR_speed_slope
  accel=(d.VF_feedback-static)/d.VR_accel_slope
  accel=d.VF_acceleration.where(d.VR_fallback.eq(1),accel)
  pred=kp*d.VR_integrator_error-z.Kd*accel
 p_error=float((pred[a]-d.VR_proportional_term[a]).abs().max())
 u_error=float((d.VF_setpoint[a]+d.VR_proportional_term[a]+d.VF_integral[a]-d.VF_unsaturated[a]).abs().max())
 sat_error=float((np.clip(d.VF_unsaturated[a],.2,4)-d.VF_command[a]).abs().max())
 gate=((d.VF_unsaturated<4)|(d.VR_integrator_error<0))&((d.VF_unsaturated>.2)|(d.VR_integrator_error>0))
 delta=d.VF_integral.shift(-1)-d.VF_integral
 update_error=float((delta[a]-0.015*ki*d.VR_integrator_error[a]*gate[a]).dropna().abs().max())
 assert max(p_error,u_error,sat_error,update_error)<1e-7,(f,p_error,u_error,sat_error,update_error)
 stats.append(dict(file=f.name,proportional_replay=p_error,command_replay=u_error,saturation_replay=sat_error,integrator_replay=update_error))
pd.DataFrame(stats).to_csv(r/(phase+'_implementation_checks.csv'),index=False)
assert len(stats)=={'tune':80,'transfer':105,'ablation':1}[phase]
print('Verified',len(stats),'saved trajectories:',pd.DataFrame(stats).drop(columns='file').max().to_dict())
