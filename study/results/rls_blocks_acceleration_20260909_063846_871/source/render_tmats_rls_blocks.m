function render_tmats_rls_blocks(out)
mdl='GasTurbine_Dyn_Template_GPT_RLS_Blocks';
load_system(mdl); sub=[mdl '/RLS Acceleration Observer'];
systems={sub,[sub '/RLS matrix arithmetic'],[sub '/Validity and update gate']};
names={'observer_blocks.png','rls_matrix_blocks.png','validity_gate_blocks.png'};
for k=1:3
    open_system(systems{k}); set_param(systems{k},'ZoomFactor','FitSystem'); drawnow;
    print(['-s' systems{k}],'-dpng','-r72',fullfile(out,names{k}));
end
end

