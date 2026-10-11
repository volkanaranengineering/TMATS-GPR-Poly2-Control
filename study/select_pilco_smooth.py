"""Select using 10% plant tuning only; write frozen policy before validation."""
import json
import numpy as np
import pandas as pd
from pilco_smooth import OUT
t=pd.read_csv(OUT/'tuning_results.csv');p=json.loads((OUT/'protocol.json').read_text())
assert len(t)==len(p['weights'])
t['rmse_ratio']=t.rmse_rpm/p['base_rmse'];t['ringing_ratio']=t.ringing_excess_TV_lbm_s/p['base_ringing']
t['selection_score']=np.maximum(t.rmse_ratio,t.ringing_ratio)
t.loc[~t.accepted.astype(bool),'selection_score']=np.inf
assert np.isfinite(t.selection_score.min())
s=t.loc[t.selection_score.idxmin()]
selected={k:float(s[k]) for k in ['Kp','Ki','weight','selection_score','rmse_rpm','ringing_excess_TV_lbm_s']}
selected.update(candidate=int(s.candidate),Kd=0,selection_rule=p['selection'],validation_used=False)
(OUT/'selected_policy.json').write_text(json.dumps(selected,indent=2));t.to_csv(OUT/'selection_scores.csv',index=False)
print(json.dumps(selected,indent=2))
