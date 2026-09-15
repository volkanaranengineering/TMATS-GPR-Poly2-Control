try
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
build_tmats_pto_model;
out=run_tmats_pto_study;
analyze_tmats_pto(out);
catch ME,disp(getReport(ME,'extended','hyperlinks','off'));exit(1);end
exit(0);
