try
    run_tmats_exact_gpr;
catch ME
    disp(getReport(ME,'extended','hyperlinks','off')); exit(1);
end
exit(0);
