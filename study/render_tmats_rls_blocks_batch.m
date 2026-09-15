try
    out=strtrim(fileread(fullfile('tmp','rls_blocks_directory.txt')));
    render_tmats_rls_blocks(out);
    close_system('GasTurbine_Dyn_Template_GPT_RLS_Blocks',0);
    fprintf('BLOCK_DIAGRAMS_RENDERED\n');
catch ME
    disp(getReport(ME,'extended','hyperlinks','off')); exit(1);
end
exit(0);
