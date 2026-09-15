function tmats_gpr_ff_sfun(block)
% Discrete inverse-model feedforward; no disturbance/plant-acceleration input.
block.NumDialogPrms=1; block.NumInputPorts=2; block.NumOutputPorts=5;
block.SetPreCompInpPortInfoToDynamic; block.SetPreCompOutPortInfoToDynamic;
for k=1:2
 block.InputPort(k).Dimensions=1;block.InputPort(k).DirectFeedthrough=true;
 block.InputPort(k).SamplingMode='Sample';
end
for k=1:5,block.OutputPort(k).Dimensions=1;block.OutputPort(k).SamplingMode='Sample';end
block.SampleTimes=[block.DialogPrm(1).Data.Ts 0];
block.SimStateCompliance='DefaultSimState';
block.RegBlockMethod('PostPropagationSetup',@setupState);
block.RegBlockMethod('InitializeConditions',@initialize);
block.RegBlockMethod('Outputs',@outputs);block.RegBlockMethod('Update',@update);
end
function setupState(b)
b.NumDworks=1;b.Dwork(1).Name='previousReference';b.Dwork(1).Dimensions=1;
b.Dwork(1).DatatypeID=0;b.Dwork(1).Complexity='Real';b.Dwork(1).UsedAsDiscState=true;
end
function initialize(b)
b.Dwork(1).Data=10000;
end
function outputs(b)
f=b.DialogPrm(1).Data; sensed=b.InputPort(1).Data; ref=b.InputPort(2).Data;
a=max(-f.rate,min(f.rate,(ref-b.Dwork(1).Data)/f.Ts));
n=max(f.speedRange(1),min(f.speedRange(2),sensed));
if f.enabled
 z=([n a]-f.model.inputMean)./f.model.inputScale./f.model.lengthScale';
 d=sum(bsxfun(@minus,f.scaledTraining,z).^2,2);
 fuel=f.model.outputMean+f.model.outputScale*f.model.signalSD^2*(exp(-.5*d)'*f.model.alpha);
 ramp=max(0,min(1,(b.CurrentTime-f.start)/f.enableTime));
 correction=ramp*max(-f.limit,min(f.limit,fuel-f.trimFuel));
else
 fuel=f.trimFuel;correction=0;
end
b.OutputPort(1).Data=correction;b.OutputPort(2).Data=fuel;
b.OutputPort(3).Data=a;b.OutputPort(4).Data=n;
b.OutputPort(5).Data=double(sensed<f.speedRange(1) || sensed>f.speedRange(2));
end
function update(b)
b.Dwork(1).Data=b.InputPort(2).Data;
end
