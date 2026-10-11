# Steady 10000 rpm regulation with sudden shaft power extraction

The original PI is compared against the existing frozen-model PI+DOB, without retuning. The speed demand stays at 10000 rpm throughout. Fuel-injection disturbances are disabled.

## Physical definition and scenario

A 60 s unloaded preparation is followed by 90 s evaluation. The reference is mean gross turbine shaft power over preparation seconds 55-60: **27896.507327 hp** (20802.421931 kW). Mean compressor load is 27896.507327 hp; unloaded net shaft power is 0.000000000 hp. Thus 10% is taken from gross turbine power, which balances compressor load at steady speed, not from near-zero net power.

Each extraction pulse is fixed at **2789.650733 hp = 2080.242193 kW** for both controllers. It is not recomputed as a percentage of the changing turbine output under load. Sudden on/off edges occur at 10.005/15.000, 30.000/40.005, and 60.000/75.000 s after preparation. These represent three applications of the same 10% additional load, with 4.995, 10.005 and 15.000 s holds.

The installed Shaft block power port receives positive extraction in hp. Its equation is

    dN/dt = 60/(2*pi*J) * (T_turbine + T_compressor - 5252.11*P_PTO/N),

with the original J=30. The turbine and compressor torque conversions use 5252.113 in the component code. The observer sees sensed speed and known fuel command only; the load profile and plant acceleration are not observer inputs.

## Comparison

PI gains remain Kp=0.025, Ki=0.05. DOB gain=0.25, Q pole-frequency parameter=0.5 Hz, compensation bound=0.15 lbm/s. Trim is latched at 30 s and compensation ramps in over two seconds, well before the evaluation.

| Measure | PI | PI + DOB |
|---|---:|---:|
| RMSE (rpm) | 4.821036 | 4.627883 |
| IAE (rpm s) | 103.1914 | 86.3594 |
| Maximum speed droop (rpm) | 38.23095 | 37.97716 |
| Maximum overspeed (rpm) | 40.12642 | 40.12642 |
| Fuel min (lbm/s) | 2.746102 | 2.746102 |
| Fuel max (lbm/s) | 4 | 4 |
| Fuel mass in 90 s (lbm) | 295.7642 | 295.7748 |
| Fuel-limit fraction | 0.005499083 | 0.006498917 |
| DOB correction-limit fraction | 0 | 0.3187802 |
| Maximum flow residual | 9.983553e-10 | 9.998794e-10 |
| Maximum iterations | 14 | 14 |
| Minimum compressor margin (%) | 7.635762 | 7.642796 |

Both full trajectories pass numerical/physical checks: PI=1, PI+DOB=1. Tracking RMSE change is 4.006% improvement; maximum droop change is 0.664% improvement.

The main benefit is faster recovery rather than suppression of the initial mechanical shock. The load-removal overspeed is essentially unchanged. The fuel command reaches its 4 lbm/s ceiling for 0.550% of PI evaluation samples and 0.650% of DOB samples. DOB correction reaches its bound for 31.878% of samples; the inherited PI has no added anti-windup. These limits should be considered before increasing observer gain or extraction power.

## Recovery after each edge

Recovery means the error remains within +/-1 rpm until the next load edge, with at least 0.5 s of confirmed dwell. NaN means recovery was not established before that edge; 0 means the response never left the band.

| Edge time (s) | Event | PI peak abs. error (rpm) | DOB peak abs. error (rpm) | PI recovery (s) | DOB recovery (s) |
|---:|---|---:|---:|---:|---:|
| 10.005 | Apply load | 38.23095 | 37.97716 | 1.695 | 1.365 |
| 15.000 | Remove load | 40.12567 | 40.12605 | 1.680 | 1.140 |
| 30.000 | Apply load | 38.23095 | 37.97716 | 1.695 | 1.365 |
| 40.005 | Remove load | 40.12642 | 40.12642 | 1.680 | 1.140 |
| 60.000 | Apply load | 38.23095 | 37.97716 | 1.695 | 1.365 |
| 75.000 | Remove load | 40.12642 | 40.12642 | 1.680 | 1.140 |

## Verification and reproduction

The power and speed profiles match exactly between controllers. The independent shaft torque-balance reconstruction matches logged acceleration to 1.556e-12 rpm/s for PI and 1.566e-12 rpm/s for PI+DOB. Acceptance requires finite signals, positive fuel and compressor margin, residual <=1e-9, and fewer than 200 iterations throughout preparation and evaluation.

Run `run_tmats_pto_batch` from TMATSGPT to build the new `_DOB_PTO.mdl` copy, measure steady turbine power, and simulate both controllers. Run `analyze_tmats_pto` to regenerate this report and the figures. Open the model after `tmats_pto_setup`; its default uses the measured reference saved in `tmp/dob/pto_reference.json`.

Saved evidence: `trim.mat/csv`, `reference.json`, `case_01.mat/csv`, `case_02.mat/csv`, `metrics.json/csv`, `events.csv`, `pto_comparison.png`, and `pto_transient_detail.png`. Existing GPT and DOB model files are preserved.

This is one deterministic, noise-free sample-engine operating point. The estimate is fuel-equivalent lumped model error, not a direct calibrated power measurement. The experiment tests mechanical load rejection but does not qualify the observer for hardware or establish broad closed-loop robustness.
