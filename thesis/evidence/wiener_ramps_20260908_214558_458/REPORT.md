# Wiener identification: actual fuel flow to shaft speed

Fitted in MATLAB R2018b, System Identification Toolbox 9.9, using `nlhw`,
`unitgain` on the input and `poly1d(2)` on the output.

## Selected model and free-run fits

| Record | Fit, NRMSE (%) | RMSE (rpm) |
|---|---:|---:|
| Training: converged chirp prefix | 94.0903 | 21.4845 |
| Ramp/hold model-selection record | 87.1724 | 39.5604 |
| Held-out ramp/hold final validation | 87.0954 | 41.9286 |

Selected orders **[nb nf nk] = [1 3 0]** at
Ts=0.015 s. nb is the number of numerator coefficients excluding delay
zeros; nf is denominator degree. Both are capped at 10 (the cap is per polynomial,
not a total of 10 across both). Output nonlinearity degree is exactly 2.
Maximum absolute linear-block pole is 0.9786791711; the selected
linear block is stable. Maximum absolute final-validation error is
58.5106 rpm.

Fit = 100 * (1 - norm(y-yhat)/norm(y-mean(y))). These are free-run simulation
scores with zero normalized initial states, not one-step prediction scores.
Measured validation speed is not fed back to the predictor or used to estimate
initial states. The coefficient-only implementation and MATLAB `compare` metric
were checked against the saved predictions; the exported metrics were independently
recomputed from the CSV files.

## Training and validation separation

Training uses ONLY the first 1187 samples, 0-17.790 s, of the
previous 9000-10000 rpm chirp. Every sample at and after the first solver failure
at 17.805 s was excluded. Consequently the accepted chirp frequency coverage is
approximately 0.1-0.36685 Hz, not the requested full
0.1-1 Hz. The discarded samples were not interpolated, repaired or used for fitting.

Ramp/hold records are separate simulations, each with 60 s retained after a 30 s
preparation interval. The selection and final validation records use different
levels, ramp rates and hold durations. All ramp profiles stay within 9000-10000 rpm.
Across them, nonzero rate magnitudes are 50, 60, 95, 100 and 150 rpm/s.
Actual fuel flow Wf (lbm/s), rather than the speed-demand signal, is the model input;
mechanical shaft speed Nmech (rpm) is the output.

Only the chirp estimates model parameters and normalization. The selection ramp
chooses model order and whether training-only refinement is retained. The final
validation ramp is evaluated after that choice, without refitting.
44 candidate order/delay structures were tested, with up to
80 iterations per candidate and up to 200 for final refinement. The coarse search
tests all nb/nf pairs 1-4 and equal nb/nf orders 5-10, with delays 0 and 1; local
neighboring orders are then tested. "Best" means best selection fit among this
search, not a proof of a global optimum or an exhaustive search of all orders.
Candidate errors and scores are retained in candidate_scores.csv.

## Accepted simulation checks

| Record | Max normalized flow residual | Max iterations | Min fuel (lbm/s) | Min stability margin (%) |
|---|---:|---:|---:|---:|
| Selection | 9.9944e-10 | 30 | 0.9337 | 16.6316 |
| Validation | 9.9968e-10 | 20 | 0.8548 | 15.9367 |

Both entire 90 s source runs pass the 1e-9 flow tolerance and 200-iteration limit.
Recorded fuel remains positive and compressor stability margin remains positive.
The original GPT model and PI controller were not changed to obtain these runs.
These are noise-free synthetic closed-loop experiments. Fit on these trajectories
does not establish validity for failed high-frequency chirps, abrupt full-range
steps, untested operating conditions or measurement noise. The Wiener structure
is an approximation of the gas-turbine dynamics.

## Numerical model

Let u_n=(Wf-u0)/su; v=filter(B,F,u_n); Nmech=y0+sy*polyval(p,v),
with zero filter initial states and coefficients ordered as MATLAB expects:

```text
B = [1]
F = [1, -2.746098163319219, 2.550083469024761, -0.8028568299992156]
p = [-1.328480990017108e-07, 0.001843948442874731, -0.001341555354298684]  # [quadratic, linear, constant]
u0 = 0.9810869146816966 lbm/s
su = 1.108919409314424 lbm/s
y0 = 9000.000000000004 rpm
sy = 363.6986568026227 rpm
```

Leading zeros in B already implement nk. Do not add the delay again.
Normalization is part of the saved model wrapper; it must be applied exactly.
For other starting operating points, consistent filter initial states are needed.

## Use in MATLAB

```matlab
s = load('best_wiener_model.mat');
disp(s.bestModel)
% Full toolbox model, with the supplied normalized final validation data:
compare(s.zv, s.bestModel, Inf, compareOptions('InitialCondition','zero'))

% Coefficient-only implementation, physical fuel -> physical rpm:
d = readtable('validation_data.csv');
Nhat = predict_wiener_gpt(d.Wf, 'best_wiener_model.mat');
```

## Files

- best_wiener_model.mat: selected idnlhw model, coefficients, scales, metrics,
  iddata estimation/selection/validation objects and predicted outputs.
- model_coefficients.json and fit_metrics.json: portable numerical model and scores.
- identification_data.mat: data tables, normalized iddata objects and scaling.
- training_chirp_valid.csv: only the accepted training segment.
- selection_data.csv and validation_data.csv: converged ramp/hold measurements.
- selection_profile.csv and validation_profile.csv: ramp breakpoints.
- *_predictions.csv: actual output, simulated output and residuals.
- candidate_scores.csv and search_checkpoint.mat: search results and candidate models.
- wiener_fit.png: training and held-out validation comparison and errors.
- experiments.mat: ramp data, metadata and original simulation-directory references.
- reproduction scripts and MATLAB logs: included for traceability. Simulation
  scripts require the original project layout and adjacent T-MATS installation.
