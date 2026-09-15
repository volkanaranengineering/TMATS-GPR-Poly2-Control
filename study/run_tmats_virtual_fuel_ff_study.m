function out=run_tmats_virtual_fuel_ff_study(out,indices,caseIndices)
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
worker=nargin>=2 && ~isempty(indices);
benchWorker=nargin>=3 && ~isempty(caseIndices);
selectionOnly=nargin>=3 && isempty(caseIndices);
if nargin<1
 build_tmats_virtual_fuel_ff_model;
 out=fullfile(root,'results',['virtual_fuel_ff_' datestr(now,'yyyymmdd_HHMMSS_FFF')]);mkdir(out);
end
if worker || benchWorker
 cacheId=0;if worker,cacheId=indices(1);else,cacheId=20+caseIndices(1);end
 cache=fullfile(root,'tmp',sprintf('vfff%02d',cacheId));if ~exist(cache,'dir'),mkdir(cache);end
 Simulink.fileGenControl('set','CacheFolder',cache,'CodeGenFolder',cache,'createDir',true);
end
if ~worker && ~benchWorker,fid=fopen(fullfile(root,'tmp','virtual_fuel_ff_directory.txt'),'w');fprintf(fid,'%s',out);fclose(fid);end
m='GasTurbine_Dyn_Template_VirtualFuelFF';load_system(m);cleanup=onCleanup(@()close_system(m,0));
% Tune against all four 9000-rpm ramp amplitudes, without 9500-rpm results.
fractions=[.05 .1 .2 .3];baseline=zeros(4,1);metrics=[];
for c=1:4
 label=sprintf('baseline_9000_%02d',round(100*fractions(c)));
 if exist(fullfile(out,[label '.mat']),'file'),s=load(fullfile(out,[label '.mat']));d=s.d;met=s.met;
 else,[d,met]=runone(9000,fractions(c),1,[1 20],false);savecase(d,met,label);end
 baseline(c)=met.rmse_rpm;
