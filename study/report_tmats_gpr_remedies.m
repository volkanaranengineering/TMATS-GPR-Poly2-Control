function report_tmats_gpr_remedies(out)
source=strtrim(fileread('tmp/environment_directory.txt'));s=load(fullfile(out,'selected_remedies.mat'),'selected');selected=s.selected;
records=[];target=cell(1,5);names={'Base PI','Previous inverse PI','R1 retuned inverse PI','R2 split feedback','R3 normalized feedback'};
for c=1:36
 for j=1:5
  if j<=2,old={'BasePI','InvGPR_PI_GPRFF'};file=fullfile(source,sprintf('comparison_%02d_%s.mat',c,old{j}));
  elseif c==36,file=fullfile(out,sprintf('tune_e36_c%02d.mat',selected(j-2)));
  else,file=fullfile(out,sprintf('transfer_e%02d_c%02d.mat',c,selected(j-2)));end
  s=load(file,'d','met');if c==36,target{j}=s.d;end
  z=unify(s.met,c,j,names{j});if isempty(records),records=z;else,records(end+1)=z;end
 end
end
T=struct2table(records);assert(height(T)==180);writetable(T,fullfile(out,'remedy_comparison.csv'));
colors=[.25 .25 .25;.8 .4 .3;.15 .45 .8;.2 .65 .35;.58 .25 .7];styles={'-','--','-','-','-'};
f=newfig(1100,700);V=readtable(fullfile(out,'tuning_summary.csv'));hold on;h=gobjects(1,3);
for j=1:3,q=V.mode==j&V.accepted;h(j)=scatter(V.rmse_rpm(q),V.ringing_excess_TV_lbm_s(q),35,colors(j+2,:),'filled');end
b=T(T.environment==36&T.method_id==1,:);old=T(T.environment==36&T.method_id==2,:);
plot([b.rmse_rpm b.rmse_rpm],ylim,'k:');plot(xlim,[b.ringing_excess_TV_lbm_s b.ringing_excess_TV_lbm_s],'k:');
plot(old.rmse_rpm,old.ringing_excess_TV_lbm_s,'kp','MarkerFaceColor','k','MarkerSize',12);
for j=1:3,q=V.candidate==selected(j);plot(V.rmse_rpm(q),V.ringing_excess_TV_lbm_s(q),'ko','MarkerSize',13);text(V.rmse_rpm(q),V.ringing_excess_TV_lbm_s(q),sprintf(' R%d',j));end
grid on;xlabel('Speed RMSE (rpm)');ylabel('Fuel ringing excess TV (lbm/s)');title('Tuning: lower left of both dotted lines beats base PI');legend(h,names(3:5),'Location','best');export(f,out,'remedy_tuning');
f=newfig(1100,780);
for ax=1:3
 subplot(3,1,ax);hold on;
 for j=1:5,d=target{j};q=d.time_s>=60;y=d.Nmech-9500;if ax==2,y=d.Wf;elseif ax==3,y=d.DOB_SM;end;plot(d.time_s(q)-60,y(q),'Color',colors(j,:),'LineStyle',styles{j},'LineWidth',1.2);end
 grid on;labels={'Speed error (rpm)','Fuel (lbm/s)','Surge margin (%)'};ylabel(labels{ax});
 if ax==1,title('4000 m / ISA+5 / 9500 rpm / 10% load');legend(names,'Location','best','NumColumns',2);end
 if ax==3,xlabel('Evaluation time (s)');end
end
export(f,out,'remedy_overview');
windows=[69.75 72.5;74.75 78];figNames={'remedy_load_zoom','remedy_unload_zoom'};
for w=1:2
 f=newfig(1150,850);
 for row=1:3
  for col=1:2
   subplot(3,2,(row-1)*2+col);hold on;
   for j=[1 2 row+2],d=target{j};q=d.time_s>=windows(w,1)&d.time_s<=windows(w,2);y=d.Nmech-9500;if col==2,y=d.Wf;end
    plot(d.time_s(q)-60,y(q),'Color',colors(j,:),'LineStyle',styles{j},'LineWidth',1.2);
   end
   grid on;xlim(windows(w,:)-60);if col==1,ylabel('Speed error (rpm)');else,ylabel('Fuel (lbm/s)');end
   title(names{row+2});if row==1,legend(names([1 2 row+2]),'Location','best');end
   if row==3,xlabel('Evaluation time (s)');end
  end
 end
 export(f,out,figNames{w});
