# Inverse exact GPR fuel estimation

The inverse model maps **speed [rpm] and acceleration [rpm/s] to fuel flow [lbm/s]**. It uses an exact ARD squared-exponential Gaussian process, with predictive uncertainty and a 95% response interval.

Train and validate in MATLAB:

```matlab
out = run_tmats_inverse_gpr;
s = load(fullfile(out,'inverse_gpr_model.mat'),'model');
[fuel, uncertainty, interval95, latentSD] = ...
    predict_tmats_inverse_gpr(s.model,9500,100);
```

Training requires Statistics and Machine Learning Toolbox. The saved exported predictor needs base MATLAB only. Matching row or column vectors are accepted and outputs are columns; `interval95` has lower and upper columns. Multiply fuel and its uncertainty by `0.45359237` for kg/s.

For feedforward estimation, supply current speed and desired acceleration. The GP does not include a speed controller, actuator limits, or closed-loop validation. It was learned under fixed ambient conditions and zero external shaft load. Noisy measured acceleration introduces additional input uncertainty that these intervals do not propagate.

The runner reuses the previous forward study's 600 training samples and the same 100 held-out test samples in the 9000–10000 rpm band. It learns fuel directly from speed and plant acceleration. The forward GP is not used to generate training inputs or target labels. You can pass the forward study directory explicitly with `run_tmats_inverse_gpr(forwardDirectory)`.

Outputs are saved to `results/inverse_gpr_<timestamp>`: `inverse_gpr_model.mat`, `test_100_points.csv`, `training_points.csv`, `metrics.csv`, `REPORT.md`, and `validation.png`. The report distinguishes measured coverage from nominal 95% coverage.

Method follows Aran's thesis (2019), section 5.1 and section 6.2.1 on inverse feedforward modeling, and its reference [92], Rasmussen and Williams, *Gaussian Processes for Machine Learning*, chapter 2. A separately fitted inverse GP is not necessarily an algebraic inverse of the forward model.
