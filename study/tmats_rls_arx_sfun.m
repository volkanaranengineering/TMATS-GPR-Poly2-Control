function tmats_rls_arx_sfun(block)
% Level-2 MATLAB S-function: causal ARX(5,5,1) acceleration observer.
block.NumDialogPrms=1;
cfg=block.DialogPrm(1).Data;
assert(cfg.na==5 && cfg.nb==5 && cfg.nk==1,'This observer uses ARX(5,5,1).');
block.NumInputPorts=5; block.NumOutputPorts=7;
block.SetPreCompInpPortInfoToDynamic; block.SetPreCompOutPortInfoToDynamic;
inDims=[1 1 3 1 1]; outDims=[1 1 10 10 3 10 1];
for k=1:5
    block.InputPort(k).Dimensions=inDims(k);
    block.InputPort(k).DatatypeID=0; block.InputPort(k).Complexity='Real';
    block.InputPort(k).SamplingMode='Sample';
    block.InputPort(k).DirectFeedthrough=true;
end
for k=1:7
    block.OutputPort(k).Dimensions=outDims(k);
    block.OutputPort(k).DatatypeID=0; block.OutputPort(k).Complexity='Real';
    block.OutputPort(k).SamplingMode='Sample';
end
block.SampleTimes=[cfg.Ts 0];
block.SimStateCompliance='DefaultSimState';
block.RegBlockMethod('PostPropagationSetup',@allocate);
block.RegBlockMethod('InitializeConditions',@initialize);
block.RegBlockMethod('Outputs',@outputs);
block.RegBlockMethod('Update',@update);
end

function allocate(block)
names={'theta','covariance','pastY','pastU','updates','fault','fuelOffset'};
dims=[10 100 5 5 1 1 1]; block.NumDworks=numel(names);
for k=1:numel(names)
    block.Dwork(k).Name=names{k}; block.Dwork(k).Dimensions=dims(k);
    block.Dwork(k).DatatypeID=0; block.Dwork(k).Complexity='Real';
    block.Dwork(k).UsedAsDiscState=true;
end
end

function initialize(block)
c=block.DialogPrm(1).Data;
for k=1:7, block.Dwork(k).Data=zeros(block.Dwork(k).Dimensions,1); end
block.Dwork(2).Data=reshape(c.P0*eye(10),100,1);
block.Dwork(7).Data=3;
end

function [phi,y,good,enabled] = signals(block)
c=block.DialogPrm(1).Data;
u=block.InputPort(1).Data; yd=block.InputPort(2).Data;
err=block.InputPort(3).Data; iter=block.InputPort(4).Data; sm=block.InputPort(5).Data;
good=all(isfinite([u;yd;err(:);iter;sm])) && ...
    max(abs(err))<=c.flowTolerance && iter<c.iterationLimit && u>=0 && sm>0;
phi=[-block.Dwork(3).Data;block.Dwork(4).Data]; y=yd/c.yScale;
enabled=block.CurrentTime>=c.startTime-1e-9 && good && ...
    block.Dwork(6).Data==0 && norm(phi)>c.minPhiNorm;
end

function outputs(block)
c=block.DialogPrm(1).Data;
[phi,y,good,enabled]=signals(block);
theta=block.Dwork(1).Data; P=reshape(block.Dwork(2).Data,10,10);
yhat=phi'*theta;
fault=block.Dwork(6).Data~=0 || ~good;
if fault, yhat=NaN; end
block.OutputPort(1).Data=yhat*c.yScale;
block.OutputPort(2).Data=(y-yhat)*c.yScale;
block.OutputPort(3).Data=theta;
block.OutputPort(4).Data=diag(P);
block.OutputPort(5).Data=[double(enabled);double(fault);block.Dwork(5).Data];
block.OutputPort(6).Data=phi;
block.OutputPort(7).Data=block.Dwork(7).Data;
end

function update(block)
c=block.DialogPrm(1).Data;
[phi,y,good,enabled]=signals(block);
if ~good, block.Dwork(6).Data=1; end
if block.Dwork(6).Data~=0, return; end
if enabled
    [theta,P]=tmats_rls_step(block.Dwork(1).Data,reshape(block.Dwork(2).Data,10,10),phi,y,c.lambda);
    block.Dwork(1).Data=theta; block.Dwork(2).Data=P(:);
    block.Dwork(5).Data=block.Dwork(5).Data+1;
end
if block.CurrentTime<c.startTime-1e-9
    % Track equilibrium during preparation, then freeze this input offset.
    block.Dwork(7).Data=block.InputPort(1).Data;
end
u=(block.InputPort(1).Data-block.Dwork(7).Data)/c.uScale;
block.Dwork(3).Data=[y;block.Dwork(3).Data(1:4)];
block.Dwork(4).Data=[u;block.Dwork(4).Data(1:4)];
end
