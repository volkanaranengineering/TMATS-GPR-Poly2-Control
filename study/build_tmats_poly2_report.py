from pathlib import Path
import ast,json,shutil
import pandas as pd
import numpy as np
root=Path(__file__).resolve().parent;run=root/'results/r3_poly2_challenger_20260915';fit=root/'results/poly2_inverse_20260915';work=root/'tmp/pdfs/r3_poly2';work.mkdir(parents=True,exist_ok=True)
m=pd.read_csv(run/'summary.csv').set_index('method');cov=pd.read_csv(run/'coverage_summary.csv').set_index('method');p=json.loads((fit/'poly2_model.json').read_text());fm=pd.read_csv(fit/'fit_metrics.csv').set_index('split')
assert len(m)==4 and m.accepted.eq(1).all()
def f(x,n=4):return '--' if np.isnan(x) else ('NR' if np.isinf(x) else f'{x:.{n}g}')
def table(h,rows,caption,align=None):
 return r'\begin{table}[H]\centering\small\begin{tabular}{'+(align or ('l'+'r'*(len(h)-1)))+r'}\toprule'+'\n'+' & '.join(h)+r'\\\midrule'+'\n'+'\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+'\n'+r'\bottomrule\end{tabular}\caption{'+caption+r'}\end{table}'
def fig(name,caption):
 shutil.copy2(run/(name+'.pdf'),work/(name+'.pdf'));return r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{'+name+r'.pdf}\caption{'+caption+r'}\end{figure}'
