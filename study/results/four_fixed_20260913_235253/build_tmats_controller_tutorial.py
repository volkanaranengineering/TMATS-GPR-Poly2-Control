"""Build the native LaTeX tutorial from verified MATLAB runs and vector figures."""
from pathlib import Path
import ast, re, shutil, json, zipfile
from datetime import datetime
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/pdf'
WORK=ROOT/'tmp/pdfs/fixed_controller_tutorial'
WORK.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
run=Path((ROOT/'tmp/four_fixed_directory.txt').read_text().strip())
tuning=Path((ROOT/'tmp/ff_lowgain_directory.txt').read_text().strip())
T=pd.read_csv(run/'summary.csv')
S=pd.read_csv(tuning/'tuning.csv')
assert len(T)==44 and len(S)==12
baseline=S.iloc[0]
eligible=S[(S.accepted==1)&(S.ringing_excess_TV_lbm_s<=.1*baseline.ringing_excess_TV_lbm_s)]
best=eligible.loc[eligible.rmse_rpm.idxmin()]
kp,ki=float(best.Kp),float(best.Ki)
assert np.allclose(T[T.method.str.startswith('InvGPR')].Kp,kp)
assert np.allclose(T[T.method.str.startswith('InvGPR')].Ki,ki)
methods=['BasePI','BasePI_GPRFF','InvGPR_PI','InvGPR_PI_GPRFF']
names=['base PI','base PI plus GPR FF','inverse-GPR PI','inverse-GPR PI plus GPR FF']
case=T.drop_duplicates('case_index').sort_values('case_index')

def fmt(v,d=3):
    if pd.isna(v): return '--'
    if np.isinf(v): return 'NR'
    if abs(v)<1e-10: return '0'
    return f'{v:.{d}g}'
def esc(s):
    s=str(s).replace('\\',r'\textbackslash{}')
    for a,b in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]: s=s.replace(a,b)
    return s
def table(headers,rows,caption,align=None):
    if align is None: align='l'+'r'*(len(headers)-1)
    return (r'\begin{table}[H]\centering\small'+'\n'+
        r'\begin{tabular}{@{}'+align+r'@{}}\toprule'+'\n'+
        ' & '.join(headers)+r'\\\midrule'+'\n'+
        '\n'.join(' & '.join(map(str,row))+r'\\' for row in rows)+'\n'+
        r'\bottomrule\end{tabular}\caption{'+caption+r'}\end{table}'+'\n')
def perf(field,caption):
    rows=[]
    for _,c in case.iterrows():
        v=T[T.case_index==c.case_index].set_index('method')
        label=f'{int(c.rpm)}/{100*c.fraction:g}'+r'\%/'+('R' if c['shape']=='ramps' else 'S')
        rows.append([label]+[fmt(v.loc[m,field]) for m in methods])
    return table(['rpm/load/type','P','PF','V','VF'],rows,caption+
      r' P: base PI; PF: base PI plus GPR FF; V: inverse-GPR PI; VF: inverse-GPR PI plus FF. R: ramps; S: steps. A dash denotes an invalid full run; NR denotes no recovery before the next event.')
def diagram(content,caption):
    return (r'\begin{figure}[H]\centering\resizebox{\linewidth}{!}{'+content+
        r'}\caption{'+caption+r'}\end{figure}')
def case_sentence(c):
    q=T[T.case_index==c].set_index('method')
    pieces=[]
    for m,n in zip(methods,names):
        z=q.loc[m]
        if not z.accepted:
            pieces.append(n+' failed validity')
        else:
            pieces.append(n+f' gave RMSE {fmt(z.rmse_rpm)} rpm, ringing {fmt(z.ringing_excess_TV_lbm_s)} lbm/s and minimum surge margin {fmt(z.minimum_margin_percent)}'+r'\%')
    return '; '.join(pieces)+'.'

source=ast.parse((ROOT/'build_virtual_fuel_pdf.py').read_text(encoding='utf-8'))
values={}
for node in source.body:
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name) and target.id in ('PREAMBLE','DIAGRAMS'):
                values[target.id]=ast.literal_eval(node.value)
