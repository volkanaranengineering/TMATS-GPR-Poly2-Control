# Three inverse-GPR controller remedies

This addendum preserves the existing T-MATS plant and frozen four-input exact GP. It implements three alternatives and compares them with the recorded base PI and previous inverse PI at 4000 m / ISA+5 / 9500 rpm with 10% shaft-power pulses, then freezes each selection for 35 environmental cases.

## Open and simulate

Run MATLAB R2018b from the TMATSGPT workspace with the existing T-MATS libraries and compiled blocks on its path. The models require that workspace; the source archive is an overlay, not a standalone engine installation.

```matlab
tmats_gpr_remedy_setup(3);
open_system('GasTurbine_Remedy3');
sim('GasTurbine_Remedy3');
```

Use `GasTurbine_Remedy1` / setup mode 1 or `GasTurbine_Remedy2` / mode 2 for the other alternatives. Each saved model also invokes the appropriate setup in its preload callback. Simulations run 150 s; the evaluation interval is 60-150 s, after the environmental ramp and bumpless controller handover at 45 s. Plots show evaluation time, with load edges at approximately 10, 15, 30, 40, 60 and 75 s.

## Implemented feedback

Let g(N,a,T,P) predict fuel in lbm/s, r be requested speed, Ns sensed speed, and a filtered sensed acceleration.

| Controller | Feedback | Selected parameters |
|---|---|---|
| R1 | Original virtual-fuel error, with reduced PI gains | Kp=1.5, Ki=22 |
| R2 | Integrate static inverse error; independently attenuate acceleration feedback | Kp=16, Ki=40, beta=0.05 |
| R3 | Normalize inverse errors by local derivatives; independent acceleration damping; guarded speed-feedback fallback | Kp=0.025, Ki=0.1, Kd=0.002 |

All use acceleration filter tau=0.03 s and sample time 0.015 s. R1/R2 gains act on fuel-domain errors, whereas R3 gains act on approximate speed/acceleration, so their numbers cannot be compared directly. All retain GP feedforward, fuel limits and conditional anti-windup integration. No uncertainty gain scheduling is used.

R3 falls back when either derivative is <=1e-5 in its own physical units, corrected compressor speed leaves [0.5,1.05], or normalized/raw speed-error ratio leaves [0.25,4] for raw error magnitude >0.01 rpm. Fallback uses ordinary speed error and filtered acceleration while retaining GP feedforward. It does not validate compressor-map extrapolation. `VF.forceFallback=true` is only the matched-gain PID diagnostic; normal setup leaves it absent/false.

## Target results

| Method | Speed RMSE (rpm) | Fuel ringing (lbm/s) | Fine recovery to 0.1 rpm (s) |
|---|---:|---:|---:|
| Base PI | 2.53147 | 2.03043 | 2.46 |
| Previous inverse PI | 1.81870 | 3.81687 | Not recovered in every event interval |
| R1 | 2.43867 | 1.79810 | Not recovered in every event interval |
| R2 | 2.32297 | 0.68612 | 1.53 |
| R3 | 1.75198 | 1.45899 | 1.38 |

All target responses remain within the broad +/-95 rpm (1%) window, so its recovery metric is zero. Ringing is summed excess fuel total variation in the six two-second edge windows, not fuel consumption. The target is a tuning case: these gains were selected from 80 candidates using the minimum worst ratio of RMSE/base and ringing/base, separately for each family.

The matched-gain filtered PID diagnostic produces RMSE=1.74912 rpm and ringing=1.42916 lbm/s. Thus the target benefit primarily comes from the feedback architecture and tuning; these results do not establish an advantage of GPR over an equally tuned PID.

R3 improves both RMSE and ringing in all 35 environmental cases, including all 25 without monitored compressor-map speed overruns. It uses fallback in 10 conditions. R1 improves both in 7/35; R2 in 9/35, with eight rejected R2 runs. R1 retains slow-tail and negative-slope problems. Consult the PDF and complete grid table for measured transfer results before choosing a controller. R3 is the preferred implemented architecture for this simulation study.

## Results and reproduction

`tmp/remedies_directory.txt` points to `results/gpr_remedies_20260914_220633`; `tmp/environment_directory.txt` identifies the previous environmental study. These pointer files currently contain absolute paths. If relocating the workspace, update both pointers before setup. The inherited setup also loads the original `results/inverse_gpr_20260913_150824_698/inverse_gpr_model.mat` before replacing it with the environmental GP.

The new directory contains the 80 tuning, 105 transfer and one ablation trajectory files, selected parameters, derivative diagnostics, implementation replay checks, and `remedy_comparison.csv`. Native MAT and CSV trajectories remain in the workspace; the compact controller archive contains the implementations, required GP/trim parameters, and summary/verification tables.

```matlab
out = strtrim(fileread('tmp/remedies_directory.txt'));
diagnose_tmats_inverse_feedback(out);
run_tmats_gpr_remedies(out,1:80,'tune');
select_tmats_gpr_remedies(out);
run_tmats_gpr_remedies(out,1:105,'transfer');
run_tmats_gpr_remedies(out,1,'ablation');
report_tmats_gpr_remedies(out);
```

The runner resumes existing MAT results. Use a new output directory for a genuinely fresh study, and select parameters there before transfer. `verify_tmats_gpr_remedies.py tune` and `verify_tmats_gpr_remedies.py transfer` replay saved control equations independently. `build_tmats_remedy_report.py` assembles LaTeX using the directory pointer; compile twice with pdflatex. The LaTeX archive includes the final source and vector figures.

Early-stopped or otherwise invalid runs receive no performance score. The acceptance test requires full duration, finite valid plant signals, positive fuel/surge margin, flow convergence and pre-test trim. Numerical acceptance is separate from the compressor-map boundary flag. The saved controller models omit the study-only invalid-state stopping instrumentation.
