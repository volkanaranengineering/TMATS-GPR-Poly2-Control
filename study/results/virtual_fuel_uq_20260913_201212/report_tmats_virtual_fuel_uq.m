function report_tmats_virtual_fuel_uq(out)
if nargin<1,out=strtrim(fileread('tmp/virtual_fuel_uq_directory.txt'));end
root=fileparts(mfilename('fullpath'));s=load(fullfile(out,'configuration.mat'));
old=fullfile(root,'results','virtual_fuel_20260913_182229_028');fixed=s.fixed;
P=readtable(fullfile(old,'summary.csv'));P=P(strcmp(P.method,'VirtualFuel'),:);
F=readtable(fullfile(fixed,'summary.csv'));F=F(strcmp(F.method,'VirtualFuelFF'),:);
U=readtable(fullfile(out,'summary.csv'));
assert(height(U)==10 && isequal(U.rpm,P.rpm,F.rpm) && isequal(U.fraction,P.fraction,F.fraction) && isequal(U.shape,P.shape,F.shape));
C=U(:,{'rpm','fraction','shape'});
C.previous_valid=P.accepted;C.fixed_FF_valid=F.accepted;C.scheduled_valid=U.accepted;
C.previous_RMSE=P.rmse_rpm;C.fixed_FF_RMSE=F.rmse_rpm;C.scheduled_RMSE=U.rmse_rpm;
C.improvement_vs_previous_percent=100*(1-U.rmse_rpm./P.rmse_rpm);
C.improvement_vs_fixed_percent=100*(1-U.rmse_rpm./F.rmse_rpm);
C.previous_peak=P.peak_rpm;C.fixed_FF_peak=F.peak_rpm;C.scheduled_peak=U.peak_rpm;
C.previous_IAE=P.iae_rpm_s;C.fixed_FF_IAE=F.iae_rpm_s;C.scheduled_IAE=U.iae_rpm_s;
C.previous_margin=P.minimum_margin_percent;C.fixed_FF_margin=F.minimum_margin_percent;C.scheduled_margin=U.minimum_margin_percent;
C.minimum_gain_factor=U.minimum_gain_factor;C.mean_gain_factor=U.mean_gain_factor;
writetable(C,fullfile(out,'comparison.csv'));
ratio=(0:.01:6)';factor=tmats_uncertainty_gain_factor(ratio*s.sigmaReference,zeros(size(ratio)),s.sigmaReference);
writetable(table(ratio,factor),fullfile(out,'gain_schedule_curve.csv'));
[~,~,~,vf]=tmats_virtual_fuel_uq_setup;
probeSpeed=(8500:25:11000)';
[~,probeSD]=predict_tmats_inverse_gpr(vf.model,probeSpeed,zeros(size(probeSpeed)));
[~,referenceSD]=predict_tmats_inverse_gpr(vf.model,9500,0);
probeFactor=tmats_uncertainty_gain_factor(referenceSD,probeSD,s.sigmaReference);
writetable(table(probeSpeed,probeSD,probeFactor),fullfile(out,'offline_uncertainty_probe.csv'));
f=figure('Visible','off','Color','w','Position',[20 20 1100 650]);
subplot(2,1,1);plot(probeSpeed,probeSD/s.sigmaReference);hold on;plot([8500 11000],[3 3],'r--');grid on;ylabel('Feedback SD / reference SD');title('Offline GP queries at zero acceleration; not a plant simulation');legend('GP uncertainty','Three-SD threshold');
subplot(2,1,2);plot(probeSpeed,probeFactor);hold on;plot([8500 11000],[.1 .1],'r--');grid on;ylabel('Gain factor');xlabel('Queried feedback speed [rpm]');
print(f,fullfile(out,'offline_uncertainty_probe.png'),'-dpng','-r130');close(f);
for group=1:3
 if group==1,ids=1:4;label='9000rpm_ramps';elseif group==2,ids=5:8;label='9500rpm_ramps';else,ids=9:10;label='9500rpm_steps';end
 f=figure('Visible','off','Color','w','Position',[20 20 1400 300*numel(ids)]);
 for j=1:numel(ids)
  c=ids(j);[a,b,u]=getruns(c);
  subplot(numel(ids),2,2*j-1);
  plot(a.time_s-60,a.Nmech-U.rpm(c),'Color',[.5 .5 .5]);hold on;
  plot(b.time_s-60,b.Nmech-U.rpm(c),'Color',[.85 .3 .1]);plot(u.time_s-60,u.Nmech-U.rpm(c),'b');grid on;xlim([0 90]);
  ylabel('Speed error [rpm]');title(sprintf('%g rpm, %g%% %s; valid old/fixed/UQ: %d/%d/%d',U.rpm(c),100*U.fraction(c),U.shape{c},P.accepted(c),F.accepted(c),U.accepted(c)));
  if j==1,legend('Previous inverse GP PI','FF + fixed retuned PI','FF + uncertainty PI','Location','best');end
  subplot(numel(ids),2,2*j);plot(a.time_s-60,a.Wf,'Color',[.5 .5 .5]);hold on;
  plot(b.time_s-60,b.Wf,'Color',[.85 .3 .1]);plot(u.time_s-60,u.Wf,'b');grid on;xlim([0 90]);ylabel('Fuel [lbm/s]');
 end
 xlabel('Time after preparation [s]');print(f,fullfile(out,['comparison_' label '.png']),'-dpng','-r120');close(f);
