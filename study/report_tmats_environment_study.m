function report_tmats_environment_study(out)
files=dir(fullfile(out,'comparison_*.mat'));metrics=[];
for k=1:numel(files),s=load(fullfile(out,files(k).name),'met');if isempty(metrics),metrics=s.met;else,metrics(end+1)=s.met;end;end
T=sortrows(struct2table(metrics),{'environment','method'});writetable(T,fullfile(out,'comparison_summary.csv'));
assert(height(T)==73);g=readtable(fullfile(out,'test_200_points.csv'));tr=readtable(fullfile(out,'training_points.csv'));
f=newfig(1100,700);
subplot(2,2,1);scatter(tr.inlet_temperature_K,tr.inlet_pressure_kPa,15,tr.environment,'filled');hold on;plot(g.inlet_temperature_K,g.inlet_pressure_kPa,'k.');
 xlabel('Inlet total temperature (K)');ylabel('Inlet total pressure (kPa)');title('Training environment coverage');grid on;
subplot(2,2,2);scatter(g.fuel_lbm_s,g.prediction_lbm_s,25,g.environment,'filled');hold on;lim=[min(g.fuel_lbm_s) max(g.fuel_lbm_s)];plot(lim,lim,'k--');
 xlabel('T-MATS fuel (lbm/s)');ylabel('Inverse GPR fuel (lbm/s)');title('200 held-out predictions');grid on;
