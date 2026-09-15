# R3 versus base PI within the GP input envelope

Open `GasTurbine_Covered_R3.mdl` or `GasTurbine_Covered_BasePI.mdl` in the existing TMATSGPT workspace. Both call `tmats_r3_covered_cycle_setup.m`. The original broad-cycle models and results are preserved.

Final speed envelope: **9450-9550 rpm**, with 5 s ramps (20 rpm/s) and 10 s holds. Four cycles occupy 120 s after a separate 60 s preparation. The original ambient route is retained: 0 m/ISA-20 at test time 0, 10000 m/ISA+20 at 60 s, and 0 m/ISA 0 at 120 s, with linear interpolation of altitude and ISA departure. Mach is zero. No extra shaft-load or fuel disturbances are applied.

Base PI gains remain Kp=0.025, Ki=0.05. R3 remains Kp=0.025, Ki=0.1, Kd=0.002, with the same exact GP, 0.03 s acceleration filter, 0.015 s sampling, saturation, conditional integration and fallback logic. Setpoint inverse acceleration remains zero. The common request governor uses its inherited 150 rpm/s limit; no gain retuning is performed.

```matlab
tmats_r3_covered_cycle_setup;
open_system('GasTurbine_Covered_R3');
sim('GasTurbine_Covered_R3');

out='results/r3_covered_cycle_20260915_final';
run_tmats_r3_cycle(out,true);
report_tmats_r3_cycle(out);
```

The report function invokes `audit_tmats_cycle_coverage.m`. It audits all three inverse-query branches at every evaluation sample against both the original 1400-point GP's rectangular input bounds and its joint 4D convex hull. Base PI receives no GP feedback; its queries are reconstructed offline for the same domain check. Coverage applies to the 120 s test, not the inherited initial condition before preparation.

Strict bounds are reported alongside numerical-tolerance bounds. The hull uses standardized coordinates and a 1e-7 half-space tolerance. Degenerate zero-volume simplices from coplanar training rows are excluded, and all retained half-spaces are verified against the training set. Nearest-neighbour distances in GP kernel coordinates are supplied as a density diagnostic; hull membership does not guarantee dense local training support or low uncertainty.

The preliminary 9400-9600 rpm attempt is retained in `results/r3_covered_cycle_20260915`. It had zero min/max range flags but brief joint-hull excursions. It is excluded from the final result archive. The final test adds speed/acceleration margin and must pass both coverage checks for acceptance as a constrained test.

`BasePI.mat` and `R3.mat` contain the complete traces and configurations. The CSV files include summary metrics, all sixteen ramp/hold segments and every audited GP query. `verify_tmats_r3_cycle.py covered` independently checks request reproduction, speed RMSE, segment fuel variation, R3 command algebra and integration. `build_tmats_covered_cycle_report.py` generates native LaTeX for the report.

The fuel reversal metric sums excess total variation separately within each ramp/hold segment. Ambient changes can cause legitimate fuel reversals, so this is a ringing proxy and differs from the earlier two-second shaft-load metric. Hold recovery is measured to a persistent 1% speed window. The models/results package is an overlay for the existing T-MATS and frozen-GP workspace, not a standalone engine installation.

Final results: all 24003 queries per method are within strict input bounds and the joint hull. R3 has no range flags or fallback use; neither trajectory exceeds the monitored compressor speed map. Base PI / R3 full RMSE is 0.591513 / 0.702711 rpm; ramp RMSE 0.745638 / 1.118469 rpm; hold RMSE 0.496482 / 0.337547 rpm; segment fuel reversal 0.723611 / 0.387541 lbm/s. R3 therefore improves hold accuracy and fuel smoothness but has higher overall RMSE because of the ramps. All eight holds remain within the 1% speed window.
