function run_tmats_environment_data(out,indices)
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
cache=fullfile(root,'tmp',sprintf('environment_data_%02d',indices(1)));
Simulink.fileGenControl('set','CacheFolder',cache,'CodeGenFolder',cache,'createDir',true);
[aa,dd]=ndgrid([0 2500 5000 7500 10000],[0 -10 10 20 -20 30 -30]);
grid=[aa(:) dd(:)];
[MWS,DOB,PTO]=tmats_pto_setup(0,.1,9500,[0 0 0]);[MWS,ENV]=tmats_environment_config(MWS,0,0);
m='GasTurbine_Dyn_Template_GPT_DOB_PTO';load_system(m);set_param(m,'CloseFcn','');
cleanup=onCleanup(@()close_system(m,0));tmats_environment_patch(m);
for j=indices
 file=fullfile(out,sprintf('environment_%02d.mat',j));if exist(file,'file'),continue;end
 fprintf('ENVIRONMENT_START %d altitude=%g ISA=%g\n',j,grid(j,:));started=tic;
 [MWS,DOB,PTO]=tmats_pto_setup(0,.1,9500,[0 0 0]);DOB.gain=0;
 [MWS,ENV]=tmats_environment_config(MWS,grid(j,1),grid(j,2));
 t=(0:10000)'*DOB.Ts;q=max(0,t-40);
 n=9500+150*sin(2*pi*.025*q)+100*sin(2*pi*.065*q);
 n(t<40)=interp1([0 5 10 40],[10000 10000 9500 9500],t(t<40));
 u=zeros(size(t));ix=t>=40 & t<90;u(ix)=.025*sin(2*pi*.7*q(ix))+.012*sin(2*pi*1.13*q(ix));
 ix=t>=100;n(ix)=9500+170*sin(2*pi*.031*(t(ix)-100)) +70*sin(2*pi*.081*(t(ix)-100));
 u(ix)=.023*sin(2*pi*.57*(t(ix)-100))+.01*sin(2*pi*.93*(t(ix)-100));
 DOB.request(:,2)=n;DOB.disturbance(:,2)=u;
 in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('ENV',ENV);
 in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');raw=sim(in);d=tmats_environment_data(raw);
 config=struct('grid_index',j,'altitude_m',grid(j,1),'isa_delta_C',grid(j,2),'wall_seconds',toc(started));
 save(file,'d','config','MWS','ENV','DOB','PTO','-v7.3');writetable(d,fullfile(out,sprintf('environment_%02d.csv',j)));
 fprintf('ENVIRONMENT_DONE %d validTrain=%d validTest=%d wall=%.1f\n',j,sum(d.valid&d.time_s>=45&d.time_s<90),sum(d.valid&d.time_s>=105),config.wall_seconds);
end
end
