function render_tmats_dob(out)
if nargin<1,out=strtrim(fileread('tmp/dob/latest_directory.txt'));end
tmats_dob_setup;m='GasTurbine_Dyn_Template_GPT_DOB';load_system(m);set_param(m,'CloseFcn','');
s=[m '/Data driven DOB'];open_system(s);set_param(s,'ZoomFactor','50');drawnow;
set_param(s,'PaperPositionMode','auto','PaperOrientation','landscape');
print(['-s' s],'-dpng','-r72',fullfile(out,'dob_blocks.png'));
close_system(m,0);fprintf('DOB_RENDER_SUCCESS\n');
end
