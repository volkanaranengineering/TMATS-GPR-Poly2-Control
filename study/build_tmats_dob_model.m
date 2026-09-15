function build_tmats_dob_model()
% Observer uses ordinary Simulink arithmetic and discrete transfer-function blocks.
root=fileparts(mfilename('fullpath')); [MWS,DOB]=tmats_dob_setup(); %#ok<ASGLU>
src='GasTurbine_Dyn_Template_GPT'; m=[src '_DOB'];
assert(~bdIsLoaded(src)&&~bdIsLoaded(m),'Close the source and DOB models before building.');
target=fullfile(root,[m '.mdl']);
if exist(target,'file'),copyfile(target,[target '.bak']);end
load_system(fullfile(root,[src '.mdl']));set_param(src,'CloseFcn','');
save_system(src,target);close_system(src,0);load_system(target);
set_param(m,'CloseFcn','','PreLoadFcn','tmats_dob_setup;', ...
 'Description','Frozen sparse ARX disturbance observer extension; see TMATS_DOB_STUDY.md.');
% Replace speed command source, preserving its consumers.
b=[m '/Model Source1'];p=get_param(b,'PortHandles');l=get_param(p.Outport,'Line');dst=get_param(l,'DstPortHandle');
delete_line(l);delete_block(b);
add_block('simulink/Sources/From Workspace',b,'VariableName','DOB.request', ...
 'Interpolate','off','OutputAfterFinalValue','Holding final value','SampleTime','DOB.Ts','Position',[140 180 265 210]);
add_block('simulink/Discontinuities/Rate Limiter',[m '/Speed demand governor'], ...
 'RisingSlewLimit','DOB.rate','FallingSlewLimit','-DOB.rate','InitialCondition','10000', ...
 'Position',[300 180 405 210]);
add_line(m,'Model Source1/1','Speed demand governor/1');
p=get_param([m '/Speed demand governor'],'PortHandles');
for k=1:numel(dst),add_line(m,p.Outport,dst(k),'autorouting','on');end
% Interpose compensation and a shared fuel limit after the unchanged PI.
p=get_param([m '/Simple PI controller'],'PortHandles');l=get_param(p.Outport,'Line');dst=get_param(l,'DstPortHandle');delete_line(l);
add_block('simulink/Math Operations/Sum',[m '/PI minus DOB'],'Inputs','+-','Position',[675 280 700 310]);
add_block('simulink/Discontinuities/Saturation',[m '/Fuel command limits'], ...
 'UpperLimit','DOB.fuelMax','LowerLimit','DOB.fuelMin','Position',[750 280 855 310]);
add_block('simulink/Math Operations/Sum',[m '/Unknown fuel disturbance'],'Inputs','++','Position',[905 280 930 310]);
add_block('simulink/Sources/From Workspace',[m '/Disturbance test source'], ...
 'VariableName','DOB.disturbance','SampleTime','DOB.Ts','Interpolate','off', ...
 'OutputAfterFinalValue','Holding final value','Position',[740 375 870 405]);
