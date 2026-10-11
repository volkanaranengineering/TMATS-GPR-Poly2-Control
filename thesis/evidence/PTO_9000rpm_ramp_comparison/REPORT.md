# 9000 rpm: ramped shaft-load rejection study

Steady gross turbine shaft power: **11789.245211 hp** (8.791239 MW). Steady fuel: 0.981087 lbm/s. Percentages use this frozen reference, not near-zero net shaft power.

## Scenario and formulation

Each amplitude uses three separate ramp/hold/ramp pulses. Application starts at 10.005, 30 and 60 s; removal starts at 15, 40.005 and 75 s. Corresponding rise and fall durations are 0.30, 1.50 and 3.00 s. The 90 s evaluation follows 60 s preparation (10000 rpm initially, demand ramp to 9000 rpm during seconds 5–10). Sampling is 15 ms. Thus ramps contain 20, 100 and 200 sample intervals.

For amplitude α and measured turbine power P₀, each pulse is P_L(t)=αP₀[sat((t−t_on)/T_r)−sat((t−t_off)/T_r)], where sat(x)=min(1,max(0,x)). The three nonoverlapping pulses are summed and applied as actual shaft power extraction. The speed demand stays at 9000 rpm; injected fuel disturbance is zero.

PI gains remain Kp=0.025 and Ki=0.05. The frozen eight-term identified model, equilibrium correction, DOB gain 0.25, Q pole-frequency parameter 0.5 Hz, compensation bound ±0.15 lbm/s and fuel bounds 0.2–4 lbm/s are unchanged. No controller is retuned between amplitudes or ramp rates. The observer uses sensed speed and known fuel, without access to injected shaft load.

## Complete-run results

| Load | MW | Controller | Valid | RMSE rpm | Peak absolute error rpm | First failure s |
|---|---:|---|---|---:|---:|---:|
| 5% | 0.440 | PI | True | 0.594 | 5.325 | — |
| 5% | 0.440 | PI+DOB | True | 0.517 | 5.162 | — |
| 10% | 0.879 | PI | True | 1.193 | 10.677 | — |
| 10% | 0.879 | PI+DOB | True | 1.038 | 10.351 | — |
| 20% | 1.758 | PI | True | 2.540 | 22.553 | — |
| 20% | 1.758 | PI+DOB | True | 2.237 | 22.329 | — |
| 30% | 2.637 | PI | True | 3.973 | 35.359 | — |
| 30% | 2.637 | PI+DOB | True | 3.664 | 35.258 | — |

![Overview](overview.png)

## Time response at each ramp

Recovery is the first sample after the last excursion outside ±1 rpm, confirmed by at least 0.5 s within the band through the next ramp start. After-ramp recovery is max(0, recovery from start − ramp duration). A zero means recovery occurred by ramp completion. Metrics are withheld for an event if any earlier plant solve was invalid. A dash can also mean no confirmed settling.

