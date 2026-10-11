"""Combined five-second speed ramp and five-second 10% shaft-load pulse."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
RUN=ROOT/'results/pilco_combined_cycle_20261010'
KEYS=['base','poly','previous','smooth']
NAMES=['Base PI','Retuned Poly2 + PID','Previous PILCO','Smooth PILCO']
DATA=[pd.read_csv(RUN/f'{k}.csv') for k in KEYS]
SRC=ROOT/'output/pdf/combined_cycle_source'

def main():
    SRC.mkdir(parents=True,exist_ok=True)
    rows=[]
    hp=float(DATA[0].PTO_hp.max())
    ref=pd.read_csv(ROOT/'results/pilco_ramp90_equal_sensor_20261010/base.csv')
    reference=ref.PTO_turbine_hp[(ref.time_s>=68)&(ref.time_s<70)].mean()
    assert abs(hp/reference-.1)<1e-10
    for key,name,d in zip(KEYS,NAMES,DATA):
        t=d.time_s.to_numpy()-60;e=(d.Nmech-d.DOB_request).to_numpy();u=d.Wf.to_numpy()
        q=(t>=-1e-8);r=q&(t<5);ld=q&(t>=10)
        assert d.valid.eq(1).all() and d.time_s.iloc[-1]>=85
        assert np.allclose(d.time_s,DATA[0].time_s) and np.allclose(d.PTO_hp,DATA[0].PTO_hp)
        assert np.max(abs(d.DOB_request[q]-(9000+200*np.clip(t[q],0,5))))<1e-7
        assert np.allclose(d.PTO_hp,np.where((t>=10-1e-8)&(t<15-1e-8),hp,0))
        def ring(a,b):
            x=u[(t>=a-1e-8)&(t<b-1e-8)];return max(0.,abs(np.diff(x)).sum()-abs(x[-1]-x[0]))
        rows.append(dict(method=name,ramp_rmse_rpm=np.sqrt(np.mean(e[r]**2)),load_rmse_rpm=np.sqrt(np.mean(e[ld]**2)),full_rmse_rpm=np.sqrt(np.mean(e[q]**2)),load_peak_abs_rpm=max(abs(e[ld])),load_min_error_rpm=min(e[ld]),load_max_error_rpm=max(e[ld]),load_segment_excess_tv_lbm_s=ring(10,15)+ring(15,25.02),min_surge_margin_pct=d.DOB_SM[q].min(),fuel_saturation_pct=100*np.mean((u[q]<=.2+1e-9)|(u[q]>=4-1e-9))))
    m=pd.DataFrame(rows);m.to_csv(RUN/'comparison.csv',index=False);print(m.to_string(index=False),flush=True)
    (RUN/'protocol.json').write_text(json.dumps(dict(ramp_start_s=0,ramp_end_s=5,start_rpm=9000,end_rpm=10000,load_on_s=10,load_off_s=15,reference_turbine_hp=reference,pulse_hp=hp,fraction=.1,sensor_tau_s=.05,sensor_noise=False,sample_s=.015),indent=2))
    fig,axes=plt.subplots(4,1,figsize=(10,9),sharex=True)
    colors=['#2671b8','#bc8000','#8753bb','#008975']
    for name,color,d in zip(NAMES,colors,DATA):
        t=d.time_s-60;q=t>=-1
        for ax,y in zip(axes[:3],[d.Nmech/100,d.Nmech-d.DOB_request,d.Wf]):ax.plot(t[q],y[q],label=name,color=color,lw=1.2)
    axes[0].plot(t[q],DATA[0].DOB_request[q]/100,'k--',lw=1,label='Target')
    axes[3].step(t[q],DATA[0].PTO_hp[q],where='post',color='#277fb0')
    for ax,label in zip(axes,['Speed (%)','Actual - target (rpm)','Fuel (lbm/s)','External load (hp)']):
        ax.set_ylabel(label);ax.grid(alpha=.25);ax.axvspan(0,5,color='orange',alpha=.10);ax.axvspan(10,15,color='blue',alpha=.06)
    axes[0].legend(ncol=3,fontsize=8);axes[-1].set_xlabel('Time from test start (s)');fig.tight_layout();fig.savefig(SRC/'responses.pdf');fig.savefig(RUN/'responses.png',dpi=150);plt.close(fig)
    table='\n'.join(f'{x.method} & {x.ramp_rmse_rpm:.3f} & {x.load_rmse_rpm:.3f} & {x.full_rmse_rpm:.3f} \\\\' for x in m.itertuples())
    extra='\n'.join(f'{x.method} & {x.load_peak_abs_rpm:.2f} & {x.load_segment_excess_tv_lbm_s:.3f} & {x.min_surge_margin_pct:.2f} & {x.fuel_saturation_pct:.1f} \\\\' for x in m.itertuples())
    tex=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=22mm]{geometry}\usepackage{lmodern,amsmath,graphicx,booktabs,url}
\title{Combined acceleration and shaft-load cycle}\author{Four frozen controllers with identical speed sensors}\date{10 October 2026}
\begin{document}\maketitle
\section{Requested cycle}
Define relative time $\tau=t-60$ s. The shaft-speed target and external load are
\begin{align}
r(\tau)&=9000+200\min(5,\max(0,\tau))\quad\mathrm{rpm},\\
P_L(\tau)&=\begin{cases}0.1P_{\rm ref},&10\le\tau<15,\\0,&\text{otherwise}.\end{cases}
\end{align}
The speed target ramps from 90\% to 100\% in five seconds, then remains at 10000 rpm. A common load is applied at second 10 and removed at second 15. Recovery is recorded through second 25.005. The five-second pulse is programmed as a zero-order-held workspace signal, with interpolation disabled.

The reference is the mean turbine shaft power at settled 10000 rpm from seconds 8--10 of the preceding no-load base-PI run: $P_{\rm ref}=__REF__$ hp. Therefore every controller receives exactly the same pulse amplitude, __HP__ hp. This is 10\% of that common turbine-power reference, not 10\% of each controller's instantaneous power. Internal compressor power is still present.

The preparation stage begins at 10000 rpm, moves to 9000 rpm during absolute seconds 5--10, and settles before the cycle starts at absolute second 60. All cases use sea-level ISA-zero, Mach-zero conditions. Controller gains remain fixed. All four sensors have a 0.05 s time constant, unity gain, identical limits and initial conditions, and noise disabled. Wiring assertions confirm that each active controller receives the sensor output.

The model sample interval is 0.015 s. The first logged loaded sample is at relative 10.005 s, and the first unloaded sample is at 15.000 s. The programmed event interval is exactly 10--15 s; observed event timing is resolved on the sample grid. All simulations pass the existing model-validity checks.
\section{Comparison definitions}
Error means actual shaft speed minus target, $e_k=N_k-r_k$. Ramp RMSE uses $0\le\tau<5$ s; load/recovery RMSE uses $10\le\tau\le25.005$ s; full-cycle RMSE uses $0\le\tau\le25.005$ s. These are sample-weighted metrics. Scoring the two phases separately prevents the long recovery interval from concealing ramp differences.
\clearpage\section{Recorded responses}
\includegraphics[width=\textwidth]{responses.pdf}
Orange shading marks the target ramp; blue shading marks the external-load pulse. These are raw nonlinear simulation traces, with no visual smoothing.
\clearpage\section{Numerical results}
\begin{center}\small\begin{tabular}{lrrr}\toprule
Controller & Ramp RMSE & Load/recovery RMSE & Full RMSE\\ & rpm & rpm & rpm\\\midrule
__TABLE__
\bottomrule\end{tabular}\end{center}
\begin{center}\small\begin{tabular}{lrrrr}\toprule
Controller & Load peak $|e|$ & Fuel excess TV & Min. surge & Saturation\\
& rpm & lbm/s & \% & \% samples\\\midrule
__EXTRA__
\bottomrule\end{tabular}\end{center}
Fuel excess total variation is $\sum|\Delta u|-|u_{\rm end}-u_{\rm start}|$, computed separately over 10--15 s and 15--25.005 s and then summed. It describes excess command movement, not fuel consumption. Minimum surge margin and fuel saturation are evaluated over the full cycle.

The previous and smooth PILCO policies use quadratic setpoint feedforward plus PI feedback. Retuned Poly2 retains its inverse-model/PID implementation; base PI remains the original baseline. No gains, feedforward coefficients or ringing weights were fitted to this combined cycle. These are nominal transfer-test results, not proof of robustness or global superiority. In particular, all controllers share the same sensor dynamics; differences in actual-speed tracking must not be attributed to unequal sensor time constants.
\section{Reproduction and saved outputs}
Run \path{combined_cycle_batch.m} in the existing MATLAB/T-MATS workspace. New models are named \path{GasTurbine_Combined_*.mdl}; earlier studies are preserved. Raw traces, model audit JSON, numerical metrics and the exact protocol are saved under \path{results/pilco_combined_cycle_20261010}. Analysis and video builders are \path{build_combined_cycle.py} and \path{build_combined_video.py}.
\end{document}
'''.replace('__REF__',f'{reference:.3f}').replace('__HP__',f'{hp:.3f}').replace('__TABLE__',table).replace('__EXTRA__',extra)
    (SRC/'Combined_Cycle.tex').write_text(tex)

if __name__=='__main__':main()
