function run_tmats_r3_cycle(out,covered,compareFF,comparePoly)
if nargin<2,covered=false;end
if nargin<3,compareFF=false;end
if nargin<4,comparePoly=false;end
if comparePoly,assert(covered&&compareFF);end
root=fileparts(mfilename('fullpath'));cd(root);addpath(root);if ~exist(out,'dir'),mkdir(out);end
Simulink.fileGenControl('set','CacheFolder',fullfile(root,'tmp','r3cycle'),'CodeGenFolder',fullfile(root,'tmp','r3cycle'),'createDir',true);
sources={'GasTurbine_Dyn_Template_GPT_DOB_PTO','GasTurbine_Remedy3'};
names={'BasePI','R3'};metrics=[];
if compareFF,sources{3}='GasTurbine_Remedy3';names{3}='R3_GPRFF';end
if comparePoly,sources{4}='GasTurbine_Remedy3';names{4}='R3_Poly2FF';end
for j=1:numel(names)
 src=sources{j};load_system(src);set_param(src,'CloseFcn','');
 prefix='GasTurbine_Cycle_';setup='tmats_r3_cycle_setup';
 if covered,prefix='GasTurbine_Covered_';setup='tmats_r3_covered_cycle_setup';end
 if compareFF,prefix='GasTurbine_FFCompare_';end
 if comparePoly,prefix='GasTurbine_PolyCompare_';end
 if j==4,setup='tmats_r3_poly2_setup';end
 m=[prefix names{j}];save_system(src,fullfile(root,[m '.mdl']));close_system(src,0);load_system(m);
 if j==1,tmats_environment_patch(m);end
 if j==3
  set_param([m '/Virtual fuel PI'],'FunctionName','tmats_gpr_remedy_sfun');
 end
 if compareFF&&j==2,set_param([m '/Virtual fuel PI'],'FunctionName','tmats_r3_feedback_only_sfun');end
 if j==4,set_param([m '/Virtual fuel PI'],'FunctionName','tmats_r3_poly2_sfun');end
 set_param(m,'CloseFcn','','PreLoadFcn',[setup ';'],'Description','120 s speed-ramp and ambient cycle. See the cycle study usage notes.');
 [MWS,DOB,PTO,VF,ENV]=feval(setup);set_param(m,'SimulationCommand','update');save_system(m);
 tmats_remedy_stop_invalid(m);
 in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('VF',VF);in=in.setVariable('ENV',ENV);
 in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');fprintf('CYCLE_START %s\n',names{j});raw=sim(in);d=tmats_environment_data(raw);
 if j>=2
  extra={'VR_integrator_error','VR_proportional_term','VR_speed_slope','VR_accel_slope','VR_fallback'};
  for k=1:numel(extra),v=raw.get(extra{k});d.(extra{k})=double(v.Data(:));end
  if compareFF,d.FF_total=zeros(height(d),1);if j>=3,d.FF_total=d.VF_setpoint;end;end
 end
 rel=d.time_s-60;d.altitude_m=interp1([0 60 120],[0 10000 0],max(0,rel));d.isa_delta_C=interp1([0 60 120],[-20 20 0],max(0,rel));
 assert(max(abs(d.PTO_hp))==0);
 request_error=max(abs(d.DOB_request-DOB.request(1:height(d),2)));
 fprintf('REQUEST_CHECK %s max_error=%g\n',names{j},request_error);
 if request_error>=1e-7,save(fullfile(out,[names{j} '_request_diagnostic.mat']),'d','DOB','MWS','ENV','-v7.3');writetable(d,fullfile(out,[names{j} '_request_diagnostic.csv']));end
 assert(request_error<1e-7);
 [met,segments]=cycle_metrics(d,names{j});
 save(fullfile(out,[names{j} '.mat']),'d','met','segments','MWS','DOB','PTO','VF','ENV','-v7.3');writetable(d,fullfile(out,[names{j} '.csv']));writetable(segments,fullfile(out,[names{j} '_segments.csv']));
 if isempty(metrics),metrics=met;else,metrics(end+1)=met;end
 writetable(struct2table(metrics),fullfile(out,'summary.csv'));
 fprintf('CYCLE_DONE %s accepted=%d RMSE=%g ring=%g\n',names{j},met.accepted,met.rmse_rpm,met.segment_excess_TV_lbm_s);close_system(m,0);
