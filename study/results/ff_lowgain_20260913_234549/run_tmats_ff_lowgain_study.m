function out=run_tmats_ff_lowgain_study(out,indices)
% Fixed FF + virtual-fuel PI retuning for 9500 rpm, 5 percent step loads.
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
worker=nargin>=2 && ~isempty(indices);
if nargin<1
 out=fullfile(root,'results',['ff_lowgain_' datestr(now,'yyyymmdd_HHMMSS_FFF')]);mkdir(out);
end
if ~worker,fid=fopen(fullfile(root,'tmp','ff_lowgain_directory.txt'),'w');fprintf(fid,'%s',out);fclose(fid);end
if worker
 cache=fullfile(root,'tmp',sprintf('fflow%02d',indices(1)));if ~exist(cache,'dir'),mkdir(cache);end
 Simulink.fileGenControl('set','CacheFolder',cache,'CodeGenFolder',cache,'createDir',true);
end
m='GasTurbine_Dyn_Template_VirtualFuelFF';load_system(m);cleanup=onCleanup(@()close_system(m,0));
grid=[3 60;3 40;2.5 40;2 40;2 30;1.5 30;1.5 20;1 20;1 10;.5 10;.5 5;.25 5];
if ~worker,indices=1:size(grid,1);end
metrics=[];
for j=indices
 label=sprintf('candidate_%02d',j);
 if exist(fullfile(out,[label '.mat']),'file'),z=load(fullfile(out,[label '.mat']));d=z.d;met=z.met;
 else,[d,met]=runone(9500,.05,0,grid(j,:),true);end
 met.candidate=j;
 savecase(d,met,label);writetable(d,fullfile(out,[label '.csv']));
 if isempty(metrics),metrics=met;else,metrics(end+1)=met;end
 name='tuning.csv';if worker,name=sprintf('tuning_worker_%02d.csv',indices(1));end
 writetable(struct2table(metrics),fullfile(out,name));
end
if ~worker
 T=struct2table(metrics);assert(isequal(T.candidate,(1:size(grid,1))'));
 assert(T.accepted(1),'Baseline must be valid to define relative ringing.');
 baselineRinging=T.ringing_excess_TV_lbm_s(1);targetRinging=.1*baselineRinging;
 eligible=T.accepted & T.ringing_excess_TV_lbm_s<=targetRinging;
 assert(any(eligible),'No valid candidate meets 90 percent ringing reduction target; extend grid.');
 score=T.rmse_rpm;score(~eligible)=Inf;[~,selected]=min(score);gains=grid(selected,:);
 save(fullfile(out,'selected_gains.mat'),'gains','selected','grid','baselineRinging','targetRinging');
 sources={'run_tmats_ff_lowgain_study.m','tmats_virtual_fuel_ff_setup.m','tmats_virtual_fuel_ff_sfun.m','GasTurbine_Dyn_Template_VirtualFuelFF.mdl'};
 for k=1:numel(sources),copyfile(fullfile(root,sources{k}),out);end
 fprintf('SELECTED_FIXED_GAINS Kp=%g Ki=%g ringing=%g RMSE=%g\n',gains,T.ringing_excess_TV_lbm_s(selected),T.rmse_rpm(selected));
end
fprintf('LOWGAIN_STUDY_COMPLETE %s\n',out);
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
  met.ringing_excess_TV_lbm_s=NaN;met.max_2s_fuel_range_lbm_s=NaN;met.max_fuel_slew_lbm_s2=NaN;met.settling_to_point1_rpm_s=NaN;
  if accepted
   starts=[70.005 75 90 100.005 120 135];ends=[75 90 100.005 120 135 150];
   ringing=0;fuelRange=0;fuelSlew=0;settling=0;
   for event=1:6
    q=d.time_s>=starts(event)-1e-8 & d.time_s<=starts(event)+2+1e-8;f=d.Wf(q);
    ringing=ringing+max(0,sum(abs(diff(f)))-abs(f(end)-f(1)));
    fuelRange=max(fuelRange,max(f)-min(f));fuelSlew=max(fuelSlew,max(abs(diff(f)))/DOB.Ts);
    q=find(d.time_s>=starts(event)-1e-8 & d.time_s<ends(event)-1e-8);bad=find(abs(d.Nmech(q)-rpm)>.1,1,'last');
    recovery=0;if ~isempty(bad),if bad==numel(q),recovery=Inf;else,recovery=d.time_s(q(bad+1))-starts(event);end;end
    settling=max(settling,recovery);
   end
   met.ringing_excess_TV_lbm_s=ringing;met.max_2s_fuel_range_lbm_s=fuelRange;met.max_fuel_slew_lbm_s2=fuelSlew;met.settling_to_point1_rpm_s=settling;
  end
  fprintf('RUN rpm=%g load=%g %s %s Kp=%g Ki=%g valid=%d RMSE=%g wall=%.1f\n',rpm,fraction,shape,method,gain,accepted,met.rmse_rpm,met.wall_seconds);
 end
 function savecase(d,met,label)
  save(fullfile(out,[label '.mat']),'d','met','-v7.3');
 end
end


