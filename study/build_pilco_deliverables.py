"""Verify nonlinear traces and produce the comparison paper and animation."""
from pathlib import Path
import json, hashlib, shutil, subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
import imageio.v2 as imageio
import fitz
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/pilco_quadratic_pi_20261010';OLD=ROOT/'results/poly2_tune9250_20260915'
PAPER=ROOT/'output/pdf/pilco_quadratic_pi_source';PAPER.mkdir(parents=True,exist_ok=True)
VIDEO=ROOT/'output/video';VIDEO.mkdir(parents=True,exist_ok=True)
COLORS=['#60758b','#d69a32','#8c64b3','#00a18d']
NAMES=['Base PI','Original Poly2 + PID','Retuned Poly2 + PID','PILCO quadratic FF + PI']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,'pdf.fonttype':42})

def datasets(validation=False):
    files=[OLD/f'validation_{s}.csv' for s in ['base','original','tuned']] if validation else [OLD/f'candidate_{i:02d}.csv' for i in [0,1,34]]
    files.append(OUT/('pilco_5pct.csv' if validation else 'pilco_10pct.csv'))
    return [pd.read_csv(f) for f in files]

def metrics(d):
    q=d.time_s>=60;e=d.Nmech[q]-9250
    starts=np.array([70.005,75,90,100.005,120,135]);ends=[75,90,100.005,120,135,150]
    ring=0;settle=0
    for a,b in zip(starts,ends):
        f=d.Wf[(d.time_s>=a-1e-8)&(d.time_s<=a+2+1e-8)].to_numpy()
        ring+=max(0,np.abs(np.diff(f)).sum()-abs(f[-1]-f[0]))
        z=d[(d.time_s>=a-1e-8)&(d.time_s<b-1e-8)];bad=np.flatnonzero(abs(z.Nmech.to_numpy()-9250)>.1)
        val=0 if len(bad)==0 else (np.inf if bad[-1]==len(z)-1 else z.time_s.iloc[bad[-1]+1]-a)
        settle=max(settle,val)
    return dict(rmse_rpm=np.sqrt(np.mean(e*e)),peak_rpm=abs(e).max(),iae_rpm_s=abs(e).sum()*.015,
                ringing_excess_TV_lbm_s=ring,settling_to_point1_rpm_s=settle,
                minimum_margin_percent=d.DOB_SM[q].min(),fuel_limit_percent=100*np.mean((d.DOB_command[q]<=.2+1e-9)|(d.DOB_command[q]>=4-1e-9)))

def verify():
    policy=json.loads((OUT/'policy.json').read_text());checks=[];records=[]
    for val in [False,True]:
        ds=datasets(val)
        for name,d in zip(NAMES,ds):
            assert d.valid.eq(1).all() and abs(d.time_s.iloc[-1]-150)<1e-8
            for field in ['time_s','DOB_request','PTO_hp']:
                assert np.max(abs(d[field]-ds[0][field]))<1e-8,(name,field)
            records.append(dict(method=name,amplitude_pct=5 if val else 10,**metrics(d)))
        d=ds[-1];q=d.time_s>=45
        e=d.DOB_request-d.DOB_sensed
        predicted=d.VF_setpoint+policy['Kp']*e+d.VF_integral
        err=float(np.max(abs(predicted[q]-d.VF_unsaturated[q])))
        cmd=float(np.max(abs(np.clip(predicted[q],.2,4)-d.Wf[q])))
        integ=d.VF_integral.to_numpy();u=d.VF_unsaturated.to_numpy();ev=e.to_numpy()
        active=((u<4)|(ev<0))&((u>.2)|(ev>0))
        expected=integ[:-1]+.015*policy['Ki']*ev[:-1]*active[:-1]
        imax=float(np.max(abs(expected[q.to_numpy()[:-1]]-integ[1:][q.to_numpy()[:-1]])))
        assert max(err,cmd,imax)<1e-8,(err,cmd,imax)
        checks.append(dict(amplitude_pct=5 if val else 10,command_replay_error=cmd,unsaturated_replay_error=err,integral_update_error=imax,all_valid=True))
    summary=pd.DataFrame(records);summary.to_csv(OUT/'comparison.csv',index=False)
    pd.DataFrame(checks).to_csv(OUT/'verification.csv',index=False)
    # Independent agreement with original MATLAB metric implementation.
    saved=pd.read_csv(OUT/'simulation_summary.csv')
    for method,pct in [('pilco_10pct',10),('pilco_5pct',5)]:
        a=saved[saved.method==method].iloc[0];b=summary[(summary.method==NAMES[-1])&(summary.amplitude_pct==pct)].iloc[0]
        assert a.accepted==1
        for field in metrics(d):assert np.isclose(a[field],b[field],rtol=1e-8,atol=1e-8),(field,a[field],b[field])
    return summary,checks

