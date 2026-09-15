"""Assemble the scholarly synthesis from archived results, without retuning."""
from pathlib import Path
import shutil, json, hashlib, re
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parent
WORK=ROOT/'tmp/pdfs/control_evolution'
WORK.mkdir(parents=True,exist_ok=True)
(WORK/'data').mkdir(exist_ok=True)
sources={}
def read(key,relative):
    p=ROOT/relative
    sources[key]={'path':relative,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    shutil.copy2(p,WORK/'data'/f'{key}_{p.name}')
    return pd.read_csv(p)
def fmt(x,n=4):
    if pd.isna(x):return '--'
    if np.isinf(x):return 'NR'
    if abs(x)<1e-10:return '0'
    return f'{x:.{n}g}'
def esc(s):
    return str(s).replace('&',r'\&').replace('_',r'\_').replace('%',r'\%')
def tab(name,headers,rows,caption,align=None,long=False):
    align=align or ('l'+'r'*(len(headers)-1))
    head=' & '.join(headers)+r'\\\midrule'+'\n'
    lines='\n'.join(' & '.join(str(v) for v in row)+r'\\' for row in rows)
    if long:
        text=r'{\small\setlength{\tabcolsep}{4pt}\begin{longtable}{@{}'+align+r'@{}}'+'\n'+r'\caption{'+caption+r'}\label{tab:'+name+r'}\\\toprule '+head+r'\endfirsthead\toprule '+head+r'\endhead\bottomrule\endfoot'+'\n'+lines+r'\end{longtable}}'
    else:
        text=r'\begin{table}[htbp]\centering\small\setlength{\tabcolsep}{4pt}\begin{tabular}{@{}'+align+r'@{}}\toprule'+'\n'+head+lines+'\n'+r'\bottomrule\end{tabular}\caption{'+caption+r'}\label{tab:'+name+r'}\end{table}'
    (WORK/f'table_{name}.tex').write_text(text,encoding='utf-8')

initial=read('D01','results/inverse_gpr_20260913_150824_698/metrics.csv')
early=read('D02','results/virtual_fuel_uqup_20260913_231743/comparison_all_methods.csv')
low=read('D03','results/ff_lowgain_20260913_234549/tuning.csv')
fixed=read('D04','results/four_fixed_20260913_235253/summary.csv')
envfit=read('D05','results/environment_gpr_20260914_201325/gpr_metrics.csv')
env=read('D06','results/environment_gpr_20260914_201325/comparison_summary.csv')
rem=read('D07','results/gpr_remedies_20260914_220633/remedy_comparison.csv')
slopes=read('D08','results/gpr_remedies_20260914_220633/inverse_slope_diagnosis.csv')
ablation=read('D09','results/gpr_remedies_20260914_220633/ablation_worker_01.csv')
broad=read('D10','results/r3_ambient_cycle_20260915/summary.csv')
coverage=read('D11','results/r3_covered_cycle_20260915_final/coverage_summary.csv')
cycle=read('D12','results/r3_poly2_challenger_20260915/summary.csv')
polyfit=read('D13','results/poly2_inverse_20260915/fit_metrics.csv')
coef=read('D14','results/poly2_inverse_20260915/coefficients.csv')
tune=read('D15','results/poly2_tune9250_20260915/tuning_scores.csv')
val=read('D16','results/poly2_tune9250_20260915/validation_summary.csv')
selected=read('D17','results/poly2_tune9250_20260915/selected.csv').iloc[0]
held=read('D18','results/environment_gpr_20260914_201325/test_200_points.csv')
polycoverage=read('D19','results/r3_poly2_challenger_20260915/coverage_summary.csv')
checks=read('D20','results/poly2_tune9250_20260915/verification.csv')
samegain=read('D21','results/virtual_fuel_ff_20260913_194955/same_gains_ablation.csv')
model_path=ROOT/'results/poly2_inverse_20260915/poly2_model.json'
sources['D22']={'path':model_path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(model_path.read_bytes()).hexdigest()}
shutil.copy2(model_path,WORK/'data'/'D22_poly2_model.json')
em=['VirtualFuel','VirtualFuelFF','VirtualFuelUQ','VirtualFuelUQUp']
en=['Initial inverse PI','FF + retuned PI','SD down','SD up']
fm=['BasePI','BasePI_GPRFF','InvGPR_PI','InvGPR_PI_GPRFF']
fn=['Base PI','Base PI + FF','Inverse PI','Inverse PI + FF']
cn=['Base PI','R3 feedback only','R3 + GPR FF','R3 + Poly2 FF']
assert len(early)==40 and len(fixed)==44 and len(rem)==180
assert len(held)==200 and held.environment.nunique()==33
assert selected.candidate==34 and np.allclose(selected[['Kp','Ki','Kd']].to_numpy(dtype=float),[.025,.14,.00125])
assert tune.accepted.eq(1).all() and val.accepted.eq(1).all()
assert len(checks)==35 and polycoverage.covered_all.eq(1).all()
assert samegain.max_speed_difference_rpm.max()<1.38e-7

tab('early_example',['Method','RMSE','Peak','Ringing','Valid/10'],[
    [label]+[fmt(early[(early.case_index==2)&(early.method==method)].iloc[0][k]) for k in ['rmse_rpm','peak_rpm','ringing_excess_TV_lbm_s']]+[f'{int(early[early.method==method].accepted.sum())}/10'] for method,label in zip(em,en)],
    r'Early-stage 9000 rpm / 10\% shaft-load ramps. RMSE and peak are rpm; ringing is lbm/s. Validity counts cover all ten scenarios (D02).')
for field,name,unit in [('rmse_rpm','early_rmse','speed RMSE (rpm)'),('ringing_excess_TV_lbm_s','early_ring','load-edge fuel ringing (lbm/s)')]:
    rows=[]
    for i,c in early.drop_duplicates('case_index').iterrows():
        q=early[early.case_index==c.case_index].set_index('method')
        rows.append([f'{int(c.rpm)}/{100*c.fraction:g}/'+('R' if c['shape']=='ramps' else 'S')]+[fmt(q.loc[m,field]) for m in em])
    tab(name,[r'rpm/\%/type','Initial','FF retune','SD down','SD up'],rows,f'All early scenarios: {unit}. R: ramped load; S: stepped load. A dash is a rejected full trajectory, not zero (D02).')
tab('lowgain',['$K_p$','$K_i$','RMSE','Ringing','Fine settling'],[[fmt(z[k]) for k in ['Kp','Ki','rmse_rpm','ringing_excess_TV_lbm_s','settling_to_point1_rpm_s']] for _,z in low.iterrows()],r'Fixed-gain search at 9500 rpm / 5\% load steps. RMSE in rpm, ringing in lbm/s, fine settling in seconds (D03).')
for field,name,unit in [('rmse_rpm','fixed_rmse','speed RMSE (rpm)'),('ringing_excess_TV_lbm_s','fixed_ring','fuel ringing (lbm/s)'),('settling_to_point1_rpm_s','fixed_fine','persistent recovery to 0.1 rpm (s)')]:
    rows=[]
    for _,c in fixed.drop_duplicates('case_index').iterrows():
        q=fixed[fixed.case_index==c.case_index].set_index('method')
        rows.append([f'{int(c.rpm)}/{100*c.fraction:g}/'+('R' if c['shape']=='ramps' else 'S')]+[fmt(q.loc[m,field]) for m in fm])
    tab(name,[r'rpm/\%/type','P','PF','V','VF'],rows,f'Four fixed controllers: {unit}. P: base PI; PF: base PI + FF; V: inverse PI; VF: inverse PI + FF (D04).')
q=fixed[fixed.case_index==11].set_index('method')
tab('fixed_target',['Method','RMSE','Peak','Ringing','Fine settling'],[[n]+[fmt(q.loc[m,k]) for k in ['rmse_rpm','peak_rpm','ringing_excess_TV_lbm_s','settling_to_point1_rpm_s']] for n,m in zip(fn,fm)],r'9500 rpm / 5\% steps at the final fixed fuel-domain gains 2/30. Units: rpm, rpm, lbm/s, s (D04).')
tab('fits',['Inverse model','Train/test','Test RMSE','MAE','$R^2$',r'95\% coverage'],[
['2-input exact GP','600/100']+[fmt(initial.iloc[0][k],6) for k in ['rmse_lbm_s','mae_lbm_s','r2','coverage95']],
['4-input exact GP','1400/200']+[fmt(envfit.iloc[0][k],6) for k in ['rmse_lbm_s','mae_lbm_s','r2','coverage95']],
['4-input Poly2','1400/200']+[fmt(polyfit.iloc[1][k],6) for k in ['rmse_lbm_s','mae_lbm_s','r2']]+['N/A']],r'Held-out inverse fuel prediction. RMSE/MAE in lbm/s; coverage is a fraction. The two GP rows use different datasets; only the 4-input GP and Poly2 share the same split (D01, D05, D13).')
target=rem[rem.environment==36]
tab('remedies',['Method','RMSE','Peak','Ringing','Fine settling'],[[n]+[fmt(z[k]) for k in ['rmse_rpm','peak_rpm','ringing_excess_TV_lbm_s','settling_to_point1_rpm_s']] for n,(_,z) in zip(['Base PI','Previous inverse PI','R1','R2','R3 + static FF'],target.iterrows())]+[['Matched PID + FF']+[fmt(ablation.iloc[0][k]) for k in ['rmse_rpm','peak_rpm','ringing_excess_TV_lbm_s','settling_to_point1_rpm_s']]],r'4000 m / ISA+5 / 9500 rpm / 10\% steps. Units: rpm, rpm, lbm/s, s. R1--R3 are tuned at this target; the matched PID ablates inverse feedback normalization (D07, D09).')
grid=rem[rem.environment<=35]
rows=[]
for mid in [2,3,4,5]:
    a=grid[grid.method_id==mid].set_index('environment');b=grid[grid.method_id==1].set_index('environment')
    both=a.accepted.eq(1)&(a.rmse_rpm<b.rmse_rpm)&(a.ringing_excess_TV_lbm_s<b.ringing_excess_TV_lbm_s)
    mapok=(a.compressor_Nc_outside_percent==0)&(b.compressor_Nc_outside_percent==0)
    rows.append([['Previous inverse','R1','R2','R3 + FF'][mid-2],f'{int(a.accepted.sum())}/35',f'{int(both.sum())}/35',f'{int((both&mapok).sum())}/{int(mapok.sum())}',int((a.fallback_percent.fillna(0)>0).sum())])
tab('remedy_grid',['Method','Accepted','Both better','Both / map clean','Fallback cases'],rows,r"Frozen-gain environmental transfer. ``Both better'' means lower RMSE and ringing than the paired base PI. Rejected trajectories do not count as wins. Map-clean denominators use both trajectories (D07).")
for name,df,names in [('broad',broad,['Base PI','R3 + static FF']),('cycle',cycle,cn)]:
    fields=['rmse_rpm','ramp_rmse_rpm','hold_rmse_rpm','segment_excess_TV_lbm_s','hold_excess_TV_lbm_s','peak_error_rpm']
    tab(name,['Metric']+names,[[lab]+[fmt(z[k],6) for _,z in df.iterrows()] for lab,k in zip(['Full RMSE (rpm)','Ramp RMSE (rpm)','Hold RMSE (rpm)','Segment reversal (lbm/s)','Hold reversal (lbm/s)','Peak error (rpm)'],fields)],('Broad 9025--9975 rpm cycle (D10).' if name=='broad' else 'Final covered 9450--9550 rpm cycle: same gains and frozen models. All four trajectories pass box/hull coverage, with no fallback or monitored map-speed overrun (D12, D19).'))
fields=['rmse_rpm','peak_rpm','iae_rpm_s','ringing_excess_TV_lbm_s','settling_to_point1_rpm_s','recovery_1pct_speed_s','max_fuel_slew_lbm_s2','minimum_margin_percent']
labs=['RMSE (rpm)','Peak error (rpm)','IAE (rpm s)','Ringing (lbm/s)','Fine recovery (s)',r'1\% recovery (s)','Peak slew (lbm/s$^2$)',r'Minimum SM (\%)']
tab('tune',['Metric','Base PI','Original Poly2','Retuned Poly2'],[[lab]+[fmt(tune[tune.candidate==i].iloc[0][k],6) for i in [0,1,34]] for lab,k in zip(labs,fields)],r'9250 rpm / 0 m / ISA 0 / 10\% load steps. The retune changes only the gains (D15).')
tab('validation',['Metric','Base PI','Original Poly2','Retuned Poly2'],[[lab]+[fmt(z[k],6) for _,z in val.iterrows()] for lab,k in zip(labs[:6],fields[:6])],r'Frozen gains evaluated on 5\% load steps at the same operating point. This is amplitude transfer, not an independent speed/environment test (D16).')
tab('polycoef',['Term','Coefficient (lbm/s)'],[[r'$'+str(z.term).replace('*','').replace('z1','z_1').replace('z2','z_2').replace('z3','z_3').replace('z4','z_4')+'$',fmt(z.coefficient_lbm_s,12)] for _,z in coef.iterrows()],r'Full quadratic coefficients in standardized coordinates. All 15 terms are retained (D14).')
tab('tune_all',['ID','$K_p$','$K_i$','$K_d$','RMSE','Ringing','$J$'],[[int(z.candidate)]+[fmt(z[k],6) for k in ['Kp','Ki','Kd','rmse_rpm','ringing_excess_TV_lbm_s','joint_score']] for _,z in tune[tune.candidate>0].iterrows()],r'All 34 tested Poly2 gain settings at 9250 rpm. All were numerically accepted; candidate 34 minimizes the stated joint score (D15).',long=True)
rows=[]
for e in range(1,36):
    q=grid[grid.environment==e].set_index('method_id');b=q.loc[1]
    row=[int(b.altitude_m),f'{b.isa_delta_C:+g}',fmt(b.rmse_rpm),fmt(b.ringing_excess_TV_lbm_s)]
    row += [fmt(q.loc[mid,'rmse_rpm']/b.rmse_rpm) for mid in [2,3,4,5]]
    row += [fmt(q.loc[5,'ringing_excess_TV_lbm_s']/b.ringing_excess_TV_lbm_s),fmt(q.loc[5,'fallback_percent'])]
    rows.append(row)
tab('environment_all',['$h$','ISA','P RMSE','P ring','V/P','R1/P','R2/P','R3/P','R3 ring/P',r'FB\%'],rows,r'Complete 35-condition transfer audit, 9500 rpm / 10\% load steps. The four middle ratios are speed RMSE relative to base PI. V: previous inverse PI; R3 includes static FF. A dash means rejected. FB: R3 fallback percentage (D07).',long=True)
tab('slopes',['Condition','$g_N$','$g_a$','$K_{p,eq}$','$K_{i,eq}$','$K_{d,eq}$'],[[n]+[fmt(slopes[slopes.environment==i].iloc[0][k],5) for k in ['speed_slope','accel_slope','equivalent_P','equivalent_I','equivalent_D']] for i,n in [(1,'0 m / ISA 0'),(36,'4000 m / ISA+5'),(35,'10000 m / ISA-30')]],r'Nominal inverse slopes and ideal local equivalent gains for the 2/30 fuel-domain PI. Negative $g_N$ reverses integral feedback sign (D08).')

figures={
'fixed_zoom':('fixed_controller_tutorial','zoom_case_11.pdf'),
'fixed_tradeoff':('fixed_controller_tutorial','tuning_tradeoff.pdf'),
'env_validation':('environment_controller_tutorial','gpr_validation.pdf'),
'env_zoom':('environment_controller_tutorial','target_zoom_first.pdf'),
'env_grid':('environment_controller_tutorial','grid_rmse_rpm.pdf'),
'remedy_zoom':('gpr_remedies','remedy_load_zoom.pdf'),
'remedy_unload':('gpr_remedies','remedy_unload_zoom.pdf'),
'remedy_grid':('gpr_remedies','remedy_grid_ratios.pdf'),
'broad_environment':('r3_cycle','cycle_environment.pdf'),
'broad_overview':('r3_cycle','cycle_overview.pdf'),
'covered_zoom':('r3_covered','cycle_zoom_1.pdf'),
'static_components':('r3_static_ff','static_ff_components.pdf'),
'poly_overview':('r3_poly2','cycle_overview.pdf'),
'poly_zoom':('r3_poly2','cycle_zoom_1.pdf'),
'tune_overview':('poly9250','poly9250_overview.pdf'),
'tune_zoom':('poly9250','poly9250_zoom.pdf'),
'tune_search':('poly9250','poly9250_tuning.pdf')}
for name,(directory,filename) in figures.items():
    p=ROOT/'tmp/pdfs'/directory/filename
    shutil.copy2(p,WORK/f'{name}.pdf')
    sources['figure_'+name]={'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for name in ['early_zoom','schedules','realized_schedule']:
    p=WORK/f'{name}.pdf'
    sources['figure_'+name]={'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(WORK/'code').mkdir(exist_ok=True)
code_names=['tmats_gpr_ff_sfun.m','tmats_virtual_fuel_sfun.m','tmats_virtual_fuel_ff_sfun.m',
 'tmats_virtual_fuel_uq_sfun.m','tmats_virtual_fuel_uqup_sfun.m','tmats_uncertainty_gain_factor.m',
 'tmats_uncertainty_increasing_gain_factor.m','tmats_environment_vf_sfun.m','tmats_gpr_remedy_sfun.m',
 'tmats_r3_feedback_only_sfun.m','tmats_r3_poly2_sfun.m','tmats_poly2_mean_gradient.m',
 'tmats_gp_mean_gradient.m','fit_tmats_environment_gpr.m','fit_tmats_poly2_inverse.py',
 'tmats_fixed_comparison_metrics.m','tmats_r3_covered_cycle_setup.m','run_tmats_poly9250.m',
 'select_tmats_poly9250.m','validate_tmats_poly9250.m','verify_tmats_poly9250.py',
 'plot_control_evolution.m','audit_control_evolution.py','build_control_evolution_paper.py']
for name in code_names:
    p=ROOT/name;shutil.copy2(p,WORK/'code'/name)
    sources['code_'+name]={'path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

rows=[]
for key,info in sources.items():
    if key.startswith('D'):rows.append(r'\texttt{'+key+r'} & \path{'+info['path']+r'}\\')
(WORK/'data_register.tex').write_text(r'{\footnotesize\begin{longtable}{@{}p{.07\linewidth}p{.90\linewidth}@{}}\toprule ID & Archived evidence file\\\midrule\endhead'+'\n'+'\n'.join(rows)+r'\bottomrule\end{longtable}}',encoding='utf-8')
for name in ['control_evolution_paper.tex','control_evolution_diagrams.tex','control_evolution_references.tex']:
    shutil.copy2(ROOT/name,WORK/name)
sources['manuscript']={'path':'control_evolution_paper.tex','sha256':hashlib.sha256((ROOT/'control_evolution_paper.tex').read_bytes()).hexdigest()}
(WORK/'evidence_manifest.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
print('Assembled',len(sources),'evidence entries;',len(list(WORK.glob('table_*.tex'))),'generated tables.')
