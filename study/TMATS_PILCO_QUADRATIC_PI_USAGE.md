# PILCO-style quadratic feedforward + PI

The model `GasTurbine_PILCO_Quadratic_PI.mdl` runs the existing T-MATS plant at
9250 rpm, sea level, ISA 0 with 10% shaft-power load pulses.

```matlab
tmats_pilco_setup;
open_system('GasTurbine_PILCO_Quadratic_PI');
sim('GasTurbine_PILCO_Quadratic_PI');
```

The frozen quadratic inverse supplies `p2(reference,0,inletTemperature,inletPressure)`.
The learned speed-error PI has Kp = 0.06460568152289617,
Ki = 0.17102609607596805, and no derivative action. Fuel limits are 0.2 to 4
lbm/s with conditional integration and startup tracking before 45 seconds.

## What was learned

This is an offline PILCO-style improvement step: a GP transition model with
analytic uncertain-input moments and numerical policy gradients tunes the two
PI gains. The polynomial coefficients remain frozen. It does not implement
the complete original PILCO data-collection loop. A constant-speed test cannot
identify the benefit of the quadratic surface across operating points.

The first two pulses of three historical controller runs train the GP; the
third pulse is held out for a dynamics check. A short probabilistic planning
rollout selects the gains. They are frozen before nonlinear 10% and 5% plant
tests. Existing previous-model traces supply the comparison methods.

## Results and practical interpretation

| 10% load controller | Speed RMSE (rpm) | Fuel ringing (lbm/s) |
|---|---:|---:|
| Base PI | 2.42090 | 2.07023 |
| Original quadratic + PID | 1.66580 | 1.69680 |
| Retuned quadratic + PID | 1.54614 | 1.29904 |
| PILCO quadratic FF + PI | 1.19728 | 14.82523 |

The new gains improve tracking but substantially worsen fuel oscillation,
fine settling and minimum surge margin relative to retuned Poly2. Do not
interpret the RMSE improvement as an overall replacement recommendation.
The 5% validation shows the same tradeoff. All new traces pass the inherited
numerical validity checks, and command/integral replay agrees within 1e-8.

## Reproduction

1. Run `pilco_tmats.py` with NumPy, pandas and SciPy. The environment used here
   is the bundled Python 3.12 with `PYTHONPATH=tmp/pilco_deps`.
2. Run `run_tmats_pilco` in MATLAB. This builds a separate model copy and runs
   the learned 10%, learned 5%, and initial-policy 10% cases.
3. Run `build_pilco_deliverables.py` with matplotlib, imageio, imageio-ffmpeg,
   PyMuPDF and the installed MiKTeX compiler. `--no-video` rebuilds the paper
   and verification without rendering the movie again.

Study outputs live in `results/pilco_quadratic_pi_20261010`. The PDF is in
`output/pdf/PILCO_Quadratic_FF_PI_Comparison.pdf`; editable LaTeX and figures
are in `output/pdf/pilco_quadratic_pi_source`. The animation is
`output/video/PILCO_Quadratic_FF_PI_Comparison.mp4`.

The model is an overlay for this workspace and its adjacent T-MATS library.
It needs the historical setup, trim, inverse-GPR configuration, and quadratic
fit files already present. Rerunning replaces only this study's outputs.

The animated rotors are illustrative, visually scaled motion. Curves,
readouts and metrics come from the saved nonlinear T-MATS simulations.
