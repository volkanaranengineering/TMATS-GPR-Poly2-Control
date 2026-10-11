"""Check the published record and independently replay key metrics; stdlib only."""
from pathlib import Path
import csv,hashlib,json,math

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
for record in manifest['files']:
    p=ROOT/record['path'];assert p.is_file(),record['path']
    assert p.stat().st_size==record['bytes'],record['path']
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    assert h.hexdigest()==record['sha256'],record['path']
print('Verified',len(manifest['files']),'file hashes.',flush=True)
run=ROOT/'study/results/poly2_tune9250_20260915'
with (run/'tuning_scores.csv').open() as f:scores={int(x['candidate']):x for x in csv.DictReader(f)}
for candidate in [0,1,34]:
    with (run/f'candidate_{candidate:02d}.csv').open() as f:
        rows=[(float(x['time_s']),float(x['Nmech']),float(x['Wf'])) for x in csv.DictReader(f)]
    errors=[n-9250 for t,n,u in rows if t>=60]
    rmse=math.sqrt(sum(e*e for e in errors)/len(errors));ring=0
    for edge in [70.005,75,90,100.005,120,135]:
        values=[u for t,n,u in rows if edge-1e-8<=t<=edge+2+1e-8]
        ring+=max(0,sum(abs(b-a) for a,b in zip(values,values[1:]))-abs(values[-1]-values[0]))
    assert abs(rmse-float(scores[candidate]['rmse_rpm']))<1e-8
    assert abs(ring-float(scores[candidate]['ringing_excess_TV_lbm_s']))<1e-8
    print(f'Candidate {candidate}: RMSE={rmse:.9f}; ringing={ring:.9f}')
latest=ROOT/'study/results/dob98_pi_20261010'
with (latest/'dobpi.csv').open() as f:
    trace=list(csv.DictReader(f))
assert all(int(float(x['valid']))==1 for x in trace)
def speed_rmse(start,end,exclusive_end=False):
    errors=[]
    for x in trace:
        t=float(x['time_s'])-60
        inside=t>=start-1e-8 and (t<end-1e-8 if exclusive_end else t<=end+1e-8)
        if inside:errors.append(float(x['Nmech'])-float(x['DOB_request']))
    assert errors
    return math.sqrt(sum(e*e for e in errors)/len(errors))
with (latest/'comparison.csv').open() as f:
    selected=next(x for x in csv.DictReader(f) if x['method']=='DOB98 + tuned PI')
for field,value in [('full_rmse_rpm',speed_rmse(0,25.005)),('ramp_rmse_rpm',speed_rmse(0,5,True)),('load_rmse_rpm',speed_rmse(10,25.005))]:
    assert abs(value-float(selected[field]))<1e-8,(field,value,selected[field])
    print(f'DOB98 {field}={value:.9f}')
with (latest/'tuning.csv').open() as f:
    candidates=list(csv.DictReader(f))
best=min((x for x in candidates if int(x['accepted'])==1),key=lambda x:float(x['objective']))
assert int(best['case_index'])==11 and float(best['Kp'])==0.048 and float(best['Ki'])==0.05
assert all(abs(float(x['objective'])-float(x['rmse_rpm'])-.05*float(x['fuel_excess_TV']))<1e-8 for x in candidates)
with (ROOT/'study/results/pilco_ramp90_equal_sensor_20261010/sensor_comparison.csv').open() as f:
    sensors=list(csv.DictReader(f))
assert len(sensors)==4
for row in sensors:
    assert float(row['sensor_tau_s'])==.05 and row['sensor_noise_enabled']=='False'
    assert all(float(row[k])==0 for k in row if k.startswith('max_'))
print('PASS: archive integrity, saved Poly2/DOB98 metrics, tuning selection, and equal-sensor audit. No simulation executed.')
