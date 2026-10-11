function tmats_pilco_pi_sfun(b)
% Frozen quadratic setpoint feedforward + speed-error PI, learned by PILCO.
% Port contract matches the existing quadratic model, retaining its logging.
b.NumDialogPrms=1;b.NumInputPorts=6;b.NumOutputPorts=13;
b.SetPreCompInpPortInfoToDynamic;b.SetPreCompOutPortInfoToDynamic;
for k=1:6,b.InputPort(k).Dimensions=1;b.InputPort(k).DirectFeedthrough=true;b.InputPort(k).SamplingMode='Sample';end
for k=1:13,b.OutputPort(k).Dimensions=1;b.OutputPort(k).SamplingMode='Sample';end
b.SampleTimes=[b.DialogPrm(1).Data.Ts 0];b.SimStateCompliance='DefaultSimState';
b.RegBlockMethod('PostPropagationSetup',@states);b.RegBlockMethod('InitializeConditions',@init);
b.RegBlockMethod('Outputs',@outputs);b.RegBlockMethod('Update',@update);
end
function states(b)
b.NumDworks=1;b.Dwork(1).Name='integral';b.Dwork(1).Dimensions=1;b.Dwork(1).DatatypeID=0;b.Dwork(1).Complexity='Real';b.Dwork(1).UsedAsDiscState=true;
end
function init(b)
b.Dwork(1).Data=0;
end
function v=evaluate(b)
f=b.DialogPrm(1).Data;n=b.InputPort(1).Data;r=b.InputPort(2).Data;
X=[r 0 b.InputPort(5).Data b.InputPort(6).Data];ff=tmats_poly2_mean_gradient(f,X);
e=r-n;p=f.Kp*e;u=ff+p+b.Dwork(1).Data;
command=max(f.fuelMin,min(f.fuelMax,u));
if b.CurrentTime<f.start,command=b.InputPort(4).Data;end
outside=any(X<f.poly.trainingInputRange(1,:) | X>f.poly.trainingInputRange(2,:));
v=[command;ff;0;e;0;b.Dwork(1).Data;u;double(outside);e;p;0;0;0];
end
function outputs(b)
v=evaluate(b);for k=1:13,b.OutputPort(k).Data=v(k);end
end
function update(b)
f=b.DialogPrm(1).Data;v=evaluate(b);
if b.CurrentTime<f.start
 b.Dwork(1).Data=b.InputPort(4).Data-v(2)-v(10);
elseif (v(7)<f.fuelMax || v(4)<0) && (v(7)>f.fuelMin || v(4)>0)
 b.Dwork(1).Data=b.Dwork(1).Data+f.Ts*f.Ki*v(4);
end
end
