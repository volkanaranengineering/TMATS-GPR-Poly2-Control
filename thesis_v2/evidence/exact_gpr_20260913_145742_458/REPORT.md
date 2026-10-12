# Exact GPR turbine dynamics

Inputs: speed N [rpm], fuel Wf [lbm/s]. Output: dN/dt [rpm/s], predictive standard deviation [rpm/s], 95% response interval, and latent standard deviation.

Exact maximum-likelihood fit and exact prediction with ARD squared-exponential kernel. 600 training points; exactly 100 independent-experiment test points. Training uses valid chirp and selection-ramp records; validation uses a separate ramp. Training samples selected by input-only farthest-point coverage. No test outputs used for fitting or selection.

100 target speeds are linspace(9000,10000,100). Each selects the nearest unique valid recorded validation sample, without synthesizing labels. Actual speed range 9000.000000 to 9998.885249 rpm; maximum target mismatch 1.6856 rpm. Training speed 9000.0000 to 9999.8978 rpm; fuel 0,183863 to 4,194426 lbm/s.

RMSE 0.645908 rpm/s; MAE 0.510063 rpm/s; R2 0.99996430; nominal 95% response-interval coverage 90.0%.

Checks: power-law acceleration versus direct plant output max error 2.41e-10 rpm/s; exported Cholesky posterior versus MATLAB mean/SD errors 2.97e-09 / 2.73e-10 rpm/s.

Labels use signed compressor and turbine power and J=30: dN/dt = 60/(2*pi*30)*5252.113*(Pc+Pt)/N. No finite-difference derivative is used. These records assume zero external shaft load and fixed ambient conditions. A two-input model cannot identify arbitrary changes in load, ambient conditions or hidden dynamic states. Exact refers to GP inference, not an exact physical model.

Uncertainty: latent variance = k(x,x)-||L\k(X,x)||^2; response variance adds fitted noise variance. Hyperparameters are fixed at their likelihood estimate; intervals are model-conditional, not guaranteed physical error bounds or a calibrated safety bound. No test-based interval rescaling. Test points come from one trajectory and are not statistically independent replicates.

References: Volkan Aran (2019), Flexible and Robust Control of Heavy Duty Diesel Engine Airpath Using Data Driven Disturbance Observers and GPR Models, sec. 5.1, eqs. 5.5-5.14, and sec. 6.2.1. Uses per-input length scales of eq. 5.8. Thesis reference [92]: Rasmussen and Williams, Gaussian Processes for Machine Learning (2006), ch. 2, https://gaussianprocess.org/gpml/chapters/RW2.pdf . MATLAB: https://www.mathworks.com/help/stats/fitrgp.html and https://www.mathworks.com/help/stats/regressiongp.predict.html . This adapts the GP methodology to forward turbine acceleration; it does not reproduce the thesis diesel inverse controller.
