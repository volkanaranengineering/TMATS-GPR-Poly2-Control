function validate_tmats_poly2()
root=fileparts(mfilename('fullpath'));out=fullfile(root,'results','poly2_inverse_20260915');f.poly=jsondecode(fileread(fullfile(out,'poly2_model.json')));
t=readtable(fullfile(out,'test_predictions.csv'));X=t{:,{'speed_rpm','acceleration_rpm_s','inlet_temperature_K','inlet_pressure_kPa'}};
[mu,g]=tmats_poly2_mean_gradient(f,X);meanError=max(abs(mu-t.poly2_prediction_lbm_s));assert(meanError<1e-10);
fd=zeros(size(g));for k=1:4,h=1e-5*f.poly.inputScale(k);xp=X;xm=X;xp(:,k)=xp(:,k)+h;xm(:,k)=xm(:,k)-h;fd(:,k)=(tmats_poly2_mean_gradient(f,xp)-tmats_poly2_mean_gradient(f,xm))/(2*h);end
gradientError=max(abs(g(:)-fd(:)));assert(gradientError<1e-8);
z=table(meanError,gradientError,'VariableNames',{'python_matlab_prediction_error','gradient_finite_difference_error'});writetable(z,fullfile(out,'implementation_checks.csv'));disp(z);
end
