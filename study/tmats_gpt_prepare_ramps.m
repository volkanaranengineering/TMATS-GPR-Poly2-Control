% Generate ramp/hold selection and final validation data; train on valid chirp.
try
    root=fileparts(mfilename('fullpath'));
    assert(license('test','Identification_Toolbox')==1,'System Identification Toolbox license unavailable.');
    disp(ver('ident')); disp(which('nlhw')); disp(poly1d(2));
    outDir=fullfile(root,'results',['wiener_ramps_' datestr(now,'yyyymmdd_HHMMSS_FFF')]);
    mkdir(outDir);
    profiles(1)=struct('name','estimation','t',[0 3 13 16 21 24 34 37 42 45 51 54 58 60], ...
        'N',[9000 9000 10000 10000 9500 9500 9000 9000 10000 10000 9400 9400 10000 10000]);
    profiles(2)=struct('name','selection','t',[0 4 12 16 22 25 35 38 43 46 52 55 60], ...
        'N',[9000 9000 9800 9800 9200 9200 9700 9700 10000 10000 9100 9100 9100]);
    profiles(3)=struct('name','validation','t',[0 3 9 12 17 20 28 31 36 40 50 54 60], ...
        'N',[9000 9000 9900 9900 9400 9400 9800 9800 9050 9050 10000 10000 10000]);
    warmup=30; Ts=.015;
    experiments=struct;
    for j=2:3
        p=profiles(j);
        % If a planned ramp fails, retry the entire record with all times doubled.
        accepted=false;
        for stretch=[1 2 4]
            scenario=struct('name',['ramp_' p.name '_stretch' num2str(stretch)], ...
                'time_s',[0 5 10 warmup+stretch*p.t], ...
                'speed_rpm',[10000 10000 9000 p.N], ...
                'altitude_ft',0,'stop_s',warmup+stretch*p.t(end), ...
                'sample_s',Ts,'interpolation','linear');
            fprintf('SIMULATING %s, stretch %g\n',p.name,stretch);
            result=run_tmats_gpt(scenario);
            data=result.data(result.data.time_s>=warmup-1e-9,:);
            data.time_s=data.time_s-warmup;
            accepted=result.metadata.converged && all(data.Wf>0) && ...
                all(data.C_Data_SMavail>0) && all(all(isfinite(data{:,:})));
            if accepted, break; end
            fprintf('REJECTED %s at stretch %g; slowing ramp schedule.\n',p.name,stretch);
        end
        assert(accepted,'Unable to create converged %s ramps.',p.name);
        profile=table(stretch*p.t(:),p.N(:),'VariableNames',{'time_s','speed_demand_rpm'});
        compact=data(:,{'time_s','N_request','Nmech','Wf','N_sensed','Fnet','C_Data_SMavail', ...
            's3_Tt','s3_Pt','s4_Tt','s5_Tt','Iterations','FlowErrors_1','FlowErrors_2','FlowErrors_3'});
        writetable(profile,fullfile(outDir,[p.name '_profile.csv']));
        writetable(compact,fullfile(outDir,[p.name '_data.csv']));
        experiments.(p.name)=struct('data',compact,'profile',profile, ...
            'metadata',result.metadata,'source_directory',result.directory, ...
            'ramp_rates_rpm_s',diff(p.N)./(stretch*diff(p.t)));
        fprintf('ACCEPTED %s: %d samples, fuel %.4g..%.4g, min SM %.4g\n', ...
            p.name,height(compact),min(compact.Wf),max(compact.Wf),min(compact.C_Data_SMavail));
        save(fullfile(outDir,'experiments.mat'),'experiments','profiles','Ts','warmup','-v7.3');
    end
    fid=fopen(fullfile(root,'tmp','wiener_ramp_directory.txt'),'w'); fwrite(fid,outDir,'char'); fclose(fid);
    fprintf('RAMP_DATA_SUCCESS: %s\n',outDir);
catch ME
    disp(getReport(ME,'extended','hyperlinks','off')); exit(1);
end
exit(0);