def plots():
    for val in [False,True]:
        ds=datasets(val)
        for zoom in ([False,True] if not val else [False]):
            fig,axs=plt.subplots(3,1,figsize=(10,5.7),sharex=True,gridspec_kw={'height_ratios':[2,1.3,.7]})
            for i,d in enumerate(ds):
                d=d[(d.time_s>=69 if zoom else d.time_s>=60)&(d.time_s<=78 if zoom else d.time_s<=150)]
                t=d.time_s-60
                axs[0].plot(t,d.Nmech-9250,color=COLORS[i],lw=1.1,label=NAMES[i])
                axs[1].plot(t,d.Wf,color=COLORS[i],lw=1.1)
            axs[2].plot(ds[0].time_s-60,ds[0].PTO_hp,color='#20374e')
            axs[0].set_ylabel('Speed error (rpm)');axs[1].set_ylabel('Fuel (lbm/s)');axs[2].set_ylabel('Load (hp)');axs[2].set_xlabel('Evaluation time (s)')
            axs[0].legend(ncol=2,fontsize=8,loc='upper right');axs[-1].set_xlim(9,18) if zoom else axs[-1].set_xlim(0,90)
            fig.suptitle(f'{5 if val else 10}% shaft-load pulses | 9250 rpm | sea level ISA 0',fontweight='bold');fig.tight_layout()
            filename='zoom_10pct' if zoom else f'comparison_{5 if val else 10}pct'
            fig.savefig(PAPER/(filename+'.pdf'));fig.savefig(OUT/(filename+'.png'),dpi=160);plt.close(fig)
    p=pd.read_csv(OUT/'policy_search.csv');r=pd.read_csv(OUT/'predicted_rollout.csv')
    fig,ax=plt.subplots(1,2,figsize=(10,3.4));ax[0].plot(p.evaluation,p.expected_cost,color=COLORS[-1]);ax[0].set(xlabel='Objective evaluation',ylabel='Expected cost',title='Offline policy improvement')
    ax[1].plot(r.time_s,r.mean_speed_error_rpm,color=COLORS[-1]);ax[1].fill_between(r.time_s,r.mean_speed_error_rpm-2*r.std_speed_rpm,r.mean_speed_error_rpm+2*r.std_speed_rpm,color=COLORS[-1],alpha=.2)
    ax[1].set(xlabel='Planning time (s)',ylabel='Speed error (rpm)',title='GP mean and +/- 2 standard deviations');fig.tight_layout();fig.savefig(PAPER/'learning.pdf');plt.close(fig)

def table(summary,pct):
    t=summary[summary.amplitude_pct==pct]
    rows=[]
    for _,r in t.iterrows():
        rows.append(f"{r.method.replace('quadratic FF + PI','FF+PI')} & {r.rmse_rpm:.4f} & {r.peak_rpm:.3f} & {r.ringing_excess_TV_lbm_s:.4f} & {r.settling_to_point1_rpm_s:.3f} " + r'\\')
    return r'\begin{table}[H]\centering\small\begin{tabular}{lrrrr}\toprule Controller & RMSE & Peak & Ringing & Settling\\ & rpm & rpm & lbm/s & s\\\midrule'+'\n'+'\n'.join(rows)+r'\bottomrule\end{tabular}\caption{'+str(pct)+r'\% load-amplitude comparison.}\end{table}'

