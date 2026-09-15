function report_tmats_r3_cycle(out)
if ~isempty(strfind(out,'covered_cycle')),audit_tmats_cycle_coverage(out);end
a=load(fullfile(out,'BasePI.mat'),'d');b=load(fullfile(out,'R3.mat'),'d');D={a.d,b.d};col=[.25 .25 .25;.58 .25 .7];
labelsMethods={'Base PI','R3'};
if exist(fullfile(out,'R3_GPRFF.mat'),'file')
 b=load(fullfile(out,'R3_GPRFF.mat'),'d');D{3}=b.d;col(3,:)=[.1 .6 .35];labelsMethods={'Base PI','R3 feedback only','R3 + static GPR FF'};
end
if exist(fullfile(out,'R3_Poly2FF.mat'),'file')
 b=load(fullfile(out,'R3_Poly2FF.mat'),'d');D{4}=b.d;col(4,:)=[.1 .4 .85];labelsMethods{4}='R3 + quadratic FF';
end
f=figure('Visible','off','Color','w','Position',[30 30 1100 920]);
for k=1:4
 subplot(4,1,k);hold on;
 for j=1:numel(D)
  d=D{j};q=d.time_s>=60;y=d.Nmech;if k==2,y=d.Nmech-d.DOB_request;elseif k==3,y=d.Wf;elseif k==4,y=d.DOB_SM;end
  plot(d.time_s(q)-60,y(q),'Color',col(j,:),'LineWidth',1.2);
 end
 if k==1,d=D{1};q=d.time_s>=60;plot(d.time_s(q)-60,d.DOB_request(q),'--','Color',[.2 .6 .7]);legend([labelsMethods {'Request'}],'Location','best');title('Four speed cycles with a changing atmosphere');end
 labels={'Speed (rpm)','Tracking error (rpm)','Fuel (lbm/s)','Surge margin (%)'};ylabel(labels{k});grid on;xlim([0 120]);if k==4,xlabel('Test time (s)');end
end
export(f,out,'cycle_overview');
f=figure('Visible','off','Color','w','Position',[30 30 1100 850]);d=b.d;q=d.time_s>=60;t=d.time_s(q)-60;
subplot(4,1,1);yyaxis left;plot(t,d.altitude_m(q),'LineWidth',1.3);ylabel('Altitude (m)');yyaxis right;plot(t,d.isa_delta_C(q),'LineWidth',1.3);ylabel('ISA departure (C)');title('Ambient inputs and R3 model diagnostics');grid on;
subplot(4,1,2);yyaxis left;plot(t,d.inlet_temperature_K(q),'LineWidth',1.3);ylabel('Inlet T (K)');yyaxis right;plot(t,d.inlet_pressure_kPa(q),'LineWidth',1.3);ylabel('Inlet P (kPa)');grid on;
subplot(4,1,3);plot(t,d.compressor_NcMap(q),'LineWidth',1.3);hold on;plot([0 120],[1.05 1.05],'r--');ylabel('Compressor Nc');grid on;
subplot(4,1,4);stairs(t,d.VR_fallback(q),'Color',col(2,:),'LineWidth',1.3);hold on;stairs(t,d.VF_outside(q),'--','Color',[.8 .4 .2]);ylim([-.1 1.3]);legend('R3 fallback','GP input range flag','Location','best');ylabel('Active flag');xlabel('Test time (s)');grid on;
export(f,out,'cycle_environment');
for win=1:2
 range=[0 30];if win==2,range=[45 75];end
 f=figure('Visible','off','Color','w','Position',[30 30 1100 850]);
 for k=1:3
  subplot(3,1,k);hold on;
  for j=1:numel(D),d=D{j};q=d.time_s>=60+range(1)&d.time_s<=60+range(2);y=d.Nmech;if k==2,y=d.Nmech-d.DOB_request;elseif k==3,y=d.Wf;end;plot(d.time_s(q)-60,y(q),'Color',col(j,:),'LineWidth',1.3);end
  if k==1,plot(d.time_s(q)-60,d.DOB_request(q),'--','Color',[.2 .6 .7]);legend([labelsMethods {'Request'}],'Location','best');title(sprintf('Cycle detail: %g-%g s',range));end
  labs={'Speed (rpm)','Tracking error (rpm)','Fuel (lbm/s)'};ylabel(labs{k});grid on;xlim(range);if k==3,xlabel('Test time (s)');end
 end
 export(f,out,sprintf('cycle_zoom_%d',win));
end
fprintf('CYCLE_FIGURES_COMPLETE\n');
end
function export(f,out,name)
set(findall(f,'Type','axes'),'FontSize',12);set(findall(f,'Type','legend'),'FontSize',10);p=get(f,'Position');set(f,'PaperUnits','inches','PaperSize',p(3:4)/96,'PaperPosition',[0 0 p(3:4)/96]);print(f,fullfile(out,[name '.pdf']),'-dpdf','-painters');print(f,fullfile(out,[name '.png']),'-dpng','-r130');close(f);
end
