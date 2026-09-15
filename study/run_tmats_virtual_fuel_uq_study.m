function out=run_tmats_virtual_fuel_uq_study(out,caseIndices)
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
worker=nargin>=2 && ~isempty(caseIndices);
fixed=strtrim(fileread(fullfile(root,'tmp','virtual_fuel_ff_directory.txt')));
s=load(fullfile(fixed,'selected_gains.mat'),'gains');gains=s.gains;
if nargin<1
 build_tmats_virtual_fuel_uq_model;
 out=fullfile(root,'results',['virtual_fuel_uq_' datestr(now,'yyyymmdd_HHMMSS_FFF')]);mkdir(out);
end
if ~worker,fid=fopen(fullfile(root,'tmp','virtual_fuel_uq_directory.txt'),'w');fprintf(fid,'%s',out);fclose(fid);end
if worker
 cache=fullfile(root,'tmp',sprintf('vfuq%02d',caseIndices(1)));if ~exist(cache,'dir'),mkdir(cache);end
 Simulink.fileGenControl('set','CacheFolder',cache,'CodeGenFolder',cache,'createDir',true);
end
[~,~,~,cal]=tmats_virtual_fuel_uq_setup;
sigmaReference=cal.sigmaReference;
factor=tmats_uncertainty_gain_factor([0 1 3 6 Inf]*sigmaReference,zeros(1,5),sigmaReference);
assert(abs(factor(1)-1)<1e-14 && abs(factor(3)-.1)<1e-14 && all(diff(factor)<0));
assert(tmats_uncertainty_gain_factor(0,3*sigmaReference,sigmaReference)==factor(3));
if ~worker,save(fullfile(out,'configuration.mat'),'gains','sigmaReference','fixed');end
m='GasTurbine_Dyn_Template_VirtualFuelUQ';load_system(m);cleanup=onCleanup(@()close_system(m,0));
cases=[9000 .05 1;9000 .1 1;9000 .2 1;9000 .3 1;9500 .05 1;9500 .1 1;9500 .2 1;9500 .3 1;9500 .2 0;9500 .3 0];
if ~worker,caseIndices=1:10;end
metrics=[];
for c=caseIndices
 shape='ramps';if cases(c,3)==0,shape='steps';end
 label=sprintf('%drpm_%02dpct_%s_VirtualFuelUQ',cases(c,1),round(100*cases(c,2)),shape);
 if exist(fullfile(out,[label '.mat']),'file'),s=load(fullfile(out,[label '.mat']));d=s.d;met=s.met;
 else,[d,met]=runone(cases(c,1),cases(c,2),cases(c,3),gains,true);end
 savecase(d,met,label);writetable(d,fullfile(out,[label '.csv']));
 if isempty(metrics),metrics=met;else,metrics(end+1)=met;end
 name='summary.csv';if worker,name=sprintf('summary_worker_%02d.csv',caseIndices(1));end
 writetable(struct2table(metrics),fullfile(out,name));
end
if ~worker
 sources={'tmats_virtual_fuel_uq_setup.m','tmats_virtual_fuel_uq_sfun.m','tmats_uncertainty_gain_factor.m','build_tmats_virtual_fuel_uq_model.m','run_tmats_virtual_fuel_uq_study.m'};
 for k=1:numel(sources),copyfile(fullfile(root,sources{k}),out);end
end
fprintf('UNCERTAINTY_STUDY_COMPLETE %s sigmaReference=%.12g\n',out,sigmaReference);
 function [d,met]=runone(rpm,fraction,ramp,gain,enabled)
  [MWS,DOB,PTO,VF]=tmats_virtual_fuel_uq_setup(rpm,fraction,ramp*[.3 1.5 3],gain,enabled);
  assert(PTO.reference_hp>0);in=Simulink.SimulationInput(m);
  in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('VF',VF);
  in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');started=tic;
  raw=sim(in);d=table(raw.Nmech.Time(:),'VariableNames',{'time_s'});
  names={'Nmech','Wf','DOB_request','DOB_sensed','DOB_PI','DOB_command','DOB_disturbance','DOB_acceleration','DOB_SM','DOB_iterations', ...
   'PTO_hp','PTO_turbine_hp','PTO_compressor_hp','VF_command','VF_setpoint','VF_feedback','VF_error','VF_acceleration','VF_integral','VF_unsaturated','VF_outside','VF_sdSetpoint','VF_sdFeedback','VF_gainFactor','VF_Kp','VF_Ki'};
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
   active=d.time_s>=VF.start;assert(max(abs(d.VF_unsaturated(active)-d.VF_setpoint(active)-d.VF_Kp(active).*d.VF_error(active)-d.VF_integral(active)))<1e-9);
  else,assert(max(abs(d.VF_command-d.DOB_PI))<1e-9);end
  method='PI';if enabled,method='VirtualFuelUQ';end
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
    assert(max(abs(d.VF_Kp-VF.Kp*d.VF_gainFactor))<1e-12);
  assert(max(abs(d.VF_Ki-VF.Ki*d.VF_gainFactor))<1e-12);
  [~,sdFeedback]=predict_tmats_inverse_gpr(VF.model,d.DOB_sensed(sample),d.VF_acceleration(sample));
  [~,sdSetpoint]=predict_tmats_inverse_gpr(VF.model,d.DOB_request(sample),zeros(numel(sample),1));
  met.sd_replay_error=max([abs(sdFeedback-d.VF_sdFeedback(sample));abs(sdSetpoint-d.VF_sdSetpoint(sample))]);
  assert(met.sd_replay_error<1e-6);
  met.sigma_reference=VF.sigmaReference;
  met.minimum_gain_factor=min(d.VF_gainFactor(ix));met.mean_gain_factor=mean(d.VF_gainFactor(ix));
  met.maximum_sd=max(max(d.VF_sdSetpoint(ix),d.VF_sdFeedback(ix)));
  % Replay the discrete bumpless transfer and anti-windup recurrence.
  q=find(d.time_s>VF.start & d.valid);q=q(q>1);q=q(d.valid(q-1));
  allow=(d.VF_unsaturated(q-1)<VF.fuelMax|d.VF_error(q-1)<0)&(d.VF_unsaturated(q-1)>VF.fuelMin|d.VF_error(q-1)>0);
  expected=d.VF_integral(q-1)+VF.Ts*d.VF_Ki(q-1).*d.VF_error(q-1).*allow+(d.VF_Kp(q-1)-d.VF_Kp(q)).*d.VF_error(q);
  met.integral_replay_error=max(abs(d.VF_integral(q)-expected));assert(met.integral_replay_error<1e-9);
  fprintf('RUN rpm=%g load=%g %s %s Kp=%g Ki=%g valid=%d RMSE=%g wall=%.1f\n',rpm,fraction,shape,method,gain,accepted,met.rmse_rpm,met.wall_seconds);
 end
 function savecase(d,met,label)
  save(fullfile(out,[label '.mat']),'d','met','-v7.3');
 end
end


