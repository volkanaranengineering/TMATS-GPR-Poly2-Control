function [MWS,DOB,PTO,VF,ENV]=tmats_gpr_remedy_setup(mode)
if nargin<1,mode=3;end
[MWS,DOB,PTO,VF,ENV]=tmats_environment_controller_setup;
out=strtrim(fileread('tmp/remedies_directory.txt'));s=load(fullfile(out,'selected_remedies.mat'),'selected','C');row=s.C(s.selected(mode),:);
VF.mode=mode;VF.Kp=row(2);VF.Ki=row(3);VF.Kd=row(4);VF.accelTau=row(5);VF.accelWeight=row(6);
assignin('base','VF',VF);
end
