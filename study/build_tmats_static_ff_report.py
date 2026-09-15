from pathlib import Path
import ast,shutil
import pandas as pd
import numpy as np
root=Path(__file__).resolve().parent;run=root/'results/r3_static_ff_20260915';work=root/'tmp/pdfs/r3_static_ff';work.mkdir(parents=True,exist_ok=True)
m=pd.read_csv(run/'summary.csv').set_index('method');c=pd.read_csv(run/'coverage_summary.csv').set_index('method');v=pd.read_csv(run/'verification.csv').set_index('method')
assert len(m)==3 and m.accepted.eq(1).all() and c.covered_all.eq(1).all()
assert v.loc['R3_GPRFF','previous_speed_equivalence_rpm']<1e-7
def fmt(x):return '--' if np.isnan(x) else ('NR' if np.isinf(x) else f'{x:.4g}')
def table(headers,rows,caption):
 return r'\begin{table}[H]\centering\small\begin{tabular}{l'+('r'*(len(headers)-1))+r'}\toprule'+'\n'+' & '.join(headers)+r'\\\midrule'+'\n'+'\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+'\n'+r'\bottomrule\end{tabular}\caption{'+caption+r'}\end{table}'
def fig(name,caption):
 shutil.copy2(run/(name+'.pdf'),work/(name+'.pdf'))
 return r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{'+name+r'.pdf}\caption{'+caption+r'}\end{figure}'
