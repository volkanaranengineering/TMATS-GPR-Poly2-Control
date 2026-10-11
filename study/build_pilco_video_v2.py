"""Four synchronized controller windows, explicit loads, and comparison scorecards.
Uses recorded T-MATS traces only; renders 1080p with Pillow and FFmpeg.
"""
from pathlib import Path
import bisect, json, subprocess
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/pilco_quadratic_pi_20261010/video_v2'
OUT.mkdir(parents=True,exist_ok=True)
DEST=ROOT/'output/video/PILCO_Four_Window_Load_Comparison.mp4'
OLD=ROOT/'results/poly2_tune9250_20260915'
RUN=ROOT/'results/pilco_quadratic_pi_20261010'
W,H,FPS=1920,1080,24
BG='#0b1423'; PANEL='#142238'; INK='#edf3fc'; MUTED='#9aacc4';GRID='#2b3c53'; LOAD='#ffb45b'
COLORS=['#77b9ff','#ffce68','#be9bff','#3ee0c1']
ERROR_LIMITS={10:(-24,24),5:(-12,12)}
NAMES=['Base PI','Original Poly2 + PID','Retuned Poly2 + PID','PILCO quadratic FF + PI']
GAINS=['Kp .025  |  Ki .050','Kp .025  |  Ki .100  |  Kd .002',
       'Kp .025  |  Ki .140  |  Kd .00125','Kp .06461  |  Ki .17103  |  Kd 0']
FONTS={}
def font(size,bold=False,mono=False):
    key=(size,bold,mono)
    if key not in FONTS:
        file='consola.ttf' if mono else ('segoeuib.ttf' if bold else 'segoeui.ttf')
        FONTS[key]=ImageFont.truetype('C:/Windows/Fonts/'+file,size)
    return FONTS[key]
def txt(d,xy,s,size=22,fill=INK,bold=False,mono=False,anchor=None):
    d.text(xy,str(s),font=font(size,bold,mono),fill=fill,anchor=anchor)
def trace_data(pct):
    files=[OLD/f'candidate_{i:02d}.csv' for i in [0,1,34]] if pct==10 else [OLD/f'validation_{n}.csv' for n in ['base','original','tuned']]
    files.append(RUN/f'pilco_{pct}pct.csv')
    ds=[pd.read_csv(f) for f in files]
    for d in ds:
        assert d.valid.eq(1).all()
        assert np.allclose(d.time_s,ds[0].time_s) and np.allclose(d.PTO_hp,ds[0].PTO_hp)
    return ds
DATA={p:trace_data(p) for p in [10,5]}
MET=pd.read_csv(RUN/'comparison.csv')
PULSES=[(10.005,15),(30,40.005),(60,75)]
BOXES=[(36,242,948,606),(972,242,1884,606),(36,626,948,990),(972,626,1884,990)]

def grid(d,box,limits,start,end,label,ticks):
    l,t,r,b=box;low,high=limits
    d.rectangle(box,fill='#0f1c2e')
    for a,z in PULSES:
        left=max(start,a);right=min(end,z)
        if right>left:
            d.rectangle((l+(left-start)/(end-start)*(r-l),t,l+(right-start)/(end-start)*(r-l),b),fill='#272a32')
    for y in ticks:
        yy=b-(y-low)/(high-low)*(b-t)
        d.line((l,yy,r,yy),fill=GRID,width=1)
        txt(d,(l-10,yy),f'{y:g}',16,MUTED,anchor='rm')
    xticks=np.linspace(start,end,7)
    for x in xticks:
        xx=l+(x-start)/(end-start)*(r-l)
        d.line((xx,t,xx,b),fill=GRID,width=1)
        txt(d,(xx,b+6),f'{x:g}',15,MUTED,anchor='mt')
    txt(d,(l,t-25),label,18,MUTED)

def coords(times,values,box,limits,start,end):
    l,t,r,b=box;lo,hi=limits
    mask=(times>=start)&(times<=end)
    ts=times[mask];ys=values[mask]
    assert ys.min()>=lo and ys.max()<=hi,(ys.min(),ys.max(),limits)
    return ts.tolist(),list(zip((l+(ts-start)/(end-start)*(r-l)).astype(int),(b-(ys-lo)/(hi-lo)*(b-t)).astype(int)))

