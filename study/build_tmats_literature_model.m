function build_tmats_literature_model()
% Add low-order observers using only Gain, Sum, Mux and Unit Delay blocks.
root=fileparts(mfilename('fullpath'));tmats_literature_setup();
src='GasTurbine_Dyn_Template_GPT_DOB_PTO';m=[src '_ALT'];
assert(~bdIsLoaded(src)&&~bdIsLoaded(m));
target=fullfile(root,[m '.mdl']);if exist(target,'file'),copyfile(target,[target '.bak']);end
load_system(src);set_param(src,'CloseFcn','');save_system(src,target);close_system(src,0);load_system(target);
set_param(m,'CloseFcn','','PreLoadFcn','tmats_literature_setup;', ...
 'Description','PI with existing DOB, LESO, UDE or ramp GPIO; basic blocks. See TMATS_LITERATURE_OBSERVER_COMPARISON.md.');
s=[m '/Data driven DOB'];p=get_param([s '/Observer variant'],'PortHandles');
l=get_param(p.Outport,'Line');dst=get_param(l,'DstPortHandle');delete_line(l);
add_block('built-in/Subsystem',[s '/Low order observer'],'Position',[440 470 660 580]);q=[s '/Low order observer'];
add_block('built-in/Inport',[q '/Speed deviation'],'Port','1','Position',[25 40 55 60]);
add_block('built-in/Inport',[q '/Fuel deviation'],'Port','2','Position',[25 110 55 130]);
add_block('simulink/Math Operations/Gain',[q '/Normalize speed'],'Gain','1/ALT.b0','Position',[90 35 165 65]);
add_block('simulink/Signal Routing/Mux',[q '/Measurements'],'Inputs','2','Position',[200 45 205 125]);
add_line(q,'Speed deviation/1','Normalize speed/1');add_line(q,'Normalize speed/1','Measurements/1');add_line(q,'Fuel deviation/1','Measurements/2');
add_block('simulink/Discrete/Unit Delay',[q '/Observer state'],'SampleTime','DOB.Ts','InitialCondition','ALT.x0','Position',[485 190 565 230]);
gain(q,'A state','ALT.Ad',[590 200 675 240]);gain(q,'B input','ALT.Bd',[260 125 340 165]);
gain(q,'C state','ALT.C',[590 45 675 85]);gain(q,'D speed only','ALT.D(1)',[270 35 350 75]);
add_block('simulink/Math Operations/Sum',[q '/State update'],'Inputs','++','Position',[400 190 425 230]);
add_block('simulink/Math Operations/Sum',[q '/Disturbance estimate'],'Inputs','++','Position',[720 40 745 80]);
add_line(q,'Measurements/1','B input/1');add_line(q,'Normalize speed/1','D speed only/1');
add_line(q,'Observer state/1','A state/1');add_line(q,'Observer state/1','C state/1');
add_line(q,'A state/1','State update/1');add_line(q,'B input/1','State update/2');add_line(q,'State update/1','Observer state/1');
add_line(q,'C state/1','Disturbance estimate/1');add_line(q,'D speed only/1','Disturbance estimate/2');
add_block('built-in/Outport',[q '/Equivalent fuel disturbance'],'Position',[800 45 830 65]);add_line(q,'Disturbance estimate/1','Equivalent fuel disturbance/1');
add_line(s,'Speed deviation/1','Low order observer/1');add_line(s,'Fuel deviation/1','Low order observer/2');
add_block('simulink/Sources/Constant',[s '/Use literature observer'],'Value','ALT.use','Position',[750 500 800 530]);
add_block('simulink/Signal Routing/Switch',[s '/Selected estimator'],'Criteria','u2 >= Threshold','Threshold','.5','Position',[875 450 915 525]);
add_line(s,'Low order observer/1','Selected estimator/1');add_line(s,'Use literature observer/1','Selected estimator/2');add_line(s,'Observer variant/1','Selected estimator/3');
p=get_param([s '/Selected estimator'],'PortHandles');for k=1:numel(dst),add_line(s,p.Outport,dst(k),'autorouting','on');end
try,Simulink.BlockDiagram.arrangeSystem(q);catch ME,fprintf('LAYOUT_NOTE %s\n',ME.message);end
try,Simulink.BlockDiagram.arrangeSystem(s);catch ME,fprintf('LAYOUT_NOTE %s\n',ME.message);end
assert(isempty(find_system(q,'BlockType','S-Function')),'Observer must not use S-functions.');
set_param(m,'AlgebraicLoopMsg','error');
set_param(m,'SimulationCommand','update');save_system(m,target);close_system(m,0);
fprintf('LITERATURE_MODEL_BUILT\n');
end
function gain(q,name,value,pos)
add_block('simulink/Math Operations/Gain',[q '/' name],'Gain',value,'Multiplication','Matrix(K*u)','Position',pos);
end
