function outDir=run_tmats_dob_study(stage)
% Nonlinear T-MATS closed-loop comparison. Every simulation is saved, including failures.
if nargin<1,stage='refined';end
root=fileparts(mfilename('fullpath'));[MWS,DOB0]=tmats_dob_setup();
m='GasTurbine_Dyn_Template_GPT_DOB'; load_system(fullfile(root,[m '.mdl']));set_param(m,'CloseFcn','');
cleanup=onCleanup(@()close_system(m,0)); %#ok<NASGU>
outDir=fullfile(root,'results',['dob_' stage '_' datestr(now,'yyyymmdd_HHMMSS_FFF')]);mkdir(outDir);
fid=fopen(fullfile(root,'tmp','dob','latest_directory.txt'),'w');fprintf(fid,'%s',outDir);fclose(fid);
if strcmp(stage,'pilot')
 gains=[0 .25 .5 1]; modes=[2 2 2 2]; fcs=[.5 .5 .5 .5]; dur=30;
else
 gains=[0 DOB0.gain 0 DOB0.gain 0 DOB0.gain DOB0.gain 0 DOB0.gain]; modes=[2 2 2 2 2 2 1 2 2];fcs=ones(size(gains))*.5;dur=60;
end
metrics=struct([]);
for j=1:numel(gains)
 DOB=DOB0; DOB.gain=gains(j);DOB.mode=modes(j);DOB.fc=fcs(j);
 t=(0:round((30+dur)/DOB.Ts))'*DOB.Ts; rel=t-30;
 request=interp1([0 5 10 30],[10000 10000 9000 9000],min(t,30));
 bits=logical([0 1 0 1 1 0 1]);
 if ~strcmp(stage,'pilot'),bits=logical([0 1 1 0 1 0 1]);end
 for k=1:254,bits(k+7)=xor(bits(k),bits(k+3));end
 ix=t>=30;idx=floor(max(rel(ix),0)/10.005)+1;request(ix)=9000+1000*double(bits(idx))';
 disturbance=zeros(size(t));
 disturbance(rel>=7.5 & rel<15)=.08;
 disturbance(rel>=20 & rel<27.5)=-.08;
 disturbance(rel>=35 & rel<50)=.06*sin(2*pi*.2*(rel(rel>=35 & rel<50)-35));
 kind='governed_prbs_disturbed';
 if ~strcmp(stage,'pilot') && ismember(j,[3 4])
  disturbance(:)=0;kind='governed_prbs_nominal';
 elseif ~strcmp(stage,'pilot') && ismember(j,[5 6])
  request=interp1([0 5 10 30],[10000 10000 9500 9500],min(t,30));
  idx=floor(max(rel(ix),0)/.51)+1;request(ix)=9495+10*double(bits(idx))';DOB.rate=1e6;
  kind='strict_small_prbs_disturbed';
 elseif ~strcmp(stage,'pilot') && ismember(j,[8 9])
  t=(0:2200)'*DOB.Ts;rel=t-30;ix=t>=30;
  request=interp1([0 5 10 30],[10000 10000 9000 9000],min(t,30));
  idx=floor(max(rel(ix),0)/.51)+1;request(ix)=9000+1000*double(bits(idx))';
  disturbance=zeros(size(t));DOB.rate=1e6;kind='strict_full_prbs_diagnostic';
 end
 DOB.request=[t request];DOB.disturbance=[t disturbance];MWS.in.SimTime=t(end);
 DOB.request(2:end,1)=DOB.request(2:end,1)-DOB.Ts/4;
 DOB.disturbance(2:end,1)=DOB.disturbance(2:end,1)-DOB.Ts/4;
 input=Simulink.SimulationInput(m);input=input.setVariable('MWS',MWS);input=input.setVariable('DOB',DOB);
 input=input.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');
 fprintf('DOB_RUN_START %d gain %.3g mode %d %s\n',j,DOB.gain,DOB.mode,kind);started=tic;
 raw=sim(input);elapsed=toc(started);
 rawNames={'Nmech','Wf','DOB_rawRequest','DOB_request','DOB_sensed','DOB_PI','DOB_command', ...
  'DOB_disturbance','DOB_compensation','DOB_estimate','DOB_acceleration','DOB_SM','DOB_iterations'};
 data=table(raw.Nmech.Time(:),'VariableNames',{'time_s'});
 for k=1:numel(rawNames),v=raw.get(rawNames{k});data.(rawNames{k})=double(v.Data(:));end
 assert(max(abs(data.DOB_rawRequest-request))<1e-7,'PRBS source timing mismatch.');
 assert(max(abs(data.DOB_disturbance-disturbance))<1e-7,'Disturbance source timing mismatch.');
 data.max_flow_error=max(abs(reshape(raw.DOB_flowErrors.Data,numel(data.time_s),[])),[],2);
 data.valid=all(isfinite(data{:,:}),2)&data.Wf>0&data.max_flow_error<=MWS.Solve.C_Lim ...
  &data.DOB_iterations<MWS.Solve.Max_Iter & data.DOB_SM>0;
 ix=data.time_s>=30-1e-8; e=data.DOB_request(ix)-data.Nmech(ix);er=data.DOB_rawRequest(ix)-data.Nmech(ix);
 met=struct('case_index',j,'kind',kind,'gain',DOB.gain,'mode',DOB.mode,'fc_Hz',DOB.fc, ...
 'accepted',all(data.valid),'wall_seconds',elapsed,'rmse_rpm',sqrt(mean(e.^2)), ...
 'raw_request_rmse_rpm',sqrt(mean(er.^2)),'iae_rpm_s',sum(abs(e))*DOB.Ts, ...
 'peak_error_rpm',max(abs(e)),'fuel_min',min(data.Wf),'fuel_max',max(data.Wf), ...
 'compensation_peak',max(abs(data.DOB_compensation(ix))),'max_flow_error',max(data.max_flow_error), ...
 'max_iterations',max(data.DOB_iterations),'min_SM',min(data.DOB_SM),'first_failure_s',-1, ...
 'fuel_command_total_variation',sum(abs(diff(data.DOB_command(ix)))), ...
 'fuel_limit_fraction',mean(data.DOB_command(ix)<=DOB.fuelMin+1e-9 | data.DOB_command(ix)>=DOB.fuelMax-1e-9), ...
 'comp_limit_fraction',mean(abs(DOB.gain*data.DOB_estimate(ix))>=DOB.compLimit));
 bad=find(~data.valid,1);if ~isempty(bad),met.first_failure_s=data.time_s(bad)-30;end
 if isempty(metrics),metrics=met;else,metrics(end+1)=met;end
 save(fullfile(outDir,sprintf('case_%02d.mat',j)),'raw','data','DOB','MWS','met','-v7.3');
 writetable(data,fullfile(outDir,sprintf('case_%02d.csv',j)));
 fid=fopen(fullfile(outDir,'metrics.json'),'w');fwrite(fid,jsonencode(metrics),'char');fclose(fid);
 disp(met);
end
writetable(struct2table(metrics),fullfile(outDir,'metrics.csv'));
fprintf('DOB_STUDY_SUCCESS %s\n',outDir);
end