class Scene:
    def __init__(self,pct,start,end,title,rate):
        self.pct=pct;self.start=start;self.end=end;self.ds=DATA[pct];self.rate=rate
        self.bg=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(self.bg)
        txt(d,(36,21),title,36,bold=True)
        txt(d,(36,71),'9250 rpm  /  Sea level, ISA 0  /  Same plant, request and shaft-load profile',22,MUTED)
        txt(d,(1884,31),f'{pct}% LOAD TEST',25,LOAD,True,anchor='ra')
        txt(d,(1884,73),f'{rate:g}x playback  |  24 fps',20,MUTED,anchor='ra')
        d.rounded_rectangle((36,111,1884,221),16,fill=PANEL)
        txt(d,(56,125),'SHAFT LOAD',19,LOAD,True)
        txt(d,(56,169),'Applied to all four controllers',18,MUTED)
        self.loadbox=(450,137,1520,184)
        l,t,r,b=self.loadbox
        d.rounded_rectangle((l,t,r,b),5,fill='#0c192a')
        for a,z in PULSES:
            left=max(start,a);right=min(end,z)
            if right>left:d.rectangle((l+(left-start)/(end-start)*(r-l),t,l+(right-start)/(end-start)*(r-l),b),fill='#976124')
        for x in np.linspace(start,end,7):
            xx=l+(x-start)/(end-start)*(r-l)
            txt(d,(xx,191),f'{x:g} s',16,MUTED,anchor='mt')
        self.plots=[]
        for i,(l,t,r,b) in enumerate(BOXES):
            d.rounded_rectangle((l,t,r,b),16,fill=PANEL,outline=GRID,width=1)
            d.rounded_rectangle((l,t,l+7,b),3,fill=COLORS[i])
            txt(d,(l+22,t+13),NAMES[i],25,COLORS[i],True)
            txt(d,(r-18,t+19),GAINS[i],15,MUTED,anchor='ra')
            # Two independent response charts within each controller window.
            left=(l+65,t+126,l+432,t+278)
            right=(l+526,t+126,r-24,t+278)
            errlim=ERROR_LIMITS[pct]
            fuellim=(1.0,2.2) if pct==10 else (1.2,1.85)
            grid(d,left,errlim,start,end,'Speed error (rpm)',[-20,0,20] if pct==10 else [-10,0,10])
            grid(d,right,fuellim,start,end,'Fuel command (lbm/s)',[1,1.4,1.8,2.2] if pct==10 else [1.2,1.4,1.6,1.8])
            ts=self.ds[i].time_s.to_numpy()-60
            c1=coords(ts,self.ds[i].Nmech.to_numpy()-9250,left,errlim,start,end)
            c2=coords(ts,self.ds[i].Wf.to_numpy(),right,fuellim,start,end)
            self.plots.append((left,right,c1,c2))
            m=MET[(MET.amplitude_pct==pct)&(MET.method==NAMES[i])].iloc[0]
            txt(d,(l+22,b-35),f'Full-test RMSE  {m.rmse_rpm:.3f} rpm',18,MUTED)
            txt(d,(r-22,b-35),f'Fuel ringing  {m.ringing_excess_TV_lbm_s:.3f} lbm/s',18,MUTED,anchor='ra')
        txt(d,(36,1012),'MATCHED AXES  |  Orange shading = load ON  |  White playheads = synchronized test time',20,MUTED)
        txt(d,(36,1042),'Recorded nonlinear simulations; PILCO-style offline gain learning. Ringing measures fuel reversals, not consumption.',18,MUTED)
    def frame(self,time):
        im=self.bg.copy();d=ImageDraw.Draw(im)
        times=self.ds[0].time_s.to_numpy()-60
        ix=min(np.searchsorted(times,time,side='right')-1,len(times)-1)
        hp=float(self.ds[0].PTO_hp.iloc[ix]);on=hp>1
        event='LOAD ON' if on else 'LOAD OFF'
        for a,b in PULSES:
            if 0<=time-a<.65:event='LOAD APPLIED'
            if 0<=time-b<.65:event='LOAD REMOVED'
        l,t,r,b=self.loadbox;x=l+(time-self.start)/(self.end-self.start)*(r-l)
        d.line((x,t-6,x,b+6),fill=INK,width=3)
        txt(d,(1560,125),f'{hp:,.1f} hp',28,LOAD if on else INK,True)
        txt(d,(1560,165),f'{event}   |   t = {time:05.2f} s',19,LOAD if on else MUTED)
        for i,((l,t,r,b),(p1,p2,c1,c2)) in enumerate(zip(BOXES,self.plots)):
            n=float(self.ds[i].Nmech.iloc[ix]);fuel=float(self.ds[i].Wf.iloc[ix])
            txt(d,(l+22,t+57),f'{n:,.2f} rpm',25,INK,mono=True)
            txt(d,(l+300,t+61),f'Error  {n-9250:+.2f}',21,COLORS[i],mono=True)
            txt(d,(r-24,t+101),f'{fuel:.3f}',18,COLORS[i],mono=True,anchor='ra')
            d.rounded_rectangle((r-227,t+54,r-20,t+87),7,fill='#684719' if on else '#24354b')
            txt(d,(r-123,t+70),f'{hp:,.0f} hp  |  {"ON" if on else "OFF"}',18,INK,bold=True,anchor='mm')
            for box,(ts,pts) in [(p1,c1),(p2,c2)]:
                k=bisect.bisect_right(ts,time)
                if k>1:d.line(pts[:k],fill=COLORS[i],width=3)
                xx=box[0]+(time-self.start)/(self.end-self.start)*(box[2]-box[0])
                d.line((xx,box[1],xx,box[3]),fill='#aec0d4',width=1)
                if k:
                    px,py=pts[k-1];d.ellipse((px-4,py-4,px+4,py+4),fill=COLORS[i])
        return im

