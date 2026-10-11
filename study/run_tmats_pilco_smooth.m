function run_tmats_pilco_smooth(phase)
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
out=fullfile(root,'results','pilco_smooth_20261010');
Simulink.fileGenControl('set','CacheFolder',fullfile(root,'tmp','pilco_smooth_sim'),'CodeGenFolder',fullfile(root,'tmp','pilco_smooth_sim'),'createDir',true);
m='GasTurbine_PILCO_Smooth_PI';
if strcmp(phase,'tune')
 src='GasTurbine_PILCO_Quadratic_PI';load_system(src);set_param(src,'CloseFcn','');save_system(src,fullfile(root,[m '.mdl']));close_system(src,0);
 load_system(m);set_param(m,'CloseFcn','','PreLoadFcn','tmats_pilco_setup;');
 C=readtable(fullfile(out,'candidates.csv'));records=[];
 for k=1:height(C)
  [MWS,DOB,PTO,VF,ENV]=tmats_pilco_setup();VF.Kp=C.Kp(k);VF.Ki=C.Ki(k);VF.Kd=0;
  name=sprintf('candidate_%02d',C.candidate(k));file=fullfile(out,[name '.mat']);
  if exist(file,'file'),s=load(file,'met');met=s.met;
  else
   fprintf('SMOOTH_START %s\n',name);[d,met]=runone(m,MWS,DOB,PTO,VF,ENV);
   met.candidate=C.candidate(k);met.weight=C.weight(k);met.Kp=VF.Kp;met.Ki=VF.Ki;
   save(file,'d','met','MWS','DOB','PTO','VF','ENV','-v7.3');writetable(d,fullfile(out,[name '.csv']));
  end
  if isempty(records),records=met;else,records(end+1)=met;end
  writetable(struct2table(records),fullfile(out,'tuning_results.csv'));
  fprintf('SMOOTH_DONE %d accepted=%d rmse=%g ring=%g\n',met.candidate,met.accepted,met.rmse_rpm,met.ringing_excess_TV_lbm_s);
 end
elseif strcmp(phase,'validate')
 load_system(m);set_param(m,'CloseFcn','','PreLoadFcn','tmats_pilco_smooth_setup;');save_system(m);
 [MWS,DOB,PTO,VF,ENV]=tmats_pilco_smooth_setup();PTO.profile(:,2)=PTO.profile(:,2)/2;PTO.fraction=.05;
 [d,met]=runone(m,MWS,DOB,PTO,VF,ENV);met.Kp=VF.Kp;met.Ki=VF.Ki;
 save(fullfile(out,'validation_5pct.mat'),'d','met','MWS','DOB','PTO','VF','ENV','-v7.3');writetable(d,fullfile(out,'validation_5pct.csv'));writetable(struct2table(met),fullfile(out,'validation_summary.csv'));
 fprintf('SMOOTH_VALIDATION accepted=%d rmse=%g ring=%g\n',met.accepted,met.rmse_rpm,met.ringing_excess_TV_lbm_s);
else,error('Unknown phase');end
close_system(m,0);
end
function [d,met]=runone(m,MWS,DOB,PTO,VF,ENV)
if isempty(find_system(m,'SearchDepth',1,'Name','Validity signals')),tmats_remedy_stop_invalid(m);end
in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('VF',VF);in=in.setVariable('ENV',ENV);in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');
raw=sim(in);d=tmats_environment_data(raw);met=tmats_fixed_comparison_metrics(d,9250,[0 0 0],DOB);
end
