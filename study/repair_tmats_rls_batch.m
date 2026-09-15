try
    build_tmats_rls_model(true);
    run_tmats_rls_batch;
catch ME
    disp(getReport(ME,'extended','hyperlinks','off')); exit(1);
end
