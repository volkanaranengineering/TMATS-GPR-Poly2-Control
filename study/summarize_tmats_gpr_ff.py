"""Verify six-controller runs, extend observer tables, and append a PDF report."""
from pathlib import Path
import csv, json, hashlib, sys
from xml.sax.saxutils import escape
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'tmp/pdfs/python_deps'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter

source=Path((root/'tmp/gpr_ff_directory.txt').read_text().strip())
out=root/'results/Observer_9000_9500_GPR_FF_Comparison';out.mkdir(exist_ok=True)
pdfout=root/'output/pdf';pdfout.mkdir(exist_ok=True,parents=True)
tmp=root/'tmp/pdfs/gpr_ff';tmp.mkdir(exist_ok=True,parents=True)
rows=json.loads((source/'summary.json').read_text())
assert len(rows)==60,'All 60 simulations must finish before reporting.'
names=['PI','DOB','LESO','UDE','GPIO','GPR_FF']
palette=['#555555','#7e57c2','#0072b2','#d55e00','#009e73','#cc3377']
styles=['-',':','--','-.','-',(0,(5,1))]
edges=np.array([10.005,15,30,40.005,60,75]);events=[];runs={};checks={};failures=[]
for r in rows:
    key=(r['scenario'],r['method'])
    assert key not in runs
    d=np.genfromtxt(source/r['scenario']/(r['method']+'.csv'),delimiter=',',names=True)
    t=d['time_s']-60;e=d['Nmech']-r['rpm'];mask=t>=0
    assert len(d)==10001 and abs(t[-1]-90)<1e-8
    bad=np.flatnonzero(d['valid']==0);accepted=len(bad)==0
    assert bool(r['accepted'])==accepted
    prefix=np.arange(len(d))<(bad[0] if len(bad) else len(d));v=mask&prefix
    if accepted:
        assert abs(np.sqrt(np.mean(e[mask]**2))-r['rmse_rpm'])<1e-8
        assert abs(np.sum(abs(e[mask]))*.015-r['iae_rpm_s'])<1e-7
    else:
        assert r['rmse_rpm'] is None and abs(t[bad[0]]-r['first_failure_s'])<1e-8
        i=bad[0]
        failures.append(dict(scenario=r['scenario'],method=r['method'],first_failure_s=float(t[i]),
            max_flow_error=float(d['max_flow_error'][i]),iterations=float(d['DOB_iterations'][i]),
            compressor_margin=float(d['DOB_SM'][i]),fuel_lbm_s=float(d['Wf'][i])))
    assert np.max(abs(d['DOB_disturbance']))==0
    assert np.max(abs(d['DOB_request'][mask]-r['rpm']))<1e-7
    command=np.clip(d['DOB_PI']-d['DOB_compensation']+d['GPR_FF'],.2,4)
    command_error=float(np.max(abs(command[prefix]-d['DOB_command'][prefix])))
    assert command_error<1e-8
    if r['method']=='GPR_FF':
        assert np.max(abs(d['DOB_compensation']))==0
        assert np.max(abs(d['GPR_referenceAcceleration'][mask]))<1e-6
        assert np.max(abs(d['GPR_querySpeed'][prefix]-np.clip(d['DOB_sensed'][prefix],9000,10000)))<1e-8
    else:assert np.max(abs(d['GPR_FF']))==0
    checks['_'.join(key)]={'command_replay_max_error':command_error,'valid_samples':int(prefix.sum()),
                           'shaft_balance_max_error':r['shaft_balance_error'],'gp_replay_max_error':r['gp_replay_error']}
    runs[key]=(t,e,d,v)
    ramps=np.repeat([.3,1.5,3],2) if r['shape']=='ramps' else np.zeros(6)
    for k,(edge,ramp) in enumerate(zip(edges,ramps)):
        end=edges[k+1] if k<5 else 90
        win=(t>=edge-1e-8)&(t<end-1e-8);tt=t[win]-edge;ee=e[win]
        valid=bool(np.all(d['valid'][t<end-1e-8]));settle=None
        if valid:
            outside=np.flatnonzero(abs(ee)>1);i=int(outside[-1]+1) if len(outside) else 0
            if i<len(tt) and tt[-1]-tt[i]>=.5:settle=float(tt[i])
        events.append(dict(scenario=r['scenario'],rpm=r['rpm'],fraction=r['fraction'],shape=r['shape'],method=r['method'],
            edge='apply' if k%2==0 else 'remove',start_s=float(edge),ramp_s=float(ramp),valid=valid,
            peak_rpm=float(np.max(abs(ee))) if valid else None,recovery_from_start_s=settle,
            recovery_after_ramp_s=max(0,settle-ramp) if settle is not None else None))
for scenario in sorted({r['scenario'] for r in rows}):
    baseline=runs[scenario,'PI'][2]['PTO_hp']
    for n in names:assert np.array_equal(runs[scenario,n][2]['PTO_hp'],baseline)
# Cross-check that introducing a disabled GP branch preserved previous methods.
old_dirs={9000:root/'results/literature_observers_9000rpm_10pct_20260912_211600_355',
          9500:root/'results/literature_observers_9500rpm_10pct_20260912_213607_364'}
for rpm,folder in old_dirs.items():
    for n in names[:-1]:
        old=np.genfromtxt(folder/(n+'.csv'),delimiter=',',names=True)
        new=runs[f'{rpm}rpm_10pct_ramps',n][2]
        delta=float(np.max(abs(old['Nmech']-new['Nmech'])))
        assert delta<1e-6, f'Baseline changed: {rpm} {n}: {delta}'
        checks[f'baseline_{rpm}_{n}']={'max_speed_difference_rpm':delta}
