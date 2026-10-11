"""Replace previous PILCO by identified 9800-rpm DOB+PI in the combined cycle."""
import json,shutil,sys
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image,ImageDraw
import matplotlib.pyplot as plt
import build_combined_cycle as a

ROOT=a.ROOT;RUN=ROOT/'results/dob98_pi_20261010';OLD=a.RUN
policy=json.loads((RUN/'selected_policy.json').read_text());model=json.loads((RUN/'identified_model.json').read_text())
for key in ['base','poly','smooth']:shutil.copy2(OLD/f'{key}.csv',RUN/f'{key}.csv')
a.RUN=RUN;a.SRC=ROOT/'output/pdf/dob98_pi_source';a.KEYS=['base','poly','dobpi','smooth']
a.NAMES=['Base PI','Retuned Poly2 + PID','DOB98 + tuned PI','Smooth PILCO'];a.DATA=[pd.read_csv(RUN/f'{k}.csv') for k in a.KEYS]
a.main()
metrics=pd.read_csv(RUN/'comparison.csv');tuning=pd.read_csv(RUN/'tuning.csv');validation=pd.read_csv(RUN/'heldout_validation.csv').iloc[0]
fig,axes=plt.subplots(1,2,figsize=(10,3.3))
d=pd.read_csv(RUN/'validation_prediction.csv');q=d.time_s<65
axes[0].plot(d.time_s[q]-60,d.actual_rpm[q]-9800,label='Nonlinear plant');axes[0].plot(d.time_s[q]-60,d.predicted_rpm[q]-9800,'--',label='Identified model');axes[0].set(xlabel='Validation time (s)',ylabel='Speed deviation (rpm)');axes[0].legend(fontsize=8)
axes[1].plot(tuning.case_index,tuning.objective,'o-');axes[1].axvline(policy['case_index'],color='green',ls='--');axes[1].set(xlabel='PI candidate',ylabel='Selection objective')
for ax in axes:ax.grid(alpha=.25)
fig.tight_layout();fig.savefig(a.SRC/'identification_tuning.pdf');plt.close(fig)
tab='\n'.join(f'{x.method} & {x.ramp_rmse_rpm:.3f} & {x.load_rmse_rpm:.3f} & {x.full_rmse_rpm:.3f} \\\\' for x in metrics.itertuples())
extra='\n'.join(f'{x.method} & {x.load_peak_abs_rpm:.2f} & {x.load_segment_excess_tv_lbm_s:.3f} & {x.min_surge_margin_pct:.2f} \\\\' for x in metrics.itertuples())
tex=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=22mm]{geometry}\usepackage{lmodern,amsmath,amssymb,graphicx,booktabs,url}
\title{Identified 9800-rpm disturbance observer\\with PI retuned after observer engagement}
\author{T-MATS combined acceleration and load-pulse comparison}\date{10 October 2026}
\begin{document}\maketitle
\section{Scope and identification experiment}
Previous PILCO is replaced in this comparison by DOB98 + tuned PI. Base PI, retuned Poly2 + PID and smooth PILCO retain their earlier gains and traces. The new controller uses no quadratic feedforward. Its structure is PI minus a filtered input-disturbance estimate, followed by the common fuel limits.

A new nominal model is identified specifically at 9800 rpm (98\% rated speed), with zero external shaft load. After preparation, training applies a deterministic binary fuel perturbation of amplitude 0.035 lbm/s, switched approximately every 0.18 s for 30 s. The base PI stabilizes the experiment; identification uses actual applied fuel, including the excitation, and actual shaft speed. Independent validation uses the sum of 0.37 and 1.17 Hz sinusoids, with amplitudes 0.025 and 0.015 lbm/s. No validation samples enter the least-squares fit.

Let $y_k=N_k-9800$ and $v_k=u_k-u_0$, with $u_0=__U0__$ lbm/s and $T_s=0.015$ s. A parsimonious local model is
\begin{equation}y_{k+1}=a y_k+b v_k,\qquad
a=__A__,\quad b=__B__.\end{equation}
The parameters minimize the squared one-step residual over the excited training interval. The identified pole is stable, and the numerator has no finite nonminimum-phase zero. The model is local: the training speed varies only a few rpm around 9800. Independent free-run fit is __FIT__\%, with __VRMSE__ rpm RMSE. Fit means $100(1-\|y-\hat y\|/\|y-\bar y\|)$.
\par\noindent\includegraphics[width=\textwidth]{identification_tuning.pdf}
\clearpage\section{Causal filtered inverse, step by step}
\textbf{1. Nominal speed dynamics.} With $q=z^{-1}$ denoting a one-sample delay,
\begin{equation}P_n(q)=\frac{bq}{1-aq}.\end{equation}
\textbf{2. Include the sensor.} Every controller retains the same physical sensor: time constant 0.05 s, unity gain, common initial conditions and noise disabled. The DOB uses its discrete approximation
\begin{equation}H_n(q)=\frac{(1-p)q}{1-pq},\qquad p=e^{-T_s/0.05}.\end{equation}
Thus the inverse is formed for sensed-speed dynamics $P_nH_n$. This approximation does not change the physical sensor blocks.

