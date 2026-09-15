function report_tmats_virtual_fuel_ff(out)
% Compare frozen previous runs with feedforward and retuned fuel PI.
if nargin<1,out=strtrim(fileread('tmp/virtual_fuel_ff_directory.txt'));end
root=fileparts(mfilename('fullpath'));
old=fullfile(root,'results','virtual_fuel_20260913_182229_028');
T=readtable(fullfile(out,'summary.csv'));T=T(strcmp(T.method,'VirtualFuelFF'),:);
P=readtable(fullfile(old,'summary.csv'));P=P(strcmp(P.method,'VirtualFuel'),:);
assert(height(T)==10 && isequal(T.rpm,P.rpm) && isequal(T.fraction,P.fraction) && isequal(T.shape,P.shape));
C=T(:,{'rpm','fraction','shape'});
C.previous_valid=P.accepted;C.FF_valid=T.accepted;
C.previous_RMSE=P.rmse_rpm;C.FF_RMSE=T.rmse_rpm;
C.RMSE_reduction_percent=100*(1-T.rmse_rpm./P.rmse_rpm);
C.previous_peak=P.peak_rpm;C.FF_peak=T.peak_rpm;
C.previous_IAE=P.iae_rpm_s;C.FF_IAE=T.iae_rpm_s;
C.previous_margin=P.minimum_margin_percent;C.FF_margin=T.minimum_margin_percent;
writetable(C,fullfile(out,'comparison.csv'));
ablation=[];
for c=1:4
 tag=sprintf('9000rpm_%02dpct_ramps_VirtualFuel.mat',round(100*P.fraction(c)));
 a=load(fullfile(old,tag));b=load(fullfile(out,sprintf('tune_01_%02d.mat',c)));
 ix=a.d.time_s>=30;
 ablation=[ablation;P.fraction(c) max(abs(a.d.Nmech(ix)-b.d.Nmech(ix))) max(abs(a.d.Wf(ix)-b.d.Wf(ix)))]; %#ok<AGROW>
end
writetable(array2table(ablation,'VariableNames',{'fraction','max_speed_difference_rpm','max_fuel_difference_lbm_s'}),fullfile(out,'same_gains_ablation.csv'));
assert(max(ablation(:,2))<1e-5 && max(ablation(:,3))<1e-7,'Same-gain feedforward equivalence failed.');
failures=[];
for c=1:height(T)
 if T.accepted(c),continue;end
 tag=sprintf('%drpm_%02dpct_%s_VirtualFuelFF.mat',T.rpm(c),round(100*T.fraction(c)),T.shape{c});
 b=load(fullfile(out,tag));bad=find(~b.d.valid,1);
 if isempty(bad),continue;end
 entry=struct('rpm',T.rpm(c),'fraction',T.fraction(c),'shape',T.shape{c},'first_invalid_eval_s',b.d.time_s(bad)-60, ...
  'flow_error',b.d.max_flow_error(bad),'iterations',b.d.DOB_iterations(bad),'surge_margin',b.d.DOB_SM(bad));
 if isempty(failures),failures=entry;else,failures(end+1)=entry;end
end
if ~isempty(failures),writetable(struct2table(failures),fullfile(out,'failure_details.csv'));end
for rpm=[9000 9500]
 f=figure('Visible','off','Color','w','Position',[20 20 1350 900]);
 ids=find(T.rpm==rpm & strcmp(T.shape,'ramps'));
 for j=1:numel(ids)
  c=ids(j);tag=sprintf('%drpm_%02dpct_ramps_',rpm,round(100*T.fraction(c)));
  a=load(fullfile(old,[tag 'VirtualFuel.mat']));b=load(fullfile(out,[tag 'VirtualFuelFF.mat']));
  a.d=prefix(a.d);b.d=prefix(b.d);
  subplot(4,2,2*j-1);plot(a.d.time_s-60,a.d.Nmech-rpm,'Color',[.5 .5 .5]);hold on;
  plot(b.d.time_s-60,b.d.Nmech-rpm,'b');grid on;xlim([0 90]);ylabel('Speed error [rpm]');title(sprintf('%g rpm, %g%% load',rpm,100*T.fraction(c)));
  if j==1,legend('Previous inverse GP PI','GP FF + retuned PI','Location','best');end
  subplot(4,2,2*j);plot(a.d.time_s-60,a.d.Wf,'Color',[.5 .5 .5]);hold on;plot(b.d.time_s-60,b.d.Wf,'b');grid on;xlim([0 90]);ylabel('Fuel [lbm/s]');
 end
 xlabel('Time after preparation [s]');print(f,fullfile(out,sprintf('comparison_%drpm.png',rpm)),'-dpng','-r140');close(f);
