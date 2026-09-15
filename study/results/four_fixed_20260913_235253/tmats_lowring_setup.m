function [MWS,DOB,PTO,VF]=tmats_lowring_setup()
% Selected fixed fuel-domain PI + GPR FF: 9500 rpm, 5% shaft-load steps.
% 90.35% less ringing than [3 60] on this tuning condition.
[MWS,DOB,PTO,VF]=tmats_virtual_fuel_ff_setup(9500,.05,[0 0 0],[2 30],true);
end