\textbf{3. Make the inverse causal and filtered.} Choose a unity-DC, two-pole low-pass filter with two delays:
\begin{equation}Q(q)=\frac{(1-r)^2q^2}{(1-rq)^2},\qquad r=e^{-2\pi f_cT_s},\quad f_c=1\ \mathrm{Hz}.\end{equation}
Then the two nominal delays cancel analytically:
\begin{equation}\frac{Q}{P_nH_n}=\frac{(1-r)^2(1-aq)(1-pq)}{b(1-p)(1-rq)^2}.\end{equation}
This is proper, causal and stable. A numerical frequency-response check verifies the identity, and an independent Python filter replay is compared with the recorded Simulink observer output.

\textbf{4. Estimate input-equivalent disturbance.} Use the known saturated command, without access to the external load signal:
\begin{equation}\hat d_{\rm raw}=\frac{Q}{P_nH_n}(N_s-N_0)-Q(u_{\rm cmd}-u_0).\end{equation}
The last estimate before absolute time 45 s is latched as a trim bias $d_0$. Compensation engages over the following two seconds, before the evaluation starts at 60 s:
\begin{equation}c=\operatorname{clip}\{0.7(\hat d_{\rm raw}-d_0),-1,1\},\qquad
u_{\rm cmd}=\operatorname{clip}\{u_{\rm PI}-c,0.2,4\}.\end{equation}
The compensation and fuel-command bounds are in lbm/s. The observer gain 0.7, cutoff 1 Hz and compensation limit 1 lbm/s are fixed engineering choices during the PI search; they are not claimed optimal.

\textbf{5. Tune PI after enabling the DOB.} The existing PI block uses $K_p(r-N_s)+K_i\int(r-N_s)dt$. Nine gain pairs, including the original (.025,.05), are followed by four local refinements. All candidates are evaluated with the DOB enabled on the requested combined cycle. Selection minimizes
\begin{equation}J=\mathrm{RMSE}_{0:25.005}+0.05R_{\rm seg},\end{equation}
where $R_{\rm seg}$ sums excess fuel total variation over 0--5, 5--10, 10--15 and 15--25.005 s. The weight is a numerical tuning weight with units rpm/(lbm/s). Invalid trajectories are rejected. This finite search selects $K_p=__KP__$ and $K_i=__KI__$; it does not establish a global optimum.
\clearpage\section{Same combined cycle, revised four-controller comparison}
The target ramps from 9000 to 10000 rpm during relative seconds 0--5. A common 2789.650 hp external load is applied at second 10 and removed at second 15, followed by recovery through 25.005 s. The load is 10\% of the previously measured settled turbine power at 10000 rpm. Physical plant, sensor settings, reference, external load and fuel limits are matched. Saved comparator traces are reused because their implementations are unchanged.
\par\noindent\includegraphics[width=\textwidth]{responses.pdf}
\clearpage\section{Results and limits}
\begin{center}\small\begin{tabular}{lrrr}\toprule Controller & Ramp RMSE & Load/recovery RMSE & Full RMSE\\ & rpm & rpm & rpm\\\midrule
__TABLE__
\bottomrule\end{tabular}\end{center}
\begin{center}\small\begin{tabular}{lrrr}\toprule Controller & Load peak $|e|$ & Load excess TV & Min. surge\\ & rpm & lbm/s & \%\\\midrule
__EXTRA__
\bottomrule\end{tabular}\end{center}
Errors use actual shaft speed, not sensed speed. Ramp RMSE covers 0--5 s; load/recovery RMSE covers 10--25.005 s; full RMSE covers the entire cycle. Load excess TV sums the 10--15 and 15--25.005 s segments. Sample interval is 0.015 s; first logged load-on is 10.005 s, and load-off is 15.000 s.

\textbf{Contribution of each change.} Base PI full-cycle RMSE is 5.408 rpm. Adding the DOB while retaining the original PI gains gives __UNTUNED__ rpm. Retuning PI with the DOB enabled gives __TUNED__ rpm. This ablation separates observer addition from gain tuning.

