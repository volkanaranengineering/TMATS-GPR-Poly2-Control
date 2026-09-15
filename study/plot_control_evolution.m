function plot_control_evolution
out='tmp/pdfs/control_evolution';if ~exist(out,'dir'),mkdir(out);end
dirs={'virtual_fuel_20260913_182229_028','virtual_fuel_ff_20260913_194955','virtual_fuel_uq_20260913_201212','virtual_fuel_uqup_20260913_231743'};
methods={'VirtualFuel','VirtualFuelFF','VirtualFuelUQ','VirtualFuelUQUp'};
names={'Initial inverse PI','FF + retuned PI','SD down','SD up'};
colors=[.3 .3 .3;.1 .35 .8;.1 .6 .35;.8 .3 .1];
f=figure('Visible','off','Color','w','Position',[10 10 1100 750]);
for j=1:4
 d=readtable(fullfile('results',dirs{j},['9000rpm_10pct_ramps_' methods{j} '.csv']));
 q=d.time_s>=69.8 & d.time_s<=74;
 subplot(2,1,1);hold on;plot(d.time_s(q)-60,d.Nmech(q)-9000,'Color',colors(j,:),'LineWidth',1.2);
 subplot(2,1,2);hold on;plot(d.time_s(q)-60,d.Wf(q),'Color',colors(j,:),'LineWidth',1.2);
end
subplot(2,1,1);ylabel('Actual speed error (rpm)');legend(names,'Location','best');title('9000 rpm, 10% load: first 0.3 s load ramp');grid on;xlim([9.8 14]);
subplot(2,1,2);ylabel('Fuel (lbm/s)');xlabel('Evaluation time (s)');grid on;xlim([9.8 14]);export(f,out,'early_zoom');
f=figure('Visible','off','Color','w','Position',[10 10 1050 600]);
s=linspace(0,6,601);x=max(0,min(1,(s-1)/2));plot(s,10.^(-(s/3).^2),'LineWidth',1.8);hold on;plot(s,1+3*x.^2-2*x.^3,'LineWidth',1.8);grid on;
xlabel('Maximum response SD / reference SD');ylabel('Gain multiplier');legend('Decreasing schedule','Increasing schedule','Location','best');title('Implemented uncertainty schedules');export(f,out,'schedules');
f=figure('Visible','off','Color','w','Position',[10 10 1100 700]);
for j=3:4
 d=readtable(fullfile('results',dirs{j},['9000rpm_10pct_ramps_' methods{j} '.csv']));q=d.time_s>=60;
 subplot(2,1,1);hold on;plot(d.time_s(q)-60,max(d.VF_sdSetpoint(q),d.VF_sdFeedback(q))/.00117869140423888,'Color',colors(j,:),'LineWidth',1.2);
 subplot(2,1,2);hold on;plot(d.time_s(q)-60,d.VF_gainFactor(q),'Color',colors(j,:),'LineWidth',1.2);
end
subplot(2,1,1);ylabel('Normalized maximum SD');title('9000 rpm, 10% load ramps: realized scheduling');legend(names(3:4),'Location','best');grid on;xlim([0 90]);
subplot(2,1,2);ylabel('Gain multiplier');xlabel('Evaluation time (s)');grid on;xlim([0 90]);export(f,out,'realized_schedule');
fprintf('CONTROL_EVOLUTION_FIGURES_COMPLETE\n');
end
function export(f,out,name)
set(findall(f,'Type','axes'),'FontSize',12);set(findall(f,'Type','legend'),'FontSize',10);p=get(f,'Position');set(f,'PaperUnits','inches','PaperSize',p(3:4)/96,'PaperPosition',[0 0 p(3:4)/96]);print(f,fullfile(out,[name '.pdf']),'-dpdf','-painters');close(f);
end
