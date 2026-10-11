# Ringing-aware PILCO-style quadratic feedforward + PI

This study learns PI gains using a GP dynamics model and an expected excess
total-variation penalty. The static quadratic feedforward and deployed PI
structure are unchanged. The extra command-memory states exist only during
offline prediction; no post-processing smooths the plotted results.

Selected weight: 0.20. Kp = 0.0247976184654604,
Ki = 0.0538591996239495, Kd = 0.

```matlab
tmats_pilco_smooth_setup;
open_system('GasTurbine_PILCO_Smooth_PI');
sim('GasTurbine_PILCO_Smooth_PI');
```

## Measured results

At 9250 rpm, sea level ISA 0, with the same 10% load pulses:

| Controller | RMSE, rpm | Ringing, lbm/s | Fine settling, s |
|---|---:|---:|---:|
| Base PI | 2.42090 | 2.07023 | 2.475 |
| Retuned Poly2 + PID | 1.54614 | 1.29904 | 0.930 |
| Previous PILCO | 1.19728 | 14.82523 | 1.920 |
| Smooth PILCO | 2.38773 | 2.08375 | 2.220 |

The new controller reduces ringing by 85.9% and peak fuel slew by about
54.7% relative to previous PILCO. It gives up much of the previous tracking
advantage. Compared with base PI, its RMSE is about 1.4% lower and ringing
about 0.7% higher. Retuned Poly2 still has lower RMSE and ringing.

Frozen-gain 5% validation gives RMSE 1.15329 rpm and ringing 1.06150 lbm/s,
an 86.6% ringing reduction relative to previous PILCO. Both selected runs
pass numerical validity checks. This is local amplitude validation, not
proof of robustness across speeds, ambient conditions or hardware.

## What the new penalty does

For each planned load edge, ringing equals sum(abs(fuel increments)) minus
abs(net fuel change). Required monotone fuel motion has zero excess variation;
reversals increase it. The objective is expected tracking cost + expected fuel
magnitude cost + lambda times expected normalized ringing.

A previous-command state and an event-start anchor retain their correlations
with the turbine state. Expected absolute Gaussian increments use the
folded-normal formula. This includes uncertainty rather than penalizing only
the mean command. The analytic penalty agrees with a 5,000-particle check on
the same GP to about 0.0014%; this validates surrogate calculation consistency,
not physical confidence-band calibration.

Seven coarse weights and three intermediate refinements are tested. The
selected policy minimizes max(RMSE/base_PI_RMSE, ringing/base_PI_ringing) on
the 10% tuning runs. The 5% validation is performed only after selection.
No global optimum or dominance over the derivative-feedback comparator is claimed.

## Reproduce

Use the existing T-MATS workspace and adjacent library. Python dependencies
are available under `tmp/pilco_deps` in this environment.

1. Run `pilco_smooth.py` to optimize the seven coarse weights using the frozen GP.
2. Run `run_tmats_pilco_smooth('tune')` in MATLAB.
3. Run `refine_pilco_smooth.py`, then repeat the MATLAB tuning command. It resumes
   existing cases and runs only the three additions.
4. Run `select_pilco_smooth.py`, then `run_tmats_pilco_smooth('validate')`.
5. Run `check_pilco_smooth_mc.py`, `build_pilco_smooth_report.py`, and
   `build_pilco_smooth_video.py` in that order.

Results, checks, candidate traces, and the frozen policy are in
`results/pilco_smooth_20261010`. The detailed nine-page native LaTeX report is
`output/pdf/PILCO_Smooth_Ringing_Penalty.pdf`. Editable source and figures are
under `output/pdf/pilco_smooth_source`. The approved four-window layout is
reused in `output/video/PILCO_Smooth_Four_Window_Load_Comparison.mp4`, a
102-second 1080p/24fps comparison with explanation and results cards.

The new model and package are overlays for this workspace, not standalone
T-MATS installations. Prior studies remain available. Reruns overwrite this
study's outputs, so preserve a copy before running a separate experiment.