\textbf{Independent scenario check.} The selected gains are frozen and tested on a four-second speed ramp with a 5\% load pulse at seconds 10--15. Full-cycle RMSE is __HOLDOUT__ rpm; minimum surge margin is __HSM__\%. This check does not enter selection and is not a comparison against retuned baselines on that second scenario.

The requested combined cycle is a tuning case for DOB+PI, while the other gains were frozen from earlier studies. Consequently this is a comparison of the resulting controllers, not an equal-budget optimization contest. A local nominal model plus a DOB can tolerate some mismatch, but the small-excitation fit alone does not prove accuracy over 9000--10000 rpm. These nominal simulations are not a robust-stability proof. Fuel limits and compensation limits remain active parts of the implementation; the CSV records saturation and observer traces.
\section{Reproduction}
Run \path{dob98_identify_batch.m}, then \path{fit_dob98_model.py}, then \path{dob98_tune_batch.m}. The saved controller is \path{GasTurbine_DOB98_PI.mdl}, initialized by \path{tmats_dob98_setup.m}. Run \path{validate_dob98.py} for independent replay checks and \path{build_dob98_deliverables.py} for the revised figures and video. Data and selected parameters are under \path{results/dob98_pi_20261010}. Existing T-MATS workspace dependencies are required.
\end{document}
'''
replacements={'__U0__':f"{model['u0']:.9f}",'__A__':f"{model['a']:.10f}",'__B__':f"{model['b']:.10f}",'__FIT__':f"{model['scores'][1]['free_run_fit_pct']:.4f}",'__VRMSE__':f"{model['scores'][1]['free_run_rmse_rpm']:.6f}",'__KP__':f"{policy['Kp']:.6g}",'__KI__':f"{policy['Ki']:.6g}",'__TABLE__':tab,'__EXTRA__':extra,'__UNTUNED__':f'{tuning.iloc[0].rmse_rpm:.3f}','__TUNED__':f"{metrics.iloc[2].full_rmse_rpm:.3f}",'__HOLDOUT__':f'{validation.rmse_rpm:.3f}','__HSM__':f'{validation.min_surge_margin:.2f}'}
for k,value in replacements.items():tex=tex.replace(k,value)
(a.SRC/'DOB98_PI_Comparison.tex').write_text(tex)
if '--report-only' in sys.argv:sys.exit(0)

import build_combined_video as v
v.DATA=a.DATA;v.RUN=RUN;v.NAMES=a.NAMES;v.M=metrics;v.OUT=RUN/'video';v.OUT.mkdir(exist_ok=True)
v.DEST=ROOT/'output/video/DOB98_PI_Combined_Cycle_Comparison.mp4'
v.GAINS[2]=f"Kp {policy['Kp']:.4g} | Ki {policy['Ki']:.4g} | DOB 9800 rpm"
v.SUBTITLE='Ramp 0-5 s | 10% load 10-15 s | Identical sensors | Previous PILCO replaced by DOB98 + tuned PI'
def card():
    im=Image.new('RGB',(1920,1080),v.v.BG);d=ImageDraw.Draw(im);h=v.v
    h.txt(d,(65,55),'DOB98 + PI: identified locally, then PI retuned',40,bold=True)
    h.txt(d,(65,123),'Same combined cycle and sensors. DOB gains fixed during PI tuning.',27,h.MUTED)
    cols=[75,745,1100,1510]
    for x,s in zip(cols,['Controller','Ramp RMSE','Load/recovery RMSE','Full RMSE']):h.txt(d,(x,235),s,24,h.MUTED)
    for i,row in metrics.iterrows():
        y=330+i*100;d.rounded_rectangle((55,y-15,1865,y+68),10,fill=h.PANEL)
        for x,s in zip(cols,[row.method,f'{row.ramp_rmse_rpm:.3f}',f'{row.load_rmse_rpm:.3f}',f'{row.full_rmse_rpm:.3f}']):h.txt(d,(x,y),s,31,h.COLORS[i],True)
    h.txt(d,(75,795),f"Full RMSE: base PI 5.408 -> DOB + original PI {tuning.iloc[0].rmse_rpm:.3f} -> tuned {metrics.iloc[2].full_rmse_rpm:.3f} rpm",28,h.LOAD,True)
    h.txt(d,(75,865),'DOB+PI was tuned on this cycle. Other controller gains remain frozen.',26)
    h.txt(d,(75,922),f"Separate 4 s ramp / 5% load check: {validation.rmse_rpm:.3f} rpm full RMSE with frozen DOB+PI gains.",26)
    h.txt(d,(75,995),'Model fit is local to 9800 rpm. Nominal simulation results; no global optimality claim.',23,h.MUTED)
    return im
v.card=card;v.main()
