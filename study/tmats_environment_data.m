function d=tmats_environment_data(raw)
d=table(raw.Nmech.Time(:),'VariableNames',{'time_s'});
fields={'Nmech','Wf','DOB_request','DOB_sensed','DOB_PI','DOB_command','DOB_disturbance', ...
 'DOB_acceleration','DOB_SM','DOB_iterations','PTO_hp','PTO_turbine_hp','PTO_compressor_hp'};
available=raw.who;
vf={'VF_command','VF_setpoint','VF_feedback','VF_error','VF_acceleration','VF_integral','VF_unsaturated','VF_outside'};
if ismember('VF_command',available),fields=[fields vf];end
for k=1:numel(fields),v=raw.get(fields{k});d.(fields{k})=double(v.Data(:));end
d.inlet_temperature_K=double(raw.s2.Tt.Data(:))/1.8;
d.inlet_pressure_kPa=double(raw.s2.Pt.Data(:))*6.894757293168;
d.max_flow_error=max(abs(reshape(raw.DOB_flowErrors.Data,height(d),[])),[],2);
d.valid=all(isfinite(d{:,:}),2)&d.Wf>0&d.max_flow_error<=1e-9&d.DOB_iterations<200&d.DOB_SM>0;
d.compressor_NcMap=d.Nmech./sqrt(d.inlet_temperature_K/288.15)/10000;
d.compressor_Nc_outside=d.compressor_NcMap<.5 | d.compressor_NcMap>1.05;
end
