# Frozen R3 versus base PI: speed and ambient cycle

Open `GasTurbine_Cycle_R3.mdl` or `GasTurbine_Cycle_BasePI.mdl` from the existing TMATSGPT workspace. Both use `tmats_r3_cycle_setup.m` as preload callback. They depend on the existing T-MATS installation and the frozen R3/environment-GPR files from the preceding study.

The simulation lasts 180 s: 60 s preparation followed by the requested 120 s test. Test time is simulation time minus 60 s.

Each of four 30 s cycles is: 9025 to 9975 rpm in 5 s, high hold for 10 s, return to 9025 rpm in 5 s, low hold for 10 s. These limits interpret the earlier 9500 rpm and 5% context as +/-5%. Ambient altitude and ISA departure interpolate linearly through `(0 s, 0 m, -20 C)`, `(60 s, 10000 m, +20 C)`, `(120 s, 0 m, 0 C)`. The actual inlet temperature and pressure are computed by the existing atmosphere and supplied to the GP. Mach is zero.

Base PI gains remain Kp=0.025, Ki=0.05. R3 remains Kp=0.025, Ki=0.1, Kd=0.002, with acceleration filter 0.03 s, sample time 0.015 s, and its existing fallback guards. No desired-acceleration feedforward is added; its setpoint inverse query still uses zero acceleration. The common request governor is set to 200 rpm/s because its inherited 150 rpm/s limit would stretch the requested 190 rpm/s ramps. The logged governed request is verified against the input profile.

Earlier shaft-power pulses and additive fuel disturbances are disabled. No new sensor noise or actuator lag is introduced. Original controller models and gains are preserved.

```matlab
tmats_r3_cycle_setup;
open_system('GasTurbine_Cycle_R3');
sim('GasTurbine_Cycle_R3');

out='results/r3_ambient_cycle_20260915';
run_tmats_r3_cycle(out);
report_tmats_r3_cycle(out);
```

`summary.csv` contains full/ramp/hold RMSE, peak error, integral absolute error, fuel reversal metrics, hold recovery to the 1% speed window, and validity/map diagnostics. The two segment CSVs give all sixteen ramp/hold intervals. `BasePI.mat` and `R3.mat` contain the complete traces and configuration.

Both final runs pass numerical acceptance. Base PI / R3 full RMSE is 3.66889 / 6.13779 rpm; segment excess fuel TV is 6.75506 / 4.24234 lbm/s. R3 therefore has 67.3% higher actual-speed RMSE and 37.2% lower fuel reversal metric on this test. Both remain within the 1% hold-speed window throughout. R3 uses fallback for 78.69% of samples and queries outside the training input range throughout; approximately 19.8% of each trajectory exceeds the monitored compressor map speed range. The PDF discusses these limitations and sensor delay during ramps.

Ringing is evaluated as excess fuel total variation separately within each ramp and hold, then summed. Hold-only excess variation is also reported. Because the ambient conditions keep moving, commanded fuel reversals need not all represent oscillation. This metric differs from the earlier two-second shaft-load disturbance windows. Recovery is timed from each hold start until speed remains within 1% of that hold's request through its end.

Run `verify_tmats_r3_cycle.py` to independently verify the request profile, core metrics, R3 command algebra and conditional integration. `build_tmats_r3_cycle_report.py` generates native LaTeX from the saved results; compile twice with pdflatex. The source/results archive is an overlay for this existing workspace, not a standalone T-MATS installation.

Files containing `request_diagnostic` record the preliminary run with the inherited 150 rpm/s request limit. They are excluded from the final comparison and deliverable archive.
