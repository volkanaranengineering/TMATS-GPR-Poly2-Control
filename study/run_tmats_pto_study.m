function out=run_tmats_pto_study(fraction,nominalRpm,rampSeconds)
if nargin<1,fraction=.1;end
if nargin<2,nominalRpm=10000;end
if nargin<3,rampSeconds=[0 0 0];end
root=fileparts(mfilename('fullpath'));[MWS,DOB,PTO]=tmats_pto_setup(0,fraction,nominalRpm,rampSeconds);
m='GasTurbine_Dyn_Template_GPT_DOB_PTO';load_system(m);set_param(m,'CloseFcn','');
cleanup=onCleanup(@()close_system(m,0)); %#ok<NASGU>
out=fullfile(root,'results',sprintf('dob_pto_%grpm_%02dpct_%s',nominalRpm,round(100*fraction),datestr(now,'yyyymmdd_HHMMSS_FFF')));mkdir(out);
fid=fopen(fullfile(root,'tmp','dob','pto_directory.txt'),'w');fprintf(fid,'%s',out);fclose(fid);
% Measure the reference before freezing an identical physical load for both loops.
MWS.in.SimTime=60;DOB.gain=0;raw=simulate(m,MWS,DOB,PTO);trim=flatten(raw);
assert(all(trim.valid),'Unloaded preparation failed numerical validation.');
ix=trim.time_s>=55;
assert(max(abs(trim.Nmech(ix)-nominalRpm))<.1 && max(abs(trim.DOB_acceleration(ix)))<.01, ...
 'The requested operating point did not settle.');
ref=struct('turbine_power_hp',mean(trim.PTO_turbine_hp(ix)), ...
 'compressor_load_hp',-mean(trim.PTO_compressor_hp(ix)), ...
 'speed_rpm',mean(trim.Nmech(ix)),'fuel_lbm_s',mean(trim.Wf(ix)), ...
 'window_absolute_s',[55 60],'power_fraction',fraction,'nominal_speed_rpm',nominalRpm);
