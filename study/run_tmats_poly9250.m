function run_tmats_poly9250(out,phase)
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);if ~exist(out,'dir'),mkdir(out);end
Simulink.fileGenControl('set','CacheFolder',fullfile(root,'tmp','p9250'),'CodeGenFolder',fullfile(root,'tmp','p9250'),'createDir',true);
[MWS,DOB,PTO,VF,ENV]=tmats_poly9250_setup();base='GasTurbine_PolyCompare_BasePI';poly='GasTurbine_PolyCompare_R3_Poly2FF';
load_system(base);load_system(poly);set_param(base,'CloseFcn','');set_param(poly,'CloseFcn','');cleanup=onCleanup(@()closeboth(base,poly));
if ~exist(fullfile(out,'trim.mat'),'file')
 [MWS,DOB,PTO,VF,ENV]=tmats_poly9250_setup([.025 .1 .002],0);MWS.in.SimTime=60;
 raw=simulate(base,MWS,DOB,PTO,VF,ENV);d=tmats_environment_data(raw);q=d.time_s>=55;assert(all(d.valid)&&max(abs(d.Nmech(q)-9250))<.1);
 reference_hp=mean(d.PTO_turbine_hp(q));save(fullfile(out,'trim.mat'),'reference_hp','d');
end
s=load(fullfile(out,'trim.mat'),'reference_hp');reference_hp=s.reference_hp;
if strcmp(phase,'coarse')
 [p,i,dd]=ndgrid([.015 .025 .035],[.08 .14 .20],[.001 .002 .003]);C=[[.025 .1 .002];p(:) i(:) dd(:)];save(fullfile(out,'candidates.mat'),'C');
else
 s=load(fullfile(out,'candidates.mat'),'C');C=s.C;t=readtable(fullfile(out,'summary.csv'));original=t(t.candidate==1,:);
 score=max(t.rmse_rpm/original.rmse_rpm,t.ringing_excess_TV_lbm_s/original.ringing_excess_TV_lbm_s);score(~t.accepted|t.candidate==0)=Inf;[~,best]=min(score);g=[t.Kp(best) t.Ki(best) t.Kd(best)];
 extra=repmat(g,6,1);for k=1:3,extra(2*k-1,k)=.75*g(k);extra(2*k,k)=1.25*g(k);end;C=unique([C;extra],'rows','stable');save(fullfile(out,'candidates.mat'),'C');
end
tmats_remedy_stop_invalid(base);tmats_remedy_stop_invalid(poly);records=[];
for candidate=0:size(C,1)
 name=sprintf('candidate_%02d',candidate);file=fullfile(out,[name '.mat']);
 if exist(file,'file'),s=load(file,'met');met=s.met;
 else
  g=[.025 .05 0];m=base;if candidate>0,g=C(candidate,:);m=poly;end
  [MWS,DOB,PTO,VF,ENV]=tmats_poly9250_setup(g,reference_hp);
  fprintf('POLY9250_START candidate=%d gains=%g,%g,%g\n',candidate,g);
  raw=simulate(m,MWS,DOB,PTO,VF,ENV);d=tmats_environment_data(raw);
  if candidate>0,extra={'VR_integrator_error','VR_proportional_term','VR_speed_slope','VR_accel_slope','VR_fallback'};for k=1:5,v=raw.get(extra{k});d.(extra{k})=double(v.Data(:));end;end
  met=tmats_fixed_comparison_metrics(d,9250,[0 0 0],DOB);met.candidate=candidate;met.Kp=g(1);met.Ki=g(2);met.Kd=g(3);met.reference_hp=reference_hp;
  q=d.time_s>=60;met.fallback_percent=NaN;met.input_outside_percent=NaN;if candidate>0,met.fallback_percent=100*mean(d.VR_fallback(q));met.input_outside_percent=100*mean(d.VF_outside(q));end
  met.Nc_outside_percent=100*mean(d.compressor_Nc_outside(q));
  save(file,'d','met','MWS','DOB','PTO','VF','ENV','-v7.3');writetable(d,fullfile(out,[name '.csv']));
  fprintf('POLY9250_DONE candidate=%d accepted=%d RMSE=%g ring=%g\n',candidate,met.accepted,met.rmse_rpm,met.ringing_excess_TV_lbm_s);
 end
 if isempty(records),records=met;else,records(end+1)=met;end;writetable(struct2table(records),fullfile(out,'summary.csv'));
end
end
function raw=simulate(m,MWS,DOB,PTO,VF,ENV)
in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('VF',VF);in=in.setVariable('ENV',ENV);in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');raw=sim(in);
end
function closeboth(a,b)
if bdIsLoaded(a),close_system(a,0);end;if bdIsLoaded(b),close_system(b,0);end
end
