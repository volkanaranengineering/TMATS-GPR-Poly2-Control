# Uncertainty-scheduled inverse-GPR fuel controller

This follows the fixed feedforward study in `TMATS_VIRTUAL_FUEL_FF_USAGE.md` and retains its selected base gains, Kp=3 and Ki=60 /s.

```matlab
out = run_tmats_virtual_fuel_uq_study;
report_tmats_virtual_fuel_uq(out);
```

The reference scale `VF.sigmaReference` is the median predictive **response** standard deviation of the frozen inverse GP at its 600 training inputs. It has fuel units (lbm/s) and does not depend on benchmark outcomes. Both GP outputs are evaluated for their own predictive uncertainty each controller sample:

```text
sigma_max = max(sigma_setpoint, sigma_feedback)
s = sigma_max / sigmaReference
alpha = 10^(-(s/3)^2)
Kp = 3 * alpha
Ki = 60 * alpha
```

At `sigma_max = 3*sigmaReference`, both gains are 10% of their base values. At six times the reference SD they are 0.01%. The factor tends to zero as uncertainty rises. This is a threshold based on normalized predictive SD, not a three-sigma tail probability. Response SD includes fitted observation noise, so the nominal factor need not equal one.

The fuel command is `clip(g(reference,0) + Kp*(g(reference,0)-g(sensedSpeed,filteredAcceleration)) + integral, 0.2, 4)`. The integral tracks startup fuel before the 30 s handover. A gain change transfers `(previousKp-currentKp)*error` into the integral, avoiding a command discontinuity caused solely by scheduling. The accumulated integral remains to support the load when gains shrink; its new increments shrink with Ki. Conditional anti-windup uses the complete unsaturated command.

Open `GasTurbine_Dyn_Template_VirtualFuelUQ.mdl`, or configure a single case:

```matlab
[MWS,DOB,PTO,VF] = tmats_virtual_fuel_uq_setup(9500,.1,[.3 1.5 3],[3 60],true);
sim('GasTurbine_Dyn_Template_VirtualFuelUQ');
```

Logs include `VF_sdSetpoint`, `VF_sdFeedback`, `VF_gainFactor`, `VF_Kp`, and `VF_Ki`, in addition to command, feedforward, feedback, error, filtered acceleration and integral. The exact GP's saved Cholesky factor computes predictive variance online. No uncertainty clipping conceals out-of-training-range queries.

The runner uses the fixed FF study referenced by `tmp/virtual_fuel_ff_directory.txt`; it loads that study's selected gains and records its path in `configuration.mat`. It compares ten inherited scenarios against the previous inverse-GPR PI and the fixed FF version. Figures truncate invalid trajectories and full-run scores are withheld for invalid plant results. SD replay, gain identities and the bumpless integral recurrence are checked numerically.

Uncertainty is conditional on the fitted GP and its nominal training conditions. It does not guarantee detection of unmodeled shaft loads or sensor error. If uncertainty barely changes, the resulting behavior is mostly constant gain derating. The report states measured performance and validity rather than assuming scheduling improves every case.
