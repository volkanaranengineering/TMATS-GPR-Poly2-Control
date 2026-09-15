% Speed-demand chirp: 9000..10000 rpm, linear sweep 0.1..1 Hz, 60 s.
% Run in a dedicated MATLAB process. The first 30 s prepare the initial state.
try
    root=fileparts(mfilename('fullpath'));
    Ts=0.015; duration=60; warmup=30;
    chirp_t=(0:round(duration/Ts))'*Ts;
    frequency_Hz=0.1+(1-0.1)*chirp_t/duration;
    phase=2*pi*(0.1*chirp_t+0.5*(1-0.1)/duration*chirp_t.^2);
    command_rpm=9500-500*cos(phase);
    prep_t=(0:round(warmup/Ts))'*Ts;
    prep_N=interp1([0 5 10 warmup],[10000 10000 9000 9000],prep_t);
    scenario=struct('name','chirp_9000_10000_01_1Hz_60s', ...
        'time_s',[prep_t;warmup+chirp_t(2:end)], ...
        'speed_rpm',[prep_N;command_rpm(2:end)], ...
        'altitude_ft',0,'stop_s',warmup+duration,'sample_s',Ts,'interpolation','linear');
    requestDir=fullfile(root,'results',['chirp_request_' datestr(now,'yyyymmdd_HHMMSS_FFF')]);
    mkdir(requestDir);
    command=table(chirp_t,command_rpm,frequency_Hz,'VariableNames', ...
        {'time_s','N_request_rpm','instantaneous_frequency_Hz'});
    writetable(command,fullfile(requestDir,'requested_command.csv'));
    save(fullfile(requestDir,'scenario.mat'),'scenario','command','warmup');
    fprintf('CHIRP_REQUEST_DIR: %s\n',requestDir);
    fprintf('Simulating 30 s preparation plus 60 s chirp, at 15 ms.\n');
    result=run_tmats_gpt(scenario);
    data=result.data(result.data.time_s>=warmup-1e-9,:);
    data.time_s=data.time_s-warmup;
    assert(height(data)==4001);
    assert(max(abs(data.N_request-command_rpm))<1e-7);
    data.instantaneous_frequency_Hz=frequency_Hz;
    errCols=startsWith(data.Properties.VariableNames,'FlowErrors_');
    residual=max(abs(data{:,errCols}),[],2);
    data.flow_converged=residual<=result.metadata.flow_error_tolerance & ...
        data.Iterations<result.metadata.iteration_limit;
    data.valid_sample=data.flow_converged & all(isfinite(data{:,:}),2) & data.Wf>=0;
    summary=struct('duration_s',duration,'sample_interval_s',Ts,'samples',height(data), ...
        'preparation_s',warmup,'frequency_start_Hz',0.1,'frequency_end_Hz',1, ...
        'command_formula','9500 - 500*cos(2*pi*(0.1*t + 0.0075*t^2))', ...
        'interpretation','Speed demand oscillates between 9000 and 10000 rpm; not a monotonic acceleration.', ...
        'source_run_directory',result.directory, ...
        'valid_samples',nnz(data.valid_sample),'all_samples_valid',all(data.valid_sample), ...
        'max_abs_flow_error',max(residual),'max_iterations',max(data.Iterations), ...
        'speed_min_rpm',min(data.Nmech),'speed_max_rpm',max(data.Nmech), ...
        'fuel_min_lbm_s',min(data.Wf),'fuel_max_lbm_s',max(data.Wf), ...
        'tracking_rmse_rpm',sqrt(mean((data.Nmech-data.N_request).^2)), ...
        'initial_speed_rpm',data.Nmech(1),'final_speed_rpm',data.Nmech(end));
    writetable(data,fullfile(requestDir,'chirp_data.csv'));
    identification=data(:,{'time_s','N_request','Nmech','N_sensed','Wf','Fnet', ...
        's3_Tt','s3_Pt','s4_Tt','s5_Tt','C_Data_SMavail', ...
        'instantaneous_frequency_Hz','flow_converged','valid_sample'});
    writetable(identification,fullfile(requestDir,'diagnostic_signals.csv'));
    save(fullfile(requestDir,'chirp_data.mat'),'data','identification','summary','scenario','command','-v7.3');
    fid=fopen(fullfile(requestDir,'summary.json'),'w');
    fwrite(fid,jsonencode(summary),'char'); fclose(fid);
    f=figure('Visible','off','Color','w','Position',[50 50 1250 900]);
    subplot(4,1,1); plot(data.time_s,data.N_request,data.time_s,data.Nmech); grid on;
    ylabel('Speed (rpm)'); legend('Demand','Actual','Location','eastoutside');
    title('9000-10000 rpm demand chirp: 0.1 to 1 Hz in 60 s'); xlim([0 duration]);
    subplot(4,1,2); plot(data.time_s,data.Wf); grid on; ylabel('Fuel (lbm/s)'); xlim([0 duration]);
    subplot(4,1,3); plot(data.time_s,data.Fnet); grid on; ylabel('Net thrust (lbf)'); xlim([0 duration]);
    subplot(4,1,4); semilogy(data.time_s,max(residual,eps)); hold on;
    plot([0 duration],[1e-9 1e-9],'r--'); grid on; ylabel('Flow residual'); xlabel('Chirp time (s)'); xlim([0 duration]);
    print(f,fullfile(requestDir,'chirp_overview.png'),'-dpng','-r130'); close(f);
    disp(summary);
    fprintf('CHIRP_EXPORT_COMPLETE: %s\n',requestDir);
catch ME
    if exist('requestDir','var')
        failure=getReport(ME,'extended','hyperlinks','off');
        fid=fopen(fullfile(requestDir,'simulation_failure.txt'),'w');
        fwrite(fid,failure,'char'); fclose(fid);
    end
    disp(getReport(ME,'extended','hyperlinks','off'));
    exit(1);
end
exit(0);