preamble=values['PREAMBLE'].split(r'\begin{document}')[0]
preamble=preamble.replace('9000 rpm tuning / 9500 rpm transfer evaluation','9500 rpm step tuning / fixed-controller comparison')
preamble=preamble.replace('/Title (Inverse-GPR Virtual-Fuel PI Controller)','/Title (From Speed PI to Inverse-GPR Virtual-Fuel Control)')
preamble+=r'\begin{document}'+'\n'
diagrams=values['DIAGRAMS']
gp=next(x for x in diagrams if '600 training samples' in x)
control=diagrams[0].replace('K_p=4',f'K_p={kp:g}').replace('K_i=40',f'K_i={ki:g}')
local=next(x for x in diagrams if 'Ideal local PID' in x)
local=local.replace('Eq. (27)','the discrete filter equations in this report')
reduction=100*(1-best.ringing_excess_TV_lbm_s/baseline.ringing_excess_TV_lbm_s)
rmse_increase=100*(best.rmse_rpm/baseline.rmse_rpm-1)
summary=(f'Lowering the fuel-domain gains from (3,60) to ({kp:g},{ki:g}) reduced ringing by {reduction:.1f}'+
    r'\%'+f' on the 9500 rpm, 5'+r'\%'+f' step tuning case. Speed RMSE changed from {baseline.rmse_rpm:.3f} to {best.rmse_rpm:.3f} rpm ({rmse_increase:.1f}'+r'\%'+
    f' higher). This is a measured damping-versus-tracking tradeoff.')
tunrows=[]
for _,z in S.iterrows():
    label=f'{int(z.candidate)}'+('*' if int(z.candidate)==int(best.candidate) else '')
    tunrows.append([label,fmt(z.Kp),fmt(z.Ki),fmt(z.rmse_rpm),fmt(z.ringing_excess_TV_lbm_s),
        fmt(100*(1-z.ringing_excess_TV_lbm_s/baseline.ringing_excess_TV_lbm_s)),fmt(z.settling_to_point1_rpm_s)])
counts=[int(T[T.method==m].accepted.sum()) for m in methods]
equiv=pd.read_csv(run/'inverse_pair_equivalence.csv')
valid=T[T.accepted==1]
invalid=T[T.accepted==0]
zeros=int((valid.recovery_1pct_speed_s==0).sum())
casesrows=[[f'C{int(c.case_index)}',str(int(c.rpm)),f'{100*c.fraction:g}'+r'\%',esc(c['shape'])] for _,c in case.iterrows()]
note=(f'All {zeros} of {len(valid)} valid runs stayed inside the requested 1'+r'\%'+
      r' band throughout. Zero therefore means no band exit, not instantaneous physical recovery. Use the 0.1 rpm table to distinguish settling.')
final=(f'Valid runs out of eleven: P={counts[0]}, PF={counts[1]}, V={counts[2]}, VF={counts[3]}. '+
       f'{len(invalid)} invalid runs have their full-run performance metrics withheld. All four methods were rerun after the gain selection; archived trajectories were not substituted for these runs.')
if len(invalid):
    final+=' Invalid conditions are listed in the supplementary failure table and identified by dashes below.'
