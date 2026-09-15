function [MWS,DOB,PTO,VF,ENV]=tmats_r3_covered_cycle_setup()
% Preserve the ambient route and frozen feedback; narrow motion to GP coverage.
[MWS,DOB,PTO,VF,ENV]=tmats_r3_cycle_setup();
DOB.rate=150;
t=DOB.request(:,1);t(2:end)=t(2:end)+DOB.Ts/4;phase=mod(max(0,t-60),30);
r=9450+100*min(phase/5,1);q=phase>=15;r(q)=9550-100*min((phase(q)-15)/5,1);
r(t<60)=interp1([0 5 10 60],[10000 10000 9450 9450],t(t<60));
DOB.request(:,2)=r;
assignin('base','DOB',DOB);
end
