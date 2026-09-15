# Inverse-GPR feedforward with retuned fuel-domain PI

This extends the previous dual inverse-GPR controller in `tmats_virtual_fuel_sfun.m`. The previous model and archived results are preserved.

The completed local search selected **Kp=3, Ki=60 /s**, compared with the previous Kp=4, Ki=40 /s. These are the setup defaults; each runner trial still supplies its gains explicitly.

```matlab
out = run_tmats_virtual_fuel_ff_study;
report_tmats_virtual_fuel_ff(out);
```

The runner builds `GasTurbine_Dyn_Template_VirtualFuelFF.mdl`, evaluates a local eight-pair gain grid using the four 9000 rpm ramp cases, freezes the best physically valid pair, and compares ten ramp/step scenarios. The timestamped output path is saved in `tmp/virtual_fuel_ff_directory.txt`. The report compares against the previous inverse-GPR fuel PI (Kp=4, Ki=40), rather than only against the original speed PI.

The controller computes:

```text
v_ref = g(governed reference, acceleration setpoint)
v_feedback = g(sensed speed, filtered sensed acceleration)
error = v_ref - v_feedback
fuel_unsaturated = v_ref + Kp*error + integral
fuel_command = clip(fuel_unsaturated, 0.2, 4)  [lbm/s]
```

`v_ref` is the GPR feedforward term. `VF_setpoint` logs it directly. `VF_integral` logs the residual PI integral, and `VF_unsaturated` includes feedforward. Before handover at 30 s, the integral tracks `startup_PI - v_ref - Kp*error` to avoid adding nominal fuel twice. Conditional integration prevents windup against the full command limits. The causal acceleration filter retains its 0.03 s time constant and the sample time remains 0.015 s.

The acceleration setpoint is zero in the inherited constant-speed disturbance scenarios. Feedforward is consequently constant after handover. At identical gains, feedforward and a compensating integral offset are algebraically equivalent to the old controller. `same_gains_ablation.csv` verifies that fact numerically on all four 9000 rpm cases. Any disturbance-response improvement comes from the finer gain search; these tests do not measure feedforward reference-tracking benefits.

After running, configure the model with the actual selected gains:

```matlab
s = load(fullfile(out,'selected_gains.mat'),'gains');
[MWS,DOB,PTO,VF] = tmats_virtual_fuel_ff_setup(9500,.1,[.3 1.5 3],s.gains,true);
sim('GasTurbine_Dyn_Template_VirtualFuelFF');
```

Gain units are dimensionless Kp and Ki in 1/s, acting on a fuel-valued error. They are not numerically comparable to the original speed PI gains. The GP stays frozen; it is not trained on the disturbance runs. Held-out 9500 rpm cases do not select gains. Invalid plant trajectories have their full-run scores withheld and their plots truncated at first invalid sample.

The saved results include tuning scores, selected gains, run MAT/CSV files, validity and surge-margin metrics, comparison tables, a same-gain ablation, and response figures. A finite grid establishes the best tested pair, not global optimality or robustness outside the tested conditions.
