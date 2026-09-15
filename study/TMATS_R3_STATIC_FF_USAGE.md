# R3 with static GPR feedforward driven by the moving setpoint

The requested FF is `g(request, 0, inlet_temperature, inlet_pressure)` from the same frozen four-input inverse GP. Measured acceleration is used only in the unchanged R3 feedback path. No desired-acceleration feedforward is included.

The previously named R3 already used this static FF term. The new study explicitly compares:

- `GasTurbine_FFCompare_BasePI.mdl`: unchanged base PI.
- `GasTurbine_FFCompare_R3.mdl`: R3 feedback-only, with direct static FF removed from its command sum. The GP setpoint evaluation remains in the virtual error.
- `GasTurbine_FFCompare_R3_GPRFF.mdl`: R3 with the requested static FF. Its trajectory exactly reproduces the previous R3 result.

Use these in the existing TMATSGPT/T-MATS workspace with the prior frozen models and setup files. All call the same `tmats_r3_covered_cycle_setup.m`: 9450-9550 rpm, 5 s ramps, 10 s holds, four cycles in 120 s after 60 s preparation. The ambient route is 0 m/ISA-20 to 10000 m/ISA+20 to 0 m/ISA 0, with linear knots at test times 0, 60 and 120 s.

Base PI gains remain 0.025/0.05. Both R3 cases use Kp=0.025, Ki=0.1, Kd=0.002, with the same filtering and guard logic. Startup integral tracking accounts for whether FF is present. No gains are retuned and the posterior is not refitted.

```matlab
out='results/r3_static_ff_20260915';
run_tmats_r3_cycle(out,true,true);
audit_tmats_cycle_coverage(out);
report_tmats_static_ff(out);
```

`verify_tmats_static_ff.py` independently verifies the request, RMSE, command algebra, saturation, integration and equivalence with earlier base PI/R3+FF trajectories. `build_tmats_static_ff_report.py` creates the native LaTeX report. The result folder contains MAT and CSV traces, per-segment performance and all GP coverage queries.

Results (base PI / R3 feedback-only / R3+static FF): overall RMSE 0.591513 / 0.639320 / 0.702711 rpm; hold RMSE 0.496482 / 0.394958 / 0.337547 rpm; fuel reversal metric 0.723611 / 0.378265 / 0.387541 lbm/s. Static FF improves hold accuracy, peak error and IAE compared with feedback-only R3, but increases overall RMSE by 9.9% and fuel reversals by 2.5%. All queries pass strict bounds and joint hull checks; no fallback or compressor-map speed overrun occurs.

The models/results archive is an overlay for the existing workspace. Prior broad-cycle and covered-cycle models are preserved. The superseded dynamic-acceleration FF attempt is excluded from these results and deliverables.