end
grid=[4 40;3 50;4 50;5 50;3 60;4 60;5 60;6 60];
tuning=[];best=inf;gains=grid(1,:);
if ~worker,indices=1:size(grid,1);end
for j=indices
 scores=zeros(4,1);
 for c=1:4
  label=sprintf('tune_%02d_%02d',j,c);file=fullfile(out,[label '.mat']);
  if exist(fullfile(out,[label '_failure.txt']),'file'),scores(c:end)=inf;break;end
  try
   if exist(file,'file'),s=load(file);d=s.d;met=s.met;
   else,[d,met]=runone(9000,fractions(c),1,grid(j,:),true);savecase(d,met,label);end
   scores(c)=met.rmse_rpm/baseline(c);if ~met.accepted,scores(c)=inf;end
  catch ME
   fid=fopen(fullfile(out,[label '_failure.txt']),'w');fprintf(fid,'%s',getReport(ME,'extended','hyperlinks','off'));fclose(fid);
   scores(c)=inf;
  end
  % One invalid operating case already disqualifies the gain pair.
  if ~isfinite(scores(c)),scores(c:end)=inf;break;end
 end
 score=mean(scores);tuning=[tuning;grid(j,:) score scores']; %#ok<AGROW>
 tunefile='tuning.csv';if worker,tunefile=sprintf('tuning_worker_%02d.csv',indices(1));end
 if ~benchWorker,writetable(array2table(tuning,'VariableNames',{'Kp','Ki','score','ratio05','ratio10','ratio20','ratio30'}),fullfile(out,tunefile));end
 if score<best,best=score;gains=grid(j,:);end
 fprintf('TUNING %d Kp=%g Ki=%g score=%g best=%g\n',j,grid(j,:),score,best);
end
if worker,fprintf('TUNING_WORKER_COMPLETE\n');return;end
assert(isfinite(best),'No physically valid tuning candidate.');
if ~benchWorker,save(fullfile(out,'selected_gains.mat'),'gains','best','grid','baseline');
else,s=load(fullfile(out,'selected_gains.mat'),'gains');assert(isequal(gains,s.gains),'Frozen gains changed.');end
if selectionOnly,fprintf('GAINS_SELECTED Kp=%g Ki=%g\n',gains);return;end
cases=[9000 .05 1;9000 .1 1;9000 .2 1;9000 .3 1;9500 .05 1;9500 .1 1;9500 .2 1;9500 .3 1;9500 .2 0;9500 .3 0];
if ~benchWorker,caseIndices=1:size(cases,1);end
for c=caseIndices
 for enabled=[false true]
  shape='ramps';if cases(c,3)==0,shape='steps';end
  method='PI';if enabled,method='VirtualFuelFF';end
  label=sprintf('%drpm_%02dpct_%s_%s',cases(c,1),round(100*cases(c,2)),shape,method);
  if exist(fullfile(out,[label '.mat']),'file'),s=load(fullfile(out,[label '.mat']));d=s.d;met=s.met;
  elseif c<=4
   if enabled,j=find(all(bsxfun(@eq,grid,gains),2));cached=sprintf('tune_%02d_%02d.mat',j,c);
   else,cached=sprintf('baseline_9000_%02d.mat',round(100*cases(c,2)));end
   s=load(fullfile(out,cached));d=s.d;met=s.met;
  else,[d,met]=runone(cases(c,1),cases(c,2),cases(c,3),gains,enabled);end
  if ~enabled,met.Kp=.025;met.Ki=.05;end
  savecase(d,met,label);writetable(d,fullfile(out,[label '.csv']));
  if isempty(metrics),metrics=met;else,metrics(end+1)=met;end
  summaryName='summary.csv';if benchWorker,summaryName=sprintf('summary_worker_%02d.csv',caseIndices(1));end
  writetable(struct2table(metrics),fullfile(out,summaryName));
 end
end
if benchWorker,fprintf('BENCHMARK_WORKER_COMPLETE\n');return;end
sources={'tmats_virtual_fuel_ff_setup.m','tmats_virtual_fuel_ff_sfun.m','build_tmats_virtual_fuel_ff_model.m','run_tmats_virtual_fuel_ff_study.m'};
for k=1:numel(sources),copyfile(fullfile(root,sources{k}),out);end
fprintf('VIRTUAL_FUEL_COMPLETE %s Kp=%g Ki=%g\n',out,gains);

 function [d,met]=runone(rpm,fraction,ramp,gain,enabled)
  [MWS,DOB,PTO,VF]=tmats_virtual_fuel_ff_setup(rpm,fraction,ramp*[.3 1.5 3],gain,enabled);
  assert(PTO.reference_hp>0);in=Simulink.SimulationInput(m);
  in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('VF',VF);
  in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');started=tic;
  raw=sim(in);d=table(raw.Nmech.Time(:),'VariableNames',{'time_s'});
  names={'Nmech','Wf','DOB_request','DOB_sensed','DOB_PI','DOB_command','DOB_disturbance','DOB_acceleration','DOB_SM','DOB_iterations', ...
   'PTO_hp','PTO_turbine_hp','PTO_compressor_hp','VF_command','VF_setpoint','VF_feedback','VF_error','VF_acceleration','VF_integral','VF_unsaturated','VF_outside'};
  for k=1:numel(names),v=raw.get(names{k});d.(names{k})=double(v.Data(:));end
  d.max_flow_error=max(abs(reshape(raw.DOB_flowErrors.Data,height(d),[])),[],2);
  d.valid=all(isfinite(d{:,:}),2)&d.Wf>0&d.max_flow_error<=1e-9&d.DOB_iterations<200&d.DOB_SM>0;
  assert(height(d)==10001 && abs(d.time_s(end)-150)<1e-8);
  ix=d.time_s>=60;trim=d.time_s>=55&d.time_s<=60;
  assert(max(abs(d.PTO_hp-PTO.profile(:,2)))<1e-7);
  assert(max(abs(d.DOB_request(ix)-rpm))<1e-7 && max(abs(d.DOB_disturbance))==0);
  assert(max(abs(d.VF_error-(d.VF_setpoint-d.VF_feedback)))<1e-12);
  assert(max(abs(d.DOB_command-max(DOB.fuelMin,min(DOB.fuelMax,d.VF_command))))<1e-9);
  sample=find(ix&d.valid);sample=sample(unique(round(linspace(1,numel(sample),min(50,numel(sample))))));
  gp=predict_tmats_inverse_gpr(VF.model,d.DOB_sensed(sample),d.VF_acceleration(sample));
  replay=max(abs(gp-d.VF_feedback(sample)));assert(replay<1e-6);
  gp=predict_tmats_inverse_gpr(VF.model,d.DOB_request(sample),zeros(numel(sample),1));assert(max(abs(gp-d.VF_setpoint(sample)))<1e-6);
  if enabled
   active=d.time_s>=VF.start;assert(max(abs(d.VF_unsaturated(active)-d.VF_setpoint(active)-VF.Kp*d.VF_error(active)-d.VF_integral(active)))<1e-9);
  else,assert(max(abs(d.VF_command-d.DOB_PI))<1e-9);end
  method='PI';if enabled,method='VirtualFuelFF';end
  shape='ramps';if ~ramp,shape='steps';end
  accepted=all(d.valid)&&max(abs(d.Nmech(trim)-rpm))<.1;
  met=struct('rpm',rpm,'fraction',fraction,'shape',shape,'method',method,'Kp',gain(1),'Ki',gain(2),'accepted',accepted, ...
   'rmse_rpm',NaN,'peak_rpm',NaN,'iae_rpm_s',NaN,'fuel_peak_lbm_s',NaN,'fuel_limit_percent',NaN,'minimum_margin_percent',NaN, ...
   'outside_training_percent',100*mean(d.VF_outside(ix)),'trim_error_rpm',max(abs(d.Nmech(trim)-rpm)), ...
   'gp_replay_error',replay,'wall_seconds',toc(started));
  if accepted
   e=d.Nmech(ix)-rpm;met.rmse_rpm=sqrt(mean(e.^2));met.peak_rpm=max(abs(e));met.iae_rpm_s=sum(abs(e))*DOB.Ts;
   met.fuel_peak_lbm_s=max(d.Wf(ix));met.fuel_limit_percent=100*mean(d.DOB_command(ix)<=DOB.fuelMin+1e-9|d.DOB_command(ix)>=DOB.fuelMax-1e-9);
   met.minimum_margin_percent=min(d.DOB_SM(ix));
  end
  if ~enabled,met.Kp=.025;met.Ki=.05;end
  fprintf('RUN rpm=%g load=%g %s %s Kp=%g Ki=%g valid=%d RMSE=%g wall=%.1f\n',rpm,fraction,shape,method,gain,accepted,met.rmse_rpm,met.wall_seconds);
 end
 function savecase(d,met,label)
  save(fullfile(out,[label '.mat']),'d','met','-v7.3');
 end
end

