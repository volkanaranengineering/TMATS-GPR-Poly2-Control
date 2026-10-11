function [MWS,DOB,PTO,VF,ENV]=tmats_ramp90_setup(method)
% 90% to 100% of 10000 rpm in exactly 5 s, no external power extraction.
if nargin<1,method='smooth';end
root=fileparts(mfilename('fullpath'));
g=[.025 .05 0];
if strcmp(method,'poly'),g=[.025 .14 .00125];
elseif strcmp(method,'previous')
 p=jsondecode(fileread(fullfile(root,'results','pilco_quadratic_pi_20261010','policy.json')));g=[p.Kp p.Ki 0];
elseif strcmp(method,'smooth')
 p=jsondecode(fileread(fullfile(root,'results','pilco_smooth_20261010','selected_policy.json')));g=[p.Kp p.Ki 0];
elseif ~strcmp(method,'base'),error('Unknown method');end
[MWS,DOB,PTO,VF,ENV]=tmats_poly9250_setup(g,0);
DOB.rate=200;DOB.gain=0;
DOB.request=[0 10000;5 10000;10 9000;60 9000;65 10000;80.01 10000];
DOB.disturbance=[0 0;80.01 0];PTO.profile=[0 0;80.01 0];PTO.fraction=0;PTO.reference_hp=0;
MWS.in.SimTime=80.01;
assignin('base','MWS',MWS);assignin('base','DOB',DOB);assignin('base','PTO',PTO);assignin('base','VF',VF);assignin('base','ENV',ENV);
end
