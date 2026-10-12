# Literature observer comparison: 9000 rpm, 10% load

Load is **0.879124 MW** (10% of 11789.245211 hp gross turbine power). The previous 0.30, 1.50 and 3.00 s ramp/hold/ramp scenario is repeated with five controllers. PI gains, 0.25 compensation gain, ±0.15 lbm/s correction bound, fuel limits and preparation are unchanged. The observer pole-frequency parameter is 0.5 Hz for every method; actual estimator bandwidths differ. No test-based tuning is performed.

The three candidates are LESO (two states), UDE (one state), and ramp GPIO (three states). See the accompanying formulation for equations, primary literature, implementation details and comparison limitations.

## Measured comparison

| Method | Valid | RMSE rpm | Reduction vs PI | Peak error rpm | IAE rpm·s | Peak fuel lbm/s |
|---|---|---:|---:|---:|---:|---:|
| PI | True | 1.193 | 0.000% | 10.677 | 36.774 | 1.333 |
| DOB | True | 1.038 | 13.021% | 10.351 | 28.341 | 1.338 |
| LESO | True | 1.039 | 12.903% | 10.349 | 28.694 | 1.338 |
| UDE | True | 0.969 | 18.746% | 9.377 | 27.587 | 1.336 |
| GPIO | True | 0.951 | 20.301% | 9.866 | 27.577 | 1.344 |

![Overview](overview.png)

## Event recovery

Recovery requires remaining within ±1 rpm to the next ramp, with at least 0.5 s confirmed dwell. After-ramp recovery subtracts the ramp duration, bounded below by zero. Failed propagated trajectories receive no performance claim.

| Ramp s | Edge | Method | Peak rpm | Recovery from start s | After ramp s |
|---:|---|---|---:|---:|---:|
| 0.30 | apply | PI | 10.677 | 1.350 | 1.050 |
| 0.30 | apply | DOB | 10.351 | 1.005 | 0.705 |
| 0.30 | apply | LESO | 10.349 | 1.020 | 0.720 |
| 0.30 | apply | UDE | 9.377 | 1.080 | 0.780 |
| 0.30 | apply | GPIO | 9.866 | 0.915 | 0.615 |
| 0.30 | remove | PI | 10.457 | 1.380 | 1.080 |
| 0.30 | remove | DOB | 10.140 | 1.035 | 0.735 |
| 0.30 | remove | LESO | 10.137 | 1.050 | 0.750 |
| 0.30 | remove | UDE | 9.205 | 1.095 | 0.795 |
| 0.30 | remove | GPIO | 9.670 | 0.930 | 0.630 |
| 1.50 | apply | PI | 3.950 | 2.130 | 0.630 |
| 1.50 | apply | DOB | 3.145 | 1.845 | 0.345 |
| 1.50 | apply | LESO | 3.171 | 1.845 | 0.345 |
| 1.50 | apply | UDE | 3.050 | 1.920 | 0.420 |
| 1.50 | apply | GPIO | 2.850 | 1.785 | 0.285 |
| 1.50 | remove | PI | 3.901 | 2.145 | 0.645 |
| 1.50 | remove | DOB | 3.134 | 1.860 | 0.360 |
| 1.50 | remove | LESO | 3.158 | 1.875 | 0.375 |
| 1.50 | remove | UDE | 3.022 | 1.920 | 0.420 |
| 1.50 | remove | GPIO | 2.817 | 1.800 | 0.300 |
| 3.00 | apply | PI | 2.054 | 3.315 | 0.315 |
| 3.00 | apply | DOB | 1.565 | 3.165 | 0.165 |
| 3.00 | apply | LESO | 1.577 | 3.165 | 0.165 |
| 3.00 | apply | UDE | 1.545 | 3.165 | 0.165 |
| 3.00 | apply | GPIO | 1.528 | 3.150 | 0.150 |
| 3.00 | remove | PI | 2.042 | 3.315 | 0.315 |
| 3.00 | remove | DOB | 1.566 | 3.150 | 0.150 |
| 3.00 | remove | LESO | 1.578 | 3.150 | 0.150 |
| 3.00 | remove | UDE | 1.536 | 3.150 | 0.150 |
| 3.00 | remove | GPIO | 1.513 | 3.150 | 0.150 |

