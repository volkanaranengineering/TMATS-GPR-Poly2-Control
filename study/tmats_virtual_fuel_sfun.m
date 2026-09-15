function tmats_virtual_fuel_sfun(b)
% Inputs: sensed speed, governed speed, explicit acceleration setpoint, startup PI.
% Outputs: command, virtual setpoint/feedback, error, sensed acceleration,
% integral, unsaturated command, outside training rectangle flag.
b.NumDialogPrms=1;b.NumInputPorts=4;b.NumOutputPorts=8;
b.SetPreCompInpPortInfoToDynamic;b.SetPreCompOutPortInfoToDynamic;
for k=1:4,b.InputPort(k).Dimensions=1;b.InputPort(k).DirectFeedthrough=true;b.InputPort(k).SamplingMode='Sample';end
for k=1:8,b.OutputPort(k).Dimensions=1;b.OutputPort(k).SamplingMode='Sample';end
b.SampleTimes=[b.DialogPrm(1).Data.Ts 0];b.SimStateCompliance='DefaultSimState';
b.RegBlockMethod('PostPropagationSetup',@states);b.RegBlockMethod('InitializeConditions',@init);
b.RegBlockMethod('Outputs',@outputs);b.RegBlockMethod('Update',@update);
end
function states(b)
b.NumDworks=3;names={'previousSpeed','acceleration','integral'};
for k=1:3,b.Dwork(k).Name=names{k};b.Dwork(k).Dimensions=1;b.Dwork(k).DatatypeID=0;b.Dwork(k).Complexity='Real';b.Dwork(k).UsedAsDiscState=true;end
end
function init(b)
b.Dwork(1).Data=10000;b.Dwork(2).Data=0;b.Dwork(3).Data=3;
end
function [v,a]=evaluate(b)
f=b.DialogPrm(1).Data;n=b.InputPort(1).Data;r=b.InputPort(2).Data;ar=b.InputPort(3).Data;
p=exp(-f.Ts/f.accelTau);a=p*b.Dwork(2).Data+(1-p)*(n-b.Dwork(1).Data)/f.Ts;
X=[r ar;n a];z=bsxfun(@rdivide,bsxfun(@rdivide,bsxfun(@minus,X,f.model.inputMean),f.model.inputScale),f.model.lengthScale');
fuel=zeros(2,1);
for k=1:2,d=sum(bsxfun(@minus,f.scaledTraining,z(k,:)).^2,2);fuel(k)=f.model.outputMean+f.model.outputScale*f.model.signalSD^2*(exp(-.5*d)'*f.model.alpha);end
e=fuel(1)-fuel(2);u=f.Kp*e+b.Dwork(3).Data;
command=max(f.fuelMin,min(f.fuelMax,u));
if b.CurrentTime<f.start || ~f.enabled,command=b.InputPort(4).Data;end
outside=any(X(:,1)<9000|X(:,1)>9999.897804|X(:,2)<-1153.470131|X(:,2)>1076.907740);
v=[command;fuel;e;a;b.Dwork(3).Data;u;double(outside)];
end
function outputs(b)
[v,~]=evaluate(b);for k=1:8,b.OutputPort(k).Data=v(k);end
end
function update(b)
f=b.DialogPrm(1).Data;[v,a]=evaluate(b);
if b.CurrentTime<f.start || ~f.enabled
 b.Dwork(3).Data=b.InputPort(4).Data-f.Kp*v(4);
else
 % Conditional integration prevents windup in the direction of saturation.
 if (v(7)<f.fuelMax || v(4)<0) && (v(7)>f.fuelMin || v(4)>0)
  b.Dwork(3).Data=b.Dwork(3).Data+f.Ts*f.Ki*v(4);
 end
end
b.Dwork(1).Data=b.InputPort(1).Data;b.Dwork(2).Data=a;
end
