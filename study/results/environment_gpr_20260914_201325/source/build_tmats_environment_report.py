"""Typeset the altitude/ISA exact inverse-GPR study from recorded simulations."""
from pathlib import Path
import ast, json, shutil
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
RUN=Path((ROOT/'tmp/environment_directory.txt').read_text().strip())
WORK=ROOT/'tmp/pdfs/environment_controller_tutorial'
WORK.mkdir(parents=True,exist_ok=True)
T=pd.read_csv(RUN/'comparison_summary.csv')
G=pd.read_csv(RUN/'gpr_metrics.csv').iloc[0]
C=pd.read_csv(RUN/'environment_coverage.csv')
TR=pd.read_csv(RUN/'training_points.csv')
TE=pd.read_csv(RUN/'test_200_points.csv')
E=pd.read_csv(RUN/'target_events.csv')
Q=T[T.environment==36].set_index('method')
assert len(T)==73 and len(TR)==1400 and len(TE)==200
assert T[T.method!='BasePI'].Kp.eq(2).all() and T[T.method!='BasePI'].Ki.eq(30).all()
assert not set(zip(TR.environment,TR.source_row)) & set(zip(TE.environment,TE.source_row))

def fmt(v,d=3):
    if pd.isna(v):return '--'
    if np.isinf(v):return 'NR'
    if abs(v)<1e-15:return '0'
    return f'{v:.{d}g}'
def esc(s):return str(s).replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')
def table(headers,rows,caption,align=None):
    align=align or 'l'+'r'*(len(headers)-1)
    return ('\\begin{table}[H]\\centering\\small\n\\setlength{\\tabcolsep}{5pt}\n'
        +r'\begin{tabular}{@{}'+align+r'@{}}\toprule'+'\n'
        +' & '.join(headers)+r'\\\midrule'+'\n'
        +'\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+'\n'
        +r'\bottomrule\end{tabular}\caption{'+caption+r'}\end{table}'+'\n')
def figure(name,caption,width=r'\linewidth'):
    shutil.copy2(RUN/(name+'.pdf'),WORK/(name+'.pdf'))
    return r'\begin{figure}[H]\centering\includegraphics[width='+width+']{'+name+r'.pdf}\caption{'+caption+r'}\end{figure}'+'\n'

source=ast.parse((ROOT/'build_virtual_fuel_pdf.py').read_text(encoding='utf-8'))
pre=next(ast.literal_eval(n.value) for n in source.body if isinstance(n,ast.Assign)
    and any(isinstance(a,ast.Name) and a.id=='PREAMBLE' for a in n.targets))
pre=pre.split(r'\begin{document}')[0]
pre=pre.replace('9000 rpm tuning / 9500 rpm transfer evaluation','Altitude / ISA extension with fixed PI gains')
pre=pre.replace('/Title (Inverse-GPR Virtual-Fuel PI Controller)','/Title (Environment-Aware Exact Inverse-GPR Fuel Control)')
body=(ROOT/'tmats_environment_report_template.tex').read_text(encoding='utf-8')
base=Q.loc['BasePI'];inv=Q.loc['InvGPR_PI_GPRFF'];noff=Q.loc['InvGPR_PI']
summary=(f'At 4000 m, ISA+5 and 9500 rpm, base PI achieved speed RMSE {base.rmse_rpm:.3f} rpm; '
    f'the fixed-gain inverse-GPR PI plus feedforward achieved {inv.rmse_rpm:.3f} rpm. '
    f'The corresponding fuel-ringing scores were {base.ringing_excess_TV_lbm_s:.3f} and '
    f'{inv.ringing_excess_TV_lbm_s:.3f} lbm/s. Both controllers '
    +('passed' if base.accepted and inv.accepted else 'did not both pass')+' the full-run numerical and surge-margin checks.')
targetrows=[]
for field,label,unit in [
 ('rmse_rpm','Speed RMSE','rpm'),('peak_rpm','Peak absolute speed error','rpm'),
 ('iae_rpm_s','Integral absolute speed error','rpm s'),('ringing_excess_TV_lbm_s','Fuel ringing, excess TV','lbm/s'),
 ('max_2s_fuel_range_lbm_s','Largest 2 s fuel range','lbm/s'),('max_fuel_slew_lbm_s2','Largest event-window fuel slew',r'lbm/s$^2$'),
 ('recovery_1pct_speed_s',r'Recovery to 1\% speed band','s'),('settling_to_point1_rpm_s','Recovery to 0.1 rpm band','s'),
 ('minimum_margin_percent','Minimum surge margin',r'\%'),('fuel_peak_lbm_s','Peak fuel','lbm/s'),
 ('fuel_limit_percent','Time at a fuel limit',r'\%'),('gp_outside_percent','Outside GP input rectangle',r'\%'),
 ('compressor_Nc_outside_percent','Outside compressor speed-map range',r'\%')]:
    targetrows.append([label,unit,fmt(base[field]),fmt(inv[field]),fmt(noff[field])])
