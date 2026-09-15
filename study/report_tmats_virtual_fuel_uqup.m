function report_tmats_virtual_fuel_uqup(out)
% Compare original, fixed FF, decreasing SD, and increasing SD schedules.
if nargin<1,out=strtrim(fileread('tmp/virtual_fuel_uqup_directory.txt'));end
root=fileparts(mfilename('fullpath'));cfg=load(fullfile(out,'configuration.mat'));
folders={fullfile(root,'results','virtual_fuel_20260913_182229_028'),cfg.fixed, ...
 fullfile(root,'results','virtual_fuel_uq_20260913_201212'),out};
methods={'VirtualFuel','VirtualFuelFF','VirtualFuelUQ','VirtualFuelUQUp'};
labels={'Previous inverse GP PI','FF fixed PI','SD decreasing gains','SD increasing gains'};
colors=[.5 .5 .5;.85 .3 .1;0 .3 .85;.55 .1 .7];
U=readtable(fullfile(out,'summary.csv'));assert(height(U)==10);
D=cell(10,4);R=[];
for c=1:10
 for j=1:4
  tag=sprintf('%drpm_%02dpct_%s_%s.mat',U.rpm(c),round(100*U.fraction(c)),U.shape{c},methods{j});
  z=load(fullfile(folders{j},tag));D{c,j}=z.d;met=z.met;
  ring=NaN;range=NaN;
  if met.accepted
   ramps=[0 0 0];if strcmp(U.shape{c},'ramps'),ramps=[.3 1.5 3];end
   starts=[70.005+ramps(1) 75+ramps(1) 90+ramps(2) 100.005+ramps(2) 120+ramps(3) 135+ramps(3)];
   ring=0;range=0;
   for t=starts
    ix=z.d.time_s>=t-1e-8 & z.d.time_s<=t+2+1e-8;fuel=z.d.Wf(ix);
    ring=ring+max(0,sum(abs(diff(fuel)))-abs(fuel(end)-fuel(1)));
    range=max(range,max(fuel)-min(fuel));
   end
  end
  row=struct('case_index',c,'rpm',U.rpm(c),'fraction',U.fraction(c),'shape',U.shape{c},'method',methods{j}, ...
   'accepted',met.accepted,'rmse_rpm',met.rmse_rpm,'peak_rpm',met.peak_rpm,'iae_rpm_s',met.iae_rpm_s, ...
   'minimum_margin_percent',met.minimum_margin_percent,'ringing_excess_TV_lbm_s',ring,'max_2s_fuel_range_lbm_s',range);
  if isempty(R),R=row;else,R(end+1)=row;end
 end
end
T=struct2table(R);writetable(T,fullfile(out,'comparison_all_methods.csv'));
for group=1:3
 if group==1,ids=1:4;label='9000rpm_ramps';elseif group==2,ids=5:8;label='9500rpm_ramps';else,ids=9:10;label='9500rpm_steps';end
 f=figure('Visible','off','Color','w','Position',[20 20 1450 300*numel(ids)]);
 for k=1:numel(ids)
  c=ids(k);
  for j=1:4
   d=prefix(D{c,j});
   subplot(numel(ids),2,2*k-1);plot(d.time_s-60,d.Nmech-U.rpm(c),'Color',colors(j,:));hold on;
   subplot(numel(ids),2,2*k);plot(d.time_s-60,d.Wf,'Color',colors(j,:));hold on;
  end
  subplot(numel(ids),2,2*k-1);grid on;xlim([0 90]);ylabel('Speed error [rpm]');title(sprintf('%g rpm, %g%% %s',U.rpm(c),100*U.fraction(c),U.shape{c}));
  if k==1,legend(labels,'Location','best');end
  subplot(numel(ids),2,2*k);grid on;xlim([0 90]);ylabel('Fuel [lbm/s]');
 end
 xlabel('Time after preparation [s]');print(f,fullfile(out,['comparison_' label '.png']),'-dpng','-r120');close(f);
end
s=(-4:.01:4)';up=tmats_uncertainty_increasing_gain_factor(abs(s)*cfg.sigmaReference,zeros(size(s)),cfg.sigmaReference);
down=tmats_uncertainty_gain_factor(abs(s)*cfg.sigmaReference,zeros(size(s)),cfg.sigmaReference);
writetable(table(s,up,down),fullfile(out,'schedule_curves.csv'));
f=figure('Visible','off','Color','w','Position',[20 20 1250 820]);
subplot(3,2,1);plot(s,up,'Color',colors(4,:),'LineWidth',1.5);hold on;plot(s,down,'Color',colors(3,:));grid on;xlabel('Signed band coordinate / reference SD');ylabel('Gain factor');legend('Increasing','Decreasing','Location','best');title('Both PI gains use the same factor');
subplot(3,2,2);counts=zeros(4,1);for j=1:4,counts(j)=sum(T.accepted(strcmp(T.method,methods{j})));end
bar(counts);set(gca,'XTickLabel',{'Previous','Fixed FF','SD down','SD up'});ylim([0 10]);ylabel('Valid cases / 10');grid on;
for k=1:2
 c=[4 9];c=c(k);
 for j=3:4
  d=prefix(D{c,j});subplot(3,2,k+2);plot(d.time_s-60,max(d.VF_sdSetpoint,d.VF_sdFeedback)/cfg.sigmaReference,'Color',colors(j,:));hold on;
  subplot(3,2,k+4);plot(d.time_s-60,d.VF_gainFactor,'Color',colors(j,:));hold on;
 end
 subplot(3,2,k+2);grid on;xlim([0 90]);ylabel('max SD / reference SD');title(sprintf('%g rpm, %g%% %s',U.rpm(c),100*U.fraction(c),U.shape{c}));legend('SD down','SD up');
 subplot(3,2,k+4);grid on;xlim([0 90]);ylabel('Gain factor');xlabel('Time after preparation [s]');
