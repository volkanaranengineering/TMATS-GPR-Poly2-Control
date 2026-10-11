function [MWS,DOB,PTO,VF,ENV]=tmats_pilco_setup()
root=fileparts(mfilename('fullpath'));
p=jsondecode(fileread(fullfile(root,'results','pilco_quadratic_pi_20261010','policy.json')));
[MWS,DOB,PTO,VF,ENV]=tmats_poly9250_setup([p.Kp p.Ki 0]);
assignin('base','VF',VF);
end