targettable=table(['Metric','Unit','P','VF','V'],targetrows,
 'Requested off-grid disturbance case. P: base PI; VF: inverse-GPR PI plus FF; V: inverse-GPR PI without FF. Gains are unchanged. Recovery is the worst of six events.', 'llrrr')

rmsechange=100*(inv.rmse_rpm/base.rmse_rpm-1)
ringchange=100*(inv.ringing_excess_TV_lbm_s/base.ringing_excess_TV_lbm_s-1)
targetdiscussion=(f'The new inverse controller changes RMSE by {rmsechange:+.1f}'+r'\%'+
    f' and fuel ringing by {ringchange:+.1f}'+r'\%'+
    f' relative to base PI. Its worst recovery to the supplementary 0.1 rpm band is {fmt(inv.settling_to_point1_rpm_s)} s, '
    f'compared with {fmt(base.settling_to_point1_rpm_s)} s for base PI. '
    f'The minimum surge margins are {fmt(inv.minimum_margin_percent)}'+r'\%'+
    f' and {fmt(base.minimum_margin_percent)}'+r'\%'+', respectively. '
    'These metrics describe different aspects of the transient; a smaller speed RMSE alone does not establish a better fuel command.')
targetdiscussion=targetdiscussion.replace('is NR s,','is not reached before the next event in the first pulse,')
local=pd.read_csv(RUN/'target_gp_local.csv').iloc[0]
localtext=(f'Finite differences of the frozen posterior at the requested setpoint give '
    f'$g_N={local.dFuel_dSpeed:.6f}$ lbm/s per rpm and '
    f'$g_a={local.dFuel_dAcceleration:.6f}$ lbm/s per (rpm/s). '
    f'The ideal local equivalent proportional coefficient is {2*local.dFuel_dSpeed+30*local.dFuel_dAcceleration:.5f}, '
    f'the integral coefficient is {30*local.dFuel_dSpeed:.5f}, and the derivative coefficient is {2*local.dFuel_dAcceleration:.5f}, '
    'in the corresponding speed-domain units. These are an interpretation of the inverse slopes, not a replacement controller. '
    f'When the virtual error is close to zero, the local relation gives a speed-error tail with time constant '
    f'$g_a/g_N\\simeq{local.dFuel_dAcceleration/local.dFuel_dSpeed:.3f}$ s. '
    'This helps explain the longer fine-settling tail despite the lower peak speed deviation.')
eventrows=[]
for k in range(1,7):
    a=E[(E.event==k)&(E.method=='BasePI')].iloc[0]
    b=E[(E.event==k)&(E.method=='InvGPR_PI_GPRFF')].iloc[0]
    eventrows.append([fmt(a.edge_evaluation_s,5),'on' if k%2 else 'off',fmt(a.peak_error_rpm),fmt(b.peak_error_rpm),
        fmt(a.ringing_excess_TV_lbm_s),fmt(b.ringing_excess_TV_lbm_s),fmt(a.recovery_point1_rpm_s),fmt(b.recovery_point1_rpm_s)])
eventtable=table(['Time (s)','Edge',r'Peak P',r'Peak VF',r'Ring P',r'Ring VF',r'$t_{.1}$ P',r'$t_{.1}$ VF'],
    eventrows,'Six individual load transitions. Peak errors are rpm, ringing is lbm/s, and supplementary recovery is seconds. Time is measured from the start of the 90 s evaluation.')

gridtables=[]
for altitude in [0,2500,5000,7500,10000]:
    rows=[]
    for delta in [-30,-20,-10,0,10,20,30]:
        z=T[(T.altitude_m==altitude)&(T.isa_delta_C==delta)].set_index('method');p=z.loc['BasePI'];v=z.loc['InvGPR_PI_GPRFF']
        marker=r'$^*$' if max(p.compressor_Nc_outside_percent,v.compressor_Nc_outside_percent)>0 else ''
        rows.append([f'{delta:+d}'+marker]+[fmt(x) for x in [p.rmse_rpm,v.rmse_rpm,p.ringing_excess_TV_lbm_s,v.ringing_excess_TV_lbm_s,
            p.recovery_1pct_speed_s,v.recovery_1pct_speed_s,p.minimum_margin_percent,v.minimum_margin_percent]])
    gridtables.append(table(['ISA',r'RMSE P',r'RMSE VF',r'Ring P',r'Ring VF',r'$t_{1\%}$ P',r'$t_{1\%}$ VF',r'SM P',r'SM VF'],rows,
        f'{altitude} m: 9500 rpm and 10'+r'\%'+r' shaft-load steps. Units: RMSE rpm; ringing lbm/s; recovery s; SM percent. A dash means a rejected full run. An asterisk flags a compressor corrected-speed map overrun during evaluation.'))
    if altitude==2500:gridtables.append(r'\clearpage'+'\n')

