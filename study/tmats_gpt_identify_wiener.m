function tmats_gpt_identify_wiener()
% Estimate a pure Wiener model on the converged chirp prefix using MATLAB SIT.
% Orders [nb nf nk]: nb <= 10, nf <= 10, quadratic output; input is unitgain.
root=fileparts(mfilename('fullpath'));
assert(license('test','Identification_Toolbox')==1,'System Identification Toolbox unavailable.');
rng(20260908,'twister');
outDir=strtrim(fileread(fullfile(root,'tmp','wiener_ramp_directory.txt')));
r=load(fullfile(outDir,'experiments.mat'));
c=load(fullfile(root,'results','chirp_request_20260907_203021_394','chirp_data.mat'));
bad=find(~c.data.valid_sample,1);
assert(~isempty(bad),'Expected documented chirp failure boundary.');
train=c.data(1:bad-1,:);
selection=r.experiments.selection.data;
validation=r.experiments.validation.data;
assert(height(train)==1187 && abs(train.time_s(end)-17.79)<1e-9);
assert(r.experiments.selection.metadata.converged && r.experiments.validation.metadata.converged);
Ts=r.Ts;
scaling=struct('input_offset',train.Wf(1),'input_scale',std(train.Wf), ...
    'output_offset',train.Nmech(1),'output_scale',std(train.Nmech));
makeData=@(d) iddata((d.Nmech-scaling.output_offset)/scaling.output_scale, ...
    (d.Wf-scaling.input_offset)/scaling.input_scale,Ts);
ze=makeData(train); zs=makeData(selection); zv=makeData(validation);
ze.InputName={'fuel_flow_normalized'}; ze.OutputName={'shaft_speed_normalized'};
zs.InputName=ze.InputName; zs.OutputName=ze.OutputName;
zv.InputName=ze.InputName; zv.OutputName=ze.OutputName;
writetable(train,fullfile(outDir,'training_chirp_valid.csv'));
save(fullfile(outDir,'identification_data.mat'),'ze','zs','zv','scaling','train','selection','validation','Ts','-v7.3');
orders=[];
for nb=1:4
    for nf=1:4
        for nk=0:1, orders(end+1,:)=[nb nf nk]; end
    end
end
for n=5:10
    for nk=0:1, orders(end+1,:)=[n n nk]; end
end
options=nlhwOptions('Display','off','InitialCondition','zero');
options.SearchOptions.MaxIterations=80;
options.SearchOptions.Tolerance=1e-6;
models={}; records=struct([]); tested=zeros(0,3);
checkpoint=fullfile(outDir,'search_checkpoint.mat');
if exist(checkpoint,'file')
    previous=load(checkpoint,'models','records','tested');
    models=previous.models; records=previous.records; tested=previous.tested;
    fprintf('RESUMING %d stored candidates.\n',numel(records));
