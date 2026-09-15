try
 run_tmats_gpr_ff_benchmarks;
catch ME
 disp(getReport(ME,'extended','hyperlinks','off'));exit(1);
end
exit(0);
