function run_tmats_dob98_tune()
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);out=fullfile(root,'results','dob98_pi_20261010');
Simulink.fileGenControl('set','CacheFolder',fullfile(root,'tmp','dob98_sim'),'CodeGenFolder',fullfile(root,'tmp','dob98_sim'),'createDir',true);
src='GasTurbine_Combined_base';m='GasTurbine_DOB98_PI';load_system(src);set_param(src,'CloseFcn','');save_system(src,fullfile(root,[m '.mdl']));close_system(src,0);load_system(m);
set_param(m,'CloseFcn','','PreLoadFcn','tmats_dob98_setup();');
set_param([m '/Simple PI controller'],'Kp_M','VF.Kp','Ki_M','VF.Ki');
sensor=[m '/1st order  Sensor'];assert(strcmp(get_param(sensor,'Tau_M'),'0.05'));assert(strcmp(get_param(sensor,'GN_EN_M'),'off'));
ports=get_param([m '/Simple PI controller'],'PortHandles');assert(strcmp(getfullname(get_param(get_param(ports.Inport(2),'Line'),'SrcBlockHandle')),sensor));
save_system(m);
gains=[.025 .05;.015 .025;.015 .05;.015 .1;.025 .025;.025 .1;.04 .025;.04 .05;.04 .1];
records=struct([]);
for j=1:size(gains,1),records=onecase(m,gains(j,:),j,records,out,false);end
[~,best]=min([records.objective]);g0=gains(best,:);
refine=[g0.*[.8 1];g0.*[1.2 1];g0.*[1 .8];g0.*[1 1.2]];
for j=1:4,records=onecase(m,refine(j,:),9+j,records,out,false);end
[~,best]=min([records.objective]);s=records(best);assert(isfinite(s.objective),'No valid candidate');
policy=struct('Kp',s.Kp,'Ki',s.Ki,'Kd',0,'case_index',s.case_index,'objective',s.objective,'DOB_gain',.7,'DOB_fc_Hz',1,'nominal_rpm',9800,'selection','minimum full-cycle RMSE + 0.05 times segmented excess fuel TV; selected on requested combined cycle');
fid=fopen(fullfile(out,'selected_policy.json'),'w');fwrite(fid,jsonencode(policy));fclose(fid);
copyfile(fullfile(out,sprintf('case_%02d.csv',s.case_index)),fullfile(out,'dobpi.csv'));
copyfile(fullfile(out,sprintf('case_%02d.mat',s.case_index)),fullfile(out,'dobpi.mat'));
% Frozen-gain robustness check: faster four-second ramp and half load.
onecase(m,[s.Kp s.Ki],100,struct([]),out,true);
tmats_dob98_setup();save_system(m);close_system(m,0);fprintf('DOB98_TUNING_DONE best=%d Kp=%g Ki=%g\n',s.case_index,s.Kp,s.Ki);
end
function records=onecase(m,g,j,records,out,validation)
file=fullfile(out,sprintf('case_%02d.mat',j));
if exist(file,'file'),old=load(file,'met');met=old.met;else
 [MWS,DOB,PTO,VF,ENV]=tmats_dob98_setup(g);
 if validation,DOB.rate=250;DOB.request=[0 10000;5 10000;10 9000;60 9000;64 10000;85.005 10000];PTO.profile(:,2)=PTO.profile(:,2)*.5;end
 in=Simulink.SimulationInput(m);vars={'MWS','DOB','PTO','VF','ENV'};for k=1:numel(vars),in=in.setVariable(vars{k},eval(vars{k}));end
 in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');
 fprintf('DOB98_TUNE_START %d Kp=%g Ki=%g\n',j,g(1),g(2));raw=sim(in);d=tmats_environment_data(raw);
 for name={'DOB_compensation','DOB_estimate'},v=raw.get(name{1});d.(name{1})=double(v.Data(:));end
 t=d.time_s-60;q=t>=-1e-8;e=d.Nmech-d.DOB_request;u=d.Wf;rampEnd=5;if validation,rampEnd=4;end
 accepted=all(d.valid)&&d.time_s(end)>=85;rmse=sqrt(mean(e(q).^2));ring=0;
 for bounds=[0 5 10 15;5 10 15 25.02],x=u(t>=bounds(1)-1e-8&t<bounds(2)-1e-8);if numel(x)>1,ring=ring+sum(abs(diff(x)))-abs(x(end)-x(1));end;end
 objective=rmse+.05*ring;if ~accepted,objective=inf;end
 met=struct('case_index',j,'Kp',g(1),'Ki',g(2),'accepted',accepted,'rmse_rpm',rmse,'fuel_excess_TV',ring,'objective',objective,'ramp_rmse_rpm',sqrt(mean(e(t>=0&t<rampEnd).^2)),'load_rmse_rpm',sqrt(mean(e(t>=10).^2)),'min_surge_margin',min(d.DOB_SM(q)),'peak_compensation',max(abs(d.DOB_compensation(q))));
 save(file,'d','met','MWS','DOB','PTO','VF','-v7.3');writetable(d,fullfile(out,sprintf('case_%02d.csv',j)));
 fprintf('DOB98_TUNE_DONE %d accepted=%d J=%g RMSE=%g\n',j,accepted,objective,rmse);
end
if isempty(records),records=met;else,records(end+1)=met;end
if validation,writetable(struct2table(records),fullfile(out,'heldout_validation.csv'));else,writetable(struct2table(records),fullfile(out,'tuning.csv'));end
end

