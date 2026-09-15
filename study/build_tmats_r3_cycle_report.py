"""Native LaTeX report for the frozen-R3 ambient and speed cycle."""
from pathlib import Path
import ast,shutil
import pandas as pd
import numpy as np
root=Path(__file__).resolve().parent
run=root/'results/r3_ambient_cycle_20260915';work=root/'tmp/pdfs/r3_cycle';work.mkdir(parents=True,exist_ok=True)
m=pd.read_csv(run/'summary.csv').set_index('method')
assert len(m)==2 and m.accepted.eq(1).all(), 'Report requires accepted full trajectories; inspect failures first.'
def f(x):
 if np.isnan(x):return '--'
 if np.isinf(x):return 'NR'
 return f'{x:.4g}'
def table(headers,rows,caption):
 return r'\begin{table}[H]\centering\small\begin{tabular}{l'+('r'*(len(headers)-1))+r'}\toprule'+'\n'+' & '.join(headers)+r'\\\midrule'+'\n'+'\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+'\n'+r'\bottomrule\end{tabular}\caption{'+caption+r'}\end{table}'
def fig(name,caption):
 shutil.copy2(run/(name+'.pdf'),work/(name+'.pdf'))
 return r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{'+name+r'.pdf}\caption{'+caption+r'}\end{figure}'
fields=[('Full RMSE (rpm)','rmse_rpm'),('Ramp RMSE (rpm)','ramp_rmse_rpm'),('Hold RMSE (rpm)','hold_rmse_rpm'),('Peak error (rpm)','peak_error_rpm'),('IAE (rpm s)','iae_rpm_s'),('Segment excess TV (lbm/s)','segment_excess_TV_lbm_s'),('Hold excess TV (lbm/s)','hold_excess_TV_lbm_s'),('Worst hold recovery (s)','max_recovery_1pct_s'),('Holds not recovered','holds_not_recovered'),('Minimum surge margin (percent)','minimum_SM_percent'),('Peak fuel (lbm/s)','fuel_peak_lbm_s'),('Maximum fuel slew (lbm/s squared)','max_fuel_slew_lbm_s2'),('Compressor Nc outside (percent)','Nc_outside_percent'),('Fallback active (percent)','fallback_percent'),('GP input range outside (percent)','gp_outside_percent')]
summary=table(['Metric','Base PI','R3'],[[label,f(m.loc['BasePI',key]),f(m.loc['R3',key])] for label,key in fields], 'The same 120 s evaluation interval and recorded speed request are used for both methods. NR means no persistent recovery before the end of a hold.')
s0=pd.read_csv(run/'BasePI_segments.csv');s1=pd.read_csv(run/'R3_segments.csv')
segs=table(['Time (s)','Phase','RMSE base','RMSE R3','TV base','TV R3'],[[f'{a.start_s:g}--{a.end_s:g}',a.type,f(a.rmse_rpm),f(b.rmse_rpm),f(a.excess_TV_lbm_s),f(b.excess_TV_lbm_s)] for (_,a),(_,b) in zip(s0.iterrows(),s1.iterrows())], 'Per-segment speed RMSE in rpm and excess fuel total variation in lbm/s. Ambient conditions continue changing during every hold.').replace('{lrrrrr}','{llrrrr}')
changes={k:100*(m.loc['R3',k]/m.loc['BasePI',k]-1) for k in ['rmse_rpm','ramp_rmse_rpm','hold_rmse_rpm','segment_excess_TV_lbm_s','hold_excess_TV_lbm_s']}
diag=[]
for name in ['BasePI','R3']:
 d=pd.read_csv(run/(name+'.csv'));ph=np.mod(d.time_s-60,30);q=d.time_s>=60;mid=q&(ph>2)&(ph<4.5)
 diag.append([name,f(np.sqrt(np.mean((d.DOB_sensed[q]-d.DOB_request[q])**2))),f(np.mean((d.Nmech-d.DOB_request)[mid])),f(np.mean((d.DOB_sensed-d.DOB_request)[mid]))])
