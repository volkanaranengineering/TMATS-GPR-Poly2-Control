# Steady 9500 rpm regulation with sudden shaft power extraction

The original PI is compared against the existing frozen-model PI+DOB, without retuning. The speed demand stays at 9500 rpm during evaluation. Fuel-injection disturbances are disabled.

## Physical definition and scenario

A 60 s unloaded preparation is followed by 90 s evaluation. Preparation starts from the standard 10000 rpm initial state, holds to 5 s, ramps to 9500 rpm by 10 s, and then holds. The reference is mean gross turbine shaft power over preparation seconds 55-60: **19160.793887 hp** (14288.201541 kW). Mean compressor load is 19160.793887 hp; unloaded net shaft power is 0.000000000 hp. Thus 20% is taken from gross turbine power, which balances compressor load at steady speed, not from near-zero net power.

Each extraction pulse is fixed at **3832.158777 hp = 2857.640308 kW** for both controllers. It is not recomputed as a percentage of the changing turbine output under load. Sudden on/off edges occur at 10.005/15.000, 30.000/40.005, and 60.000/75.000 s after preparation. These represent three applications of the same 20% additional load, with 4.995, 10.005 and 15.000 s holds.

The installed Shaft block power port receives positive extraction in hp. Its equation is

    dN/dt = 60/(2*pi*J) * (T_turbine + T_compressor - 5252.11*P_PTO/N),

with the original J=30. The turbine and compressor torque conversions use 5252.113 in the component code. The observer sees sensed speed and known fuel command only; the load profile and plant acceleration are not observer inputs.

## Comparison

PI gains remain Kp=0.025, Ki=0.05. DOB gain=0.25, Q pole-frequency parameter=0.5 Hz, compensation bound=0.15 lbm/s. Trim is latched at 30 s and compensation ramps in over two seconds, well before the evaluation.

| Measure | PI | PI + DOB |
|---|---:|---:|
| RMSE (rpm) | 6.429517 | 6.202717 |
| IAE (rpm s) | 137.6882 | 120.5082 |
| Maximum speed droop (rpm) | 53.39709 | 53.01274 |
| Maximum overspeed (rpm) | 54.09983 | 54.09983 |
| Fuel min (lbm/s) | 1.539098 | 1.539098 |
| Fuel max (lbm/s) | 3.333468 | 3.360189 |
| Fuel mass in 90 s (lbm) | 200.9487 | 200.9488 |
| Fuel-limit fraction | 0 | 0 |
| DOB correction-limit fraction | 0 | 0.332278 |
| Maximum flow residual | 9.985193e-10 | 9.986633e-10 |
| Maximum iterations | 20 | 20 |
| Minimum compressor margin (%) | 4.863939 | 4.594614 |

Both full trajectories pass numerical/physical checks: PI=1, PI+DOB=1. Tracking RMSE change is 3.527% improvement; maximum droop change is 0.720% improvement.

Performance must be assessed together with saturation and the recovery table. The fuel command reaches its limits for 0.000% of PI evaluation samples and 0.000% of DOB samples. DOB correction reaches its bound for 33.228% of samples; the inherited PI has no added anti-windup. These limits should be considered before increasing observer gain or extraction power.

## Recovery after each edge

Recovery means the error remains within +/-1 rpm until the next load edge, with at least 0.5 s of confirmed dwell. NaN means recovery was not established before that edge; 0 means the response never left the band.

| Edge time (s) | Event | PI peak abs. error (rpm) | DOB peak abs. error (rpm) | PI recovery (s) | DOB recovery (s) |
|---:|---|---:|---:|---:|---:|
| 10.005 | Apply load | 53.39709 | 53.01274 | 1.815 | 1.665 |
| 15.000 | Remove load | 54.09907 | 54.09928 | 1.875 | 1.320 |
| 30.000 | Apply load | 53.39709 | 53.01274 | 1.815 | 1.665 |
| 40.005 | Remove load | 54.09983 | 54.09983 | 1.875 | 1.320 |
| 60.000 | Apply load | 53.39709 | 53.01274 | 1.815 | 1.665 |
| 75.000 | Remove load | 54.09983 | 54.09983 | 1.875 | 1.320 |

## Verification and reproduction

The power and speed profiles match exactly between controllers. The independent shaft torque-balance reconstruction matches logged acceleration to 1.286e-12 rpm/s for PI and 1.286e-12 rpm/s for PI+DOB. Acceptance requires finite signals, positive fuel and compressor margin, residual <=1e-9, and fewer than 200 iterations throughout preparation and evaluation.

Run `out=run_tmats_pto_study(0.20,9500); analyze_tmats_pto(out);` from TMATSGPT using the existing `_DOB_PTO.mdl` copy to measure steady turbine power and simulate both controllers. Run `analyze_tmats_pto` to regenerate this report and the figures. To configure an already loaded model, run `tmats_pto_setup([],0.20,9500)`. This uses the measured, speed-specific reference cache. The no-argument setup retains the original 10000 rpm, 10% defaults.

Saved evidence: `trim.mat/csv`, `reference.json`, `case_01.mat/csv`, `case_02.mat/csv`, `metrics.json/csv`, `events.csv`, `pto_comparison.png`, and `pto_transient_detail.png`. Existing GPT and DOB model files are preserved.

This is one deterministic, noise-free sample-engine operating point. The estimate is fuel-equivalent lumped model error, not a direct calibrated power measurement. The experiment tests mechanical load rejection but does not qualify the observer for hardware or establish broad closed-loop robustness.
