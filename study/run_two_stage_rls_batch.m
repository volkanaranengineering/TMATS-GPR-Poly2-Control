try
    analyze_two_stage_rls;
catch ME
    disp(getReport(ME,'extended','hyperlinks','off')); exit(1);
end
exit(0);