end
f=figure('Visible','off','Color','w','Position',[20 20 1350 900]);
subplot(3,2,1);plot(ratio,factor,'LineWidth',1.5);hold on;plot(3,.1,'ro');grid on;xlabel('max(SD) / reference SD');ylabel('Gain factor');title('Both Kp and Ki multiplied by this factor');
for j=1:2
 c=[4 9];c=c(j);[~,~,u]=getruns(c);t=u.time_s-60;
 subplot(3,2,j+2);plot(t,u.VF_sdSetpoint/s.sigmaReference,t,u.VF_sdFeedback/s.sigmaReference);grid on;xlim([0 90]);ylabel('SD / reference SD');title(sprintf('%g rpm, %g%% %s',U.rpm(c),100*U.fraction(c),U.shape{c}));legend('Setpoint GP','Feedback GP');
 subplot(3,2,j+4);plot(t,u.VF_Kp,t,u.VF_Ki);grid on;xlim([0 90]);ylabel('Scheduled gains');xlabel('Time after preparation [s]');legend('Kp','Ki /s');
end
subplot(3,2,2);bar([sum(P.accepted) sum(F.accepted) sum(U.accepted)]);set(gca,'XTickLabel',{'Previous','Fixed FF','Scheduled FF'});ylim([0 10]);ylabel('Valid scenarios / 10');grid on;
print(f,fullfile(out,'uncertainty_schedule.png'),'-dpng','-r130');close(f);
failure=[];
for c=1:height(U)
 if U.accepted(c),continue;end
 tag=sprintf('%drpm_%02dpct_%s_VirtualFuelUQ.mat',U.rpm(c),round(100*U.fraction(c)),U.shape{c});z=load(fullfile(out,tag));bad=find(~z.d.valid,1);
 if isempty(bad),continue;end
 row=struct('rpm',U.rpm(c),'fraction',U.fraction(c),'shape',U.shape{c},'first_invalid_eval_s',z.d.time_s(bad)-60,'margin',z.d.DOB_SM(bad),'flow_error',z.d.max_flow_error(bad),'iterations',z.d.DOB_iterations(bad));
 if isempty(failure),failure=row;else,failure(end+1)=row;end
