"""Create the measured three-remedy addendum as native LaTeX."""
from pathlib import Path
import ast,json,shutil
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
RUN=Path((ROOT/'tmp/remedies_directory.txt').read_text().strip())
WORK=ROOT/'tmp/pdfs/gpr_remedies';WORK.mkdir(parents=True,exist_ok=True)
T=pd.read_csv(RUN/'remedy_comparison.csv');U=pd.read_csv(RUN/'tuning_summary.csv');D=pd.read_csv(RUN/'inverse_slope_diagnosis.csv')
assert len(T)==180 and T[T.environment==36].accepted.eq(1).all()
target=T[T.environment==36].set_index('method_id');base=target.loc[1];old=target.loc[2]
ablation=pd.read_csv(RUN/'ablation_worker_01.csv').iloc[0]
def fmt(x,n=3):
 if pd.isna(x):return '--'
 if np.isinf(x):return 'NR'
 if x==0:return '0'
 return f'{x:.{n}g}'
def table(headers,rows,caption,align=None):
 return ('\\begin{table}[H]\\centering\\small\\setlength{\\tabcolsep}{5pt}\n'+r'\begin{tabular}{@{}'+(align or 'l'+'r'*(len(headers)-1))+r'@{}}\toprule'+'\n'+
  ' & '.join(headers)+r'\\\midrule'+'\n'+'\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+'\n'+r'\bottomrule\end{tabular}\caption{'+caption+r'}\end{table}'+'\n')
def fig(name,caption):
 shutil.copy2(RUN/(name+'.pdf'),WORK/(name+'.pdf'))
 return r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{'+name+r'.pdf}\caption{'+caption+r'}\end{figure}'+'\n'
short=['Base PI','Previous inverse','R1','R2','R3'];rows=[]
for j in range(1,6):
 z=target.loc[j];rows.append([short[j-1],fmt(z.rmse_rpm,4),fmt(z.ringing_excess_TV_lbm_s,4),fmt(z.peak_rpm,4),fmt(z.recovery_1pct_speed_s),fmt(z.settling_to_point1_rpm_s),fmt(z.minimum_margin_percent)])
targettable=table(['Method','RMSE','Ringing','Peak error',r'$t_{1\%}$',r'$t_{0.1}$','Min. SM'],rows,
 r'4000 m/ISA+5, 9500 rpm, 10\% shaft-load steps. RMSE and peak error: rpm; ringing: lbm/s; recovery: s; surge margin: percent. NR means no persistent recovery before the next edge or evaluation end.')
extra=table(['Method','IAE','Peak fuel','Peak slew','GP outside','Fallback'],[
 [short[j-1]]+[fmt(target.loc[j,f]) for f in ['iae_rpm_s','fuel_peak_lbm_s','max_fuel_slew_lbm_s2','gp_outside_percent','fallback_percent']] for j in range(1,6)],
 'Complementary target metrics: IAE rpm s; peak fuel lbm/s; peak event-window slew lbm/s squared; GP input-range excursions and fallback usage percent. A dash denotes an unavailable/not-applicable diagnostic.')
rows=[];selected=[]
for j in range(3,6):
 z=target.loc[j];rows.append([f'R{j-2}',fmt(z.Kp,5),fmt(z.Ki,5),fmt(z.Kd,5),fmt(z.accelTau,4),fmt(z.accelWeight,4)])
 selected.append(U[(U['mode']==j-2)&np.isclose(U.Kp,z.Kp)&np.isclose(U.Ki,z.Ki)&np.isclose(U.Kd,z.Kd)&np.isclose(U.accelTau,z.accelTau)&np.isclose(U.accelWeight,z.accelWeight)].sort_values('joint_score').iloc[0])
gainstable=table(['Remedy',r'$K_p$',r'$K_i$',r'$K_d$',r'$\tau_a$ (s)',r'$\beta$'],rows,
 'Selected parameters. R1/R2 gains act on virtual fuel; R3 gains act on normalized speed/acceleration. Kd is used only by R3, beta only by R2. Their numerical gains are not directly comparable across architectures.')
claims=[]
for j in range(3,6):
 z=target.loc[j];claims.append(f'R{j-2}: RMSE changes by {100*(z.rmse_rpm/base.rmse_rpm-1):+.1f}'+r'\%'+
  f' and ringing by {100*(z.ringing_excess_TV_lbm_s/base.ringing_excess_TV_lbm_s-1):+.1f}'+r'\%'+
  ' relative to base PI. Relative to the previous inverse controller, the changes are '+
  f'{100*(z.rmse_rpm/old.rmse_rpm-1):+.1f}'+r'\%'+f' and {100*(z.ringing_excess_TV_lbm_s/old.ringing_excess_TV_lbm_s-1):+.1f}'+r'\%'+', respectively.')
counts=[];gr=T[T.environment<=35];bg=gr[gr.method_id==1].set_index('environment');gridrows=[]
for j in range(2,6):
 q=gr[gr.method_id==j].set_index('environment');valid=q.accepted.eq(1)&bg.accepted.eq(1);inside=q.compressor_Nc_outside_percent.eq(0)&bg.compressor_Nc_outside_percent.eq(0)
 both=valid&q.rmse_rpm.lt(bg.rmse_rpm)&q.ringing_excess_TV_lbm_s.lt(bg.ringing_excess_TV_lbm_s)
 counts.append([short[j-1],int(valid.sum()),int((valid&q.rmse_rpm.lt(bg.rmse_rpm)).sum()),int((valid&q.ringing_excess_TV_lbm_s.lt(bg.ringing_excess_TV_lbm_s)).sum()),int(both.sum()),int((both&inside).sum()),int((valid&q.recovery_1pct_speed_s.eq(0)).sum())])
counttable=table(['Method','Accepted','RMSE wins','Ring wins','Both','Both/in map',r'No 1\% exit'],counts,
 r'Counts out of 35 grid conditions. All wins compare paired accepted cases with base PI. Both/in map additionally excludes the monitored compressor corrected-speed overruns. No 1\% exit counts trajectories staying inside the band throughout all six event windows.')
ablationtable=table(['Feedback','RMSE (rpm)','Ringing (lbm/s)',r'$t_{0.1}$ (s)'],[
 ['R3 normalized GPR',fmt(target.loc[5,'rmse_rpm'],5),fmt(target.loc[5,'ringing_excess_TV_lbm_s'],5),fmt(target.loc[5,'settling_to_point1_rpm_s'])],
 ['Matched-gain filtered PID',fmt(ablation.rmse_rpm,5),fmt(ablation.ringing_excess_TV_lbm_s,5),fmt(ablation.settling_to_point1_rpm_s)]],
 'Diagnostic ablation at the target: identical gains, filtering, feedforward, startup and load, with raw sensed speed error and acceleration replacing the normalized inverse signals.')
rejected=gr[gr.accepted.ne(1)]
rejecttext='All new grid runs passed numerical acceptance.' if rejected.empty else 'Rejected grid cases: '+ '; '.join(f"{short[int(z.method_id)-1]} at {int(z.altitude_m)} m/ISA{int(z.isa_delta_C):+d}" for _,z in rejected.iterrows())+'. These cases receive no performance score.'
fallback=gr[(gr.method_id==5)&gr.fallback_percent.gt(0)]
gridtext=rejecttext+f' R3 used its speed-feedback fallback in {len(fallback)} of the 35 environments. '
gridtext+='R3 improves both metrics in all 35 cases, including all 25 cases without a monitored compressor-map speed overrun. R1 improves both in 7 cases and R2 in 9; eight R2 cases are rejected. The most broadly supported choice is R3; R2 is the smoothest target-case option but its target tuning does not establish reliable grid-wide transfer. R1 is a minimal modification with a remaining slow-tail and slope-sign limitation.'
for c in range(1,36):
 q=gr[gr.environment==c].set_index('method_id');z=q.loc[1];label=f'{int(z.altitude_m)}/{int(z.isa_delta_C):+d}'
 if q.compressor_Nc_outside_percent.max()>0:label+=r'$^*$'
 gridrows.append([label]+[fmt(q.loc[j,f]) for j in [3,4,5] for f in ['rmse_rpm','ringing_excess_TV_lbm_s']])
gridtables=table(['m/ISA',r'RMSE R1',r'Ring R1',r'RMSE R2',r'Ring R2',r'RMSE R3',r'Ring R3'],gridrows,
 'Frozen-gain grid transfer: RMSE rpm, ringing lbm/s. Asterisk: compressor-map speed overrun in at least one compared method. Dash: rejected full run.')
diagrows=[]
for c in [36,33]:
 z=D[D.environment==c].iloc[0];diagrows.append([f'{int(z.altitude_m)}/{int(z.isa_delta_C):+d}',fmt(z.speed_slope,6),fmt(z.accel_slope,6),fmt(z.equivalent_P,5),fmt(z.equivalent_I,5),fmt(z.inverse_tail_tau_s,5)])
diagtable=table(['m/ISA',r'$g_N$',r'$g_a$',r'$K_{P,eq}$',r'$K_{I,eq}$',r'$g_a/g_N$ (s)'],diagrows,'Verified derivatives of the unchanged GP at 9500 rpm and zero acceleration. The previous gains are Kp=2, Ki=30.')
trainrows=[]
for z in selected:trainrows.append([int(z.candidate),int(z['mode']),fmt(z.rmse_ratio),fmt(z.ringing_ratio),fmt(z.joint_score),'yes' if z.beats_base_both else 'no'])
selectiontable=table(['Candidate','Remedy','RMSE/base','Ring/base','Joint score','Both lower'],trainrows,'Winner of each remedy family under the declared joint score. These target-case results are tuning results, not independent hold-out validation.','rrrrrl')
txt=(ROOT/'tmats_remedy_report_template.tex').read_text(encoding='utf-8')
replacement={'TARGET_TABLE':targettable,'EXTRA_TARGET':extra,'GAINS':gainstable,'TARGET_CLAIMS':'\n\n'.join(claims),'GRID_COUNTS':counttable,'GRID_TABLES':gridtables,'DIAG_TABLE':diagtable,'SELECTION_TABLE':selectiontable,
 'ABLATION_TABLE':ablationtable,'GRID_INTERPRETATION':gridtext,
 'CANDIDATES':str(len(U)),'NEGATIVE':str(int((D.speed_slope<=0).sum())),'GRAD_CHECK':f'{D.gradient_check.max():.3g}',
 'TUNING_FIG':fig('remedy_tuning','All accepted tuning candidates. Dotted lines mark base-PI performance, black circles mark selected remedies, and the black star marks the previous inverse PI.'),
 'OVERVIEW':fig('remedy_overview','Full target evaluation with identical load timing and amplitude. The previous inverse controller is retained as an explicit comparator.'),
 'LOAD_ZOOM':fig('remedy_load_zoom','Detailed first load application: each remedy is compared with base PI and the previous inverse controller.'),
 'UNLOAD_ZOOM':fig('remedy_unload_zoom','Detailed first unloading event. Smoother application alone is insufficient; unloading is also included in the ringing score.'),
 'GRID_FIG':fig('remedy_grid_ratios','Frozen-parameter transfer. Ratios below one improve on base PI; colour is capped at two while numeric labels retain larger values. X denotes a rejected full run.'),
 'COLD_FIG':fig('remedy_cold_case','The previously problematic 5000 m/ISA-30 case. The compressor-map limitation remains; controller guards do not validate the missing physical map range.'),
 'RUN':RUN.name}
for key,value in replacement.items():txt=txt.replace('@@'+key+'@@',value)
assert '@@' not in txt
a=ast.parse((ROOT/'build_virtual_fuel_pdf.py').read_text(encoding='utf-8'));pre=next(ast.literal_eval(n.value) for n in a.body if isinstance(n,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='PREAMBLE' for z in n.targets)).split(r'\begin{document}')[0]
pre=pre.replace('9000 rpm tuning / 9500 rpm transfer evaluation','Three remedies / measured feedback tradeoffs')
pre=pre.replace('INVERSE-GPR VIRTUAL-FUEL PI','INVERSE GPR: THREE REMEDIES')
(WORK/'GPR_Three_Remedies.tex').write_text(pre+r'\begin{document}'+'\n'+txt,encoding='utf-8')
for name in ['remedy_comparison.csv','tuning_summary.csv','inverse_slope_diagnosis.csv']:shutil.copy2(RUN/name,WORK/name)
(RUN/'report_summary.json').write_text(json.dumps({'target':target.reset_index().to_dict('records'),'grid_counts':counts,'candidates':len(U)},indent=2))
print(WORK/'GPR_Three_Remedies.tex')
