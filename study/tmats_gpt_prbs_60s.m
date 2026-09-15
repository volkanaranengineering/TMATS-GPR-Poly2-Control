% Independent validation input: 9000/10000 rpm PRBS, 60 s at 15 ms.
% 7-stage recurrence b(k+7)=xor(b(k),b(k+3)); period 127; bit interval .51 s.
try
    root=fileparts(mfilename('fullpath'));
    Ts=.015; duration=60; warmup=30; bitSamples=34;
    t=(0:4000)'*Ts;
    seed=logical([0 1 0 1 1 0 1]);
    sequence=false(1,261); sequence(1:7)=seed;
    for k=1:254, sequence(k+7)=xor(sequence(k),sequence(k+3)); end
    assert(isequal(sequence(1:127),sequence(128:254)));
    % Verify every 7-bit state in the first period is distinct.
    states=zeros(127,7);
    for k=1:127, states(k,:)=sequence(k:k+6); end
    assert(size(unique(states,'rows'),1)==127);
    bitIndex=floor((0:4000)'/bitSamples)+1;
    bitValue=double(sequence(bitIndex)); bitValue=bitValue(:);
    N=9000+1000*bitValue;
    prep_t=(0:2000)'*Ts;
    prep_N=interp1([0 5 10 warmup],[10000 10000 9000 9000],prep_t);
    scenario=struct('name','prbs_9000_10000_60s','time_s',[prep_t;warmup+t(2:end)], ...
        'speed_rpm',[prep_N;N(2:end)],'altitude_ft',0,'stop_s',warmup+duration, ...
        'sample_s',Ts,'interpolation','zoh');
    outDir=fullfile(root,'results',['prbs_validation_' datestr(now,'yyyymmdd_HHMMSS_FFF')]);
    mkdir(outDir);
    command=table(t,N,bitValue,bitIndex,'VariableNames', ...
        {'time_s','N_request_rpm','prbs_bit','bit_index'});
    writetable(command,fullfile(outDir,'prbs_command.csv'));
    save(fullfile(outDir,'scenario.mat'),'scenario','command','seed','sequence','bitSamples');
    fprintf('PRBS_OUTPUT_DIRECTORY: %s\n',outDir);
    fprintf('Running 30 s preparation plus 60 s PRBS; 0.51 s bit interval.\n');
    result=run_tmats_gpt(scenario);
    data=result.data(result.data.time_s>=warmup-1e-9,:);
    data.time_s=data.time_s-warmup;
    assert(height(data)==4001 && max(abs(data.N_request-N))<1e-7);
    data.prbs_bit=bitValue;
    errCols=startsWith(data.Properties.VariableNames,'FlowErrors_');
    residual=max(abs(data{:,errCols}),[],2);
    data.flow_converged=residual<=1e-9 & data.Iterations<result.metadata.iteration_limit;
    data.sample_checks_pass=data.flow_converged & all(isfinite(data{:,:}),2) & data.Wf>=0;
    % Later numerical recovery cannot validate states evolved through failed solves.
    data.before_first_failure=cumprod(double(data.sample_checks_pass))>0;
    accepted=all(data.sample_checks_pass) && result.metadata.converged;
    status='FAILED_VALIDATION_DIAGNOSTIC_ONLY';
    if accepted, status='NUMERICAL_CHECKS_PASSED'; end
    firstBad=find(~data.sample_checks_pass,1);
    firstNegative=find(data.Wf<0,1);
    summary=struct('status',status,'accepted_for_validation',accepted, ...
        'duration_s',duration,'sample_s',Ts,'samples',height(data),'preparation_s',warmup, ...
        'speed_levels_rpm',[9000 10000],'bit_interval_s',bitSamples*Ts, ...
        'samples_per_bit',bitSamples,'period_bits',127,'period_s',127*bitSamples*Ts, ...
        'recurrence','b(k+7) = xor(b(k), b(k+3))','initial_bits',double(seed), ...
        'prbs_window_note','60 s is a truncated 64.77 s PRBS period, with final bit held to endpoint.', ...
        'interpolation','zero-order hold','input_transitions',nnz(diff(N)), ...
        'source_run_directory',result.directory,'pointwise_pass_samples',nnz(data.sample_checks_pass), ...
        'consecutive_pass_samples',nnz(data.before_first_failure), ...
        'max_abs_flow_error',max(residual),'flow_tolerance',1e-9, ...
        'max_iterations',max(data.Iterations),'negative_fuel_samples',nnz(data.Wf<0), ...
        'fuel_min_lbm_s',min(data.Wf),'fuel_max_lbm_s',max(data.Wf), ...
        'speed_min_rpm',min(data.Nmech),'speed_max_rpm',max(data.Nmech), ...
        'initial_speed_rpm',data.Nmech(1));
    if ~isempty(firstBad), summary.first_failed_time_s=data.time_s(firstBad); end
    if ~isempty(firstNegative), summary.first_negative_fuel_time_s=data.time_s(firstNegative); end
    signals=data(:,{'time_s','N_request','Nmech','N_sensed','Wf','Fnet','s3_Tt', ...
        's3_Pt','s4_Tt','s5_Tt','C_Data_SMavail','prbs_bit','flow_converged', ...
        'sample_checks_pass','before_first_failure'});
    writetable(data,fullfile(outDir,'all_signals.csv'));
    name='diagnostic_signals.csv'; if accepted, name='validation_signals.csv'; end
    writetable(signals,fullfile(outDir,name));
    save(fullfile(outDir,'prbs_data.mat'),'data','signals','summary','scenario','command','-v7.3');
    fid=fopen(fullfile(outDir,'summary.json'),'w'); fwrite(fid,jsonencode(summary),'char'); fclose(fid);
    f=figure('Visible','off','Color','w','Position',[50 50 1250 950]);
    subplot(4,1,1); stairs(t,N); hold on; plot(t,data.Nmech); grid on;
    ylabel('Speed (rpm)'); legend('PRBS demand','Simulated speed','Location','best');
    title(strrep(status,'_',' ')); xlim([0 duration]);
    subplot(4,1,2); plot(t,data.Wf); grid on; ylabel('Fuel (lbm/s)'); xlim([0 duration]);
    subplot(4,1,3); plot(t,data.Fnet); grid on; ylabel('Net thrust (lbf)'); xlim([0 duration]);
    subplot(4,1,4); semilogy(t,max(residual,eps)); hold on;
    plot([0 duration],[1e-9 1e-9],'r--'); grid on; ylabel('Flow residual'); xlabel('PRBS time (s)'); xlim([0 duration]);
    print(f,fullfile(outDir,'prbs_overview.png'),'-dpng','-r130'); close(f);
    disp(summary); fprintf('PRBS_EXPORT_COMPLETE: %s\n',outDir);
catch ME
    message=getReport(ME,'extended','hyperlinks','off');
    if exist('outDir','var')
        fid=fopen(fullfile(outDir,'simulation_failure.txt'),'w'); fwrite(fid,message,'char'); fclose(fid);
    end
    disp(message); exit(1);
end
exit(0);