eqtext=(f'Over the common physically valid prefix after handover, the maximum discrepancy between the inverse-GPR pair was {equiv.maximum_speed_difference_rpm.max():.4g} rpm in speed and {equiv.maximum_fuel_difference_lbm_s.max():.4g} lbm/s in fuel. '+
r'These values quantify the constant-feedforward equivalence rather than presuming it from similar plots. Complete-run validity is assessed separately for each trajectory. The residual integral differs by the nominal GP feedforward offset, while the total commands match to numerical precision when the physical solves remain valid.')
reproduction=(r'The primary entry points are \path{run_tmats_ff_lowgain_study.m}, \path{run_tmats_four_fixed_comparison.m}, and \path{report_tmats_four_fixed_comparison.m}. The dedicated tuned model is \path{GasTurbine_Dyn_Template_LowRinging.mdl}; its setup uses 9500 rpm, 5\% steps and the selected fixed pair.'+'\n\n'+
r'\begin{verbatim}'+'\n'+
'outTune = run_tmats_ff_lowgain_study;\n'+
'out = run_tmats_four_fixed_comparison;\n'+
'report_tmats_four_fixed_comparison(out);\n'+
'[MWS,DOB,PTO,VF] = tmats_lowring_setup;\n'+
"sim('GasTurbine_Dyn_Template_LowRinging');\n"+r'\end{verbatim}'+'\n'+
r'The report source package contains the complete generated \LaTeX{} document and vector figures. Compile twice with \path{pdflatex -interaction=nonstopmode Controller_Tutorial.tex}. MATLAB R2018b and the existing adjacent T-MATS library are required to rerun the plant. The exported predictor does not require refitting the GP.'+'\n\n'+
r'Current tuning directory: \path{'+tuning.name+r'}. Final comparison directory: \path{'+run.name+r'}. Both are under the project results directory. Raw MAT/CSV files retain the signals and validity flags. Summary tables, the gain grid, selected gains, failure table and equivalence table accompany the report.'+'\n\n'+
r'Earlier ideation evidence is archived in \path{inverse_gpr_20260913_150824_698}, \path{virtual_fuel_20260913_182229_028}, \path{virtual_fuel_ff_20260913_194955}, \path{virtual_fuel_uq_20260913_201212}, and \path{virtual_fuel_uqup_20260913_231743}. Controller equations and local interpretations are derived for this project; the references support the nominal GP formulation and T-MATS plant framework, not a claimed closed-loop theorem.')
mapping={
'KP':f'{kp:g}','KI':f'{ki:g}','DATE':datetime.now().strftime('%d %B %Y'),
'TUNING_SUMMARY':summary,
'GP_DIAGRAM':diagram(gp,'Frozen inverse-GPR training and online mean evaluation. The saved Cholesky factor supplies uncertainty when scheduling is active.'),
'CONTROL_DIAGRAM':diagram(control,'Virtual-fuel feedback. The FF extension adds the virtual reference fuel before the common limits.'),
'LOCAL_DIAGRAM':diagram(local,'Local ideal PID interpretation of fuel-coordinate PI. The implemented acceleration filter and sample timing remain essential.'),
'CASE_TABLE':table(['Case','Speed [rpm]','Load','Shape'],casesrows,'The eleven final comparison cases. C11 is the tuning condition.','lrll'),
'TUNING_TABLE':table(['ID','$K_p$','$K_i$','RMSE','Ringing','Reduction '+r'[\%]','$T_{0.1}$'],tunrows,'Twelve fixed-gain candidates on 9500 rpm, 5\\% steps. RMSE is in rpm; ringing in lbm/s; recovery in seconds. The asterisk marks the selected pair.'),
'TUNING_DISCUSSION':summary+' '+f'The allowable ringing threshold was {0.1*baseline.ringing_excess_TV_lbm_s:.4f} lbm/s; the selected result was {best.ringing_excess_TV_lbm_s:.4f} lbm/s. The worst recovery to 0.1 rpm changed from {baseline.settling_to_point1_rpm_s:.3f} to {best.settling_to_point1_rpm_s:.3f} s. No further gains were adjusted on the transfer cases.',
'FINAL_SUMMARY':final,
'RMSE_TABLE':perf('rmse_rpm','Full-run speed RMSE [rpm].'),
'RING_TABLE':perf('ringing_excess_TV_lbm_s','Six-window fuel-ringing excess total variation [lbm/s].'),
'RECOVERY_TABLE':perf('recovery_1pct_speed_s','Worst recovery to a 1\\% commanded-speed band [s], measured from transition onset.'),
'STRICT_TABLE':perf('settling_to_point1_rpm_s','Worst recovery to a 0.1 rpm band [s], measured from transition onset.'),
'MARGIN_TABLE':perf('minimum_margin_percent','Minimum surge margin [\\%].'),
'RECOVERY_DISCUSSION':note,
'TARGET_DISCUSSION':case_sentence(11)+' The retuned inverse controller still rings more than base PI on this case, despite its large reduction relative to the earlier inverse-controller gains. Its advantage here is lower speed RMSE, not minimum fuel ringing. The two-second zoom does not replace the full-event recovery measurement; it emphasizes the initial fuel reversals.',
'TRANSFER_DISCUSSION':case_sentence(9)+' This transfer result must be assessed separately from the successful 5\\% tuning result.',
'EQUIVALENCE_DISCUSSION':eqtext,
'REPRODUCTION':reproduction
}
body=(ROOT/'tmats_controller_tutorial_template.tex').read_text(encoding='utf-8')
for key,value in mapping.items():body=body.replace('@@'+key+'@@',value)
assert not re.search(r'@@[A-Z_]+@@',body)
tex=preamble+body
(WORK/'Controller_Tutorial.tex').write_text(tex,encoding='utf-8')
for name in ['tuning_tradeoff','overview_9000','overview_9500','overview_steps','zoom_case_11','zoom_case_09','zoom_case_08','controller_components']:
    shutil.copy2(run/(name+'.pdf'),WORK/(name+'.pdf'))
T.to_csv(WORK/'performance_all_methods.csv',index=False)
S.to_csv(WORK/'tuning_grid.csv',index=False)
invalid.to_csv(WORK/'invalid_runs.csv',index=False)
equiv.to_csv(WORK/'inverse_pair_equivalence.csv',index=False)
(run/'tutorial_summary.json').write_text(json.dumps({'gains':[kp,ki],'ringing_reduction_percent':reduction,'rmse_increase_percent':rmse_increase,'valid_counts':dict(zip(methods,counts)),'valid_runs_inside_1pct':zeros,'total_valid_runs':len(valid)},indent=2))
print('LATEX_READY',WORK/'Controller_Tutorial.tex')



