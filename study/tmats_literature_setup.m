function [MWS,DOB,PTO,ALT]=tmats_literature_setup(method,frequencyHz,nominalRpm)
% Basic-block realizations: method 1=existing DOB, 2=LESO, 3=UDE, 4=GPIO.
if nargin<1,method=2;end
if nargin<2,frequencyHz=.5;end
if nargin<3,nominalRpm=9000;end
[MWS,DOB,PTO]=tmats_pto_setup([],0.1,nominalRpm,[.30 1.50 3.00]);
ALT.method=method;ALT.use=double(method>=2);ALT.frequencyHz=frequencyHz;
% Identified one-step fuel-to-acceleration gain; other dynamics are lumped.
ALT.b0=DOB.B(2);assert(ALT.b0>0);w=2*pi*frequencyHz;
switch method
 case {1,2}
  ALT.name='LESO';A=[-2*w 1;-w*w 0];B=[2*w 1;w*w 0];C=[0 1];D=[0 0];
 case 3
  ALT.name='UDE';A=-w;B=[-w*w -w];C=1;D=[w 0];
 case 4
  ALT.name='GPIO';A=[-3*w 1 0;-3*w*w 0 1;-w^3 0 0];B=[3*w 1;3*w*w 0;w^3 0];C=[0 1 0];D=[0 0];
 otherwise,error('Unknown observer method.');
end
% Exact ZOH of observer driven by sampled speed and limited fuel command.
n=size(A,1);E=expm([A B;zeros(2,n+2)]*DOB.Ts);
ALT.Ad=E(1:n,1:n);ALT.Bd=E(1:n,n+1:end);ALT.C=C;ALT.D=D;ALT.x0=zeros(n,1);
ALT.poles=eig(ALT.Ad);assert(all(abs(ALT.poles)<1));
assignin('base','ALT',ALT);
end
