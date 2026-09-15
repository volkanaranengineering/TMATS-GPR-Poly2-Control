function out=run_tmats_inverse_gpr(forwardDirectory)
% Train a separate exact inverse GP using the forward study's fixed split.
% Requires Statistics and Machine Learning Toolbox; MATLAB R2018b compatible.
root=fileparts(mfilename('fullpath'));
if nargin<1
    forwardDirectory=fullfile(root,'results','exact_gpr_20260913_145742_458');
end
rng(42,'twister');
out=fullfile(root,'results',['inverse_gpr_' datestr(now,'yyyymmdd_HHMMSS_FFF')]); mkdir(out);
trainingFile=fullfile(forwardDirectory,'training_points.csv');
testFile=fullfile(forwardDirectory,'test_100_points.csv');
tr=readtable(trainingFile);
X=[tr.speed_rpm tr.acceleration_rpm_s]; y=tr.fuel_lbm_s;
assert(size(X,1)==600 && all(isfinite([X(:);y])));
assert(all(X(:,1)>=9000 & X(:,1)<=10000));
model.mapping='speed_acceleration_to_fuel';
model.inputMean=mean(X); model.inputScale=std(X);
model.outputMean=mean(y); model.outputScale=std(y);
model.Z=bsxfun(@rdivide,bsxfun(@minus,X,model.inputMean),model.inputScale);
yn=(y-model.outputMean)/model.outputScale;
fprintf('Training inverse exact GPR on %d points.\n',numel(y));
gp=fitrgp(model.Z,yn,'KernelFunction','ardsquaredexponential', ...
    'BasisFunction','none','FitMethod','exact','PredictMethod','exact', ...
    'Standardize',false,'Sigma',0.01,'SigmaLowerBound',1e-6);
