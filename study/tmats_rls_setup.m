function [MWS,RLS] = tmats_rls_setup()
% Setup for GasTurbine_Dyn_Template_GPT_RLS.mdl.
MWS=tmats_gpt_setup();
t=(0:4000)'*.015;
MWS.in.t_vec=[0 5 10 30+t'];
MWS.in.Ndmd=[10000 10000 9000 9500-500*cos(2*pi*(.1*t'+.0075*t'.^2))];
MWS.in.Alt=zeros(size(MWS.in.t_vec));
MWS.in.SimTime=90;
RLS=struct('Ts',.015,'na',5,'nb',5,'nk',1,'lambda',.999, ...
    'P0',1e4,'yScale',1000,'uScale',1,'startTime',30, ...
    'flowTolerance',1e-9,'iterationLimit',200,'minPhiNorm',1e-10);
assignin('base','MWS',MWS); assignin('base','RLS',RLS);
end
