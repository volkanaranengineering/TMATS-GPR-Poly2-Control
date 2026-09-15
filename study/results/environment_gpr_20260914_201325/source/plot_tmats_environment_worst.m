function plot_tmats_environment_worst(out)
methods={'BasePI','InvGPR_PI_GPRFF'};colors=[.12 .32 .64;.82 .28 .1];
f=figure('Visible','off','Color','w','Position',[50 50 1100 620]);
for j=1:2
 s=load(fullfile(out,['comparison_33_' methods{j} '.mat']),'d');d=s.d;q=d.time_s>=119.5&d.time_s<=150;
 subplot(3,1,1);hold on;plot(d.time_s(q)-60,d.Nmech(q)-9500,'Color',colors(j,:),'LineWidth',1.3);ylabel('Speed error (rpm)');grid on;
 subplot(3,1,2);hold on;plot(d.time_s(q)-60,d.Wf(q),'Color',colors(j,:),'LineWidth',1.3);ylabel('Fuel (lbm/s)');grid on;
 subplot(3,1,3);hold on;plot(d.time_s(q)-60,d.compressor_NcMap(q),'Color',colors(j,:),'LineWidth',1.3);ylabel('Compressor Nc map');grid on;xlabel('Evaluation time (s)');
end
subplot(3,1,1);plot([59.5 90],[95 95],'k:');plot([59.5 90],[-95 -95],'k:');legend('Base PI','InvGPR PI + FF','1% speed limits','Location','best');title('Map-flagged example: 5000 m / ISA-30 / 9500 rpm / 10% load');
subplot(3,1,3);plot([59.5 90],[1.05 1.05],'k:');legend('Base PI','InvGPR PI + FF','Map upper boundary','Location','best');
set(findall(f,'Type','axes'),'FontSize',12);set(findall(f,'Type','legend'),'FontSize',11);
set(f,'PaperUnits','inches','PaperSize',[1100 620]/96,'PaperPosition',[0 0 1100 620]/96);
print(f,fullfile(out,'grid_worst_zoom.pdf'),'-dpdf','-painters');print(f,fullfile(out,'grid_worst_zoom.png'),'-dpng','-r130');close(f);
end