def scorecard():
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    txt(d,(64,40),'The tradeoff: faster tracking, more fuel oscillation',38,bold=True)
    txt(d,(64,99),'Full 90-second evaluation. Lower RMSE, ringing and settling time are better.',25,MUTED)
    for pct,top in [(10,166),(5,514)]:
        txt(d,(64,top),f'{pct}% shaft-load pulses',29,LOAD,True)
        cols=[64,760,1110,1510]
        for x,title in zip(cols,['Controller','Speed RMSE (rpm)','Fuel ringing (lbm/s)','Settling to 0.1 rpm (s)']):txt(d,(x,top+51),title,21,MUTED)
        for i,name in enumerate(NAMES):
            y=top+91+i*49
            d.rounded_rectangle((52,y-5,1866,y+39),5,fill=PANEL if i%2==0 else '#101e31')
            m=MET[(MET.amplitude_pct==pct)&(MET.method==name)].iloc[0]
            for x,s in zip(cols,[name,f'{m.rmse_rpm:.3f}',f'{m.ringing_excess_TV_lbm_s:.3f}',f'{m.settling_to_point1_rpm_s:.3f}']):txt(d,(x,y),s,24,COLORS[i],bold=(i==3))
    d.rounded_rectangle((52,871,1866,1002),14,fill='#29302d',outline='#807042',width=1)
    txt(d,(78,890),'PILCO vs retuned Poly2 at 10% load',24,LOAD,True)
    txt(d,(78,937),'22.6% lower speed RMSE  /  11.4x higher fuel ringing  /  Longer fine settling',29,INK,True)
    txt(d,(64,1030),'A tracking improvement is not an overall controller improvement. Gains were frozen before the 5% validation.',21,MUTED)
    return im

def main(preview=False):
    specs=[(10,0,90,30,'01  /  Full test: four controllers, one load'),
           (10,9,18,20,'02  /  Load application and removal: 10%'),
           (5,9,18,20,'03  /  Frozen-policy validation: 5%')]
    scenes=[Scene(p,a,b,title,(b-a)/dur) for p,a,b,dur,title in specs]
    for i,(s,spec) in enumerate(zip(scenes,specs)):
        snap=s.frame(10.35 if spec[1] else 30.35)
        snap.save(OUT/f'preview_{i+1}.png')
    summary=scorecard();summary.save(OUT/'summary.png')
    if preview:return
    with imageio.get_writer(DEST,fps=FPS,codec='libx264',quality=8,macro_block_size=8,ffmpeg_params=['-preset','fast','-movflags','+faststart']) as writer:
        for scene,(_,a,b,dur,title) in zip(scenes,specs):
            for k,t in enumerate(np.linspace(a,b,dur*FPS)):
                writer.append_data(np.asarray(scene.frame(t)))
                if k%(FPS*10)==0:print(title,'frame',k,flush=True)
            print('DONE',title,flush=True)
        arr=np.asarray(summary)
        for _ in range(8*FPS):writer.append_data(arr)
    reader=imageio.get_reader(DEST);meta=reader.get_meta_data()
    assert meta['size']==(1920,1080) and abs(meta['duration']-78)<.1,meta
    for name,k in [('encoded_10pct',int(32*FPS)),('encoded_5pct',int(52*FPS)),('encoded_summary',int(74*FPS))]:
        Image.fromarray(reader.get_data(k)).save(OUT/f'{name}.png')
    reader.close()
    r=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(DEST),'-f','null','-'],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    meta={k:v for k,v in meta.items() if k!='nframes'};meta['full_decode_passed']=True
    (OUT/'verification.json').write_text(json.dumps(meta,indent=2))
    print('VERIFIED',DEST,DEST.stat().st_size,flush=True)

if __name__=='__main__':
    import sys
    main('--preview' in sys.argv)
