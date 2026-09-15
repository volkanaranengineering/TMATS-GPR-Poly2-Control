function fit_tmats_environment_gpr(out)
% Exact four-input inverse GP. Freeze fit before selecting held-out labels.
rng(42,'twister');train=[];coverage=[];
for j=1:35
 s=load(fullfile(out,sprintf('environment_%02d.mat',j)),'d','config');d=s.d;
 rows=find(d.valid & d.time_s>=45 & d.time_s<90 & d.Nmech>=9000 & d.Nmech<=10000);
 X=[d.Nmech d.DOB_acceleration d.inlet_temperature_K d.inlet_pressure_kPa];
 coverage=[coverage;[j s.config.altitude_m s.config.isa_delta_C numel(rows) sum(d.valid&d.time_s>=105) min(d.DOB_SM(d.time_s>=45))]];
 assert(numel(rows)>=40,'Insufficient valid training rows in environment %d.',j);
 Z=X(rows,1:2);Z=bsxfun(@rdivide,bsxfun(@minus,Z,mean(Z)),std(Z));
 sel=spacefill(Z,40);r=rows(sel);
 train=[train;[repmat(j,40,1) r d.time_s(r) X(r,:) d.Wf(r)]];
end
names={'environment','source_row','time_s','speed_rpm','acceleration_rpm_s','inlet_temperature_K','inlet_pressure_kPa','fuel_lbm_s'};
writetable(array2table(train,'VariableNames',names),fullfile(out,'training_points.csv'));
writetable(array2table(coverage,'VariableNames',{'environment','altitude_m','isa_delta_C','valid_training_pool','valid_test_pool','minimum_margin_percent'}),fullfile(out,'environment_coverage.csv'));
X=train(:,4:7);y=train(:,8);model.mapping='speed_acceleration_inlet_temperature_pressure_to_fuel';
model.inputMean=mean(X);model.inputScale=std(X);model.outputMean=mean(y);model.outputScale=std(y);
model.Z=bsxfun(@rdivide,bsxfun(@minus,X,model.inputMean),model.inputScale);yn=(y-model.outputMean)/model.outputScale;
if exist(fullfile(out,'environment_inverse_gpr_model.mat'),'file')
 frozen=load(fullfile(out,'environment_inverse_gpr_model.mat'),'model','gp');
 assert(isequal(frozen.model.trainingRows,train(:,1:2)));model=frozen.model;gp=frozen.gp;
 fprintf('REUSING_FROZEN_GP; no refitting on validation results\n');
else
fprintf('FITTING_EXACT_GP %d training points, four inputs\n',numel(y));
gp=fitrgp(model.Z,yn,'KernelFunction','ardsquaredexponential','BasisFunction','none', ...
 'FitMethod','exact','PredictMethod','exact','Standardize',false,'Sigma',.01,'SigmaLowerBound',1e-6);
p=gp.KernelInformation.KernelParameters;model.lengthScale=p(1:4);model.signalSD=p(5);model.noiseSD=gp.Sigma;
A=bsxfun(@rdivide,model.Z,model.lengthScale');D=max(0,bsxfun(@plus,sum(A.^2,2),sum(A.^2,2)')-2*A*A');
model.L=chol(model.signalSD^2*exp(-.5*D)+model.noiseSD^2*eye(numel(y)),'lower');model.alpha=model.L'\(model.L\yn);
model.trainingInputRange=[min(X);max(X)];model.inputUnits={'rpm','rpm/s','K','kPa'};model.outputUnits='lbm/s';
model.trainingRows=train(:,1:2);model.conditions='35 altitude/ISA combinations, Mach 0, zero shaft extraction';
save(fullfile(out,'environment_inverse_gpr_model.mat'),'model','gp');
end
fprintf('MODEL_FROZEN; evaluating 200 held-out points\n');test=[];
available=find(coverage(:,5)>=7);counts=zeros(35,1);counts(available)=floor(200/numel(available));
counts(available(1:mod(200,numel(available))))=counts(available(1:mod(200,numel(available))))+1;
for j=1:35
 s=load(fullfile(out,sprintf('environment_%02d.mat',j)),'d');d=s.d;
 rows=find(d.valid & d.time_s>=105 & d.Nmech>=9000 & d.Nmech<=10000);
 count=counts(j);if count==0,continue;end
 assert(numel(rows)>=count);r=rows(unique(round(linspace(1,numel(rows),count))));
 test=[test;[repmat(j,count,1) r d.time_s(r) d.Nmech(r) d.DOB_acceleration(r) d.inlet_temperature_K(r) d.inlet_pressure_kPa(r) d.Wf(r)]];
end
assert(size(test,1)==200 && isempty(intersect(train(:,1:2),test(:,1:2),'rows')));
[mu,sd,lsd]=predict_tmats_environment_gpr(model,test(:,4:7));
zt=bsxfun(@rdivide,bsxfun(@minus,test(:,4:7),model.inputMean),model.inputScale);[gm,gs]=predict(gp,zt);
mc=max(abs(mu-model.outputMean-model.outputScale*gm));sc=max(abs(sd-model.outputScale*gs));assert(mc<1e-6&&sc<1e-6);
err=mu-test(:,8);metrics=table(size(train,1),200,sqrt(mean(err.^2)),mean(abs(err)),max(abs(err)), ...
 1-sum(err.^2)/sum((test(:,8)-mean(test(:,8))).^2),mean(abs(err)<=1.95996398454*sd),mc,sc, ...
 'VariableNames',{'training_points','test_points','rmse_lbm_s','mae_lbm_s','max_error_lbm_s','r2','coverage95','mean_export_error','sd_export_error'});
T=array2table(test,'VariableNames',names);T.prediction_lbm_s=mu;T.response_sd_lbm_s=sd;T.latent_sd_lbm_s=lsd;T.error_lbm_s=err;
writetable(T,fullfile(out,'test_200_points.csv'));writetable(metrics,fullfile(out,'gpr_metrics.csv'));
save(fullfile(out,'environment_inverse_gpr_model.mat'),'model','gp','metrics');disp(metrics);fprintf('EXACT_ENVIRONMENT_GP_COMPLETE\n');
end
function idx=spacefill(Z,n)
idx=zeros(n,1);[~,idx(1)]=min(Z(:,1));dist=inf(size(Z,1),1);
for k=1:n,dist=min(dist,sum(bsxfun(@minus,Z,Z(idx(k),:)).^2,2));dist(idx(1:k))=-Inf;if k<n,[~,idx(k+1)]=max(dist);end;end
end
