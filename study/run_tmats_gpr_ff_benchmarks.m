function out=run_tmats_gpr_ff_benchmarks()
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
build_tmats_gpr_ff_model;
out=fullfile(root,'results',['gpr_ff_benchmarks_' datestr(now,'yyyymmdd_HHMMSS_FFF')]);mkdir(out);
fid=fopen(fullfile(root,'tmp','gpr_ff_directory.txt'),'w');fprintf(fid,'%s',out);fclose(fid);
m='GasTurbine_Dyn_Template_GPR_FF';load_system(m);set_param(m,'CloseFcn','');
cleanup=onCleanup(@()close_system(m,0));
names={'PI','DOB','LESO','UDE','GPIO','GPR_FF'}; metrics=[];
cases=[9000 .05 1;9000 .1 1;9000 .2 1;9000 .3 1; ...
       9500 .05 1;9500 .1 1;9500 .2 1;9500 .3 1;9500 .2 0;9500 .3 0];
for c=1:size(cases,1)
 rpm=cases(c,1);fraction=cases(c,2);ramps=cases(c,3)*[.3 1.5 3];
 shape='ramps';if cases(c,3)==0,shape='steps';end
 scenario=sprintf('%drpm_%02dpct_%s',rpm,round(100*fraction),shape);
 folder=fullfile(out,scenario);mkdir(folder);
 for j=1:numel(names)
  [MWS,DOB,PTO,ALT,FF]=tmats_gpr_ff_setup(rpm,fraction,ramps,names{j});
  assert(PTO.reference_hp>0);
  fprintf('FF_BENCHMARK_START %s %s\n',scenario,names{j});started=tic;
  in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);
  in=in.setVariable('PTO',PTO);in=in.setVariable('ALT',ALT);in=in.setVariable('FF',FF);
  in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');
  raw=sim(in);d=flatten(raw); elapsed=toc(started);
  assert(height(d)==10001 && abs(d.time_s(end)-150)<1e-8);
  t=d.time_s-60;ix=t>=0;trim=d.time_s>=55&d.time_s<=60;
  assert(max(abs(d.Nmech(trim)-rpm))<.1 && max(abs(d.DOB_acceleration(trim)))<.01);
  assert(abs(mean(d.PTO_turbine_hp(trim))/PTO.reference_hp-1)<1e-6);
  assert(max(abs(d.PTO_hp-PTO.profile(:,2)))<1e-7);
  assert(max(abs(d.DOB_request(ix)-rpm))<1e-7 && max(abs(d.DOB_disturbance))==0);
  balance=(5252.113*(d.PTO_turbine_hp+d.PTO_compressor_hp)-5252.11*d.PTO_hp)./d.Nmech*60/(2*pi*MWS.Shaft.N_I);
  bad=find(~d.valid,1);prefix=true(height(d),1);if ~isempty(bad),prefix(bad:end)=false;end
  balanceError=max(abs(balance(prefix)-d.DOB_acceleration(prefix)));assert(balanceError<1e-5);
  command=max(DOB.fuelMin,min(DOB.fuelMax,d.DOB_PI-d.DOB_compensation+d.GPR_FF));
  assert(max(abs(command(prefix)-d.DOB_command(prefix)))<1e-9);
  ffCheck=0;
  if FF.enabled
   % Replay exact GP on 100 logged valid evaluation samples, including SD.
   indices=find(ix&prefix);indices=indices(unique(round(linspace(1,numel(indices),min(100,numel(indices))))));
   [fuel,sd,ci]=predict_tmats_inverse_gpr(FF.model,d.GPR_querySpeed(indices),d.GPR_referenceAcceleration(indices));
   ffCheck=max(abs(fuel-d.GPR_nominalFuel(indices)));assert(ffCheck<1e-6);
   uncertainty=table(d.time_s(indices),fuel,sd,ci(:,1),ci(:,2),'VariableNames', ...
     {'time_s','nominal_fuel_lbm_s','predictive_sd_lbm_s','lower95_lbm_s','upper95_lbm_s'});
   writetable(uncertainty,fullfile(folder,'GPR_FF_uncertainty.csv'));
   expected=max(0,min(1,(d.time_s-FF.start)/FF.enableTime)).*max(-FF.limit,min(FF.limit,d.GPR_nominalFuel-FF.trimFuel));
   assert(max(abs(expected(prefix)-d.GPR_FF(prefix)))<1e-9);
  else,assert(max(abs(d.GPR_FF))==0);end
  e=d.Nmech(ix)-rpm;accepted=all(d.valid);
  met=struct('scenario',scenario,'rpm',rpm,'fraction',fraction,'shape',shape, ...
   'method',names{j},'accepted',accepted,'rmse_rpm',NaN,'peak_rpm',NaN,'iae_rpm_s',NaN, ...
   'fuel_peak_lbm_s',NaN,'fuel_limit_percent',NaN,'compensation_clip_percent',NaN, ...
   'ff_speed_guard_percent',NaN,'minimum_margin_percent',NaN,'first_failure_s',NaN, ...
   'load_MW',fraction*PTO.reference_hp*.7456998715822702/1000, ...
   'shaft_balance_error',balanceError,'gp_replay_error',ffCheck,'wall_seconds',elapsed);
  if accepted
   met.rmse_rpm=sqrt(mean(e.^2));met.peak_rpm=max(abs(e));met.iae_rpm_s=sum(abs(e))*DOB.Ts;
   met.fuel_peak_lbm_s=max(d.Wf(ix));met.minimum_margin_percent=min(d.DOB_SM(ix));
   met.fuel_limit_percent=100*mean(d.DOB_command(ix)<=DOB.fuelMin+1e-9|d.DOB_command(ix)>=DOB.fuelMax-1e-9);
   correction=d.DOB_compensation;if FF.enabled,correction=d.GPR_FF;end
   met.compensation_clip_percent=100*mean(abs(correction(ix))>=DOB.compLimit-1e-9);
   met.ff_speed_guard_percent=100*FF.enabled*mean(d.GPR_speedGuard(ix));
  else,met.first_failure_s=t(bad);end
  % Keep physical failed-run data; do not publish full-run performance for them.
  save(fullfile(folder,[names{j} '.mat']),'d','met','MWS','DOB','PTO','ALT','FF','-v7.3');
  writetable(d,fullfile(folder,[names{j} '.csv']));
  if isempty(metrics),metrics=met;else,metrics(end+1)=met;end
  writetable(struct2table(metrics),fullfile(out,'summary.csv'));
  fid=fopen(fullfile(out,'summary.json'),'w');fwrite(fid,jsonencode(metrics),'char');fclose(fid);
  fprintf('FF_BENCHMARK_DONE %s %s accepted=%d RMSE=%g wall=%.1fs\n',scenario,names{j},accepted,met.rmse_rpm,elapsed);
 end