previous_pto={
 '9000rpm_05pct_ramps':'dob_pto_9000rpm_05pct_20260912_201537_806',
 '9000rpm_10pct_ramps':'dob_pto_9000rpm_10pct_20260912_201600_313',
 '9000rpm_20pct_ramps':'dob_pto_9000rpm_20pct_20260912_201611_189',
 '9000rpm_30pct_ramps':'dob_pto_9000rpm_30pct_20260912_201622_343',
 '9500rpm_20pct_steps':'dob_pto_9500rpm_20pct_20260912_195059_980',
 '9500rpm_30pct_steps':'dob_pto_9500rpm_30pct_20260912_195120_747'}
for scenario,folder in previous_pto.items():
    for j,n in enumerate(['PI','DOB'],1):
        old=np.genfromtxt(root/'results'/folder/f'case_{j:02d}.csv',delimiter=',',names=True)
        new=runs[scenario,n][2]
        bad=np.flatnonzero((old['valid']==0)|(new['valid']==0));end=bad[0] if len(bad) else len(new)
        delta=float(np.max(abs(old['Nmech'][:end]-new['Nmech'][:end])))
        assert delta<1e-6
        assert np.max(abs(old['PTO_hp']-new['PTO_hp']))<1e-7
        checks[f'previous_pto_{scenario}_{n}']={'valid_prefix_speed_difference_rpm':delta}

