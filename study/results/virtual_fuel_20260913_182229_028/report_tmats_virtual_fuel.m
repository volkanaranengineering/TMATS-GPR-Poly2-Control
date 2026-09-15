function report_tmats_virtual_fuel(out)
% Create comparison figures and a standalone numerical report from saved runs.
if nargin<1,out=strtrim(fileread(fullfile('tmp','virtual_fuel_directory.txt')));end
T=readtable(fullfile(out,'summary.csv'));s=load(fullfile(out,'selected_gains.mat'));
P=T(strcmp(T.method,'PI'),:);V=T(strcmp(T.method,'VirtualFuel'),:);
assert(height(P)==10&&height(V)==10);
comparison=P(:,{'rpm','fraction','shape'});
comparison.PI_valid=P.accepted;comparison.VF_valid=V.accepted;
comparison.PI_RMSE=P.rmse_rpm;comparison.VF_RMSE=V.rmse_rpm;
comparison.RMSE_improvement_percent=100*(1-V.rmse_rpm./P.rmse_rpm);
comparison.PI_peak=P.peak_rpm;comparison.VF_peak=V.peak_rpm;
comparison.peak_improvement_percent=100*(1-V.peak_rpm./P.peak_rpm);
comparison.PI_IAE=P.iae_rpm_s;comparison.VF_IAE=V.iae_rpm_s;
writetable(comparison,fullfile(out,'comparison.csv'));
failures=[];
for k=1:height(T)
 if T.accepted(k),continue;end
 tag=sprintf('%drpm_%02dpct_%s_%s.mat',T.rpm(k),round(100*T.fraction(k)),T.shape{k},T.method{k});z=load(fullfile(out,tag));
 bad=find(~z.d.valid,1);if isempty(bad),continue;end
 r=struct('rpm',T.rpm(k),'fraction',T.fraction(k),'shape',T.shape{k},'method',T.method{k}, ...
  'first_failure_eval_s',z.d.time_s(bad)-60,'flow_error',z.d.max_flow_error(bad),'iterations',z.d.DOB_iterations(bad),'surge_margin',z.d.DOB_SM(bad));
 if isempty(failures),failures=r;else,failures(end+1)=r;end
end
if ~isempty(failures),writetable(struct2table(failures),fullfile(out,'failure_details.csv'));end
for rpm=[9000 9500]
 f=figure('Visible','off','Color','w','Position',[30 30 1300 850]);
 for c=1:4
  fraction=[.05 .1 .2 .3];tag=sprintf('%drpm_%02dpct_ramps_',rpm,round(100*fraction(c)));
  p=load(fullfile(out,[tag 'PI.mat']));v=load(fullfile(out,[tag 'VirtualFuel.mat']));
  p.d=plotprefix(p.d);v.d=plotprefix(v.d);
  subplot(4,2,2*c-1);plot(p.d.time_s-60,p.d.Nmech-rpm,'Color',[.55 .55 .55]);hold on;
  plot(v.d.time_s-60,v.d.Nmech-rpm,'b');grid on;xlim([0 90]);ylabel('Speed error [rpm]');title(sprintf('%g rpm, %g%% load',rpm,100*fraction(c)));
  if c==1,legend('Original PI','Virtual-fuel PI','Location','best');end
  subplot(4,2,2*c);plot(p.d.time_s-60,p.d.Wf,'Color',[.55 .55 .55]);hold on;plot(v.d.time_s-60,v.d.Wf,'b');
  grid on;xlim([0 90]);ylabel('Fuel [lbm/s]');
 end
 xlabel('Time after preparation [s]');print(f,fullfile(out,sprintf('comparison_%drpm.png',rpm)),'-dpng','-r140');close(f);
