try
run_tmats_pilco;
catch ME
disp(getReport(ME,'extended'));
fid=fopen('tmp/pilco_matlab_failed.txt','w');fprintf(fid,'%s',getReport(ME,'extended'));fclose(fid);
end
exit;
