# RLS study repeated with basic Simulink blocks

The new model is `GasTurbine_Dyn_Template_GPT_RLS_Blocks.mdl`. Its complete acceleration observer is implemented using basic Simulink blocks; there are **zero S-functions and zero MATLAB Function blocks inside the observer**. The T-MATS reference plant retains its existing component S-functions. MATLAB R2018b successfully compiled and simulated the chirp and independent ramp/hold experiments.

## Implementation

Double-click the green `RLS Acceleration Observer` subsystem. The top level contains input sampling, normalization, ten explicit scalar history delays, coefficient/covariance states, update switches, output scaling and logging. The nested `RLS matrix arithmetic` subsystem exposes every calculation. `Validity and update gate` exposes the acceptance checks and latched fault logic. The inventory contains 157 blocks including subsystem and mask internals.

Ordinary Unit Delay blocks hold theta, P, the histories, fuel offset and update count. Matrix Product blocks, transpose Math Function blocks, Sum and Gain blocks implement the RLS equations. Switch blocks accept the new theta/P only when enabled. No custom executable estimator code is hidden behind the subsystem masks. The `.m` setup file initializes parameters; the `.m` builder constructs the diagram. Neither executes the estimator during simulation.

The configuration is unchanged: actual fuel flow in lbm/s to direct shaft acceleration Ndot in rpm/s, ARX(5,5,1), ten regressors, Ts=0.015 s, lambda=0.999, initial theta=0 and P=10000*I. Normalize acceleration by 1000 and subtract the preparation fuel equilibrium, 0.9810869146824126 lbm/s, from input fuel. The output remains in rpm/s.

```
phi(k) = [-y(k-1), ..., -y(k-5), u(k-1), ..., u(k-5)]'
yhat(k|k-1) = phi(k)' * theta(k-1)
Pprior = P / lambda
K = Pprior*phi / (1 + phi'*Pprior*phi)
thetaNext = theta + K*(y - phi'*theta)
J = I - K*phi'
Pnext = J*Pprior*J' + K*K'
Pnext = (Pnext + Pnext')/2
```

The Unit Delays ensure predictions use the coefficients from the preceding update. Joseph-form covariance arithmetic preserves the same algorithm as the previous implementation. The matrices are visible signal values, not a call to the earlier `tmats_rls_step` helper. That helper is used only for independent offline verification.

## Experiment and results

After 30 s of preparation, the command is `9500-500*cos(2*pi*(0.1*t+0.0075*t^2))` rpm for 60 s. It oscillates between 9000 and 10000 rpm, sweeping 0.1–1 Hz. Actual fuel flow produced by the existing PI controller is the RLS input.

The unchanged reference plant first becomes invalid at **17.805 s of chirp time**. The gate freezes the observer and makes its prediction NaN from that point. There are 1187 valid samples through 17.790 s and 1185 coefficient updates. Consequently, the chirp metrics establish performance only over approximately 0.1–0.36685 Hz, not the full requested frequency range.

Fit is `100*(1-norm(y-yhat)/norm(y-mean(y)))`, not R-squared.

| Evaluation | Fit | RMSE (rpm/s) |
|---|---:|---:|
| Online, pre-update one-step chirp prediction | 99.8729% | 0.7050 |
| Persistence baseline, previous measured acceleration | 97.1964% | 15.5513 |
| Last five valid seconds, online prediction | 99.8779% | 0.8860 |
| Own-output simulation with evolving learned coefficients | 91.2627% | 48.4640 |
| Final frozen model, chirp free-run | 88.3707% | 64.5050 |
| Final frozen model, independent 60 s ramp/hold free-run | 62.6192% | 30.5107 |

The frozen ramp simulation uses no ramp output samples for adaptation or output feedback. Its demand includes ramps of +150, -100, +50, -150 and +95 rpm/s and holds within 9000–10000 rpm. All ramp flow residuals pass the 1e-9 criterion; their maximum is 9.9971e-10. The profile is included as `validation_profile.csv`.

The evolving-coefficient own-output simulation still uses parameters learned online from reference acceleration, so it is not an independent validation result. Frozen free-run filters start with zero normalized state following equilibrium preparation. Lower RMSE on the ramp despite lower percentage fit reflects its smaller acceleration variation.

## Agreement with the previous implementation

Every sample was compared against the previous S-function simulation, including invalid-output locations and the entire frozen remainder.

