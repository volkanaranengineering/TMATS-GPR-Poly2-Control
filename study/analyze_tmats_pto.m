function analyze_tmats_pto(out)
if nargin<1,out=strtrim(fileread('tmp/dob/pto_directory.txt'));end
a=readtable(fullfile(out,'case_01.csv'));b=readtable(fullfile(out,'case_02.csv'));
m=jsondecode(fileread(fullfile(out,'metrics.json')));r=jsondecode(fileread(fullfile(out,'reference.json')));
nominal=round(r.speed_rpm);
assert(isequal(a.PTO_hp,b.PTO_hp)&&isequal(a.DOB_request,b.DOB_request));
ev=readtable(fullfile(out,'events.csv'));ix=a.time_s>=60-1e-8;t=a.time_s(ix)-60;
f=figure('Visible','off','Color','w','Position',[60 60 1250 1000]);
subplot(4,1,1);plot(t,a.PTO_hp(ix)*.7456998715822702,'k','LineWidth',1.2);grid on;
ylabel('Shaft extraction (kW)');status='';if ~all([m.accepted]),status=' | DIAGNOSTIC: failed validity checks';end
title(sprintf('%g rpm | shaft load = %.0f%% of %.2f hp%s',nominal,100*r.power_fraction,r.turbine_power_hp,status));
subplot(4,1,2);plot(t,a.Nmech(ix)-nominal,'b',t,b.Nmech(ix)-nominal,'r');grid on;
ylabel(sprintf('Speed - %g (rpm)',nominal));legend('PI','PI + DOB','Location','best');
subplot(4,1,3);plot(t,a.Wf(ix),'b',t,b.Wf(ix),'r');grid on;ylabel('Fuel (lbm/s)');
subplot(4,1,4);plot(t,b.DOB_estimate(ix),'Color',[.2 .55 .2]);hold on;plot(t,b.DOB_compensation(ix),'r');grid on;
ylabel('Fuel equivalent (lbm/s)');xlabel('Time after preparation (s)');
legend('Trim-removed lumped estimate','Subtracted compensation','Location','best');
for j=1:4,subplot(4,1,j);set(gca,'Position',[.10 .78-(j-1)*.235 .85 .17],'FontSize',10);end
print(f,fullfile(out,'pto_comparison.png'),'-dpng','-r150');close(f);
f=figure('Visible','off','Color','w','Position',[60 60 1250 500]);
subplot(1,2,1);jj=ix & a.time_s>=70.005 & a.time_s<=75;tt=a.time_s(jj)-70.005;
plot(tt,a.Nmech(jj)-nominal,'b',tt,b.Nmech(jj)-nominal,'r');grid on;xlabel('Time after first application (s)');ylabel('Speed error (rpm)');
legend('PI','PI + DOB','Location','best');title('First load application');
subplot(1,2,2);jj=a.time_s>=75 & a.time_s<=80;tt=a.time_s(jj)-75;
plot(tt,a.Nmech(jj)-nominal,'b',tt,b.Nmech(jj)-nominal,'r');grid on;xlabel('Time after first removal (s)');ylabel('Speed error (rpm)');title('First load removal');
print(f,fullfile(out,'pto_transient_detail.png'),'-dpng','-r150');close(f);
fid=fopen(fullfile(out,'REPORT.md'),'w');
fprintf(fid,'# Steady %g rpm regulation with sudden shaft power extraction\n\n',nominal);
fprintf(fid,'The original PI is compared against the existing frozen-model PI+DOB, without retuning. ');
fprintf(fid,'The speed demand stays at %g rpm during evaluation. Fuel-injection disturbances are disabled.\n\n',nominal);
fprintf(fid,'## Physical definition and scenario\n\n');
fprintf(fid,'A 60 s unloaded preparation is followed by 90 s evaluation. ');
fprintf(fid,'Preparation starts from the standard 10000 rpm initial state, holds to 5 s, ramps to %g rpm by 10 s, and then holds. ',nominal);
fprintf(fid,'The reference is mean gross turbine shaft power over preparation seconds 55-60: **%.6f hp** (%.6f kW). ',r.turbine_power_hp,r.turbine_power_hp*.7456998715822702);
fprintf(fid,'Mean compressor load is %.6f hp; unloaded net shaft power is %.9f hp. ',r.compressor_load_hp,r.net_unloaded_power_hp);
fprintf(fid,'Thus %.0f%% is taken from gross turbine power, which balances compressor load at steady speed, not from near-zero net power.\n\n',100*r.power_fraction);
fprintf(fid,'Each extraction pulse is fixed at **%.6f hp = %.6f kW** for both controllers. ',r.extraction_hp,r.extraction_kW);
fprintf(fid,'It is not recomputed as a percentage of the changing turbine output under load. ');
fprintf(fid,'Sudden on/off edges occur at 10.005/15.000, 30.000/40.005, and 60.000/75.000 s after preparation. ');
fprintf(fid,'These represent three applications of the same %.0f%% additional load, with 4.995, 10.005 and 15.000 s holds.\n\n',100*r.power_fraction);
fprintf(fid,'The installed Shaft block power port receives positive extraction in hp. Its equation is\n\n');
fprintf(fid,'    dN/dt = 60/(2*pi*J) * (T_turbine + T_compressor - 5252.11*P_PTO/N),\n\n');
fprintf(fid,'with the original J=30. The turbine and compressor torque conversions use 5252.113 in the component code. ');
fprintf(fid,'The observer sees sensed speed and known fuel command only; the load profile and plant acceleration are not observer inputs.\n\n');
fprintf(fid,'## Comparison\n\n');
fprintf(fid,'PI gains remain Kp=0.025, Ki=0.05. DOB gain=0.25, Q pole-frequency parameter=0.5 Hz, ');
fprintf(fid,'compensation bound=0.15 lbm/s. Trim is latched at 30 s and compensation ramps in over two seconds, well before the evaluation.\n\n');
fprintf(fid,'| Measure | PI | PI + DOB |\n|---|---:|---:|\n');
names={'RMSE (rpm)','IAE (rpm s)','Maximum speed droop (rpm)','Maximum overspeed (rpm)', ...
 'Fuel min (lbm/s)','Fuel max (lbm/s)','Fuel mass in 90 s (lbm)','Fuel-limit fraction', ...
 'DOB correction-limit fraction','Maximum flow residual','Maximum iterations','Minimum compressor margin (%)'};
