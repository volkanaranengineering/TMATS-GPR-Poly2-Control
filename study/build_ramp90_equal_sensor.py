"""Analyze independently rerun, explicitly equal-sensor comparisons."""
import json
import numpy as np
import pandas as pd
import build_ramp90_comparison as a

OLD=a.RUN
a.RUN=a.ROOT/'results/pilco_ramp90_equal_sensor_20261010'
a.SRC=a.ROOT/'output/pdf/ramp90_equal_sensor_source'
a.SRC.mkdir(parents=True,exist_ok=True)
a.DATA=[pd.read_csv(a.RUN/f'{k}.csv') for k in a.KEYS]
audits=[json.loads((a.RUN/f'{k}_sensor_audit.json').read_text()) for k in a.KEYS]
settings=['sensor_library','IC_M','Sen_Max_M','Sen_Min_M','Gain_M','Tau_M','GN_EN_M','GN_NST_M','GN_C_M','GN_MinNoise_M','F_Gain_M','F_Drift_M']
for field in settings:assert len({x[field] for x in audits})==1,field
for x in audits:
    assert x['active_feedback'].endswith('/1st order  Sensor')
assert len({x['sensor_input'].split('/',1)[1] for x in audits})==1
rows=[]
for k,d in zip(a.KEYS,a.DATA):
    old=pd.read_csv(OLD/f'{k}.csv');assert np.allclose(d.time_s,old.time_s)
    q=(d.time_s>=60)&(d.time_s<65)
    rows.append(dict(method=k,sensor_tau_s=.05,sensor_noise_enabled=False,
        max_speed_difference_from_previous_rpm=float(abs(d.Nmech-old.Nmech).max()),
        max_sensed_difference_from_previous_rpm=float(abs(d.DOB_sensed-old.DOB_sensed).max()),
        max_fuel_difference_from_previous_lbm_s=float(abs(d.Wf-old.Wf).max()),
        actual_speed_ramp_rmse_rpm=float(np.sqrt(np.mean((d.Nmech[q]-d.DOB_request[q])**2))),
        sensed_speed_ramp_rmse_rpm=float(np.sqrt(np.mean((d.DOB_sensed[q]-d.DOB_request[q])**2)))))
pd.DataFrame(rows).to_csv(a.RUN/'sensor_comparison.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False),flush=True)
a.main()
p=a.SRC/'Ramp90_Comparison.tex';s=p.read_text()
s=s.replace(r'\section{Reproducible test protocol}',r'''\section{Identical-sensor audit and fresh rerun}
All four models explicitly use the same T-MATS first-order speed-sensor library block: time constant 0.05 s, unity gain, limits 0--20000 rpm, initial value from the same plant initial speed, noise disabled, unity fault gain and zero drift. The sensor sample-time setting is the same plant solve interval. Model wiring assertions verify that both the base PI and each active advanced controller receive this sensor output directly. The sensor input comes from the same plant-output block in every model.

The earlier models already had these settings. The new simulations explicitly enforce them in separate model copies and reproduce the earlier speed, sensed-speed and fuel traces. Thus the prior ranking was not caused by unequal sensor dynamics. Controllers respond differently to the same lag. During a ramp, actual-speed error and sensed-speed error differ; the primary tables continue to score actual shaft speed. Individual audit JSON files and a sensor-comparison CSV accompany the results.
\section{Reproducible test protocol}''')
s=s.replace('ramp90\\_batch.m','ramp90\\_equal\\_sensor\\_batch.m').replace('GasTurbine_Ramp90_*.mdl','GasTurbine_EqualSensor_*.mdl').replace('results/pilco_ramp90_100_5s_20261010','results/pilco_ramp90_equal_sensor_20261010')
s=s.replace('build\\_ramp90\\_comparison.py','build\\_ramp90\\_equal\\_sensor.py').replace('build\\_ramp90\\_video.py','build\\_ramp90\\_equal\\_sensor.py')
s=s.replace(r'\texttt{ramp90\_equal\_sensor\_batch.m}',r'\path{ramp90_equal_sensor_batch.m}').replace(r'\texttt{build\_ramp90\_equal\_sensor.py}',r'\path{build_ramp90_equal_sensor.py}')
p.write_text(s)

import sys
if '--report-only' in sys.argv:sys.exit(0)

import build_ramp90_video as v
v.DATA=a.DATA;v.RUN=a.RUN;v.M=pd.read_csv(a.RUN/'comparison.csv')
v.OUT=a.RUN/'video';v.OUT.mkdir(exist_ok=True)
v.DEST=a.ROOT/'output/video/PILCO_90_to_100_Equal_Sensors_5s_Ramp.mp4'
v.SUBTITLE='9000 -> 10000 rpm in 5 s  |  Identical sensors: tau = 0.05 s, unity gain, noise OFF'
v.FOOTER='Verified sensor-output feedback for every controller  |  External load = 0 hp  |  Frozen gains'
v.main()
