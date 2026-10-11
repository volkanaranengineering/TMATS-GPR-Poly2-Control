"""Verify plant traces, generate detailed figures and native LaTeX paper."""
from pathlib import Path
import json,shutil,subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pymupdf
from pilco_smooth import ROOT,OUT
from build_pilco_deliverables import metrics
OLD=ROOT/'results/poly2_tune9250_20260915';PREV=ROOT/'results/pilco_quadratic_pi_20261010'
PAPER=ROOT/'output/pdf/pilco_smooth_source';PAPER.mkdir(parents=True,exist_ok=True)
NAMES=['Base PI','Original Poly2','Retuned Poly2','Previous PILCO','Smooth PILCO']
COLORS=['#6699cc','#ccaa55','#a18ac6','#e77858','#00a68c']
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2,'pdf.fonttype':42})

def data(pct):
    sel=json.loads((OUT/'selected_policy.json').read_text())
    fs=[OLD/f'candidate_{i:02d}.csv' for i in [0,1,34]] if pct==10 else [OLD/f'validation_{n}.csv' for n in ['base','original','tuned']]
    fs += [PREV/f'pilco_{pct}pct.csv',OUT/(f"candidate_{sel['candidate']:02d}.csv" if pct==10 else 'validation_5pct.csv')]
    return [pd.read_csv(f) for f in fs]

def verify():
    sel=json.loads((OUT/'selected_policy.json').read_text());records=[];checks=[];events=[]
    for pct in [10,5]:
        ds=data(pct)
        for name,d in zip(NAMES,ds):
            assert d.valid.eq(1).all() and abs(d.time_s.iloc[-1]-150)<1e-8
            for col in ['time_s','DOB_request','PTO_hp']:assert np.max(abs(d[col]-ds[0][col]))<1e-8
            rec=dict(method=name,amplitude_pct=pct,**metrics(d))
            q=d.time_s>=60;rec['peak_fuel_slew']=float(np.max(abs(np.diff(d.Wf[q])))/.015)
            records.append(rec)
            for event,start in enumerate([70.005,75,90,100.005,120,135],1):
                win=d[(d.time_s>=start-1e-8)&(d.time_s<=start+2+1e-8)]
                f=win.Wf.to_numpy();tv=float(abs(np.diff(f)).sum());net=float(abs(f[-1]-f[0]))
                events.append(dict(method=name,amplitude_pct=pct,event=event,event_time_s=start-60,
                                   total_variation=tv,net_change=net,excess_TV=max(0,tv-net),
                                   peak_error_rpm=float(abs(win.Nmech-9250).max())))
        d=ds[-1];q=d.time_s>=45;e=d.DOB_request-d.DOB_sensed
        u=d.VF_setpoint+sel['Kp']*e+d.VF_integral
        cmd=float(max(abs(np.clip(u[q],.2,4)-d.Wf[q])))
        ev=e.to_numpy();raw=d.VF_unsaturated.to_numpy();ii=d.VF_integral.to_numpy();active=((raw<4)|(ev<0))&((raw>.2)|(ev>0))
        pred=ii[:-1]+.015*sel['Ki']*ev[:-1]*active[:-1]
        ierr=float(max(abs(pred[q.to_numpy()[:-1]]-ii[1:][q.to_numpy()[:-1]])))
        assert max(cmd,ierr)<1e-8
        saved=pd.read_csv(OUT/('tuning_results.csv' if pct==10 else 'validation_summary.csv'))
        row=saved[saved.candidate==sel['candidate']].iloc[0] if pct==10 else saved.iloc[0]
        assert row.accepted==1
        for col in metrics(d):assert np.isclose(row[col],records[-1][col],rtol=1e-8,atol=1e-8)
        checks.append(dict(amplitude_pct=pct,command_replay_max_error=cmd,integrator_replay_max_error=ierr,accepted=True))
    # Verify all candidate ringing/RMSE scores, not only the selected result.
    for _,row in pd.read_csv(OUT/'tuning_results.csv').iterrows():
        d=pd.read_csv(OUT/f'candidate_{int(row.candidate):02d}.csv');m=metrics(d)
        if row.accepted:
            for col in ['rmse_rpm','ringing_excess_TV_lbm_s']:assert np.isclose(m[col],row[col],rtol=1e-8)
    summary=pd.DataFrame(records);summary.to_csv(OUT/'comparison.csv',index=False);pd.DataFrame(checks).to_csv(OUT/'verification.csv',index=False)
    pd.DataFrame(events).to_csv(OUT/'event_breakdown.csv',index=False)
    return summary,checks

