# Fuel-to-acceleration recursive ARX estimation

Created and simulated `GasTurbine_Dyn_Template_GPT_RLS.mdl` in MATLAB R2018b. The new model adds a discrete, online RLS observer to the GPT gas-turbine copy. It identifies actual fuel flow (lbm/s) to shaft acceleration (rpm/s), using the plant's direct `Ndot` signal. The original GPT file is unchanged.

The observer is very accurate for one-step prediction, but its frozen fuel-only model has moderate independent validation accuracy. These are different capabilities: the one-step predictor uses measured past acceleration; the frozen simulation does not.

## Results

Fit is `100*(1-norm(reference-estimate)/norm(reference-mean(reference)))`, not R-squared. RMSE is in rpm/s. Chirp scores cover only the converged 0–17.790 s prefix, including initial learning transients.

| Evaluation | Fit | RMSE |
|---|---:|---:|
| Online RLS, prediction before current-sample update | 99.8729% | 0.7050 |
| Persistence baseline: previous measured acceleration | 97.1964% | 15.5513 |
| Online RLS, final five valid seconds | 99.8779% | 0.8860 |
| Evolving coefficients, own predicted acceleration history | 91.2627% | 48.4640 |
| Final frozen ARX, chirp free-run | 88.3707% | 64.5050 |
| Final frozen ARX, independent 60 s ramp/hold free-run | 62.6191% | 30.5107 |

The evolving-coefficient free-run check still receives coefficient updates learned from reference data; it is not independent validation. The frozen ramp test uses no ramp acceleration for parameter estimation or prediction feedback. Free-run filters start from zero normalized state after the equilibrium preparation. No validation-based parameter tuning was performed. The smaller ramp RMSE despite its lower fit reflects the ramp's smaller acceleration variation.

## Scenario and validity

The demanded speed is `9500-500*cos(2*pi*(0.1*t+0.0075*t^2))` rpm over 60 s: 9000–10000 rpm, with a linear frequency sweep from 0.1 to 1 Hz. A preceding 30 s preparation holds 10000 rpm to 5 s, ramps to 9000 rpm at 10 s and holds to 30 s. The simulation uses 0.015 s sampling and runs for 90 s total. The PI controller converts speed demand into actual fuel flow, which is the identification input.

The reference solver first fails the validity checks at chirp time **17.805 s** (absolute simulation time 47.805 s). Only 1187 samples through 17.790 s are usable, covering approximately 0.1–0.36685 Hz; 1185 RLS updates occur because near-zero initial regressors are skipped. Results do not establish accuracy over the complete requested 0.1–1 Hz sweep.

Updates require finite reference signals, flow residuals no greater than 1e-9, fewer than 200 inner solver iterations, nonnegative fuel and positive compressor stability margin. A failure latches the gate closed, freezes coefficients/covariance/history, and makes prediction output NaN. Restarting the simulation resets the latch. The full failed remainder is retained as diagnostic data, not training data.

The independent ramp profile has knots:

| Time (s) | 0 | 3 | 9 | 12 | 17 | 20 | 28 | 31 | 36 | 40 | 50 | 54 | 60 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Demand (rpm) | 9000 | 9000 | 9900 | 9900 | 9400 | 9400 | 9800 | 9800 | 9050 | 9050 | 10000 | 10000 | 10000 |

This gives ramps of +150, -100, +50, -150 and +95 rpm/s with intervening holds. Its entire 60 s evaluation passes the flow-residual and iteration checks; maximum absolute residual is 9.9971e-10.

## Estimator implementation

Orders are `na=5, nb=5, nk=1`, exactly ten estimated coefficients, with no extra intercept. Define `y=Ndot/1000` and `u=(Wf-0.9810869146824126)/1`. The fuel offset is measured during preparation and frozen at the chirp start. Each sample forms

```
phi(k) = [-y(k-1), ..., -y(k-5), u(k-1), ..., u(k-5)]'
yhat(k|k-1) = phi(k)' * theta(k-1)
```

Thus the delay is one sample, 15 ms. Multiply normalized predictions by 1000 to recover rpm/s. The controller is unchanged; the estimator does not feed back into the plant. Its reference is direct shaft acceleration, avoiding numerical differentiation of speed in this experiment.

Initialization: `theta=0`, `P=10000*eye(10)`. Forgetting factor `lambda=0.999` gives approximately 1000 samples, or 15 s, of effective memory. For each accepted sample:

```
Pprior = P / lambda
K = Pprior*phi / (1 + phi'*Pprior*phi)
theta = theta + K*(y - phi'*theta)
J = eye(10) - K*phi'
P = J*Pprior*J' + K*K'
P = (P + P')/2
```

This Joseph-form covariance update improves numerical robustness. The Simulink S-function publishes predictions and coefficient states before its Update method, preventing current-output leakage into the reported one-step prediction. Covariance represents algorithm information under its assumed scaling; it is not a calibrated parameter confidence interval.

The green `RLS Acceleration Observer` subsystem contains the estimator. `Acceleration Reference vs RLS` displays reference and prediction. Workspace logs include `RLS_reference`, `RLS_yhat`, `RLS_error`, `RLS_theta`, `RLS_Pdiag`, `RLS_status`, `RLS_phi`, `RLS_u0` and `RLS_flowErrors`. Status is `[update_enabled, fault_latched, updates_before_sample]`.

## Evolution and interpretation

The first 3 s prediction RMSE is 0.9218 rpm/s. The two-second rolling error decreases during early learning, then rises somewhat as chirp amplitude in acceleration and frequency increase. Its final-five-second fit remains 99.8779%. RLS lowers full-prefix RMSE about 22-fold versus persistence, so the improvement is substantial even against a strong smooth-signal baseline.

