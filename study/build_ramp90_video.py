"""Four independent controller windows for the recorded no-load speed ramp."""
import bisect,json,subprocess
import numpy as np
import pandas as pd
from PIL import Image,ImageDraw
import imageio.v2 as imageio
import imageio_ffmpeg
import build_pilco_video_v2 as v
from build_ramp90_comparison import ROOT,RUN,DATA,NAMES

DEST=ROOT/'output/video/PILCO_90_to_100_No_Load_5s_Ramp.mp4'
OUT=RUN/'video';OUT.mkdir(exist_ok=True)
M=pd.read_csv(RUN/'comparison.csv')
v.PULSES=[(0,5)]
GAINS=['Kp .025 | Ki .050','Kp .025 | Ki .140 | Kd .00125','Kp .06461 | Ki .17103','Kp .02480 | Ki .05386']
SUBTITLE='9000 -> 10000 rpm  |  Target ramp: 5 seconds  |  Frozen gains  |  Sea level, ISA 0'
FOOTER='External shaft extraction = 0 hp throughout. Internal compressor work remains. No visual smoothing.'

def grid(d,box,limits,start,end,label,ticks):
    l,t,r,b=box;lo,hi=limits
    d.rectangle(box,fill='#0f1c2e')
    a=max(start,0);z=min(end,5)
    if z>a:d.rectangle((l+(a-start)/(end-start)*(r-l),t,l+(z-start)/(end-start)*(r-l),b),fill='#272a32')
    for y in ticks:
        yy=b-(y-lo)/(hi-lo)*(b-t);d.line((l,yy,r,yy),fill=v.GRID)
        v.txt(d,(l-10,yy),f'{y:g}',16,v.MUTED,anchor='rm')
    for x in np.linspace(start,end,5):
        xx=l+(x-start)/(end-start)*(r-l);d.line((xx,t,xx,b),fill=v.GRID)
        v.txt(d,(xx,b+6),f'{x:.1f}',15,v.MUTED,anchor='mt')
    v.txt(d,(l,t-25),label,18,v.MUTED)

class Scene:
    def __init__(self,start,end,error=False):
        self.start,self.end,self.error=start,end,error
        self.bg=Image.new('RGB',(1920,1080),v.BG);d=ImageDraw.Draw(self.bg)
        v.txt(d,(36,20),'90% to 100% speed  /  No-load acceleration',38,bold=True)
        v.txt(d,(36,73),SUBTITLE,23,v.MUTED)
        d.rounded_rectangle((36,111,1884,221),16,fill=v.PANEL)
        v.txt(d,(56,128),'TARGET SPEED',22,v.LOAD,True)
        v.txt(d,(56,171),'200 rpm/s during the ramp',20,v.MUTED)
        box=(480,136,1450,183);self.targetbox=box
        tt=np.linspace(start,end,200);yy=90+2*np.clip(tt,0,5)
        _,pts=v.coords(tt,yy,box,(89,101),start,end);d.line(pts,fill=v.LOAD,width=4)
        for x in np.linspace(start,end,6):v.txt(d,(box[0]+(x-start)/(end-start)*(box[2]-box[0]),193),f'{x:g}s',16,v.MUTED,anchor='mt')
        self.plots=[]
        q=(DATA[0].time_s>=59)&(DATA[0].time_s<=80.01)
        maxerr=max(abs(a.Nmech[q]-a.DOB_request[q]).max() for a in DATA)
        lim=5*np.ceil(maxerr/5)
        low=np.floor(min(a.Wf[q].min() for a in DATA)*10)/10-.1
        high=np.ceil(max(a.Wf[q].max() for a in DATA)*10)/10+.1
        for i,(l,t,r,b) in enumerate(v.BOXES):
            d.rounded_rectangle((l,t,r,b),16,fill=v.PANEL,outline=v.GRID)
            d.rounded_rectangle((l,t,l+7,b),3,fill=v.COLORS[i])
            v.txt(d,(l+22,t+13),NAMES[i],25,v.COLORS[i],True)
            v.txt(d,(r-18,t+20),GAINS[i],15,v.MUTED,anchor='ra')
            left=(l+65,t+126,l+432,t+278);right=(l+526,t+126,r-24,t+278)
            limits=(-lim,lim) if error else (89,101)
            grid(d,left,limits,start,end,'Actual - target (rpm)' if error else 'Speed (%) / dashed target',[-lim,0,lim] if error else [90,95,100])
            grid(d,right,(low,high),start,end,'Fuel command (lbm/s)',np.round(np.linspace(low,high,4),2))
            a=DATA[i];ts=a.time_s.to_numpy()-60
            if not error:
                tt,pts=v.coords(ts,a.DOB_request.to_numpy()/100,left,limits,start,end)
                for j in range(0,len(pts)-5,12):d.line(pts[j:j+6],fill=v.INK,width=2)
            y=(a.Nmech-a.DOB_request).to_numpy() if error else a.Nmech.to_numpy()/100
            self.plots.append((left,right,v.coords(ts,y,left,limits,start,end),v.coords(ts,a.Wf.to_numpy(),right,(low,high),start,end)))
            v.txt(d,(l+22,b-35),f'Ramp RMSE  {M.iloc[i].ramp_rmse_rpm:.3f} rpm',18,v.MUTED)
            v.txt(d,(r-22,b-35),f'Full RMSE  {M.iloc[i].full_rmse_rpm:.3f} rpm',18,v.MUTED,anchor='ra')
        v.txt(d,(36,1010),'MATCHED AXES  |  Orange shading = target ramp  |  Each window uses its own recorded controller response',21,v.MUTED)
        v.txt(d,(36,1045),FOOTER,20,v.MUTED)
    def frame(self,time):
        im=self.bg.copy();d=ImageDraw.Draw(im)
        ix=max(0,np.searchsorted(DATA[0].time_s.to_numpy()-60,time,side='right')-1)
        target=9000+200*np.clip(time,0,5)
        v.txt(d,(1500,125),f'{target/100:.2f}%  |  {target:.0f} rpm',25,v.LOAD,True)
        v.txt(d,(1500,171),f't = {time:05.2f}s  |  '+('RAMP' if 0<=time<5 else 'HOLD'),21,v.MUTED)
        l,t,r,b=self.targetbox;x=l+(time-self.start)/(self.end-self.start)*(r-l);d.line((x,t-4,x,b+4),fill=v.INK,width=2)
        for i,((l,t,r,b),(p1,p2,c1,c2)) in enumerate(zip(v.BOXES,self.plots)):
            a=DATA[i].iloc[ix];v.txt(d,(l+22,t+57),f'{a.Nmech:,.2f} rpm',25,mono=True)
            v.txt(d,(l+300,t+61),f'Error {a.Nmech-a.DOB_request:+.2f}',21,v.COLORS[i],mono=True)
            v.txt(d,(r-24,t+60),'0 hp | NO LOAD',19,v.MUTED,anchor='ra')
            v.txt(d,(r-24,t+101),f'{a.Wf:.3f}',18,v.COLORS[i],mono=True,anchor='ra')
            for box,(ts,pts) in [(p1,c1),(p2,c2)]:
                k=bisect.bisect_right(ts,time)
                if k>1:d.line(pts[:k],fill=v.COLORS[i],width=3)
                xx=box[0]+(time-self.start)/(self.end-self.start)*(box[2]-box[0]);d.line((xx,box[1],xx,box[3]),fill='#aec0d4')
        return im