add_line(m,'Simple PI controller/1','PI minus DOB/1');add_line(m,'PI minus DOB/1','Fuel command limits/1');
add_line(m,'Fuel command limits/1','Unknown fuel disturbance/1');add_line(m,'Disturbance test source/1','Unknown fuel disturbance/2');
p=get_param([m '/Unknown fuel disturbance'],'PortHandles');
for k=1:numel(dst),add_line(m,p.Outport,dst(k),'autorouting','on');end
set_param(get_param(p.Outport,'Line'),'Name','Wf');
s=[m '/Data driven DOB'];add_block('built-in/Subsystem',s,'Position',[485 500 780 655],'BackgroundColor','lightBlue');
add_block('built-in/Inport',[s '/Sensed speed'],'Port','1','Position',[25 60 55 80]);
add_block('built-in/Inport',[s '/Known fuel command'],'Port','2','Position',[25 290 55 310]);
add_block('simulink/Math Operations/Bias',[s '/Speed deviation'],'Bias','-DOB.N0','Position',[90 50 180 90]);
add_block('simulink/Math Operations/Bias',[s '/Fuel deviation'],'Bias','-DOB.u0','Position',[90 280 180 320]);
add_line(s,'Sensed speed/1','Speed deviation/1');add_line(s,'Known fuel command/1','Fuel deviation/1');
dtf(s,'Causal Q over nominal plant','DOB.InvNum','DOB.InvDen',[225 35 410 85]);
dtf(s,'Q known fuel','DOB.Qnum','DOB.Qden',[225 120 410 160]);
add_line(s,'Speed deviation/1','Causal Q over nominal plant/1');add_line(s,'Fuel deviation/1','Q known fuel/1');
add_block('simulink/Math Operations/Sum',[s '/Input disturbance estimate'],'Inputs','+-','Position',[460 65 485 115]);
add_line(s,'Causal Q over nominal plant/1','Input disturbance estimate/1');add_line(s,'Q known fuel/1','Input disturbance estimate/2');
dtf(s,'ARX output residual','DOB.ResY','[1 zeros(1,length(DOB.ResY)-1)]',[220 220 405 260]);
dtf(s,'ARX input residual','DOB.ResU','[1 zeros(1,length(DOB.ResU)-1)]',[220 310 405 350]);
add_line(s,'Speed deviation/1','ARX output residual/1');add_line(s,'Fuel deviation/1','ARX input residual/1');
add_block('simulink/Math Operations/Sum',[s '/Equation 4_13 residual'],'Inputs','+-','Position',[460 240 485 290]);
add_line(s,'ARX output residual/1','Equation 4_13 residual/1');add_line(s,'ARX input residual/1','Equation 4_13 residual/2');
dtf(s,'Residual Q','DOB.ResQnum','DOB.ResQden',[525 245 620 280]);add_line(s,'Equation 4_13 residual/1','Residual Q/1');
add_block('simulink/Sources/Constant',[s '/Mode'],'Value','DOB.mode','Position',[555 155 595 185]);
add_block('simulink/Signal Routing/Switch',[s '/Observer variant'],'Criteria','u2 >= Threshold','Threshold','1.5','Position',[680 85 720 165]);
add_line(s,'Input disturbance estimate/1','Observer variant/1');add_line(s,'Mode/1','Observer variant/2');add_line(s,'Residual Q/1','Observer variant/3');
% Latch the last pre-engagement residual to remove the local trim bias.
add_block('simulink/Sources/Step',[s '/Latch trim at engagement'],'Time','DOB.start', ...
 'Before','0','After','1','SampleTime','DOB.Ts','Position',[550 395 595 425]);
add_block('simulink/Signal Routing/Switch',[s '/Track then hold trim'], ...
 'Criteria','u2 >= Threshold','Threshold','.5','Position',[680 355 720 415]);
add_block('simulink/Discrete/Unit Delay',[s '/Trim memory'], ...
 'SampleTime','DOB.Ts','InitialCondition','0','Position',[780 370 830 410]);
add_line(s,'Trim memory/1','Track then hold trim/1');
add_line(s,'Latch trim at engagement/1','Track then hold trim/2');
add_line(s,'Observer variant/1','Track then hold trim/3');
add_line(s,'Track then hold trim/1','Trim memory/1');
add_block('simulink/Math Operations/Sum',[s '/Remove trim bias'],'Inputs','+-','Position',[745 175 770 205]);
add_line(s,'Observer variant/1','Remove trim bias/1');add_line(s,'Trim memory/1','Remove trim bias/2');
add_block('simulink/Math Operations/Gain',[s '/Compensation gain'],'Gain','DOB.gain','Position',[760 100 825 140]);
add_line(s,'Remove trim bias/1','Compensation gain/1');
add_block('simulink/Discontinuities/Saturation',[s '/Compensation limit'], ...
 'UpperLimit','DOB.compLimit','LowerLimit','-DOB.compLimit','Position',[865 100 965 140]);