| Load | Ramp s | Edge | Controller | Peak error rpm | Recovery from start s | After ramp s |
|---|---:|---|---|---:|---:|---:|
| 5% | 0.30 | application | PI | 5.325 | 1.035 | 0.735 |
| 5% | 0.30 | removal | PI | 5.215 | 1.050 | 0.750 |
| 5% | 1.50 | application | PI | 1.965 | 1.785 | 0.285 |
| 5% | 1.50 | removal | PI | 1.932 | 1.785 | 0.285 |
| 5% | 3.00 | application | PI | 1.020 | 3.045 | 0.045 |
| 5% | 3.00 | removal | PI | 1.020 | 2.985 | 0.000 |
| 5% | 0.30 | application | PI+DOB | 5.162 | 0.825 | 0.525 |
| 5% | 0.30 | removal | PI+DOB | 5.055 | 0.825 | 0.525 |
| 5% | 1.50 | application | PI+DOB | 1.565 | 1.665 | 0.165 |
| 5% | 1.50 | removal | PI+DOB | 1.567 | 1.650 | 0.150 |
| 5% | 3.00 | application | PI+DOB | 0.784 | 0.000 | 0.000 |
| 5% | 3.00 | removal | PI+DOB | 0.782 | 0.000 | 0.000 |
| 10% | 0.30 | application | PI | 10.677 | 1.350 | 1.050 |
| 10% | 0.30 | removal | PI | 10.457 | 1.380 | 1.080 |
| 10% | 1.50 | application | PI | 3.950 | 2.130 | 0.630 |
| 10% | 1.50 | removal | PI | 3.901 | 2.145 | 0.645 |
| 10% | 3.00 | application | PI | 2.054 | 3.315 | 0.315 |
| 10% | 3.00 | removal | PI | 2.042 | 3.315 | 0.315 |
| 10% | 0.30 | application | PI+DOB | 10.351 | 1.005 | 0.705 |
| 10% | 0.30 | removal | PI+DOB | 10.140 | 1.035 | 0.735 |
| 10% | 1.50 | application | PI+DOB | 3.145 | 1.845 | 0.345 |
| 10% | 1.50 | removal | PI+DOB | 3.134 | 1.860 | 0.360 |
| 10% | 3.00 | application | PI+DOB | 1.565 | 3.165 | 0.165 |
| 10% | 3.00 | removal | PI+DOB | 1.566 | 3.150 | 0.150 |
| 20% | 0.30 | application | PI | 22.553 | 1.695 | 1.395 |
| 20% | 0.30 | removal | PI | 22.380 | 1.740 | 1.440 |
| 20% | 1.50 | application | PI | 8.786 | 2.490 | 0.990 |
| 20% | 1.50 | removal | PI | 7.988 | 2.490 | 0.990 |
| 20% | 3.00 | application | PI | 4.649 | 3.705 | 0.705 |
| 20% | 3.00 | removal | PI | 4.363 | 3.660 | 0.660 |
| 20% | 0.30 | application | PI+DOB | 21.914 | 1.170 | 0.870 |
| 20% | 0.30 | removal | PI+DOB | 22.329 | 1.215 | 0.915 |
| 20% | 1.50 | application | PI+DOB | 7.096 | 2.055 | 0.555 |
| 20% | 1.50 | removal | PI+DOB | 6.823 | 2.040 | 0.540 |
| 20% | 3.00 | application | PI+DOB | 3.536 | 3.360 | 0.360 |
| 20% | 3.00 | removal | PI+DOB | 3.771 | 3.345 | 0.345 |
| 30% | 0.30 | application | PI | 35.359 | 1.875 | 1.575 |
| 30% | 0.30 | removal | PI | 35.257 | 1.950 | 1.650 |
| 30% | 1.50 | application | PI | 13.677 | 2.685 | 1.185 |
| 30% | 1.50 | removal | PI | 12.372 | 2.700 | 1.200 |
| 30% | 3.00 | application | PI | 7.239 | 3.900 | 0.900 |
| 30% | 3.00 | removal | PI | 6.909 | 3.870 | 0.870 |
| 30% | 0.30 | application | PI+DOB | 34.333 | 1.680 | 1.380 |
| 30% | 0.30 | removal | PI+DOB | 35.258 | 1.410 | 1.110 |
| 30% | 1.50 | application | PI+DOB | 11.032 | 2.580 | 1.080 |
| 30% | 1.50 | removal | PI+DOB | 12.372 | 2.190 | 0.690 |
| 30% | 3.00 | application | PI+DOB | 6.730 | 3.870 | 0.870 |
| 30% | 3.00 | removal | PI+DOB | 6.901 | 3.480 | 0.480 |

## Ramp rates

| Load | 0.30 s ramp (MW/s) | 1.50 s ramp (MW/s) | 3.00 s ramp (MW/s) |
|---|---:|---:|---:|
| 5% | 1.465 | 0.293 | 0.147 |
| 10% | 2.930 | 0.586 | 0.293 |
| 20% | 5.861 | 1.172 | 0.586 |
| 30% | 8.791 | 1.758 | 0.879 |

These magnitudes apply to both rising and falling ramps. The source is sampled and held at 15 ms.

## Interpretation

