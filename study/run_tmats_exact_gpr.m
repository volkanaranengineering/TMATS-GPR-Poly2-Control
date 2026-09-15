function out = run_tmats_exact_gpr()
% Exact two-input continuous-time acceleration GP; MATLAB R2018b.
root=fileparts(mfilename('fullpath')); rng(42,'twister');
out=fullfile(root,'results',['exact_gpr_' datestr(now,'yyyymmdd_HHMMSS_FFF')]); mkdir(out);
sources={fullfile(root,'results','chirp_9000_10000_01_1Hz_60s_20260907_203056_686','run.mat'), ...
 fullfile(root,'results','ramp_selection_stretch1_20260908_214642_454','run.mat'), ...
 fullfile(root,'results','ramp_validation_stretch1_20260908_214653_124','run.mat')};
train=[];
for j=1:2
 s=load(sources{j},'data'); d=s.data; g=validRows(d);
 if j==1, g=g & d.time_s<47.805-1e-9; end % first latched invalid chirp sample
 rows=find(g); a=shaftAcceleration(d);
 train=[train; [repmat(j,numel(rows),1) rows d.time_s(g) d.Nmech(g) d.Wf(g) a(g)]]; %#ok<AGROW>
end
% Deterministic input-only space-filling design, exact inference on 600 samples.
X=train(:,4:5); im=mean(X); isc=std(X); Z=bsxfun(@rdivide,bsxfun(@minus,X,im),isc);
idx=spacefill(Z,min(600,size(Z,1))); train=train(idx,:); X=train(:,4:5); y=train(:,6);
model.inputMean=mean(X); model.inputScale=std(X);
model.Z=bsxfun(@rdivide,bsxfun(@minus,X,model.inputMean),model.inputScale);
model.outputMean=mean(y); model.outputScale=std(y); yn=(y-model.outputMean)/model.outputScale;
fprintf('Training exact GPR on %d points.\n',numel(y));
gp=fitrgp(model.Z,yn,'KernelFunction','ardsquaredexponential','BasisFunction','none', ...
 'FitMethod','exact','PredictMethod','exact','Standardize',false,'Sigma',0.01,'SigmaLowerBound',1e-6);
