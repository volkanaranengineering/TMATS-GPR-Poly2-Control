function build_tmats_gpr_remedy_models()
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
Simulink.fileGenControl('set','CacheFolder',fullfile(root,'tmp','rm'),'CodeGenFolder',fullfile(root,'tmp','rm'),'createDir',true);
src='GasTurbine_Dyn_Template_VirtualFuelFF';
for mode=1:3
 m=sprintf('GasTurbine_Remedy%d',mode);assert(~bdIsLoaded(src)&&~bdIsLoaded(m));
 load_system(src);set_param(src,'CloseFcn','');save_system(src,fullfile(root,[m '.mdl']));close_system(src,0);load_system(m);
 set_param(m,'CloseFcn','','PreLoadFcn',sprintf('tmats_gpr_remedy_setup(%d);',mode),'Description',sprintf('Inverse-GPR remedy %d. Frozen target-selected controller. See TMATS_GPR_REMEDIES_USAGE.md.',mode));
 tmats_gpr_remedy_setup(mode);tmats_environment_patch(m);tmats_environment_vf_patch(m);set_param([m '/Virtual fuel PI'],'FunctionName','tmats_gpr_remedy_sfun');
 extra={'VR_integrator_error','VR_proportional_term','VR_speed_slope','VR_accel_slope','VR_fallback'};
 for k=1:5
  add_block('simulink/Sinks/To Workspace',[m '/' extra{k}],'VariableName',extra{k},'SaveFormat','Timeseries','MaxDataPoints','inf','Position',[1300 1150+40*k 1440 1170+40*k]);
  add_line(m,['Virtual fuel PI/' num2str(k+8)],[extra{k} '/1'],'autorouting','on');
 end
 set_param(m,'SimulationCommand','update');save_system(m);close_system(m,0);
end
fprintf('THREE_REMEDY_MODELS_SAVED\n');
end
