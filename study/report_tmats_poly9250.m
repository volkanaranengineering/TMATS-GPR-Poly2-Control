function report_tmats_poly9250(out)
t=readtable(fullfile(out,'tuning_scores.csv'));s=load(fullfile(out,'selected.mat'),'selected');ids=[0 1 s.selected.candidate];names={'Base PI','Poly2 original gains','Poly2 retuned'};colors=[.3 .3 .3;.15 .45 .85;.1 .6 .35];D=cell(1,3);
for j=1:3,s=load(fullfile(out,sprintf('candidate_%02d.mat',ids(j))),'d');D{j}=s.d;end
f=figure('Visible','off','Color','w','Position',[30 30 1100 800]);
for k=1:3
 subplot(3,1,k);hold on;for j=1:3,d=D{j};q=d.time_s>=60;y=d.Nmech-9250;if k==2,y=d.Wf;elseif k==3,y=d.DOB_SM;end;plot(d.time_s(q)-60,y(q),'Color',colors(j,:),'LineWidth',1.2);end
 labs={'Speed error (rpm)','Fuel (lbm/s)','Surge margin (%)'};ylabel(labs{k});grid on;xlim([0 90]);if k==1,legend(names,'Location','best');title('9250 rpm / 0 m / ISA 0 / 10% shaft-load pulses');end;if k==3,xlabel('Evaluation time (s)');end
end
export(f,out,'poly9250_overview');
f=figure('Visible','off','Color','w','Position',[30 30 1150 850]);
windows=[9.8 13;14.8 18];for row=1:2,for col=1:2
 subplot(2,2,(row-1)*2+col);hold on;for j=1:3,d=D{j};q=d.time_s>=60+windows(row,1)&d.time_s<=60+windows(row,2);y=d.Nmech-9250;if col==2,y=d.Wf;end;plot(d.time_s(q)-60,y(q),'Color',colors(j,:),'LineWidth',1.2);end
 grid on;xlim(windows(row,:));xlabel('Evaluation time (s)');if col==1,ylabel('Speed error (rpm)');else,ylabel('Fuel (lbm/s)');end;if row==1,title('Load application');else,title('Load removal');end;if row==1&&col==1,legend(names,'Location','best');end
end;end
export(f,out,'poly9250_zoom');
f=figure('Visible','off','Color','w','Position',[30 30 1000 650]);q=t.candidate>0&t.accepted;scatter(t.rmse_rpm(q),t.ringing_excess_TV_lbm_s(q),45,t.joint_score(q),'filled');hold on;
for j=1:3,z=t(t.candidate==ids(j),:);plot(z.rmse_rpm,z.ringing_excess_TV_lbm_s,'ko','MarkerSize',12);text(z.rmse_rpm,z.ringing_excess_TV_lbm_s,[' ' names{j}]);end
grid on;xlabel('RMSE (rpm)');ylabel('Fuel ringing excess TV (lbm/s)');title('Tested gain candidates; lower left is better');colorbar;export(f,out,'poly9250_tuning');
end
function export(f,out,name)
set(findall(f,'Type','axes'),'FontSize',12);set(findall(f,'Type','legend'),'FontSize',10);p=get(f,'Position');set(f,'PaperUnits','inches','PaperSize',p(3:4)/96,'PaperPosition',[0 0 p(3:4)/96]);print(f,fullfile(out,[name '.pdf']),'-dpdf','-painters');print(f,fullfile(out,[name '.png']),'-dpng','-r130');close(f);
end
