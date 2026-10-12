# Exact GPR acceleration model

Run `out = run_tmats_exact_gpr;` from this directory in MATLAB with Statistics and Machine Learning Toolbox. The runner uses existing T-MATS experiments and writes a timestamped folder under `results`. It does not launch plant simulations.

Load the trained model and evaluate any speed/fuel pairs:

```matlab
s = load(fullfile(out,'exact_gpr_model.mat'),'model');
[acceleration, uncertainty, interval95, latentSD] = ...
    predict_tmats_exact_gpr(s.model, 9500, 1.2);
```

Speed is rpm; fuel is lbm/s. All returned acceleration and uncertainty quantities are rpm/s. `uncertainty` is predictive response standard deviation, `interval95` has lower/upper columns, and `latentSD` is uncertainty in the latent GP function. The exported predictor uses base MATLAB only. Vector inputs are supported.

The continuous-time model is `dN/dt = f(N,Wf)`. Training uses an exact ARD squared-exponential GP with maximum-likelihood hyperparameters and 600 input-space-selected points from valid chirp and ramp experiments. The 100 **test** points come exclusively from a separate validation ramp. A target grid spans 9000–10000 rpm, and the nearest unique real recorded sample is selected for each target. The results report actual speeds and target mismatches. Test points are not training points or inducing points.

`test_100_points.csv` contains reference acceleration, predictions, both standard deviations, and intervals. `training_points.csv` preserves source IDs and row numbers. `exact_gpr_model.mat` includes both the native MATLAB GP and its exported Cholesky representation. `REPORT.md`, `metrics.csv`, and `validation.png` describe validation and uncertainty coverage.

The model applies to the fixed ambient, zero external shaft-load conditions in the source experiments. Predictions outside the sampled speed/fuel support require additional validation. GP uncertainty is conditional on the fitted model and does not guarantee coverage of unmodeled disturbances. Exact inference does not imply exact turbine physics.

Method: Volkan Aran's 2019 thesis, *Flexible and Robust Control of Heavy Duty Diesel Engine Airpath Using Data Driven Disturbance Observers and GPR Models*, section 5.1, equations 5.5–5.14, and section 6.2.1. The local thesis is `tmp/dob/Volkan_Aran_PhD_2019.pdf`. Per-input length scales follow equation 5.8. Posterior uncertainty follows thesis reference [92], [Rasmussen and Williams, chapter 2](https://gaussianprocess.org/gpml/chapters/RW2.pdf). Implementation uses [MATLAB fitrgp](https://www.mathworks.com/help/stats/fitrgp.html) with both fitting and prediction set to `exact`.
