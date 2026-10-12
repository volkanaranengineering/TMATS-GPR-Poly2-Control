# Inverse-GPR virtual-fuel PI controller

The new `GasTurbine_Dyn_Template_VirtualFuel.mdl` model implements the requested dual projection:

The tuned defaults are **Kp=4, Ki=40 1/s**, selected using only the 9000-rpm disturbance cases. See `results/virtual_fuel_20260913_182229_028/REPORT.md` for measured comparison results.

```text
speed setpoint, acceleration setpoint -> inverse GP -> virtual fuel setpoint --+
                                                                           subtract -> PI -> limited fuel -> plant
sensed speed, estimated acceleration  -> inverse GP -> virtual fuel feedback --+
```

Both projections use the same frozen 600-sample exact inverse GP from `results/inverse_gpr_20260913_150824_698/inverse_gpr_model.mat`. Neither projection receives shaft power, plant acceleration, or a disturbance estimate.

At sample k, with sampling interval T:

```
a[k] = p*a[k-1] + (1-p)*(Ns[k]-Ns[k-1])/T, p=exp(-T/0.03)
vsp[k] = g(Nsp[k], asp[k])
vfb[k] = g(Ns[k], a[k])
e[k] = vsp[k] - vfb[k]
u_raw[k] = Kp*e[k] + I[k]
u[k] = clip(u_raw[k], 0.2, 4.0)
I[k+1] = I[k] + T*Ki*e[k]
```

The integral update is held only when it would drive the command further into saturation. Fuel quantities are lbm/s, speed is rpm, and acceleration is rpm/s. Kp is dimensionless and Ki has units 1/s. The 0.03-second derivative filter is an implementation choice held fixed during PI tuning. The existing speed sensor remains in place.

The `Acceleration setpoint` block is an explicit input to the setpoint GP and is zero for all constant-speed disturbance tests. For a varying-speed application, replace it with the acceleration trajectory consistent with the governed speed command. The feedback acceleration comes from the sensed-speed backward difference and causal low-pass filter; logged plant acceleration is used only for validation.

The original speed PI prepares the engine from 10000 rpm to the operating point. Before 30 seconds the new integral tracks `original_PI - Kp*virtual_error`; after that time the fuel-domain PI alone commands fuel. This retains a known startup procedure and makes the transfer approximately bumpless to one sample. Evaluation starts at 60 seconds. There is no additive GPR feedforward term and no residual original speed PI in the active controller output.

Run the complete reproducible tuning and comparison:

```matlab
out = run_tmats_virtual_fuel_study;
s = load(fullfile(out,'selected_gains.mat'));
load_system('GasTurbine_Dyn_Template_VirtualFuel');
[MWS,DOB,PTO,VF] = tmats_virtual_fuel_setup(9500,.2,[.3 1.5 3],s.gains,true);
open_system('GasTurbine_Dyn_Template_VirtualFuel');
```

Load the model before calling setup so its PreLoadFcn cannot overwrite custom setup values. For programmatic simulation use `Simulink.SimulationInput` as demonstrated in the runner, which explicitly sets all experiment variables. Generate the report and plots with `report_tmats_virtual_fuel(out)`.

The search minimizes the mean of four RMSE ratios relative to the original PI, over 9000-rpm 5%, 10%, 20%, and 30% turbine-power ramp disturbances. A candidate must finish all four simulations with finite data, positive fuel and surge margin, flow residual <=1e-9, solver iterations <200, and pre-test speed error <0.1 rpm. The finite grid is a practical tuning search, not proof of an optimal PI or global stability. The selected gains are then frozen for the 9500-rpm tests.

The comparison reproduces the existing ten-case benchmark: four ramp amplitudes at each speed plus 20% and 30% steps at 9500 rpm. Each 90-second evaluation contains three pulses with onset times 10.005, 30, and 60 seconds and removal times 15, 40.005, and 75 seconds. Ramp durations are 0.3, 1.5, and 3 seconds. Load amplitude is the specified fraction of unloaded turbine power at that operating point. Both controllers use identical plant, sensor, reference governor, startup, fuel limits, and load profiles. The original speed PI retains Kp=0.025 and Ki=0.05.

Saved time histories include both virtual fuels, their error, derivative estimate, integral state, raw and limited command, training-range flag, actual speed/fuel, load, and plant-validity signals. The study replays both projections through the exported predictor and verifies command and error equations. Failed simulations are retained but are not assigned full-run performance scores.

Queries are not clipped to the speed training band: clipping at 9000 rpm would erase the restoring speed error during underspeed excursions. Queries outside the training rectangle are logged; these simulations do not validate GP extrapolation generally. The GP was trained with no external shaft load, so virtual fuel feedback is a nominal model coordinate, not a measurement of actual injected fuel under load. Sensor noise, other ambient conditions, startup using this controller alone, and robustness outside the tested cases remain untested.
