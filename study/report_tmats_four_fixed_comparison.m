function report_tmats_four_fixed_comparison(out)
if nargin<1,out=strtrim(fileread('tmp/four_fixed_directory.txt'));end
cfg=load(fullfile(out,'configuration.mat'));T=readtable(fullfile(out,'summary.csv'));assert(height(T)==44);
labels={'Base PI','Base PI + GP FF','Inverse GP PI','Inverse GP PI + FF'};
colors=[.45 .45 .45;0 .45 .75;.8 .25 .1;.05 .55 .35];styles={'-','--','-',':'};
D=cell(11,4);equivalence=[];
for c=1:11
 for j=1:4
  shape='ramps';if cfg.cases(c,3)==0,shape='steps';end
  tag=sprintf('%drpm_%02dpct_%s_%s.mat',cfg.cases(c,1),round(100*cfg.cases(c,2)),shape,cfg.methods{j});
  z=load(fullfile(out,tag));D{c,j}=z.d;
 end
 a=D{c,3};b=D{c,4};ok=a.valid&b.valid&a.time_s>=30;
 % Only evaluate before the first invalid solve in either trajectory.
 bad=find(~a.valid|~b.valid,1);if ~isempty(bad),ok(bad:end)=false;end
 equivalence=[equivalence;c max(abs(a.Nmech(ok)-b.Nmech(ok))) max(abs(a.Wf(ok)-b.Wf(ok)))]; %#ok<AGROW>
end
writetable(array2table(equivalence,'VariableNames',{'case_index','maximum_speed_difference_rpm','maximum_fuel_difference_lbm_s'}),fullfile(out,'inverse_pair_equivalence.csv'));
for group=1:3
 if group==1,ids=1:4;name='overview_9000';elseif group==2,ids=5:8;name='overview_9500';else,ids=[9 10 11];name='overview_steps';end
 f=figure('Visible','off','Color','w','Position',[20 20 1250 260*numel(ids)]);
 for k=1:numel(ids)
  c=ids(k);
  for j=1:4
   d=prefix(D{c,j});subplot(numel(ids),2,2*k-1);plot(d.time_s-60,d.Nmech-cfg.cases(c,1),styles{j},'Color',colors(j,:),'LineWidth',1);hold on;
   subplot(numel(ids),2,2*k);plot(d.time_s-60,d.Wf,styles{j},'Color',colors(j,:),'LineWidth',1);hold on;
  end
  subplot(numel(ids),2,2*k-1);grid on;xlim([0 90]);ylabel('Speed error [rpm]');title(sprintf('%g rpm, %g%% shaft load',cfg.cases(c,1),100*cfg.cases(c,2)));
  if k==1,legend(labels,'Location','best','FontSize',8);end
  subplot(numel(ids),2,2*k);grid on;xlim([0 90]);ylabel('Fuel flow [lbm/s]');
 end
 xlabel('Time after preparation [s]');export(f,name);
end
for c=[11 9 8]
 f=figure('Visible','off','Color','w','Position',[20 20 1150 780]);
 for j=1:4
  d=prefix(D{c,j});t=d.time_s-60;
  subplot(2,2,1);plot(t,d.Nmech-cfg.cases(c,1),styles{j},'Color',colors(j,:),'LineWidth',1.2);hold on;
  subplot(2,2,2);plot(t,d.Wf,styles{j},'Color',colors(j,:),'LineWidth',1.2);hold on;
  subplot(2,2,3);plot(t,d.Nmech-cfg.cases(c,1),styles{j},'Color',colors(j,:),'LineWidth',1.2);hold on;
  subplot(2,2,4);plot(t,d.Wf,styles{j},'Color',colors(j,:),'LineWidth',1.2);hold on;
 end
 for p=1:4,subplot(2,2,p);grid on;if p<=2,xlim([9.9 12]);else,xlim([14.9 17]);end;xlabel('Time after preparation [s]');end
 subplot(2,2,1);ylabel('Speed error [rpm]');title('Load application');legend(labels,'Location','best','FontSize',8);
 subplot(2,2,2);ylabel('Fuel flow [lbm/s]');title('Load application: fuel detail');
 subplot(2,2,3);ylabel('Speed error [rpm]');title('Load removal');
 subplot(2,2,4);ylabel('Fuel flow [lbm/s]');title('Load removal: fuel detail');
 if ~any(cellfun(@(z)any(z.time_s>=74.9 & z.time_s<=77 & z.valid),D(c,:)))
  for pp=3:4,subplot(2,2,pp);text(.5,.5,'All runs invalid before this event','Units','normalized','HorizontalAlignment','center','FontSize',11);end
 end
 export(f,sprintf('zoom_case_%02d',c));
