function select_tmats_gpr_remedies(out)
files=dir(fullfile(out,'tune_e36_c*.mat'));metrics=[];
for k=1:numel(files),s=load(fullfile(out,files(k).name),'met');if ~isfield(s.met,'accelWeight'),s.met.accelWeight=1;end;s.met=orderfields(s.met);if isempty(metrics),metrics=s.met;else,metrics(end+1)=s.met;end;end
T=sortrows(struct2table(metrics),'candidate');C=tmats_gpr_remedy_candidates();assert(height(T)==size(C,1));
source=strtrim(fileread('tmp/environment_directory.txt'));b=load(fullfile(source,'comparison_36_BasePI.mat'),'met');
T.rmse_ratio=T.rmse_rpm/b.met.rmse_rpm;T.ringing_ratio=T.ringing_excess_TV_lbm_s/b.met.ringing_excess_TV_lbm_s;
T.joint_score=max(T.rmse_ratio,T.ringing_ratio);T.joint_score(~T.accepted)=Inf;
T.beats_base_both=T.accepted&T.rmse_ratio<1&T.ringing_ratio<1;
selected=zeros(1,3);
for mode=1:3,q=find(T.mode==mode);[~,k]=min(T.joint_score(q));selected(mode)=T.candidate(q(k));end
save(fullfile(out,'selected_remedies.mat'),'selected','C');writetable(T,fullfile(out,'tuning_summary.csv'));
disp(T(ismember(T.candidate,selected),:));fprintf('SELECTED_REMEDIES %d %d %d\n',selected);
end
