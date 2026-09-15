function verify_tmats_dob_saved()
root=fileparts(mfilename('fullpath'));out=strtrim(fileread(fullfile(root,'tmp','dob','latest_directory.txt')));
build_tmats_dob_model;
[MWS,DOB]=tmats_dob_setup();m='GasTurbine_Dyn_Template_GPT_DOB';
load_system(m);set_param(m,'CloseFcn','');
input=Simulink.SimulationInput(m);input=input.setVariable('MWS',MWS);input=input.setVariable('DOB',DOB);
input=input.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');raw=sim(input);
ref=readtable(fullfile(out,'case_02.csv'));
speedError=max(abs(raw.Nmech.Data(:)-ref.Nmech));
fuelError=max(abs(raw.Wf.Data(:)-ref.Wf));
assert(speedError<1e-7 && fuelError<1e-7,'Default saved model does not reproduce the reported run.');
fprintf('DEFAULT_MODEL_REPLAY speed=%g fuel=%g\n',speedError,fuelError);
close_system(m,0);
render_tmats_dob(out);
analyze_tmats_dob(out);
fid=fopen(fullfile(out,'default_replay.json'),'w');fwrite(fid,jsonencode(struct( ...
 'speed_max_abs_difference_rpm',speedError,'fuel_max_abs_difference_lbm_s',fuelError)),'char');fclose(fid);
end
