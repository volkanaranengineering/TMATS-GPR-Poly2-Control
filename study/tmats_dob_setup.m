function [MWS,DOB] = tmats_dob_setup(options)
% Frozen eight-term model DOB. Run before opening the *_DOB model.
root=fileparts(mfilename('fullpath'));
MWS=tmats_gpt_setup();
c=jsondecode(fileread(fullfile(root,'results','two_stage_rls_20260912_125027_844','coefficients.json')));
DOB.Ts=c.Ts; DOB.A=c.A(:)'; DOB.B=c.B_physical(:)'; DOB.u0=c.u0;
DOB.N0=9000; DOB.start=30; DOB.enableTime=2; DOB.gain=0.25; DOB.mode=2; DOB.fc=0.5;
DOB.fuelMin=.2; DOB.fuelMax=4; DOB.compLimit=.15; DOB.rate=150;
if nargin>0
 names=fieldnames(options);
 assert(all(ismember(names,{'gain','fc','compLimit','rate','enableTime'})),'Unsupported DOB option.');
 for k=1:numel(names),DOB.(names{k})=options.(names{k});end
end
assert(DOB.fc>0 && DOB.fc<1/(2*DOB.Ts) && DOB.gain>=0 && DOB.gain<1, ...
 'Use positive sub-Nyquist pole frequency and 0<=gain<1 for this bounded implementation.');
% Project modification, not a thesis formula: enforce zero steady acceleration.
DOB.Beq=DOB.B; DOB.Beq(end)=DOB.Beq(end)-sum(DOB.Beq);
DOB.Bspeed=DOB.Ts*cumsum(DOB.Beq(1:end-1));
assert(max(abs(roots(DOB.Bspeed(2:end))))<1,'Corrected nominal inverse is unstable.');
% Sensor is approximated by a ZOH first-order discrete model, H=q(1-p)/(1-pq).
p=exp(-DOB.Ts/.05); r=exp(-2*pi*DOB.fc*DOB.Ts);
DOB.Qnum=[0 0 (1-r)^2]; DOB.Qden=[1 -2*r r*r];
% Q/Pn has its two advances cancelled analytically; retain q-polynomial form.
DOB.InvNum=conv(DOB.A,[1 -p])*(1-r)^2;
DOB.InvDen=conv(DOB.Bspeed(2:end)*(1-p),DOB.Qden);
DOB.InvDen=DOB.InvDen(:)';
nn=max(numel(DOB.InvNum),numel(DOB.InvDen));
DOB.InvNum(end+1:nn)=0; DOB.InvDen(end+1:nn)=0;
% Time-domain ARX residual, thesis Eq. 4.13 with explicit delayed input.
DOB.ResY=conv(DOB.A,[1 -1])/(DOB.Ts*DOB.B(2));
DOB.ResU=DOB.B/DOB.B(2);
DOB.ResQnum=[0 1-r]; DOB.ResQden=[1 -r];
t=(0:6000)'*DOB.Ts;
bits=logical([0 1 1 0 1 0 1]);
for k=1:254,bits(k+7)=xor(bits(k),bits(k+3));end
request=interp1([0 5 10 30],[10000 10000 9000 9000],min(t,30));
ix=t>=30; bidx=floor((t(ix)-30)/10.005)+1;
request(ix)=9000+1000*double(bits(bidx))';
DOB.request=[t request]; rel=t-30;d=zeros(size(t));
d(rel>=7.5 & rel<15)=.08;d(rel>=20 & rel<27.5)=-.08;
ix=rel>=35 & rel<50;d(ix)=.06*sin(2*pi*.2*(rel(ix)-35));
DOB.disturbance=[t d];
DOB.request(2:end,1)=DOB.request(2:end,1)-DOB.Ts/4;
DOB.disturbance(2:end,1)=DOB.disturbance(2:end,1)-DOB.Ts/4;
MWS.in.SimTime=t(end); MWS.Solve.T=DOB.Ts;
assignin('base','MWS',MWS);assignin('base','DOB',DOB);
end
