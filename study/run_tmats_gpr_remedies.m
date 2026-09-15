function run_tmats_gpr_remedies(out,indices,phase)
% Candidate tuning at environment 36, then frozen transfer to environments 1:35.
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
source=strtrim(fileread('tmp/environment_directory.txt'));s=load(fullfile(source,'environment_inverse_gpr_model.mat'),'model');model=s.model;
cacheTag=sprintf('rx%02d',indices(1));if strcmp(phase,'ablation'),cacheTag='ra';end
Simulink.fileGenControl('set','CacheFolder',fullfile(root,'tmp',cacheTag),'CodeGenFolder',fullfile(root,'tmp',cacheTag),'createDir',true);
[aa,dd]=ndgrid([0 2500 5000 7500 10000],[0 -10 10 20 -20 30 -30]);envs=[aa(:) dd(:);4000 5];
C=tmats_gpr_remedy_candidates();
if ~strcmp(phase,'tune'),ss=load(fullfile(out,'selected_remedies.mat'),'selected');selected=ss.selected;end
[MWS,DOB,PTO,VF]=tmats_virtual_fuel_ff_setup(9500,.1,[0 0 0],[2 30],true);[MWS,ENV]=tmats_environment_config(MWS,4000,5);
m='GasTurbine_Dyn_Template_VirtualFuelFF';load_system(m);set_param(m,'CloseFcn','');cleanup=onCleanup(@()close_system(m,0));
tmats_environment_patch(m);tmats_environment_vf_patch(m);set_param([m '/Virtual fuel PI'],'FunctionName','tmats_gpr_remedy_sfun');
if strcmp(phase,'transfer'),tmats_remedy_stop_invalid(m);end
extra={'VR_integrator_error','VR_proportional_term','VR_speed_slope','VR_accel_slope','VR_fallback'};
for k=1:5
 add_block('simulink/Sinks/To Workspace',[m '/' extra{k}],'VariableName',extra{k},'SaveFormat','Timeseries','MaxDataPoints','inf','Position',[1300 1150+40*k 1440 1170+40*k]);
 add_line(m,['Virtual fuel PI/' num2str(k+8)],[extra{k} '/1'],'autorouting','on');
end
metrics=[];
for job=indices
 if strcmp(phase,'tune'),c=36;candidate=job;elseif strcmp(phase,'ablation'),c=36;candidate=selected(3);else,c=ceil(job/3);candidate=selected(mod(job-1,3)+1);end
 row=C(candidate,:);file=fullfile(out,sprintf('%s_e%02d_c%02d.mat',phase,c,candidate));
 if exist(file,'file'),z=load(file,'met');met=z.met;
 else
  fprintf('REMEDY_START %s environment=%d candidate=%d mode=%d\n',phase,c,candidate,row(1));started=tic;
  tr=load(fullfile(source,sprintf('trim_%02d.mat',c)),'reference_hp');
  [MWS,DOB,PTO]=tmats_pto_setup(tr.reference_hp,.1,9500,[0 0 0]);DOB.gain=0;
  [MWS,ENV]=tmats_environment_config(MWS,envs(c,1),envs(c,2));
  vf=VF;vf.model=rmfield(model,{'L','Z','trainingRows'});vf.scaledTraining=bsxfun(@rdivide,model.Z,model.lengthScale');
  vf.start=45;vf.mode=row(1);vf.Kp=row(2);vf.Ki=row(3);vf.Kd=row(4);vf.accelTau=row(5);
  vf.accelWeight=1;if numel(row)>=6,vf.accelWeight=row(6);end
  vf.forceFallback=strcmp(phase,'ablation');
  in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('ENV',ENV);in=in.setVariable('VF',vf);
  in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');raw=sim(in);d=tmats_environment_data(raw);
  for k=1:5,z=raw.get(extra{k});d.(extra{k})=double(z.Data(:));end
  assert(height(d)<=10001 && max(abs(d.PTO_hp-PTO.profile(1:height(d),2)))<1e-7);
  ix=d.time_s>=45&d.valid;
  assert(max(abs(d.VF_unsaturated(ix)-d.VF_setpoint(ix)-d.VR_proportional_term(ix)-d.VF_integral(ix)))<1e-9);
  met=tmats_fixed_comparison_metrics(d,9500,[0 0 0],DOB);met.phase=phase;met.environment=c;met.candidate=candidate;
  met.mode=row(1);met.Kp=row(2);met.Ki=row(3);met.Kd=row(4);met.accelTau=row(5);met.altitude_m=envs(c,1);met.isa_delta_C=envs(c,2);
  ix=d.time_s>=60;met.fallback_percent=100*mean(d.VR_fallback(ix));met.compressor_Nc_outside_percent=100*mean(d.compressor_Nc_outside(ix));met.gp_outside_percent=100*mean(d.VF_outside(ix));
  met.accelWeight=vf.accelWeight;met.wall_seconds=toc(started);save(file,'d','met','vf','ENV','PTO','-v7.3');writetable(d,strrep(file,'.mat','.csv'));
  fprintf('REMEDY_DONE candidate=%d environment=%d valid=%d RMSE=%g ringing=%g wall=%.1f\n',candidate,c,met.accepted,met.rmse_rpm,met.ringing_excess_TV_lbm_s,met.wall_seconds);
 end
 if ~isfield(met,'accelWeight'),met.accelWeight=1;end
 met=orderfields(met);
 if isempty(metrics),metrics=met;else,metrics(end+1)=met;end
 writetable(struct2table(metrics),fullfile(out,sprintf('%s_worker_%02d.csv',phase,indices(1))));
end
end
