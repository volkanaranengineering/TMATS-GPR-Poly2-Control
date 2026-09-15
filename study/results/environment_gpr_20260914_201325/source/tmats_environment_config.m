function [MWS,ENV]=tmats_environment_config(MWS,altitude_m,isa_delta_C)
% T-MATS atmosphere: altitude feet, temperature departure degF; Mach zero.
% Approach the new environment during preparation to avoid an artificial jump.
ENV.altitude_m=altitude_m;ENV.isa_delta_C=isa_delta_C;
ENV.profile=[0 0;5 0;30 isa_delta_C*1.8;300 isa_delta_C*1.8];
MWS.in.t_vec=[0 5 30 300];
MWS.in.Alt=[0 0 altitude_m altitude_m]/.3048;
assignin('base','ENV',ENV);assignin('base','MWS',MWS);
end