end
S=readtable(fullfile(cfg.tuning,'tuning.csv'));selection=load(fullfile(cfg.tuning,'selected_gains.mat'));
old=load(fullfile(cfg.tuning,'candidate_01.mat'));new=load(fullfile(cfg.tuning,sprintf('candidate_%02d.mat',selection.selected)));
f=figure('Visible','off','Color','w','Position',[20 20 1150 780]);
for j=1:2
 d=old.d;col=[.75 .2 .15];if j==2,d=new.d;col=[.05 .5 .35];end
 subplot(2,2,1);plot(d.time_s-60,d.Nmech-9500,'Color',col);hold on;
 subplot(2,2,2);plot(d.time_s-60,d.Wf,'Color',col);hold on;
 subplot(2,2,3);plot(d.time_s-60,d.Wf,'Color',col);hold on;
end
subplot(2,2,1);grid on;xlim([9.9 15]);ylabel('Speed error [rpm]');title('9500 rpm, 5% steps');legend('Previous 3,60','Selected lower gains');
subplot(2,2,2);grid on;xlim([10 11]);ylabel('Fuel flow [lbm/s]');title('First second after load application');
subplot(2,2,3);grid on;xlim([15 16]);ylabel('Fuel flow [lbm/s]');xlabel('Time after preparation [s]');title('First second after load removal');
subplot(2,2,4);scatter(S.ringing_excess_TV_lbm_s,S.rmse_rpm,35,[.25 .4 .6],'filled');hold on;
for j=1:height(S),text(S.ringing_excess_TV_lbm_s(j),S.rmse_rpm(j),sprintf(' %g,%g',S.Kp(j),S.Ki(j)),'FontSize',8);end
grid on;xlabel('Fuel ringing: excess total variation [lbm/s]');ylabel('Speed RMSE [rpm]');title('Gain search tradeoff');export(f,'tuning_tradeoff');
f=figure('Visible','off','Color','w','Position',[20 20 1150 580]);d=D{11,4};t=d.time_s-60;
subplot(2,1,1);plot(t,d.VF_setpoint,t,d.VF_feedback);grid on;xlim([9.9 17]);ylabel('Virtual fuel [lbm/s]');legend('g(reference,0)','g(sensed speed,estimated acceleration)');
subplot(2,1,2);plot(t,d.DOB_command,t,d.VF_setpoint,t,d.VF_integral,t,cfg.gains(1)*d.VF_error);grid on;xlim([9.9 17]);ylabel('Fuel contributions [lbm/s]');xlabel('Time after preparation [s]');legend('Command','Feedforward','Integral','Proportional');export(f,'controller_components');
function export(f,name)
 set(findall(f,'Type','axes'),'FontSize',14);set(findall(f,'Type','legend'),'FontSize',12);
 p=get(f,'Position');sz=p(3:4)/100;
 set(f,'PaperUnits','inches','PaperSize',sz,'PaperPosition',[0 0 sz],'PaperPositionMode','manual');
 print(f,fullfile(out,[name '.pdf']),'-dpdf','-painters');print(f,fullfile(out,[name '.png']),'-dpng','-r130');close(f);
end
end
function d=prefix(d)
bad=find(~d.valid,1);if ~isempty(bad),d=d(1:max(1,bad-1),:);end
end
