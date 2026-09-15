function [MWS,DOB,PTO,ALT,FF]=tmats_gpr_ff_setup(nominalRpm,fraction,ramps,method)
% Six methods: PI, DOB, LESO, UDE, GPIO, GPR_FF (inverse GP + existing PI).
if nargin<1,nominalRpm=9000;end
if nargin<2,fraction=.1;end
if nargin<3,ramps=[.3 1.5 3];end
if nargin<4,method='GPR_FF';end
names={'PI','DOB','LESO','UDE','GPIO','GPR_FF'}; codes=[1 1 2 3 4 1];
j=find(strcmp(method,names));assert(numel(j)==1);
[~,~,~,ALT]=tmats_literature_setup(codes(j),.5,nominalRpm);
[MWS,DOB,PTO]=tmats_pto_setup([],fraction,nominalRpm,ramps);
if any(j==[1 6]),DOB.gain=0;end
root=fileparts(mfilename('fullpath'));
FF.modelFile=fullfile(root,'results','inverse_gpr_20260913_150824_698','inverse_gpr_model.mat');
s=load(FF.modelFile,'model'); FF.model=s.model;
FF.Ts=DOB.Ts; FF.enabled=double(j==6); FF.nominalRpm=nominalRpm;
FF.start=DOB.start; FF.enableTime=DOB.enableTime; FF.limit=DOB.compLimit;
FF.rate=DOB.rate; FF.speedRange=[9000 10000];
FF.trimFuel=predict_tmats_inverse_gpr(FF.model,nominalRpm,0);
% Precompute constants for O(n) exact GP mean evaluation in the controller.
FF.scaledTraining=bsxfun(@rdivide,FF.model.Z,FF.model.lengthScale');
assignin('base','FF',FF);assignin('base','DOB',DOB);assignin('base','ALT',ALT);
end
