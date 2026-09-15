function tmats_environment_vf_patch(m)
set_param([m '/Virtual fuel PI'],'FunctionName','tmats_environment_vf_sfun');
add_block('simulink/Signal Routing/Bus Selector',[m '/Inlet measurements'], ...
 'OutputSignals','PlantBus.s2.Tt,PlantBus.s2.Pt','Position',[1000 1250 1005 1340]);
add_line(m,'IterativeSolver and InnerLoopPlant/1','Inlet measurements/1','autorouting','on');
names={'Temperature K','Pressure kPa'};factors={'1/1.8','6.894757293168'};initial={'288.15','99.298'};
for k=1:2
 add_block('simulink/Math Operations/Gain',[m '/' names{k}],'Gain',factors{k},'Position',[1050 1200+70*k 1100 1230+70*k]);
 add_block('simulink/Discrete/Unit Delay',[m '/' names{k} ' sampled'], ...
  'SampleTime','VF.Ts','InitialCondition',initial{k},'Position',[1150 1200+70*k 1200 1230+70*k]);
 add_line(m,['Inlet measurements/' num2str(k)],[names{k} '/1'],'autorouting','on');
 add_line(m,[names{k} '/1'],[names{k} ' sampled/1'],'autorouting','on');
 add_line(m,[names{k} ' sampled/1'],['Virtual fuel PI/' num2str(k+4)],'autorouting','on');
end
end