All sampled instantaneous ARX parameter sets have pole magnitudes below one; the final maximum magnitude is 0.978884. The adaptive own-output simulation also remains finite. Instantaneous pole stability alone is not a general stability guarantee for a time-varying model.

Several coefficients continue moving rather than settling. The normalized regressor matrix condition number is 1.0167e6 and its effective rank is 9 at a relative singular-value threshold of 1e-6. It is mathematically full rank, but the weakest direction is poorly identified. Total covariance trace rises from 100000 to 107324.6 despite contraction in some directions. The high one-step fit therefore does not establish convergence of all ten physical dynamic parameters.

The ramp free-run plot shows underpredicted positive acceleration and nonzero acceleration during some holds. This reveals a low-frequency/equilibrium mismatch that is much less visible in one-step prediction. A single local linear model trained on a short oscillatory record does not fully reproduce the nonlinear fuel-to-acceleration dynamics across the operating range.

## What works and what to improve

- **Works:** causal online updates, strong prediction accuracy, bounded simulated free-run behavior, explicit invalid-data protection, and a compact ten-coefficient estimator. The RLS arithmetic needs only a 10-by-10 covariance matrix and rank-one updates per sample; real-time execution timing was not benchmarked.
- **First priority:** obtain a fully converged excitation record spanning the required frequencies. Adjust demand amplitude/rate or controller/plant operating limits in a separately reviewed experiment. The current full-amplitude sweep cannot support a valid 60 s identification claim.
- **Improve excitation and conditioning:** collect longer valid chirps or multisine records at several equilibria, inspect singular values, and compare lower orders or resampling to avoid highly correlated adjacent 15 ms lags. Keep ten regressors if required, but consider stronger regularization or directional forgetting in poorly excited directions.
- **Improve free-run equilibrium behavior:** evaluate a speed-state formulation with acceleration derived from it, a physically constrained zero-DC fuel-to-acceleration model around equilibrium, or models scheduled by shaft speed. For a stable speed response, a settled fuel change should eventually give zero acceleration; the ramp holds expose this issue. Test any changes on a separate selection record, preserving the current ramp as a held-out benchmark.
- **Tune memory cautiously:** reducing lambda improves one-step fit slightly but greatly inflates covariance. The sensitivity results below do not justify choosing a smaller lambda solely for fit. Adaptation to a deliberately changing plant has not been tested.
- **For measured engine data:** direct Ndot is unavailable in many installations. Use a validated causal acceleration observer/filter and account for its delay. Closed-loop measurement noise can bias ordinary ARX least squares; investigate recursive output-error or instrumental-variable methods if noise tests show bias. The present ideal simulation does not establish noise robustness.
- **Maintain numerical safeguards:** covariance positivity and stability checks passed here. Stability projection or constrained parameter updates would be appropriate before deploying the estimator in control; the current observer only monitors the plant.

| Forgetting factor | One-step fit | RMSE (rpm/s) | Final pole radius | Final covariance trace |
|---|---:|---:|---:|---:|
| 1 | 99.8616% | 0.7675 | 0.97829 | 38717.8 |
| 0.999 (implemented) | 99.8729% | 0.7050 | 0.97888 | 107324.6 |
| 0.995 | 99.8934% | 0.5911 | 0.98095 | 4749947.8 |

## Verification

- Offline replay reproduces every logged pre-update coefficient exactly.
- Final coefficients match exponentially weighted batch least squares to relative error 4.44e-8.
- Final coefficients match MATLAB System Identification Toolbox `recursiveLS` to relative error 4.81e-10.
- Covariance remains positive definite; final minimum eigenvalue is 1.1637e-4.
- No coefficient changes or updates occur after the reference-failure gate latches.
- Against the original valid chirp, maximum plant speed difference is 4.18e-11 rpm and fuel difference is 7.16e-13 lbm/s.
- Original GPT MDL SHA256 remains `99D95A3F42A12DD42EE5C4353B8D3AE6DB2A54F7AC15A106FC72D0EEBBB31376`.

## Run and files

From the existing TMATSGPT folder, with its adjacent T-MATS libraries and standard example setup installed:

```matlab
tmats_rls_setup;
open_system('GasTurbine_Dyn_Template_GPT_RLS');
sim('GasTurbine_Dyn_Template_GPT_RLS');
```

The model also runs from the Simulink Run button after setup. Changing the scenario requires updating `MWS.in` after loading the model; loading invokes its default setup callback. `run_tmats_rls_batch` runs the chirp plus ramp and exits MATLAB, for command-line use. `analyze_tmats_rls_batch` analyzes the latest run and also exits MATLAB; call `analyze_tmats_rls` interactively instead.

The batch workflow uses the existing `tmp/wiener_ramp_directory.txt` and previous chirp results for its validation profile and unchanged-plant assertion. The archive is a bundle for this existing T-MATS workspace, not a standalone T-MATS distribution. The model itself only requires the supplied setup/S-function/step files and adjacent T-MATS installation.

`rls_valid_evolution.csv` contains estimates, reference, error, all ten coefficients, covariance diagonals and rolling metrics. `full_chirp_gate_diagnostics.csv` preserves the complete chirp gate history. `frozen_ramp_validation.csv` contains the independent comparison. `final_arx_coefficients.json` contains A/B polynomials, physical scaling and offset. MAT files retain full simulation and analysis data. PNGs show estimation evolution, free-run comparisons and gate behavior.
