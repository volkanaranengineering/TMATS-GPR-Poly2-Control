% Four amplitudes, each tested with 0.30, 1.50 and 3.00 s load ramps.
try
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
directories={};
for fraction=[.05 .1 .2 .3]
 try
  out=run_tmats_pto_study(fraction,9000,[.30 1.50 3.00]);directories{end+1}=out;
 catch ME
  fprintf('PTO_9000_LEVEL_FAILED %.2f\n%s\n',fraction,getReport(ME,'extended','hyperlinks','off'));
 end
 fid=fopen('tmp/dob/pto_9000_ramp_directories.json','w');fwrite(fid,jsonencode(directories),'char');fclose(fid);
end
fprintf('PTO_9000_RAMP_BATCH_COMPLETE\n');
catch ME,disp(getReport(ME,'extended','hyperlinks','off'));exit(1);end
exit(0);