def plots():
    for pct,zoom,name in [(10,False,'full_comparison'),(10,True,'zoom_comparison'),(5,True,'validation_comparison')]:
        ds=data(pct);fig,ax=plt.subplots(3,1,figsize=(10,5.8),sharex=True,gridspec_kw={'height_ratios':[2,1.5,.65]})
        for i in [0,2,3,4]:
            d=ds[i];d=d[(d.time_s>=69 if zoom else d.time_s>=60)&(d.time_s<=78 if zoom else d.time_s<=150)]
            ax[0].plot(d.time_s-60,d.Nmech-9250,color=COLORS[i],lw=1.2,label=NAMES[i]);ax[1].plot(d.time_s-60,d.Wf,color=COLORS[i],lw=1.2)
        ax[2].plot(d.time_s-60,d.PTO_hp,color='#29384b');ax[0].legend(ncol=4,fontsize=8)
        for a,label in zip(ax,['Speed error (rpm)','Fuel (lbm/s)','Load (hp)']):a.set_ylabel(label)
        ax[-1].set_xlabel('Evaluation time (s)');ax[-1].set_xlim((9,18) if zoom else (0,90))
        fig.suptitle(f'{pct}% load pulses | 9250 rpm | matched nonlinear T-MATS tests',fontsize=12,fontweight='bold')
        fig.tight_layout();fig.savefig(PAPER/f'{name}.pdf');fig.savefig(OUT/f'{name}.png',dpi=150);plt.close(fig)
    t=pd.read_csv(OUT/'selection_scores.csv').sort_values('weight');fig,ax=plt.subplots(1,2,figsize=(10,3.8))
    ax[0].plot(t.rmse_rpm,t.ringing_excess_TV_lbm_s,'o-',color='#00a68c')
    for _,r in t.iterrows():ax[0].annotate(f'{r.weight:g}',(r.rmse_rpm,r.ringing_excess_TV_lbm_s),xytext=(5,4),textcoords='offset points',fontsize=8)
    ax[0].set(xlabel='Plant speed RMSE (rpm)',ylabel='Plant fuel ringing (lbm/s)',title='Penalty-weight tradeoff')
    ax[1].plot(range(len(t)),t.selection_score,'o-',color='#00a68c');ax[1].set_xticks(range(len(t)),[f'{x:g}' for x in t.weight]);ax[1].axhline(1,color='gray',ls='--');ax[1].set(xlabel='Ringing weight',ylabel='Joint score (lower is better)',title='Declared selection rule')
    fig.tight_layout();fig.savefig(PAPER/'tradeoff.pdf');plt.close(fig)
    events=pd.read_csv(OUT/'event_breakdown.csv');fig,ax=plt.subplots(figsize=(10,3.3));x=np.arange(6)
    for i,name in enumerate(['Retuned Poly2','Previous PILCO','Smooth PILCO']):
        values=events[(events.amplitude_pct==10)&(events.method==name)].sort_values('event').excess_TV.to_numpy()
        ax.bar(x+(i-1)*.24,values,width=.24,label=name,color=[COLORS[2],COLORS[3],COLORS[4]][i])
    ax.set_xticks(x,['Load 1','Unload 1','Load 2','Unload 2','Load 3','Unload 3']);ax.set_ylabel('Two-second excess TV (lbm/s)');ax.legend(ncol=3,fontsize=9);fig.tight_layout();fig.savefig(PAPER/'event_ringing.pdf');plt.close(fig)

