function results = analyze_two_stage_rls(inputFile)
% Offline sparse lag selection followed by RLS, MATLAB R2018b compatible.
% results = analyze_two_stage_rls() uses this project's existing MAT records.
% results = analyze_two_stage_rls('.../offline_inputs.mat') reuses exported inputs.
% No Simulink simulations are launched and no original models are modified.
root=fileparts(mfilename('fullpath'));
c=struct('Ts',.015,'L',10,'maxTerms',10,'lambda',.999,'P0',1e4, ...
    'collinearityTolerance',1e-6,'selectionToleranceNMSE',.01, ...
    'minPhiNorm',1e-10,'yScale',1000,'u0',0.9810869146824126);
if nargin<1 || isempty(inputFile), d=loadProjectData(root,c); else, s=load(inputFile,'d'); d=s.d; end
assert(size(d.X,2)==2*c.L && numel(d.train.y)==1187);
out=fullfile(root,'results',['two_stage_rls_' datestr(now,'yyyymmdd_HHMMSS_FFF')]); mkdir(out);
save(fullfile(out,'offline_inputs.mat'),'d','c','-v7.3');
% Stage 1: reorthogonalized forward selection on valid chirp only.
% Lambda_s=1. Each candidate is evaluated with Stage-2 RLS coefficients.
X=d.X; y=d.train.y; Q=zeros(numel(y),0); S=[]; models={}; records=[];
for m=1:c.maxTerms
    scores=-inf(1,2*c.L); novelty=zeros(size(scores));
    for j=setdiff(1:2*c.L,S)
        if isempty(S) && j<=c.L, continue; end % at least one fuel term
        v=X(:,j); energy=v'*v;
        if energy<=1e-20, continue; end
        v=v-Q*(Q'*v); v=v-Q*(Q'*v); % second pass avoids loss of orthogonality
        novelty(j)=(v'*v)/energy;
        if novelty(j)<=c.collinearityTolerance, continue; end
        scores(j)=(v'*y)^2/(v'*v);
    end
    [delta,j]=max(scores);
    if ~isfinite(delta), break; end
    v=X(:,j); v=v-Q*(Q'*v); v=v-Q*(Q'*v); Q=[Q v/norm(v)]; %#ok<AGROW>
    S=[S j]; %#ok<AGROW>
    model=fitRLS(X(:,S),y,c); model.support=S;
    [model.A,model.B]=polynomials(model.theta,S,c.L);
    model.poleRadius=max(abs(roots(model.A)));
    model.stable=model.poleRadius<1;
    model.trainFree=filter(model.B,model.A,d.train.u);
    % The final validation record is deliberately not referenced here.
    model.selectionFree=filter(model.B,model.A,d.selection.u);
    vscore=nmse(d.selection.y,model.selectionFree);
    if ~model.stable || ~isfinite(vscore), vscore=Inf; end
    model.selectionNMSE=vscore;
    model.condition=cond(X(:,S));
    models{end+1}=model; %#ok<AGROW>
    records=[records; m j delta novelty(j) model.condition model.poleRadius ...
        fitpercent(y,model.prior) fitpercent(y,model.trainFree) ...
        fitpercent(d.selection.y,model.selectionFree) vscore]; %#ok<AGROW>
end
assert(~isempty(models),'No informative fuel regressor found.');
best=min(records(:,10)); assert(isfinite(best),'No stable candidate found.');
chosen=find(records(:,10)<=best+c.selectionToleranceNMSE,1,'first');
selected=models{chosen};
% Final validation is accessed only after support and all hyperparameters freeze.
selected.validationFree=filter(selected.B,selected.A,d.validation.u);
baseline=fitRLS(X(:,[1:5 c.L+(1:5)]),y,c);
baseline.support=[1:5 c.L+(1:5)];
[baseline.A,baseline.B]=polynomials(baseline.theta,baseline.support,c.L);
baseline.trainFree=filter(baseline.B,baseline.A,d.train.u);
baseline.selectionFree=filter(baseline.B,baseline.A,d.selection.u);
baseline.validationFree=filter(baseline.B,baseline.A,d.validation.u);
assert(max(abs(baseline.prior*c.yScale-d.oldPrior))<1e-5,'Baseline does not reproduce previous RLS.');
% Independent weighted QR solution of the same RLS objective, including aged prior.
active=find(sqrt(sum(X(:,selected.support).^2,2))>c.minPhiNorm);
n=numel(active); weights=c.lambda.^((n-1:-1:0)'/2);
Z=[bsxfun(@times,X(active,selected.support),weights); sqrt(c.lambda^n/c.P0)*eye(chosen)];
zy=[y(active).*weights;zeros(chosen,1)];
thetaQR=Z\zy;
qrError=norm(thetaQR-selected.theta)/max(1,norm(thetaQR));
assert(qrError<1e-5 && min(eig(selected.P))>0,'RLS verification failed.');
% Toolbox cross-check with arbitrary selected regressors.
est=recursiveLS(chosen,'InitialParameters',zeros(chosen,1), ...
    'ForgettingFactor',c.lambda,'InitialParameterCovariance',c.P0);
for k=active', th=step(est,y(k),X(k,selected.support)); end
toolboxError=norm(th-selected.theta)/max(1,norm(th));
assert(toolboxError<1e-5);
summary=struct('selected_terms',chosen,'selected_indices',selected.support, ...
    'output_delays',selected.support(selected.support<=c.L), ...
    'fuel_delays',selected.support(selected.support>c.L)-c.L, ...
    'candidate_count',size(records,1),'max_candidates',20,'max_delay_samples',c.L, ...
    'valid_chirp_end_s',d.train.t(end),'first_reference_failure_s',17.805, ...
    'valid_chirp_samples',numel(y),'updates',numel(active), ...
    'train_one_step_fit',fitpercent(y,selected.prior),'train_one_step_rmse',rmsError(y,selected.prior,c), ...
    'train_free_fit',fitpercent(y,selected.trainFree),'train_free_rmse',rmsError(y,selected.trainFree,c), ...
    'selection_free_fit',fitpercent(d.selection.y,selected.selectionFree), ...
    'validation_free_fit',fitpercent(d.validation.y,selected.validationFree), ...
    'validation_free_rmse',rmsError(d.validation.y,selected.validationFree,c), ...
    'baseline_one_step_fit',fitpercent(y,baseline.prior), ...
    'baseline_train_free_fit',fitpercent(y,baseline.trainFree), ...
    'baseline_validation_free_fit',fitpercent(d.validation.y,baseline.validationFree), ...
    'baseline_validation_free_rmse',rmsError(d.validation.y,baseline.validationFree,c), ...
    'selected_condition',selected.condition,'baseline_condition',cond(X(:,baseline.support)), ...
    'selected_pole_radius',selected.poleRadius,'baseline_pole_radius',max(abs(roots(baseline.A))), ...
    'covariance_entries',chosen^2,'baseline_covariance_entries',100, ...
    'QR_relative_coefficient_error',qrError,'toolbox_relative_coefficient_error',toolboxError, ...
    'covariance_min_eigenvalue',min(eig(selected.P)), ...
    'acceleration_reconstruction_error_rpm_s',d.reconstructionError, ...
    'baseline_prior_max_difference_rpm_s',max(abs(baseline.prior*c.yScale-d.oldPrior)), ...
    'selection_best_NMSE',best,'selected_NMSE',selected.selectionNMSE, ...
    'selection_tolerance_NMSE',c.selectionToleranceNMSE);
names={'terms','added_dictionary_index','training_SSE_reduction','relative_new_energy', ...
    'condition_number','pole_radius','one_step_fit','chirp_free_fit','selection_free_fit','selection_NMSE'};
candidateTable=array2table(records,'VariableNames',names); writetable(candidateTable,fullfile(out,'candidate_path.csv'));
comparison=table({'Selected sparse';'Previous consecutive'}, ...
    [chosen;10],[summary.train_one_step_fit;summary.baseline_one_step_fit], ...
    [summary.train_free_fit;summary.baseline_train_free_fit], ...
    [summary.validation_free_fit;summary.baseline_validation_free_fit], ...
    [summary.validation_free_rmse;summary.baseline_validation_free_rmse], ...
    'VariableNames',{'model','terms','training_one_step_fit','training_free_fit','validation_free_fit','validation_rmse_rpm_s'});
writetable(comparison,fullfile(out,'comparison.csv'));
evolution=table(d.train.t,d.train.u+c.u0,y*c.yScale,selected.prior*c.yScale, ...
    selected.trainFree*c.yScale,baseline.prior*c.yScale,baseline.trainFree*c.yScale, ...
    'VariableNames',{'time_s','fuel_lbm_s','reference_Ndot','selected_prior','selected_free','baseline_prior','baseline_free'});
for j=1:chosen
    evolution.(sprintf('theta_%d',selected.support(j)))=selected.thetaHistory(:,j);
    evolution.(sprintf('Pdiag_%d',selected.support(j)))=selected.Pdiag(:,j);
end
writetable(evolution,fullfile(out,'training_evolution.csv'));
vt=table(d.validation.t,d.validation.u+c.u0,d.validation.y*c.yScale, ...
    selected.validationFree*c.yScale,baseline.validationFree*c.yScale, ...
    'VariableNames',{'time_s','fuel_lbm_s','reference_Ndot','selected_free','baseline_free'});
writetable(vt,fullfile(out,'validation_comparison.csv'));
coef=struct('A',selected.A,'B_normalized',selected.B,'B_physical',1000*selected.B, ...
    'theta',selected.theta','support',selected.support,'u0',c.u0,'Ts',c.Ts);
writeJSON(fullfile(out,'metrics.json'),summary); writeJSON(fullfile(out,'coefficients.json'),coef);
results=struct('directory',out,'summary',summary,'selected',selected,'baseline',baseline, ...
    'candidates',{models},'config',c);
save(fullfile(out,'two_stage_results.mat'),'results','candidateTable','comparison','-v7.3');
makePlots(out,d,results,records);
writeReport(out,summary,selected,c,d);
fid=fopen(fullfile(root,'tmp','two_stage_rls_directory.txt'),'w'); fprintf(fid,'%s',out); fclose(fid);
disp(comparison); disp(summary); fprintf('TWO_STAGE_RLS_SUCCESS: %s\n',out);
end

function d=loadProjectData(root,c)
base=fullfile(root,'results','rls_blocks_acceleration_20260909_063846_871');
tr=load(fullfile(base,'rls_run.mat'),'raw');
va=load(fullfile(base,'rls_validation_run.mat'),'rawVal');
sel=load(fullfile(root,'results','ramp_selection_stretch1_20260908_214642_454','run.mat'),'data');
old=load(fullfile(root,'results','chirp_9000_10000_01_1Hz_60s_20260907_203056_686','run.mat'),'data');
raw=tr.raw; t=raw.RLS_reference.Time(:); y=matrix(raw.RLS_reference)/c.yScale;
u=(matrix(raw.Wf)-c.u0); u(t<30-1e-9)=0; % previous estimator tracks fuel offset during preparation
status=matrix(raw.RLS_status); good=t>=30-1e-9 & status(:,2)==0;
X=zeros(numel(t),2*c.L);
for lag=1:c.L
    X(lag+1:end,lag)=-y(1:end-lag);
    X(lag+1:end,c.L+lag)=u(1:end-lag);
end
d.X=X(good,:); d.train=struct('t',t(good)-30,'u',u(good),'y',y(good));
pred=matrix(raw.RLS_yhat); d.oldPrior=pred(good);
% Exact shaft law: zero external power load, J=30, hp-to-torque constant 5252.113.
% Uses signed compressor and turbine powers, not numerical differentiation.
recon=shaftAcceleration(old.data);
d.reconstructionError=max(abs(recon(good)-y(good)*c.yScale));
assert(d.reconstructionError<1e-6,'Power-based acceleration differs from direct plant Ndot.');
sd=sel.data; sg=sd.time_s>=30-1e-9;
assert(all(sd.Wf>0) && all(sd.C_Data_SMavail>0) && all(sd.Iterations<200));
flow=sd{:,{'FlowErrors_1','FlowErrors_2','FlowErrors_3'}}; assert(all(abs(flow(:))<=1e-9));
sy=shaftAcceleration(sd);
d.selection=struct('t',sd.time_s(sg)-30,'u',sd.Wf(sg)-c.u0,'y',sy(sg)/c.yScale);
rv=va.rawVal; vg=rv.RLS_reference.Time>=30-1e-9;
vy=matrix(rv.RLS_reference); vu=matrix(rv.Wf); vf=matrix(rv.RLS_flowErrors); vi=matrix(rv.Iterations);
assert(all(abs(vf(:))<=1e-9) && all(vi<200) && all(vu>0));
d.validation=struct('t',rv.RLS_reference.Time(vg)-30,'u',vu(vg)-c.u0,'y',vy(vg)/c.yScale);
vd=load(fullfile(root,'results','ramp_validation_stretch1_20260908_214653_124','run.mat'),'data');
vr=shaftAcceleration(vd.data);
d.reconstructionError=max(d.reconstructionError,max(abs(vr-vy)));
assert(d.reconstructionError<1e-6);
d.provenance='Offline saved chirp and separate selection/validation ramps; selection Ndot reconstructed by verified shaft power law.';
end
function y=shaftAcceleration(d)
y=(5252.113*d.C_Data_Pwrout./d.Nmech+5252.113*d.T_Data_Pwrout./d.Nmech)*60/(2*pi*30);
end
function m=fitRLS(X,y,c)
n=size(X,1); p=size(X,2); theta=zeros(p,1); P=c.P0*eye(p);
prior=zeros(n,1); thetaHistory=zeros(n,p); Pdiag=zeros(n,p);
for k=1:n
    phi=X(k,:)'; prior(k)=phi'*theta; thetaHistory(k,:)=theta'; Pdiag(k,:)=diag(P)';
    if norm(phi)<=c.minPhiNorm, continue; end
    Pprior=P/c.lambda; v=Pprior*phi; denom=1+phi'*v;
    theta=theta+(v/denom)*(y(k)-prior(k)); P=Pprior-(v*v')/denom; P=(P+P')/2;
end
m=struct('theta',theta,'P',P,'prior',prior,'thetaHistory',thetaHistory,'Pdiag',Pdiag);
end
function [A,B]=polynomials(theta,S,L)
A=zeros(1,L+1); A(1)=1; B=zeros(1,L+1);
for k=1:numel(S)
    if S(k)<=L, A(S(k)+1)=theta(k); else, B(S(k)-L+1)=theta(k); end
end
end
function v=nmse(y,p)
if any(~isfinite(p)), v=Inf; else, v=sum((y-p).^2)/sum((y-mean(y)).^2); end
end
function f=fitpercent(y,p), f=100*(1-sqrt(nmse(y,p))); end
function e=rmsError(y,p,c), e=sqrt(mean((y-p).^2))*c.yScale; end
function x=matrix(ts)
x=ts.Data; if ~ts.IsTimeFirst, x=permute(x,[ndims(x) 1:ndims(x)-1]); end
x=reshape(x,numel(ts.Time),[]);
end
function writeJSON(path,s)
fid=fopen(path,'w'); fprintf(fid,'%s',jsonencode(s)); fclose(fid);
end
function makePlots(out,d,r,rec)
c=r.config; a=r.selected; b=r.baseline;
f=figure('Visible','off','Color','w','Position',[50 50 1300 950]);
subplot(3,2,1); accepted=isfinite(rec(:,10)); semilogy(rec(accepted,1),rec(accepted,10),'o-'); hold on;
semilogy(numel(a.support),rec(numel(a.support),10),'rp','MarkerSize',14); grid on;
xlabel('Number of terms'); ylabel('Selection normalized MSE'); title('Stable candidates only; lower is better');
subplot(3,2,2); plot(d.train.t,d.train.y*c.yScale,d.train.t,a.prior*c.yScale); grid on;
legend('Reference','Sparse RLS','Location','best'); ylabel('rpm/s'); title('Chirp one-step prediction');
subplot(3,2,3); plot(d.train.t,d.train.y*c.yScale,d.train.t,a.trainFree*c.yScale,d.train.t,b.trainFree*c.yScale); grid on;
legend('Reference','Sparse frozen','Previous frozen','Location','best'); ylabel('rpm/s'); title('Chirp free-run');
subplot(3,2,4); plot(d.validation.t,d.validation.y*c.yScale,d.validation.t,a.validationFree*c.yScale,d.validation.t,b.validationFree*c.yScale); grid on;
legend('Reference','Sparse frozen','Previous frozen','Location','best'); ylabel('rpm/s'); title('Final ramp validation');
subplot(3,2,5); plot(d.train.t,a.thetaHistory); grid on; xlabel('Chirp time (s)'); ylabel('Coefficient'); title('Selected weights before each update');
subplot(3,2,6); semilogy(d.train.t,a.Pdiag); grid on; xlabel('Chirp time (s)'); ylabel('Covariance diagonal'); title('Selected-parameter information');
print(f,fullfile(out,'two_stage_results.png'),'-dpng','-r130'); close(f);
end
function writeReport(out,s,a,c,d)
fid=fopen(fullfile(out,'REPORT.md'),'w'); cleanup=onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'# Offline two-stage RLS results\n\n');
fprintf(fid,'Stage 1 used reorthogonalized forward selection over 20 candidates (output/fuel delays 1–10), with relative residual-energy threshold %.1g. Stage 2 used RLS with lambda %.4f and P0 %.0f. The smallest stable candidate within %.3f normalized MSE of the best selection score was chosen. No final-validation outputs entered support selection.\n\n',c.collinearityTolerance,c.lambda,c.P0,c.selectionToleranceNMSE);
fprintf(fid,'Selected **%d terms**: output delays **%s**, fuel delays **%s** (samples; multiply by 15 ms). Candidate path contains %d admissible models.\n\n',s.selected_terms,mat2str(s.output_delays),mat2str(s.fuel_delays),s.candidate_count);
fprintf(fid,'| Evaluation | Selected fit | Previous ten-term fit |\n|---|---:|---:|\n');
fprintf(fid,'| Chirp one-step | %.4f%% | %.4f%% |\n| Chirp frozen free-run | %.4f%% | %.4f%% |\n| Ramp final validation free-run | %.4f%% | %.4f%% |\n\n',s.train_one_step_fit,s.baseline_one_step_fit,s.train_free_fit,s.baseline_train_free_fit,s.validation_free_fit,s.baseline_validation_free_fit);
fprintf(fid,'Selected training one-step RMSE: %.6f rpm/s; training free-run RMSE: %.6f rpm/s. Final validation RMSE: %.6f rpm/s versus previous %.6f rpm/s. Selection-ramp fit: %.4f%%.\n\n',s.train_one_step_rmse,s.train_free_rmse,s.validation_free_rmse,s.baseline_validation_free_rmse,s.selection_free_fit);
fprintf(fid,'Selected design-matrix condition number %.6g versus previous %.6g. Final maximum pole magnitude %.8f. Stage-2 covariance has %d entries versus 100; this is theoretical storage/work reduction, not a measured whole-system speedup. The 20-candidate selection stage and longer lag buffer add overhead during learning.\n\n',s.selected_condition,s.baseline_condition,s.selected_pole_radius,s.covariance_entries);
fprintf(fid,'Validation fit changes by %+.4f percentage points, with %.2f%% lower validation RMSE. Covariance storage decreases by %.0f%% and conditioning improves by a factor of %.2f. Training free-run fit changes by %+.4f percentage points. The result is a modest generalization improvement with a smaller, better-conditioned model, not a uniformly more accurate model.\n\n',s.validation_free_fit-s.baseline_validation_free_fit,100*(1-s.validation_free_rmse/s.baseline_validation_free_rmse),100*(1-s.covariance_entries/100),s.baseline_condition/s.selected_condition,s.train_free_fit-s.baseline_train_free_fit);
fprintf(fid,'The selected sample delays correspond to output delays `%s` ms and fuel delays `%s` ms. Stage 1 stopped before ten terms because remaining candidates failed the declared redundancy test. Candidate-path CSV retains rejected unstable candidates; the plot shows stable candidates only.\n\n',mat2str(1000*c.Ts*s.output_delays),mat2str(1000*c.Ts*s.fuel_delays));
fprintf(fid,'## Reproduction and verification\n\nRun `results = analyze_two_stage_rls;` in this project, or pass this folder''s `offline_inputs.mat` as an argument. The function does not exit MATLAB or launch Simulink. Raw data are reused offline. %s\n\n',d.provenance);
fprintf(fid,'Selection acceleration uses Ndot = 60/(2*pi*30) * 5252.113 * (compressor_power/N + turbine_power/N), using signed power in hp, N in rpm and zero external load. This was checked against both chirp and validation direct Ndot logs; maximum difference %.3g rpm/s.\n\n',s.acceleration_reconstruction_error_rpm_s);
fprintf(fid,'Weighted augmented QR and RLS coefficients agree to relative error %.3g; MATLAB recursiveLS agreement %.3g. Covariance minimum eigenvalue %.3g. The repeated baseline prior predictions match previous logs within %.3g rpm/s.\n\n',s.QR_relative_coefficient_error,s.toolbox_relative_coefficient_error,s.covariance_min_eigenvalue,s.baseline_prior_max_difference_rpm_s);
fprintf(fid,'## Interpretation and limits\n\nOnly the valid chirp prefix 0–17.790 s (%d samples) was used. Reference failure begins at 17.805 s; no failed samples enter the dictionary. Because the support is chosen using the full prefix, its replay one-step fit is an offline training measure, not a fully causal online structure-selection result. Weights still predict before each current-sample update.\n\n',s.valid_chirp_samples);
fprintf(fid,'The final coefficients were frozen for the 60 s validation ramp, using zero normalized filter states after equilibrium preparation. Greedy forward selection is not an exhaustive search. The predetermined redundancy threshold can exclude useful correlated dynamic terms; this run does not tune it against final validation. Sparse linear structure cannot by itself guarantee correct equilibrium or nonlinear behavior.\n\n');
fprintf(fid,'A(z^-1), including zero coefficients at skipped lags: `%s`.\n\nB normalized: `%s`.\n\nFuel offset %.16g lbm/s; acceleration scale 1000 rpm/s. Coefficient ordering follows selected dictionary indices `%s`.\n\n',mat2str(a.A,12),mat2str(a.B,12),c.u0,mat2str(a.support));
fprintf(fid,'The polynomial convention is `A(z^-1)*y = B(z^-1)*u + e`, where `y=Ndot/1000` and `u=Wf-Wf0` in the stated units. Missing lags have exactly zero coefficients. The final lag set is frozen for this offline experiment; online support switching was not simulated.\n\n');
fprintf(fid,'Files include the candidate path, full input data, weight/covariance evolution, comparison tables, coefficients, MAT results and plot. For the mathematical proposal and literature see `TWO_STAGE_RLS_PROPOSAL.md` in the project.\n');
end
