function [MWS,DOB,PTO,VF,ENV]=tmats_r3_poly2_setup()
[MWS,DOB,PTO,VF,ENV]=tmats_r3_covered_cycle_setup();
root=fileparts(mfilename('fullpath'));VF.poly=jsondecode(fileread(fullfile(root,'results','poly2_inverse_20260915','poly2_model.json')));
assignin('base','VF',VF);
end
