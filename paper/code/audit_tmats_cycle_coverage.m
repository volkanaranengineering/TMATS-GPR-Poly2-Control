function audit_tmats_cycle_coverage(out)
% Offline audit of all three inverse-query branches; base PI gets shadow queries.
source=strtrim(fileread('tmp/environment_directory.txt'));s=load(fullfile(source,'environment_inverse_gpr_model.mat'),'model');m=s.model;
train=readtable(fullfile(source,'training_points.csv'));
X=train{:,{'speed_rpm','acceleration_rpm_s','inlet_temperature_K','inlet_pressure_kPa'}};
mu=mean(X);scale=std(X);Z=bsxfun(@rdivide,bsxfun(@minus,X,mu),scale);
facets=convhulln(Z);normal=zeros(size(facets,1),4);offset=zeros(size(facets,1),1);keep=false(size(offset));
for k=1:size(facets,1)
 v=Z(facets(k,:),:);[~,sing,V]=svd(bsxfun(@minus,v(2:end,:),v(1,:)));
 if sing(3,3)<1e-10,continue;end % Zero-volume simplices from coplanar training rows.
 n=V(:,end);b=v(1,:)*n;
 if b<0,n=-n;b=-b;end;assert(max(Z*n-b)<1e-7);normal(k,:)=n';offset(k)=b;keep(k)=true;
end
normal=normal(keep,:);offset=offset(keep);assert(size(normal,1)>4);
% Nearest-neighbour distance in the exact GP's kernel coordinates.
K=bsxfun(@rdivide,bsxfun(@rdivide,bsxfun(@minus,X,m.inputMean),m.inputScale),m.lengthScale');
dist=max(0,bsxfun(@plus,sum(K.^2,2),sum(K.^2,2)')-2*(K*K'));dist(1:size(dist,1)+1:end)=Inf;
loo=sort(sqrt(min(dist,[],2)));loo95=loo(ceil(.95*numel(loo)));records=[];
methods={'BasePI','R3'};if exist(fullfile(out,'R3_GPRFF.mat'),'file'),methods{3}='R3_GPRFF';end
if exist(fullfile(out,'R3_Poly2FF.mat'),'file'),methods{4}='R3_Poly2FF';end
for name=methods
 s=load(fullfile(out,[name{1} '.mat']),'d');d=s.d;ii=find(d.time_s>=60);
 a=zeros(height(d),1);prev=10000;state=0;p=exp(-.015/.03);
 for k=1:height(d),a(k)=p*state+(1-p)*(d.DOB_sensed(k)-prev)/.015;state=a(k);prev=d.DOB_sensed(k);end
 if ismember('VF_acceleration',d.Properties.VariableNames),assert(max(abs(a-d.VF_acceleration))<1e-7);end
 temp=[288.15;d.inlet_temperature_K(1:end-1)];pressure=[99.298;d.inlet_pressure_kPa(1:end-1)];
 Q=[d.DOB_request(ii) zeros(numel(ii),1) temp(ii) pressure(ii);d.DOB_sensed(ii) a(ii) temp(ii) pressure(ii);d.DOB_sensed(ii) zeros(numel(ii),1) temp(ii) pressure(ii)];
 branches=3;
 if ismember('FF_reference_acceleration',d.Properties.VariableNames),Q=[Q;d.DOB_request(ii) d.FF_reference_acceleration(ii) temp(ii) pressure(ii)];branches=4;end
 strict=any(bsxfun(@lt,Q,m.trainingInputRange(1,:))|bsxfun(@gt,Q,m.trainingInputRange(2,:)),2);
 tol=1e-8*(m.trainingInputRange(2,:)-m.trainingInputRange(1,:));
 box=any(bsxfun(@lt,Q,m.trainingInputRange(1,:)-tol)|bsxfun(@gt,Q,m.trainingInputRange(2,:)+tol),2);
 Qz=bsxfun(@rdivide,bsxfun(@minus,Q,mu),scale);Qk=bsxfun(@rdivide,bsxfun(@rdivide,bsxfun(@minus,Q,m.inputMean),m.inputScale),m.lengthScale');
 excess=zeros(size(Q,1),1);nearest=excess;
 for first=1:512:size(Q,1)
  ix=first:min(first+511,size(Q,1));excess(ix)=max(bsxfun(@minus,Qz(ix,:)*normal',offset'),[],2);
  dd=max(0,bsxfun(@plus,sum(Qk(ix,:).^2,2),sum(K.^2,2)')-2*Qk(ix,:)*K');nearest(ix)=sqrt(min(dd,[],2));
 end
 covered=~box&excess<=1e-7;
 z=struct('method',name{1},'query_count',size(Q,1),'strict_box_outside_percent',100*mean(strict), ...
 'box_outside_percent',100*mean(box),'hull_outside_percent',100*mean(excess>1e-7), ...
 'max_hull_excess',max(excess),'covered_all',all(covered),'NN_distance_max',max(nearest), ...
 'training_LOO_NN95',loo95,'NN_above_training95_percent',100*mean(nearest>loo95));
 if isempty(records),records=z;else,records(end+1)=z;end
 audit=table(repmat(d.time_s(ii)-60,branches,1),reshape(repmat(1:branches,numel(ii),1),[],1),Q(:,1),Q(:,2),Q(:,3),Q(:,4),strict,box,excess,nearest,covered, ...
  'VariableNames',{'test_time_s','branch','speed_rpm','acceleration_rpm_s','temperature_K','pressure_kPa','strict_box_outside','box_outside','hull_excess','kernel_NN_distance','covered'});
 writetable(audit,fullfile(out,[name{1} '_coverage_queries.csv']));
end
writetable(struct2table(records),fullfile(out,'coverage_summary.csv'));
writetable(array2table(m.trainingInputRange,'VariableNames',{'speed_rpm','acceleration_rpm_s','temperature_K','pressure_kPa'}),fullfile(out,'training_bounds.csv'));
fprintf('COVERAGE_AUDIT_COMPLETE\n');disp(struct2table(records));
end
