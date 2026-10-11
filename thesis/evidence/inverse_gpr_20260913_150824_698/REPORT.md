# Inverse exact GPR: speed and acceleration to fuel flow

Inputs: N [rpm], dN/dt [rpm/s]. Output: Wf [lbm/s], response standard deviation, 95% response interval, and latent function standard deviation. This is a separately trained inverse regression, not an algebraic inverse of the forward GP.

Exact ARD squared-exponential GP with maximum-likelihood hyperparameters, zero mean on standardized responses, exact fitting and exact prediction. Uses the same 600 training observations and 100 held-out validation observations as the forward study. Training samples retain the original speed/fuel space-filling selection for direct comparison. Training records: valid chirp plus selection ramp; test record: separate validation ramp. No test-based tuning or interval rescaling.

Test target speeds span 9000-10000 rpm. Actual recorded speeds: 9000.000000 to 9998.885249 rpm; maximum target mismatch 1.685586 rpm. Test acceleration range: -151.003100 to 222.589628 rpm/s.

Fuel RMSE: 0.001048216 lbm/s (0.000475463 kg/s). MAE: 0.000832021 lbm/s. R2: 0.999997241. Nominal 95% interval coverage: 97.0% (97/100).

Exported Cholesky posterior vs MATLAB maximum mean/SD errors: 1e-11 / 4.59e-13 lbm/s. Scalar and vector API checks passed.

Training input ranges: N 9000.000000 to 9999.897804 rpm; acceleration -1153.470131 to 1076.907740 rpm/s. Training fuel range 0.183863 to 4.194426 lbm/s. The rectangular ranges do not imply every input combination is supported.

Uncertainty uses k(x,x)-||L\k(X,x)||^2 for latent variance and adds fitted noise variance for response variance. All outputs are rescaled to lbm/s. Hyperparameter and input-measurement uncertainty are not integrated. Test acceleration is the plant acceleration, not a noisy numerical derivative or a forward-GP prediction.

Application: Wf_hat = g(N, desired_acceleration) is a candidate feedforward estimate under the original fixed ambient and zero external shaft-load conditions. Closed-loop control and varying load are not validated here. Predictions are not clipped to actuator limits. The test samples are from one trajectory; exact GP inference does not guarantee an exact or globally unique physical inverse.

Method follows Volkan Aran (2019), Flexible and Robust Control of Heavy Duty Diesel Engine Airpath Using Data Driven Disturbance Observers and GPR Models, section 5.1 equations 5.5-5.14 and inverse feedforward modeling section 6.2.1; thesis reference [92], Rasmussen and Williams, Gaussian Processes for Machine Learning, chapter 2. This adapts the methodology to T-MATS shaft dynamics.

Source forward study: `C:\Users\volka\OneDrive\Belgeler\MATLAB\T-MATS_v1_3_3\T-MATS-master\Trunk\TMATSGPT\results\exact_gpr_20260913_145742_458`.