end
f=figure('Visible','off','Color','w','Position',[30 30 1200 750]);
v=load(fullfile(out,'9000rpm_30pct_ramps_VirtualFuel.mat'));d=v.d;t=d.time_s-60;
subplot(3,1,1);plot(t,d.VF_setpoint,t,d.VF_feedback);legend('Virtual setpoint','Virtual feedback');ylabel('Virtual fuel [lbm/s]');grid on;xlim([0 90]);
subplot(3,1,2);plot(t,d.VF_error);ylabel('Fuel-domain error [lbm/s]');grid on;xlim([0 90]);
subplot(3,1,3);plot(t,d.DOB_command,t,d.VF_integral);legend('Command','Integral');ylabel('Fuel [lbm/s]');xlabel('Time after preparation [s]');grid on;xlim([0 90]);
print(f,fullfile(out,'virtual_fuel_signals.png'),'-dpng','-r140');close(f);
f=figure('Visible','off','Color','w','Position',[30 30 1200 780]);
p=load(fullfile(out,'9500rpm_20pct_steps_PI.mat'));v=load(fullfile(out,'9500rpm_20pct_steps_VirtualFuel.mat'));
fields={'Nmech','Wf','DOB_SM'};labels={'Speed error [rpm]','Fuel [lbm/s]','Surge margin [%]'};
for k=1:3
 subplot(3,1,k);a=p.d.(fields{k});b=v.d.(fields{k});if k==1,a=a-9500;b=b-9500;end
 plot(p.d.time_s-60,a,'Color',[.55 .55 .55]);hold on;plot(v.d.time_s-60,b,'b');grid on;xlim([8 20]);ylabel(labels{k});
 if k==1,title('9500 rpm, 20% abrupt load: speed response and fuel / margin tradeoff');legend('Original PI','Virtual-fuel PI');end
end
xlabel('Time after preparation [s]');print(f,fullfile(out,'step_tradeoff.png'),'-dpng','-r140');close(f);
fid=fopen(fullfile(out,'REPORT.md'),'w');cl=onCleanup(@()fclose(fid));
fprintf(fid,'# Dual inverse-GPR virtual-fuel PI study\n\n');
fprintf(fid,'Selected **Kp = %g**, **Ki = %g 1/s**. Original speed PI: Kp = 0.025, Ki = 0.05. The new gains act on fuel error and are not numerically comparable to speed-domain gains.\n\n',s.gains);
fprintf(fid,'At 9000 rpm, the mean reduction in ramp-case RMSE is %.2f%%. At 9500 rpm, speed tracking also improves on valid comparison cases, but the 20%% abrupt-load test reduces minimum surge margin to %.3f%%. Full-run comparisons below exclude invalid cases.\n\n',mean(comparison.RMSE_improvement_percent(P.rpm==9000)),V.minimum_margin_percent(V.rpm==9500 & V.fraction==.2 & strcmp(V.shape,'steps')));
fprintf(fid,'The same frozen inverse GP computes g(Nsp,0) and g(Ns,estimated acceleration). Their difference drives a discrete PI, with its integral initialized by tracking the startup controller until 30 s. No original speed PI or GPR feedforward is added after handover. Feedback acceleration is estimated causally from sensed speed with a 0.03 s low-pass filter. Sampling interval is 0.015 s. Fuel limits are 0.2 to 4 lbm/s, with conditional-integration anti-windup.\n\n');
theoryFile=fullfile(fileparts(mfilename('fullpath')),'TMATS_VIRTUAL_FUEL_THEORY.md');
fprintf(fid,'%s\n\n',fileread(theoryFile));
fprintf(fid,'## Tuning outcome and evaluation split\n\n');
fprintf(fid,'A %d-pair grid was evaluated at 9000 rpm only, using 5/10/20/30%% ramp loads. A failed physical-validity case disqualifies a candidate and permits early rejection. Objective: equally weighted mean of each case RMSE divided by its original-PI RMSE. Selected objective: %.6f. Gains were frozen before all 9500-rpm runs. This is a finite search, not a claim of globally optimal tuning. Full candidate results are in tuning.csv. The reported 9000-rpm ramp cases are tuning-set performance; 9500-rpm cases test transfer to another operating point.\n\n',size(s.grid,1),s.best);
fprintf(fid,'All cases use the previous benchmark profiles: 60 s preparation plus 90 s evaluation, three pulses, 0.3/1.5/3 s ramps (or steps), and load scaled to the unloaded turbine power at each speed. Scores use actual shaft speed error. Invalid runs have no full-run performance score.\n\n');
fprintf(fid,'## Numerical local gain equivalents\n\n');
fprintf(fid,'Linearizing the GP gives e_virtual approximately cN*e_speed + cA*d(e_speed)/dt when the acceleration setpoint is consistent with the speed reference. Thus the fuel-domain PI acts locally like a speed-domain PID: Kd = Kp*cA, proportional gain = Kp*cN + Ki*cA, and integral gain = Ki*cN. The implemented derivative filter and sampling modify this ideal continuous-time interpretation. This explains why the new PI can change transient damping as well as integral action.\n\n');
root=fileparts(mfilename('fullpath'));gpmodel=load(fullfile(root,'results','inverse_gpr_20260913_150824_698','inverse_gpr_model.mat'),'model');
fprintf(fid,'| rpm | cN [lbm/s/rpm] | cA [lbm/s/(rpm/s)] | local speed Kp | local speed Ki | local speed Kd |\n|---:|---:|---:|---:|---:|---:|\n');
for rpm=[9000 9500]
 fval=predict_tmats_inverse_gpr(gpmodel.model,[rpm+1;rpm-1;rpm;rpm],[0;0;1;-1]);cn=(fval(1)-fval(2))/2;ca=(fval(3)-fval(4))/2;
 fprintf(fid,'| %g | %.6g | %.6g | %.6g | %.6g | %.6g |\n',rpm,cn,ca,s.gains(1)*cn+s.gains(2)*ca,s.gains(2)*cn,s.gains(1)*ca);
