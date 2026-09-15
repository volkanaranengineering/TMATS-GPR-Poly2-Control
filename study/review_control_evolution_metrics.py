"""Read-only reanalysis of archived traces for the three-role paper revision."""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'reviews/control_evolution_v2'
OUT.mkdir(parents=True,exist_ok=True)
RUN=ROOT/'results/poly2_tune9250_20260915'
edges=np.array([70.005,75,90,100.005,120,135])
ends=np.array([75,90,100.005,120,135,150])
rows=[]; manifest={}
for amplitude,files in [(10,['candidate_00.csv','candidate_01.csv','candidate_34.csv']),
                        (5,['validation_base.csv','validation_original.csv','validation_tuned.csv'])]:
    for method,name in zip(['Base PI','Original Poly2','Retuned Poly2'],files):
        path=RUN/name;d=pd.read_csv(path);t=d.time_s.to_numpy();e=np.abs(d.Nmech.to_numpy()-9250);u=d.Wf.to_numpy()
        manifest[name]={'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        row={'load_percent':amplitude,'method':method}
        for width in [.5,1,2,3]:
            total=0
            for start in edges:
                f=u[(t>=start-1e-8)&(t<=start+width+1e-8)]
                total+=max(0,float(np.abs(np.diff(f)).sum()-abs(f[-1]-f[0])))
            row[f'ringing_{width:g}s']=total
        for band in [.1,.5,1,92.5]:
            worst=0
            for start,end in zip(edges,ends):
                ix=np.flatnonzero((t>=start-1e-8)&(t<end-1e-8));bad=np.flatnonzero(e[ix]>band)
                recovery=0 if not len(bad) else (np.inf if bad[-1]==len(ix)-1 else t[ix[bad[-1]+1]]-start)
                worst=max(worst,recovery)
            row[f'recovery_{band:g}rpm_s']=worst
        row['peak_percent_speed']=float(e[t>=60].max()/9250*100)
        rows.append(row)
df=pd.DataFrame(rows);df.to_csv(OUT/'metric_sensitivity.csv',index=False)
(OUT/'metric_sensitivity_manifest.json').write_text(json.dumps(manifest,indent=2))
def table(columns,labels,caption,label):
    lines=[r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}rlrrrr@{}}\toprule',
           'Load & Method & '+' & '.join(labels)+r'\\\midrule']
    for row in rows:
        lines.append(f"{row['load_percent']}\\% & {row['method']} & "+' & '.join(f'{row[c]:.5g}' for c in columns)+r'\\')
    lines += [r'\bottomrule\end{tabular}',r'\caption{'+caption+r'}\label{tab:'+label+r'}',r'\end{table}']
    return '\n'.join(lines)+'\n'
(OUT/'table_sensitivity_ring.tex').write_text(table([f'ringing_{w:g}s' for w in [.5,1,2,3]],['0.5 s','1 s','2 s','3 s'],
    'Fuel reversal sensitivity at 9250 rpm. Columns change the duration of each of the six post-edge windows; entries are summed excess total variation in lbm/s. The 2 s column reproduces the published metric. These are reanalyses of the same saved trajectories, not new tuning results.','sensitivity_ring'))
(OUT/'table_sensitivity_recovery.tex').write_text(table([f'recovery_{b:g}rpm_s' for b in [.1,.5,1,92.5]],['0.1 rpm','0.5 rpm','1 rpm',r'1\% speed'],
    'Worst persistent recovery in seconds at 9250 rpm. The last band is 92.5 rpm. Event intervals and the next-event persistence rule are held fixed while changing only the band.','sensitivity_recovery'))
print(df.to_string(index=False))
