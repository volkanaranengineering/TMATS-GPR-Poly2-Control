function run_tmats_ramp90()
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
out=fullfile(root,'results','pilco_ramp90_100_5s_20261010');if ~exist(out,'dir'),mkdir(out);end
Simulink.fileGenControl('set','CacheFolder',fullfile(root,'tmp','ramp90_sim'),'CodeGenFolder',fullfile(root,'tmp','ramp90_sim'),'createDir',true);
methods={'base','poly','previous','smooth'};
sources={'GasTurbine_PolyCompare_BasePI','GasTurbine_PolyCompare_R3_Poly2FF','GasTurbine_PILCO_Quadratic_PI','GasTurbine_PILCO_Smooth_PI'};
records=[];
for k=1:4
 method=methods{k};src=sources{k};m=['GasTurbine_Ramp90_' method];
 load_system(src);set_param(src,'CloseFcn','');save_system(src,fullfile(root,[m '.mdl']));close_system(src,0);load_system(m);
 set_param(m,'CloseFcn','','PreLoadFcn',sprintf('tmats_ramp90_setup(''%s'');',method));
 block=find_system(m,'BlockType','FromWorkspace','VariableName','DOB.request');assert(numel(block)==1);set_param(block{1},'Interpolate','on');
 if isempty(find_system(m,'SearchDepth',1,'Name','Validity signals')),tmats_remedy_stop_invalid(m);end
 save_system(m);
 [MWS,DOB,PTO,VF,ENV]=tmats_ramp90_setup(method);
 in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('VF',VF);in=in.setVariable('ENV',ENV);in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');
 fprintf('RAMP90_START %s\n',method);raw=sim(in);d=tmats_environment_data(raw);
 if k==2
  fields={'VR_fallback','VR_integrator_error','VR_proportional_term'};
  for j=1:numel(fields),v=raw.get(fields{j});d.(fields{j})=double(v.Data(:));end
 end
 q=d.time_s>=60;ramp=q & d.time_s<65;prep=d.time_s>=55 & d.time_s<60;
 expected=9000+200*max(0,min(5,d.time_s-60));
 met=struct('method',method,'accepted',all(d.valid)&&d.time_s(end)>=80&&max(abs(d.Nmech(prep)-9000))<.1, ...
 'request_error_rpm',max(abs(d.DOB_request(q)-expected(q))), ...
 'max_external_load_hp',max(abs(d.PTO_hp)), ...
 'ramp_rmse_rpm',sqrt(mean((d.Nmech(ramp)-d.DOB_request(ramp)).^2)), ...
 'evaluation_rmse_rpm',sqrt(mean((d.Nmech(q)-d.DOB_request(q)).^2)), ...
 'minimum_surge_margin_percent',min(d.DOB_SM(q)),'Kp',VF.Kp,'Ki',VF.Ki,'Kd',VF.Kd);
 save(fullfile(out,[method '.mat']),'d','met','MWS','DOB','PTO','VF','ENV','-v7.3');writetable(d,fullfile(out,[method '.csv']));
 if isempty(records),records=met;else,records(end+1)=met;end;writetable(struct2table(records),fullfile(out,'simulation_summary.csv'));
 fprintf('RAMP90_DONE %s accepted=%d rampRMSE=%g requestError=%g\n',method,met.accepted,met.ramp_rmse_rpm,met.request_error_rpm);
 close_system(m,0);
end
end
