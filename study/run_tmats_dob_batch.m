try
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
build_tmats_dob_model;
out=run_tmats_dob_study('refined');
analyze_tmats_dob(out);
catch ME,disp(getReport(ME,'extended','hyperlinks','off'));exit(1);end
exit(0);