ref.extraction_hp=fraction*ref.turbine_power_hp;ref.extraction_kW=ref.extraction_hp*.7456998715822702;
ref.net_unloaded_power_hp=ref.turbine_power_hp-ref.compressor_load_hp;
ref.ramp_s=rampSeconds;
save(fullfile(out,'trim.mat'),'raw','trim','MWS','DOB','PTO','ref','-v7.3');
writetable(trim,fullfile(out,'trim.csv'));
writejson(fullfile(out,'reference.json'),ref);
cacheName='pto_reference.json';if nominalRpm~=10000,cacheName=sprintf('pto_reference_%grpm.json',nominalRpm);end
writejson(fullfile(root,'tmp','dob',cacheName),ref);
fprintf('PTO_REFERENCE %.9f hp; load %.9f hp / %.9f kW\n',ref.turbine_power_hp,ref.extraction_hp,ref.extraction_kW);
[MWS,DOB0,PTO]=tmats_pto_setup(ref.turbine_power_hp,fraction,nominalRpm,rampSeconds);metrics=[];events=[];
for j=1:2
 DOB=DOB0;if j==1,DOB.gain=0;end
 fprintf('PTO_RUN_START %d gain %.3f\n',j,DOB.gain);
 started=tic;raw=simulate(m,MWS,DOB,PTO);elapsed=toc(started);data=flatten(raw);
 t=data.time_s-PTO.preparation_s;ix=t>=-1e-8;e=nominalRpm-data.Nmech(ix);
 expect=PTO.profile(:,2);
 assert(max(abs(expect-data.PTO_hp))<1e-7,'Power source timing mismatch.');
 assert(max(abs(data.DOB_request(ix)-nominalRpm))<1e-7 && max(abs(data.DOB_disturbance))==0);
 assert(height(data)==10001 && abs(data.time_s(end)-150)<1e-8,'Incomplete comparison trajectory.');
 % Verify the sign, units and location of the physical load via torque balance.
 torque=(5252.113*(data.PTO_turbine_hp+data.PTO_compressor_hp)-5252.11*data.PTO_hp)./data.Nmech;
 balance=torque*60/(2*pi*MWS.Shaft.N_I);
 balanceError=max(abs(balance-data.DOB_acceleration));
 % Preserve failed trajectories for diagnosis; do not stop before saving them.
 met=struct('controller',j,'gain',DOB.gain,'accepted',all(data.valid),'rmse_rpm',sqrt(mean(e.^2)), ...
 'iae_rpm_s',sum(abs(e))*PTO.Ts,'maximum_droop_rpm',max(e),'maximum_overspeed_rpm',max(-e), ...
 'fuel_min_lbm_s',min(data.Wf(ix)),'fuel_max_lbm_s',max(data.Wf(ix)), ...
 'fuel_mass_lbm',trapz(data.time_s(ix),data.Wf(ix)), ...
 'fuel_limit_fraction',mean(data.DOB_command(ix)<=DOB.fuelMin+1e-9 | data.DOB_command(ix)>=DOB.fuelMax-1e-9), ...
 'comp_limit_fraction',mean(abs(DOB.gain*data.DOB_estimate(ix))>=DOB.compLimit), ...
 'compensation_peak_lbm_s',max(abs(data.DOB_compensation(ix))), ...
 'max_flow_error',max(data.max_flow_error),'max_iterations',max(data.DOB_iterations), ...
 'minimum_SM_percent',min(data.DOB_SM),'torque_balance_max_error_rpm_s',balanceError, ...
 'first_failure_s',-1,'wall_seconds',elapsed,'power_fraction',fraction,'nominal_speed_rpm',nominalRpm, ...
 'shaft_balance_verified',isfinite(balanceError)&&balanceError<1e-5);
 bad=find(~data.valid,1);if ~isempty(bad),met.first_failure_s=t(bad);end
 if isempty(metrics),metrics=met;else,metrics(end+1)=met;end
 edgeTimes=sort([PTO.on_s PTO.off_s]);
 for k=1:numel(edgeTimes)
  at=edgeTimes(k);until=PTO.duration_s;if k<numel(edgeTimes),until=edgeTimes(k+1);end
  win=t>=at-1e-9 & t<until-1e-9;ee=nominalRpm-data.Nmech(win);tt=t(win)-at;
  lastOutside=find(abs(ee)>1,1,'last');settle=0;
  if ~isempty(lastOutside)
   settle=NaN;if lastOutside<numel(tt) && tt(end)-tt(lastOutside+1)>=.5,settle=tt(lastOutside+1);end
  end
  ev=struct('controller',j,'edge_s',at,'load_applied',any(abs(PTO.on_s-at)<1e-7), ...
   'max_absolute_error_rpm',max(abs(ee)),'settling_to_1rpm_s',settle, ...
  'tail_mean_error_rpm',mean(ee(tt>=tt(end)-1)), ...
  'trajectory_valid_through_event',all(data.valid(t<until-1e-9)));
  if isempty(events),events=ev;else,events(end+1)=ev;end
 end
 save(fullfile(out,sprintf('case_%02d.mat',j)),'raw','data','met','MWS','DOB','PTO','ref','-v7.3');
 writetable(data,fullfile(out,sprintf('case_%02d.csv',j)));writejson(fullfile(out,'metrics.json'),metrics);
 disp(met);
end
writetable(struct2table(metrics),fullfile(out,'metrics.csv'));writetable(struct2table(events),fullfile(out,'events.csv'));
fprintf('PTO_STUDY_SUCCESS %s\n',out);
end
function raw=simulate(m,MWS,DOB,PTO)
in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);
in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');raw=sim(in);
end
function d=flatten(raw)
d=table(raw.Nmech.Time(:),'VariableNames',{'time_s'});
names={'Nmech','Wf','DOB_request','DOB_sensed','DOB_PI','DOB_command','DOB_disturbance', ...
 'DOB_compensation','DOB_estimate','DOB_acceleration','DOB_SM','DOB_iterations','PTO_hp','PTO_turbine_hp','PTO_compressor_hp'};
for k=1:numel(names),v=raw.get(names{k});d.(names{k})=double(v.Data(:));end
d.max_flow_error=max(abs(reshape(raw.DOB_flowErrors.Data,height(d),[])),[],2);
d.valid=all(isfinite(d{:,:}),2)&d.Wf>0&d.max_flow_error<=1e-9&d.DOB_iterations<200&d.DOB_SM>0;
end
function writejson(path,v)
f=fopen(path,'w');assert(f>=0);fwrite(f,jsonencode(v),'char');fclose(f);
end
