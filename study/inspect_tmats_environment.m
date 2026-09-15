try
 [MWS,DOB,PTO]=tmats_pto_setup(0,.1,9500,[0 0 0]);
 m='GasTurbine_Dyn_Template_GPT_DOB_PTO';load_system(m);set_param(m,'CloseFcn','');
 eng=[m '/IterativeSolver and InnerLoopPlant/InnerLoopPlant/Engine'];
 disp(get_param([eng '/Ambient'],'PortConnectivity'));
 disp(find_system([eng '/Ambient'],'LookUnderMasks','all','FollowLinks','on','BlockType','Inport'));
 MWS.in.SimTime=.03;in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setModelParameter('ReturnWorkspaceOutputs','on');r=sim(in);
 disp(r.who);disp(r.s2);close_system(m,0);
catch ME,disp(getReport(ME,'extended','hyperlinks','off'));exit(1);end
exit(0);
