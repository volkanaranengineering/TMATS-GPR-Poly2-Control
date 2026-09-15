function diagnose_tmats_inverse_feedback(out)
source=strtrim(fileread('tmp/environment_directory.txt'));s=load(fullfile(source,'environment_inverse_gpr_model.mat'),'model');m=s.model;
f.model=rmfield(m,{'L','Z','trainingRows'});f.scaledTraining=bsxfun(@rdivide,m.Z,m.lengthScale');rows=[];
for c=1:36
 s=load(fullfile(source,sprintf('trim_%02d.mat',c)),'d','ENV');d=s.d;q=d.time_s>=55;
 x=[9500 0 mean(d.inlet_temperature_K(q)) mean(d.inlet_pressure_kPa(q))];
 [mu,g]=tmats_gp_mean_gradient(f,x);h=[.01 .01 .001 .001];fd=zeros(1,4);
 for j=1:4,dx=zeros(1,4);dx(j)=h(j);fd(j)=(predict_tmats_environment_gpr(m,x+dx)-predict_tmats_environment_gpr(m,x-dx))/(2*h(j));end
 assert(max(abs(g-fd))<1e-6);
 z=struct('environment',c,'altitude_m',s.ENV.altitude_m,'isa_delta_C',s.ENV.isa_delta_C, ...
  'temperature_K',x(3),'pressure_kPa',x(4),'fuel_mean',mu,'speed_slope',g(1),'accel_slope',g(2), ...
  'equivalent_P',2*g(1)+30*g(2),'equivalent_I',30*g(1),'equivalent_D',2*g(2), ...
  'inverse_tail_tau_s',g(2)/g(1),'NcMap',9500/sqrt(x(3)/288.15)/10000,'gradient_check',max(abs(g-fd)));
 if isempty(rows),rows=z;else,rows(end+1)=z;end
end
T=struct2table(rows);writetable(T,fullfile(out,'inverse_slope_diagnosis.csv'));disp(T([33 36],:));
fprintf('NEGATIVE_SPEED_SLOPES %d\n',sum(T.speed_slope<=0));
end
