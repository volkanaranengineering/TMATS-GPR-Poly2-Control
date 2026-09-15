% Read-only model inspection and baseline execution in a separate MATLAB process.
try
    root = fileparts(mfilename('fullpath'));
    if exist(fullfile(root,'tmp','baseline_probe.mat'),'file')
        previous=load(fullfile(root,'tmp','baseline_probe.mat'));
        baseline=run_tmats_gpt();
        assert(max(abs(baseline.raw.Nmech.Data-previous.result.Nmech.Data))<1e-7, ...
            'Runner changed baseline speed response.');
        assert(max(abs(baseline.raw.Wf.Data-previous.result.Wf.Data))<1e-7, ...
            'Runner changed baseline fuel response.');
        disp(baseline.metadata);
        disp(baseline.data([1 334 668 end],{'time_s','N_request','Nmech','Wf','Fnet'}));
        step=run_tmats_gpt(struct('name','step_10rpm','time_s',[0 1.5 3], ...
            'speed_rpm',[10000 9990 9990],'altitude_ft',0,'stop_s',3, ...
            'interpolation','zoh'));
        assert(all(step.data.N_request(step.data.time_s<1.5)==10000));
        assert(all(step.data.N_request(step.data.time_s>=1.5)==9990));
        assert(baseline.metadata.converged && step.metadata.converged);
        disp('TMATS_GPT_RUNNER_SUCCESS');
        exit(0);
    end
    trunk = fileparts(root);
    addpath(genpath(fullfile(trunk,'TMATS_Library')));
    addpath(fullfile(trunk,'TMATS_Examples','Example_GasTurbine_Dyn','SimSetup'));
    MWS.engName = 'engine1'; MWS.top_level = root;
    names = {'Solve_temp','Inputs','HPC','Shaft','Noz','HPT','Burner','Duct','Inlet'};
    for k=1:numel(names), MWS=feval(['setup_' names{k}],MWS); end
    mdl='GasTurbine_Dyn_Template_GPT';
    load_system(fullfile(root,[mdl '.mdl']));
    set_param(mdl,'CloseFcn','');
    disp(version); disp(get_param(mdl,'FileName'));
    disp(find_system(mdl,'LookUnderMasks','all','FollowLinks','on','BlockType','ToWorkspace'));
    result=sim(mdl,'ReturnWorkspaceOutputs','on');
    save(fullfile(root,'tmp','baseline_probe.mat'),'result','MWS');
    disp(result); disp(result.Nmech); disp(result.C_Data); disp(result.T_Data);
    close_system(mdl,0);
    disp('TMATS_GPT_PROBE_SUCCESS');
catch ME
    disp(getReport(ME,'extended','hyperlinks','off'));
    exit(1);
end
exit(0);
