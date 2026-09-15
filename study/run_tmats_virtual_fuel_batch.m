try
 run_tmats_virtual_fuel_study;
catch ME
 disp(getReport(ME,'extended','hyperlinks','off'));exit(1);
end
exit(0);
