function [MWS,DOB,PTO,VF]=tmats_virtual_fuel_ff_setup(rpm,fraction,ramps,gains,enabled)
% Inverse-GPR feedforward plus residual fuel-domain PI.
if nargin<1,rpm=9000;end
if nargin<2,fraction=.1;end
if nargin<3,ramps=[.3 1.5 3];end
if nargin<4,gains=[3 60];end
if nargin<5,enabled=true;end
[MWS,DOB,PTO]=tmats_pto_setup([],fraction,rpm,ramps);DOB.gain=0;
root=fileparts(mfilename('fullpath'));
VF.modelFile=fullfile(root,'results','inverse_gpr_20260913_150824_698','inverse_gpr_model.mat');
s=load(VF.modelFile,'model');VF.model=s.model;
VF.scaledTraining=bsxfun(@rdivide,VF.model.Z,VF.model.lengthScale');
VF.Ts=DOB.Ts;VF.Kp=gains(1);VF.Ki=gains(2);VF.enabled=enabled;
VF.start=30;VF.accelTau=.03;VF.fuelMin=DOB.fuelMin;VF.fuelMax=DOB.fuelMax;
assignin('base','DOB',DOB);assignin('base','VF',VF);
end

