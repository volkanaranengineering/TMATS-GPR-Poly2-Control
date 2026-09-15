function [MWS,DOB,PTO,VF,ENV]=tmats_poly9250_tuned_setup()
root=fileparts(mfilename('fullpath'));s=load(fullfile(root,'results','poly2_tune9250_20260915','selected.mat'),'gains');
[MWS,DOB,PTO,VF,ENV]=tmats_poly9250_setup(s.gains);
end
