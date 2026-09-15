function build_tmats_environment_controller()
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
Simulink.fileGenControl('set','CacheFolder',fullfile(root,'tmp','em'),'CodeGenFolder',fullfile(root,'tmp','em'),'createDir',true);
tmats_environment_controller_setup;
src='GasTurbine_Dyn_Template_VirtualFuelFF';m='GasTurbine_Dyn_EnvironmentGPR';
assert(~bdIsLoaded(src)&&~bdIsLoaded(m));load_system(src);set_param(src,'CloseFcn','');
save_system(src,fullfile(root,[m '.mdl']));close_system(src,0);load_system(m);
set_param(m,'CloseFcn','','PreLoadFcn','tmats_environment_controller_setup;', ...
 'Description','Exact inverse GPR with inlet T/P, speed and acceleration. Fixed Kp=2 Ki=30. Default: 4000m ISA+5 9500rpm 10 percent shaft load.');
tmats_environment_controller_setup;tmats_environment_patch(m);tmats_environment_vf_patch(m);
set_param(m,'SimulationCommand','update');save_system(m);close_system(m,0);
fprintf('ENVIRONMENT_CONTROLLER_MODEL_SAVED\n');
end
