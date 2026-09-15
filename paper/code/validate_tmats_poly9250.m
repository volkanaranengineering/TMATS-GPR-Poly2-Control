function validate_tmats_poly9250(out)
% Frozen-gain transfer to half-amplitude load pulses; not used for selection.
s=load(fullfile(out,'selected.mat'),'gains');gains=[.025 .05 0;.025 .1 .002;s.gains];tr=load(fullfile(out,'trim.mat'),'reference_hp');
base='GasTurbine_PolyCompare_BasePI';poly='GasTurbine_PolyCompare_R3_Poly2FF';load_system(base);load_system(poly);set_param(base,'CloseFcn','');set_param(poly,'CloseFcn','');names={'base','original','tuned'};records=[];
for j=1:3
 [MWS,DOB,PTO,VF,ENV]=tmats_poly9250_setup(gains(j,:),tr.reference_hp);PTO.profile(:,2)=PTO.profile(:,2)/2;PTO.fraction=.05;m=poly;if j==1,m=base;end
 in=Simulink.SimulationInput(m);in=in.setVariable('MWS',MWS);in=in.setVariable('DOB',DOB);in=in.setVariable('PTO',PTO);in=in.setVariable('VF',VF);in=in.setVariable('ENV',ENV);in=in.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');raw=sim(in);d=tmats_environment_data(raw);
 if j>1,extra={'VR_integrator_error','VR_proportional_term','VR_speed_slope','VR_accel_slope','VR_fallback'};for k=1:5,v=raw.get(extra{k});d.(extra{k})=double(v.Data(:));end;end
 met=tmats_fixed_comparison_metrics(d,9250,[0 0 0],DOB);met.method=names{j};met.Kp=gains(j,1);met.Ki=gains(j,2);met.Kd=gains(j,3);
 save(fullfile(out,['validation_' names{j} '.mat']),'d','met','MWS','DOB','PTO','VF','ENV','-v7.3');writetable(d,fullfile(out,['validation_' names{j} '.csv']));if isempty(records),records=met;else,records(end+1)=met;end
 fprintf('POLY9250_VALIDATION %s accepted=%d RMSE=%g ring=%g\n',names{j},met.accepted,met.rmse_rpm,met.ringing_excess_TV_lbm_s);
end
writetable(struct2table(records),fullfile(out,'validation_summary.csv'));close_system(base,0);close_system(poly,0);
end