end
end
function [m,S]=cycle_metrics(d,name)
q=d.time_s>=60;trim=d.time_s>=55&d.time_s<60;e=d.Nmech-d.DOB_request;
m=struct('method',name,'accepted',all(d.valid)&&d.time_s(end)>=180-1e-9&&max(abs(e(trim)))<.1, ...
 'rmse_rpm',NaN,'ramp_rmse_rpm',NaN,'hold_rmse_rpm',NaN,'peak_error_rpm',NaN,'iae_rpm_s',NaN, ...
 'segment_excess_TV_lbm_s',NaN,'hold_excess_TV_lbm_s',NaN,'max_recovery_1pct_s',NaN,'holds_not_recovered',NaN, ...
 'minimum_SM_percent',min(d.DOB_SM(q)),'fuel_peak_lbm_s',max(d.Wf(q)), ...
 'max_fuel_slew_lbm_s2',max(abs(diff(d.Wf(q))))/.015,'Nc_outside_percent',100*mean(d.compressor_Nc_outside(q)), ...
 'fallback_percent',NaN,'gp_outside_percent',NaN);
if ismember('VR_fallback',d.Properties.VariableNames),m.fallback_percent=100*mean(d.VR_fallback(q));m.gp_outside_percent=100*mean(d.VF_outside(q));end
rows=[];
for k=0:15
 cycle=floor(k/4);part=mod(k,4);edges=[0 5 15 20 30]+30*cycle;a=edges(part+1);b=edges(part+2);
 ix=d.time_s>=60+a-1e-8&d.time_s<60+b-1e-8;names={'acceleration','high hold','deceleration','low hold'};
 z=struct('segment',k+1,'start_s',a,'end_s',b,'type',names{part+1},'rmse_rpm',NaN,'peak_rpm',NaN,'excess_TV_lbm_s',NaN,'recovery_1pct_s',NaN);
 if m.accepted
  f=d.Wf(ix);z.rmse_rpm=sqrt(mean(e(ix).^2));z.peak_rpm=max(abs(e(ix)));z.excess_TV_lbm_s=max(0,sum(abs(diff(f)))-abs(f(end)-f(1)));
  if mod(part,2)==1
   ii=find(ix);last=find(abs(e(ii))>.01*d.DOB_request(ii),1,'last');z.recovery_1pct_s=0;
   if ~isempty(last),if last==numel(ii),z.recovery_1pct_s=Inf;else,z.recovery_1pct_s=d.time_s(ii(last+1))-60-a;end;end
  end
 end
 if isempty(rows),rows=z;else,rows(end+1)=z;end
end
S=struct2table(rows);
if ~m.accepted,return;end
phase=mod(max(0,d.time_s-60),30);ramp=q&(phase<5|(phase>=15&phase<20));hold=q&~ramp;
m.rmse_rpm=sqrt(mean(e(q).^2));m.ramp_rmse_rpm=sqrt(mean(e(ramp).^2));m.hold_rmse_rpm=sqrt(mean(e(hold).^2));m.peak_error_rpm=max(abs(e(q)));m.iae_rpm_s=sum(abs(e(q)))*.015;
m.segment_excess_TV_lbm_s=sum(S.excess_TV_lbm_s);m.hold_excess_TV_lbm_s=sum(S.excess_TV_lbm_s(2:2:end));m.max_recovery_1pct_s=max(S.recovery_1pct_s(2:2:end));m.holds_not_recovered=sum(isinf(S.recovery_1pct_s(2:2:end)));
end