sensor_table=table(['Method','Sensed RMSE','Mid-ramp actual error','Mid-ramp sensed error'],diag,'All values are rpm. Signed mid-ramp means use phase 2--4.5 s of each acceleration. Full sensed RMSE uses the complete test.')
change_text=' '.join(label+f' changes by {changes[key]:+.1f}'+r'\%.' for label,key in [('Full RMSE','rmse_rpm'),('Ramp RMSE','ramp_rmse_rpm'),('Hold RMSE','hold_rmse_rpm'),('Segment excess TV','segment_excess_TV_lbm_s'),('Hold excess TV','hold_excess_TV_lbm_s')])
body=r'''
\begin{titlepage}\color{navy}\sffamily
{\small T-MATS / FROZEN R3 / MOVING OPERATING CONDITIONS}\par\vspace{22mm}
{\fontsize{30}{36}\selectfont\bfseries Repeated Speed Ramps\\Through an Ambient Cycle\par}
\vspace{12mm}{\Large Fixed R3 versus base PI\par}
\vspace{10mm}\color{teal}\rule{\linewidth}{1.2pt}\color{navy}\vspace{8mm}
\begin{tabular}{ll}
Test duration & 120 s, following a separate 60 s preparation\\[5pt]
Speed range & 9025--9975 rpm (9500 rpm $\pm5\%$)\\[5pt]
Each cycle & 5 s acceleration, 10 s hold, 5 s deceleration, 10 s hold\\[5pt]
Ambient route & 0 m/ISA$-20$ to 10000 m/ISA$+20$ to 0 m/ISA$+0$\\[5pt]
Ambient knots & 0, 60 and 120 s; linear altitude and ISA-departure ramps\\[5pt]
Controller changes & None; the selected R3 and base PI gains are frozen
\end{tabular}
\par\vspace{12mm}\normalfont\color{ink}
This test extends the earlier constant-speed shaft-load comparison to repeated reference ramps while altitude and inlet conditions change continuously. Speed limits were not specified in the new request; the previous 9500 rpm, 5\% context is interpreted here as a symmetric 9025--9975 rpm range. The ambient turning point is placed halfway through the test. Earlier shaft-power pulses are disabled to isolate this new scenario.
\vfill Numerical convergence and compressor-map coverage are reported separately. A converged simulation outside the map is not physical validation of the missing map range.
\end{titlepage}
\section{Scenario and unchanged controllers}
Define test time $t=t_{\rm simulation}-60$ and phase $s=t\bmod30$. The reference is
\begin{equation}
r(s)=\begin{cases}9025+190s,&0\leq s<5,\\9975,&5\leq s<15,\\9975-190(s-15),&15\leq s<20,\\9025,&20\leq s<30.\end{cases}
\end{equation}
The resulting four cycles contain eight ramps and eight holds. Altitude and ISA departure are
\begin{align}
h(t)&=\begin{cases}(10000/60)t,&0\leq t\leq60,\\10000-(10000/60)(t-60),&60<t\leq120,\end{cases}\\
\Delta T_{\rm ISA}(t)&=\begin{cases}-20+(40/60)t,&0\leq t\leq60,\\20-(20/60)(t-60),&60<t\leq120.\end{cases}
\end{align}
Altitude is in metres and ISA departure in degrees Celsius. The existing T-MATS atmosphere computes inlet temperature and pressure; the supplied GP receives those measured simulated inlet quantities. ISA departure is not inlet temperature itself. Mach remains zero.

The preparation starts from the inherited engine state, ramps the reference to 9025 rpm and ISA departure to $-20$ degrees, then allows settling. R3 takes over at simulation time 45 s; evaluation begins at 60 s. Both methods use identical preparation commands and plant initial state. No extra fuel or shaft-power disturbance, measurement noise, or actuator lag is added.

The shared request-governor slew limit is raised from 150 to 200 rpm/s so the requested 190 rpm/s transitions last 5 s. This is a common scenario-input adjustment, not a feedback-gain retuning. The logged governed request is checked against the supplied profile before either trajectory is accepted.

Base PI retains $K_p=0.025$, $K_i=0.05$. R3 retains $K_p=0.025$, $K_i=0.1$, $K_d=0.002$ with the 0.03 s acceleration filter and 0.015 s sampling. Its unchanged control law is
\begin{align}
\tilde e_N&=\frac{g(r,0,T,P)-g(N_s,0,T,P)}{g_N(r,0,T,P)},\\
\tilde a&=\frac{g(N_s,\hat a,T,P)-g(N_s,0,T,P)}{g_a(r,0,T,P)},\\
u^*&=g(r,0,T,P)+0.025\tilde e_N-0.002\tilde a+I,\qquad\dot I=0.1\tilde e_N.
\end{align}
The previous slope, normalized-error and compressor-speed guards substitute raw speed error and filtered acceleration when needed. Fuel saturation and conditional integration are unchanged. Setpoint feedforward still queries zero acceleration, including during ramps: desired-acceleration feedforward has not been added. The exact four-input GP is frozen and no gains are tuned on this test.
\clearpage
\section{Measured comparison}
@@SUMMARY@@
@@CHANGES@@

RMSE uses actual shaft speed minus the recorded time-varying request. Ramp and hold RMSE are also reported separately. Recovery is measured from each hold start until speed enters and remains within 1\% of that hold's requested speed through its end. This is a tracking-recovery measure, not recovery from a separate shaft-load disturbance.

Fuel ringing is represented here by excess total variation, $R_j=\sum_k|u_{k+1}-u_k|-|u_{\rm last}-u_{\rm first}|$, separately within each ramp/hold segment, then summed. Hold-only excess TV is also reported. These are reversal measures: changing ambient conditions can legitimately create nonmonotonic fuel trajectories, so neither is a pure oscillation estimate. They differ from the previous six two-second disturbance-window metric and should not be compared numerically with it.
\subsection{Why the earlier R3 advantage does not transfer unchanged}
R3 is smoother by the reversal measures but has worse actual-speed RMSE on both ramps and holds. Its earlier tuning optimized fixed-speed load rejection, not repeated speed motion through the entire ambient route. The new ramps also challenge the inverse outside its identification domain: training speeds span approximately 9264--9751 rpm and training acceleration spans $-68.84$ to $+61.63$ rpm/s, whereas this test requests 9025--9975 rpm at $\pm190$ rpm/s. The combined online GP input-range flag is active throughout the test. The unchanged R3 fallback is active for 78.69\% of evaluation samples; slope guards alone are violated for 65.64\%. Thus much of this run is the guarded speed-feedback controller rather than normalized inverse feedback.

The actual and sensed speed distinction also matters during ramps. The inherited 0.05 s sensor model delays the speed measurement. Driving sensed speed close to the moving reference can make actual shaft speed lead it. The recorded mid-acceleration averages below illustrate this effect; they do not by themselves isolate its full causal contribution. Both controllers have the same sensor. R3 retains zero-acceleration setpoint feedforward, so it has no explicit inverse feedforward term for desired ramp acceleration. No controller changes are introduced to hide these transfer limitations.
@@SENSOR@@
\section{Full time-domain response}
@@OVERVIEW@@
The request, actual speed, speed error, fuel and surge margin are recorded from the nonlinear plant simulation. A low hold RMSE alone does not establish satisfactory ramp tracking; both are retained in the table.
\clearpage
\section{Ambient evolution and fallback}
@@ENVIRONMENT@@
The fallback and training-range flags are distinct. A GP input-range flag tests the rectangular bounds of the training data, not posterior confidence or joint-density coverage. R3's fallback is driven by its existing slope/error/map guards. A controller can therefore query outside a training input range without immediately invoking fallback. Corrected-speed map overruns remain a limitation of the supplied engine simulation.
\clearpage
\section{Zoomed response: first cycle}
@@ZOOM1@@
\clearpage
\section{Zoomed response: ambient turning point}
@@ZOOM2@@
The ambient direction reverses at 60 s, at the beginning of the third acceleration ramp. This window also includes the preceding deceleration and low-speed hold.
\clearpage
\section{All ramp and hold segments}
@@SEGMENTS@@
\section{Reproduction and scope}
Open \path{GasTurbine_Cycle_BasePI.mdl} or \path{GasTurbine_Cycle_R3.mdl} in the existing T-MATS workspace. Their preload callback is \path{tmats_r3_cycle_setup.m}. The original controller models are preserved. Run \path{run_tmats_r3_cycle.m} to regenerate both trajectories and \path{report_tmats_r3_cycle.m} for plots. Native MAT and CSV traces, segment tables and configuration are saved under \path{results/r3_ambient_cycle_20260915}.

Full-run acceptance requires finite valid plant signals, converged flow residuals, positive fuel and surge margin, fewer than 200 solver iterations, a settled pre-test speed and the complete 180 s simulation. Map coverage is reported independently. These results are a frozen-controller transfer test for the stated speed limits, ambient route and deterministic sensor/plant assumptions; they do not replace testing with actuator dynamics or measurement noise.
\end{document}
'''
repl={'SUMMARY':summary,'CHANGES':change_text,'SEGMENTS':segs,'SENSOR':sensor_table,'OVERVIEW':fig('cycle_overview','Full 120 s test; the separate preparation interval is omitted.'),'ENVIRONMENT':fig('cycle_environment','Commanded environment, simulated inlet conditions, compressor map coordinate and R3 diagnostic flags.'),'ZOOM1':fig('cycle_zoom_1','First acceleration, high hold, deceleration and low hold while the environment climbs away from sea level.'),'ZOOM2':fig('cycle_zoom_2','The 45--75 s window spans the 10000 m/ISA+20 turning point.')}
for k,v in repl.items():body=body.replace('@@'+k+'@@',v)
assert '@@' not in body
a=ast.parse((root/'build_virtual_fuel_pdf.py').read_text(encoding='utf-8'));pre=next(ast.literal_eval(n.value) for n in a.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PREAMBLE' for x in n.targets)).split(r'\begin{document}')[0]
pre=pre.replace('INVERSE-GPR VIRTUAL-FUEL PI','R3 / AMBIENT AND SPEED CYCLE').replace('9000 rpm tuning / 9500 rpm transfer evaluation','Frozen R3 and base PI / 120 s cycle')
(work/'R3_Ambient_Cycle.tex').write_text(pre+r'\begin{document}'+body,encoding='utf-8')
for name in ['summary.csv','BasePI_segments.csv','R3_segments.csv']:shutil.copy2(run/name,work/name)
print(work/'R3_Ambient_Cycle.tex')
