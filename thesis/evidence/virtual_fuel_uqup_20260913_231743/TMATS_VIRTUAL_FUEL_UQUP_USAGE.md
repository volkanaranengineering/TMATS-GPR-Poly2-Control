# Increasing uncertainty gain schedule

This separate scenario preserves both earlier controllers. With the same frozen GP, nominal uncertainty scale, and base gains Kp=3, Ki=60 /s, define

```text
s = max(sigma_setpoint, sigma_feedback) / sigma_reference
x = clip((s-1)/2, 0, 1)
factor = 1 + 3*x^2 - 2*x^3
Kp = 3*factor
Ki = 60*factor
```

The factor is exactly 1 for s<=1, 1.5 at s=2, and 2 for s>=3. The cubic smoothstep has zero slope at both endpoints. Its cap of 2 beyond three reference SDs prevents unbounded gains. Standard deviation is nonnegative: the user's plus/minus bands are treated symmetrically by magnitude, not as the sign of speed or fuel error.

The reference SD remains the median response SD at the 600 frozen training locations (approximately 0.00117869140424 lbm/s). This is the same normalization used for the decreasing schedule. Gain limits are thus Kp=3 to 6 and Ki=60 to 120 /s on valid GP queries. The same feedforward, bumpless integral transfer, startup handover, causal acceleration estimate, fuel limits and anti-windup are retained.

```matlab
out = run_tmats_virtual_fuel_uqup_study;
report_tmats_virtual_fuel_uqup(out);
```

For one run:

```matlab
[MWS,DOB,PTO,VF] = tmats_virtual_fuel_uqup_setup(9500,.1,[.3 1.5 3],[3 60],true);
sim('GasTurbine_Dyn_Template_VirtualFuelUQUp');
```

Ten inherited scenarios compare against the original inverse-GPR PI, fixed FF retuning, and decreasing uncertainty schedule. Base gains are not retuned, isolating the change in scheduling direction. GP means/SDs, scheduled gains, command composition and bumpless integration are numerically checked. Full-run performance scores are withheld for invalid plant runs.
