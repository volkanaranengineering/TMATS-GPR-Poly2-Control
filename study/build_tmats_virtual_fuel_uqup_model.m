function build_tmats_virtual_fuel_uqup_model()
root=fileparts(mfilename('fullpath'));tmats_virtual_fuel_uqup_setup;
src='GasTurbine_Dyn_Template_GPT_DOB_PTO';m='GasTurbine_Dyn_Template_VirtualFuelUQUp';
assert(~bdIsLoaded(src)&&~bdIsLoaded(m));load_system(fullfile(root,[src '.mdl']));set_param(src,'CloseFcn','');
save_system(src,fullfile(root,[m '.mdl']));close_system(src,0);load_system(m);
set_param(m,'CloseFcn','','PreLoadFcn','tmats_virtual_fuel_uqup_setup;', ...
 'Description','Inverse-GPR feedforward plus uncertainty-scheduled fuel PI. See TMATS_VIRTUAL_FUEL_UQUP_USAGE.md.');
add_block('simulink/User-Defined Functions/Level-2 MATLAB S-Function',[m '/Virtual fuel PI'], ...
 'FunctionName','tmats_virtual_fuel_uqup_sfun','Parameters','VF','Position',[350 1170 600 1380]);
add_block('simulink/Sources/Constant',[m '/Acceleration setpoint'],'Value','0','Position',[130 1300 230 1330]);
add_line(m,'1st order  Sensor/1','Virtual fuel PI/1','autorouting','on');
add_line(m,'Speed demand governor/1','Virtual fuel PI/2','autorouting','on');
add_line(m,'Acceleration setpoint/1','Virtual fuel PI/3','autorouting','on');
add_line(m,'Simple PI controller/1','Virtual fuel PI/4','autorouting','on');
delete_line(m,'PI minus DOB/1','Fuel command limits/1');
add_block('simulink/Sinks/Terminator',[m '/Unused observer path'],'Position',[710 365 730 385]);
add_line(m,'PI minus DOB/1','Unused observer path/1','autorouting','on');
add_line(m,'Virtual fuel PI/1','Fuel command limits/1','autorouting','on');
names={'VF_command','VF_setpoint','VF_feedback','VF_error','VF_acceleration','VF_integral','VF_unsaturated','VF_outside','VF_sdSetpoint','VF_sdFeedback','VF_gainFactor','VF_Kp','VF_Ki'};
for k=1:numel(names)
 add_block('simulink/Sinks/To Workspace',[m '/' names{k}],'VariableName',names{k},'SaveFormat','Timeseries','MaxDataPoints','inf','Position',[750 1130+45*k 920 1155+45*k]);
 add_line(m,['Virtual fuel PI/' num2str(k)],[names{k} '/1'],'autorouting','on');
end
set_param(m,'AlgebraicLoopMsg','error');set_param(m,'SimulationCommand','update');save_system(m);close_system(m,0);
end