grid=T[T.environment<=35];counts=[]
for method,label in [('BasePI','Base PI'),('InvGPR_PI_GPRFF','InvGPR PI + FF')]:
    z=grid[grid.method==method];ok=z[z.accepted==1]
    counts.append([label,len(z),len(ok),int((z.compressor_Nc_outside_percent>0).sum()),
        int(((z.accepted==1)&(z.compressor_Nc_outside_percent==0)).sum()),fmt(ok.rmse_rpm.median()),fmt(ok.ringing_excess_TV_lbm_s.median())])
counttable=table(['Method','Runs','Accepted','Map flag','Both checks','Median RMSE','Median ring'],counts,
    'Grid summary. Accepted uses solver, positivity, surge margin, finite signals and pre-disturbance trim. Both checks additionally requires the monitored compressor corrected speed to remain inside its map during evaluation. Medians use accepted runs and are not a paired comparison.', 'lrrrrrr')
p=grid[grid.method=='BasePI'].set_index('environment');v=grid[grid.method=='InvGPR_PI_GPRFF'].set_index('environment')
common=p.accepted.eq(1)&v.accepted.eq(1)
paired=(f'Both methods pass in {int(common.sum())} of the 35 grid environments. On these shared accepted cases, the inverse controller '
    f'has lower RMSE in {int((v.loc[common,"rmse_rpm"]<p.loc[common,"rmse_rpm"]).sum())} cases and lower fuel ringing in '
    f'{int((v.loc[common,"ringing_excess_TV_lbm_s"]<p.loc[common,"ringing_excess_TV_lbm_s"]).sum())} cases. '
    'Comparisons exclude rejected full runs from both sides, rather than averaging their valid prefixes.')

failrows=[]
for _,z in T[T.accepted!=1].iterrows():
    d=pd.read_csv(RUN/f'comparison_{int(z.environment):02d}_{z.method}.csv')
    bad=d[d.valid==0]
    if len(bad):
        b=bad.iloc[0];causes=[]
        if b.DOB_SM<=0:causes.append('surge margin')
        if b.max_flow_error>1e-9:causes.append('flow residual')
        if b.DOB_iterations>=200:causes.append('iteration limit')
        if not np.isfinite(b.Nmech) or not np.isfinite(b.Wf):causes.append('nonfinite state')
        reason='/'.join(causes) or 'signal validity'
        at=fmt(b.time_s-60)
    else:reason='pre-test trim';at='before 0'
    failrows.append([int(z.altitude_m),int(z.isa_delta_C),'P' if z.method=='BasePI' else 'VF',at,reason])
failuretable=table(['Altitude (m)','ISA (C)','Method','First failure (s)','Cause'],failrows,
    'Rejected comparison trajectories. Negative times lie in preparation. Full-run RMSE, ringing and recovery are suppressed for these runs.', 'rrlll') if failrows else 'All comparison trajectories passed the numerical criteria.'

eq=pd.read_csv(RUN/'target_inverse_pair_equivalence.csv').iloc[0]
validationtable=table(['Metric','Value'],[
    ['Training observations',1400],['Held-out observations',200],['Training environments',35],['Represented held-out environments',TE.environment.nunique()],
    ['Fuel RMSE (lbm/s)',fmt(G.rmse_lbm_s,6)],['Fuel MAE (lbm/s)',fmt(G.mae_lbm_s,6)],['Maximum absolute error (lbm/s)',fmt(G.max_error_lbm_s,6)],
    [r'$R^2$',fmt(G.r2,8)],[r'Nominal 95\% interval coverage',fmt(100*G.coverage95,4)+r'\%'],
    ['Maximum exported-mean discrepancy (lbm/s)',fmt(G.mean_export_error,3)],['Maximum exported-SD discrepancy (lbm/s)',fmt(G.sd_export_error,3)]],
    'Validation of the frozen exact inverse GP. Export discrepancies compare the Cholesky implementation with MATLAB predict.', 'lr')

range_rows=[]
for col,label in [('speed_rpm','Speed (rpm)'),('acceleration_rpm_s','Acceleration (rpm/s)'),('inlet_temperature_K','Inlet total temperature (K)'),('inlet_pressure_kPa','Inlet total pressure (kPa)'),('fuel_lbm_s','Fuel response (lbm/s)')]:
    range_rows.append([label,fmt(TR[col].min(),5),fmt(TR[col].max(),5),fmt(TE[col].min(),5),fmt(TE[col].max(),5)])
