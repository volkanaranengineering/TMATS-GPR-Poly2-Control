function identify_tmats_dob98()
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
out=fullfile(root,'results','dob98_pi_20261010');if ~exist(out,'dir'),mkdir(out);end
Simulink.fileGenControl('set','CacheFolder',fullfile(root,'tmp','dob98_sim'),'CodeGenFolder',fullfile(root,'tmp','dob98_sim'),'createDir',true);
src='GasTurbine_Combined_base';m='GasTurbine_DOB98_Identification';load_system(src);set_param(src,'CloseFcn','');save_system(src,fullfile(root,[m '.mdl']));close_system(src,0);load_system(m);set_param(m,'CloseFcn','','PreLoadFcn','');
for test=1:2
 [MWS,DOB,PTO,VF,ENV]=tmats_combined_setup('base');
 DOB.request=[0 10000;5 10000;10 9800;100.005 9800];PTO.profile=[0 0;100.005 0];DOB.gain=0;
 t=(0:round(100.005/DOB.Ts))'*DOB.Ts;rel=t-60;d=zeros(size(t));q=rel>=0 & rel<30;
 if test==1
  rng(9800);bits=2*(rand(1,200)>.5)-1;d(q)=.035*bits(1+floor(rel(q)/.18));
 else
  d(q)=.025*sin(2*pi*.37*rel(q))+.015*sin(2*pi*1.17*rel(q));
 end
 DOB.disturbance=[t d];MWS.in.SimTime=t(end);
 in=Simulink.SimulationInput(m);vars={'MWS','DOB','PTO','VF','ENV'};for j=1:numel(vars),in=in.setVariable(vars{j},eval(vars{j}));end
 in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');
 fprintf('IDENTIFY98_START %d\n',test);raw=sim(in);data=tmats_environment_data(raw);
 assert(all(data.valid)&&data.time_s(end)>=100,'Invalid identification simulation');
 writetable(data,fullfile(out,sprintf('identification_%d.csv',test)));save(fullfile(out,sprintf('identification_%d.mat',test)),'data','MWS','DOB','PTO','-v7.3');
 fprintf('IDENTIFY98_DONE %d range=%g..%g\n',test,min(data.Nmech(data.time_s>=60)),max(data.Nmech(data.time_s>=60)));
end
save_system(m);close_system(m,0);
end
