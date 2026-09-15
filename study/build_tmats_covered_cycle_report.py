"""Report the constrained GP-domain cycle without retuning either controller."""
from pathlib import Path
import ast,shutil
import pandas as pd
import numpy as np
root=Path(__file__).resolve().parent;run=root/'results/r3_covered_cycle_20260915_final';work=root/'tmp/pdfs/r3_covered';work.mkdir(parents=True,exist_ok=True)
m=pd.read_csv(run/'summary.csv').set_index('method');c=pd.read_csv(run/'coverage_summary.csv').set_index('method')
assert m.accepted.eq(1).all() and c.covered_all.eq(1).all()
assert m.loc['R3','gp_outside_percent']==0 and m.loc['R3','fallback_percent']==0 and m.Nc_outside_percent.eq(0).all()
def f(x):
 if np.isnan(x):return '--'
 if np.isinf(x):return 'NR'
 return f'{x:.4g}'
def table(headers,rows,caption,alignment=None):
 return r'\begin{table}[H]\centering\small\begin{tabular}{'+(alignment or ('l'+'r'*(len(headers)-1)))+r'}\toprule'+'\n'+' & '.join(headers)+r'\\\midrule'+'\n'+'\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+'\n'+r'\bottomrule\end{tabular}\caption{'+caption+r'}\end{table}'
def fig(name,caption):
 shutil.copy2(run/(name+'.pdf'),work/(name+'.pdf'))
 return r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{'+name+r'.pdf}\caption{'+caption+r'}\end{figure}'
fields=[('Full RMSE (rpm)','rmse_rpm'),('Ramp RMSE (rpm)','ramp_rmse_rpm'),('Hold RMSE (rpm)','hold_rmse_rpm'),('Peak error (rpm)','peak_error_rpm'),('IAE (rpm s)','iae_rpm_s'),('Segment excess TV (lbm/s)','segment_excess_TV_lbm_s'),('Hold excess TV (lbm/s)','hold_excess_TV_lbm_s'),('Worst hold recovery (s)','max_recovery_1pct_s'),('Minimum surge margin (percent)','minimum_SM_percent'),('Peak fuel (lbm/s)','fuel_peak_lbm_s'),('Maximum fuel slew (lbm/s squared)','max_fuel_slew_lbm_s2'),('Compressor Nc outside (percent)','Nc_outside_percent'),('R3 fallback active (percent)','fallback_percent'),('R3 GP range flag (percent)','gp_outside_percent')]
summary=table(['Metric','Base PI','R3'],[[label,f(m.loc['BasePI',k]),f(m.loc['R3',k])] for label,k in fields],'The same 120 s test and nonlinear plant are used for both controllers. Recovery is from each hold start to persistent entry into the 1 percent speed band.')
coverage=table(['Audit','Base PI shadow','R3 actual'],[[label,f(c.loc['BasePI',k]),f(c.loc['R3',k])] for label,k in [('Query count','query_count'),('Strict box outside (percent)','strict_box_outside_percent'),('Tolerant box outside (percent)','box_outside_percent'),('Joint hull outside (percent)','hull_outside_percent'),('Largest kernel NN distance','NN_distance_max'),('Training LOO NN 95th percentile','training_LOO_NN95'),('NN above training 95th (percent)','NN_above_training95_percent')]],'Three branches at every evaluation sample: setpoint, dynamic feedback and static feedback. Base PI has no online GP; its shadow queries are constructed offline with the same input definitions.')
tr=pd.read_csv(run/'training_bounds.csv');bounds=table(['Input','Training minimum','Training maximum'],[[k,f(tr.iloc[0][key]),f(tr.iloc[1][key])] for k,key in [('Speed (rpm)','speed_rpm'),('Acceleration (rpm/s)','acceleration_rpm_s'),('Inlet temperature (K)','temperature_K'),('Inlet pressure (kPa)','pressure_kPa')]],'Bounds of the unchanged 1400-point exact GP training set. Geometric coverage is checked on actual queries, not only on commanded speed.')
delta={k:100*(m.loc['R3',k]/m.loc['BasePI',k]-1) for k in ['rmse_rpm','segment_excess_TV_lbm_s','hold_excess_TV_lbm_s']}
claims=f"R3's full actual-speed RMSE is {delta['rmse_rpm']:+.1f}"+r'\%'+f" relative to base PI. Its segment fuel-reversal metric changes by {delta['segment_excess_TV_lbm_s']:+.1f}"+r'\%'+f" and hold-only reversal metric by {delta['hold_excess_TV_lbm_s']:+.1f}"+r'\%.'
segments=[];a=pd.read_csv(run/'BasePI_segments.csv');b=pd.read_csv(run/'R3_segments.csv')
for (_,x),(_,y) in zip(a.iterrows(),b.iterrows()):segments.append([f'{x.start_s:g}--{x.end_s:g}',x.type,f(x.rmse_rpm),f(y.rmse_rpm),f(x.excess_TV_lbm_s),f(y.excess_TV_lbm_s)])
segment_table=table(['Time (s)','Phase','RMSE base','RMSE R3','TV base','TV R3'],segments,'RMSE in rpm; excess fuel total variation in lbm/s. All eight holds stay within the broad 1 percent band.','llrrrr')
diag=[]
for name in ['BasePI','R3']:
 d=pd.read_csv(run/(name+'.csv'));p=np.mod(d.time_s-60,30);q=(d.time_s>=60)&(p>2)&(p<4.5)
 diag.append([name,f(np.mean((d.Nmech-d.DOB_request)[q])),f(np.mean((d.DOB_sensed-d.DOB_request)[q]))])
