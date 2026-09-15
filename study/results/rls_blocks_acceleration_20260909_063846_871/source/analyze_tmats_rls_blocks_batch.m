try
    root=fileparts(mfilename('fullpath'));
    out=strtrim(fileread(fullfile(root,'tmp','rls_blocks_directory.txt')));
    mdl='GasTurbine_Dyn_Template_GPT_RLS_Blocks';
    analyze_tmats_rls(out,mdl);
    oldDir=fullfile(root,'results','rls_acceleration_20260908_225810_094');
    old=load(fullfile(oldDir,'rls_run.mat'),'raw');
    current=load(fullfile(out,'rls_run.mat'),'raw');
    fields={'RLS_theta','RLS_Pdiag','RLS_yhat','RLS_status','RLS_phi','RLS_u0'};
    audit=struct;
    for k=1:numel(fields)
        name=fields{k}; x=ordered(current.raw.(name)); y=ordered(old.raw.(name));
        assert(isequal(size(x),size(y)) && isequal(isfinite(x),isfinite(y)));
        valid=isfinite(x); delta=max(abs(x(valid)-y(valid)));
        audit.([name '_max_abs_difference'])=delta;
        assert(delta<1e-4,'Basic-block and S-function histories disagree: %s',name);
    end
    load_system(mdl); sub=[mdl '/RLS Acceleration Observer'];
    blocks=find_system(sub,'LookUnderMasks','all','FollowLinks','on','Type','Block');
    types=get_param(blocks,'BlockType');
    assert(~any(ismember(types,{'S-Function','MATLABSystem','Fcn'})));
    chartObjects=sfroot; charts=chartObjects.find('-isa','Stateflow.EMChart');
    for k=1:numel(charts), assert(~strncmp(charts(k).Path,sub,numel(sub))); end
    audit.observer_blocks=numel(blocks)-1;
    audit.observer_S_functions=0; audit.observer_MATLAB_Function_blocks=0;
    inventory=table(blocks,types,'VariableNames',{'block_path','block_type'});
    writetable(inventory,fullfile(out,'observer_block_inventory.csv'));
    render_tmats_rls_blocks(out);
    close_system(mdl,0);
    fid=fopen(fullfile(out,'basic_blocks_audit.json'),'w'); fwrite(fid,jsonencode(audit),'char'); fclose(fid);
    disp(audit); fprintf('RLS_BASIC_BLOCKS_ANALYSIS_SUCCESS: %s\n',out);
catch ME
    disp(getReport(ME,'extended','hyperlinks','off')); exit(1);
end
exit(0);

function x=ordered(ts)
x=ts.Data;
if ~ts.IsTimeFirst, x=permute(x,[ndims(x) 1:ndims(x)-1]); end
x=reshape(x,numel(ts.Time),[]); x=x(:);
end
