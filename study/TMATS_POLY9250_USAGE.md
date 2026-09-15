# Poly2 PID retuned at 9250 rpm, 0 m, ISA 0

Selected gains: Kp=0.025, Ki=0.14, Kd=0.00125.
Original gains: Kp=0.025, Ki=0.1, Kd=0.002.

Only the PID coefficients change. The frozen quadratic inverse, static
setpoint feedforward p2(r,0,T,P), slope normalization, fallback, acceleration
filter, limits, anti-windup and startup tracking are preserved. Kd acts on
normalized filtered acceleration, with the existing negative feedback sign.

The fixed-speed test uses 10% shaft-power load pulses, 60 seconds preparation
and 90 seconds evaluation. A 28-candidate coarse search followed by six
coordinate refinements minimizes max(RMSE/original RMSE, ringing/original
ringing). Candidate 34 is the best tested, not a global optimum.
The selected gains are frozen before a separate 5% load-amplitude check.

9250 rpm is 14.23 rpm below the original training-speed minimum. These are
local simulation tuning results with slight model extrapolation, not proof
of performance across the original altitude/speed envelope.

In the existing T-MATS workspace:

```matlab
open_system('GasTurbine_Poly2_9250_Tuned');
tmats_poly9250_tuned_setup;
sim('GasTurbine_Poly2_9250_Tuned');
```

The model preload callback loads selected.mat through
tmats_poly9250_tuned_setup.m. Original model defaults are preserved.
To reproduce a fresh search, use a new results directory:

```matlab
out='results/poly9250_repeat';
run_tmats_poly9250(out,'coarse');
run_tmats_poly9250(out,'refine'); % exactly one refinement round
select_tmats_poly9250(out);
validate_tmats_poly9250(out);
report_tmats_poly9250(out);
```

The delivered tuned setup points to results/poly2_tune9250_20260915.
If selecting a fresh output directory for deployment, update that path in
tmats_poly9250_tuned_setup.m. The search resumes existing candidate files;
use a new directory for a clean rerun. Additional refine calls add another
round and are not part of the delivered search protocol.

All candidate and validation MAT/CSV traces, gains, metrics and independent
replay checks are included. verify_tmats_poly9250.py recomputes metrics and
replays controller commands/integrator updates from accepted tuning traces.
build_tmats_poly9250_report.py creates native LaTeX and requires the report
figures, validation and verification outputs. The LaTeX ZIP is separately
rebuildable using pdflatex (two passes).

The Models_Results archive is an overlay for the existing T-MATS and frozen
model workspace; it is not a standalone engine installation. SHA256_manifest
records every packaged source/data file. Previously delivered studies remain
unchanged.
