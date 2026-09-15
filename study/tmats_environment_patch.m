function tmats_environment_patch(m)
% In-memory changes only; preserve all existing saved controller models.
eng=[m '/IterativeSolver and InnerLoopPlant/InnerLoopPlant/Engine'];
b=[eng '/Constant'];pos=get_param(b,'Position');
delete_line(eng,'Constant/1','Ambient/3');delete_block(b);
add_block('simulink/Sources/From Workspace',b,'VariableName','ENV.profile', ...
 'Interpolate','on','SampleTime','-1','OutputAfterFinalValue','Holding final value','Position',pos);
add_line(eng,'Constant/1','Ambient/3');
end