end
fprintf(fid,'\nCentral differences use +/-1 rpm or +/-1 rpm/s around zero acceleration. The 9000-rpm derivative includes a query below the training boundary.\n\n## Disturbance comparison\n\n');
fprintf(fid,'| rpm | load | shape | PI RMSE | VF RMSE | RMSE reduction | PI peak | VF peak |\n|---:|---:|:---|---:|---:|---:|---:|---:|\n');
for k=1:height(P)
 fprintf(fid,'| %g | %g%% | %s | %.4f | %.4f | %.2f%% | %.4f | %.4f |\n',P.rpm(k),100*P.fraction(k),P.shape{k},P.rmse_rpm(k),V.rmse_rpm(k),comparison.RMSE_improvement_percent(k),P.peak_rpm(k),V.peak_rpm(k));
end
fprintf(fid,'\nRMSE and peak are rpm; positive reduction means improvement. IAE values are in comparison.csv.\n\n');
step=find(P.rpm==9500 & P.fraction==.2 & strcmp(P.shape,'steps'));
fprintf(fid,'## Fuel and surge-margin tradeoff\n\n');
fprintf(fid,'For the 9500-rpm 20%% step-load case, speed RMSE changes from %.3f to %.3f rpm, but peak fuel rises from %.3f to %.3f lbm/s and minimum compressor surge margin decreases from %.3f%% to %.3f%%. This test passes the positive-margin criterion but leaves much less headroom. The selected gains minimize ramp-disturbance speed RMSE at 9000 rpm; they do not optimize surge margin or establish safe operation under untested uncertainties.\n\n',P.rmse_rpm(step),V.rmse_rpm(step),P.fuel_peak_lbm_s(step),V.fuel_peak_lbm_s(step),P.minimum_margin_percent(step),V.minimum_margin_percent(step));
fprintf(fid,'The step-load traces also show more pronounced damped oscillations in fuel command and speed with the new controller. The lower RMSE should therefore be considered alongside control activity and surge margin.\n\n');
extended=find(~P.accepted & V.accepted);
for k=extended'
 fprintf(fid,'At %g rpm and %g%% %s load, the virtual-fuel PI completes a physically valid run while the original PI fails. New-controller RMSE is %.3f rpm and minimum surge margin is %.3f%%. There is no valid full-run baseline RMSE for a percentage comparison.\n\n',V.rpm(k),100*V.fraction(k),V.shape{k},V.rmse_rpm(k),V.minimum_margin_percent(k));
