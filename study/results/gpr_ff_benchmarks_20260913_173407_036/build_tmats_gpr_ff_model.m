function build_tmats_gpr_ff_model()
root=fileparts(mfilename('fullpath'));tmats_gpr_ff_setup;
src='GasTurbine_Dyn_Template_GPT_DOB_PTO_ALT';m='GasTurbine_Dyn_Template_GPR_FF';
assert(~bdIsLoaded(src)&&~bdIsLoaded(m),'Close the source and FF models before building.');
load_system(fullfile(root,[src '.mdl']));set_param(src,'CloseFcn','');
save_system(src,fullfile(root,[m '.mdl']));close_system(src,0);load_system(m);
set_param(m,'CloseFcn','','PreLoadFcn','tmats_gpr_ff_setup;', ...
 'Description','Existing PI plus inverse exact GPR feedforward. No disturbance preview. See TMATS_GPR_FF_COMPARISON.md.');
q=[m '/Inverse GPR feedforward'];add_block('built-in/Subsystem',q,'Position',[300 1170 550 1280]);
add_block('built-in/Inport',[q '/Sensed speed'],'Port','1','Position',[25 35 55 55]);
add_block('built-in/Inport',[q '/Governed reference'],'Port','2','Position',[25 95 55 115]);
add_block('simulink/User-Defined Functions/Level-2 MATLAB S-Function',[q '/Exact inverse GP'], ...
 'FunctionName','tmats_gpr_ff_sfun','Parameters','FF','Position',[130 30 320 170]);
add_line(q,'Sensed speed/1','Exact inverse GP/1');add_line(q,'Governed reference/1','Exact inverse GP/2');
names={'Correction','Nominal fuel','Reference acceleration','Queried speed','Speed guard active'};
logs={'GPR_FF','GPR_nominalFuel','GPR_referenceAcceleration','GPR_querySpeed','GPR_speedGuard'};
for k=1:5
 add_block('built-in/Outport',[q '/' names{k}],'Port',num2str(k),'Position',[400 25+40*k 430 45+40*k]);
 add_line(q,['Exact inverse GP/' num2str(k)],[names{k} '/1']);
 add_block('simulink/Sinks/To Workspace',[m '/' logs{k}],'VariableName',logs{k}, ...
 'SaveFormat','Timeseries','MaxDataPoints','inf','Position',[700 1150+45*k 860 1175+45*k]);
 add_line(m,['Inverse GPR feedforward/' num2str(k)],[logs{k} '/1'],'autorouting','on');
end
add_line(m,'1st order  Sensor/1','Inverse GPR feedforward/1','autorouting','on');
add_line(m,'Speed demand governor/1','Inverse GPR feedforward/2','autorouting','on');
delete_line(m,'PI minus DOB/1','Fuel command limits/1');
add_block('simulink/Math Operations/Sum',[m '/PI plus GPR FF'],'Inputs','++','Position',[700 310 725 350]);
add_line(m,'PI minus DOB/1','PI plus GPR FF/1');
add_line(m,'Inverse GPR feedforward/1','PI plus GPR FF/2','autorouting','on');
add_line(m,'PI plus GPR FF/1','Fuel command limits/1','autorouting','on');
set_param(m,'AlgebraicLoopMsg','error');set_param(m,'SimulationCommand','update');
save_system(m);close_system(m,0);fprintf('GPR_FF_MODEL_BUILT\n');
end
