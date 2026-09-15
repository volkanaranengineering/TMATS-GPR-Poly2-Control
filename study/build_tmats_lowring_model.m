function build_tmats_lowring_model()
root=fileparts(mfilename('fullpath'));tmats_lowring_setup;
src='GasTurbine_Dyn_Template_VirtualFuelFF';m='GasTurbine_Dyn_Template_LowRinging';
assert(~bdIsLoaded(src)&&~bdIsLoaded(m));load_system(src);
save_system(src,fullfile(root,[m '.mdl']));close_system(src,0);load_system(m);
set_param(m,'PreLoadFcn','tmats_lowring_setup;','CloseFcn','', ...
 'Description','Fixed inverse-GPR virtual-fuel PI + FF, Kp=2 Ki=30. 9500 rpm 5% steps. See the Controller Tutorial PDF.');
tmats_lowring_setup;set_param(m,'SimulationCommand','update');save_system(m);close_system(m,0);
end
