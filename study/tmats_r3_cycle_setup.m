function [MWS,DOB,PTO,VF,ENV]=tmats_r3_cycle_setup()
% Fixed R3 and base PI: 60 s preparation, then a 120 s moving-environment cycle.
[MWS,DOB,PTO,VF,ENV]=tmats_gpr_remedy_setup(3);
DOB.rate=200; % Allow the requested 190 rpm/s ramps and the 195 rpm/s preparation.
t=(0:12000)'*DOB.Ts;rel=max(0,t-60);phase=mod(rel,30);
low=9025;high=9975;
r=low+(high-low)*min(phase/5,1);
q=phase>=15;r(q)=high-(high-low)*min((phase(q)-15)/5,1);
r(t<60)=interp1([0 5 10 60],[10000 10000 low low],t(t<60));
DOB.request=[t r];DOB.request(2:end,1)=t(2:end)-DOB.Ts/4;
DOB.disturbance=[t zeros(size(t))];PTO.profile=[t zeros(size(t))];
PTO.duration_s=120;PTO.reference_hp=0;PTO.nominal_rpm=9500;
ENV.profile=[0 0;5 0;30 -36;60 -36;120 36;180 0];
ENV.altitude_m=NaN;ENV.isa_delta_C=NaN;
ENV.cycle_knots=[0 0 -20;60 10000 20;120 0 0];
MWS.in.t_vec=[0 60 120 180];MWS.in.Alt=[0 0 10000 0]/.3048;MWS.in.SimTime=180;
assignin('base','MWS',MWS);assignin('base','DOB',DOB);assignin('base','PTO',PTO);assignin('base','VF',VF);assignin('base','ENV',ENV);
end
