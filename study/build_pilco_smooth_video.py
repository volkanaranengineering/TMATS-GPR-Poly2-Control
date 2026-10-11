"""Repeat the approved four-window format with previous vs smooth PILCO."""
import json,subprocess
import numpy as np
import pandas as pd
from PIL import Image,ImageDraw
import imageio.v2 as imageio
import imageio_ffmpeg
import build_pilco_video_v2 as v
from pilco_smooth import ROOT,OUT

sel=json.loads((OUT/'selected_policy.json').read_text())
v.OUT=OUT/'video_preview';v.OUT.mkdir(exist_ok=True)
v.DEST=ROOT/'output/video/PILCO_Smooth_Four_Window_Load_Comparison.mp4'
v.NAMES=['Base PI','Retuned Poly2 + PID','Previous PILCO','Smooth PILCO (ringing penalty)']
v.GAINS=[v.GAINS[0],v.GAINS[2],v.GAINS[3],f"Kp {sel['Kp']:.5f}  |  Ki {sel['Ki']:.5f}  |  Kd 0"]
for pct in [10,5]:
    old=v.DATA[pct]
    new=pd.read_csv(OUT/(f"candidate_{sel['candidate']:02d}.csv" if pct==10 else 'validation_5pct.csv'))
    assert new.valid.eq(1).all() and np.allclose(new.PTO_hp,old[0].PTO_hp)
    v.DATA[pct]=[old[0],old[2],old[3],new]
    maximum=max(float(abs(d.Nmech[d.time_s>=60]-9250).max()) for d in v.DATA[pct])
    lim=5*np.ceil(maximum/5);v.ERROR_LIMITS[pct]=(-lim,lim)
m=pd.read_csv(OUT/'comparison.csv')
mapping={'Base PI':v.NAMES[0],'Retuned Poly2':v.NAMES[1],'Previous PILCO':v.NAMES[2],'Smooth PILCO':v.NAMES[3]}
v.MET=m[m.method.isin(mapping)].copy();v.MET['method']=v.MET.method.map(mapping)

def explanation():
    im=Image.new('RGB',(1920,1080),v.BG);d=ImageDraw.Draw(im)
    v.txt(d,(70,65),'Smoother PILCO: what changed?',46,bold=True)
    v.txt(d,(70,137),'Same quadratic feedforward + PI structure. New gains learned with a ringing penalty.',27,v.MUTED)
    blocks=[('1  /  Keep tracking in the objective','Expected speed error + fuel magnitude remain in the cost.'),
            ('2  /  Charge for fuel reversals','Ringing = total fuel-command movement minus net endpoint change.'),
            ('3  /  Preserve uncertainty and memory','Previous fuel and event-start fuel are included in the prediction state.'),
            ('4  /  Select, freeze, validate','Choose gains on the 10% test, then validate them at 5% without retuning.')]
    for i,(title,body) in enumerate(blocks):
        y=230+i*155;d.rounded_rectangle((60,y,1860,y+132),15,fill=v.PANEL)
        v.txt(d,(90,y+20),title,29,v.COLORS[3],True);v.txt(d,(90,y+70),body,27)
    v.txt(d,(70,917),f"Selected ringing weight: {sel['weight']:g}    |    Kp = {sel['Kp']:.6f}    |    Ki = {sel['Ki']:.6f}",31,v.LOAD,True)
    v.txt(d,(70,997),'All following traces are nonlinear T-MATS results. Curves have not been visually smoothed.',23,v.MUTED)
    return im