end
f=newfig(1150,850);
for j=1:3
 q=T.environment<=35&T.method_id==j+2;v=T(q,:);b=T(T.environment<=35&T.method_id==1,:);
 for k=1:2
  if k==1,z=v.rmse_rpm./b.rmse_rpm;titleText='RMSE / base PI';else,z=v.ringing_excess_TV_lbm_s./b.ringing_excess_TV_lbm_s;titleText='Ringing / base PI';end
  z=reshape(z,5,7);z=z(:,[7 5 2 1 3 4 6]);subplot(3,2,2*(j-1)+k);h=imagesc(-30:10:30,0:2500:10000,z);set(h,'AlphaData',~isnan(z));set(gca,'YDir','normal','Color',[.8 .8 .8]);caxis([0 2]);colorbar;
  title(sprintf('R%d: %s',j,titleText));ylabel('Altitude (m)');xlabel('ISA departure (C)');set(gca,'XTick',-30:10:30,'YTick',0:2500:10000);
  for a=1:5,for bcol=1:7,str='X';if isfinite(z(a,bcol)),str=sprintf('%.2g',z(a,bcol));end;text((bcol-4)*10,(a-1)*2500,str,'HorizontalAlignment','center','FontSize',9,'BackgroundColor','w');end;end
 end
end
export(f,out,'remedy_grid_ratios');
f=newfig(1100,650);
for ax=1:3
 subplot(3,1,ax);hold on;
 for j=1:5
  if j<=2,old={'BasePI','InvGPR_PI_GPRFF'};s=load(fullfile(source,sprintf('comparison_33_%s.mat',old{j})),'d');
  else,s=load(fullfile(out,sprintf('transfer_e33_c%02d.mat',selected(j-2))),'d');end
  d=s.d;q=d.time_s>=60;bad=find(~d.valid,1);if ~isempty(bad),q=q&d.time_s<d.time_s(bad);end
  y=d.Nmech-9500;if ax==2,y=d.Wf;elseif ax==3,y=d.compressor_NcMap;end
  plot(d.time_s(q)-60,y(q),'Color',colors(j,:),'LineStyle',styles{j},'LineWidth',1.2);
 end
 grid on;if ax==1,ylabel('Speed error (rpm)');title('Map-flagged stress check: 5000 m / ISA-30');legend(names,'Location','best','NumColumns',2);
 elseif ax==2,ylabel('Fuel (lbm/s)');else,ylabel('Compressor Nc map');xlabel('Evaluation time (s)');end
end
export(f,out,'remedy_cold_case');
fprintf('REMEDY_REPORT_FIGURES_COMPLETE\n');
end
function z=unify(m,c,j,label)
z=struct('environment',c,'method_id',j,'method',label);
fields={'accepted','altitude_m','isa_delta_C','Kp','Ki','Kd','accelTau','accelWeight','rmse_rpm','peak_rpm', ...
 'ringing_excess_TV_lbm_s','recovery_1pct_speed_s','settling_to_point1_rpm_s','minimum_margin_percent', ...
 'max_fuel_slew_lbm_s2','fuel_peak_lbm_s','iae_rpm_s','fuel_limit_percent','compressor_Nc_outside_percent','gp_outside_percent','fallback_percent'};
for k=1:numel(fields),v=NaN;if isfield(m,fields{k}),v=m.(fields{k});end;z.(fields{k})=v;end
end
function f=newfig(w,h)
f=figure('Visible','off','Color','w','Position',[50 50 w h]);
end
function export(f,out,name)
set(findall(f,'Type','axes'),'FontSize',12);set(findall(f,'Type','legend'),'FontSize',10);
pos=get(f,'Position');set(f,'PaperUnits','inches','PaperSize',pos(3:4)/96,'PaperPosition',[0 0 pos(3:4)/96]);
print(f,fullfile(out,[name '.pdf']),'-dpdf','-painters');print(f,fullfile(out,[name '.png']),'-dpng','-r130');close(f);
end
