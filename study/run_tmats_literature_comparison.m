function out=run_tmats_literature_comparison(nominalRpm)
if nargin<1,nominalRpm=9000;end
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
if ~exist(fullfile(root,'GasTurbine_Dyn_Template_GPT_DOB_PTO_ALT.mdl'),'file'),build_tmats_literature_model();end
out=fullfile(root,'results',[sprintf('literature_observers_%grpm_10pct_',nominalRpm) datestr(now,'yyyymmdd_HHMMSS_FFF')]);mkdir(out);
pointer='literature_directory.txt';if nominalRpm~=9000,pointer=sprintf('literature_%grpm_directory.txt',nominalRpm);end
f=fopen(fullfile(root,'tmp','dob',pointer),'w');fprintf(f,'%s',out);fclose(f);
m='GasTurbine_Dyn_Template_GPT_DOB_PTO_ALT';load_system(m);set_param(m,'CloseFcn','');
cleanup=onCleanup(@()close_system(m,0)); %#ok<NASGU>
names={'PI','DOB','LESO','UDE','GPIO'};methods=[1 1 2 3 4];metrics=[];
for j=1:5
 [MWS,DOB,PTO,ALT]=tmats_literature_setup(methods(j),.5,nominalRpm);if j==1,DOB.gain=0;end
 assert(PTO.reference_hp>0,'Run an unloaded PTO reference study for this speed first.');
 fprintf('LITERATURE_RUN_START %s\n',names{j});
 in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('ALT',ALT);
 in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');raw=sim(in);data=flatten(raw);
 t=data.time_s-60;ix=t>=0;e=data.Nmech(ix)-nominalRpm;
 trim=data.time_s>=55 & data.time_s<=60;
 assert(max(abs(data.Nmech(trim)-nominalRpm))<.1 && max(abs(data.DOB_acceleration(trim)))<.01,'Unsettled preparation.');
 assert(abs(mean(data.PTO_turbine_hp(trim))-PTO.reference_hp)/PTO.reference_hp<1e-6,'Cached power reference does not match the current operating point.');
 assert(height(data)==10001 && abs(data.time_s(end)-150)<1e-8);
 assert(max(abs(data.PTO_hp-PTO.profile(:,2)))<1e-7 && max(abs(data.DOB_request(ix)-nominalRpm))<1e-7 && max(abs(data.DOB_disturbance))==0);
 met=struct('method',names{j},'accepted',all(data.valid),'rmse_rpm',sqrt(mean(e.^2)), ...
  'iae_rpm_s',sum(abs(e))*.015,'peak_error_rpm',max(abs(e)), ...
  'fuel_peak',max(data.Wf(ix)),'margin_min',min(data.DOB_SM(ix)), ...
  'clip_fraction',mean(abs(DOB.gain*data.DOB_estimate(ix))>=DOB.compLimit), ...
  'first_failure_s',-1,'alternative_branch_states',numel(ALT.x0),'nominal_rpm',nominalRpm);
 bad=find(~data.valid,1);if ~isempty(bad),met.first_failure_s=t(bad);end
 if isempty(metrics),metrics=met;else,metrics(end+1)=met;end
 save(fullfile(out,[names{j} '.mat']),'raw','data','met','MWS','DOB','PTO','ALT','-v7.3');
 writetable(data,fullfile(out,[names{j} '.csv']));disp(met);
end
writetable(struct2table(metrics),fullfile(out,'metrics.csv'));
f=fopen(fullfile(out,'metrics.json'),'w');fwrite(f,jsonencode(metrics),'char');fclose(f);
f=fopen(fullfile(out,'configuration.json'),'w');fwrite(f,jsonencode(struct('b0',ALT.b0,'frequency_Hz',.5,'gain',DOB.gain,'limit',DOB.compLimit,'reference_hp',PTO.reference_hp,'load_hp',.1*PTO.reference_hp,'Ts',DOB.Ts,'nominal_rpm',nominalRpm)),'char');fclose(f);
fprintf('LITERATURE_COMPARISON_COMPLETE %s\n',out);
end
function d=flatten(raw)
d=table(raw.Nmech.Time(:),'VariableNames',{'time_s'});
names={'Nmech','Wf','DOB_request','DOB_sensed','DOB_PI','DOB_command','DOB_disturbance', ...
 'DOB_compensation','DOB_estimate','DOB_acceleration','DOB_SM','DOB_iterations','PTO_hp','PTO_turbine_hp','PTO_compressor_hp'};
for k=1:numel(names),v=raw.get(names{k});d.(names{k})=double(v.Data(:));end
d.max_flow_error=max(abs(reshape(raw.DOB_flowErrors.Data,height(d),[])),[],2);
d.valid=all(isfinite(d{:,:}),2)&d.Wf>0&d.max_flow_error<=1e-9&d.DOB_iterations<200&d.DOB_SM>0;
end