| Logged quantity | Maximum absolute difference |
|---|---:|
| Acceleration prediction | 3.2557e-8 rpm/s |
| Coefficients | 3.8216e-9 |
| Covariance diagonal | 2.5763e-5 |
| Regressor | 2.2204e-16 |
| Update/fault/count status | 0 |
| Fuel offset | 0 |

These small differences are consistent with floating-point operation ordering in matrix arithmetic; covariance entries are on the order of thousands to tens of thousands. The independent numerical checks also passed: offline replay coefficient error 3.13e-9, weighted-batch relative coefficient error 4.42e-8, and MATLAB System Identification Toolbox `recursiveLS` relative coefficient error 9.81e-10. Final covariance is positive definite, with minimum eigenvalue 1.1637e-4.

Reference speed differs from the original valid chirp by at most 4.18e-11 rpm and fuel by 7.16e-13 lbm/s. The original GPT and previous RLS model files were preserved. `observer_block_inventory.csv` and `basic_blocks_audit.json` record the implementation audit.

## Evolution, successes and improvements

The one-step estimate tracks the reference closely, reducing RMSE about 22-fold relative to persistence. First-three-second RMSE is 0.9218 rpm/s; final-five-second RMSE is 0.8860 rpm/s. `rls_evolution.png` shows the output/error, ten coefficient trajectories, covariance diagonals, rolling error and pole magnitudes. `rls_free_run_and_gate.png` distinguishes one-step performance from independent fuel-only simulation.

All sampled parameter sets have pole magnitudes below one, with a final maximum of 0.978884. No adaptive free-run divergence occurs in the valid segment. This is useful evidence for this run, not a general guarantee of time-varying stability.

The block implementation makes the states, update order, gating and numerical calculations inspectable without reading S-function code. It reproduces the earlier estimator rather than changing identification performance. Runtime or deployment speed was not benchmarked, and the complete T-MATS model's code-generation suitability was not tested.

The principal identification limitations are unchanged:

1. **Insufficient valid excitation:** the reference failure prevents learning from the complete frequency sweep. Obtain a longer converged excitation record before drawing conclusions across 0.1–1 Hz.
2. **Weak coefficient determination:** regressor condition number is 1.0167e6, with effective rank 9 at relative threshold 1e-6. Some coefficients keep moving and covariance trace increases from 100000 to 107324.6. A high prediction fit does not establish convergence of all ten parameters. Compare lower orders, less correlated sampling, or regularization on a separate selection set.
3. **Moderate free-run generalization:** the 62.6192% ramp fit and nonzero estimated acceleration on some holds expose low-frequency/equilibrium mismatch. Consider a physically constrained speed-state model, a zero-DC acceleration model around equilibrium, or speed-scheduled local models.
4. **Memory tuning:** the repeated sensitivity calculation gives one-step fits of 99.8616%, 99.8729% and 99.8934% at lambda=1, 0.999 and 0.995. The smallest lambda inflates covariance trace to about 4.75e6. Its slight prediction gain does not justify selecting it without further validation.
5. **Measured-data robustness:** this experiment uses ideal direct Ndot. Real speed differentiation needs causal filtering/observation and delay treatment; closed-loop measurement noise may require methods beyond ordinary ARX least squares.

## Run and deliverables

From the existing TMATSGPT folder:

```matlab
tmats_rls_setup;
open_system('GasTurbine_Dyn_Template_GPT_RLS_Blocks');
sim('GasTurbine_Dyn_Template_GPT_RLS_Blocks');
```

To inspect just the arithmetic:

```matlab
open_system('GasTurbine_Dyn_Template_GPT_RLS_Blocks/RLS Acceleration Observer/RLS matrix arithmetic');
```

The Simulink Run button also works after setup. The model's load callback installs the default scenario, so set custom MWS inputs after loading. The completed model does not depend on `tmats_rls_arx_sfun.m` to simulate.

`TMATS_RLS_BLOCKS_USAGE.md` explains the workflow. Command-line batch scripts rebuild, simulate and analyze; they exit MATLAB when finished. They use the existing earlier-result files for comparisons. The archive is intended for the current adjacent T-MATS installation, not as a standalone engine distribution.

The bundle includes the actual MDL model, setup/builder/analysis source, both raw MAT simulations, coefficients, full evolution and validation data, numerical metrics, block inventory, block diagrams and result plots.
