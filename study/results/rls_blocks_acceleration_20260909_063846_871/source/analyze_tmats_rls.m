function analyze_tmats_rls(out,modelName)
root=fileparts(mfilename('fullpath'));
if nargin<1, out=strtrim(fileread(fullfile(root,'tmp','rls_directory.txt'))); end
if nargin<2, modelName='GasTurbine_Dyn_Template_GPT_RLS'; end
s=load(fullfile(out,'rls_run.mat')); raw=s.raw; c=s.RLS;
t=raw.RLS_reference.Time(:); y=matrix(raw.RLS_reference); u=matrix(raw.Wf);
yhat=matrix(raw.RLS_yhat); innovation=matrix(raw.RLS_error);
thetaLog=matrix(raw.RLS_theta); Pdiag=matrix(raw.RLS_Pdiag);
status=matrix(raw.RLS_status); phiLog=matrix(raw.RLS_phi); u0=matrix(raw.RLS_u0);
assert(numel(t)==6001 && size(thetaLog,2)==10 && all(abs(diff(t)-c.Ts)<1e-9));
% Reproduce online pre-update coefficients and verify weighted normal equations.
theta=zeros(10,1); P=c.P0*eye(10); H=eye(10)/c.P0; g=zeros(10,1);
maxReplay=0;
for k=1:numel(t)
    maxReplay=max(maxReplay,max(abs(theta-thetaLog(k,:)')));
    if status(k,1)>0
        phi=phiLog(k,:)'; yn=y(k)/c.yScale;
        assert(abs(yhat(k)-phi'*theta*c.yScale)<1e-7);
        [theta,P]=tmats_rls_step(theta,P,phi,yn,c.lambda);
        H=c.lambda*H+phi*phi'; g=c.lambda*g+phi*yn;
    end
end
assert(maxReplay<1e-8,'Simulink and offline RLS state evolution disagree.');
batchTheta=H\g;
batchError=norm(theta-batchTheta)/max(1,norm(batchTheta));
assert(batchError<1e-5,'RLS and exponentially weighted batch least squares disagree.');
toolboxRLS=recursiveLS(10,'InitialParameters',zeros(10,1), ...
    'ForgettingFactor',c.lambda,'InitialParameterCovariance',c.P0);
for k=find(status(:,1)>0)'
    toolboxTheta=step(toolboxRLS,y(k)/c.yScale,phiLog(k,:));
end
toolboxError=norm(theta-toolboxTheta)/max(1,norm(toolboxTheta));
assert(toolboxError<1e-5,'Custom RLS and System Identification Toolbox recursiveLS disagree.');
assert(min(eig(P))>0,'RLS covariance lost positive definiteness.');
firstFault=find(status(:,2)>0,1); assert(~isempty(firstFault));
assert(all(all(abs(thetaLog(firstFault:end,:)-thetaLog(firstFault,:))<1e-12)));
assert(all(status(firstFault:end,1)==0),'Estimator updated after invalid reference.');
window=t>=c.startTime-1e-9;
good=window & status(:,2)==0;
tv=t(good)-c.startTime; yg=y(good); ug=u(good); phig=phiLog(good,:);
pred=yhat(good); thetaG=thetaLog(good,:); offset=u0(find(good,1));
finalTheta=theta;
A=[1 finalTheta(1:5)']; B=[0 finalTheta(6:10)'];
fixed=filter(B,A,(ug-offset)/c.uScale)*c.yScale;
[adaptive,adaptiveFailure]=freeAdaptive(thetaG,phig,c.yScale);
sv=svd(phig(status(good,1)>0,:),0);
condition=sv(1)/sv(end); effectiveRank=sum(sv/sv(1)>1e-6);
poleRadius=zeros(numel(tv),1);
for k=1:numel(tv), poleRadius(k)=max(abs(roots([1 thetaG(k,1:5)]))); end
persistence=-phig(:,1)*c.yScale;
metrics=struct('model',modelName,'input','actual fuel flow, lbm/s', ...
    'output','direct plant Ndot, rpm/s','na',5,'nb',5,'nk',1,'regressors',10, ...
    'sample_s',c.Ts,'lambda',c.lambda,'P0',c.P0,'normalization',struct('u0',offset,'uScale',c.uScale,'yScale',c.yScale), ...
    'chirp_duration_s',60,'valid_end_s',tv(end),'valid_samples',numel(tv), ...
    'first_reference_failure_s',t(firstFault)-c.startTime,'updates',nnz(status(:,1)), ...
    'one_step_fit_percent',fit(yg,pred),'one_step_rmse_rpm_s',rmse(yg,pred), ...
    'persistence_fit_percent',fit(yg,persistence),'persistence_rmse_rpm_s',rmse(yg,persistence), ...
    'first_3s_rmse_rpm_s',rmse(yg(tv<3),pred(tv<3)), ...
    'last_5s_fit_percent',fit(yg(tv>=tv(end)-5),pred(tv>=tv(end)-5)), ...
    'last_5s_rmse_rpm_s',rmse(yg(tv>=tv(end)-5),pred(tv>=tv(end)-5)), ...
    'final_frozen_chirp_free_run_fit_percent',fit(yg,fixed), ...
    'final_frozen_chirp_free_run_rmse_rpm_s',rmse(yg,fixed), ...
    'final_max_pole_abs',max(abs(roots(A))), ...
    'online_unstable_parameter_samples',nnz(poleRadius>=1), ...
    'regressor_singular_values',sv','regressor_condition_number',condition, ...
    'regressor_effective_rank_relative_1e_6',effectiveRank, ...
    'max_simulink_replay_coefficient_error',maxReplay, ...
    'weighted_batch_relative_coefficient_error',batchError, ...
    'toolbox_recursiveLS_relative_coefficient_error',toolboxError, ...
    'covariance_min_eigenvalue',min(eig(P)),'covariance_trace_initial',10*c.P0, ...
    'covariance_trace_final',trace(P),'theta_frozen_after_reference_failure',true, ...
    'adaptive_free_run_failure_sample',adaptiveFailure);
if all(isfinite(adaptive))
    metrics.adaptive_free_run_fit_percent=fit(yg,adaptive);
    metrics.adaptive_free_run_rmse_rpm_s=rmse(yg,adaptive);
end
% Confirm observer leaves the reference plant unchanged over the valid prefix.
original=load(fullfile(root,'results','chirp_9000_10000_01_1Hz_60s_20260907_203056_686','run.mat'),'raw');
speed=matrix(raw.Nmech); originalSpeed=matrix(original.raw.Nmech); originalFuel=matrix(original.raw.Wf);
metrics.reference_speed_difference_rpm=max(abs(speed(good)-originalSpeed(good)));
metrics.reference_fuel_difference_lbm_s=max(abs(u(good)-originalFuel(good)));
assert(metrics.reference_speed_difference_rpm<1e-5 && metrics.reference_fuel_difference_lbm_s<1e-7);
% Freeze final chirp coefficients; test against a separately simulated ramp.
v=load(fullfile(out,'rls_validation_run.mat')); rv=v.rawVal;
vi=rv.RLS_reference.Time>=30-1e-9;
vt=rv.RLS_reference.Time(vi)-30; vy=matrix(rv.RLS_reference); vy=vy(vi);
vu=matrix(rv.Wf); vu=vu(vi); ve=matrix(rv.RLS_flowErrors); ve=ve(vi,:);
viter=matrix(rv.Iterations); viter=viter(vi);
assert(all(abs(ve(:))<=1e-9) && all(viter<200) && all(vu>0));
vpred=filter(B,A,(vu-offset)/c.uScale)*c.yScale;
metrics.frozen_ramp_fit_percent=fit(vy,vpred);
metrics.frozen_ramp_rmse_rpm_s=rmse(vy,vpred);
metrics.ramp_max_flow_error=max(abs(ve(:)));
metrics.ramp_duration_s=vt(end);
validation=table(vt,vu,vy,vpred,vy-vpred,'VariableNames', ...
    {'time_s','fuel_lbm_s','reference_acceleration_rpm_s','frozen_ARX_acceleration_rpm_s','error_rpm_s'});
writetable(validation,fullfile(out,'frozen_ramp_validation.csv'));
% Forgetting-factor sensitivity uses the SAME valid chirp, without parameter tuning.
ablations=[];
for lambda=[1 .999 .995]
    th=zeros(10,1); pp=c.P0*eye(10); predictions=zeros(size(yg));
    for k=1:numel(yg)
        phi=phig(k,:)'; predictions(k)=phi'*th*c.yScale;
        if norm(phi)>c.minPhiNorm, [th,pp]=tmats_rls_step(th,pp,phi,yg(k)/c.yScale,lambda); end
    end
    ablations=[ablations;lambda fit(yg,predictions) rmse(yg,predictions) max(abs(roots([1 th(1:5)']))) trace(pp)]; %#ok<AGROW>
end
writetable(array2table(ablations,'VariableNames',{'lambda','one_step_fit_percent','rmse_rpm_s','final_pole_radius','trace_P'}), ...
    fullfile(out,'forgetting_factor_sensitivity.csv'));
rolling=zeros(size(tv)); rollingRmse=zeros(size(tv));
for k=1:numel(tv)
    ii=max(1,k-round(2/c.Ts)+1):k;
    rolling(k)=fit(yg(ii),pred(ii)); rollingRmse(k)=rmse(yg(ii),pred(ii));
end
evolution=table(tv,ug,yg,pred,innovation(good),persistence,adaptive,fixed, ...
    rolling,rollingRmse,poleRadius,'VariableNames',{'time_s','fuel_lbm_s','reference_Ndot_rpm_s', ...
    'RLS_prior_prediction_rpm_s','innovation_rpm_s','persistence_rpm_s','adaptive_free_run_rpm_s', ...
    'final_frozen_free_run_rpm_s','rolling_2s_fit_percent','rolling_2s_rmse_rpm_s','pole_radius'});
for k=1:10
    evolution.(sprintf('theta_%d',k))=thetaG(:,k);
    evolution.(sprintf('Pdiag_%d',k))=Pdiag(good,k);
end
writetable(evolution,fullfile(out,'rls_valid_evolution.csv'));
gate=table(t(window)-30,y(window),yhat(window),status(window,1),status(window,2),status(window,3), ...
    'VariableNames',{'time_s','reference_Ndot_rpm_s','RLS_prediction_rpm_s','update_enabled','reference_fault_latched','updates_before_sample'});
writetable(gate,fullfile(out,'full_chirp_gate_diagnostics.csv'));
coefficients=struct('A',A,'B_normalized',B,'B_physical',B*c.yScale/c.uScale, ...
    'theta',finalTheta','fuel_offset_lbm_s',offset,'sample_s',c.Ts);
save(fullfile(out,'rls_results.mat'),'metrics','coefficients','finalTheta','P','H','g', ...
    'evolution','validation','ablations','c','-v7.3');
writeJson(fullfile(out,'metrics.json'),metrics); writeJson(fullfile(out,'final_arx_coefficients.json'),coefficients);
f=figure('Visible','off','Color','w','Position',[40 40 1350 1000]);
subplot(3,2,1); plot(tv,yg,tv,pred); grid on; ylabel('Acceleration (rpm/s)');
legend('T-MATS Ndot','RLS prior prediction','Location','best'); title(sprintf('Online one-step fit %.3f%%',metrics.one_step_fit_percent));
subplot(3,2,2); plot(tv,yg-pred,tv,yg-persistence); grid on; ylabel('Error (rpm/s)');
legend('RLS','Persistence','Location','best'); title('Prediction before current-sample update');
subplot(3,2,3); plot(tv,thetaG); grid on; ylabel('Normalized ARX coefficients'); title('10 coefficient trajectories');
subplot(3,2,4); semilogy(tv,Pdiag(good,:)); grid on; ylabel('Covariance diagonal'); title('Algorithm covariance, not confidence bounds');
subplot(3,2,5); plot(tv,rollingRmse); grid on; ylabel('2 s rolling RMSE (rpm/s)'); xlabel('Chirp time (s)');
subplot(3,2,6); plot(tv,poleRadius); hold on; plot([0 tv(end)],[1 1],'r--'); grid on;
ylabel('Maximum pole magnitude'); xlabel('Chirp time (s)'); title('Instantaneous ARX stability');
print(f,fullfile(out,'rls_evolution.png'),'-dpng','-r135'); close(f);
f=figure('Visible','off','Color','w','Position',[40 40 1300 850]);
subplot(2,2,1); plot(tv,yg,tv,fixed); grid on; legend('T-MATS','Frozen ARX','Location','best');
ylabel('Acceleration (rpm/s)'); title(sprintf('Frozen chirp free-run fit %.2f%%',metrics.final_frozen_chirp_free_run_fit_percent));
subplot(2,2,2); plot(vt,vy,vt,vpred); grid on; legend('T-MATS','Frozen ARX','Location','best');
title(sprintf('Held-out ramp free-run fit %.2f%%',metrics.frozen_ramp_fit_percent)); ylabel('Acceleration (rpm/s)');
subplot(2,2,3); plot(tv,yg,tv,adaptive); grid on; xlabel('Chirp time (s)'); ylabel('Acceleration (rpm/s)');
legend('T-MATS','Adaptive free-run','Location','best'); title('Own-output feedback with evolving coefficients');
subplot(2,2,4); stairs(gate.time_s,gate.update_enabled); hold on; stairs(gate.time_s,gate.reference_fault_latched);
grid on; xlabel('Chirp time (s)'); ylabel('Status'); legend('Update enabled','Fault latched','Location','best');
print(f,fullfile(out,'rls_free_run_and_gate.png'),'-dpng','-r135'); close(f);
disp(metrics); fprintf('RLS_ANALYSIS_SUCCESS: %s\n',out);
end

function x=matrix(ts)
x=ts.Data;
if ~ts.IsTimeFirst, x=permute(x,[ndims(x) 1:ndims(x)-1]); end
x=reshape(x,numel(ts.Time),[]);
end
function f=fit(y,p)
if any(~isfinite(p)) || norm(y-mean(y))<1e-10, f=NaN; else, f=100*(1-norm(y-p)/norm(y-mean(y))); end
end
function e=rmse(y,p), e=sqrt(mean((y-p).^2)); end
function [pred,failure]=freeAdaptive(th,phi,scale)
pred=NaN(size(th,1),1); h=zeros(5,1); failure=0;
for k=1:size(th,1)
    x=[-h;phi(k,6:10)']'*th(k,:)';
    if ~isfinite(x) || abs(x*scale)>1e6, failure=k; break; end
    pred(k)=x*scale; h=[x;h(1:4)];
end
end
function writeJson(path,s)
fid=fopen(path,'w'); fwrite(fid,jsonencode(s),'char'); fclose(fid);
end