add_line(s,'Compensation gain/1','Compensation limit/1');
add_block('simulink/Sources/Ramp',[s '/Enable after preparation'],'start','DOB.start', ...
 'slope','1/DOB.enableTime','InitialOutput','0','Position',[785 205 830 235]);
add_block('simulink/Discontinuities/Saturation',[s '/Enable ramp limit'], ...
 'UpperLimit','1','LowerLimit','0','Position',[860 205 940 235]);
add_line(s,'Enable after preparation/1','Enable ramp limit/1');
add_block('simulink/Math Operations/Product',[s '/Enable compensation'],'Position',[1005 125 1040 165]);
add_line(s,'Compensation limit/1','Enable compensation/1');add_line(s,'Enable ramp limit/1','Enable compensation/2');
add_block('built-in/Outport',[s '/Compensation'],'Port','1','Position',[1095 130 1125 150]);
add_block('built-in/Outport',[s '/Estimate'],'Port','2','Position',[780 30 810 50]);
add_line(s,'Enable compensation/1','Compensation/1');add_line(s,'Remove trim bias/1','Estimate/1');
add_line(m,'1st order  Sensor/1','Data driven DOB/1','autorouting','on');
add_line(m,'Fuel command limits/1','Data driven DOB/2','autorouting','on');
add_line(m,'Data driven DOB/1','PI minus DOB/2','autorouting','on');
add_block('simulink/Signal Routing/Bus Selector',[m '/DOB plant checks'], ...
 'OutputSignals','PlantBus.Ndot,PlantErrors,PlantBus.Iter,PlantBus.C_Data.SMavail','Position',[1260 635 1270 780]);
add_line(m,'IterativeSolver and InnerLoopPlant/1','DOB plant checks/1','autorouting','on');
names={'DOB_acceleration','DOB_flowErrors','DOB_iterations','DOB_SM'};
for k=1:4,sink(m,names{k},['DOB plant checks/' num2str(k)],1350,600+55*k);end
names={'DOB_rawRequest','DOB_request','DOB_sensed','DOB_PI','DOB_command','DOB_disturbance','DOB_compensation','DOB_estimate'};
sources={'Model Source1/1','Speed demand governor/1','1st order  Sensor/1','Simple PI controller/1', ...
 'Fuel command limits/1','Disturbance test source/1','Data driven DOB/1','Data driven DOB/2'};
for k=1:numel(names),sink(m,names{k},sources{k},800+170*mod(k,3),840+50*floor((k-1)/3));end
add_block('simulink/Signal Routing/Mux',[m '/Speed scope channels'],'Inputs','2','Position',[360 660 365 710]);
add_line(m,'Speed demand governor/1','Speed scope channels/1','autorouting','on');
add_line(m,'1st order  Sensor/1','Speed scope channels/2','autorouting','on');
add_block('simulink/Sinks/Scope',[m '/Applied demand and sensed speed'],'Position',[400 670 470 710]);
add_line(m,'Speed scope channels/1','Applied demand and sensed speed/1');
Simulink.BlockDiagram.arrangeSystem(s);
set_param(m,'SimulationCommand','update');save_system(m,target);close_system(m,0);
fprintf('DOB_MODEL_BUILT\n');
end
function dtf(s,n,b,a,p)
add_block('simulink/Discrete/Discrete Transfer Fcn',[s '/' n],'Numerator',b,'Denominator',a, ...
 'SampleTime','DOB.Ts','Position',p);
end
function sink(m,n,src,x,y)
add_block('simulink/Sinks/To Workspace',[m '/' n],'VariableName',n,'SaveFormat','Timeseries', ...
 'MaxDataPoints','inf','Position',[x y x+135 y+25]);add_line(m,src,[n '/1'],'autorouting','on');
end