end
if ~isempty(failure),writetable(struct2table(failure),fullfile(out,'failure_details.csv'));end
fid=fopen(fullfile(out,'REPORT.md'),'w');cleanup=onCleanup(@()fclose(fid));
fprintf(fid,'# Inverse-GPR fuel controller: feedforward, retuning, and uncertainty scheduling\n\n');
fprintf(fid,'Previous inverse-GPR PI: Kp=4, Ki=40 /s. Fixed feedforward retuning: Kp=%g, Ki=%g /s. The scheduled controller uses these same base gains, scaled online by the uncertainty of both inverse models.\n\n',s.gains);
fprintf(fid,'## Scheduling rule\n\n');
fprintf(fid,'Let sigma_max=max(sigma_setpoint,sigma_feedback), s=sigma_max/sigma_ref, and **alpha=10^(-(s/3)^2)**. Then **Kp=alpha*%g**, **Ki=alpha*%g /s**. Alpha is 1 at zero uncertainty, %.6f at one reference SD, 0.1 at three reference SDs, and 0.0001 at six. It approaches zero monotonically.\n\n',s.gains,10^(-1/9));
fprintf(fid,'The fixed reference SD is **%.12g lbm/s**, the median predictive response SD evaluated at all 600 training locations. It is computed without benchmark outcomes. Thus the three-SD point is **%.12g lbm/s**. This is a normalized uncertainty threshold, not a Gaussian tail-probability calculation. Response SD includes fitted observation noise; the latent-only SD is not used.\n\n',s.sigmaReference,3*s.sigmaReference);
fprintf(fid,'The exact GP uses its saved Cholesky factor online. Feedforward is g(reference,0); feedback is g(sensed speed,causally filtered acceleration). The command is clip(feedforward+Kp*error+I,0.2,4). The acceleration setpoint is zero in these tests. Neither actual shaft load nor the future disturbance schedule enters the controller.\n\n');
fprintf(fid,'When Kp changes, I is adjusted by (Kp_previous-Kp_current)*error before the command is formed. This cancels the jump caused solely by changing a gain, while leaving the error response gain scheduled. Ki changes the integral increment; the accumulated load-compensation integral is retained as gains approach zero. Startup tracking and conditional anti-windup use the full FF+PI command.\n\n');
fprintf(fid,'## Comparison\n\nValid scenarios: previous **%d/10**, fixed FF **%d/10**, scheduled FF **%d/10**. Invalid runs have no full-run RMSE or peak score; plotted traces stop at first invalid sample.\n\n',sum(P.accepted),sum(F.accepted),sum(U.accepted));
validRamps=logical(U.accepted)&logical(P.accepted)&strcmp(U.shape,'ramps');
fprintf(fid,'Scheduling reduces RMSE by **%.3g to %.3g%%** versus the previous controller across the seven mutually valid ramp cases, while being slower than fixed FF tuning. In the 9500 rpm 20%% step case, it restores validity relative to fixed FF and raises minimum surge margin from the previous controller value of **%.3g%% to %.3g%%**, at the cost of RMSE increasing from **%.4g to %.4g rpm**. The 9500 rpm 30%% ramp and step cases remain invalid. This is a measured tradeoff, not an across-the-board improvement.\n\n',min(C.improvement_vs_previous_percent(validRamps)),max(C.improvement_vs_previous_percent(validRamps)),P.minimum_margin_percent(9),U.minimum_margin_percent(9),P.rmse_rpm(9),U.rmse_rpm(9));
fprintf(fid,'|rpm|load %%|shape|old valid|fixed valid|scheduled valid|old RMSE|fixed RMSE|scheduled RMSE|UQ improvement vs old %%|UQ min margin %%|\n|---|---|---|---|---|---|---|---|---|---|---|\n');
for c=1:height(C)
 fprintf(fid,'|%g|%g|%s|%d|%d|%d|%.5g|%.5g|%.5g|%.3g|%.5g|\n',C.rpm(c),100*C.fraction(c),C.shape{c},C.previous_valid(c),C.fixed_FF_valid(c),C.scheduled_valid(c),C.previous_RMSE(c),C.fixed_FF_RMSE(c),C.scheduled_RMSE(c),C.improvement_vs_previous_percent(c),C.scheduled_margin(c));
end
fprintf(fid,'\nThe fixed gain grid was selected only on 9000 rpm ramp cases. The uncertainty schedule uses that frozen pair without retuning against 9500 rpm results. See the preceding fixed-feedforward study for the eight-pair grid and same-gain ablation, which established constant-reference feedforward equivalence to an integral offset.\n\n');
fprintf(fid,'Verification: maximum online-vs-exported GP SD difference **%.6g lbm/s**; maximum integral recurrence error **%.6g lbm/s**. Every run checks scheduled gains, command reconstruction, GP means, load replay, complete sample count, solver residuals, iterations, settling and positive surge margin.\n\n',max(U.sd_replay_error),max(U.integral_replay_error));
fprintf(fid,'The GP SD is model-conditional uncertainty. It does not include sensor-input uncertainty, hyperparameter uncertainty, or systematic errors from unmodeled shaft load. A confident GP can still be physically wrong. This scheduler is an uncertainty-based attenuation heuristic, not a stability guarantee or a surge-margin controller. Standard deviation can remain almost constant near the fitted noise floor, in which case scheduling mainly acts as gain derating.\n\n');
fprintf(fid,'Across valid runs, the smallest gain factor was **%.6g** and the largest SD/reference ratio was **%.6g**. The offline uncertainty probe queries the actual frozen GP from 8500 to 11000 rpm at zero acceleration, holding the setpoint GP at 9500 rpm; it illustrates the scheduler outside the modeled speed band without claiming plant validity there.\n\n',min(U.minimum_gain_factor(logical(U.accepted))),max(U.maximum_sd(logical(U.accepted)))/s.sigmaReference);
fprintf(fid,'![Offline uncertainty probe](offline_uncertainty_probe.png)\n\n');
fprintf(fid,'![Scheduling](uncertainty_schedule.png)\n\n![9000 rpm](comparison_9000rpm_ramps.png)\n\n![9500 rpm](comparison_9500rpm_ramps.png)\n\n![Steps](comparison_9500rpm_steps.png)\n');
 function [a,b,u]=getruns(c)
  tag=sprintf('%drpm_%02dpct_%s_',U.rpm(c),round(100*U.fraction(c)),U.shape{c});
  z=load(fullfile(old,[tag 'VirtualFuel.mat']));a=prefix(z.d);
  z=load(fullfile(fixed,[tag 'VirtualFuelFF.mat']));b=prefix(z.d);
  z=load(fullfile(out,[tag 'VirtualFuelUQ.mat']));u=prefix(z.d);
 end
end
function d=prefix(d)
bad=find(~d.valid,1);if ~isempty(bad),d=d(1:max(1,bad-1),:);end
end

