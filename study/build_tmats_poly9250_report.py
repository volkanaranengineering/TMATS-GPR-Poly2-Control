from pathlib import Path
import ast,shutil
import numpy as np
import pandas as pd
root=Path(__file__).resolve().parent;run=root/'results/poly2_tune9250_20260915';work=root/'tmp/pdfs/poly9250';work.mkdir(parents=True,exist_ok=True)
t=pd.read_csv(run/'tuning_scores.csv');s=pd.read_csv(run/'selected.csv').iloc[0];v=pd.read_csv(run/'validation_summary.csv').set_index('method');original=t[t.candidate==1].iloc[0];base=t[t.candidate==0].iloc[0]
assert s.accepted==1 and v.accepted.eq(1).all()
def f(x,n=4):return '--' if np.isnan(x) else ('NR' if np.isinf(x) else f'{x:.{n}g}')
def table(headers,rows,caption):
 return r'\begin{table}[H]\centering\small\begin{tabular}{l'+('r'*(len(headers)-1))+r'}\toprule'+'\n'+' & '.join(headers)+r'\\\midrule'+'\n'+'\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+'\n'+r'\bottomrule\end{tabular}\caption{'+caption+r'}\end{table}'
def fig(name,caption):
 shutil.copy2(run/(name+'.pdf'),work/(name+'.pdf'));return r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{'+name+r'.pdf}\caption{'+caption+r'}\end{figure}'
