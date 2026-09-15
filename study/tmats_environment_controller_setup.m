function [MWS,DOB,PTO,VF,ENV]=tmats_environment_controller_setup()
% Ready-to-run requested transfer case using the frozen four-input posterior.
root=fileparts(mfilename('fullpath'));out=strtrim(fileread(fullfile(root,'tmp','environment_directory.txt')));
trim=load(fullfile(out,'trim_36.mat'),'reference_hp');
[MWS,DOB,PTO,VF]=tmats_virtual_fuel_ff_setup(9500,.1,[0 0 0],[2 30],true);
[MWS,DOB,PTO]=tmats_pto_setup(trim.reference_hp,.1,9500,[0 0 0]);DOB.gain=0;
[MWS,ENV]=tmats_environment_config(MWS,4000,5);
VF.modelFile=fullfile(out,'environment_inverse_gpr_model.mat');s=load(VF.modelFile,'model');
VF.scaledTraining=bsxfun(@rdivide,s.model.Z,s.model.lengthScale');
VF.model=rmfield(s.model,{'L','Z','trainingRows'});VF.start=45;VF.feedforward=1;
assignin('base','MWS',MWS);assignin('base','DOB',DOB);assignin('base','PTO',PTO);assignin('base','VF',VF);assignin('base','ENV',ENV);
end
