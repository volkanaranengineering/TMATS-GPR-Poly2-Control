function select_tmats_poly9250(out)
t=readtable(fullfile(out,'summary.csv'));old=t(t.candidate==1,:);
t.rmse_ratio=t.rmse_rpm/old.rmse_rpm;t.ringing_ratio=t.ringing_excess_TV_lbm_s/old.ringing_excess_TV_lbm_s;t.joint_score=max(t.rmse_ratio,t.ringing_ratio);
t.joint_score(~t.accepted|t.candidate==0)=Inf;[~,k]=min(t.joint_score);selected=t(k,:);assert(selected.accepted==1);gains=[selected.Kp selected.Ki selected.Kd];
save(fullfile(out,'selected.mat'),'selected','gains');writetable(t,fullfile(out,'tuning_scores.csv'));writetable(selected,fullfile(out,'selected.csv'));disp(selected);
root=fileparts(mfilename('fullpath'));src='GasTurbine_PolyCompare_R3_Poly2FF';load_system(src);set_param(src,'CloseFcn','');name='GasTurbine_Poly2_9250_Tuned';save_system(src,fullfile(root,[name '.mdl']));close_system(src,0);load_system(name);
set_param(name,'CloseFcn','','PreLoadFcn','tmats_poly9250_tuned_setup;','Description','Poly2 static-FF PID tuned at 9250 rpm, sea level ISA 0. See TMATS_POLY9250_USAGE.md.');tmats_poly9250_tuned_setup;set_param(name,'SimulationCommand','update');save_system(name);close_system(name,0);
fprintf('POLY9250_SELECTED_AND_MODEL_SAVED\n');
end