def paper(summary,checks):
    p=json.loads((OUT/'policy.json').read_text());mc=json.loads((OUT/'moment_checks.json').read_text());gp=pd.read_csv(OUT/'gp_holdout.csv')
    t=summary[summary.amplitude_pct==10].set_index('method');new=t.loc[NAMES[-1]]
    sentence=f"The new nonlinear simulation has speed RMSE {new.rmse_rpm:.4f} rpm, peak error {new.peak_rpm:.3f} rpm, and fuel ringing {new.ringing_excess_TV_lbm_s:.4f} lbm/s. Compared with retuned Poly2, tracking RMSE falls by {100*(1-new.rmse_rpm/t.loc[NAMES[2]].rmse_rpm):.1f}\\%, but ringing grows to {new.ringing_excess_TV_lbm_s/t.loc[NAMES[2]].ringing_excess_TV_lbm_s:.1f} times its previous value. This is a tracking--actuation tradeoff, not an overall improvement."
    comparisons=[]
    for name in [NAMES[0],NAMES[2]]:
        r=t.loc[name];comparisons.append(f"Relative to {name}, RMSE changes by {100*(new.rmse_rpm/r.rmse_rpm-1):+.1f}\\% and ringing by {100*(new.ringing_excess_TV_lbm_s/r.ringing_excess_TV_lbm_s-1):+.1f}\\%.")
    seed=pd.read_csv(OUT/'simulation_summary.csv').set_index('method').loc['seed_pi_10pct']
    discussion=' '.join(comparisons)+f" The initial feedforward PI has RMSE {seed.rmse_rpm:.4f} rpm and ringing {seed.ringing_excess_TV_lbm_s:.4f} lbm/s. These quantities describe different tradeoffs; minimizing expected tracking cost does not directly minimize fuel reversals."
    checktext=f"The analytic GP covariance agrees with a 50,000-input Monte Carlo integration to {100*mc['covariance_relative_error']:.2f}\\% relative Frobenius error; input/output cross-covariance error is {100*mc['cross_covariance_relative_error']:.2f}\\%. Held-out one-step speed-increment RMSE ranges from {gp.speed_increment_rmse_rpm.min():.6f} to {gp.speed_increment_rmse_rpm.max():.6f} rpm. Independent command and integral replay errors are below $10^{{-8}}$. All evaluated new traces pass the existing numerical acceptance checks. The selected 10\\% run has minimum surge margin {new.minimum_margin_percent:.3f}\\% and fuel saturation fraction {new.fuel_limit_percent:.3f}\\%."
    text=(ROOT/'pilco_paper_template.tex').read_text()
    tokens={'RESULT_SENTENCE':sentence,'U0':f"{p['u0']:.8f}",'NTRAIN':str(p['training_transitions']),'KP':f"{p['Kp']:.8f}",'KI':f"{p['Ki']:.8f}",'J0':f"{p['initial_cost']:.6f}",'J1':f"{p['selected_cost']:.6f}",'TABLE10':table(summary,10),'TABLE5':table(summary,5),'CHECKS':checktext,'DISCUSSION':discussion}
    for k,v in tokens.items():text=text.replace('@@'+k+'@@',v)
    import re
    text=re.sub(r'\\texttt\{([^}]+)\}',lambda m:r'\path{'+m.group(1).replace(r'\_','_')+'}',text)
    assert '@@' not in text
    (PAPER/'PILCO_Quadratic_FF_PI.tex').write_text(text)
    exe=r'C:\Program Files\MiKTeX 2.9\miktex\bin\x64\pdflatex.exe'
    for _ in range(2):
        r=subprocess.run([exe,'-disable-installer','-interaction=nonstopmode','-halt-on-error','PILCO_Quadratic_FF_PI.tex'],cwd=PAPER,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
        (OUT/'latex_build.log').write_text(r.stdout)
        if r.returncode:raise RuntimeError(r.stdout[-3000:])
    final=ROOT/'output/pdf/PILCO_Quadratic_FF_PI_Comparison.pdf';shutil.copy2(PAPER/'PILCO_Quadratic_FF_PI.pdf',final)
    doc=fitz.open(final);render=OUT/'paper_preview';render.mkdir(exist_ok=True)
    for i,page in enumerate(doc):page.get_pixmap(matrix=fitz.Matrix(1.15,1.15)).save(render/f'page_{i+1:02d}.png')
    print('PAPER',len(doc),'pages',flush=True)

def video(summary):
    target=VIDEO/'PILCO_Quadratic_FF_PI_Comparison.mp4'
    writer=imageio.get_writer(target,fps=15,codec='libx264',quality=8,macro_block_size=16)
    scenes=[(False,0,90,30,'Full 10% load comparison'),(False,9,18,18,'First pulse - slow motion'),(True,9,18,18,'Frozen gains - 5% validation')]
    for val,start,end,duration,title in scenes:
        ds=datasets(val);fig=plt.figure(figsize=(12.8,7.2),dpi=100,facecolor='#f4f7fa')
        fig.text(.045,.95,title,fontsize=21,fontweight='bold',color='#142e46')
        fig.text(.045,.912,'9250 rpm | sea level ISA 0 | recorded nonlinear T-MATS simulations',fontsize=10,color='#516375')
        stamp=fig.text(.78,.942,'',fontsize=13,color='#142e46')
        ax1=fig.add_axes([.07,.39,.59,.43]);ax2=fig.add_axes([.07,.13,.59,.20],sharex=ax1)
        ax1.set_ylabel('Speed error (rpm)');ax2.set_ylabel('Fuel (lbm/s)');ax2.set_xlabel('Evaluation time (s)')
        ax1.set_xlim(start,end);ax1.set_ylim((-25,25) if not val else (-13,13));ax2.set_ylim(1.0,2.15 if not val else 1.85)
        lines=[];fuel=[];rotors=[];labels=[]
        for i,(d,name,color) in enumerate(zip(ds,NAMES,COLORS)):
            line,=ax1.plot([],[],color=color,lw=1.7,label=name);lines.append(line)
            line,=ax2.plot([],[],color=color,lw=1.5);fuel.append(line)
            a=fig.add_axes([.715,.68-i*.155,.075,.115]);a.set_aspect('equal');a.set(xlim=(-1.2,1.2),ylim=(-1.2,1.2));a.axis('off');a.add_patch(Circle((0,0),1,fill=False,ec=color,lw=2));a.add_patch(Circle((0,0),.18,color=color))
            blades=[]
            for j in range(6):
                blade=Polygon([[0,0],[.9,0],[.6,.2]],color=color,alpha=.8);a.add_patch(blade);blades.append(blade)
            rotors.append(blades)
            fig.text(.8,.762-i*.155,name,fontsize=8.5,color=color,fontweight='bold')
            labels.append(fig.text(.8,.735-i*.155,'',fontsize=10,color='#142e46',va='top'))
        ax1.legend(loc='upper right',fontsize=7.5,ncol=2)
        cursor1=ax1.axvline(start,color='#172c42',lw=.8,alpha=.5);cursor2=ax2.axvline(start,color='#172c42',lw=.8,alpha=.5)
        loadlabel=fig.text(.71,.115,'',fontsize=10,color='#142e46')
        fig.text(.045,.044,'10% test versus retuned Poly2: tracking RMSE -22.6%; fuel ringing 11.4x higher.',fontsize=10,color='#142e46')
        fig.text(.045,.018,'Rotor motion is illustrative and visually scaled. Curves and readouts use saved plant data.',fontsize=8.5,color='#516375')
        for frame,t in enumerate(np.linspace(start,end,int(duration*15))):
            stamp.set_text(f'Test time  {t:5.2f} s')
            for i,d in enumerate(ds):
                times=d.time_s.to_numpy()-60;ix=np.searchsorted(times,t);ix=min(ix,len(d)-1);mask=(times>=start)&(times<=t)
                lines[i].set_data(times[mask],d.Nmech.to_numpy()[mask]-9250);fuel[i].set_data(times[mask],d.Wf.to_numpy()[mask])
                rpm=d.Nmech.iloc[ix];labels[i].set_text(f'{rpm:8.2f} rpm\n{d.Wf.iloc[ix]:.3f} lbm/s')
                angle=frame*.15*(rpm/9250)
                for j,blade in enumerate(rotors[i]):
                    a=angle+j*np.pi/3;R=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]]);blade.set_xy(np.array([[.15,0],[.9,0],[.65,.23]])@R.T)
            cursor1.set_xdata([t,t]);cursor2.set_xdata([t,t]);loadlabel.set_text(f'Shaft load: {ds[0].PTO_hp.iloc[ix]:.1f} hp\nPlayback: {(end-start)/duration:.2f}x simulation time')
            fig.canvas.draw();writer.append_data(np.asarray(fig.canvas.buffer_rgba())[:,:,:3])
            if frame==len(np.linspace(start,end,int(duration*15)))//2:
                fig.savefig(OUT/f'video_preview_{"5pct" if val else ("zoom" if start else "full")}.png')
        plt.close(fig);print('VIDEO SCENE',title,flush=True)
    writer.close()
    reader=imageio.get_reader(target);meta=reader.get_meta_data();first=reader.get_data(0);reader.close()
    assert meta['size']==(1280,720) and abs(meta['duration']-66)<.2,meta
    (OUT/'video_metadata.json').write_text(json.dumps(meta,default=str,indent=2));print('VIDEO',target,flush=True)

def manifest():
    files=list(OUT.glob('*.csv'))+list(OUT.glob('*.json'))+[ROOT/n for n in ['pilco_tmats.py','tmats_pilco_pi_sfun.m','tmats_pilco_setup.m','run_tmats_pilco.m','GasTurbine_PILCO_Quadratic_PI.mdl','pilco_paper_template.tex','build_pilco_deliverables.py']]
    files += [OLD/f'candidate_{n:02d}.csv' for n in [0,1,34]]+[OLD/f'validation_{n}.csv' for n in ['base','original','tuned']]
    (OUT/'SHA256_manifest.txt').write_text('\n'.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(ROOT)) for f in files))

if __name__=='__main__':
    import sys
    summary,checks=verify();plots();paper(summary,checks)
    if '--no-video' not in sys.argv:video(summary)
    manifest();print(summary.to_string(index=False))