names=['BasePI','R3','R3_GPRFF','R3_Poly2FF'];labels=['Base PI','GPR only','GPR+FF','Poly2+FF']
fields=[('Overall RMSE (rpm)','rmse_rpm'),('Ramp RMSE (rpm)','ramp_rmse_rpm'),('Hold RMSE (rpm)','hold_rmse_rpm'),('Peak error (rpm)','peak_error_rpm'),('IAE (rpm s)','iae_rpm_s'),('Fuel reversal (lbm/s)','segment_excess_TV_lbm_s'),('Hold fuel reversal (lbm/s)','hold_excess_TV_lbm_s'),('Worst hold recovery (s)','max_recovery_1pct_s'),('Minimum surge margin (percent)','minimum_SM_percent'),('Peak fuel (lbm/s)','fuel_peak_lbm_s'),('Maximum fuel slew (lbm/s squared)','max_fuel_slew_lbm_s2')]
summary=table(['Metric']+labels,[[label]+[f(m.loc[n,k]) for n in names] for label,k in fields],'GPR only is the preceding feedback-only ablation. GPR+FF and Poly2+FF have identical controller architecture and gains; only the inverse representation changes.')
coef=pd.read_csv(fit/'coefficients.csv');terms=[r'$1$']+[f'$z_{i}$' for i in range(1,5)]+[f'$z_{i}^2$' for i in range(1,5)]+[f'$z_{i}z_{j}$' for i,j in p['pairs']]
coeff=table(['Term','Coefficient (lbm/s)'],[[term,f(value,11)] for term,value in zip(terms,coef.coefficient_lbm_s)],'Complete full-quadratic equation in standardized inputs. The accompanying JSON retains full floating-point precision.')
norm=table(['Input','Mean','Scale'],[[label,f(mu,11),f(s,11)] for label,mu,s in zip(['Speed (rpm)','Acceleration (rpm/s)','Inlet temperature (K)','Inlet pressure (kPa)'],p['inputMean'],p['inputScale'])],'Standardization computed from the training set only; scale is the sample standard deviation.')
gp=pd.read_csv(root/'results/environment_gpr_20260914_201325/gpr_metrics.csv').iloc[0]
accuracy=table(['Inverse','Test points','RMSE','MAE','Max error',r'$R^2$'],[['Exact GPR',200,f(gp.rmse_lbm_s,6),f(gp.mae_lbm_s,6),f(gp.max_error_lbm_s,6),f(gp.r2,6)],['Quadratic OLS',200,f(fm.loc['test','rmse_lbm_s'],6),f(fm.loc['test','mae_lbm_s'],6),f(fm.loc['test','max_error_lbm_s'],6),f(fm.loc['test','r2'],6)]],'Fuel prediction errors in lbm/s on the same 200 untouched held-out points.')
coverage=table(['Check']+labels,[[label]+[f(cov.loc[n,k]) for n in names] for label,k in [('Audited queries','query_count'),('Bounds outside (percent)','strict_box_outside_percent'),('Hull outside (percent)','hull_outside_percent')]]+[[label]+[f(m.loc[n,k]) for n in names] for label,k in [('Fallback active (percent)','fallback_percent'),('Map speed outside (percent)','Nc_outside_percent')]],'The polynomial is audited against the same training envelope as GPR; it does not supply a GP uncertainty estimate.')
changes=' '.join(label+f" {100*(m.loc['R3_Poly2FF',k]/m.loc['R3_GPRFF',k]-1):+.1f}"+r'\%' for label,k in [('Overall RMSE:','rmse_rpm'),('ramp RMSE:','ramp_rmse_rpm'),('hold RMSE:','hold_rmse_rpm'),('fuel reversal:','segment_excess_TV_lbm_s')])+'.'
body=r'''
\begin{titlepage}\color{navy}\sffamily
{\small T-MATS / INVERSE MODEL CHALLENGER / FIXED-GAIN R3}\par\vspace{22mm}
{\fontsize{30}{36}\selectfont\bfseries A Second-Order Polynomial\\Challenger to Inverse GPR\par}
\vspace{12mm}{\Large Same architecture, same data, same feedback gains\par}
\vspace{10mm}\color{teal}\rule{\linewidth}{1.2pt}\color{navy}\vspace{8mm}
\begin{tabular}{ll}
Polynomial & Full degree-two regression: 15 coefficients\\[5pt]
Inputs & Speed, acceleration, inlet temperature, inlet pressure\\[5pt]
Output & Fuel flow, lbm/s\\[5pt]
Data & Same 1400 training and 200 held-out points\\[5pt]
R3 gains & $K_p=0.025$, $K_i=0.1$, $K_d=0.002$\\[5pt]
FF & Static inverse evaluated at moving speed setpoint\\[5pt]
Cycle & 9450--9550 rpm, 5 s ramps, 10 s holds, 120 s
\end{tabular}
\par\vspace{12mm}\normalfont\color{ink}
The new challenger replaces every GPR inverse evaluation and model derivative in R3 + static FF with one frozen quadratic regression. Controller structure, gains, filters, fallback rules, fuel limits and startup tracking are preserved. No polynomial-specific gain tuning is performed.
\vfill Four fresh simulations compare base PI, GPR feedback-only, GPR + static FF and the quadratic + static FF challenger.
\end{titlepage}
\section{The second-order inverse equations}
Let $x=[N,a,T,P]^\mathsf{T}$ and define $z_i=(x_i-\mu_i)/s_i$. The fitted inverse is
\begin{equation}
p_2(x)=c_0+\sum_{i=1}^{4}b_i z_i+\sum_{i=1}^{4}q_i z_i^2+\sum_{i<j}h_{ij}z_i z_j.
\end{equation}
This is a full total-degree-two model, including all six pairwise interactions, not a polynomial omitting cross terms. Ordinary least squares is solved using the 1400 original training rows only. There is no ridge penalty, response clipping, coefficient constraint, feature selection or held-out-data tuning.
@@NORMALIZATION@@
@@COEFFICIENTS@@
\clearpage
\section{Predictor accuracy and unchanged controller structure}
@@ACCURACY@@
The quadratic design matrix has full rank 15 and condition number 13.58 after standardization. Training RMSE is 0.05981 lbm/s and held-out RMSE is 0.06222 lbm/s. The similar errors and moderate condition number are consistent with a limited global quadratic approximation, rather than numerical rank failure. GPR predicts these held-out fuel values much more accurately. Closed-loop controller performance is nevertheless evaluated separately because model derivatives, command decomposition and sensor lag also matter.

For either inverse $g$ (GPR) or $p_2$ (quadratic), write $v$ for the chosen inverse and use the same law:
\begin{align}
u_{\rm FF}&=v(r,0,T,P),\\
\tilde e_N&=\frac{v(r,0,T,P)-v(N_s,0,T,P)}{v_N(r,0,T,P)},\\
\tilde a&=\frac{v(N_s,\hat a,T,P)-v(N_s,0,T,P)}{v_a(r,0,T,P)},\\
u^*&=u_{\rm FF}+0.025\tilde e_N-0.002\tilde a+I,\qquad \dot I=0.1\tilde e_N.
\end{align}
The static FF uses the changing speed setpoint and zero acceleration. Measured acceleration remains in feedback only. The quadratic derivatives are analytic:
\begin{equation}
\frac{\partial p_2}{\partial x_i}=\frac{b_i+2q_i z_i+\sum_{j\ne i}h_{ij}z_j}{s_i},\qquad h_{ji}=h_{ij}.
\end{equation}
The same physical-unit slope thresholds and normalized-error/map guards trigger the same speed-feedback fallback when necessary. The 0.03 s acceleration filter, 0.015 s sample time, saturation and conditional integration remain unchanged. A polynomial does not provide a GP posterior standard deviation, but this R3 architecture does not use one for gain scheduling.

Python and MATLAB polynomial predictions agree to $1.34\times10^{-15}$ lbm/s on the held-out set. Analytic derivatives agree with central finite differences to $2.48\times10^{-12}$ in the tested physical input derivatives.
\clearpage
\section{Fixed-gain closed-loop comparison}
@@SUMMARY@@
Relative to GPR + static FF, the quadratic challenger changes the metrics as follows. @@CHANGES@@

The polynomial slightly improves overall, ramp and hold RMSE, IAE and the fuel-reversal metric relative to GPR + static FF on this particular cycle. Its peak speed error and maximum fuel slew are slightly higher. Base PI still has the lowest overall and ramp RMSE, while GPR feedback-only has the lowest reversal metric among the four cases. The polynomial's much larger held-out fuel error therefore does not translate directly into worse closed-loop tracking on this narrow trajectory. This is a local fixed-gain comparison, not evidence of superior polynomial prediction accuracy or broad operating-envelope superiority.

The speed cycle contains four 30 s periods: accelerate from 9450 to 9550 rpm in 5 s, hold 10 s, decelerate 5 s, hold 10 s. Ambient conditions follow the unchanged linear route through 0 m/ISA$-20$, 10000 m/ISA$+20$ and 0 m/ISA 0 at test times 0, 60 and 120 s. A separate 60 s preparation precedes evaluation. Base PI retains $K_p=0.025$, $K_i=0.05$; the other three methods share the frozen R3 gains. No extra load pulses, sensor noise or actuator lag are added.

RMSE is actual shaft speed minus the moving request. The fuel-reversal metric sums excess total variation within each ramp/hold interval; it is a ringing proxy and can include legitimate ambient-driven fuel reversals. Recovery requires persistent entry into a 1\% hold-speed window until the hold ends. No claim about real-time implementation speed is made; the quadratic has a compact algebraic form, but controller execution timing is not benchmarked here.
\clearpage
\section{Common-envelope and implementation checks}
@@COVERAGE@@
The same three inverse-query branches are audited against the original input bounds and four-dimensional training convex hull. Base PI has only offline shadow queries. Geometric coverage does not guarantee dense local support or uniformly small model error. The original training data include simulator map-boundary behaviour, and that provenance remains common to both fitted inverses.

The fresh base PI and GPR runs are checked against the previous study for unchanged trajectories. Polynomial online means are independently reconstructed from the saved coefficients and logged speed, acceleration and delayed inlet inputs. Command summation, proportional/damping action, saturation and integral updates are replayed from the saved traces. The feedback architecture differs only through the chosen inverse and its analytic derivatives.
\clearpage
\section{Full time-domain responses}
@@OVERVIEW@@
\clearpage
\section{First-cycle zoom}
@@ZOOM1@@
\clearpage
\section{Ambient-turning-point zoom}
@@ZOOM2@@
\clearpage
\section{Feedforward and feedback components}
@@COMPONENTS@@
Static model bias can be absorbed by the residual integral at a settled operating point. During changing ambient conditions and speed ramps, the model's value and slope errors can alter that compensation. The plots show the measured command decomposition; they should be interpreted together with actual-speed RMSE and fuel reversal rather than treating a smaller integral state as a performance result.
\section{Reproduction}
The challenger is \path{GasTurbine_PolyCompare_R3_Poly2FF.mdl}, with setup \path{tmats_r3_poly2_setup.m}. The three comparator models use the same \path{GasTurbine_PolyCompare_} prefix. Run \path{fit_tmats_poly2_inverse.py}, \path{validate_tmats_poly2.m}, and \path{run_tmats_r3_cycle(out,true,true,true)} with \path{out='results/r3_poly2_challenger_20260915'}. The fitted equation and normalization are stored in \path{results/poly2_inverse_20260915/poly2_model.json}.

Run \path{audit_tmats_cycle_coverage(out)}, \path{report_tmats_static_ff(out)} and \path{verify_tmats_static_ff.py poly} for the coverage audit, figures and independent checks. The archive contains the fitted equation, held-out predictions, new models, native trajectories and summary tables. It requires the existing T-MATS workspace and frozen-model dependencies.
\end{document}
'''
repl={'NORMALIZATION':norm,'COEFFICIENTS':coeff,'ACCURACY':accuracy,'SUMMARY':summary,'CHANGES':changes,'COVERAGE':coverage,'OVERVIEW':fig('cycle_overview','Four freshly simulated controllers on the same covered speed and ambient cycle.'),'ZOOM1':fig('cycle_zoom_1','First acceleration, high hold, deceleration and low hold.'),'ZOOM2':fig('cycle_zoom_2','The 45--75 s window spans the 10000 m/ISA+20 turning point.'),'COMPONENTS':fig('static_ff_components','GPR and quadratic command components, with the GPR feedback-only case retained for context.')}
for k,val in repl.items():body=body.replace('@@'+k+'@@',val)
assert '@@' not in body
a=ast.parse((root/'build_virtual_fuel_pdf.py').read_text(encoding='utf-8'));pre=next(ast.literal_eval(n.value) for n in a.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PREAMBLE' for x in n.targets)).split(r'\begin{document}')[0]
pre=pre.replace('INVERSE-GPR VIRTUAL-FUEL PI','R3 / QUADRATIC INVERSE CHALLENGER').replace('9000 rpm tuning / 9500 rpm transfer evaluation','Same architecture / same feedback gains')
(work/'R3_Poly2_Challenger.tex').write_text(pre+r'\begin{document}'+body,encoding='utf-8')
for folder,files in [(fit,['coefficients.csv','normalization.csv','fit_metrics.csv','poly2_model.json','implementation_checks.csv']),(run,['summary.csv','coverage_summary.csv','verification.csv'])]:
 for name in files:shutil.copy2(folder/name,work/name)
print(work/'R3_Poly2_Challenger.tex')
