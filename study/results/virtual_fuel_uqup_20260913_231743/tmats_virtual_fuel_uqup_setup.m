function [MWS,DOB,PTO,VF]=tmats_virtual_fuel_uqup_setup(rpm,fraction,ramps,gains,enabled)
% Inverse-GPR feedforward and uncertainty-scheduled residual fuel PI.
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
% One fixed scale from training locations only, independent of benchmark results.
persistent calibrationFile calibrationSD
if isempty(calibrationFile) || ~strcmp(calibrationFile,VF.modelFile)
 X=bsxfun(@plus,bsxfun(@times,VF.model.Z,VF.model.inputScale),VF.model.inputMean);
 [~,sd]=predict_tmats_inverse_gpr(VF.model,X(:,1),X(:,2));
 calibrationSD=median(sd);calibrationFile=VF.modelFile;
end
VF.sigmaReference=calibrationSD;
assert(isfinite(VF.sigmaReference)&&VF.sigmaReference>0);
assignin('base','DOB',DOB);assignin('base','VF',VF);
end



