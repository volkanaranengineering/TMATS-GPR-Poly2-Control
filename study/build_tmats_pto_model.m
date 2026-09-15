function build_tmats_pto_model()
% Route a real external mechanical power load to the Shaft power port.
root=fileparts(mfilename('fullpath'));[MWS,DOB,PTO]=tmats_pto_setup(); %#ok<ASGLU>
src='GasTurbine_Dyn_Template_GPT_DOB';m=[src '_PTO'];target=fullfile(root,[m '.mdl']);
assert(~bdIsLoaded(src)&&~bdIsLoaded(m),'Close the DOB and PTO models before building.');
if exist(target,'file'),copyfile(target,[target '.bak']);end
load_system(fullfile(root,[src '.mdl']));set_param(src,'CloseFcn','');
save_system(src,target);close_system(src,0);load_system(target);
set_param(m,'CloseFcn','','PreLoadFcn','tmats_pto_setup;', ...
 'Description','Steady 10000 rpm PI/DOB comparison with actual shaft power extraction. See TMATS_PTO_STUDY.md.');
add_block('simulink/Sources/From Workspace',[m '/Shaft power extraction'], ...
 'VariableName','PTO.profile','Interpolate','off','OutputAfterFinalValue','Holding final value', ...
 'SampleTime','PTO.Ts','Position',[180 1080 330 1120]);
parent=m;source='Shaft power extraction/1';
levels={'IterativeSolver and InnerLoopPlant','InnerLoopPlant','Engine'};
for k=1:numel(levels)
 child=[parent '/' levels{k}];
 ins=find_system(child,'SearchDepth',1,'BlockType','Inport');n=numel(ins)+1;
 add_block('built-in/Inport',[child '/PTO power hp'],'Port',num2str(n),'Position',[60 1050 90 1070]);
 add_line(parent,source,[levels{k} '/' num2str(n)],'autorouting','on');
 parent=child;source='PTO power hp/1';
end
ph=get_param([parent '/Shaft'],'PortHandles');l=get_param(ph.Inport(2),'Line');
old=get_param(l,'SrcBlockHandle');assert(strcmp(get_param(old,'BlockType'),'Constant'));
assert(str2double(get_param(old,'Value'))==0,'Existing shaft load is nonzero; preserve it explicitly.');
delete_line(l);delete_block(old);add_line(parent,source,'Shaft/2','autorouting','on');
add_block('simulink/Signal Routing/Bus Selector',[m '/PTO power diagnostics'], ...
 'OutputSignals','PlantBus.T_Data.Pwrout,PlantBus.C_Data.Pwrout','Position',[1300 1070 1310 1150]);
add_line(m,'IterativeSolver and InnerLoopPlant/1','PTO power diagnostics/1','autorouting','on');
names={'PTO_hp','PTO_turbine_hp','PTO_compressor_hp'};
sources={'Shaft power extraction/1','PTO power diagnostics/1','PTO power diagnostics/2'};
for k=1:3
 add_block('simulink/Sinks/To Workspace',[m '/' names{k}],'VariableName',names{k}, ...
 'SaveFormat','Timeseries','MaxDataPoints','inf','Position',[1380 1050+50*k 1530 1075+50*k]);
 add_line(m,sources{k},[names{k} '/1'],'autorouting','on');
end
set_param(m,'SimulationCommand','update');save_system(m,target);close_system(m,0);
fprintf('PTO_MODEL_BUILT\n');
end