sensor=table(['Method','Mean actual error','Mean sensed error'],diag,'Signed rpm error during phase 2--4.5 s of each acceleration. Both controllers have the same inherited speed sensor.')
body=r'''
\begin{titlepage}\color{navy}\sffamily
{\small T-MATS / FROZEN R3 / CONSTRAINED GP ENVELOPE}\par\vspace{22mm}
{\fontsize{30}{36}\selectfont\bfseries Repeating the Cycle\\Within GP Input Coverage\par}
\vspace{12mm}{\Large R3 versus base PI, with unchanged gains\par}
\vspace{10mm}\color{teal}\rule{\linewidth}{1.2pt}\color{navy}\vspace{8mm}
\begin{tabular}{ll}
Speed cycle & 9450--9550 rpm; $\pm20$ rpm/s\\[5pt]
Timing & 5 s ramp, 10 s hold, repeated for 120 s\\[5pt]
Ambient route & 0 m/ISA$-20$ to 10000 m/ISA$+20$ to 0 m/ISA$+0$\\[5pt]
Route knots & 0, 60 and 120 s; linear interpolation\\[5pt]
GP & Same exact four-input posterior; no retraining\\[5pt]
Coverage & Actual query bounds and joint four-dimensional convex hull
\end{tabular}
\par\vspace{12mm}\normalfont\color{ink}
The previous 9025--9975 rpm ramps exceeded the inverse GP's speed and acceleration training range. This repeat narrows only the speed envelope. The ambient route is retained because its inlet-temperature and pressure trajectory is already within the training range. Both controller gains remain frozen, and no reference-acceleration feedforward is added.
\vfill Coverage here means geometric interpolation support, not a guarantee of local data density, low uncertainty or closed-loop stability. Those distinctions are retained in the audit.
\end{titlepage}
\section{Constrained scenario and measured results}
Each 30 s cycle accelerates from 9450 to 9550 rpm in 5 s, holds for 10 s, decelerates in 5 s and holds for 10 s. Four cycles form the 120 s evaluation. A separate 60 s preparation settles at 9450 rpm and 0 m/ISA$-20$. The unchanged R3 takes over at simulation time 45 s. Mach remains zero and no shaft-power pulses or additive fuel disturbance are applied.

Base PI retains $K_p=0.025$, $K_i=0.05$. R3 retains $K_p=0.025$, $K_i=0.1$, $K_d=0.002$, the 0.03 s acceleration filter and 0.015 s sampling. Its slope normalization, fallback guards, zero-acceleration setpoint feedforward, fuel limits and conditional integration are unchanged. The common request governor returns to its inherited 150 rpm/s limit, which comfortably passes the 20 rpm/s test ramps and the preparation ramp. Logged governed requests match the input profiles.
@@SUMMARY@@
@@CLAIMS@@
R3 improves hold RMSE (0.338 versus 0.496 rpm), peak error (2.007 versus 2.176 rpm) and integral absolute error (51.43 versus 61.72 rpm s). Base PI has lower ramp RMSE (0.746 versus 1.118 rpm), which gives it the lower overall RMSE. The covered-domain result is therefore a more specific tradeoff than the previous broad-envelope failure: R3 settles more accurately on holds and commands smoother fuel, while base PI tracks these ramps more closely in actual shaft speed.
\clearpage
\section{Coverage audit}
@@BOUNDS@@
@@COVERAGE@@
The audit evaluates $[r,0,T,P]$, $[N_s,\hat a,T,P]$ and $[N_s,0,T,P]$ at every test sample, using the same one-sample-delayed inlet measurements as the controller. For base PI the hypothetical inverse inputs are reconstructed offline; they do not alter that controller.

A preliminary 9400--9600 rpm cycle passed the separate input-bound checks but produced 28 base-PI shadow queries and six R3 queries outside the joint hull during brief acceleration transients. The final 9450--9550 rpm envelope adds margin for those actual transients. The preliminary run is retained separately and excluded from the final comparison.

The joint hull is built from all four inputs of the original training points after standardization. Boundary membership uses a $10^{-7}$ normalized half-space tolerance, and the tolerant box uses $10^{-8}$ times each input span. Strict box results are also shown, so numerical tolerances do not conceal extrapolation. Zero-volume simplices from coplanar points are discarded when building the supporting half-spaces; every retained half-space is verified against the complete training set.

Nearest-neighbour distance is measured in the GP kernel's scaled input coordinates. Its training leave-one-out 95th percentile is a descriptive density reference, not an acceptance threshold. Convex-hull membership cannot exclude sparse regions between samples. No claim of uniformly low GP uncertainty follows from this coverage check. The coverage restriction applies to the 120 s test, not the inherited startup state before preparation is complete.
\clearpage
\section{Interpretation with extrapolation removed}
Both final trajectories pass numerical acceptance. R3 has zero GP input-range flags and zero fallback activation throughout evaluation. Both methods have zero monitored compressor corrected-speed map overruns. Thus the earlier extrapolation and fallback explanation is absent here, yet R3 still has higher actual-speed RMSE and lower fuel reversals. The earlier fixed-speed disturbance tuning does not automatically optimize ramp tracking.

The inherited sensor lag contributes a distinction between actual and sensed speed during motion. R3 can drive sensed speed closer to the ramp request while actual speed leads it. The following signed-error diagnostic illustrates this behaviour without claiming to isolate every cause.
@@SENSOR@@
R3 also retains damping based on measured acceleration, while its setpoint GP query still uses zero acceleration. No desired-acceleration feedforward or sensor-delay compensation is introduced in this repeat. The conclusion is a measured tradeoff with the original gains, not a failure of the geometric-coverage check and not evidence that every covered inverse controller must beat base PI.

Speed RMSE uses actual shaft speed minus the recorded request. Ramp and hold RMSE are separate. Hold recovery requires speed to remain within 1\% of that hold's target until its end; zero means it never leaves that band. Fuel reversal is excess total variation within each of the sixteen ramp/hold segments, summed over the test. Hold-only excess variation is also given. Because ambient conditions keep changing, fuel reversals can include legitimate responses; this is a ringing proxy, not fuel consumption. It is not the earlier six two-second shaft-load metric.
\clearpage
\section{Full time-domain response}
@@OVERVIEW@@
\clearpage
\section{Ambient route and diagnostic flags}
@@ENVIRONMENT@@
The ambient route remains unchanged. The lower speed envelope also keeps the simulated compressor corrected speed within the monitored map limits on this test.
\clearpage
\section{First-cycle detail}
@@ZOOM1@@
\clearpage
\section{Ambient-turning-point detail}
@@ZOOM2@@
\clearpage
\section{All ramp and hold intervals}
@@SEGMENTS@@
\section{Reproduction}
Open \path{GasTurbine_Covered_BasePI.mdl} or \path{GasTurbine_Covered_R3.mdl} in the existing T-MATS workspace. Both use \path{tmats_r3_covered_cycle_setup.m}. The previous broad-cycle models and results are preserved.

Run \path{run_tmats_r3_cycle(out,true)} with \path{out='results/r3_covered_cycle_20260915_final'}, then \path{report_tmats_r3_cycle(out)}. The latter includes \path{audit_tmats_cycle_coverage.m} for this study. Run \path{verify_tmats_r3_cycle.py covered} for independent request, metric, control-command and integrator replay checks. All raw trajectories, per-query coverage records and summary tables accompany the models. These are deterministic simulations with the inherited sensor, and no added actuator lag or measurement noise.
\end{document}
'''
repl={'SUMMARY':summary,'CLAIMS':claims,'BOUNDS':bounds,'COVERAGE':coverage,'SENSOR':sensor,'SEGMENTS':segment_table,'OVERVIEW':fig('cycle_overview','The four narrowed speed cycles and corresponding fuel and surge-margin histories.'),'ENVIRONMENT':fig('cycle_environment','Recorded inlet conditions, compressor map coordinate and zero R3 range/fallback flags.'),'ZOOM1':fig('cycle_zoom_1','First 30 s: acceleration, high hold, deceleration and low hold.'),'ZOOM2':fig('cycle_zoom_2','The 45--75 s window includes the 10000 m/ISA+20 turning point at 60 s.')}
for k,v in repl.items():body=body.replace('@@'+k+'@@',v)
assert '@@' not in body
a=ast.parse((root/'build_virtual_fuel_pdf.py').read_text(encoding='utf-8'));pre=next(ast.literal_eval(n.value) for n in a.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PREAMBLE' for x in n.targets)).split(r'\begin{document}')[0]
pre=pre.replace('INVERSE-GPR VIRTUAL-FUEL PI','R3 / CONSTRAINED GP ENVELOPE').replace('9000 rpm tuning / 9500 rpm transfer evaluation','9450-9550 rpm / unchanged controller gains')
(work/'R3_Covered_Cycle.tex').write_text(pre+r'\begin{document}'+body,encoding='utf-8')
for name in ['summary.csv','coverage_summary.csv','training_bounds.csv','BasePI_segments.csv','R3_segments.csv','verification.csv']:shutil.copy2(run/name,work/name)
print(work/'R3_Covered_Cycle.tex')
