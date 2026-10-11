function [MWS,DOB,PTO,VF,ENV]=tmats_dob98_setup(gains)
root=fileparts(mfilename('fullpath'));out=fullfile(root,'results','dob98_pi_20261010');
if nargin<1
 f=fullfile(out,'selected_policy.json');if exist(f,'file'),s=jsondecode(fileread(f));gains=[s.Kp s.Ki];else,gains=[.025 .05];end
end
[MWS,DOB,PTO,VF,ENV]=tmats_combined_setup('base');
c=jsondecode(fileread(fullfile(out,'identified_model.json')));
DOB.N0=c.N0;DOB.u0=c.u0;DOB.fc=c.fc_Hz;DOB.gain=c.dob_gain;DOB.compLimit=c.compensation_limit_lbm_s;
DOB.mode=2;DOB.start=45;DOB.enableTime=2;
p=exp(-DOB.Ts/c.sensor_tau_s);r=exp(-2*pi*DOB.fc*DOB.Ts);
% Pn=b*q/(1-a*q), H=q*(1-p)/(1-p*q), Q=q^2*(1-r)^2/(1-r*q)^2.
DOB.Qnum=[0 0 (1-r)^2];DOB.Qden=[1 -2*r r*r];
DOB.InvNum=conv([1 -c.a],[1 -p])*(1-r)^2/(c.b*(1-p));DOB.InvDen=DOB.Qden;
assert(max(abs(roots(DOB.InvDen)))<1);
VF.Kp=gains(1);VF.Ki=gains(2);VF.Kd=0;
assignin('base','MWS',MWS);assignin('base','DOB',DOB);assignin('base','PTO',PTO);assignin('base','VF',VF);assignin('base','ENV',ENV);
end