ranges=table(['Variable','Train min','Train max','Test min','Test max'],range_rows,'Observed ranges. A rectangular range is not a guarantee of joint input coverage.','lrrrr')
map_train=TR.speed_rpm/np.sqrt(TR.inlet_temperature_K/288.15)/10000>1.05
map_test=TE.speed_rpm/np.sqrt(TE.inlet_temperature_K/288.15)/10000>1.05
extras={
 'SUMMARY':summary,'TARGET_TABLE':targettable,'TARGET_DISCUSSION':targetdiscussion,'LOCAL_DISCUSSION':localtext,'EVENT_TABLE':eventtable,
 'GRID_TABLES':'\n'.join(gridtables),'COUNTS':counttable,'PAIRED':paired,'FAILURES':failuretable,
 'VALIDATION_TABLE':validationtable,'RANGES':ranges,'TRAIN_MAP_COUNT':str(int(map_train.sum())), 'TEST_MAP_COUNT':str(int(map_test.sum())),
 'TEMP':fmt(base.inlet_temperature_K,7),'PRESSURE':fmt(base.inlet_pressure_kPa,7),
 'POWER':fmt(base.reference_hp,7),'LOAD':fmt(base.load_hp,7),
 'EQ_SPEED':f'{eq.maximum_speed_difference_rpm:.3g}','EQ_FUEL':f'{eq.maximum_fuel_difference_lbm_s:.3g}',
 'RUN_NAME':esc(RUN.name),
 'VALIDATION_FIG':figure('gpr_validation','Four-input coverage and held-out validation. Response intervals include the fitted noise variance; they do not quantify compressor-map uncertainty.'),
 'OVERVIEW':figure('target_overview','Full requested disturbance comparison. The reference remains 9500 rpm. The three extracted-power pulses have different durations but the same amplitude. The inverse curves may overlap.'),
 'ZOOM1':figure('target_zoom_first',r'First 10\% load application and removal. The detailed fuel trace reveals reversals that are less apparent in the speed response.'),
 'ZOOM2':figure('target_zoom_second','Second load pulse and its recovery. The same frozen gains and inverse posterior are used throughout.'),
 'ZOOM3':figure('target_zoom_third','Third, longest load pulse. This window exposes sustained behaviour and unloading recovery.'),
 'COMPONENTS':figure('target_components','Virtual-fuel setpoint and feedback, PI correction terms, and plant versus estimated acceleration around the first pulse.'),
 'HEAT_RMSE':figure('grid_rmse_rpm','Speed RMSE over the 35 environmental combinations. Grey cells marked X are rejected full runs. Both panels use the same colour scale.'),
 'HEAT_RING':figure('grid_ringing_excess_TV_lbm_s','Fuel-ringing score over the grid. These heatmaps do not themselves encode compressor map support; use the flagged tables.'),
 'HEAT_REC':figure('grid_recovery_1pct_speed_s',r'Requested 1\% speed-band recovery. Zero denotes no excursion beyond the band, not instantaneous or perfect speed tracking.'),
 'HEAT_STRICT':figure('grid_settling_to_point1_rpm_s',r'Supplementary recovery to a 0.1 rpm band. This tighter measure can distinguish transients that stay within the 1\% band.'),
 'WORST_ZOOM':figure('grid_worst_zoom',r'A map-flagged grid example: inverse-controller speed drifts outside the 1\% band late in the final unloaded interval and does not recover by the end of evaluation. Numerical convergence is insufficient as a tracking-performance criterion.')}
for key,value in extras.items():body=body.replace('@@'+key+'@@',value)
assert '@@' not in body
(WORK/'Environment_Controller_Tutorial.tex').write_text(pre+r'\begin{document}'+'\n'+body,encoding='utf-8')
for name in ['comparison_summary.csv','target_events.csv','gpr_metrics.csv','training_points.csv','test_200_points.csv','environment_coverage.csv','target_inverse_pair_equivalence.csv','target_gp_local.csv']:
    shutil.copy2(RUN/name,WORK/name)
(RUN/'report_summary.json').write_text(json.dumps({'target_rmse_change_percent':rmsechange,'target_ringing_change_percent':ringchange,
    'training_points':1400,'test_points':200,'training_map_flagged':int(map_train.sum()),'test_map_flagged':int(map_test.sum()),
    'paired_accepted_grid_cases':int(common.sum()),'target':Q.reset_index().to_dict('records')},indent=2))
print(WORK/'Environment_Controller_Tutorial.tex')