end
print(f,fullfile(out,'increasing_schedule.png'),'-dpng','-r130');close(f);
failures=[];
for c=1:10
 if U.accepted(c),continue;end
 d=D{c,4};bad=find(~d.valid,1);if isempty(bad),continue;end
 row=struct('rpm',U.rpm(c),'fraction',U.fraction(c),'shape',U.shape{c},'first_invalid_eval_s',d.time_s(bad)-60, ...
  'flow_error',d.max_flow_error(bad),'iterations',d.DOB_iterations(bad),'surge_margin',d.DOB_SM(bad),'gain_factor',d.VF_gainFactor(bad));
 if isempty(failures),failures=row;else,failures(end+1)=row;end
end
if ~isempty(failures),writetable(struct2table(failures),fullfile(out,'failure_details.csv'));end
fid=fopen(fullfile(out,'REPORT.md'),'w');cleanup=onCleanup(@()fclose(fid));
fprintf(fid,'# Increasing inverse-GPR uncertainty gain scenario\n\n');
fprintf(fid,'The new scenario keeps factor **1 through one reference SD**, then smoothly increases to **2 at three reference SDs**, capped at 2 thereafter. It uses the same base gains Kp=%g and Ki=%g /s, frozen GP and reference SD as the previous FF scheduling study.\n\n',cfg.gains);
fprintf(fid,'Define s=max(sigma_setpoint,sigma_feedback)/sigma_ref, x=clip((s-1)/2,0,1), and **factor=1+3*x^2-2*x^3**. Both gains are multiplied by this factor. The slope is zero at s=1 and s=3. SD is nonnegative, so the requested plus/minus bands are interpreted symmetrically by magnitude; speed-error sign is not used. Sigma_ref=**%.12g lbm/s**, the median response SD at the 600 training locations.\n\n',cfg.sigmaReference);
fprintf(fid,'The full controller remains feedforward + scheduled fuel-domain PI with causal acceleration filtering, bumpless gain transfer, startup tracking, conditional anti-windup and fuel limits. Only the gain schedule changes relative to the SD-down scenario; no new base-gain search is performed.\n\n');
fprintf(fid,'Valid scenarios: previous **%d/10**, fixed FF **%d/10**, SD down **%d/10**, SD up **%d/10**. Scores are withheld after any invalid plant result; plot traces stop at the first invalid sample.\n\n',counts);
fprintf(fid,'|rpm|load %%|shape|previous RMSE|fixed RMSE|SD-down RMSE|SD-up RMSE|SD-up valid|SD-up minimum margin %%|\n|---|---|---|---|---|---|---|---|---|\n');
for c=1:10
 ix=T.case_index==c;v=T(ix,:);
 fprintf(fid,'|%g|%g|%s|%.5g|%.5g|%.5g|%.5g|%d|%.5g|\n',U.rpm(c),100*U.fraction(c),U.shape{c},v.rmse_rpm',v.accepted(4),v.minimum_margin_percent(4));
end
fprintf(fid,'\nFuel oscillation is also quantified in comparison_all_methods.csv: for each of six load transitions, measure the two seconds after the ramp finishes (or after the step), sum abs(diff(fuel)), subtract the absolute net fuel change, then sum those six excess-total-variation values. This measures repeated reversals rather than monotonic adjustment. The largest two-second fuel range is reported separately. Invalid runs have no full-run ringing score.\n\n');
fprintf(fid,'Verification: maximum GP SD replay error %.6g lbm/s; maximum bumpless integral recurrence error %.6g lbm/s. Endpoint factors [1,1,1.5,2,2,2] at normalized SD [0,1,2,3,6,infinity] and the max-of-either-model behavior are checked. Gain, command, GP mean, solver, load and sample-count checks are inherited.\n\n',max(U.sd_replay_error),max(U.integral_replay_error));
fprintf(fid,'Increasing uncertainty does not establish that higher feedback gains are stabilizing. The posterior SD reflects the nominal GP training distribution, not all loaded-plant model errors. These results test the requested alternative and do not assume it is superior.\n\n![Schedules](increasing_schedule.png)\n\n![9000 rpm](comparison_9000rpm_ramps.png)\n\n![9500 rpm](comparison_9500rpm_ramps.png)\n\n![Steps](comparison_9500rpm_steps.png)\n');
end
function d=prefix(d)
bad=find(~d.valid,1);if ~isempty(bad),d=d(1:max(1,bad-1),:);end
end
