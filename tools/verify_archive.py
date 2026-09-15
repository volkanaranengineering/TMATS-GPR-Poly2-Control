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
print('PASS: archive integrity and selected numerical comparisons.')
