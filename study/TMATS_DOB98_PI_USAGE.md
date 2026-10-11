# Identified 9800-rpm DOB + tuned PI

This controller replaces previous PILCO in the revised comparison. The original studies are preserved.

## Selected configuration

- Local plant: P(q) = 9.3039586704 q / (1 - 0.9789097769 q), q = one 0.015 s delay.
- Identification point: 9800 rpm; fuel trim 2.5303511983 lbm/s.
- Identical physical speed sensors: 0.05 s, unity gain, noise off.
- DOB includes the nominal sensor dynamics in its filtered inverse.
- DOB cutoff: 1 Hz; compensation gain: 0.7; compensation bound: +/-1 lbm/s.
- PI tuned with DOB enabled: Kp = 0.048, Ki = 0.05.
- Shared fuel command bounds: 0.2 to 4 lbm/s.

## Use in the existing T-MATS workspace

Run `tmats_dob98_setup` and open `GasTurbine_DOB98_PI.mdl`. The model preload callback also initializes the selected configuration. Test time zero corresponds to simulation time 60 s, after preparation. The combined cycle ramps 9000 to 10000 rpm in five seconds, applies a common 2789.650 hp load from relative seconds 10 to 15, then records recovery through second 25.005.

For full reproduction:

1. Run `dob98_identify_batch.m` in MATLAB (the batch exits MATLAB).
2. Run `fit_dob98_model.py` with NumPy, pandas and SciPy.
3. Run `dob98_tune_batch.m` in MATLAB. It caches completed candidates.
4. Run `validate_dob98.py` for independent filter replay checks.
5. Run `build_dob98_deliverables.py` for the report source and video. It also requires the prior comparison builders and traces in this workspace.
6. Compile `output/pdf/dob98_pi_source/DOB98_PI_Comparison.tex` with LaTeX.

## Results

Full-cycle RMSE: base PI 5.408 rpm; DOB with original PI 4.546 rpm; DOB with tuned PI 3.142 rpm. The tuned DOB+PI ramp RMSE is 2.459 rpm and load/recovery RMSE is 3.710 rpm. Base PI still has slightly lower ramp RMSE (2.161 rpm).

Independent local-model free-run validation fit: 99.783%. Independent four-second ramp with 5% load: 2.024 rpm full-cycle RMSE with frozen selected gains. Nominal model fit is local, and the requested combined cycle was used for PI tuning. Other comparator gains were not retuned. These results do not establish robust stability or equal-budget superiority.

The ZIP contains this study's model, code, data, report and video. It is an add-on to the existing T-MATS workspace, not a standalone MATLAB distribution.
