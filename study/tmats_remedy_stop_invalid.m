function tmats_remedy_stop_invalid(m)
% Stop a rejected experiment; this is study instrumentation, not control action.
add_block('simulink/Signal Routing/Mux',[m '/Validity signals'],'Inputs','3','Position',[1500 300 1505 430]);
names={'DOB_flowErrors','DOB_SM','DOB_iterations'};
for k=1:3
 conv=[m '/Validity double ' num2str(k)];
 add_block('simulink/Signal Attributes/Data Type Conversion',conv,'OutDataTypeStr','double','Position',[1400 280+50*k 1440 310+50*k]);
 pc=get_param([m '/' names{k}],'PortConnectivity');src=get_param(pc.SrcBlock,'PortHandles');dest=get_param(conv,'PortHandles');
 add_line(m,src.Outport(pc.SrcPort+1),dest.Inport,'autorouting','on');
 add_line(m,['Validity double ' num2str(k) '/1'],['Validity signals/' num2str(k)],'autorouting','on');
end
add_block('built-in/MATLABFcn',[m '/Reject invalid state'], ...
 'MATLABFcn','tmats_remedy_invalid_state(u)','OutputDimensions','1','Position',[1550 340 1700 380]);
add_block('simulink/Sinks/Stop Simulation',[m '/Stop rejected experiment'],'Position',[1750 340 1790 380]);
add_line(m,'Validity signals/1','Reject invalid state/1');add_line(m,'Reject invalid state/1','Stop rejected experiment/1');
end