def table(headers,rows,caption):
    return r'\begin{table}[H]\centering\small\begin{tabular}{l'+('r'*(len(headers)-1))+r'}\toprule'+'\n'+' & '.join(headers)+r'\\\midrule'+'\n'+'\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+r'\bottomrule\end{tabular}\caption{'+caption+r'}\end{table}'

def paper(summary,checks):
    sel=json.loads((OUT/'selected_policy.json').read_text());t=pd.read_csv(OUT/'selection_scores.csv').sort_values('weight');mc=json.loads((OUT/'particle_check.json').read_text())
    s=summary[summary.amplitude_pct==10].set_index('method');v=summary[summary.amplitude_pct==5].set_index('method');new=s.loc['Smooth PILCO'];old=s.loc['Previous PILCO']
    ring_reduction=100*(1-new.ringing_excess_TV_lbm_s/old.ringing_excess_TV_lbm_s)
    main=f"The selected penalty is $\\lambda={sel['weight']:g}$, with $K_p={sel['Kp']:.8f}$ and $K_i={sel['Ki']:.8f}$. In the nonlinear 10\\% test, ringing falls by {ring_reduction:.1f}\\% relative to the previous PILCO policy, from {old.ringing_excess_TV_lbm_s:.4f} to {new.ringing_excess_TV_lbm_s:.4f} lbm/s. Speed RMSE changes from {old.rmse_rpm:.4f} to {new.rmse_rpm:.4f} rpm. The smoother command therefore has a measurable tracking cost."
    candidates=table([r'$\lambda$',r'$K_p$',r'$K_i$','RMSE','Ringing','Score'],[[f'{r.weight:g}'+(r'$^\star$' if int(r.candidate)==sel['candidate'] else ''),f'{r.Kp:.5f}',f'{r.Ki:.5f}',f'{r.rmse_rpm:.4f}',f'{r.ringing_excess_TV_lbm_s:.4f}',f'{r.selection_score:.3f}'] for _,r in t.iterrows()],r'All tested penalty weights. RMSE is in rpm; ringing is in lbm/s. The star marks the selected policy.')
    tables={}
    for pct in [10,5]:
        tt=summary[summary.amplitude_pct==pct]
        tables[pct]=table(['Controller','RMSE (rpm)','Peak (rpm)','Ringing','Settling (s)'],[[r.method,f'{r.rmse_rpm:.4f}',f'{r.peak_rpm:.3f}',f'{r.ringing_excess_TV_lbm_s:.4f}',f'{r.settling_to_point1_rpm_s:.3f}'] for _,r in tt.iterrows()],f'{pct}'+r'\% load test. Ringing units are lbm/s; settling uses the persistent 0.1 rpm band.')
    paragraphs=[]
    for name in ['Base PI','Retuned Poly2','Previous PILCO']:
        r=s.loc[name]
        paragraphs.append(f"Relative to {name}, smooth PILCO changes RMSE by {100*(new.rmse_rpm/r.rmse_rpm-1):+.1f}\\%, ringing by {100*(new.ringing_excess_TV_lbm_s/r.ringing_excess_TV_lbm_s-1):+.1f}\\%, and fine settling from {r.settling_to_point1_rpm_s:.3f} to {new.settling_to_point1_rpm_s:.3f} s.")
    paragraphs.append(f"Its sampled peak fuel slew is {new.peak_fuel_slew:.3f} lbm/s$^2$, versus {old.peak_fuel_slew:.3f} for previous PILCO. Minimum surge margin changes from {old.minimum_margin_percent:.3f}\\% to {new.minimum_margin_percent:.3f}\\%; the selected 10\\% run has {new.fuel_limit_percent:.3f}\\% fuel saturation. These diagnostics complement the objective rather than entering its selection score.")
    nv=v.loc['Smooth PILCO'];ov=v.loc['Previous PILCO']
    paragraphs.append(f"With the gains frozen, the 5\\% test gives RMSE {nv.rmse_rpm:.4f} rpm and ringing {nv.ringing_excess_TV_lbm_s:.4f} lbm/s, a {100*(1-nv.ringing_excess_TV_lbm_s/ov.ringing_excess_TV_lbm_s):.1f}\\% ringing reduction from previous PILCO. This supports amplitude transfer of the smoothing effect at this operating point.")
    checktext=f"All selected traces pass the shared plant acceptance checks. Maximum independent command replay discrepancy is {max(c['command_replay_max_error'] for c in checks):.2e} lbm/s; maximum integral update discrepancy is {max(c['integrator_replay_max_error'] for c in checks):.2e} lbm/s. The folded-normal formula passes 250,000-sample scalar Monte Carlo checks, including zero-variance and nonzero-variance cases. For the selected policy, a {mc['particles']}-particle GP rollout predicts normalized excess TV {mc['particle_mean_normalized']:.6f}, compared with {mc['analytic_normalized']:.6f} from Gaussian moment closure; their relative difference is {100*mc['relative_difference']:.4f}\\%. The particle standard error is {mc['particle_standard_error']:.6f}. This checks prediction consistency on the same surrogate; it does not independently validate the physical GP uncertainty."
    limits='The result is smoother than the earlier tracking-only PILCO, but the complete comparison must also account for tracking, settling and surge margin. '
    if new.rmse_rpm>s.loc['Retuned Poly2'].rmse_rpm or new.ringing_excess_TV_lbm_s>s.loc['Retuned Poly2'].ringing_excess_TV_lbm_s:
        limits+='It does not dominate the retuned Poly2 controller on both speed RMSE and ringing. That comparator has derivative/acceleration feedback, whereas the new policy is restricted to PI. '
    limits+='The chosen weight is the best under the declared score among the tested candidates, not a universal tuning value.'
    repl=dict(MAIN=main,CANDIDATES=candidates,GAINS=r'The deployed gains are frozen at $K_p='+f"{sel['Kp']:.8f}"+r'$, $K_i='+f"{sel['Ki']:.8f}"+r'$ and $K_d=0$.',RESULTS10=tables[10],RESULTS5=tables[5],DISCUSSION='\n\n'.join(paragraphs),CHECKS=checktext,LIMITS=limits)
    tex=(ROOT/'pilco_smooth_report_template.tex').read_text()
    for k,val in repl.items():tex=tex.replace('@@'+k+'@@',val)
    assert '@@' not in tex
    (PAPER/'PILCO_Smooth_Ringing_Penalty.tex').write_text(tex)
    exe=r'C:\Program Files\MiKTeX 2.9\miktex\bin\x64\pdflatex.exe'
    for _ in range(2):
        proc=subprocess.run([exe,'-disable-installer','-interaction=nonstopmode','-halt-on-error','PILCO_Smooth_Ringing_Penalty.tex'],cwd=PAPER,capture_output=True,text=True,timeout=90)
        (OUT/'latex_build.log').write_text(proc.stdout+proc.stderr)
        if proc.returncode:raise RuntimeError(proc.stdout[-3000:])
    target=ROOT/'output/pdf/PILCO_Smooth_Ringing_Penalty.pdf';shutil.copy2(PAPER/'PILCO_Smooth_Ringing_Penalty.pdf',target)
    doc=pymupdf.open(target);preview=OUT/'paper_preview';preview.mkdir(exist_ok=True)
    for i,p in enumerate(doc):p.get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(preview/f'page_{i+1:02d}.png')
    print('PAPER',len(doc),'pages',flush=True)

if __name__=='__main__':
    summary,checks=verify();plots();paper(summary,checks);print(summary.to_string(index=False))