subplot(2,2,3);errorbar((1:200)',g.error_lbm_s,1.95996398454*g.response_sd_lbm_s,'.');ylabel('Fuel error (lbm/s)');xlabel('Test point index');title('Error and nominal 95% response interval');grid on;
subplot(2,2,4);scatter(g.speed_rpm,g.acceleration_rpm_s,22,g.error_lbm_s,'filled');colorbar;xlabel('Speed (rpm)');ylabel('Acceleration (rpm/s)');title('Held-out fuel error by shaft state');grid on;
export(f,out,'gpr_validation');
methods={'BasePI','InvGPR_PI_GPRFF','InvGPR_PI'};labels={'Base PI','InvGPR PI + FF','InvGPR PI'};
colors=[.12 .32 .64;.82 .28 .1;.15 .6 .35];styles={'-','-','--'};data=cell(3,1);
for j=1:3,s=load(fullfile(out,['comparison_36_' methods{j} '.mat']),'d');data{j}=s.d;end
windows=[60 150;69.5 77;89.5 102.5;119.5 137];names={'target_overview','target_zoom_first','target_zoom_second','target_zoom_third'};
for w=1:4
 f=newfig(1100,850);
 for ax=1:4
  subplot(4,1,ax);hold on;
  for j=1:3
   d=data{j};ix=d.time_s>=windows(w,1)&d.time_s<=windows(w,2);
   y=d.Nmech-9500;if ax==2,y=d.Wf;elseif ax==3,y=d.DOB_SM;elseif ax==4,y=d.PTO_hp;end
   plot(d.time_s(ix)-60,y(ix),'Color',colors(j,:),'LineStyle',styles{j},'LineWidth',1.25);
  end
  xlim(windows(w,:)-60);grid on;
  yl={'Speed error (rpm)','Fuel (lbm/s)','Surge margin (%)','Load (hp)'};ylabel(yl{ax});
  if ax==1,title(sprintf('4000 m / ISA+5 / 9500 rpm / 10%% step load'));legend(labels,'Location','best','Orientation','horizontal');end
  if ax==4,xlabel('Evaluation time (s); absolute time minus 60 s');end
 end
 export(f,out,names{w});
end
f=newfig(1100,650);d=data{2};ix=d.time_s>=69.5&d.time_s<=77;
subplot(3,1,1);plot(d.time_s(ix)-60,d.VF_setpoint(ix),d.time_s(ix)-60,d.VF_feedback(ix));legend('GP setpoint','GP feedback');ylabel('Virtual fuel (lbm/s)');grid on;
subplot(3,1,2);plot(d.time_s(ix)-60,2*d.VF_error(ix),d.time_s(ix)-60,d.VF_integral(ix));legend('Proportional correction','Residual integral');ylabel('Fuel terms (lbm/s)');grid on;
subplot(3,1,3);plot(d.time_s(ix)-60,d.DOB_acceleration(ix),d.time_s(ix)-60,d.VF_acceleration(ix));legend('Plant acceleration','Filtered sensed acceleration');ylabel('Acceleration (rpm/s)');xlabel('Evaluation time (s)');grid on;
export(f,out,'target_components');
fields={'rmse_rpm','ringing_excess_TV_lbm_s','recovery_1pct_speed_s','settling_to_point1_rpm_s'};
titles={'Speed RMSE (rpm)','Fuel ringing excess TV (lbm/s)','Recovery to 1% speed band (s)','Recovery to 0.1 rpm band (s)'};
for k=1:4
 f=newfig(1100,500);range=T.(fields{k})(T.environment<=35);range=range(isfinite(range));lim=[min(range) max(range)];if diff(lim)<1e-6,lim=lim+[0 1];end
 for j=1:2
  subplot(1,2,j);v=T(strcmp(T.method,methods{j})&T.environment<=35,:);[~,order]=sort(v.environment);v=v(order,:);
  z=reshape(v.(fields{k}),5,7);z=z(:,[7 5 2 1 3 4 6]);
  h=imagesc([-30 -20 -10 0 10 20 30],[0 2500 5000 7500 10000],z);set(h,'AlphaData',~isnan(z));set(gca,'YDir','normal','Color',[.8 .8 .8]);caxis(lim);colorbar;
  xlabel('ISA departure (C)');ylabel('Altitude (m)');title([labels{j} ': ' titles{k}]);
  set(gca,'XTick',-30:10:30,'YTick',0:2500:10000);
  for row=1:5,for col=1:7,str='X';if isfinite(z(row,col)),str=sprintf('%.2g',z(row,col));elseif isinf(z(row,col)),str='NR';end;text((col-4)*10,(row-1)*2500,str,'HorizontalAlignment','center','Color','k','FontSize',11,'BackgroundColor','w');end;end
 end
 export(f,out,['grid_' fields{k}]);
end
events=[];starts=[70.005 75 90 100.005 120 135];ends=[75 90 100.005 120 135 150];
for j=1:3
 d=data{j};
 for k=1:6
  q=find(d.time_s>=starts(k)-1e-8&d.time_s<ends(k)-1e-8);e=d.Nmech(q)-9500;
  iq=find(d.time_s>=starts(k)-1e-8&d.time_s<=starts(k)+2+1e-8);u=d.Wf(iq);
  ev=struct('method',methods{j},'event',k,'edge_evaluation_s',starts(k)-60,'peak_error_rpm',max(abs(e)), ...
   'rmse_rpm',sqrt(mean(e.^2)),'ringing_excess_TV_lbm_s',sum(abs(diff(u)))-abs(u(end)-u(1)), ...
   'recovery_1pct_s',recover(d.time_s(q),e,95,starts(k)), ...
   'recovery_point1_rpm_s',recover(d.time_s(q),e,.1,starts(k)));
  if isempty(events),events=ev;else,events(end+1)=ev;end
 end
end
writetable(struct2table(events),fullfile(out,'target_events.csv'));
equivalence=table(max(abs(data{2}.Nmech-data{3}.Nmech)),max(abs(data{2}.Wf-data{3}.Wf)), ...
 'VariableNames',{'maximum_speed_difference_rpm','maximum_fuel_difference_lbm_s'});
writetable(equivalence,fullfile(out,'target_inverse_pair_equivalence.csv'));
s=load(fullfile(out,'environment_inverse_gpr_model.mat'),'model');model=s.model;
x=[9500 0 mean(data{2}.inlet_temperature_K) mean(data{2}.inlet_pressure_kPa)];
q=data{2}.time_s>=60;x(3)=mean(data{2}.inlet_temperature_K(q));x(4)=mean(data{2}.inlet_pressure_kPa(q));
h=[1 1 .1 .01];derivative=zeros(1,4);
for k=1:4,dx=zeros(1,4);dx(k)=h(k);derivative(k)=(predict_tmats_environment_gpr(model,x+dx)-predict_tmats_environment_gpr(model,x-dx))/(2*h(k));end
[mu,sd]=predict_tmats_environment_gpr(model,x);
local=table(mu,sd,derivative(1),derivative(2),derivative(3),derivative(4), ...
 'VariableNames',{'nominal_fuel_lbm_s','response_sd_lbm_s','dFuel_dSpeed','dFuel_dAcceleration','dFuel_dTemperature','dFuel_dPressure'});
writetable(local,fullfile(out,'target_gp_local.csv'));
fprintf('ENVIRONMENT_FIGURES_COMPLETE\n');
end
function r=recover(t,e,band,start)
last=find(abs(e)>band,1,'last');r=0;if ~isempty(last),r=Inf;if last<numel(t),r=t(last+1)-start;end;end
end
function f=newfig(w,h)
f=figure('Visible','off','Color','w','Position',[50 50 w h]);
end
function export(f,out,name)
set(findall(f,'Type','axes'),'FontSize',12);set(findall(f,'Type','legend'),'FontSize',11);
set(f,'PaperPositionMode','auto');pos=get(f,'Position');set(f,'PaperUnits','inches','PaperSize',pos(3:4)/96,'PaperPosition',[0 0 pos(3:4)/96]);
print(f,fullfile(out,[name '.pdf']),'-dpdf','-painters');print(f,fullfile(out,[name '.png']),'-dpng','-r130');close(f);
end