end
fprintf('WIENER_SEARCH_BEGIN: %d initial candidates\n',size(orders,1));
for phase=1:2
    for k=1:size(orders,1)
        order=orders(k,:);
        if ismember(order,tested,'rows'), continue; end
        tested(end+1,:)=order;
        id=size(tested,1);
        rec=struct('candidate',id,'nb',order(1),'nf',order(2),'nk',order(3), ...
            'train_fit_percent',NaN,'selection_fit_percent',NaN, ...
            'train_rmse_rpm',NaN,'selection_rmse_rpm',NaN,'max_pole_abs',NaN, ...
            'stable',false,'seconds',NaN,'status','FAILED','error','');
        start=tic;
        try
            model=nlhw(ze,order,unitgain,poly1d(2),options);
            model.Name=sprintf('Wiener_nb%d_nf%d_nk%d_quad',order);
            poles=roots(model.F{1});
            rec.max_pole_abs=max(abs(poles)); rec.stable=all(abs(poles)<1);
            assert(rec.stable,'Unstable linear dynamics.');
            ye=sim(model,ze.InputData); ys=sim(model,zs.InputData);
            assert(all(isfinite(ye)) && all(isfinite(ys)),'Nonfinite model simulation.');
            rec.train_fit_percent=fitPct(ze.OutputData,ye);
            rec.selection_fit_percent=fitPct(zs.OutputData,ys);
            rec.train_rmse_rpm=sqrt(mean((ze.OutputData-ye).^2))*scaling.output_scale;
            rec.selection_rmse_rpm=sqrt(mean((zs.OutputData-ys).^2))*scaling.output_scale;
            rec.status='OK'; models{id}=model;
        catch ME
            rec.error=ME.message; models{id}=[];
        end
        rec.seconds=toc(start);
        if isempty(records), records=rec; else, records(id)=rec; end
        fprintf('CANDIDATE %d [%d %d %d]: train %.4f%% selection %.4f%% (%s, %.1fs)\n', ...
            id,order,rec.train_fit_percent,rec.selection_fit_percent,rec.status,rec.seconds);
        results=struct2table(records,'AsArray',true);
        writetable(results,fullfile(outDir,'candidate_scores.csv'));
        save(fullfile(outDir,'search_checkpoint.mat'),'models','records','tested','scaling','-v7.3');
    end
    scores=[records.selection_fit_percent]; scores(~isfinite(scores))=-Inf;
    [bestScore,bestID]=max(scores); assert(isfinite(bestScore),'No stable candidate was fitted.');
    if phase==1
        winner=tested(bestID,:); orders=[];
        for nb=max(1,winner(1)-1):min(10,winner(1)+1)
            for nf=max(1,winner(2)-1):min(10,winner(2)+1)
                for nk=0:1, orders(end+1,:)=[nb nf nk]; end
            end
        end
    end
end
% Refine the selected model on CHIRP ONLY. Keep it only if selection improves.
bestModel=models{bestID};
options.SearchOptions.MaxIterations=200;
try
    refined=nlhw(ze,bestModel,options);
    trial=sim(refined,zs.InputData);
    refinedScore=fitPct(zs.OutputData,trial);
    if all(abs(roots(refined.F{1}))<1) && refinedScore>bestScore
        bestModel=refined; bestScore=refinedScore;
    end
catch ME
    fprintf('REFINEMENT_NOTE: %s\n',ME.message);
end
% Final hold-out outputs have not influenced estimation or order selection.
predTrain=sim(bestModel,ze.InputData)*scaling.output_scale+scaling.output_offset;
predSelection=sim(bestModel,zs.InputData)*scaling.output_scale+scaling.output_offset;
predValidation=sim(bestModel,zv.InputData)*scaling.output_scale+scaling.output_offset;
B=bestModel.B{1}; F=bestModel.F{1}; quadratic=bestModel.OutputNonlinearity.Coefficients;
assert(bestModel.nb<=10 && bestModel.nf<=10 && bestModel.OutputNonlinearity.Degree==2);
standalone=polyval(quadratic,filter(B,F,zv.InputData))*scaling.output_scale+scaling.output_offset;
assert(max(abs(standalone-predValidation))<1e-5,'Standalone filter equation mismatch.');
compareOpt=compareOptions('InitialCondition','zero');
[~,toolboxFit]=compare(zv,bestModel,Inf,compareOpt);
assert(abs(toolboxFit-fitPct(validation.Nmech,predValidation))<1e-7,'Fit definition mismatch.');
metrics=struct('model_type','Wiener','input','actual fuel flow (lbm/s)', ...
    'output','mechanical shaft speed (rpm)','sample_s',Ts,'nb',bestModel.nb, ...
    'nf',bestModel.nf,'nk',bestModel.nk,'nonlinearity_degree',2, ...
    'training_fit_percent',fitPct(train.Nmech,predTrain), ...
    'selection_fit_percent',fitPct(selection.Nmech,predSelection), ...
    'validation_fit_percent',fitPct(validation.Nmech,predValidation), ...
    'training_rmse_rpm',sqrt(mean((train.Nmech-predTrain).^2)), ...
    'selection_rmse_rpm',sqrt(mean((selection.Nmech-predSelection).^2)), ...
    'validation_rmse_rpm',sqrt(mean((validation.Nmech-predValidation).^2)), ...
    'validation_max_abs_error_rpm',max(abs(validation.Nmech-predValidation)), ...
    'training_duration_s',train.time_s(end),'training_samples',height(train), ...
    'training_frequency_limit_Hz',.1+.015*train.time_s(end), ...
    'validation_duration_s',validation.time_s(end),'validation_samples',height(validation), ...
    'candidates_tested',numel(records),'max_pole_abs',max(abs(roots(F))), ...
    'initial_conditions','zero states after training-only equilibrium offsets', ...
    'fit_definition','100*(1-norm(y-yhat)/norm(y-mean(y)))', ...
    'search_note','Coarse orders 1..4 pairs and 5..10 diagonal, delays 0/1, then local refinement; not exhaustive.', ...
    'training_exclusion','All chirp samples at and after first failure t=17.805 s excluded.', ...
    'data_origin','Noise-free synthetic closed-loop experiments; actual fuel is plant identification input.');
