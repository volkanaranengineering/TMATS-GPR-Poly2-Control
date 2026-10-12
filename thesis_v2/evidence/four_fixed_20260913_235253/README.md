# Fixed low-ringing controller and four-method comparison

Selected virtual-fuel gains: Kp=2, Ki=30 1/s. Tuning condition: 9500 rpm, 5% shaft-load steps. Ringing was reduced 90.35% versus the earlier fixed Kp=3, Ki=60 pair; speed RMSE increased from 0.711646 to 0.930388 rpm.

Open GasTurbine_Dyn_Template_LowRinging.mdl, or run tmats_lowring_setup and simulate that model. The existing controller models remain separate. Both inverse-GPR variants in the final comparison use the selected pair; base speed PI uses Kp=0.025, Ki=0.05. The base PI + FF branch retains the earlier bounded, trimmed, sensed-speed GP correction.

All 44 final runs are fresh. All four methods pass 9 of 11 cases; 9500 rpm 30% ramps and 30% steps fail. Invalid full-run metrics are withheld. Every valid run stays within the requested +/-1% commanded-speed band, so broad-band recovery is zero. The +/-0.1 rpm recovery column differentiates settling.

Files: summary.csv (all methods), inverse_pair_equivalence.csv (same-gain feedforward check), raw per-case CSV/MAT trajectories, and vector PDF/PNG plots. See output/pdf/TMATS_Controller_Tutorial.pdf for full equations, interpretation, tables and zoomed results; the source archive accompanies it.