- **5%:** observer RMSE changes by -13.03% relative to PI. Peak absolute error changes from 5.325 to 5.162 rpm. Minimum compressor margin is 29.404% / 29.347% (PI / DOB). DOB compensation clips for 0.00% of evaluation samples.
- **10%:** observer RMSE changes by -13.02% relative to PI. Peak absolute error changes from 10.677 to 10.351 rpm. Minimum compressor margin is 24.429% / 24.322% (PI / DOB). DOB compensation clips for 0.00% of evaluation samples.
- **20%:** observer RMSE changes by -11.92% relative to PI. Peak absolute error changes from 22.553 to 22.329 rpm. Minimum compressor margin is 14.445% / 14.238% (PI / DOB). DOB compensation clips for 26.98% of evaluation samples.
- **30%:** observer RMSE changes by -7.77% relative to PI. Peak absolute error changes from 35.359 to 35.258 rpm. Minimum compressor margin is 5.526% / 5.231% (PI / DOB). DOB compensation clips for 31.98% of evaluation samples.

At 30% load, increasing the application ramp from 0.30 to 3.00 s reduces PI peak error from 35.359 to 7.239 rpm and DOB peak error from 34.333 to 6.730 rpm. However, on the 3.00 s application ramp the observer improves recovery after completion by only 0.030 s (0.900 to 0.870 s). On the 0.30 s removal ramp, the peak is effectively unchanged (35.257 versus 35.258 rpm), while after-ramp recovery improves from 1.650 to 1.110 s. This supports a recovery benefit, not uniform peak suppression. At 5% with a 3.00 s ramp, DOB error stays within ±1 rpm throughout both events.

All eight trajectories pass the numerical checks, with no fuel saturation. At 30%, DOB peak fuel is 2.191 lbm/s and minimum reported compressor margin is 5.231%. The lower margin and frequent compensation clipping motivate constraint-aware tuning before extending the load envelope. Compared with the earlier 9500 rpm step tests, both the operating point, absolute load and disturbance shape have changed: 30% is now 2.637 MW rather than 4.286 MW. The valid result cannot be attributed solely to observer performance or solely to ramp shaping.

The DOB is bounded equivalent-input compensation around the existing PI loop. It estimates the combined effect of external load and nominal-model mismatch; its estimate is not a calibrated shaft-power measurement. Slower ramps generally give the controller more time to compensate, but the event table is the evidence for this plant: peak rejection, settling and global RMSE need not improve together. The three ramp rates share a trajectory with different preceding histories and hold lengths, so these are representative scenarios rather than independent rate-identification experiments.

The fixed model was identified from fuel-to-acceleration data and corrected for zero equilibrium acceleration before observer synthesis. Its inverse and low-pass filtering introduce a bandwidth tradeoff: stronger/faster compensation can improve rejection while amplifying sensor noise and model error. Compensation clipping limits authority. PI integral action provides steady regulation; no anti-windup was added for these comparisons.

Next steps are independent runs for each rate with identical settling windows, gain scheduling across operating points, sensor-noise and delay tests, anti-windup and explicit fuel/temperature/compressor-margin constraints, then fixed-step embedded timing and hardware-in-the-loop assessment. If flow convergence fails, first establish a numerically valid operating envelope; an invalid trajectory is not proof of physical instability or surge.

## Verification and reproduction

The two controllers receive identical sampled power profiles, verified against the ramp formula. Each run has 10001 samples through 150 s. The mechanical torque balance is reconstructed from logged turbine, compressor and external powers and checked against shaft acceleration. Validity requires finite signals, positive fuel and compressor margin, flow residual ≤1e-9 and fewer than 200 solver iterations. All plots show only the prefix before the first invalid solve. Full raw trajectories are retained for diagnosis.

Run `run_tmats_pto_9000_ramp_batch` in MATLAB, then `summarize_pto_9000_ramps.py` in Python for the report. A single level is `out=run_tmats_pto_study(0.10,9000,[0.30 1.50 3.00]);`. Omitting the third argument preserves the earlier step-load study. The existing PTO Simulink model is unchanged.

## 5% response zooms

![5% zoom](zoom_05pct.png)

## 10% response zooms

![10% zoom](zoom_10pct.png)

## 20% response zooms

![20% zoom](zoom_20pct.png)

## 30% response zooms

![30% zoom](zoom_30pct.png)

