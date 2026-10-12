# Chirp simulation: diagnostic data, validation FAILED

The requested 60-second speed-demand chirp was simulated using the unchanged
GasTurbine_Dyn_Template_GPT plant and PI controller in MATLAB R2018b.
The command oscillates between 9000 and 10000 rpm; its frequency rises linearly
from 0.1 to 1 Hz. It starts and ends at 9000 rpm (33 cycles):

N_request(t) = 9500 - 500*cos(2*pi*(0.1*t + 0.0075*t^2)), 0 <= t <= 60 s.

Sampling is 0.015 s (66.6667 Hz), with 4001 rows including both endpoints.
Altitude is zero. Thirty seconds of preparation precede the exported chirp:
hold 10000 rpm to 5 s, ramp to 9000 rpm by 10 s, hold to 30 s.
Exported time starts at zero at the beginning of the chirp. Sources interpolate
linearly between the sampled command points. Initial actual speed is near 9000 rpm.

## Validation result

DO NOT USE THE FULL OUTPUT AS AN ACCEPTED SYSTEM-IDENTIFICATION DATASET.

- First failed sample: 17.805 s, at a requested instantaneous frequency of
  0.367075 Hz. The iterative solver reaches its 200-iteration limit.
- 1187 of 4001 samples pass the recorded numerical checks, through 17.790 s.
  These checks do not establish full physical validity.
- First negative fuel flow: 29.955 s. There are 447 negative-fuel samples.
- Maximum absolute normalized flow residual: approximately 1.3334e11,
  versus a 1e-9 tolerance.
- The log contains component-map warnings and a singular-Jacobian message.
  A plausible-looking speed trace after the first failure is not reliable.

The requested amplitude and frequency were not reduced, and no controller,
fuel limits, maps, solver settings or model physics were changed to force a pass.
Generating a valid full-duration response requires investigating the solver/map
limits and controller behavior, or changing the excitation specification.

## Files and columns

- requested_command.csv: exact sampled reference and instantaneous frequency.
- diagnostic_signals.csv: time, demand, actual and sensed speed, fuel, net thrust,
  station temperatures/pressure, compressor stability margin and validity flags.
- chirp_data.csv: all recorded signals and diagnostics, excluding preparation.
- chirp_data.mat: MATLAB tables, scenario and summary; all_samples_valid is false.
- scenario.mat: full input profile including preparation.
- summary.json: machine-readable validation status and failure times.
- chirp_overview.png: response plot; data after 17.805 s are invalid.
- simulation.log: complete MATLAB run log.
- scenario_script.m: scenario recipe; requires run_tmats_gpt.m and tmats_gpt_setup.m
  in the original project folder, with the adjacent T-MATS installation.

Units: time seconds; N_request/Nmech/N_sensed rpm; Wf lbm/s; Fnet lbf;
s3_Tt/s4_Tt/s5_Tt absolute Rankine; s3_Pt psia;
C_Data_SMavail percent. flow_converged tests the residual/iteration checks;
valid_sample additionally checks finite exported values and nonnegative fuel.
The case-level acceptance flag is all_samples_valid=false.