end
fprintf(fid,'| rpm | load | shape | PI peak fuel [lbm/s] | VF peak fuel [lbm/s] | PI minimum margin [%%] | VF minimum margin [%%] |\n|---:|---:|:---|---:|---:|---:|---:|\n');
for k=1:height(P)
 fprintf(fid,'| %g | %g%% | %s | %.4f | %.4f | %.4f | %.4f |\n',P.rpm(k),100*P.fraction(k),P.shape{k},P.fuel_peak_lbm_s(k),V.fuel_peak_lbm_s(k),P.minimum_margin_percent(k),V.minimum_margin_percent(k));
end
fprintf(fid,'\n');
fprintf(fid,'## Validation and limits\n\n');
fprintf(fid,'Valid complete simulations: original PI %d/10, virtual-fuel PI %d/10. Maximum exported-GP feedback replay discrepancy: %.3g lbm/s. The runner checks setpoint replay, fuel-domain subtraction, PI output equation, limits, full duration, load identity, constant reference, zero injected fuel disturbance, solver convergence, and positive compressor surge margin.\n\n',sum(P.accepted),sum(V.accepted),max(T.gp_replay_error));
historical=readtable(fullfile(root,'results','gpr_ff_benchmarks_20260913_173407_036','summary.csv'));
historical=historical(strcmp(historical.method,'PI'),:);assert(isequal(P.accepted,historical.accepted));
valid=P.accepted==1;delta=max(abs(P.rmse_rpm(valid)-historical.rmse_rpm(valid)));assert(delta<1e-7);
fprintf(fid,'The original PI validity classifications match the previous ten-case benchmark; maximum RMSE difference on valid cases is %.3g rpm. NaN entries denote invalid full runs, not zero error. Comparison plots stop at the first invalid sample; complete raw histories are retained in MAT/CSV files. Rejected tuning runs can include solver convergence failures without proving closed-loop instability.\n\n',delta);
if ~isempty(failures)
 fprintf(fid,'| rpm | load | shape | controller | first invalid time after preparation [s] | flow residual | solver iterations |\n|---:|---:|:---|:---|---:|---:|---:|\n');
 for k=1:numel(failures),r=failures(k);fprintf(fid,'| %g | %g%% | %s | %s | %.3f | %.4g | %g |\n',r.rpm,100*r.fraction,r.shape,r.method,r.first_failure_eval_s,r.flow_error,r.iterations);end
 fprintf(fid,'\n');
end
fprintf(fid,'The 9000-rpm lower training boundary is crossed during underspeed. Queries are deliberately not clipped, preserving restoring action; VF out-of-training-rectangle sample fractions span %.2f to %.2f%% across evaluation cases. A rectangular training flag is only a coarse coverage diagnostic. These deterministic tests do not establish robustness to noisy sensors, ambient changes, broad extrapolation, or startup without the original PI. The inverse GP was trained at zero external load and its virtual fuel is a nominal model coordinate, not measured actual fuel.\n\n',min(V.outside_training_percent),max(V.outside_training_percent));
fprintf(fid,'![9000 rpm comparison](comparison_9000rpm.png)\n\n![9500 rpm comparison](comparison_9500rpm.png)\n\n![Virtual fuel signals](virtual_fuel_signals.png)\n');
fprintf(fid,'\n![20 percent step-load tradeoff](step_tradeoff.png)\n');
end
function d=plotprefix(d)
bad=find(~d.valid,1);if ~isempty(bad),d.Nmech(bad:end)=NaN;d.Wf(bad:end)=NaN;end
end
