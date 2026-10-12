# Inverse GPR feedforward with the existing PI

Open `GasTurbine_Dyn_Template_GPR_FF.mdl` after building it, or run:

```matlab
out = run_tmats_gpr_ff_benchmarks;
```

The runner creates the new Simulink model and executes 60 runs: PI, DOB, LESO, UDE, GPIO, and GPR_FF across ten physical shaft-load scenarios. It saves a timestamped results directory and its path in `tmp/gpr_ff_directory.txt`.

To configure a single case:

```matlab
[MWS,DOB,PTO,ALT,FF] = tmats_gpr_ff_setup(9500,0.10,[0.30 1.50 3.00],'GPR_FF');
sim('GasTurbine_Dyn_Template_GPR_FF');
```

Use `[0 0 0]` for the earlier step-load protocol. Other supported method names are `PI`, `DOB`, `LESO`, `UDE`, and `GPIO`. The helper sets up the inherited plant parameters; use the benchmark runner for validated and archived results.

The feedforward uses the frozen exact inverse GP:

```text
a_ref = limit((reference - previous_reference)/Ts, -150, 150)
query_speed = limit(sensed_speed, 9000, 10000)
FF = enable_ramp * limit(g(query_speed,a_ref) - g(nominal_speed,0), -0.15, 0.15)
fuel_command = limit(original_PI + FF, 0.2, 4)
```

The GP inputs are speed in rpm and reference acceleration in rpm/s; its output and the correction are lbm/s. The PI gains remain 0.025 and 0.05. The GP is activated over absolute seconds 30–32 after the reference transition has settled. The inverse equilibrium estimate is subtracted because the inherited PI integral already supplies nominal fuel.

The state-dependent speed input makes this **state-scheduled nominal feedforward**, not purely reference-only feedforward. It does not use actual plant acceleration, injected shaft power, or a future disturbance schedule. No additional speed-error gain is hidden in the desired acceleration. During the constant-speed disturbance tests the desired acceleration is zero. This architecture therefore need not improve unknown-load rejection, even when inverse fuel prediction is accurate.

`GPR_speedGuard` records when sensed speed is outside the modeled speed band; the queried speed is clipped to that band. `GPR_FF`, `GPR_nominalFuel`, `GPR_referenceAcceleration`, and `GPR_querySpeed` are logged. The exact GP mean is evaluated online using all 600 training points. Model-conditional fuel uncertainty is exported offline at up to 100 valid evaluation samples per run and is not used as a loaded-plant error bound.

Run `summarize_tmats_gpr_ff.py` with the project's PDF Python dependencies to regenerate the extended comparison, recovery tables, figures, and PDFs. It verifies the disabled GP branch reproduces the earlier five methods at 10% load and withholds complete-run scores after any invalid plant solve.

This Level-2 MATLAB S-function implementation is for desktop Simulink simulation. The original models remain separate; no embedded code-generation or closed-loop robustness guarantee is implied.
