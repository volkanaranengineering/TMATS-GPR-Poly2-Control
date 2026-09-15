function checks=analyze_tmats_dob(outDir)
% Compare paired nonlinear responses, verify the block realization, and plot.
root=fileparts(mfilename('fullpath'));
if nargin<1,outDir=strtrim(fileread(fullfile(root,'tmp','dob','latest_directory.txt')));end
[MWS,DOB]=tmats_dob_setup(); %#ok<ASGLU>
metrics=jsondecode(fileread(fullfile(outDir,'metrics.json')));
data=cell(1,numel(metrics));for j=1:numel(metrics),data{j}=readtable(fullfile(outDir,sprintf('case_%02d.csv',j)));end
checks=struct();
q=exp(-1i*linspace(0,pi,1001));
ev=@(c) polyval(fliplr(c(:)'),q);
p=exp(-DOB.Ts/.05);
Pn=ev(DOB.Bspeed)./ev(DOB.A).*((1-p)*q./(1-p*q));
Qi=ev(DOB.Qnum)./ev(DOB.Qden);
impl=ev(DOB.InvNum)./ev(DOB.InvDen);
checks.inverse_identity_max_abs_error=max(abs(impl-Qi./Pn));
assert(checks.inverse_identity_max_abs_error<1e-6,'Q/Pn realization failed.');
checks.raw_acceleration_zero_radius=max(abs(roots(DOB.B(2:end))));
checks.corrected_speed_zero_radius=max(abs(roots(DOB.Bspeed(2:end))));
checks.inverse_pole_radius=max(abs(roots(DOB.InvDen)));
checks.nominal_speed_dc_gain=sum(DOB.Bspeed)/sum(DOB.A);
checks.B10_correction=DOB.Beq(end)-DOB.B(end);
m='GasTurbine_Dyn_Template_GPT_DOB';load_system(fullfile(root,[m '.mdl']));set_param(m,'CloseFcn','');
s=[m '/Data driven DOB'];bb=find_system(s,'LookUnderMasks','all','FollowLinks','on','Type','Block');
types=get_param(bb,'BlockType');
checks.observer_block_count=numel(bb)-1;
checks.observer_sfunction_count=sum(strcmp(types,'S-Function'));
checks.observer_matlab_function_count=numel(find_system(s,'LookUnderMasks','all','SFBlockType','MATLAB Function'));
assert(checks.observer_sfunction_count==0 && checks.observer_matlab_function_count==0);
checks.PI_Kp=eval(get_param([m '/Simple PI controller'],'Kp_M'));
checks.PI_Ki=eval(get_param([m '/Simple PI controller'],'Ki_M'));
assert(abs(checks.PI_Kp-.025)<eps && abs(checks.PI_Ki-.05)<eps);
close_system(m,0);
assert(isequal(data{1}.DOB_request,data{2}.DOB_request));
assert(isequal(data{1}.DOB_disturbance,data{2}.DOB_disturbance));
assert(isequal(data{1}.DOB_request,data{3}.DOB_request));
ix=data{1}.time_s>=30-1e-8;
if all([metrics(1:4).accepted])
 effectPI=data{1}.Nmech(ix)-data{3}.Nmech(ix);
 effectDOB=data{2}.Nmech(ix)-data{4}.Nmech(ix);
 checks.disturbance_induced_speed_rmse_PI=sqrt(mean(effectPI.^2));
 checks.disturbance_induced_speed_rmse_DOB=sqrt(mean(effectDOB.^2));
 checks.disturbance_rejection_rmse_improvement_percent=100*(1-norm(effectDOB)/norm(effectPI));
 checks.disturbance_induced_speed_peak_PI=max(abs(effectPI));
 checks.disturbance_induced_speed_peak_DOB=max(abs(effectDOB));
else
 checks.paired_rejection_note='One nominal or disturbed trajectory failed; paired rejection metric is not accepted.';
end
checks.governed_tracking_rmse_improvement_percent=100*(1-metrics(2).rmse_rpm/metrics(1).rmse_rpm);
checks.small_prbs_tracking_rmse_improvement_percent=100*(1-metrics(6).rmse_rpm/metrics(5).rmse_rpm);
fid=fopen(fullfile(outDir,'verification.json'),'w');fwrite(fid,jsonencode(checks),'char');fclose(fid);
for pair=1:3
 ids=[1 2;3 4;5 6];a=data{ids(pair,1)};b=data{ids(pair,2)};ix=a.time_s>=30-1e-8;t=a.time_s(ix)-30;
 f=figure('Visible','off','Color','w','Position',[50 50 1200 1000]);
 subplot(4,1,1);plot(t,a.DOB_rawRequest(ix),'--','Color',[.65 .65 .65]);hold on;
 plot(t,a.DOB_request(ix),'k',t,a.Nmech(ix),'b',t,b.Nmech(ix),'r');grid on;
 ylabel('Speed (rpm)');legend('Raw PRBS','Applied demand','PI','PI + DOB','Location','best');
 title(sprintf('%s | PI %.3f, PI+DOB %.3f rpm RMSE',metrics(ids(pair,1)).kind, ...
  metrics(ids(pair,1)).rmse_rpm,metrics(ids(pair,2)).rmse_rpm),'Interpreter','none');
 subplot(4,1,2);plot(t,a.DOB_request(ix)-a.Nmech(ix),'b',t,b.DOB_request(ix)-b.Nmech(ix),'r');
 grid on;ylabel('Tracking error (rpm)');legend('PI','PI + DOB','Location','best');
 subplot(4,1,3);plot(t,a.Wf(ix),'b',t,b.Wf(ix),'r');grid on;ylabel('Actual fuel (lbm/s)');
 subplot(4,1,4);plot(t,b.DOB_disturbance(ix),'k');hold on;
 plot(t,b.DOB_estimate(ix),'Color',[.2 .55 .2]);
 plot(t,b.DOB_compensation(ix),'r');grid on;ylabel('Fuel equivalent (lbm/s)');xlabel('Evaluation time (s)');
 legend('Injected disturbance','Lumped estimate, trim removed','Applied compensation','Location','best');
 for axk=1:4
  subplot(4,1,axk);set(gca,'Position',[.10 .78-(axk-1)*.235 .85 .17],'FontSize',10);
 end
 print(f,fullfile(outDir,sprintf('comparison_%d.png',pair)),'-dpng','-r150');close(f);
end
if all([metrics(1:4).accepted])
 f=figure('Visible','off','Color','w','Position',[50 50 1150 620]);t=data{1}.time_s(ix)-30;
 subplot(2,1,1);plot(t,effectPI,'b',t,effectDOB,'r');grid on;ylabel('Disturbance-induced speed (rpm)');
 legend('PI disturbed - nominal','PI+DOB disturbed - nominal','Location','best');
 title('Paired disturbance rejection: nominal tracking contribution removed');
 subplot(2,1,2);plot(t,data{1}.DOB_disturbance(ix),'k');grid on;ylabel('Injected fuel offset (lbm/s)');xlabel('Time (s)');
 print(f,fullfile(outDir,'disturbance_rejection.png'),'-dpng','-r150');close(f);
end
disp(checks);fprintf('DOB_ANALYSIS_SUCCESS %s\n',outDir);
end