p=gp.KernelInformation.KernelParameters;
model.lengthScale=p(1:2); model.signalSD=p(3); model.noiseSD=gp.Sigma;
A=bsxfun(@rdivide,model.Z,model.lengthScale');
D=max(0,bsxfun(@plus,sum(A.^2,2),sum(A.^2,2)')-2*A*A');
K=model.signalSD^2*exp(-D/2)+model.noiseSD^2*eye(numel(y));
model.L=chol(K,'lower'); model.alpha=model.L'\(model.L\yn);
model.speedRange=[9000 10000];
model.trainingInputRange=[min(X);max(X)]; model.fuelRange=[min(y) max(y)];
model.inputUnits={'rpm','rpm/s'}; model.outputUnits='lbm/s';
model.trainingRows=[tr.source_id tr.source_row]; model.trainingFile=trainingFile;
model.conditions='Fixed ambient, zero external shaft load, original T-MATS configuration';
% Freeze hyperparameters before accessing the 100 held-out samples.
te=readtable(testFile);
assert(height(te)==100 && numel(unique(te.source_row))==100);
N=te.speed_rpm; acceleration=te.true_acceleration; truth=te.fuel_lbm_s;
[mu,sd,ci,lsd]=predict_tmats_inverse_gpr(model,N,acceleration);
zt=bsxfun(@rdivide,bsxfun(@minus,[N acceleration],model.inputMean),model.inputScale);
[gm,gs]=predict(gp,zt);
meanCheck=max(abs(mu-(model.outputMean+model.outputScale*gm)));
sdCheck=max(abs(sd-model.outputScale*gs));
assert(meanCheck<1e-6 && sdCheck<1e-6,'Exported posterior disagrees with MATLAB.');
assert(all(isfinite([mu;sd;lsd])) && all(sd>=lsd) && all(lsd>=0));
% Check scalar and row-vector API use against batch prediction.
[one,oneSD]=predict_tmats_inverse_gpr(model,N(1),acceleration(1));
[row,rowSD]=predict_tmats_inverse_gpr(model,N',acceleration');
assert(abs(one-mu(1))<1e-6 && abs(oneSD-sd(1))<1e-6);
assert(max(abs(row-mu))<1e-6 && max(abs(rowSD-sd))<1e-6);
rmse=sqrt(mean((mu-truth).^2)); mae=mean(abs(mu-truth));
r2=1-sum((mu-truth).^2)/sum((truth-mean(truth)).^2);
coverage=mean(truth>=ci(:,1)&truth<=ci(:,2));
metrics=table(height(tr),height(te),rmse,mae,r2,coverage,meanCheck,sdCheck, ...
    'VariableNames',{'training_points','test_points','rmse_lbm_s','mae_lbm_s', ...
    'r2','coverage95','posterior_mean_check_lbm_s','posterior_sd_check_lbm_s'});
test=table(te.target_rpm,te.source_row,te.time_s,N,acceleration,truth,mu,sd,lsd,ci(:,1),ci(:,2), ...
    'VariableNames',{'target_rpm','source_row','time_s','speed_rpm','acceleration_rpm_s', ...
    'true_fuel_lbm_s','estimated_fuel_lbm_s','predictive_sd_lbm_s', ...
    'latent_sd_lbm_s','lower95_lbm_s','upper95_lbm_s'});
writetable(test,fullfile(out,'test_100_points.csv'));
writetable(tr,fullfile(out,'training_points.csv')); writetable(metrics,fullfile(out,'metrics.csv'));
save(fullfile(out,'inverse_gpr_model.mat'),'model','gp','metrics','forwardDirectory');
f=figure('Visible','off','Color','w','Position',[100 100 1100 720]);
subplot(2,2,1); scatter(X(:,1),X(:,2),12,y,'filled'); hold on; plot(N,acceleration,'k.');
colorbar; xlabel('Speed (rpm)'); ylabel('Acceleration (rpm/s)'); title('Training fuel flow; black = test points');
subplot(2,2,2); errorbar(N,mu,1.95996398454005*sd,'.'); hold on; plot(N,truth,'k.');
xlabel('Speed (rpm)'); ylabel('Fuel flow (lbm/s)'); title('Inverse GP and 95% response intervals'); legend('GPR','T-MATS','Location','best');
subplot(2,2,3); plot(truth,mu,'.'); hold on; lim=[min(truth) max(truth)]; plot(lim,lim,'k--');
xlabel('T-MATS fuel flow (lbm/s)'); ylabel('Estimated fuel flow (lbm/s)'); title(sprintf('RMSE %.5g lbm/s; R^2 %.6f',rmse,r2));
subplot(2,2,4); errorbar(N,mu-truth,1.95996398454005*sd,'.'); hold on; plot([9000 10000],[0 0],'k--');
xlabel('Speed (rpm)'); ylabel('Fuel error and 95% interval (lbm/s)'); title(sprintf('95%% interval coverage %.1f%%',100*coverage));
print(f,fullfile(out,'validation.png'),'-dpng','-r150'); close(f);
fid=fopen(fullfile(out,'REPORT.md'),'w'); assert(fid>=0); cleanup=onCleanup(@() fclose(fid));
fprintf(fid,'# Inverse exact GPR: speed and acceleration to fuel flow\n\n');
fprintf(fid,'Inputs: N [rpm], dN/dt [rpm/s]. Output: Wf [lbm/s], response standard deviation, 95%% response interval, and latent function standard deviation. This is a separately trained inverse regression, not an algebraic inverse of the forward GP.\n\n');
fprintf(fid,'Exact ARD squared-exponential GP with maximum-likelihood hyperparameters, zero mean on standardized responses, exact fitting and exact prediction. Uses the same 600 training observations and 100 held-out validation observations as the forward study. Training samples retain the original speed/fuel space-filling selection for direct comparison. Training records: valid chirp plus selection ramp; test record: separate validation ramp. No test-based tuning or interval rescaling.\n\n');
fprintf(fid,'Test target speeds span 9000-10000 rpm. Actual recorded speeds: %.6f to %.6f rpm; maximum target mismatch %.6f rpm. Test acceleration range: %.6f to %.6f rpm/s.\n\n',min(N),max(N),max(abs(N-te.target_rpm)),min(acceleration),max(acceleration));
fprintf(fid,'Fuel RMSE: %.9f lbm/s (%.9f kg/s). MAE: %.9f lbm/s. R2: %.9f. Nominal 95%% interval coverage: %.1f%% (%d/100).\n\n',rmse,rmse*0.45359237,mae,r2,100*coverage,round(100*coverage));
fprintf(fid,'Exported Cholesky posterior vs MATLAB maximum mean/SD errors: %.3g / %.3g lbm/s. Scalar and vector API checks passed.\n\n',meanCheck,sdCheck);
fprintf(fid,'Training input ranges: N %.6f to %.6f rpm; acceleration %.6f to %.6f rpm/s. Training fuel range %.6f to %.6f lbm/s. The rectangular ranges do not imply every input combination is supported.\n\n',min(X(:,1)),max(X(:,1)),min(X(:,2)),max(X(:,2)),min(y),max(y));
fprintf(fid,'Uncertainty uses k(x,x)-||L\\k(X,x)||^2 for latent variance and adds fitted noise variance for response variance. All outputs are rescaled to lbm/s. Hyperparameter and input-measurement uncertainty are not integrated. Test acceleration is the plant acceleration, not a noisy numerical derivative or a forward-GP prediction.\n\n');
fprintf(fid,'Application: Wf_hat = g(N, desired_acceleration) is a candidate feedforward estimate under the original fixed ambient and zero external shaft-load conditions. Closed-loop control and varying load are not validated here. Predictions are not clipped to actuator limits. The test samples are from one trajectory; exact GP inference does not guarantee an exact or globally unique physical inverse.\n\n');
fprintf(fid,'Method follows Volkan Aran (2019), Flexible and Robust Control of Heavy Duty Diesel Engine Airpath Using Data Driven Disturbance Observers and GPR Models, section 5.1 equations 5.5-5.14 and inverse feedforward modeling section 6.2.1; thesis reference [92], Rasmussen and Williams, Gaussian Processes for Machine Learning, chapter 2. This adapts the methodology to T-MATS shaft dynamics.\n\nSource forward study: `%s`.\n',forwardDirectory);
copyfile(fullfile(root,'predict_tmats_inverse_gpr.m'),out);
copyfile(fullfile(root,'run_tmats_inverse_gpr.m'),out);
disp(metrics); fprintf('RESULT_DIRECTORY=%s\n',out);
end
