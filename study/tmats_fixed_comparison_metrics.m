function met=tmats_fixed_comparison_metrics(d,rpm,ramps,DOB)
% Shared physical validity and response metrics for fixed-controller trials.
ix=d.time_s>=60;trim=d.time_s>=55 & d.time_s<=60;
met=struct('accepted',all(d.valid)&&d.time_s(end)>=150-1e-9&&any(trim)&&max(abs(d.Nmech(trim)-rpm))<.1, ...
 'rmse_rpm',NaN,'peak_rpm',NaN,'iae_rpm_s',NaN,'minimum_margin_percent',NaN, ...
 'fuel_peak_lbm_s',NaN,'fuel_limit_percent',NaN,'ringing_excess_TV_lbm_s',NaN, ...
 'max_2s_fuel_range_lbm_s',NaN,'max_fuel_slew_lbm_s2',NaN,'settling_to_point1_rpm_s',NaN, ...
 'recovery_1pct_speed_s',NaN,'events_inside_1pct_throughout',NaN,'first_failure_eval_s',NaN);
bad=find(~d.valid,1);if ~isempty(bad),met.first_failure_eval_s=d.time_s(bad)-60;end
if ~met.accepted,return;end
e=d.Nmech(ix)-rpm;met.rmse_rpm=sqrt(mean(e.^2));met.peak_rpm=max(abs(e));met.iae_rpm_s=sum(abs(e))*DOB.Ts;
met.minimum_margin_percent=min(d.DOB_SM(ix));met.fuel_peak_lbm_s=max(d.Wf(ix));
met.fuel_limit_percent=100*mean(d.DOB_command(ix)<=DOB.fuelMin+1e-9|d.DOB_command(ix)>=DOB.fuelMax-1e-9);
starts=[70.005 75 90 100.005 120 135];ringStarts=starts+[ramps(1) ramps(1) ramps(2) ramps(2) ramps(3) ramps(3)];
ends=[75 90 100.005 120 135 150];ringing=0;range=0;slew=0;settling=0;onePct=0;insideCount=0;
for k=1:6
 q=d.time_s>=ringStarts(k)-1e-8 & d.time_s<=ringStarts(k)+2+1e-8;f=d.Wf(q);
 ringing=ringing+max(0,sum(abs(diff(f)))-abs(f(end)-f(1)));range=max(range,max(f)-min(f));slew=max(slew,max(abs(diff(f)))/DOB.Ts);
 q=find(d.time_s>=starts(k)-1e-8 & d.time_s<ends(k)-1e-8);bad=find(abs(d.Nmech(q)-rpm)>.1,1,'last');
 recovery=0;if ~isempty(bad),if bad==numel(q),recovery=Inf;else,recovery=d.time_s(q(bad+1))-starts(k);end;end
 settling=max(settling,recovery);
 bad=find(abs(d.Nmech(q)-rpm)>.01*rpm,1,'last');recovery=0;
 if isempty(bad),insideCount=insideCount+1;elseif bad==numel(q),recovery=Inf;else,recovery=d.time_s(q(bad+1))-starts(k);end
 onePct=max(onePct,recovery);
end
met.ringing_excess_TV_lbm_s=ringing;met.max_2s_fuel_range_lbm_s=range;met.max_fuel_slew_lbm_s2=slew;met.settling_to_point1_rpm_s=settling;
met.recovery_1pct_speed_s=onePct;met.events_inside_1pct_throughout=insideCount;
end
