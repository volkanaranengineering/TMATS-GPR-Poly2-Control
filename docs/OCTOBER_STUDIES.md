# October studies: chronology and evidence

All results below predate the complete-thesis publication. No new plant simulation was added for the report or repository update.

| Directory | Purpose and interpretation |
|---|---|
| pilco_quadratic_pi_20261010 | Offline GP moment-matching policy search with a frozen quadratic FF; improves RMSE while increasing ringing. |
| pilco_smooth_20261010 | Expected excess-TV penalty, ten weights including refinements, 10% selection and frozen 5% check. |
| pilco_ramp90_100_5s_20261010 | Frozen-controller no-load 9000–10000 rpm, five-second ramp. |
| pilco_ramp90_equal_sensor_20261010 | Explicit common-sensor settings and wiring audit; reruns reproduce prior traces exactly. |
| pilco_combined_cycle_20261010 | Five-second ramp plus 10% common-power load at seconds 10–15; original four controllers. |
| dob98_pi_20261010 | Separate 9800-rpm local identification, causal filtered inverse, 13-case PI tuning, revised comparison, and held-out scenario. |

Each folder is under `study/results/`. JSON records define the protocol and selected policy; CSV files preserve metrics and time histories, and MAT files retain native data. Consult the full thesis for equations and limitations.

The October video builders use the existing recorded trajectories. Their imports may execute analysis or artifact creation; they are not needed to read the PDF or play a saved MP4. Learning scripts and MATLAB batch runners can overwrite fixed study output names, so reproduce in a separate working copy.
