function tmats_r3_dynamic_ff_sfun(b)
% Three remedy architectures; preserve original eight outputs plus diagnostics.
b.NumDialogPrms=1;b.NumInputPorts=6;b.NumOutputPorts=16;
b.SetPreCompInpPortInfoToDynamic;b.SetPreCompOutPortInfoToDynamic;
for k=1:6,b.InputPort(k).Dimensions=1;b.InputPort(k).DirectFeedthrough=true;b.InputPort(k).SamplingMode='Sample';end
for k=1:16,b.OutputPort(k).Dimensions=1;b.OutputPort(k).SamplingMode='Sample';end
b.SampleTimes=[b.DialogPrm(1).Data.Ts 0];b.SimStateCompliance='DefaultSimState';
b.RegBlockMethod('PostPropagationSetup',@states);b.RegBlockMethod('InitializeConditions',@init);
b.RegBlockMethod('Outputs',@outputs);b.RegBlockMethod('Update',@update);
end
function states(b)
b.NumDworks=4;names={'previousSpeed','acceleration','integral','previousRequest'};
for k=1:4,b.Dwork(k).Name=names{k};b.Dwork(k).Dimensions=1;b.Dwork(k).DatatypeID=0;b.Dwork(k).Complexity='Real';b.Dwork(k).UsedAsDiscState=true;end
end
function init(b)
b.Dwork(1).Data=10000;b.Dwork(2).Data=0;b.Dwork(3).Data=3;b.Dwork(4).Data=10000;
end
function [v,a,ei,pterm]=evaluate(b)
f=b.DialogPrm(1).Data;n=b.InputPort(1).Data;r=b.InputPort(2).Data;
temp=b.InputPort(5).Data;pressure=b.InputPort(6).Data;
p=exp(-f.Ts/f.accelTau);a=p*b.Dwork(2).Data+(1-p)*(n-b.Dwork(1).Data)/f.Ts;
ar=(r-b.Dwork(4).Data)/f.Ts;
X=[r 0 temp pressure;n a temp pressure;n 0 temp pressure;r ar temp pressure];
if f.mode==3,[mu,grad]=tmats_gp_mean_gradient(f,X);else,mu=tmats_gp_mean_gradient(f,X);grad=zeros(4,4);end
ev=mu(1)-mu(2);e0=mu(1)-mu(3);en=r-n;fallback=0;gn=grad(1,1);ga=grad(1,2);
if f.mode==1,ei=ev;pterm=f.Kp*ev;
elseif f.mode==2
 beta=1;if isfield(f,'accelWeight'),beta=f.accelWeight;end
 ei=e0;pterm=f.Kp*(e0-beta*(mu(2)-mu(3)));
else
 nc=n/sqrt(temp/288.15)/10000;
 fallback=double(gn<=1e-5 || ga<=1e-5 || nc<.5 || nc>1.05);
 if isfield(f,'forceFallback')&&f.forceFallback,fallback=1;end
 if fallback,ei=en;agp=a;
 else
  ei=e0/gn;agp=(mu(2)-mu(3))/ga;
  if abs(en)>.01 && (ei/en<.25 || ei/en>4),fallback=1;ei=en;agp=a;end
 end
 pterm=f.Kp*ei-f.Kd*agp;
end
u=mu(4)+pterm+b.Dwork(3).Data;command=max(f.fuelMin,min(f.fuelMax,u));
if b.CurrentTime<f.start,command=b.InputPort(4).Data;end
outside=any(any(bsxfun(@lt,X,f.model.trainingInputRange(1,:))|bsxfun(@gt,X,f.model.trainingInputRange(2,:))));
v=[command;mu(1:2);ev;a;b.Dwork(3).Data;u;double(outside);ei;pterm;gn;ga;fallback;ar;mu(4)-mu(1);mu(4)];
end
function outputs(b)
[v,~,~,~]=evaluate(b);for k=1:16,b.OutputPort(k).Data=v(k);end
end
function update(b)
f=b.DialogPrm(1).Data;[v,a,ei,pterm]=evaluate(b);
if b.CurrentTime<f.start,b.Dwork(3).Data=b.InputPort(4).Data-v(16)-pterm;
elseif (v(7)<f.fuelMax || ei<0) && (v(7)>f.fuelMin || ei>0)
 b.Dwork(3).Data=b.Dwork(3).Data+f.Ts*f.Ki*ei;
end
b.Dwork(1).Data=b.InputPort(1).Data;b.Dwork(2).Data=a;b.Dwork(4).Data=b.InputPort(2).Data;
end
