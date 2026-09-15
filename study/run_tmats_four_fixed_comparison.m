function out=run_tmats_four_fixed_comparison(out,indices)
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
worker=nargin>=2 && ~isempty(indices);
tuning=strtrim(fileread('tmp/ff_lowgain_directory.txt'));s=load(fullfile(tuning,'selected_gains.mat'),'gains');gains=s.gains;
if nargin<1,out=fullfile(root,'results',['four_fixed_' datestr(now,'yyyymmdd_HHMMSS_FFF')]);mkdir(out);end
if ~worker,fid=fopen('tmp/four_fixed_directory.txt','w');fprintf(fid,'%s',out);fclose(fid);end
if worker
 cache=fullfile(root,'tmp',sprintf('fourfixed%02d',indices(1)));if ~exist(cache,'dir'),mkdir(cache);end
 Simulink.fileGenControl('set','CacheFolder',cache,'CodeGenFolder',cache,'createDir',true);
end
models={'GasTurbine_Dyn_Template_GPR_FF','GasTurbine_Dyn_Template_VirtualFuel','GasTurbine_Dyn_Template_VirtualFuelFF'};
cleanup=onCleanup(@()closemodels(models));
methods={'BasePI','BasePI_GPRFF','InvGPR_PI','InvGPR_PI_GPRFF'};
cases=[9000 .05 1;9000 .1 1;9000 .2 1;9000 .3 1;9500 .05 1;9500 .1 1;9500 .2 1;9500 .3 1;9500 .2 0;9500 .3 0;9500 .05 0];
if ~worker,indices=1:44;end
metrics=[];
for job=indices
 c=ceil(job/4);j=mod(job-1,4)+1;rpm=cases(c,1);fraction=cases(c,2);ramps=cases(c,3)*[.3 1.5 3];
 shape='ramps';if cases(c,3)==0,shape='steps';end
 tag=sprintf('%drpm_%02dpct_%s_%s',rpm,round(100*fraction),shape,methods{j});file=fullfile(out,[tag '.mat']);
 if exist(file,'file'),z=load(file);d=z.d;met=z.met;
 else
  fprintf('START %s\n',tag);started=tic;
  if j<=2
   names={'PI','GPR_FF'};[MWS,DOB,PTO,ALT,FF]=tmats_gpr_ff_setup(rpm,fraction,ramps,names{j});m=models{1};
   load_system(m);in=Simulink.SimulationInput(m);in=in.setVariable('ALT',ALT);in=in.setVariable('FF',FF);kp=.025;ki=.05;
  else
   if j==3,[MWS,DOB,PTO,VF]=tmats_virtual_fuel_setup(rpm,fraction,ramps,gains,true);m=models{2};
   else,[MWS,DOB,PTO,VF]=tmats_virtual_fuel_ff_setup(rpm,fraction,ramps,gains,true);m=models{3};end
   load_system(m);in=Simulink.SimulationInput(m);in=in.setVariable('VF',VF);kp=gains(1);ki=gains(2);
  end
  in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);
  in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');raw=sim(in);
  d=table(raw.Nmech.Time(:),'VariableNames',{'time_s'});
  fields={'Nmech','Wf','DOB_request','DOB_sensed','DOB_PI','DOB_command','DOB_disturbance','DOB_acceleration','DOB_SM','DOB_iterations','PTO_hp','PTO_turbine_hp','PTO_compressor_hp'};
  if j<=2,fields=[fields {'DOB_compensation','GPR_FF','GPR_nominalFuel','GPR_referenceAcceleration','GPR_querySpeed','GPR_speedGuard'}];
  else,fields=[fields {'VF_command','VF_setpoint','VF_feedback','VF_error','VF_acceleration','VF_integral','VF_unsaturated','VF_outside'}];end
  for k=1:numel(fields),v=raw.get(fields{k});d.(fields{k})=double(v.Data(:));end
  d.max_flow_error=max(abs(reshape(raw.DOB_flowErrors.Data,height(d),[])),[],2);
  d.valid=all(isfinite(d{:,:}),2)&d.Wf>0&d.max_flow_error<=1e-9&d.DOB_iterations<200&d.DOB_SM>0;
  assert(height(d)==10001 && abs(d.time_s(end)-150)<1e-8);
  assert(PTO.reference_hp>0 && max(abs(d.PTO_hp-PTO.profile(:,2)))<1e-7);
  assert(max(abs(d.DOB_request(d.time_s>=60)-rpm))<1e-7 && max(abs(d.DOB_disturbance))==0);
  q=find(d.valid&d.time_s>=60);q=q(unique(round(linspace(1,numel(q),min(50,numel(q))))));gpReplay=0;
  if j<=2
   expected=max(DOB.fuelMin,min(DOB.fuelMax,d.DOB_PI-d.DOB_compensation+d.GPR_FF));assert(max(abs(expected(d.valid)-d.DOB_command(d.valid)))<1e-9);
   if j==1,assert(max(abs(d.GPR_FF))==0);
   else
    gp=predict_tmats_inverse_gpr(FF.model,d.GPR_querySpeed(q),d.GPR_referenceAcceleration(q));gpReplay=max(abs(gp-d.GPR_nominalFuel(q)));assert(gpReplay<1e-6);
    correction=max(0,min(1,(d.time_s-FF.start)/FF.enableTime)).*max(-FF.limit,min(FF.limit,d.GPR_nominalFuel-FF.trimFuel));
    assert(max(abs(correction(d.valid)-d.GPR_FF(d.valid)))<1e-9);
   end
  else
   gp=predict_tmats_inverse_gpr(VF.model,d.DOB_sensed(q),d.VF_acceleration(q));gpReplay=max(abs(gp-d.VF_feedback(q)));assert(gpReplay<1e-6);
   assert(max(abs(d.VF_error-(d.VF_setpoint-d.VF_feedback)))<1e-12);
   active=d.time_s>=30 & d.valid;ff=zeros(height(d),1);if j==4,ff=d.VF_setpoint;end
   assert(max(abs(d.VF_unsaturated(active)-ff(active)-kp*d.VF_error(active)-d.VF_integral(active)))<1e-9);
   expected=max(DOB.fuelMin,min(DOB.fuelMax,d.VF_command));assert(max(abs(expected(d.valid)-d.DOB_command(d.valid)))<1e-9);
  end
  met=tmats_fixed_comparison_metrics(d,rpm,ramps,DOB);
  met.case_index=c;met.method=methods{j};met.rpm=rpm;met.fraction=fraction;met.shape=shape;met.Kp=kp;met.Ki=ki;met.gp_replay_error=gpReplay;met.wall_seconds=toc(started);
  save(file,'d','met','-v7.3');writetable(d,fullfile(out,[tag '.csv']));
  fprintf('DONE %s valid=%d RMSE=%g ring=%g wall=%.1f\n',tag,met.accepted,met.rmse_rpm,met.ringing_excess_TV_lbm_s,met.wall_seconds);
 end
 if isempty(metrics),metrics=met;else,metrics(end+1)=met;end
 name='summary.csv';if worker,name=sprintf('summary_worker_%02d.csv',indices(1));end
 writetable(struct2table(metrics),fullfile(out,name));
end
if ~worker,save(fullfile(out,'configuration.mat'),'gains','tuning','cases','methods');end
fprintf('FOUR_FIXED_COMPLETE %s\n',out);
end
function closemodels(models)
for k=1:numel(models),if bdIsLoaded(models{k}),close_system(models{k},0);end;end
end