methods=['BasePI','R3','R3_GPRFF'];fields=[('Full RMSE (rpm)','rmse_rpm'),('Ramp RMSE (rpm)','ramp_rmse_rpm'),('Hold RMSE (rpm)','hold_rmse_rpm'),('Peak error (rpm)','peak_error_rpm'),('IAE (rpm s)','iae_rpm_s'),('Segment fuel reversal (lbm/s)','segment_excess_TV_lbm_s'),('Hold fuel reversal (lbm/s)','hold_excess_TV_lbm_s'),('Worst hold recovery (s)','max_recovery_1pct_s'),('Minimum surge margin (percent)','minimum_SM_percent'),('Peak fuel (lbm/s)','fuel_peak_lbm_s'),('Maximum fuel slew (lbm/s squared)','max_fuel_slew_lbm_s2')]
summary=table(['Metric','Base PI','R3 only','R3 + FF'],[[label]+[fmt(m.loc[n,k]) for n in methods] for label,k in fields],'R3 only means feedback-only in this new ablation. R3 + FF is the static-feedforward architecture previously reported as R3. All feedback gains are unchanged.')
coverage=table(['Check','Base PI','R3 only','R3 + FF'],[[label]+[fmt(c.loc[n,k]) for n in methods] for label,k in [('Audited queries','query_count'),('Strict input bounds outside (percent)','strict_box_outside_percent'),('Joint hull outside (percent)','hull_outside_percent')]]+[[label]+[fmt(m.loc[n,k]) for n in methods] for label,k in [('Fallback active (percent)','fallback_percent'),('GP range flags (percent)','gp_outside_percent'),('Compressor map overrun (percent)','Nc_outside_percent')]],'Each GP audit uses three query branches per evaluation sample. Base PI uses offline shadow queries only. Geometric coverage does not guarantee uniformly dense training support.')
change=' '.join(label+f" {100*(m.loc['R3_GPRFF',k]/m.loc['R3',k]-1):+.1f}"+r'\%' for label,k in [('Overall RMSE:', 'rmse_rpm'),('ramp RMSE:','ramp_rmse_rpm'),('hold RMSE:','hold_rmse_rpm'),('fuel reversal:','segment_excess_TV_lbm_s')])+'.'
body=r'''
\begin{titlepage}\color{navy}\sffamily
{\small T-MATS / R3 / STATIC SETPOINT FEEDFORWARD}\par\vspace{22mm}
{\fontsize{30}{36}\selectfont\bfseries Static GPR Feedforward\\Driven by the Moving Setpoint\par}
\vspace{12mm}{\Large Base PI, R3 feedback-only, and R3 + GPR FF\par}
\vspace{10mm}\color{teal}\rule{\linewidth}{1.2pt}\color{navy}\vspace{8mm}
\begin{tabular}{ll}
FF query & $g(r(t),0,T(t),P(t))$ from the same frozen inverse GP\\[5pt]
Motion & 9450--9550 rpm, 5 s ramps, 10 s holds\\[5pt]
Duration & Four cycles in 120 s, after 60 s preparation\\[5pt]
Environment & 0 m/ISA$-20$ to 10000 m/ISA$+20$ to 0 m/ISA$+0$\\[5pt]
R3 gains & $K_p=0.025$, $K_i=0.1$, $K_d=0.002$; unchanged
\end{tabular}
\par\vspace{12mm}\normalfont\color{ink}
The requested feedforward uses the changing speed setpoint and zero acceleration. Measured acceleration remains in the unchanged R3 feedback path only. No reference-acceleration feedforward is used.

The previous R3 already contained this static feedforward term. This repeat makes the comparison explicit by adding a feedback-only ablation. The freshly rerun R3 + static FF trajectory reproduces the previous R3 trajectory exactly, rather than adding the same fuel term twice.
\vfill All three final trajectories pass numerical acceptance and the same geometric GP-coverage checks.
\end{titlepage}
\section{What is added and what is held fixed}
Let $g(N,a,T,P)$ be the unchanged exact inverse GPR. Its static feedforward evaluation is
\begin{equation}u_{\rm FF}(t)=g(r(t),0,T(t),P(t)).\end{equation}
The setpoint $r(t)$ changes throughout the speed ramps. Zero acceleration selects the static slice of the same four-input model; the feedforward query does not use measured acceleration or the derivative of the setpoint. Inlet temperature and pressure retain their existing one-sample measurement delay.

Define the unchanged R3 feedback variables
\begin{align}
e_0&=g(r,0,T,P)-g(N_s,0,T,P),\\
\tilde e_N&=e_0/g_N(r,0,T,P),\\
\tilde a&=[g(N_s,\hat a,T,P)-g(N_s,0,T,P)]/g_a(r,0,T,P),\\
p&=0.025\tilde e_N-0.002\tilde a,\qquad\dot I=0.1\tilde e_N.
\end{align}
The two R3 command variants are
\begin{align}
u_{\rm R3\ only}^{*}&=p+I,\\
u_{\rm R3+FF}^{*}&=u_{\rm FF}+p+I.
\end{align}
Both retain the original slope/map guards, 0.03 s acceleration filter, 0.015 s sampling, fuel limits and conditional integration. Startup tracking initializes the residual integral consistently with the selected command equation before the 45 s handover. Even feedback-only R3 uses $g(r,0,T,P)$ to construct its virtual error; it does not add that value directly to the fuel command.

Base PI retains $K_p=0.025$, $K_i=0.05$. The 9450--9550 rpm cycle uses $\pm20$ rpm/s ramps and 10 s holds. The ambient trajectory is linear through the specified conditions at test times 0, 60 and 120 s. Mach is zero, and no extra load pulses, fuel disturbance, sensor noise or actuator lag are added. All three cases are freshly simulated.
\clearpage
\section{Measured results and interpretation}
@@SUMMARY@@
Relative to R3 feedback-only, static feedforward gives the following changes. @@CHANGE@@

Static FF improves hold tracking, peak error and integral absolute error, but worsens ramp and overall actual-speed RMSE on this fixed-gain cycle. Fuel reversals also increase slightly relative to feedback-only R3, although both R3 variants remain substantially smoother than base PI under this metric. Static feedforward is therefore not a uniform improvement here.

The static FF value varies with the requested speed and environment, transferring much of the slowly varying command burden away from the integral state. It does not explicitly supply the acceleration-dependent fuel requirement. The shared sensor lag also means closer tracking of sensed speed can make actual shaft speed lead a moving reference. These mechanisms explain why a static FF term can improve holds without guaranteeing lower ramp RMSE; this test does not isolate their individual causal contributions.

Fuel reversal is the sum of excess total variation within all sixteen ramp/hold intervals; ambient changes can produce legitimate reversals, so it is a ringing proxy rather than fuel consumption. All holds stay within the 1\% speed window; zero recovery means no band exit. This is the same metric definition as the preceding covered-cycle study.
\clearpage
\section{Coverage and implementation checks}
@@COVERAGE@@
The queries $[r,0,T,P]$, $[N_s,\hat a,T,P]$ and $[N_s,0,T,P]$ stay within the original training input bounds and joint four-dimensional convex hull throughout evaluation. R3 + FF reuses the existing setpoint mean; no additional dynamic-acceleration GP query is needed. The hull check uses the same normalized $10^{-7}$ half-space tolerance as the previous study. Coverage applies to the test interval after preparation, and denotes geometric support rather than a guarantee of uniformly low uncertainty.

Saved traces independently reproduce the request, speed RMSE, proportional/damping correction, feedforward addition, saturation and conditional integral updates. The rerun base PI and R3 + FF actual-speed traces match their previous counterparts sample for sample, with maximum difference zero. This confirms that the previous R3 already had the requested static feedforward architecture.
\clearpage
\section{Full response}
@@OVERVIEW@@
\clearpage
\section{Feedforward and feedback command components}
@@COMPONENTS@@
The integral states have different offsets because startup tracking allocates the equilibrium command according to whether FF is present. Their absolute magnitudes should not be compared as if both used the same command decomposition. The measured total fuel and speed remain the performance quantities.
\clearpage
\section{First-cycle zoom}
@@ZOOM1@@
\clearpage
\section{Ambient-turning-point zoom}
@@ZOOM2@@
\section{Reproduction}
The saved models are \path{GasTurbine_FFCompare_BasePI.mdl}, \path{GasTurbine_FFCompare_R3.mdl} (feedback-only), and \path{GasTurbine_FFCompare_R3_GPRFF.mdl}. They use the same covered-cycle setup and original frozen GP in the existing T-MATS workspace. Previous model files are preserved.

Run \path{run_tmats_r3_cycle(out,true,true)} with \path{out='results/r3_static_ff_20260915'}, followed by \path{audit_tmats_cycle_coverage(out)} and \path{report_tmats_static_ff(out)}. Run \path{verify_tmats_static_ff.py} for independent replay and equivalence checks. Native trajectories, segment tables, per-query coverage and source files accompany the report. The superseded dynamic-acceleration FF attempt is excluded.
\end{document}
'''
repl={'SUMMARY':summary,'CHANGE':change,'COVERAGE':coverage,'OVERVIEW':fig('cycle_overview','Fresh simulations of all three architectures on the identical covered cycle.'),'COMPONENTS':fig('static_ff_components','Static feedforward is driven by the moving setpoint and inlet conditions; measured acceleration is confined to feedback.'),'ZOOM1':fig('cycle_zoom_1','First 30 s of acceleration, holds and deceleration.'),'ZOOM2':fig('cycle_zoom_2','The 45--75 s window includes the environmental reversal at 60 s.')}
for k,val in repl.items():body=body.replace('@@'+k+'@@',val)
assert '@@' not in body
a=ast.parse((root/'build_virtual_fuel_pdf.py').read_text(encoding='utf-8'));pre=next(ast.literal_eval(n.value) for n in a.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PREAMBLE' for x in n.targets)).split(r'\begin{document}')[0]
pre=pre.replace('INVERSE-GPR VIRTUAL-FUEL PI','R3 / STATIC SETPOINT GPR FF').replace('9000 rpm tuning / 9500 rpm transfer evaluation','Same inverse GP / fixed feedback gains')
(work/'R3_Static_FF.tex').write_text(pre+r'\begin{document}'+body,encoding='utf-8')
for p in run.glob('*.csv'):
 if 'coverage_queries' not in p.name and p.name not in ['BasePI.csv','R3.csv','R3_GPRFF.csv']:shutil.copy2(p,work/p.name)
print(work/'R3_Static_FF.tex')
