function run_tmats_environment_comparison(out,indices)
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);
cache=fullfile(root,'tmp',sprintf('ec%02d',indices(1)));
Simulink.fileGenControl('set','CacheFolder',cache,'CodeGenFolder',cache,'createDir',true);
s=load(fullfile(out,'environment_inverse_gpr_model.mat'),'model');model=s.model;
[aa,dd]=ndgrid([0 2500 5000 7500 10000],[0 -10 10 20 -20 30 -30]);grid=[aa(:) dd(:);4000 5];
[MWS,DOB,PTO,VF]=tmats_virtual_fuel_ff_setup(9500,.1,[0 0 0],[2 30],true);[MWS,ENV]=tmats_environment_config(MWS,0,0);
base='GasTurbine_Dyn_Template_GPT_DOB_PTO';inv='GasTurbine_Dyn_Template_VirtualFuelFF';
load_system(base);load_system(inv);set_param(base,'CloseFcn','');set_param(inv,'CloseFcn','');
cleanup=onCleanup(@()closeboth(base,inv));tmats_environment_patch(base);tmats_environment_patch(inv);tmats_environment_vf_patch(inv);
metrics=[];
for c=indices
 fprintf('COMPARE_ENVIRONMENT_START %d altitude=%g ISA=%g\n',c,grid(c,:));
 trimFile=fullfile(out,sprintf('trim_%02d.mat',c));
 if exist(trimFile,'file'),z=load(trimFile);reference_hp=z.reference_hp;
 else
  [MWS,DOB,PTO]=tmats_pto_setup(0,.1,9500,[0 0 0]);DOB.gain=0;MWS.in.SimTime=60;
  [MWS,ENV]=tmats_environment_config(MWS,grid(c,1),grid(c,2));
  raw=simulate(base,MWS,DOB,PTO,ENV,[]);d=tmats_environment_data(raw);ix=d.time_s>=55;
  reference_hp=mean(d.PTO_turbine_hp(ix));assert(isfinite(reference_hp)&&reference_hp>0);
  save(trimFile,'d','reference_hp','MWS','DOB','PTO','ENV','-v7.3');
 end
 methods={'BasePI','InvGPR_PI_GPRFF'};if c==36,methods{3}='InvGPR_PI';end
 for j=1:numel(methods)
  file=fullfile(out,sprintf('comparison_%02d_%s.mat',c,methods{j}));
  if exist(file,'file'),z=load(file,'met');met=z.met;
  else
   started=tic;[MWS,DOB,PTO]=tmats_pto_setup(reference_hp,.1,9500,[0 0 0]);DOB.gain=0;
   [MWS,ENV]=tmats_environment_config(MWS,grid(c,1),grid(c,2));
   if j==1,m=base;vf=[];kp=.025;ki=.05;
   else
    m=inv;vf=VF;vf.model=rmfield(model,{'L','Z','trainingRows'});vf.scaledTraining=bsxfun(@rdivide,model.Z,model.lengthScale');
    vf.feedforward=double(j==2);vf.start=45;vf.Kp=2;vf.Ki=30;kp=2;ki=30;
   end
   raw=simulate(m,MWS,DOB,PTO,ENV,vf);d=tmats_environment_data(raw);
   assert(height(d)==10001 && max(abs(d.PTO_hp-PTO.profile(:,2)))<1e-7);
   met=tmats_fixed_comparison_metrics(d,9500,[0 0 0],DOB);
   met.environment=c;met.altitude_m=grid(c,1);met.isa_delta_C=grid(c,2);met.method=methods{j};met.Kp=kp;met.Ki=ki;
   met.reference_hp=reference_hp;met.load_hp=.1*reference_hp;met.wall_seconds=toc(started);
   ix=d.time_s>=60;met.compressor_Nc_outside_percent=100*mean(d.compressor_Nc_outside(ix));
   met.inlet_temperature_K=mean(d.inlet_temperature_K(ix));met.inlet_pressure_kPa=mean(d.inlet_pressure_kPa(ix));
   met.gp_replay_error=0;met.gp_outside_percent=0;
   if j>1
    q=find(d.valid&ix);q=q(unique(round(linspace(1,numel(q),min(100,numel(q))))));
    if isempty(q),met.gp_replay_error=NaN;
    else
     X=[d.DOB_sensed(q) d.VF_acceleration(q) d.inlet_temperature_K(q) d.inlet_pressure_kPa(q)];
     gp=predict_tmats_environment_gpr(model,X);met.gp_replay_error=max(abs(gp-d.VF_feedback(q)));assert(met.gp_replay_error<1e-6);
    end
    active=d.valid&d.time_s>=45;
    assert(max(abs(d.VF_unsaturated(active)-vf.feedforward*d.VF_setpoint(active)-kp*d.VF_error(active)-d.VF_integral(active)))<1e-9);
    met.gp_outside_percent=100*mean(d.VF_outside(ix));
   end
   save(file,'d','met','MWS','DOB','PTO','ENV','vf','-v7.3');writetable(d,strrep(file,'.mat','.csv'));
   fprintf('COMPARE_DONE env=%d %s accepted=%d RMSE=%g ring=%g NcOutside=%.1f wall=%.1f\n',c,methods{j},met.accepted,met.rmse_rpm,met.ringing_excess_TV_lbm_s,met.compressor_Nc_outside_percent,met.wall_seconds);
  end
  if isempty(metrics),metrics=met;else,metrics(end+1)=met;end
  writetable(struct2table(metrics),fullfile(out,sprintf('comparison_worker_%02d.csv',indices(1))));
 end
end
end
function raw=simulate(m,MWS,DOB,PTO,ENV,VF)
in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('ENV',ENV);
if ~isempty(VF),in=in.setVariable('VF',VF);end
in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');raw=sim(in);
end
function closeboth(a,b)
if bdIsLoaded(a),close_system(a,0);end;if bdIsLoaded(b),close_system(b,0);end
end
