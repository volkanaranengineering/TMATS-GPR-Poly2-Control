"""Full total-degree-two OLS inverse; same training/held-out split as frozen GP."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
root=Path(__file__).resolve().parent;src=Path((root/'tmp/environment_directory.txt').read_text().strip());out=root/'results/poly2_inverse_20260915';out.mkdir(parents=True,exist_ok=True)
cols=['speed_rpm','acceleration_rpm_s','inlet_temperature_K','inlet_pressure_kPa']
tr=pd.read_csv(src/'training_points.csv');te=pd.read_csv(src/'test_200_points.csv')
X=tr[cols].to_numpy();y=tr.fuel_lbm_s.to_numpy();mean=X.mean(axis=0);scale=X.std(axis=0,ddof=1)
pairs=[(i,j) for i in range(4) for j in range(i+1,4)]
def design(X):
 z=(X-mean)/scale
 return np.column_stack([np.ones(len(z)),z,z*z]+[z[:,i]*z[:,j] for i,j in pairs])
A=design(X);coef,res,rank,s=np.linalg.lstsq(A,y,rcond=None);assert rank==15
metrics=[]
for name,data in [('training',tr),('test',te)]:
 pred=design(data[cols].to_numpy())@coef;e=pred-data.fuel_lbm_s.to_numpy()
 metrics.append(dict(split=name,points=len(data),rmse_lbm_s=float(np.sqrt(np.mean(e*e))),mae_lbm_s=float(np.mean(abs(e))),max_error_lbm_s=float(np.max(abs(e))),r2=float(1-np.sum(e*e)/np.sum((data.fuel_lbm_s-data.fuel_lbm_s.mean())**2))))
 data=data.copy();data['poly2_prediction_lbm_s']=pred;data['poly2_error_lbm_s']=e;data.to_csv(out/(name+'_predictions.csv'),index=False)
model=dict(inputMean=mean.tolist(),inputScale=scale.tolist(),coefficients=coef.tolist(),pairs=(np.array(pairs)+1).tolist(),trainingInputRange=[X.min(axis=0).tolist(),X.max(axis=0).tolist()],rank=int(rank),condition_number=float(s[0]/s[-1]),training_points=len(tr),test_points=len(te))
(out/'poly2_model.json').write_text(json.dumps(model,indent=2));pd.DataFrame(metrics).to_csv(out/'fit_metrics.csv',index=False)
terms=['1']+[f'z{i}' for i in range(1,5)]+[f'z{i}^2' for i in range(1,5)]+[f'z{i+1}*z{j+1}' for i,j in pairs]
pd.DataFrame({'term':terms,'coefficient_lbm_s':coef}).to_csv(out/'coefficients.csv',index=False)
pd.DataFrame({'input':cols,'mean':mean,'scale':scale}).to_csv(out/'normalization.csv',index=False)
print(pd.DataFrame(metrics).to_string(index=False));print('Design rank',rank,'condition number',s[0]/s[-1])
