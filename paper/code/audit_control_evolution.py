from pathlib import Path
import pandas as pd
import json
root=Path(__file__).resolve().parent
dirs={
'early':'virtual_fuel_uqup_20260913_231743', 'fixed':'four_fixed_20260913_235253',
'environment':'environment_gpr_20260914_201325','remedies':'gpr_remedies_20260914_220633',
'cycle':'r3_ambient_cycle_20260915','covered':'r3_covered_cycle_20260915_final',
'poly':'r3_poly2_challenger_20260915','tune':'poly2_tune9250_20260915'}
def read(key,name):return pd.read_csv(root/'results'/dirs[key]/name)
early=read('early','comparison_all_methods.csv')
print('EARLY\n',early.to_string(index=False))
fixed=read('fixed','summary.csv')
print('FIXED\n',fixed[['case_index','rpm','fraction','shape','method','accepted','rmse_rpm','ringing_excess_TV_lbm_s','settling_to_point1_rpm_s']].to_string(index=False))
env=read('environment','comparison_summary.csv')
print('ENV target\n',env[env.environment==36].to_string(index=False))
print('ENV validity',env.groupby('method').accepted.agg(['count','sum']).to_dict())
rem=read('remedies','remedy_comparison.csv')
print('REMEDY target\n',rem[rem.environment==36].to_string(index=False))
print('REMEDY grid',rem[rem.environment<=35].groupby('method').accepted.agg(['count','sum']).to_dict())
sl=read('remedies','inverse_slope_diagnosis.csv')
print('SLOPES\n',sl[sl.environment.isin([1,36])|(sl.speed_slope<=0)].to_string(index=False))
print('COVERAGE\n',read('covered','coverage_summary.csv').to_string(index=False))
print('ENV HELDOUT',read('environment','test_200_points.csv').groupby('environment').size().to_dict())