![Zooms](rejection_zooms.png)

## Actuation and model validity

| Method | Fuel limit % | Compensation clip % | Fuel total variation lbm/s | Minimum compressor margin % |
|---|---:|---:|---:|---:|
| PI | 0.000 | 0.000 | 2.116 | 24.429 |
| DOB | 0.000 | 0.000 | 2.136 | 24.322 |
| LESO | 0.000 | 0.000 | 2.143 | 24.302 |
| UDE | 0.000 | 0.000 | 2.144 | 24.389 |
| GPIO | 0.000 | 0.000 | 2.174 | 24.161 |

## Assessment

**GPIO has the lowest RMSE in this fixed-setting test: 0.9509 rpm.** This is a measured result for the chosen nominal gain, observer poles and limits, not a universal ranking or optimally tuned benchmark. The existing DOB uses the fuller identified model; new observers use only its first fuel-to-acceleration coefficient as an approximate input gain.

**Practical recommendation:** start with UDE if implementation simplicity and peak rejection are the priorities; retain GPIO as the performance candidate when faster recovery justifies two extra observer states. LESO is a simpler-model substitute for the existing DOB here, but does not improve its overall RMSE. This recommendation is conditional on passing subsequent noise and robustness tests.

For the 0.30 s application ramp, post-ramp recovery is 1.050 s (PI), 0.705 s (DOB), 0.720 s (LESO), 0.780 s (UDE), and 0.615 s (GPIO). Thus UDE has the lowest peak, but is slower to enter the ±1 rpm band than DOB and GPIO. For the 1.50 s ramp, GPIO application peak is 2.850 rpm versus 3.950 rpm for PI, with post-ramp recovery 0.285 versus 0.630 s. At 3.00 s, after-ramp recovery differs by only one sample or less among the augmented methods.

Relative to the existing DOB, UDE lowers RMSE by about 6.58% and GPIO by 8.37%. Neither fuel nor compensation saturation occurs. GPIO has the greatest fuel total variation (2.174 versus 2.116 lbm/s for PI) and the highest peak fuel (1.344 versus 1.333 lbm/s), illustrating a small actuation tradeoff. These total-variation values sum absolute sample-to-sample command changes; they are not fuel consumption.

UDE has the smallest state count and no raw derivative, but its direct speed term makes measurement-noise testing important. LESO is a simple general-purpose candidate. GPIO represents disturbance slope explicitly, at the cost of an additional state and stronger high-frequency correction. A shaft-power ramp is not necessarily a ramp in equivalent-fuel disturbance because the plant and sensor contribute to the residual.

Next compare separately tuned settings using an independent tuning case, then hold out load profiles for validation. Include sensor noise, delay variation, gain mismatch, fuel constraints and compressor margin. Do not choose a deployed method using speed RMSE alone: peak excursions, recovery, actuator variation and numerical/physical limits matter.

## Verification and reproduction

All five actual Simulink trajectories contain 10001 samples through 150 s. Checks confirm identical shaft profiles, 9000 rpm evaluation demand, zero fuel disturbance and mechanical torque balance. The three new estimators are independently replayed from logged sensed speed and applied fuel with their exact discrete state equations. PI and existing DOB responses reproduce the preceding 10% study. Detailed numerical errors are in verification.json.

Run `out=run_tmats_literature_comparison;` in MATLAB, then `summarize_literature_observers.py` in Python. The new model is `GasTurbine_Dyn_Template_GPT_DOB_PTO_ALT.mdl`; original models are preserved. Load the model first, then select an alternative with `tmats_literature_setup(2)` (LESO), `(3)` (UDE) or `(4)` (GPIO) before simulation; its PreLoadFcn initializes LESO by default. Observer pole stability does not establish nonlinear closed-loop robustness. No noisy or hardware experiment is claimed.

