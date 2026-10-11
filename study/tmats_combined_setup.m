function [MWS,DOB,PTO,VF,ENV]=tmats_combined_setup(method)
% Relative test time: speed ramp 0--5 s, 10% shaft load 10--15 s.
if nargin<1,method='smooth';end
[MWS,DOB,PTO,VF,ENV]=tmats_ramp90_setup(method);
root=fileparts(mfilename('fullpath'));
ref=readtable(fullfile(root,'results','pilco_ramp90_equal_sensor_20261010','base.csv'));
q=ref.time_s>=68 & ref.time_s<70;
PTO.reference_hp=mean(ref.PTO_turbine_hp(q));
PTO.fraction=.10;PTO.nominal_rpm=10000;PTO.on_s=10;PTO.off_s=15;PTO.duration_s=25.005;
PTO.profile=[0 0;70 .10*PTO.reference_hp;75 0;85.005 0];
DOB.request=[0 10000;5 10000;10 9000;60 9000;65 10000;85.005 10000];
DOB.disturbance=[0 0;85.005 0];MWS.in.SimTime=85.005;
assignin('base','MWS',MWS);assignin('base','DOB',DOB);assignin('base','PTO',PTO);assignin('base','VF',VF);assignin('base','ENV',ENV);
end