coefficients=struct('B',B,'F',F,'quadratic_descending',quadratic,'scaling',scaling,'sample_s',Ts);
save(fullfile(outDir,'best_wiener_model.mat'),'bestModel','coefficients','metrics','ze','zs','zv', ...
    'predTrain','predSelection','predValidation','-v7.3');
fid=fopen(fullfile(outDir,'fit_metrics.json'),'w'); fwrite(fid,jsonencode(metrics),'char'); fclose(fid);
fid=fopen(fullfile(outDir,'model_coefficients.json'),'w'); fwrite(fid,jsonencode(coefficients),'char'); fclose(fid);
exportPrediction(train,predTrain,fullfile(outDir,'training_predictions.csv'));
exportPrediction(selection,predSelection,fullfile(outDir,'selection_predictions.csv'));
exportPrediction(validation,predValidation,fullfile(outDir,'validation_predictions.csv'));
f=figure('Visible','off','Color','w','Position',[40 40 1250 850]);
subplot(2,2,1); plot(train.time_s,train.Nmech,train.time_s,predTrain); grid on;
ylabel('Speed (rpm)'); xlabel('Time (s)'); legend('T-MATS','Wiener','Location','best');
title(sprintf('Training: valid chirp | Fit %.3f%%',metrics.training_fit_percent));
subplot(2,2,2); plot(validation.time_s,validation.Nmech,validation.time_s,predValidation); grid on;
ylabel('Speed (rpm)'); xlabel('Time (s)'); legend('T-MATS','Wiener','Location','best');
title(sprintf('Held-out ramp/hold | Fit %.3f%%',metrics.validation_fit_percent));
subplot(2,2,3); plot(train.time_s,train.Nmech-predTrain); grid on;
ylabel('Error (rpm)'); xlabel('Time (s)'); title('Training simulation error');
subplot(2,2,4); plot(validation.time_s,validation.Nmech-predValidation); grid on;
ylabel('Error (rpm)'); xlabel('Time (s)'); title('Validation simulation error');
print(f,fullfile(outDir,'wiener_fit.png'),'-dpng','-r140'); close(f);
disp(bestModel); disp(metrics); fprintf('WIENER_IDENTIFICATION_SUCCESS: %s\n',outDir);
end

function fit=fitPct(y,yhat)
fit=100*(1-norm(y-yhat)/norm(y-mean(y)));
end

function exportPrediction(d,p,path)
tab=table(d.time_s,d.Wf,d.Nmech,p,d.Nmech-p, ...
    'VariableNames',{'time_s','fuel_lbm_s','actual_speed_rpm','model_speed_rpm','error_rpm'});
writetable(tab,path);
end