fields=[('Speed RMSE (rpm)','rmse_rpm'),('Peak speed error (rpm)','peak_rpm'),('IAE (rpm s)','iae_rpm_s'),('Fuel ringing (lbm/s)','ringing_excess_TV_lbm_s'),('Recovery to 1 percent (s)','recovery_1pct_speed_s'),('Recovery to 0.1 rpm (s)','settling_to_point1_rpm_s'),('Minimum surge margin (percent)','minimum_margin_percent'),('Peak fuel (lbm/s)','fuel_peak_lbm_s'),('Maximum fuel slew (lbm/s squared)','max_fuel_slew_lbm_s2'),('Fuel saturation (percent)','fuel_limit_percent')]
results=table(['Metric','Base PI','Original Poly2','Retuned Poly2'],[[label]+[f(z[k]) for z in [base,original,s]] for label,k in fields],'10 percent shaft-load pulses at the requested condition. Recovery is the worst of six application/removal events; NR means no persistent entry before the next edge.')
validation=table(['Metric','Base PI','Original Poly2','Retuned Poly2'],[[label]+[f(v.loc[n,k]) for n in ['base','original','tuned']] for label,k in fields[:6]],'Independent 5 percent load-amplitude check after gain selection. These results are not used to select or refine gains.')
gains=table(['Controller',r'$K_p$',r'$K_i$',r'$K_d$'],[[label]+[f(z[k],7) for k in ['Kp','Ki','Kd']] for label,z in [('Base PI',base),('Original Poly2',original),('Retuned Poly2',s)]],'The derivative coefficient multiplies the normalized, filtered acceleration feedback, as in the original R3 architecture.')
changes=' '.join(label+f" {100*(s[k]/original[k]-1):+.1f}"+r'\%' for label,k in [('RMSE:','rmse_rpm'),('ringing:','ringing_excess_TV_lbm_s'),('peak error:','peak_rpm')])+'.'
body=r'''
\begin{titlepage}\color{navy}\sffamily
{\small T-MATS / POLY2 PID / OPERATING-POINT RETUNING}\par\vspace{22mm}
{\fontsize{30}{36}\selectfont\bfseries Retuning Poly2 PID\\at 9250 rpm, Sea Level, ISA 0\par}
\vspace{12mm}{\Large Joint tracking and fuel-ringing objective\par}
\vspace{10mm}\color{teal}\rule{\linewidth}{1.2pt}\color{navy}\vspace{8mm}
\begin{tabular}{ll}
Inverse & Frozen full-quadratic, four-input fuel model\\[5pt]
Feedforward & Same static $p_2(r,0,T,P)$ term\\[5pt]
Tuning condition & 9250 rpm, 0 m, ISA 0, Mach 0\\[5pt]
Tuning excitation & 10\% shaft-load application/removal pulses\\[5pt]
Validation & 5\% load pulses, evaluated after selection\\[5pt]
Preparation / evaluation & 60 s / 90 s
\end{tabular}
\par\vspace{12mm}\normalfont\color{ink}
The polynomial model, controller architecture, sensor, acceleration filter and actuator command limits are preserved. Only the three PID coefficients are retuned. The disturbance protocol follows the earlier fixed-speed study because the requested new condition specifies an operating point rather than a speed-ramp cycle.
\vfill The requested speed lies slightly below the original training-speed minimum. The model is not refitted, and this extrapolation is reported explicitly.
\end{titlepage}
\section{Selected gains and test definition}
@@GAINS@@
The unchanged R3-style Poly2 controller is
\begin{align}
\tilde e_N&=\frac{p_2(r,0,T,P)-p_2(N_s,0,T,P)}{\partial_N p_2(r,0,T,P)},\\
\tilde a&=\frac{p_2(N_s,\hat a,T,P)-p_2(N_s,0,T,P)}{\partial_a p_2(r,0,T,P)},\\
u^*&=p_2(r,0,T,P)+K_p\tilde e_N-K_d\tilde a+I,\qquad \dot I=K_i\tilde e_N.
\end{align}
The existing guards substitute speed error and filtered acceleration if inverse slopes, error ratios or the compressor map coordinate are unsuitable. The 0.03 s acceleration filter, 0.015 s sampling, fuel limits and conditional integration remain unchanged. The previous gains were $[0.025,0.1,0.002]$.

An unloaded trim establishes condition-specific turbine shaft power before any controller comparison. Ten percent of this reference is then applied at evaluation times 10.005, 30 and 60 s and removed at 15, 40.005 and 75 s. The load reference is @@POWER@@ hp, so the tuning pulses are @@LOAD@@ hp. All cases use the same load and 9250 rpm request; no ambient variation is added.
\section{Selection objective and search}
For each numerically accepted candidate, minimize
\begin{equation}
J=\max\left(\frac{\mathrm{RMSE}}{\mathrm{RMSE}_{\rm original}},\frac{R}{R_{\rm original}}\right).
\end{equation}
The denominator is the original Poly2 controller at the same condition. The base PI is a comparator, not part of the candidate selection. The initial sweep includes the original gains and a $3\times3\times3$ grid with $K_p\in\{0.015,0.025,0.035\}$, $K_i\in\{0.08,0.14,0.20\}$ and $K_d\in\{0.001,0.002,0.003\}$. A local refinement changes each coefficient of the best grid point separately by $\pm25\%$.

All @@COUNT@@ Poly2 candidates are retained. Candidate @@CANDIDATE@@ is the best tested under this declared objective; this is a bounded search, not a proof of a global optimum. Gains are frozen before the 5\% validation case.
\clearpage
\section{Tuning-condition results}
@@RESULTS@@
Relative to the original Poly2 controller, the selected gains give: @@CHANGES@@

The selected setting leaves proportional action unchanged, raises integral gain by 40\% and reduces derivative gain by 37.5\%. It gives faster fine settling and less cumulative fuel reversal, but the peak speed excursion is larger than with the original Poly2 setting. This tradeoff is consistent with reduced acceleration feedback allowing a larger initial departure, while stronger integral action removes the remaining error sooner. The measured trace, rather than this interpretation alone, establishes the performance change. The objective explicitly balances RMSE and ringing; it does not minimize peak error or establish robustness away from this operating point.

Speed RMSE is measured over the complete 90 s evaluation. Ringing is the sum of fuel total variation minus net fuel change in six two-second load-edge windows. It is measured in lbm/s, not total fuel consumption. The broad 1\% band is $\pm92.5$ rpm; zero recovery means no band exit. The 0.1 rpm criterion exposes finer settling and requires persistent entry through the end of each event interval.
@@TUNING@@
\clearpage
\section{Full and zoomed time-domain responses}
@@OVERVIEW@@
\clearpage
@@ZOOM@@
\clearpage
\section{Frozen-gain 5 percent validation}
@@VALIDATION@@
The validation halves the disturbance magnitude and preserves timing, model, environment and selected gains. It tests amplitude transfer at this operating point; it is not validation at another speed or altitude. No subsequent gain selection is based on these results.
\section{Coverage, validity and reproduction}
The original training-speed interval is approximately 9264.23--9750.60 rpm. The requested 9250 rpm setpoint is 14.23 rpm below it, and disturbances can move actual speed farther below. Consequently the static inverse query is outside the fitted speed interval throughout evaluation. This repeat intentionally honors the requested condition rather than silently shifting it into the old covered envelope. Numerical convergence does not turn extrapolation into in-domain model validation.

The accepted runs satisfy finite valid plant signals, positive fuel and surge margin, converged flow residuals, solver iteration limits, a settled pre-test speed and full duration. Saved controller commands and integral updates are independently replayed, and the RMSE and ringing metrics are recomputed from traces. Fallback and map diagnostics are retained with each run.

Open \path{GasTurbine_Poly2_9250_Tuned.mdl} in the existing T-MATS workspace. Its preload callback \path{tmats_poly9250_tuned_setup.m} loads the selected gains and unchanged polynomial. The search runner is \path{run_tmats_poly9250.m}; selection is \path{select_tmats_poly9250.m}; amplitude validation is \path{validate_tmats_poly9250.m}. All trials, selected parameters, native traces and validation results are under \path{results/poly2_tune9250_20260915}. Original controller files and fitted coefficients are preserved.
\end{document}
'''
repl={'GAINS':gains,'POWER':f(s.reference_hp,8),'LOAD':f(.1*s.reference_hp,8),'COUNT':str(len(t)-1),'CANDIDATE':str(int(s.candidate)),'RESULTS':results,'CHANGES':changes,'VALIDATION':validation,'TUNING':fig('poly9250_tuning','All accepted Poly2 candidates, coloured by the joint objective; original and selected gains and base PI are identified.'),'OVERVIEW':fig('poly9250_overview','Identical 10 percent shaft-load pulses with base PI, original Poly2 and selected Poly2 gains.'),'ZOOM':fig('poly9250_zoom','First load application and removal, including speed error and fuel-command reversals.')}
for k,val in repl.items():body=body.replace('@@'+k+'@@',val)
assert '@@' not in body
a=ast.parse((root/'build_virtual_fuel_pdf.py').read_text(encoding='utf-8'));pre=next(ast.literal_eval(n.value) for n in a.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PREAMBLE' for x in n.targets)).split(r'\begin{document}')[0]
pre=pre.replace('INVERSE-GPR VIRTUAL-FUEL PI','POLY2 PID / 9250 RPM RETUNING').replace('9000 rpm tuning / 9500 rpm transfer evaluation','Sea level ISA 0 / fixed polynomial model')
(work/'Poly2_9250_Tuning.tex').write_text(pre+r'\begin{document}'+body,encoding='utf-8')
for name in ['tuning_scores.csv','selected.csv','validation_summary.csv','verification.csv']:shutil.copy2(run/name,work/name)
print(work/'Poly2_9250_Tuning.tex')
