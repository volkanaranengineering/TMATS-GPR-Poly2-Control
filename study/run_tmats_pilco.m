function run_tmats_pilco()
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
out=fullfile(root,'results','pilco_quadratic_pi_20261010');
Simulink.fileGenControl('set','CacheFolder',fullfile(root,'tmp','pilco_sim'),'CodeGenFolder',fullfile(root,'tmp','pilco_sim'),'createDir',true);
src='GasTurbine_PolyCompare_R3_Poly2FF';m='GasTurbine_PILCO_Quadratic_PI';
load_system(src);set_param(src,'CloseFcn','');save_system(src,fullfile(root,[m '.mdl']));close_system(src,0);
load_system(m);set_param(m,'CloseFcn','','PreLoadFcn','tmats_pilco_setup;','Description','PILCO-style learned PI with frozen quadratic feedforward; 9250 rpm benchmark.');
blocks=find_system(m,'LookUnderMasks','all','FollowLinks','on','FunctionName','tmats_r3_poly2_sfun');assert(numel(blocks)==1);set_param(blocks{1},'FunctionName','tmats_pilco_pi_sfun');save_system(m);
tmats_remedy_stop_invalid(m);records=[];
for k=1:3
 [MWS,DOB,PTO,VF,ENV]=tmats_pilco_setup();
 names={'pilco_10pct','pilco_5pct','seed_pi_10pct'};
 if k==2,PTO.profile(:,2)=PTO.profile(:,2)/2;PTO.fraction=.05;end
 if k==3,VF.Kp=.025;VF.Ki=.05;end
 in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('VF',VF);in=in.setVariable('ENV',ENV);in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');
 fprintf('PILCO_SIM_START %s\n',names{k});raw=sim(in);d=tmats_environment_data(raw);
 met=tmats_fixed_comparison_metrics(d,9250,[0 0 0],DOB);met.method=names{k};met.Kp=VF.Kp;met.Ki=VF.Ki;met.Kd=0;
 save(fullfile(out,[names{k} '.mat']),'d','met','MWS','DOB','PTO','VF','ENV','-v7.3');writetable(d,fullfile(out,[names{k} '.csv']));
 if isempty(records),records=met;else,records(end+1)=met;end
 writetable(struct2table(records),fullfile(out,'simulation_summary.csv'));
 fprintf('PILCO_SIM_DONE %s accepted=%d RMSE=%g ring=%g\n',names{k},met.accepted,met.rmse_rpm,met.ringing_excess_TV_lbm_s);
end
close_system(m,0);
end