end
f=figure('Visible','off','Color','w','Position',[20 20 1250 720]);
for j=1:2
 c=j+8;tag=sprintf('9500rpm_%02dpct_steps_',round(100*T.fraction(c)));
 a=load(fullfile(old,[tag 'VirtualFuel.mat']));b=load(fullfile(out,[tag 'VirtualFuelFF.mat']));a.d=prefix(a.d);b.d=prefix(b.d);
 subplot(2,2,2*j-1);plot(a.d.time_s-60,a.d.Nmech-9500,b.d.time_s-60,b.d.Nmech-9500);grid on;xlim([0 90]);ylabel('Speed error [rpm]');title(sprintf('%g%% abrupt load; invalid traces stop at first failure',100*T.fraction(c)));legend('Previous','FF + retuned');
 subplot(2,2,2*j);plot(a.d.time_s-60,a.d.Wf,b.d.time_s-60,b.d.Wf);grid on;xlim([0 90]);ylabel('Fuel [lbm/s]');
end
print(f,fullfile(out,'comparison_steps.png'),'-dpng','-r140');close(f);
fid=fopen(fullfile(out,'REPORT.md'),'w');cleanup=onCleanup(@()fclose(fid));
fprintf(fid,'# Inverse-GPR feedforward plus retuned fuel-domain PI\n\n');
fprintf(fid,'Previous gains: Kp=4, Ki=40 /s. Selected gains: **Kp=%g, Ki=%g /s**.\n\n',T.Kp(1),T.Ki(1));
fprintf(fid,'The frozen inverse GP supplies v_ref=g(reference,0) and v_feedback=g(sensed speed,filtered acceleration). The enhanced command is sat(v_ref + Kp*(v_ref-v_feedback) + I). Before the 30 s handover, I tracks startup_PI-v_ref-Kp*error. Conditional integration uses the full unsaturated command. The feedforward term is logged as VF_setpoint; VF_integral is now the residual integral contribution. Sampling, sensor, plant, loads, GP, and fuel limits are inherited unchanged.\n\n');
fprintf(fid,'For constant reference, feedforward is constant and is absorbed by the bumpless integral offset. Same-gain ablation over four 9000 rpm cases gives maximum speed difference %.6g rpm and fuel difference %.6g lbm/s. Improvements in this benchmark are therefore due to gain retuning; these tests do not establish an additional reference-tracking benefit from feedforward.\n\n',max(ablation(:,2)),max(ablation(:,3)));
fprintf(fid,'Eight gain pairs were evaluated on all four 9000 rpm ramp amplitudes (5,10,20,30%%), minimizing mean RMSE normalized by the archived original speed PI. Every training case must pass solver, positive surge-margin, finite-signal and pre-disturbance settling checks. Gains were frozen before the 9500 rpm held-out tests. This is a finite local gain search, not a global optimum. Full-run metrics are withheld after any invalid plant solve.\n\n');
fprintf(fid,'|rpm|load %%|shape|previous valid|new valid|old RMSE|new RMSE|reduction %%|old peak|new peak|min new margin %%|\n|---|---|---|---|---|---|---|---|---|---|---|\n');
for c=1:height(C)
 fprintf(fid,'|%g|%g|%s|%d|%d|%.5g|%.5g|%.3g|%.5g|%.5g|%.5g|\n',C.rpm(c),100*C.fraction(c),C.shape{c},C.previous_valid(c),C.FF_valid(c),C.previous_RMSE(c),C.FF_RMSE(c),C.RMSE_reduction_percent(c),C.previous_peak(c),C.FF_peak(c),C.FF_margin(c));
end
fprintf(fid,'\nFuel-domain gains are not speed-domain PI gains. The GP was trained at nominal zero shaft load. At 9000 rpm, negative speed excursions leave its training speed range; outside-training percentages remain in summary.csv. Small positive surge margin is not a robustness guarantee.\n\n![9000 rpm](comparison_9000rpm.png)\n\n![9500 rpm](comparison_9500rpm.png)\n\n![Abrupt loads](comparison_steps.png)\n');
end
function d=prefix(d)
bad=find(~d.valid,1);if ~isempty(bad),d=d(1:max(1,bad-1),:);end
end
