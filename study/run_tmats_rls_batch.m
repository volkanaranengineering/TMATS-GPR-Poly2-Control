try
    root=fileparts(mfilename('fullpath'));
    mdl='GasTurbine_Dyn_Template_GPT_RLS';
    if ~exist(fullfile(root,[mdl '.mdl']),'file'), build_tmats_rls_model(); end
    [MWS,RLS]=tmats_rls_setup();
    load_system(fullfile(root,[mdl '.mdl']));
    observer=find_system(mdl,'SearchDepth',1,'Name','RLS Acceleration Observer');
    assert(numel(observer)==1, ...
        'Incomplete RLS model; finish the builder before simulation.');
    input=Simulink.SimulationInput(mdl);
    input=input.setVariable('MWS',MWS);
    input=input.setVariable('RLS',RLS);
    input=input.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');
    raw=sim(input);
    outDir=fullfile(root,'results',['rls_acceleration_' datestr(now,'yyyymmdd_HHMMSS_FFF')]);
    mkdir(outDir);
    save(fullfile(outDir,'rls_run.mat'),'raw','MWS','RLS','-v7.3');
    fid=fopen(fullfile(root,'tmp','rls_directory.txt'),'w'); fwrite(fid,outDir,'char'); fclose(fid);
    % Independent frozen-model check: reuse the previous held-out ramp profile.
    rampDir=strtrim(fileread(fullfile(root,'tmp','wiener_ramp_directory.txt')));
    ramp=readtable(fullfile(rampDir,'validation_profile.csv'));
    MWSv=MWS;
    MWSv.in.t_vec=[0 5 10 30+ramp.time_s'];
    MWSv.in.Ndmd=[10000 10000 9000 ramp.speed_demand_rpm'];
    MWSv.in.Alt=zeros(size(MWSv.in.t_vec));
    MWSv.in.SimTime=30+ramp.time_s(end);
    RLSv=RLS; RLSv.startTime=Inf;
    vi=Simulink.SimulationInput(mdl);
    vi=vi.setVariable('MWS',MWSv);
    vi=vi.setVariable('RLS',RLSv);
    vi=vi.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');
    rawVal=sim(vi);
    save(fullfile(outDir,'rls_validation_run.mat'),'rawVal','MWSv','RLSv','ramp','-v7.3');
    close_system(mdl,0);
    fprintf('RLS_SIMULATION_SUCCESS: %s\n',outDir);
catch ME
    disp(getReport(ME,'extended','hyperlinks','off')); exit(1);
end
exit(0);
