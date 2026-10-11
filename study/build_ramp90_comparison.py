"""Analyze frozen controllers on the five-second, no-external-load speed ramp."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
RUN=ROOT/'results/pilco_ramp90_100_5s_20261010'
SRC=ROOT/'output/pdf/ramp90_source'
SRC.mkdir(parents=True,exist_ok=True)
KEYS=['base','poly','previous','smooth']
NAMES=['Base PI','Retuned Poly2 + PID','Previous PILCO','Smooth PILCO']
COLORS=['#2671b8','#bc8000','#8753bb','#008975']
DATA=[pd.read_csv(RUN/f'{k}.csv') for k in KEYS]

def main():
    rows=[]
    for key,name,d in zip(KEYS,NAMES,DATA):
        t=d.time_s.to_numpy()-60;q=(t>=-1e-8)&(t<=20.01+1e-8);r=q&(t<5);post=q&(t>=5)
        e=d.Nmech.to_numpy()-d.DOB_request.to_numpy();u=d.Wf.to_numpy()
        assert d.valid.eq(1).all() and abs(d.PTO_hp).max()==0
        assert np.max(abs(d.DOB_request[q]-(9000+200*np.clip(t[q],0,5))))<1e-7
        assert np.max(abs(d.Nmech[(t>=-5)&(t<0)]-9000))<.1
        tp=t[post];ep=e[post];outside=np.flatnonzero(abs(ep)>1)
        settle=tp[outside[-1]+1]-5 if len(outside) and outside[-1]+1<len(tp) else (0. if not len(outside) else np.nan)
        def ring(x):return max(0.,np.abs(np.diff(x)).sum()-abs(x[-1]-x[0]))
        rows.append(dict(method=name,key=key,ramp_rmse_rpm=np.sqrt(np.mean(e[r]**2)),full_rmse_rpm=np.sqrt(np.mean(e[q]**2)),peak_abs_error_rpm=max(abs(e[q])),peak_lag_rpm=max(0.,-min(e[q])),overshoot_rpm=max(0.,max(ep)),end_ramp_speed_rpm=d.Nmech[post].iloc[0],settle_1rpm_after_ramp_s=settle,fuel_excess_tv_lbm_s=ring(u[q]),post_ramp_fuel_excess_tv_lbm_s=ring(u[post]),peak_fuel_slew_lbm_s2=max(abs(np.diff(u[q])/np.diff(t[q]))),min_surge_margin_pct=min(d.DOB_SM[q])))
    m=pd.DataFrame(rows);m.to_csv(RUN/'comparison.csv',index=False);print(m.to_string(index=False))
    fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True)
    for name,color,d in zip(NAMES,COLORS,DATA):
        t=d.time_s-60;q=(t>=-1)&(t<=20.01)
        for ax,y in zip(axes,[d.Nmech/100,d.Nmech-d.DOB_request,d.Wf]):ax.plot(t[q],y[q],label=name,color=color,lw=1.25)
    t=DATA[0].time_s-60;q=(t>=-1)&(t<=20.01);axes[0].plot(t[q],DATA[0].DOB_request[q]/100,'k--',lw=1,label='Target')
    for ax,label in zip(axes,['Speed (% of 10000 rpm)','Actual - target (rpm)','Fuel command (lbm/s)']):
        ax.set_ylabel(label);ax.grid(alpha=.25);ax.axvspan(0,5,color='orange',alpha=.09)
    axes[0].legend(ncol=3,fontsize=8);axes[-1].set_xlabel('Time from ramp start (s)');fig.tight_layout();fig.savefig(SRC/'responses.pdf');fig.savefig(RUN/'responses.png',dpi=160);plt.close(fig)
    tab='\n'.join(f"{x.method} & {x.ramp_rmse_rpm:.3f} & {x.full_rmse_rpm:.3f} & {x.peak_abs_error_rpm:.2f} & {x.settle_1rpm_after_ramp_s:.3f} \\\\" for x in m.itertuples())
    fuel='\n'.join(f"{x.method} & {x.fuel_excess_tv_lbm_s:.4f} & {x.post_ramp_fuel_excess_tv_lbm_s:.4f} & {x.overshoot_rpm:.2f} & {x.min_surge_margin_pct:.2f} \\\\" for x in m.itertuples())
    tex=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=22mm]{geometry}\usepackage{lmodern,amsmath,amssymb,graphicx,booktabs,float,url}
\title{No-load acceleration from 90\% to 100\% speed\\Five-second target ramp: frozen-controller comparison}
\author{T-MATS simulation study}\date{10 October 2026}
\begin{document}\maketitle
\begin{abstract}Four existing controllers are tested on the same nonlinear plant with zero external shaft extraction. The target rises from 9000 to 10000 rpm in five seconds. Base PI has the lowest ramp tracking error in this experiment. Ringing-aware PILCO improves ramp tracking relative to the previous PILCO, but does not outperform base PI. This is a transfer test of frozen policies, not a new training result.\end{abstract}
\section{Reproducible test protocol}
Rated speed is defined as $N_{100}=10000$ rpm. With $\tau=t-60$ s, the reference is
\begin{equation}r(\tau)=9000+200\min\{5,\max\{0,\tau\}\}\quad\text{rpm}.\end{equation}
Thus the reference acceleration is $200$ rpm/s, or two percentage points of rated speed per second. External PTO load is identically zero. The compressor still consumes shaft power: no external load does not mean zero internal torque.

The plant starts at 10000 rpm, ramps down during absolute time 5--10 s, and settles at 9000 rpm before the evaluation begins at 60 s. Controller handover is at 45 s. All four traces are within 0.1 rpm of 9000 rpm throughout the final five seconds before the test. The requested acceleration occurs at absolute time 60--65 s; simulation continues to 80.01 s. Sea-level, ISA-zero, Mach-zero settings are shared. The reference governor permits 200 rpm/s.

Logged samples are spaced by 0.015 s. The continuous target ramp lasts exactly 5 s; its first post-end sample is at $\tau=5.01$ s. Maximum logged-reference discrepancy from the equation above is below $2\times10^{-12}$ rpm. Every saved sample passes the existing model-validity flag, and every external-load sample is zero.

\section{Controllers held fixed}
\begin{center}\small\begin{tabular}{lrrr}\toprule Controller & $K_p$ & $K_i$ & $K_d$\\\midrule
Base PI & .025 & .050 & 0\\
Retuned Poly2 + PID & .025 & .140 & .00125\\
Previous PILCO & .06460568 & .17102610 & 0\\
Smooth PILCO & .02479762 & .05385920 & 0\\\bottomrule\end{tabular}\end{center}
Both PILCO-style policies retain the prior quadratic feedforward, PI feedback, saturation and anti-windup implementation. Their nominal command structure is
\begin{align}u_k^*&=p_2(r_k,0,T_k,P_k)+K_p(r_k-N_k)+I_k,\\
u_k&=\operatorname{clip}(u_k^*,0.2,4.0),\qquad
I_{k+1}=I_k+hK_i(r_k-N_k),\end{align}
with conditional integration at saturation. The zero second feedforward argument is retained from the prior controller, including during acceleration. No acceleration feedforward term is newly fitted for this test. The Poly2 PID comparator retains its previous inverse-model/derivative implementation; it is not replaced by the PILCO PI law.
\clearpage\section{Measured response}
\includegraphics[width=\textwidth]{responses.pdf}
The pale band marks the five-second target ramp. Curves are raw recorded simulation traces; no display smoothing is used. Speed curves nearly overlap at the full-speed scale, so the signed error panel is needed to distinguish tracking performance.
\clearpage\section{Quantitative comparison}
For each sample, $e_k=N_k-r_k$. Ramp RMSE uses $0\leq\tau<5$ s; full RMSE uses $0\leq\tau\leq20.01$ s. Settling is measured after ramp completion: the first recorded time after which every remaining sample stays within $\pm1$ rpm of 10000 rpm, minus 5 s. It is a finite-record measurement.
\begin{center}\small\begin{tabular}{lrrrr}\toprule
Controller & Ramp RMSE & Full RMSE & Peak $|e|$ & Settle\\
 & rpm & rpm & rpm & s after ramp\\\midrule
__TABLE__
\bottomrule\end{tabular}\end{center}
Fuel excess total variation is
\begin{equation}R_u=\sum_{k=a+1}^{b}|u_k-u_{k-1}|-|u_b-u_a|.\end{equation}
It measures movement beyond net endpoint change, in lbm/s, not fuel consumption. For acceleration, some excess variation is physically useful: fuel may rise to accelerate and then drop to its steady value. Therefore the whole-test measure is not a pure measure of unwanted oscillation. A separate post-ramp value is included. These intervals differ from the earlier load-pulse study; their totals must not be compared directly.
\begin{center}\small\begin{tabular}{lrrrr}\toprule
Controller & Whole $R_u$ & Post-ramp $R_u$ & Overshoot & Min. surge\\
 & lbm/s & lbm/s & rpm & \%\\\midrule
__FUEL__
\bottomrule\end{tabular}\end{center}
\section{Interpretation and limits}
Base PI gives the smallest ramp and full-evaluation RMSE. The smooth PILCO ramp RMSE is 10.252 rpm versus 11.224 rpm for the previous PILCO, an 8.7\% reduction. This does not establish a universal ranking: the earlier load-disturbance objective and the present acceleration objective are different.

PILCO gains were learned around 9250 rpm under load pulses. This ramp moves beyond that local operating condition; portions also lie beyond the approximately 9264--9750 rpm polynomial fitting range. The present result is evidence for this single deterministic nominal simulation, not a robustness guarantee. It does not validate the Gaussian-process model across the entire ramp or prove that a ringing penalty alone explains all differences between the gain sets.

The previous derivation remains applicable to how the gains were obtained: expected tracking and fuel-magnitude costs were augmented by expected excess fuel variation, using previous-command and segment-anchor memory. This run does not retrain that objective. A dedicated acceleration-training study would be needed to claim optimized ramp performance.
\section{Reproduction}
Run \texttt{ramp90\_batch.m} in MATLAB with the existing T-MATS dependencies. The four \path{GasTurbine_Ramp90_*.mdl} copies preserve previous studies. Raw CSV/MAT traces and summary metrics are in \path{results/pilco_ramp90_100_5s_20261010}. Run \texttt{build\_ramp90\_comparison.py} for this analysis and \texttt{build\_ramp90\_video.py} for the synchronized video.
\end{document}
'''.replace('__TABLE__',tab).replace('__FUEL__',fuel)
    (SRC/'Ramp90_Comparison.tex').write_text(tex,encoding='utf-8')

if __name__=='__main__':main()