p=gp.KernelInformation.KernelParameters;
model.lengthScale=p(1:2); model.signalSD=p(3); model.noiseSD=gp.Sigma;
A=bsxfun(@rdivide,model.Z,model.lengthScale');
D=max(0,bsxfun(@plus,sum(A.^2,2),sum(A.^2,2)')-2*A*A');
K=model.signalSD^2*exp(-D/2)+model.noiseSD^2*eye(numel(y));
model.L=chol(K,'lower'); model.alpha=model.L'\(model.L\yn);
model.speedRange=[9000 10000]; model.fuelRange=[min(X(:,2)) max(X(:,2))];
model.units={'rpm','lbm/s','rpm/s'}; model.sources=sources; model.trainingRows=train(:,1:2);
% Freeze model before opening held-out validation experiment.
s=load(sources{3},'data'); d=s.data; a=shaftAcceleration(d);
% Check acceleration labels independently against direct Simulink shaft output.
b=fullfile(root,'results','rls_blocks_acceleration_20260909_063846_871');
r=load(fullfile(b,'rls_validation_run.mat'),'rawVal'); direct=double(r.rawVal.RLS_reference.Data(:));
labelError=max(abs(a-direct)); assert(labelError<1e-6);
eligible=find(validRows(d)); targets=linspace(9000,10000,100)'; testIdx=zeros(100,1);
for k=1:100
 [~,q]=min(abs(d.Nmech(eligible)-targets(k))); testIdx(k)=eligible(q); eligible(q)=[];
end
assert(numel(unique(testIdx))==100);
N=d.Nmech(testIdx); Wf=d.Wf(testIdx); truth=a(testIdx);
[mu,sd,ci,lsd]=predict_tmats_exact_gpr(model,N,Wf);
zt=bsxfun(@rdivide,bsxfun(@minus,[N Wf],model.inputMean),model.inputScale);
[gm,gs]=predict(gp,zt);
meanCheck=max(abs(mu-(model.outputMean+model.outputScale*gm)));
sdCheck=max(abs(sd-model.outputScale*gs));
assert(meanCheck<1e-3 && sdCheck<1e-3,'Exported posterior disagrees with fitrgp.');
assert(all(isfinite(sd))&&all(sd>=lsd)&&all(lsd>=0));
rmse=sqrt(mean((mu-truth).^2)); mae=mean(abs(mu-truth));
r2=1-sum((mu-truth).^2)/sum((truth-mean(truth)).^2); coverage=mean(truth>=ci(:,1)&truth<=ci(:,2));
test=table(targets,testIdx,d.time_s(testIdx),N,Wf,truth,mu,sd,lsd,ci(:,1),ci(:,2), ...
 'VariableNames',{'target_rpm','source_row','time_s','speed_rpm','fuel_lbm_s','true_acceleration','predicted_acceleration','predictive_sd','latent_sd','lower95','upper95'});
writetable(test,fullfile(out,'test_100_points.csv'));
writetable(array2table(train,'VariableNames',{'source_id','source_row','time_s','speed_rpm','fuel_lbm_s','acceleration_rpm_s'}),fullfile(out,'training_points.csv'));
metrics=table(numel(y),100,rmse,mae,r2,coverage,labelError,meanCheck,sdCheck);
writetable(metrics,fullfile(out,'metrics.csv'));
save(fullfile(out,'exact_gpr_model.mat'),'model','gp','metrics','sources');
f=figure('Visible','off','Color','w','Position',[100 100 1100 720]);
subplot(2,2,1); scatter(X(:,1),X(:,2),12,y,'filled'); hold on; plot(N,Wf,'k.'); colorbar; xlabel('Speed (rpm)'); ylabel('Fuel (lbm/s)'); title('Training acceleration; black = 100 test points');
subplot(2,2,2); errorbar(N,mu,1.95996398454005*sd,'.'); hold on; plot(N,truth,'k.'); xlabel('Speed (rpm)'); ylabel('Acceleration (rpm/s)'); title('Held-out prediction and 95% response intervals'); legend('GPR','T-MATS','Location','best');
subplot(2,2,3); plot(truth,mu,'.'); hold on; lim=[min(truth) max(truth)]; plot(lim,lim,'k--'); xlabel('T-MATS acceleration (rpm/s)'); ylabel('GPR acceleration (rpm/s)'); title(sprintf('RMSE %.3f rpm/s; R^2 %.5f',rmse,r2));
subplot(2,2,4); plot(N,sd,'.',N,lsd,'.'); xlabel('Speed (rpm)'); ylabel('Standard deviation (rpm/s)'); legend('Response','Latent','Location','best'); title(sprintf('95%% interval coverage %.1f%%',100*coverage));
print(f,fullfile(out,'validation.png'),'-dpng','-r150'); close(f);
fid=fopen(fullfile(out,'REPORT.md'),'w'); cleanup=onCleanup(@() fclose(fid));
fprintf(fid,'# Exact GPR turbine dynamics\n\nInputs: speed N [rpm], fuel Wf [lbm/s]. Output: dN/dt [rpm/s], predictive standard deviation [rpm/s], 95%% response interval, and latent standard deviation.\n\n');
fprintf(fid,'Exact maximum-likelihood fit and exact prediction with ARD squared-exponential kernel. %d training points; exactly 100 independent-experiment test points. Training uses valid chirp and selection-ramp records; validation uses a separate ramp. Training samples selected by input-only farthest-point coverage. No test outputs used for fitting or selection.\n\n',numel(y));
fprintf(fid,'100 target speeds are linspace(9000,10000,100). Each selects the nearest unique valid recorded validation sample, without synthesizing labels. Actual speed range %.6f to %.6f rpm; maximum target mismatch %.4f rpm. Training speed %.4f to %.4f rpm; fuel %.6f to %.6f lbm/s.\n\n',min(N),max(N),max(abs(N-targets)),min(X(:,1)),max(X(:,1)),min(X(:,2)),max(X(:,2)));
fprintf(fid,'RMSE %.6f rpm/s; MAE %.6f rpm/s; R2 %.8f; nominal 95%% response-interval coverage %.1f%%.\n\n',rmse,mae,r2,100*coverage);
fprintf(fid,'Checks: power-law acceleration versus direct plant output max error %.3g rpm/s; exported Cholesky posterior versus MATLAB mean/SD errors %.3g / %.3g rpm/s.\n\n',labelError,meanCheck,sdCheck);
fprintf(fid,'Labels use signed compressor and turbine power and J=30: dN/dt = 60/(2*pi*30)*5252.113*(Pc+Pt)/N. No finite-difference derivative is used. These records assume zero external shaft load and fixed ambient conditions. A two-input model cannot identify arbitrary changes in load, ambient conditions or hidden dynamic states. Exact refers to GP inference, not an exact physical model.\n\n');
fprintf(fid,'Uncertainty: latent variance = k(x,x)-||L\\k(X,x)||^2; response variance adds fitted noise variance. Hyperparameters are fixed at their likelihood estimate; intervals are model-conditional, not guaranteed physical error bounds or a calibrated safety bound. No test-based interval rescaling. Test points come from one trajectory and are not statistically independent replicates.\n\n');
fprintf(fid,'References: Volkan Aran (2019), Flexible and Robust Control of Heavy Duty Diesel Engine Airpath Using Data Driven Disturbance Observers and GPR Models, sec. 5.1, eqs. 5.5-5.14, and sec. 6.2.1. Uses per-input length scales of eq. 5.8. Thesis reference [92]: Rasmussen and Williams, Gaussian Processes for Machine Learning (2006), ch. 2, https://gaussianprocess.org/gpml/chapters/RW2.pdf . MATLAB: https://www.mathworks.com/help/stats/fitrgp.html and https://www.mathworks.com/help/stats/regressiongp.predict.html . This adapts the GP methodology to forward turbine acceleration; it does not reproduce the thesis diesel inverse controller.\n');
disp(metrics); fprintf('RESULT_DIRECTORY=%s\n',out);
end
function g=validRows(d)
flow=d{:,{'FlowErrors_1','FlowErrors_2','FlowErrors_3'}};
g=d.time_s>=30-1e-9 & d.Nmech>=9000 & d.Nmech<=10000 & d.Wf>0 & ...
 d.C_Data_SMavail>0 & d.Iterations<200 & all(abs(flow)<=1e-9,2) & ...
 all(isfinite([d.Nmech d.Wf d.C_Data_Pwrout d.T_Data_Pwrout]),2);
end
function a=shaftAcceleration(d)
a=(5252.113*d.C_Data_Pwrout./d.Nmech+5252.113*d.T_Data_Pwrout./d.Nmech)*60/(2*pi*30);
end
function idx=spacefill(Z,n)
idx=zeros(n,1); [~,idx(1)]=min(Z(:,1)); dist=inf(size(Z,1),1);
for k=1:n
 dist=min(dist,sum(bsxfun(@minus,Z,Z(idx(k),:)).^2,2)); dist(idx(1:k))=-Inf;
 if k<n, [~,idx(k+1)]=max(dist); end
end
end