end
copyfile(fullfile(root,'tmats_gpr_ff_setup.m'),out);copyfile(fullfile(root,'tmats_gpr_ff_sfun.m'),out);
copyfile(fullfile(root,'build_tmats_gpr_ff_model.m'),out);copyfile(fullfile(root,'run_tmats_gpr_ff_benchmarks.m'),out);
fprintf('FF_BENCHMARKS_COMPLETE %s\n',out);
end
function d=flatten(raw)
d=table(raw.Nmech.Time(:),'VariableNames',{'time_s'});
names={'Nmech','Wf','DOB_request','DOB_sensed','DOB_PI','DOB_command','DOB_disturbance', ...
 'DOB_compensation','DOB_estimate','DOB_acceleration','DOB_SM','DOB_iterations','PTO_hp','PTO_turbine_hp','PTO_compressor_hp', ...
 'GPR_FF','GPR_nominalFuel','GPR_referenceAcceleration','GPR_querySpeed','GPR_speedGuard'};
for k=1:numel(names),v=raw.get(names{k});d.(names{k})=double(v.Data(:));end
d.max_flow_error=max(abs(reshape(raw.DOB_flowErrors.Data,height(d),[])),[],2);
d.valid=all(isfinite(d{:,:}),2)&d.Wf>0&d.max_flow_error<=1e-9&d.DOB_iterations<200&d.DOB_SM>0;
end
