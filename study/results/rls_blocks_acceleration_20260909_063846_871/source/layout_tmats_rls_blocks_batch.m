try
    mdl='GasTurbine_Dyn_Template_GPT_RLS_Blocks'; load_system(mdl);
    sub=[mdl '/RLS Acceleration Observer'];
    for k=1:5
        set_param([sub sprintf('/Negative Y %d',k)],'Position',[1420 560+k*40 1480 585+k*40]);
    end
    set_param([sub '/History vector'],'Position',[1540 580 1545 870]);
    set_param([sub '/Phi column'],'Position',[1590 680 1670 720]);
    names={'Ndot_prediction','Innovation','Theta','CovarianceDiagonal','UpdateStatus','Regressor','FuelOffset'};
    for k=1:7, set_param([sub '/' names{k}],'Position',[1850 30+100*k 1880 50+100*k]); end
    save_system(mdl);
    out=strtrim(fileread(fullfile('tmp','rls_blocks_directory.txt')));
    render_tmats_rls_blocks(out); close_system(mdl,0);
    fprintf('BLOCK_LAYOUT_COMPLETE\n');
catch ME
    disp(getReport(ME,'extended','hyperlinks','off')); exit(1);
end
exit(0);
