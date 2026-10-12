# PRBS validation experiment - FAILED - DIAGNOSTIC OUTPUT ONLY

## Specification

- Binary shaft-speed demand: 9000 or 10000 rpm, starting at 9000 rpm.
- Duration: 60 s, 4001 samples including endpoints, Ts=0.015 s (66.6667 Hz).
- Bit duration: 0.51 s = 34 samples; adjacent equal bits produce longer holds.
- 7-bit maximum-length recurrence: b(k+7)=xor(b(k),b(k+3)).
- Initial bits: [0 1 0 1 1 0 1]; verified period: 127 bits = 64.77 s.
- The 60-second window is a truncated period. It has 59 level changes.
- Zero-order-hold application; exact agreement of all logged command samples
  with the independently regenerated sequence was checked.
- Sea-level altitude, original PI controller and unchanged GPT model.
- 30 s of preparation precede the exported window: initially 10000 rpm,
  small sample-held decrements during 5-10 s, then 9000 rpm until 30 s.
  The full preparation response is preserved in full_run_with_preparation.mat.

This is a separate PRBS experiment from the earlier chirp. It is not a frequency
sweep and is not band-limited to 0.1-1 Hz. Actual shaft speed is the plant response,
not a guaranteed binary 9000/10000 rpm signal.

## Acceptance

Status: FAILED - DIAGNOSTIC OUTPUT ONLY

First failed sample: 0.51 seconds into the PRBS.
Consecutive samples before first failure: 34.
Maximum normalized flow residual: 0.992188; tolerance: 1e-9.
Maximum iteration count: 200 (limit 200).
Negative-fuel samples: 0.
Fuel-flow range: 0.981087 to 826.302 lbm/s.

DO NOT use this full simulated response for model validation. Later sample-level
checks cannot validate states propagated through a failed solver. No excitation
amplitude, PI gain, fuel limit, plant parameter or map was changed to force a pass.
The PRBS command itself is reproducible and may be reused after resolving model
and controller limitations. A filtered or slew-limited command would be a different
experiment and must be identified as such.

## Contents

- prbs_command.csv: reference time, speed command, binary bit and bit index.
- all_signals.csv: all model outputs plus PRBS and validity diagnostics.
- diagnostic_signals.csv (or validation_signals.csv if checks pass): compact
  selection of speed, fuel, thrust, temperatures, pressure and stability margin.
- prbs_data.mat: MATLAB data tables, summary, command and scenario.
- full_run_with_preparation.mat: native Simulink outputs, complete MWS parameters,
  metadata and full 90-second run.
- scenario.mat: requested PRBS and preparation profiles, seed and bit sequence.
- summary.json: machine-readable status and checks.
- prbs_overview.png: response and flow residual plot with acceptance status.
- simulation.log: MATLAB diagnostics.
- scenario_script.m, run_tmats_gpt.m, tmats_gpt_setup.m: reproduction scripts.
  Place these in the original project folder (scenario_script.m can be run there);
  the adjacent T-MATS installation and copied model are required.

Units: time s; speed rpm; Wf lbm/s; Fnet lbf; s3/s4/s5_Tt absolute Rankine;
s3_Pt psia; C_Data_SMavail percent; normalized flow residuals dimensionless.
sample_checks_pass marks pointwise numerical checks; before_first_failure is false
from the first failed sample onward. Case-level status controls dataset acceptance.
