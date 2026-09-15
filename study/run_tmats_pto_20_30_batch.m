try
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
directories={};
for fraction=[.2 .3]
 try
  out=run_tmats_pto_study(fraction);directories{end+1}=out;
  analyze_tmats_pto(out);
 catch ME
  fprintf('PTO_LEVEL_FAILED %.2f\n%s\n',fraction,getReport(ME,'extended','hyperlinks','off'));
 end
end
fid=fopen('tmp/dob/pto_20_30_directories.json','w');fwrite(fid,jsonencode(directories),'char');fclose(fid);
fprintf('PTO_20_30_BATCH_COMPLETE\n');
catch ME,disp(getReport(ME,'extended','hyperlinks','off'));exit(1);end
exit(0);