def card():
    im=Image.new('RGB',(1920,1080),v.BG);d=ImageDraw.Draw(im)
    v.txt(d,(65,55),'Result: base PI tracks this acceleration best',42,bold=True)
    v.txt(d,(65,123),'Same nonlinear plant. 9000 -> 10000 rpm target in 5 s. External load = 0 hp.',27,v.MUTED)
    cols=[75,745,1100,1450]
    for x,s in zip(cols,['Controller','Ramp RMSE','Full RMSE','Settle to +/-1 rpm']):v.txt(d,(x,235),s,25,v.MUTED)
    for x,s in zip(cols,['','rpm / 0-5 s','rpm / 0-20.01 s','s after ramp end']):v.txt(d,(x,276),s,20,v.MUTED)
    for i,row in M.iterrows():
        y=345+i*100;d.rounded_rectangle((55,y-15,1865,y+68),10,fill=v.PANEL)
        for x,s in zip(cols,[row.method,f'{row.ramp_rmse_rpm:.3f}',f'{row.full_rmse_rpm:.3f}',f'{row.settle_1rpm_after_ramp_s:.3f}']):v.txt(d,(x,y),s,31,v.COLORS[i],True)
    v.txt(d,(75,805),'Smooth PILCO: 8.7% lower ramp RMSE than previous PILCO.',30,v.LOAD,True)
    v.txt(d,(75,871),'Load-pulse training does not guarantee optimal acceleration tracking.',27)
    v.txt(d,(75,922),'The ringing penalty is retained; no gains were retrained for this ramp.',27)
    v.txt(d,(75,1000),'Settling is measured over the remaining recorded horizon. All model-validity checks passed.',22,v.MUTED)
    return im

def main(preview=False):
    scenes=[Scene(-1,20),Scene(-1,9,True)];summary=card()
    for i,s in enumerate(scenes):s.frame(5.5).save(OUT/f'preview_{i}.png')
    summary.save(OUT/'summary.png')
    if preview:return
    with imageio.get_writer(DEST,fps=24,codec='libx264',quality=8,macro_block_size=8,ffmpeg_params=['-preset','fast','-movflags','+faststart']) as w:
        for s,duration in zip(scenes,[28,25]):
            for j,t in enumerate(np.linspace(s.start,s.end,duration*24)):
                w.append_data(np.asarray(s.frame(t)))
                if j%240==0:print('FRAME',j,flush=True)
        for _ in range(12*24):w.append_data(np.asarray(summary))
    reader=imageio.get_reader(DEST);meta=reader.get_meta_data();assert meta['size']==(1920,1080) and abs(meta['duration']-65)<.1
    Image.fromarray(reader.get_data(37*24)).save(OUT/'encoded.png');reader.close()
    p=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(DEST),'-f','null','-'],capture_output=True,text=True);assert p.returncode==0,p.stderr
    meta.pop('nframes',None);meta['full_decode_passed']=True;(OUT/'verification.json').write_text(json.dumps(meta,indent=2));print(DEST)

if __name__=='__main__':
    import sys
    main('--preview' in sys.argv)