def write_records(path,records):
    path.with_suffix('.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    with path.with_suffix('.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
write_records(out/'all_scenarios',rows);write_records(out/'events',events)
if failures:write_records(out/'failures',failures)
matched=[r for r in rows if r['fraction']==.1 and r['shape']=='ramps']
write_records(out/'summary',matched)
(out/'verification.json').write_text(json.dumps(checks,indent=2))
plt.rcParams.update({'font.size':9,'axes.titlesize':10,'axes.labelsize':9})
fig,ax=plt.subplots(figsize=(11,4.8));ax.set_xlim(0,15);ax.set_ylim(0,6.6);ax.axis('off')
def box(x,y,w,h,label,color='#edf3f6'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.05',facecolor=color,edgecolor='#17334d',lw=1.2))
    ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=8.5)
def arrow(points,color='#17334d'):
    for start,end in zip(points[:-2],points[1:-1]):ax.plot([start[0],end[0]],[start[1],end[1]],color=color,lw=1.2)
    ax.annotate('',xy=points[-1],xytext=points[-2],arrowprops=dict(arrowstyle='->',color=color,lw=1.2))
box(.2,3.4,1.5,.8,'Governed\nreference r');box(3,3.4,2,.8,'Existing PI\ne = r - sensed speed')
box(3,5.2,2,.8,'Reference derivative\nlimit +/-150 rpm/s')
box(5.8,5.2,2,.8,'Exact inverse GP\ng(Nq, a_ref)','#fbe8f0')
box(8.5,5.2,2.3,.8,'Subtract nominal trim\nlimit +/-0.15; enable','#fbe8f0')
box(8.5,3.4,.7,.8,'+');box(10,3.4,1.8,.8,'Fuel limits\n0.2 to 4 lbm/s')
box(12.7,3.4,1.8,.8,'T-MATS\nturbine');box(12.7,1,1.8,.8,'Speed sensor\n0.05 s')
box(5.8,1,2,.8,'Speed guard\n9000 to 10000 rpm','#fbe8f0')
ax.text(13.6,5.55,'Unknown shaft load',ha='center',fontsize=8.5)
arrow([(1.7,3.8),(3,3.8)]);arrow([(2.25,3.8),(2.25,5.6),(3,5.6)])
arrow([(5,5.6),(5.8,5.6)]);arrow([(7.8,5.6),(8.5,5.6)]);arrow([(9.65,5.2),(9.65,4.7),(8.85,4.7),(8.85,4.2)])
arrow([(5,3.8),(8.5,3.8)]);arrow([(9.2,3.8),(10,3.8)]);arrow([(11.8,3.8),(12.7,3.8)])
arrow([(13.6,5.25),(13.6,4.2)]);arrow([(13.6,3.4),(13.6,1.8)])
arrow([(12.7,1.4),(7.8,1.4)]);arrow([(6.8,1.8),(6.8,5.2)])
arrow([(12.2,1.4),(12.2,.4),(4,.4),(4,3.4)])
ax.text(7.5,.08,'No load signal or plant acceleration is supplied to the inverse GP.',ha='center',fontsize=9,color='#17334d')
fig.tight_layout();fig.savefig(out/'controller_architecture.png',dpi=180);plt.close(fig)
for rpm in [9000,9500]:
    scenario=f'{rpm}rpm_10pct_ramps'
    fig,ax=plt.subplots(4,1,figsize=(8,8),layout='constrained')
    for n,c,ls in zip(names,palette,styles):
        t,e,d,v=runs[scenario,n]
        for a,y in zip(ax[:3],[e,d['DOB_command'],d['GPR_FF'] if n=='GPR_FF' else -d['DOB_compensation']]):
            a.plot(t[v],y[v],color=c,ls=ls,lw=1.2,label=n)
    t,e,d,v=runs[scenario,'PI'];ax[3].plot(t[v],d['PTO_hp'][v]*.7456998715822702/1000,color='gray')
    for a,label in zip(ax,['Speed error (rpm)','Fuel command (lbm/s)','Added correction (lbm/s)','Shaft extraction (MW)']):
        a.set_ylabel(label);a.grid(alpha=.2);a.set_xlim(0,90)
    ax[0].legend(ncol=3,fontsize=8);ax[-1].set_xlabel('Time after preparation (s)')
    fig.suptitle(f'{rpm} rpm / 10% ramp loads / unchanged PI');fig.savefig(out/f'overview_{rpm}.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(3,2,figsize=(8,7),layout='constrained')
    for k,(edge,ramp) in enumerate(zip(edges,np.repeat([.3,1.5,3],2))):
        a=ax.flat[k]
        for n,c,ls in zip(names,palette,styles):
            t,e,d,v=runs[scenario,n];m=v&(t>=edge-.4)&(t<min(edge+ramp+3.5,edges[k+1] if k<5 else 90))
            a.plot(t[m]-edge,e[m],color=c,ls=ls,lw=1.1,label=n)
        a.axhspan(-1,1,color='#009e73',alpha=.1);a.axvspan(0,ramp,color='gray',alpha=.1)
        a.set_title(f'{ramp:.2f} s '+('application' if k%2==0 else 'removal'));a.set_xlabel('Time from load edge (s)');a.set_ylabel('Error (rpm)');a.grid(alpha=.2)
    fig.suptitle(f'{rpm} rpm: six-controller recovery comparison');fig.savefig(out/f'zooms_{rpm}.png',dpi=180);plt.close(fig)
# Main FF vs PI response over all ten physical scenarios, limited to valid prefix.
fig,axes=plt.subplots(5,2,figsize=(10,13),layout='constrained')
scenarios=list(dict.fromkeys(r['scenario'] for r in rows))
for a,scenario in zip(axes.flat,scenarios):
    for n,c in [('PI',palette[0]),('GPR_FF',palette[-1])]:
        t,e,d,v=runs[scenario,n];a.plot(t[v],e[v],color=c,label=n,lw=1)
        bad=np.flatnonzero(d['valid']==0)
        if len(bad):a.axvline(t[bad[0]],color=c,ls=':',lw=1)
    a.set_title(scenario.replace('_',' '));a.grid(alpha=.2);a.set_xlabel('Time (s)');a.set_ylabel('Error (rpm)');a.legend(fontsize=7)
fig.savefig(out/'all_loads.png',dpi=180);plt.close(fig)

def f(x,n=3):return 'N/A' if x is None else f'{x:.{n}f}'
def table_md(records):
    lines=['| Speed | Load | Shape | Method | Valid | RMSE rpm | Peak rpm | IAE rpm s | Failure s |',
           '|---:|---:|---|---|---|---:|---:|---:|---:|']
    for r in records:lines.append(f"| {r['rpm']} | {100*r['fraction']:.0f}% | {r['shape']} | {r['method']} | {bool(r['accepted'])} | {f(r['rmse_rpm'])} | {f(r['peak_rpm'])} | {f(r['iae_rpm_s'])} | {f(r['first_failure_s'])} |")
    return lines
findings=[]
ff_slopes={}
recovery_counts={}
for rpm in [9000,9500]:
    pi=next(r for r in matched if r['rpm']==rpm and r['method']=='PI');gp=next(r for r in matched if r['rpm']==rpm and r['method']=='GPR_FF')
    change=100*(gp['rmse_rpm']/pi['rmse_rpm']-1)
    _,_,gd,gv=runs[f'{rpm}rpm_10pct_ramps','GPR_FF']
    slope_mask=gv&(abs(gd['DOB_sensed']-rpm)>.01)&(gd['GPR_speedGuard']==0)&(abs(gd['GPR_FF'])<.15-1e-8)
    ff_slopes[rpm]=float(np.polyfit(gd['DOB_sensed'][slope_mask]-rpm,gd['GPR_FF'][slope_mask],1)[0])
    findings.append(f"At {rpm} rpm, GPR_FF RMSE is {gp['rmse_rpm']:.6f} rpm versus PI {pi['rmse_rpm']:.6f} rpm ({change:+.2f}% change; positive is worse). Peak error is {gp['peak_rpm']:.6f} rpm. Speed guard active: {gp['ff_speed_guard_percent']:.2f}% of evaluation samples.")
    faster=equal=slower=0
    for ev in [e for e in events if e['rpm']==rpm and e['fraction']==.1 and e['method']=='GPR_FF']:
        base_ev=next(e for e in events if e['rpm']==rpm and e['fraction']==.1 and e['method']=='PI' and e['start_s']==ev['start_s'])
        delta=ev['recovery_after_ramp_s']-base_ev['recovery_after_ramp_s']
        faster+=int(delta < -1e-8);equal+=int(abs(delta)<=1e-8);slower+=int(delta>1e-8)
    recovery_counts[rpm]=(faster,equal,slower)
    findings.append(f"GPR_FF +/-1 rpm recovery at {rpm} rpm is faster than PI in {faster}/6 events, equal in {equal}/6, and slower in {slower}/6. Thus the larger peaks and RMSE coexist with faster threshold recovery; these metrics must not be collapsed into a single blanket ranking.")
lines=['# Six-controller comparison with inverse GPR feedforward','',
       'GPR_FF is the inverse-GP feedforward requested as GPT FF. It augments the original PI; it is not a disturbance observer. All 60 runs are new Simulink simulations. The previous five controllers at 10% load reproduce the archived speed histories within 1e-6 rpm.','',
       '## Controller','',
       '![Controller architecture](controller_architecture.png)','',
       '`a_ref[k] = clip((r[k]-r[k-1])/0.015, -150, 150)`','',
       '`Nq[k] = clip(N_sensed[k], 9000, 10000)`','',
       '`delta_u_FF[k] = rho(t) * clip(g(Nq[k],a_ref[k])-g(N_nominal,0), -0.15, 0.15)`','',
       '`u[k] = clip(u_PI[k] + delta_u_FF[k], 0.2, 4)`','',
       'The original continuous PI retains Kp=0.025, Ki=0.05 and integrator initialization 3. The sensor time constant remains 0.05 s. rho ramps from 0 to 1 over absolute seconds 30-32. No observer compensation is active in GPR_FF. No shaft-load value, future disturbance schedule, actual plant acceleration, or inverse-model refit is supplied to the controller.','',
       'The observer branches retain their inherited compensation gain 0.25 and pole-frequency parameter 0.5 Hz. The physical inverse-GP correction uses unit gain before the same +/-0.15 lbm/s limit; it is not bandwidth-matched to the observers. No noise, delay, or gain-tuning comparison is claimed.','',
       'This is state-scheduled nominal feedforward: sensed speed schedules the inverse model. It is not purely reference-only feedforward; that would remain constant throughout these constant-reference tests. There is no extra speed-error-to-acceleration gain. The trim subtraction prevents double-counting equilibrium fuel already supplied by the inherited PI integrator. The speed guard prevents extrapolation below the 9000 rpm training boundary, but can make the 9000 rpm response asymmetric.','',
       'The inverse model is the frozen 600-point exact ARD squared-exponential GP. Online mean evaluation is O(600); its 100-point held-out inverse fuel RMSE was 0.001048216 lbm/s and 95% response interval coverage was 97%. Fuel uncertainty is evaluated offline on up to 100 valid samples per control run; it is not used as a control gain or as a bound on loaded-plant error.','',
       '## Matched 10% observer comparison','',*table_md(matched),'','## Findings','',*findings,'',
       'A nominal inverse learned at zero external shaft load cannot anticipate an unknown load. Accurate offline inverse regression does not imply improved rejection. In these tests a_ref is zero during evaluation, so the FF branch only schedules nominal fuel with sensed speed; the PI integrator supplies the additional load-dependent fuel. A learned increase in equilibrium fuel with speed can reduce effective restoring feedback when added to the unchanged PI. Results are reported without retuning to favor the GP.','',
       f"Regression of unclipped FF correction against sensed speed on the matched runs gives slopes {ff_slopes[9000]:.7f} and {ff_slopes[9500]:.7f} lbm/s per rpm at 9000 and 9500 rpm, respectively. These are descriptive trajectory fits, not independent linearizations; the 9000 rpm fit excludes the active speed guard.",'',
       '## All load scenarios','',*table_md(rows),'',
       'At both speeds, 5%, 10%, 20%, and 30% gross-turbine-power extraction uses three ramp/hold/ramp pulses (0.30, 1.50, 3.00 s). The earlier 9500 rpm 20% and 30% step-load cases are repeated too. Application times are 10.005, 30, 60 s; removal times 15, 40.005, 75 s after 60 s preparation. The 9500 rpm ramped 5/20/30% cases extend the previous matrix. Loads are speed-specific fractions, not equal absolute powers.','',
       '## Validity and recovery','',
       'Validity requires finite logged signals, positive fuel, positive compressor margin, flow residual <=1e-9, and fewer than 200 iterations. Full-run scores are withheld after any invalid solve; plots show only the valid prefix. A later numerically converged sample does not rehabilitate the trajectory. Shaft balance and command reconstruction are verified independently. Identical load profiles are checked across methods.','',
       'Recovery is the first sample after the last excursion outside +/-1 rpm with at least 0.5 s dwell before the next load edge. After-ramp recovery subtracts ramp duration and is bounded below by zero. Event scores are withheld if any preceding sample is invalid. All 360 event records are in events.csv.','',
       '## Reproduce','',
       '`run_tmats_gpr_ff_benchmarks` builds GasTurbine_Dyn_Template_GPR_FF.mdl and runs the matrix. Then run `summarize_tmats_gpr_ff.py`. The previous models and trained inverse GP remain separate. The new Level-2 MATLAB S-function is a desktop simulation implementation, not an embedded code-generation claim.','',
       'References: Aran (2019), thesis sections 5.1 and 6.2.1; Rasmussen and Williams, Gaussian Processes for Machine Learning, chapter 2. Previous report derivations for the inherited PI/DOB/LESO/UDE/GPIO remain applicable.','']
for rpm in [9000,9500]:
    lines += [f'## {rpm} rpm plots','',f'![Six-controller response](overview_{rpm}.png)','',f'![Recovery zooms](zooms_{rpm}.png)','']
if failures:
    lines+=['## First-invalid-sample diagnostics','','| Scenario | Method | Time s | Flow residual | Iterations | Margin % |','|---|---|---:|---:|---:|---:|']
    for r in failures:lines.append(f"| {r['scenario']} | {r['method']} | {r['first_failure_s']:.3f} | {r['max_flow_error']:.3g} | {r['iterations']:.0f} | {r['compressor_margin']:.3f} |")
lines += ['## Wider load tests','','![All loads](all_loads.png)','']
report='\n'.join(lines)
(out/'REPORT.md').write_text(report,encoding='utf-8')
rootreport=report
for name in ['overview_9000.png','overview_9500.png','zooms_9000.png','zooms_9500.png','all_loads.png','controller_architecture.png']:
    rootreport=rootreport.replace(f']({name})',f'](results/Observer_9000_9500_GPR_FF_Comparison/{name})')
(root/'TMATS_GPR_FF_COMPARISON.md').write_text(rootreport,encoding='utf-8')
# Extend the original comparison without destroying its historical derivation.
oldout=root/'results/Observer_9000_9500_Comparison'
appendix='\n\n<!-- GPR_FF_EXTENSION -->\n\n## Inverse GPR feedforward extension\n\n'+ '\n\n'.join(findings)+'\n\n'+'\n'.join(table_md(matched))+'\n\nFull extended report: [Six-controller GPR FF comparison](../Observer_9000_9500_GPR_FF_Comparison/REPORT.md).\n'
oldreport=(oldout/'REPORT.md').read_text(encoding='utf-8').split('<!-- GPR_FF_EXTENSION -->')[0].rstrip()
notice='> Updated with GPR_FF: the historical five-method analysis below is retained. The current six-method table is in the GPR_FF extension at the end.\n\n'
if not oldreport.startswith('> Updated with GPR_FF:'):oldreport=notice+oldreport
(oldout/'REPORT.md').write_text(oldreport+appendix,encoding='utf-8')
main=root/'TMATS_OBSERVER_9000_9500_COMPARISON.md'
prior=main.read_text(encoding='utf-8').split('<!-- GPR_FF_EXTENSION -->')[0].rstrip()
if not prior.startswith('> Updated with GPR_FF:'):prior=notice+prior
main.write_text(prior+appendix.replace('../Observer_9000_9500_GPR_FF_Comparison/REPORT.md','results/Observer_9000_9500_GPR_FF_Comparison/REPORT.md'),encoding='utf-8')
# Updated machine-readable observer comparison, preserving the original tables.
if not (oldout/'summary_before_GPR_FF.json').exists():
    for ext in ['json','csv']:(oldout/f'summary_before_GPR_FF.{ext}').write_bytes((oldout/f'summary.{ext}').read_bytes())
oldrows=json.loads((oldout/'summary_before_GPR_FF.json').read_text())
for r in matched:
    if r['method']!='GPR_FF':continue
    added={k:r.get(k) for k in oldrows[0]}
    added['peak_fuel_lbm_s']=r['fuel_peak_lbm_s'];oldrows.append(added)
write_records(oldout/'summary',oldrows)
for stem in ['events','recovery_comparison']:
    if not (oldout/f'{stem}_before_GPR_FF.json').exists():
        for ext in ['json','csv']:(oldout/f'{stem}_before_GPR_FF.{ext}').write_bytes((oldout/f'{stem}.{ext}').read_bytes())
oldevents=json.loads((oldout/'events_before_GPR_FF.json').read_text())
for e in events:
    if e['method']=='GPR_FF' and e['fraction']==.1 and e['shape']=='ramps':
        added={k:e.get(k) for k in oldevents[0]};added['peak_error_rpm']=e['peak_rpm'];oldevents.append(added)
write_records(oldout/'events',oldevents)
oldtiming=json.loads((oldout/'recovery_comparison_before_GPR_FF.json').read_text())
for ramp in [.3,1.5,3]:
    added={'ramp_s':ramp,'method':'GPR_FF'}
    for rpm in [9000,9500]:
        for edge in ['apply','remove']:
            ev=next(e for e in events if e['rpm']==rpm and e['fraction']==.1 and e['method']=='GPR_FF' and e['ramp_s']==ramp and e['edge']==edge)
            for key in ['recovery_after_ramp_s','recovery_from_start_s']:added[f'{rpm}_{edge}_{key}']=ev[key]
    oldtiming.append(added)
write_records(oldout/'recovery_comparison',oldtiming)

for name,file in [('Body','arial.ttf'),('Bold','arialbd.ttf')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
navy=colors.HexColor('#17334d');W=487
ps=ParagraphStyle('p',fontName='Body',fontSize=9.5,leading=13.5,spaceAfter=9)
hs=ParagraphStyle('h',fontName='Bold',fontSize=17,leading=21,textColor=navy,spaceAfter=14)
cs=ParagraphStyle('c',fontName='Body',fontSize=7.5,leading=10)
ts=ParagraphStyle('th',parent=cs,fontName='Bold',textColor=colors.white)
story=[]
def p(s):story.append(Paragraph(s,ps))
def h(s):story.append(Paragraph(s,hs))
def page():story.append(PageBreak())
def tab(vals,widths):
    cells=[[Paragraph(escape(str(v)).replace('\n','<br/>'),ts if i==0 else cs) for v in row] for i,row in enumerate(vals)]
    obj=Table(cells,colWidths=widths,repeatRows=1)
    obj.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#edf3f6')]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.extend([obj,Spacer(1,10)])
def img(path,maxh=620):
    im=Image(str(path));scale=min(W/im.imageWidth,maxh/im.imageHeight);im.drawWidth=im.imageWidth*scale;im.drawHeight=im.imageHeight*scale;story.append(im)
def footer(c,doc):
    c.setFont('Body',8);c.setFillColor(navy);c.drawString(42,25,'T-MATS | Ters GPR ileri besleme | 9000 / 9500 rpm');c.drawRightString(553,25,str(doc.page))
h('Ters GPR ile PI ileri besleme desteği')
p('Altı denetleyicili gözlemci karşılaştırması ve önceki mühendislik makalesine sayısal ek')
p('<b>Yeni kapsam:</b> PI, DOB, LESO, UDE, GPIO ve GPR_FF; iki nominal hızda toplam 60 yeni Simulink koşusu. GPR_FF, kullanıcı isteğindeki GPT FF adının Gaussian Process Regression karşılığıdır. Bir bozucu gözlemci değildir.')
tab([['rpm','Yöntem','RMSE\nrpm','Tepe hata\nrpm','IAE\nrpm s'],*[[r['rpm'],r['method'],f(r['rmse_rpm']),f(r['peak_rpm']),f(r['iae_rpm_s'])] for r in matched]],[48,83,111,120,125])
for rpm in [9000,9500]:
    pi=next(r for r in matched if r['rpm']==rpm and r['method']=='PI');gp=next(r for r in matched if r['rpm']==rpm and r['method']=='GPR_FF')
    faster,equal,slower=recovery_counts[rpm]
    p(f"{rpm} rpm: GPR_FF / PI RMSE değişimi <b>{100*(gp['rmse_rpm']/pi['rmse_rpm']-1):+.2f}%</b>. Pozitif değer daha yüksek hata demektir. Buna karşılık ±1 rpm toparlanması {faster}/6 olayda daha kısa, {equal}/6 olayda eşit, {slower}/6 olayda daha uzundur. Tepe hata, RMSE ve toparlanma ayrı ölçütlerdir.")
page();h('1. Denetleyici bağlantıları');img(out/'controller_architecture.png',300)
p('Pembe bloklar yeni GPR koludur. Mevcut PI, sensör, yakıt doyumu ve T-MATS fiziksel modeli korunur. Şaft yükü yalnız bitkiye uygulanır; GPR girişine bağlanmaz. Artı düğümündeki katkı, nominal denge yakıtı çıkarılmış ileri beslemedir.')
p('Gözlemci karşılaştırmasının diğer koşularında önceki DOB/LESO/UDE/GPIO seçimi aktiftir ve GPR katkısı sıfırdır. GPR_FF koşusunda gözlemci telafisi sıfırlanır. Böylece GPR+PI, eski gözlemci+PI yöntemlerinden ayrı bir aday olarak değerlendirilir.')
p('Gözlemcilerin 0.25 telafi kazancı ve 0.5 Hz kutup-frekans ayarı korunur. Fiziksel ters GPR düzeltmesi, aynı ±0.15 lbm/s sınırından önce birim kazançla eklenir. Bu düzenek eşit bant genişliği iddiası taşımaz; gürültü, gecikme veya en iyi kazanç ayarı karşılaştırması değildir.')
page();h('1. Denetleyici denklemleri ve bilgi sınırı')
for s in [
 'Mevcut PI korunur: u_PI = 0.025 (r - N_s) + I, dI/dt = 0.05 (r - N_s), I(0)=3. Sensör zaman sabiti 0.05 s; GPR örnekleme süresi 0.015 s. İlave hız hatası kazancı eklenmez.',
 'Referans ivmesi: a_ref[k] = sat[-150,150]((r[k]-r[k-1])/0.015). Başlangıç referans belleği 10000 rpm. r, mevcut hız talebi sınırlayıcısının çıkışıdır.',
 'Sorgu hızı: N_q = sat[9000,10000](N_s). Ham hız aralık dışındaysa GPR_speedGuard kaydı etkin olur. Bu, modelin eğitim hız aralığı dışına çıkmasını önler; aralık içindeki her ivme-hız çiftinin eğitim verisiyle kapsandığı anlamına gelmez.',
 'İleri besleme: delta_u_FF = rho(t) sat[-0.15,0.15](g(N_q,a_ref)-g(N_nominal,0)). rho, mutlak 30-32 s arasında 0’dan 1’e çıkar. Son komut: u = sat[0.2,4](u_PI + delta_u_FF). Birimler: hız rpm, ivme rpm/s, yakıt lbm/s.',
 'Denge yakıtının çıkarılması, PI integralinin zaten sağladığı nominal yakıtı iki kez eklemeyi önler. GPR_FF koşusunda DOB telafisi sıfırdır. Diğer beş yöntemde GPR kolu tam olarak sıfırdır.',
 'Bu yapı, ölçülen hıza göre çizelgelenen nominal ileri beslemedir. Salt referans ileri beslemesi değildir; bu ayrım önemlidir, çünkü değerlendirme boyunca referans ve a_ref sabittir. Tüm yük reddetme koşularında a_ref = 0 doğrulanmıştır.',
 'GPR koluna şaft yükü, gelecek bozucu takvimi veya gerçek bitki ivmesi verilmez. İleri besleme yükü önceden bilemez. Yükün gerektirdiği ek yakıtı PI integrali sağlamaya devam eder.'
]:p(s)
page();h('2. Model, belirsizlik ve uygulama')
p('Dondurulmuş ters exact GPR, 600 eğitim gözlemiyle hız ve ivmeden yakıt debisini kestirir. ARD karesel üstel çekirdek ve maksimum olabilirlik hiperparametreleri kullanılır. Ayrı 100 test noktasında yakıt RMSE 0.001048216 lbm/s, R² 0.999997241 ve nominal %95 aralık kapsaması %97’dir. Denetim testleri sırasında yeniden eğitim veya kazanç ayarı yapılmaz.')
p('Çevrimiçi S-function, 600 çekirdek terimini kullanarak exact posterior ortalamasını hesaplar. Belirsizlik, her koşunun geçerli bölümünden en fazla 100 örnekte çevrimdışı hesaplanır. Bu tercih üçgensel kovaryans çözümünü her denetim adımında çalıştırmaz; kestirim ortalaması sparse yaklaşım değildir.')
p('Yanıt varyansı, latent varyansa öğrenilen gürültü varyansının eklenmesidir. Bu aralıklar yüksüz nominal ters model için koşulludur. Yük altındaki gerçek yakıt gereksiniminin güvenli sınırı veya kapalı çevrim performans garantisi olarak kullanılmaz. Giriş ölçüm hatası ayrıca yayılmamıştır.')
p('Simulink modeli: <b>GasTurbine_Dyn_Template_GPR_FF.mdl</b>. Ana yapı: mevcut PI ve gözlemci seçimi → PI plus GPR FF → ortak yakıt doyumu → T-MATS. GPR alt sistemi yalnız sensör hızı ve yönetilmiş hız referansından beslenir. Mevcut modeller ayrı tutulur.')
p('Uygulama Level-2 MATLAB S-function ile masaüstü simülasyondur. Gömülü kod üretimi, gerçek zaman süresi ve uçuşa/işletime uygunluk bu çalışmada doğrulanmamıştır. Kaynak model, denetleyici ve veri dosyalarının SHA-256 kayıtları ek klasörde tutulur.')
p('9000 rpm altına düşüşlerde hız koruması etkinleşir. Bu sınır, negatif ve pozitif hız hatalarında asimetrik FF davranışı yaratabilir. Aralık dışına körlemesine ekstrapolasyon yapılmamıştır. Koruma oranı sonuçlarla birlikte verilir.')
tab([['rpm','GPR hız koruması\n% örnek','FF telafi sınırı\n% örnek','Yakıt doyumu\n% örnek'],*[[r['rpm'],f(r['ff_speed_guard_percent'],2),f(r['compensation_clip_percent'],2),f(r['fuel_limit_percent'],2)] for r in matched if r['method']=='GPR_FF']],[60,150,145,132])
for rpm in [9000,9500]:
    page();h(f'3. {rpm} rpm: %10 yük, altı yöntem');img(out/f'overview_{rpm}.png',610)
    p('Telafi grafiği yakıt komutuna eklenen işaretle çizilmiştir: gözlemciler için -c, GPR için +delta_u_FF. PI kazançları ve sınırlar aynıdır.')
    page();h(f'4. {rpm} rpm: olay yakın planları');img(out/f'zooms_{rpm}.png',580)
    p('Yöntem renkleri önceki şekille aynıdır. Gri alan yük rampasını, yeşil bant ±1 rpm kabul bölgesini gösterir. Uygulama ve kaldırma olayları ayrı değerlendirilir.')
    page();h(f'5. {rpm} rpm: toparlanma süreleri')
    vals=[['Rampa s','Yöntem','Uygulama\nrampa sonrası s','Kaldırma\nrampa sonrası s']]
    for ramp in [.3,1.5,3]:
        for n in names:
            ev=[next(e for e in events if e['rpm']==rpm and e['fraction']==.1 and e['method']==n and e['ramp_s']==ramp and e['edge']==edge) for edge in ['apply','remove']]
            vals.append([f(ramp,2),n,*[f(e['recovery_after_ramp_s']) for e in ev]])
    tab(vals,[65,95,160,167]);p('Toparlanma, ±1 rpm dışındaki son örnekten sonraki ilk örnektir; bir sonraki yük kenarına kadar en az 0.5 s kalış gerekir. Rampa sonrası süre negatifse sıfır alınır. Çözünürlük 15 ms’dir.')
for rpm,shape in [(9000,'ramps'),(9500,'ramps'),(9500,'steps')]:
    page();h(f'6. {rpm} rpm: farklı yükler ({shape})')
    subset=[r for r in rows if r['rpm']==rpm and r['shape']==shape]
    tab([['Yük','Yöntem','Geçerli','RMSE\nrpm','Tepe\nrpm','İlk hata\ns'],*[[f"{100*r['fraction']:.0f}%",r['method'],'EVET' if r['accepted'] else 'HAYIR',f(r['rmse_rpm']),f(r['peak_rpm']),f(r['first_failure_s'])] for r in subset]],[45,78,65,96,98,105])
    p('RMSE/tepe sütunlarındaki N/A, tam koşunun geçerlilik ölçütlerini sağlamadığını gösterir. İlk hata sütunundaki N/A ise geçersiz örnek olmadığını belirtir. İlk hata zamanı 60 s hazırlıktan sonradır. Yük yüzdesi, o hızdaki yüksüz brüt türbin gücüne göredir.')
if failures:
    page();h('7. İlk geçersiz örneğin tanısı')
    tab([['Senaryo','Yöntem','Zaman s','Akış artığı','İterasyon','Marj %'],*[[r['scenario'],r['method'],f(r['first_failure_s']),f"{r['max_flow_error']:.3g}",f(r['iterations'],0),f"{r['compressor_margin']:.3g}"] for r in failures]],[140,72,68,76,61,70])
    p('İlk başarısız ölçüt örneği doğrudan logdan alınır. Pozitif kompresör marjı tek başına kabul için yeterli değildir: çözücü iterasyon sınırına ulaşmış veya akış artığı büyümüş olabilir. Bu kayıtlar gerçek motor kararsızlığının kanıtı olarak yorumlanmaz; simülasyonun geçerlilik sınırıdır.')
page();h('7. PI ve GPR_FF: bütün yük koşulları');img(out/'all_loads.png',640)
p('Yalnız ilk geçersiz çözüme kadar çizilir. Kesikli dikey çizgi ilk geçersiz örneği gösterir; sonrasındaki sayısal toparlanma sonuçları geçerli yapmaz.')
page();h('8. Doğrulama, yorum ve yeniden üretim')
p('60 yeni koşunun her biri 10001 örnek, 60 s hazırlık ve 90 s değerlendirme içerir. 9000 ve 9500 rpm’de %5, %10, %20, %30 rampalı yükler; ayrıca önceki 9500 rpm %20 ve %30 basamak yükleri kullanılır. Üç rampa süresi 0.30, 1.50, 3.00 s’dir. Bütün yöntemlere aynı fiziksel şaft yükü uygulanır.')
p('Geçerlilik: sonlu sinyaller, pozitif yakıt ve kompresör marjı, akış artıklarında en çok 1e-9 ve 200’den az çözücü iterasyonu. Şaft güç-tork dengesi ve son yakıt komutu bağımsız tekrar hesaplanır. İlk geçersiz örnekten sonraki tüm performans sonuçları dışlanır.')
p('Önceki %10 yük koşularının PI, DOB, LESO, UDE, GPIO hız geçmişleri yeni modelde 1e-6 rpm içinde tekrar elde edilmiştir. GPR çevrimiçi ortalaması bağımsız posterior kestiricisiyle 1e-6 lbm/s içinde doğrulanır. Rapor verileri doğrudan kayıtlı CSV dosyalarından yeniden hesaplanır.')
p('Yüksüz modelden gelen nominal yakıtın hızla artması, hız düştüğünde daha az yakıt isteyen bir FF katkısı oluşturabilir. Bu nedenle değişmeyen PI’ye eklenen bu nominal katkı, bilinmeyen yük reddetmesini iyileştirmek zorunda değildir. Bu çalışma olumsuz sonuçları gizlemez ve GPR’yi üstün göstermek için PI kazançlarını değiştirmez.')
p(f"Doymamış ve hız koruması etkin olmayan örneklerde FF/hız eğimi yaklaşık {ff_slopes[9000]:.7f} (9000 rpm) ve {ff_slopes[9500]:.7f} (9500 rpm) lbm/s/rpm bulunur. Bunlar yörünge üzerinden betimleyici doğrusal uyumlardır; bağımsız bitki lineerleştirmesi değildir. Pozitif eğim, mevcut PI oransal etkisinin bir kısmına ters yönde katkı yapar.")
p('Daha iyi bilinmeyen yük reddetmesi için yük ölçümü, yük kestiricisi veya ayrıca tasarlanmış hata geri beslemesi gerekebilir. Bunlar ek bilgi ya da farklı denetleyici tasarımıdır; burada elde edilen sonuçlar bu tür başka yapıların sonucu olarak sunulmaz. Referans izleme üstünlüğü bu sabit referanslı testlerden çıkarılamaz.')
p('Yeniden üretim: MATLAB içinde <b>run_tmats_gpr_ff_benchmarks</b>; ardından <b>summarize_tmats_gpr_ff.py</b>. summary.csv eşlenmiş %10 karşılaştırmasını; all_scenarios.csv bütün koşuları; events.csv 360 olayı; verification.json bağımsız denetimleri içerir.')
p('Kaynaklar: Volkan Aran (2019), <i>Flexible and Robust Control of Heavy Duty Diesel Engine Airpath Using Data Driven Disturbance Observers and GPR Models</i>, bölüm 5.1 ve 6.2.1; Rasmussen ve Williams (2006), <i>Gaussian Processes for Machine Learning</i>, bölüm 2. PI ve gözlemci formülasyonlarının kaynakları önceki mühendislik makalesinde korunmuştur.')
pdf=pdfout/'TMATS_GPR_FF_Observer_Comparison.pdf'
SimpleDocTemplate(str(pdf),pagesize=(595.3,841.9),leftMargin=42,rightMargin=66.3,topMargin=42,bottomMargin=42,title='Ters GPR ileri besleme ve gözlemci karşılaştırması').build(story,onFirstPage=footer,onLaterPages=footer)
base=pdfout/'TMATS_Gaz_Turbini_Bozucu_Bastirma_Makale_TR.pdf'
combined=pdfout/'TMATS_Gaz_Turbini_Bozucu_Bastirma_Makale_TR_GPR_FF.pdf'
# Add a current-results preface, retain the prior article, then append the complete extension.
preface=tmp/'preface.pdf';pref=[]
pref.append(Paragraph('GPR ileri besleme ile genişletilmiş sürüm',hs))
pref.append(Paragraph('Bu dosya önceki mühendislik makalesini ve yeni 60 koşuluk GPR_FF karşılaştırmasını birlikte sunar. Önceki makaledeki beş yöntemli tablolar tarihsel sonuçlardır. Güncel altı yöntemli değerlendirme, sondaki “Ters GPR ile PI ileri besleme desteği” ekindedir.',ps))
for rpm in [9000,9500]:
    pi=next(r for r in matched if r['rpm']==rpm and r['method']=='PI');gp=next(r for r in matched if r['rpm']==rpm and r['method']=='GPR_FF')
    pref.append(Paragraph(f"{rpm} rpm ve %10 rampalı yük: GPR_FF RMSE {gp['rmse_rpm']:.6f} rpm, PI RMSE {pi['rmse_rpm']:.6f} rpm. Göreli değişim {100*(gp['rmse_rpm']/pi['rmse_rpm']-1):+.2f}% (pozitif değer daha kötü). GPR_FF tepe hatası {gp['peak_rpm']:.6f} rpm.",ps))
    faster,equal,slower=recovery_counts[rpm]
    pref.append(Paragraph(f"Buna karşılık ±1 rpm toparlanması {faster}/6 olayda daha kısa ve {equal}/6 olayda eşittir. Ortalama/tepe hata ve eşik toparlanması ayrı değerlendirilmelidir.",ps))
pref.append(Paragraph('GPR_FF nominal ters model desteğidir, bozucu gözlemci değildir. Önceki PI ayarları korunmuş ve bozucu bilgisi GPR’ye verilmemiştir. Başarısız fiziksel çözümlerin tam koşu metrikleri yayımlanmamıştır.',ps))
SimpleDocTemplate(str(preface),pagesize=(595.3,841.9),leftMargin=42,rightMargin=66.3,topMargin=42,bottomMargin=42).build(pref,onFirstPage=footer)
writer=PdfWriter();writer.append(str(preface));writer.append(str(base));writer.append(str(pdf))
with combined.open('wb') as fobj:writer.write(fobj)
original_pages=len(PdfReader(str(base)).pages);supplement_pages=len(PdfReader(str(pdf)).pages)
assert len(PdfReader(str(combined)).pages)==1+original_pages+supplement_pages
for file in [pdf,combined]:
    reader=PdfReader(str(file));assert all((p.extract_text() or '').strip() for p in reader.pages)
files=[root/'tmats_gpr_ff_setup.m',root/'tmats_gpr_ff_sfun.m',root/'build_tmats_gpr_ff_model.m',root/'run_tmats_gpr_ff_benchmarks.m',root/'GasTurbine_Dyn_Template_GPR_FF.mdl',root/'results/inverse_gpr_20260913_150824_698/inverse_gpr_model.mat',Path(__file__),base]
(out/'provenance.json').write_text(json.dumps({'source_directory':str(source),'sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'base_pages':original_pages,'supplement_pages':supplement_pages},indent=2))
print(json.dumps({'matched':matched,'supplement_pages':supplement_pages,'combined_pages':len(PdfReader(str(combined)).pages),'pdf':str(pdf),'extended_report':str(combined)},indent=2))
