function report_tmats_static_ff(out)
report_tmats_r3_cycle(out);
a=load(fullfile(out,'R3.mat'),'d');b=load(fullfile(out,'R3_GPRFF.mat'),'d');D={a.d,b.d};colors=[.58 .25 .7;.1 .6 .35];
names={'GPR feedback only','GPR + static FF'};
if exist(fullfile(out,'R3_Poly2FF.mat'),'file'),s=load(fullfile(out,'R3_Poly2FF.mat'),'d');D{3}=s.d;colors(3,:)=[.1 .4 .85];names{3}='Quadratic + static FF';end
f=figure('Visible','off','Color','w','Position',[30 30 1100 800]);
for k=1:3
 subplot(3,1,k);hold on;
 for j=1:numel(D),d=D{j};q=d.time_s>=60;v=d.FF_total;if k==2,v=d.VF_integral;elseif k==3,v=d.VR_proportional_term;end;plot(d.time_s(q)-60,v(q),'Color',colors(j,:),'LineWidth',1.3);end
 labels={'Static GP FF (lbm/s)','Integral state (lbm/s)','P / damping term (lbm/s)'};ylabel(labels{k});grid on;xlim([0 120]);
 if k==1,legend(names,'Location','best');title('Control-command components: FF uses g(request,0,T,P)');end
 if k==3,xlabel('Test time (s)');end
end
set(findall(f,'Type','axes'),'FontSize',12);set(findall(f,'Type','legend'),'FontSize',10);p=get(f,'Position');set(f,'PaperUnits','inches','PaperSize',p(3:4)/96,'PaperPosition',[0 0 p(3:4)/96]);print(f,fullfile(out,'static_ff_components.pdf'),'-dpdf','-painters');print(f,fullfile(out,'static_ff_components.png'),'-dpng','-r130');close(f);
end
