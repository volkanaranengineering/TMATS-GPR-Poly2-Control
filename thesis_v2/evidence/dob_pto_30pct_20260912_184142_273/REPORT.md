# Steady 10000 rpm regulation with sudden shaft power extraction

The original PI is compared against the existing frozen-model PI+DOB, without retuning. The speed demand stays at 10000 rpm throughout. Fuel-injection disturbances are disabled.

## Physical definition and scenario

A 60 s unloaded preparation is followed by 90 s evaluation. The reference is mean gross turbine shaft power over preparation seconds 55-60: **27896.507327 hp** (20802.421931 kW). Mean compressor load is 27896.507327 hp; unloaded net shaft power is 0.000000000 hp. Thus 30% is taken from gross turbine power, which balances compressor load at steady speed, not from near-zero net power.

Each extraction pulse is fixed at **8368.952198 hp = 6240.726579 kW** for both controllers. It is not recomputed as a percentage of the changing turbine output under load. Sudden on/off edges occur at 10.005/15.000, 30.000/40.005, and 60.000/75.000 s after preparation. These represent three applications of the same 30% additional load, with 4.995, 10.005 and 15.000 s holds.

The installed Shaft block power port receives positive extraction in hp. Its equation is

    dN/dt = 60/(2*pi*J) * (T_turbine + T_compressor - 5252.11*P_PTO/N),

with the original J=30. The turbine and compressor torque conversions use 5252.113 in the component code. The observer sees sensed speed and known fuel command only; the load profile and plant acceleration are not observer inputs.

## Comparison

PI gains remain Kp=0.025, Ki=0.05. DOB gain=0.25, Q pole-frequency parameter=0.5 Hz, compensation bound=0.15 lbm/s. Trim is latched at 30 s and compensation ramps in over two seconds, well before the evaluation.

| Measure | PI | PI + DOB |
|---|---:|---:|
| RMSE (rpm) | 1013.207 | 1012.912 |
| IAE (rpm s) | 59446.57 | 59413.71 |
| Maximum speed droop (rpm) | 1962.359 | 1958.126 |
| Maximum overspeed (rpm) | 3817.354 | 3817.02 |
| Fuel min (lbm/s) | 0.2 | 0.2 |
| Fuel max (lbm/s) | 4 | 4 |
| Fuel mass in 90 s (lbm) | 297.6923 | 297.7046 |
| Fuel-limit fraction | 0.6190635 | 0.6188969 |
| DOB correction-limit fraction | 0 | 0.5812365 |
| Maximum flow residual | 1.37208 | 1.371998 |
| Maximum iterations | 200 | 200 |
| Minimum compressor margin (%) | 7.839323e-07 | 1.050164e-06 |

Both full trajectories pass numerical/physical checks: PI=0, PI+DOB=0. FAILED trajectories are diagnostic only. Their aggregate errors above must not be used as valid control-performance evidence. First failure after preparation: PI 10.770000 s, PI+DOB 10.770000 s.

## Recovery after each edge

Recovery means the error remains within +/-1 rpm until the next load edge, with at least 0.5 s of confirmed dwell. NaN means recovery was not established before that edge; 0 means the response never left the band.

| Edge time (s) | Event | PI peak abs. error (rpm) | DOB peak abs. error (rpm) | PI recovery (s) | DOB recovery (s) |
|---:|---|---:|---:|---:|---:|
| 10.005 | Apply load | 937.65620 | 937.68994 | NaN | NaN |
| 15.000 | Remove load | 1997.93505 | 1996.56568 | 7.320 | 6.900 |
| 30.000 | Apply load | 947.51358 | 947.54701 | NaN | NaN |
| 40.005 | Remove load | 3043.39841 | 3042.86043 | 11.130 | 10.815 |
| 60.000 | Apply load | 947.58797 | 947.62139 | NaN | NaN |
| 75.000 | Remove load | 3817.35357 | 3817.01973 | NaN | NaN |

## Verification and reproduction

The power and speed profiles match exactly between controllers. The independent shaft torque-balance reconstruction matches logged acceleration to 1.364e-12 rpm/s for PI and 1.414e-12 rpm/s for PI+DOB. Acceptance requires finite signals, positive fuel and compressor margin, residual <=1e-9, and fewer than 200 iterations throughout preparation and evaluation.

Run `out=run_tmats_pto_study(0.30); analyze_tmats_pto(out);` from TMATSGPT using the existing `_DOB_PTO.mdl` copy to measure steady turbine power and simulate both controllers. Run `analyze_tmats_pto` to regenerate this report and the figures. Open the model after `tmats_pto_setup`; its default uses the measured reference saved in `tmp/dob/pto_reference.json`.

Saved evidence: `trim.mat/csv`, `reference.json`, `case_01.mat/csv`, `case_02.mat/csv`, `metrics.json/csv`, `events.csv`, `pto_comparison.png`, and `pto_transient_detail.png`. Existing GPT and DOB model files are preserved.

This is one deterministic, noise-free sample-engine operating point. The estimate is fuel-equivalent lumped model error, not a direct calibrated power measurement. The experiment tests mechanical load rejection but does not qualify the observer for hardware or establish broad closed-loop robustness.
