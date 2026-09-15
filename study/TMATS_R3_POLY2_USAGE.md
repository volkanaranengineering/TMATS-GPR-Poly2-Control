# Full-quadratic inverse challenger with the same R3 architecture

The new model `GasTurbine_PolyCompare_R3_Poly2FF.mdl` replaces every inverse GPR mean and derivative in R3 + static FF with a single frozen full second-order polynomial. Static FF remains evaluated at the moving speed setpoint, zero acceleration and simulated inlet temperature/pressure. Measured acceleration remains in feedback only.

The equation has 15 terms: constant, four linear terms, four squares and six pairwise interactions in standardized inputs `[speed_rpm, acceleration_rpm_s, inlet_temperature_K, inlet_pressure_kPa]`. Output is fuel in lbm/s. `results/poly2_inverse_20260915/poly2_model.json` contains full-precision coefficients and normalization, with readable CSV tables alongside. The PDF gives the complete equation and coefficient table.

The fit uses ordinary least squares on exactly the same 1400 training rows as GPR. The same 200 held-out observations are only evaluated, never used for fitting or tuning. No regularization, coefficient constraints, clipping or polynomial-specific controller tuning is used. Training/test RMSE is 0.059814/0.062221 lbm/s; the original GPR test RMSE is 0.001612 lbm/s. The design matrix has rank 15 and condition number 13.58.

R3 gains remain Kp=0.025, Ki=0.1, Kd=0.002. Filters, slope normalization, fallback thresholds, fuel limits, conditional integration and startup tracking are unchanged. `tmats_r3_poly2_sfun.m` has the same command logic as `tmats_gpr_remedy_sfun.m`; its evaluator is `tmats_poly2_mean_gradient.m` instead of the GP evaluator. Analytic polynomial derivatives include input-standardization factors.

Four fresh models use the `GasTurbine_PolyCompare_` prefix: `BasePI`, `R3` (GPR feedback-only), `R3_GPRFF` and `R3_Poly2FF`. The test is unchanged: 9450-9550 rpm, 5 s ramps, 10 s holds, four cycles in 120 s after 60 s preparation. The ambient route is 0 m/ISA-20 to 10000 m/ISA+20 to 0 m/ISA 0 at test times 0/60/120 s. No extra load disturbance, noise or actuator lag is introduced.

```matlab
tmats_r3_poly2_setup;
open_system('GasTurbine_PolyCompare_R3_Poly2FF');
sim('GasTurbine_PolyCompare_R3_Poly2FF');

out='results/r3_poly2_challenger_20260915';
validate_tmats_poly2;
run_tmats_r3_cycle(out,true,true,true);
audit_tmats_cycle_coverage(out);
report_tmats_static_ff(out);
```

Run `fit_tmats_poly2_inverse.py` before these commands to regenerate the fitted equation. Run `verify_tmats_static_ff.py poly` for independent controller replay, polynomial prediction reconstruction and unchanged-comparator checks. `build_tmats_poly2_report.py` generates native LaTeX.

All four final trajectories pass numerical acceptance and remain within the common training input bounds and 4D hull, with zero map speed overruns and zero inverse-controller fallback. Overall RMSE is 0.591513 (base PI), 0.639320 (GPR feedback-only), 0.702711 (GPR+FF) and 0.676972 rpm (quadratic+FF). Fuel reversal is 0.723611, 0.378265, 0.387541 and 0.385818 lbm/s respectively. The polynomial slightly improves both headline metrics versus GPR+FF on this cycle despite its poorer held-out fuel prediction. Its peak error and maximum slew are slightly higher. This does not establish superiority across the full operating envelope.

The native MAT/CSV traces and all coverage queries are in `results/r3_poly2_challenger_20260915`. This archive is an overlay for the existing T-MATS and frozen-model workspace, not a standalone engine installation. Existing models and studies are preserved.
