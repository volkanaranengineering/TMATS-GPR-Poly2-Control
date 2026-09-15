function tmats_virtual_fuel_uq_sfun(b)
% Inverse-GPR FF plus uncertainty-scheduled, bumpless residual fuel PI.
b.NumDialogPrms=1;b.NumInputPorts=4;b.NumOutputPorts=13;
b.SetPreCompInpPortInfoToDynamic;b.SetPreCompOutPortInfoToDynamic;
for k=1:4,b.InputPort(k).Dimensions=1;b.InputPort(k).DirectFeedthrough=true;b.InputPort(k).SamplingMode='Sample';end
for k=1:13,b.OutputPort(k).Dimensions=1;b.OutputPort(k).SamplingMode='Sample';end
b.SampleTimes=[b.DialogPrm(1).Data.Ts 0];b.SimStateCompliance='DefaultSimState';
b.RegBlockMethod('PostPropagationSetup',@states);b.RegBlockMethod('InitializeConditions',@init);
b.RegBlockMethod('Outputs',@outputs);b.RegBlockMethod('Update',@update);
end
function states(b)
b.NumDworks=4;names={'previousSpeed','acceleration','integral','previousKp'};
for k=1:4,b.Dwork(k).Name=names{k};b.Dwork(k).Dimensions=1;b.Dwork(k).DatatypeID=0;b.Dwork(k).Complexity='Real';b.Dwork(k).UsedAsDiscState=true;end
end
function init(b)
b.Dwork(1).Data=10000;b.Dwork(2).Data=0;b.Dwork(3).Data=3;b.Dwork(4).Data=b.DialogPrm(1).Data.Kp;
end
function [v,a]=evaluate(b)
f=b.DialogPrm(1).Data;n=b.InputPort(1).Data;r=b.InputPort(2).Data;ar=b.InputPort(3).Data;
p=exp(-f.Ts/f.accelTau);a=p*b.Dwork(2).Data+(1-p)*(n-b.Dwork(1).Data)/f.Ts;
X=[r ar;n a];z=bsxfun(@rdivide,bsxfun(@rdivide,bsxfun(@minus,X,f.model.inputMean),f.model.inputScale),f.model.lengthScale');
K=zeros(size(f.scaledTraining,1),2);
for k=1:2,d=sum(bsxfun(@minus,f.scaledTraining,z(k,:)).^2,2);K(:,k)=f.model.signalSD^2*exp(-.5*d);end
fuel=f.model.outputMean+f.model.outputScale*(K'*f.model.alpha);
V=linsolve(f.model.L,K,struct('LT',true));
latentVariance=max(0,f.model.signalSD^2-sum(V.^2,1)');
sd=f.model.outputScale*sqrt(latentVariance+f.model.noiseSD^2);
factor=tmats_uncertainty_gain_factor(sd(1),sd(2),f.sigmaReference);
kp=f.Kp*factor;ki=f.Ki*factor;e=fuel(1)-fuel(2);
% Transfer only the coefficient-change part of P into I. Changes in error
% still see the scheduled gain; no fuel jump is caused by changing Kp alone.
integral=b.Dwork(3).Data+(b.Dwork(4).Data-kp)*e;
u=fuel(1)+kp*e+integral;command=max(f.fuelMin,min(f.fuelMax,u));
if b.CurrentTime<f.start || ~f.enabled,command=b.InputPort(4).Data;end
outside=any(X(:,1)<f.model.trainingInputRange(1,1)|X(:,1)>f.model.trainingInputRange(2,1)|X(:,2)<f.model.trainingInputRange(1,2)|X(:,2)>f.model.trainingInputRange(2,2));
v=[command;fuel;e;a;integral;u;double(outside);sd;factor;kp;ki];
end
function outputs(b)
[v,~]=evaluate(b);for k=1:13,b.OutputPort(k).Data=v(k);end
end
function update(b)
f=b.DialogPrm(1).Data;[v,a]=evaluate(b);
if b.CurrentTime<f.start || ~f.enabled
 integral=b.InputPort(4).Data-v(2)-v(12)*v(4);
else
 integral=v(6);
 if (v(7)<f.fuelMax || v(4)<0) && (v(7)>f.fuelMin || v(4)>0)
  integral=integral+f.Ts*v(13)*v(4);
 end
end
b.Dwork(3).Data=integral;b.Dwork(4).Data=v(12);
b.Dwork(1).Data=b.InputPort(1).Data;b.Dwork(2).Data=a;
end