def summary_card():
    im=Image.new('RGB',(1920,1080),v.BG);d=ImageDraw.Draw(im)
    v.txt(d,(64,40),'Measured result: smoother fuel, a tracking tradeoff',38,bold=True)
    v.txt(d,(64,99),'Full 90-second evaluation. Lower RMSE, ringing and settling time are better.',25,v.MUTED)
    for pct,top in [(10,166),(5,514)]:
        v.txt(d,(64,top),f'{pct}% shaft-load pulses',29,v.LOAD,True)
        cols=[64,760,1110,1510]
        for x,title in zip(cols,['Controller','Speed RMSE (rpm)','Fuel ringing (lbm/s)','Settling to 0.1 rpm (s)']):v.txt(d,(x,top+51),title,21,v.MUTED)
        for i,name in enumerate(v.NAMES):
            y=top+91+i*49;d.rounded_rectangle((52,y-5,1866,y+39),5,fill=v.PANEL if i%2==0 else '#101e31')
            row=v.MET[(v.MET.amplitude_pct==pct)&(v.MET.method==name)].iloc[0]
            for x,s in zip(cols,[name,f'{row.rmse_rpm:.3f}',f'{row.ringing_excess_TV_lbm_s:.3f}',f'{row.settling_to_point1_rpm_s:.3f}']):v.txt(d,(x,y),s,24,v.COLORS[i],bold=(i==3))
    t=v.MET[v.MET.amplitude_pct==10].set_index('method');a=t.loc[v.NAMES[2]];b=t.loc[v.NAMES[3]]
    d.rounded_rectangle((52,871,1866,1002),14,fill='#29302d',outline='#807042',width=1)
    v.txt(d,(78,890),'Smooth vs previous PILCO at 10% load',24,v.LOAD,True)
    v.txt(d,(78,937),f"Ringing reduced {100*(1-b.ringing_excess_TV_lbm_s/a.ringing_excess_TV_lbm_s):.1f}%  /  Speed RMSE {a.rmse_rpm:.3f} -> {b.rmse_rpm:.3f} rpm",29,bold=True)
    v.txt(d,(64,1030),'Smoothing is measured on the plant; it does not imply superiority over every prior controller.',21,v.MUTED)
    return im

def main(preview=False):
    specs=[(10,0,90,30,'01  /  Ringing-aware PILCO: full load test'),
           (10,9,18,24,'02  /  Observe fuel reversals: 10% load'),
           (5,9,18,24,'03  /  Frozen gains: 5% load validation')]
    scenes=[v.Scene(p,a,b,title,(b-a)/dur) for p,a,b,dur,title in specs]
    intro=explanation();summary=summary_card()
    intro.save(v.OUT/'explanation.png');summary.save(v.OUT/'summary.png')
    for i,s in enumerate(scenes):s.frame(11.2 if i else 31.2).save(v.OUT/f'preview_{i+1}.png')
    if preview:return
    with imageio.get_writer(v.DEST,fps=v.FPS,codec='libx264',quality=8,macro_block_size=8,ffmpeg_params=['-preset','fast','-movflags','+faststart']) as writer:
        for _ in range(12*v.FPS):writer.append_data(np.asarray(intro))
        for s,(_,a,b,dur,title) in zip(scenes,specs):
            for k,t in enumerate(np.linspace(a,b,dur*v.FPS)):
                writer.append_data(np.asarray(s.frame(t)))
                if k%(10*v.FPS)==0:print(title,k,flush=True)
        for _ in range(12*v.FPS):writer.append_data(np.asarray(summary))
    reader=imageio.get_reader(v.DEST);meta=reader.get_meta_data();assert meta['size']==(1920,1080) and abs(meta['duration']-102)<.1
    for name,sec in [('encoded_10pct',48),('encoded_5pct',72),('encoded_summary',95)]:Image.fromarray(reader.get_data(sec*v.FPS)).save(v.OUT/f'{name}.png')
    reader.close();proc=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(v.DEST),'-f','null','-'],capture_output=True,text=True);assert proc.returncode==0,proc.stderr
    meta.pop('nframes',None);meta['full_decode_passed']=True;(OUT/'video_verification.json').write_text(json.dumps(meta,indent=2));print('VERIFIED',v.DEST)

if __name__=='__main__':
    import sys
    main('--preview' in sys.argv)