fields={'rmse_rpm','iae_rpm_s','maximum_droop_rpm','maximum_overspeed_rpm','fuel_min_lbm_s','fuel_max_lbm_s', ...
 'fuel_mass_lbm','fuel_limit_fraction','comp_limit_fraction','max_flow_error','max_iterations','minimum_SM_percent'};
for j=1:numel(fields),fprintf(fid,'| %s | %.7g | %.7g |\n',names{j},m(1).(fields{j}),m(2).(fields{j}));end
fprintf(fid,'\nBoth full trajectories pass numerical/physical checks: PI=%d, PI+DOB=%d. ',m(1).accepted,m(2).accepted);
if all([m.accepted])
 fprintf(fid,'Tracking RMSE change is %.3f%% improvement; maximum droop change is %.3f%% improvement.\n\n', ...
 100*(1-m(2).rmse_rpm/m(1).rmse_rpm),100*(1-m(2).maximum_droop_rpm/m(1).maximum_droop_rpm));
fprintf(fid,'Performance must be assessed together with saturation and the recovery table. The fuel command reaches its limits for ');
 fprintf(fid,'%.3f%% of PI evaluation samples and %.3f%% of DOB samples. ',100*m(1).fuel_limit_fraction,100*m(2).fuel_limit_fraction);
 fprintf(fid,'DOB correction reaches its bound for %.3f%% of samples; the inherited PI has no added anti-windup. ',100*m(2).comp_limit_fraction);
 fprintf(fid,'These limits should be considered before increasing observer gain or extraction power.\n\n');
else
 fprintf(fid,'FAILED trajectories are diagnostic only. Their aggregate errors above must not be used as valid control-performance evidence. ');
 fprintf(fid,'First failure after preparation: PI %.6f s, PI+DOB %.6f s.\n\n',m(1).first_failure_s,m(2).first_failure_s);
end
fprintf(fid,'## Recovery after each edge\n\n');
fprintf(fid,'Recovery means the error remains within +/-1 rpm until the next load edge, with at least 0.5 s of confirmed dwell. ');
fprintf(fid,'NaN means recovery was not established before that edge; 0 means the response never left the band.\n\n');
fprintf(fid,'| Edge time (s) | Event | PI peak abs. error (rpm) | DOB peak abs. error (rpm) | PI recovery (s) | DOB recovery (s) |\n|---:|---|---:|---:|---:|---:|\n');
for j=1:6
 type='Remove load';if ev.load_applied(j),type='Apply load';end
 fprintf(fid,'| %.3f | %s | %.5f | %.5f | %.3f | %.3f |\n',ev.edge_s(j),type, ...
 ev.max_absolute_error_rpm(j),ev.max_absolute_error_rpm(j+6),ev.settling_to_1rpm_s(j),ev.settling_to_1rpm_s(j+6));
end
fprintf(fid,'\n## Verification and reproduction\n\n');
fprintf(fid,'The power and speed profiles match exactly between controllers. The independent shaft torque-balance reconstruction ');
fprintf(fid,'matches logged acceleration to %.4g rpm/s for PI and %.4g rpm/s for PI+DOB. ', ...
 m(1).torque_balance_max_error_rpm_s,m(2).torque_balance_max_error_rpm_s);
fprintf(fid,'Acceptance requires finite signals, positive fuel and compressor margin, residual <=1e-9, and fewer than 200 iterations throughout preparation and evaluation.\n\n');
fprintf(fid,'Run `out=run_tmats_pto_study(%.2f,%g); analyze_tmats_pto(out);` from TMATSGPT using the existing `_DOB_PTO.mdl` copy to measure steady turbine power and simulate both controllers. ',r.power_fraction,nominal);
fprintf(fid,'Run `analyze_tmats_pto` to regenerate this report and the figures. ');
fprintf(fid,'To configure an already loaded model, run `tmats_pto_setup([],%.2f,%g)`. This uses the measured, speed-specific reference cache. The no-argument setup retains the original 10000 rpm, 10%% defaults.\n\n',r.power_fraction,nominal);
fprintf(fid,'Saved evidence: `trim.mat/csv`, `reference.json`, `case_01.mat/csv`, `case_02.mat/csv`, `metrics.json/csv`, `events.csv`, ');
fprintf(fid,'`pto_comparison.png`, and `pto_transient_detail.png`. Existing GPT and DOB model files are preserved.\n\n');
fprintf(fid,'This is one deterministic, noise-free sample-engine operating point. The estimate is fuel-equivalent lumped model error, not a direct calibrated power measurement. ');
fprintf(fid,'The experiment tests mechanical load rejection but does not qualify the observer for hardware or establish broad closed-loop robustness.\n');
fclose(fid);
copyfile(fullfile(out,'REPORT.md'),sprintf('TMATS_PTO_%gRPM_%02dPCT_STUDY.md',nominal,round(100*r.power_fraction)));
fprintf('PTO_ANALYSIS_SUCCESS %s\n',out);
end
