# 9500 rpm nominal speed: 20% and 30% shaft extraction

The preceding 20% and 30% scenarios were repeated at 9500 rpm without retuning PI or DOB. Each load is recalculated using steady turbine power at 9500 rpm.

## Reference and scenario

Steady turbine shaft power is **19160.793887 hp** (14.288202 MW). The corresponding unloaded fuel flow is 1.849471 lbm/s. Power is averaged over seconds 55-60 after convergence to the operating point. Gross turbine power balances compressor load; the percentages are not taken from near-zero net shaft power.

Preparation starts at the standard 10000 rpm initial state, holds through 5 s, ramps the demand to 9500 rpm at 10 s, then holds through 60 s. The speed demand stays at 9500 rpm during the 90 s evaluation. Identical mechanical load pulses are applied at 10.005-15.000, 30.000-40.005, and 60.000-75.000 s after preparation. The injected fuel disturbance is zero.

The original PI gains (0.025, 0.05), DOB gain 0.25, Q pole-frequency parameter 0.5 Hz, correction limit +/-0.15 lbm/s, and fuel limits 0.2-4 lbm/s are unchanged. The eight-term model and its equilibrium correction are unchanged; trim removal handles the initial observer offset.

## Results

| Load | Extraction | Controller | Status | First invalid time* | RMSE | Maximum droop |
|---|---:|---|---|---:|---:|---:|
| 20% | 2.857640 MW | PI | PASS | None | 6.430 rpm | 53.397 rpm |
| 20% | 2.857640 MW | PI+DOB | PASS | None | 6.203 rpm | 53.013 rpm |
| 30% | 4.286460 MW | PI | FAIL | 10.155 s | Not valid | Not valid |
| 30% | 4.286460 MW | PI+DOB | FAIL | 10.155 s | Not valid | Not valid |

*Time after preparation; the first extraction starts at 10.005 s. Complete-run performance is suppressed if any earlier state was propagated through an invalid solve.

## Recovery and limits

| Load | Controller | First application recovery | First removal recovery | Peak fuel in valid prefix |
|---|---|---:|---:|---:|
| 20% | PI | 1.815 s | 1.875 s | 3.3335 lbm/s |
| 20% | PI+DOB | 1.665 s | 1.320 s | 3.3602 lbm/s |
| 30% | PI | Not valid | Not valid | 3.5686 lbm/s |
| 30% | PI+DOB | Not valid | Not valid | 3.5926 lbm/s |

Recovery requires remaining within +/-1 rpm until the next edge, with at least 0.5 s confirmed dwell. Invalid full trajectories do not receive recovery-time claims. Valid-prefix fuel maxima use only samples before the first invalid point.

At **20%**, the DOB reduces RMSE by **3.527%**. Application recovery changes from 1.815 to 1.665 s; removal recovery changes from 1.875 to 1.320 s. The benefit is mainly faster recovery rather than a large reduction of the initial speed excursion.

At **30%**, the complete test does not pass. PI first fails at 10.155 s; PI+DOB first fails at 10.155 s. Fuel at the first failed solve is 3.7489 lbm/s (PI) and 3.7769 lbm/s (PI+DOB), below the 4 lbm/s ceiling. Minimum reported compressor margin in the valid prefix is 0.879% and 0.625%, respectively. Thus initial failure is a flow/map convergence limitation before fuel saturation; it does not establish physical surge. Later apparent recovery and complete-run error metrics remain diagnostic. The current controller/model combination has not established regulation performance for this condition.

## Comparison with the 10000 rpm tests

At 10000 rpm, the previous 20% and 30% loads were 4.160484 and 6.240727 MW, respectively, and both levels failed. The new tests change both operating point and absolute load as requested. Therefore an improvement at the same percentage must not be described as improvement at the same absolute extracted power.

## Verification, files, and reproduction

Each run contains 10001 samples at 15 ms through 150 s. The same source profile reaches the shaft power port in both controllers. The torque-balance reconstruction is checked against logged acceleration. Validity requires finite signals, positive fuel and compressor margin, flow residual <=1e-9, and fewer than 200 solver iterations over the entire run. The observer receives sensed speed and known fuel only.

Run `run_tmats_pto_9500_batch` to repeat both simulations. For one level, use `out=run_tmats_pto_study(0.2,9500); analyze_tmats_pto(out);` (or `0.3`). For an already loaded PTO model, `tmats_pto_setup([],0.2,9500)` loads the measured speed-specific power reference. The no-argument setup still selects the original 10000 rpm, 10% case.

No model rebuild or controller retuning is necessary. The original model files are unchanged. The new `pto_reference_9500rpm.json` cache does not replace the 10000 rpm power reference. These are deterministic noise-free sample-engine tests, not a deployment qualification.

- Source result directory: `results/dob_pto_9500rpm_20pct_20260912_195059_980`
- Source result directory: `results/dob_pto_9500rpm_30pct_20260912_195120_747`
