function [MWS,DOB,PTO,VF,ENV]=tmats_poly9250_setup(gains,reference_hp)
if nargin<1,gains=[.025 .1 .002];end
if nargin<2
 root=fileparts(mfilename('fullpath'));p=fullfile(root,'results','poly2_tune9250_20260915','trim.mat');
 reference_hp=0;if exist(p,'file'),s=load(p,'reference_hp');reference_hp=s.reference_hp;end
end
[~,~,~,VF,~]=tmats_r3_poly2_setup();
[MWS,DOB,PTO]=tmats_pto_setup(reference_hp,.1,9250,[0 0 0]);DOB.gain=0;
[MWS,ENV]=tmats_environment_config(MWS,0,0);
VF.Kp=gains(1);VF.Ki=gains(2);VF.Kd=gains(3);VF.start=45;
assignin('base','MWS',MWS);assignin('base','DOB',DOB);assignin('base','PTO',PTO);assignin('base','VF',VF);assignin('base','ENV',ENV);
end
