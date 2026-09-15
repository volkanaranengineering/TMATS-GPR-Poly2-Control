function [MWS,DOB,PTO]=tmats_pto_setup(powerReferenceHp,fraction,nominalRpm,rampSeconds)
% Settle at nominal speed, then apply three specified shaft-power pulses.
if nargin<2,fraction=.1;end
if nargin<3,nominalRpm=10000;end
if nargin<4,rampSeconds=[0 0 0];end
validateattributes(rampSeconds,{'numeric'},{'vector','numel',3,'finite','nonnegative'});
validateattributes(nominalRpm,{'numeric'},{'scalar','finite','positive'});
validateattributes(fraction,{'numeric'},{'scalar','finite','positive','<',1});
[MWS,DOB]=tmats_dob_setup();
PTO=struct('Ts',DOB.Ts,'preparation_s',60,'duration_s',90,'fraction',fraction, ...
 'on_s',[10.005 30 60],'off_s',[15 40.005 75],'reference_hp',0,'nominal_rpm',nominalRpm);
root=fileparts(mfilename('fullpath'));
if nargin<1 || isempty(powerReferenceHp)
 f=fullfile(root,'tmp','dob','pto_reference.json');
 if nominalRpm~=10000,f=fullfile(root,'tmp','dob',sprintf('pto_reference_%grpm.json',nominalRpm));end
 if exist(f,'file'),c=jsondecode(fileread(f));powerReferenceHp=c.turbine_power_hp;else,powerReferenceHp=0;end
end
PTO.reference_hp=powerReferenceHp;
PTO.ramp_s=rampSeconds(:)';
t=(0:round((PTO.preparation_s+PTO.duration_s)/PTO.Ts))'*PTO.Ts;
rel=t-PTO.preparation_s;power=zeros(size(t));
for k=1:3
 if PTO.ramp_s(k)==0
  shape=double(rel>=PTO.on_s(k)-1e-9 & rel<PTO.off_s(k)-1e-9);
 else
  assert(PTO.ramp_s(k)<PTO.off_s(k)-PTO.on_s(k),'Ramp exceeds application window.');
  shape=max(0,min(1,(rel-PTO.on_s(k))/PTO.ramp_s(k)))-max(0,min(1,(rel-PTO.off_s(k))/PTO.ramp_s(k)));
 end
 power=power+shape*PTO.fraction*powerReferenceHp;
end
PTO.profile=[t power];PTO.profile(2:end,1)=PTO.profile(2:end,1)-PTO.Ts/4;
request=interp1([0 5 10 60],[10000 10000 nominalRpm nominalRpm],min(t,60));
DOB.request=[t request];DOB.request(2:end,1)=DOB.request(2:end,1)-PTO.Ts/4;
DOB.disturbance=[t zeros(size(t))];DOB.disturbance(2:end,1)=DOB.disturbance(2:end,1)-PTO.Ts/4;
MWS.in.SimTime=t(end);
assignin('base','MWS',MWS);assignin('base','DOB',DOB);assignin('base','PTO',PTO);
end
