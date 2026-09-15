Environment-aware exact inverse GPR study

Grid: 0, 2500, 5000, 7500, 10000 m crossed with ISA departures 0, -10, +10, +20, -20, +30, -30 C.
Target: 4000 m, ISA+5, 9500 rpm, 10% shaft-power extraction pulses.
Exact GP: 1400 training points, 200 held-out points; inputs speed rpm, acceleration rpm/s, inlet total temperature K, inlet total pressure kPa; output fuel lbm/s.
PI gains: virtual fuel [2 30]; base speed PI [.025 .05]. No gain scheduling or test-based retuning.

200-point validation represents 33 environmental conditions. The 10000 m ISA and ISA+10 identification trajectories have no valid held-out-window rows; these failures are preserved. The frozen GP is not refitted in response to validation results.
The original compressor map clamps out-of-range coordinates. 396 training and 52 test observations exceed its corrected-speed range; these are simulator-model results, not validated physical extrapolation.
All 73 controller comparison runs passed numerical/surge/trim acceptance. Ten of the 35 grid conditions per controller are compressor-speed-map flagged. The inverse controller failed 1% speed-band recovery in the 5000 m ISA-30 case, despite numerical acceptance.

Key files:
  environment_inverse_gpr_model.mat: full model plus MATLAB exact RegressionGP object.
  training_points.csv and test_200_points.csv: frozen split and posterior results.
  comparison_summary.csv: all 73 comparison scores.
  target_events.csv: six load-edge metrics for three target methods.
  target_gp_local.csv: posterior mean/SD and local slopes at target.
  source/: study source snapshot and dedicated Simulink model.

Reproduction in the originating workspace, MATLAB R2018b with T-MATS and Statistics Toolbox:
  out = strtrim(fileread('tmp/environment_directory.txt'));
  run_tmats_environment_data(out,1:35);
  fit_tmats_environment_gpr(out);
  run_tmats_environment_comparison(out,1:36);
  report_tmats_environment_study(out);
  plot_tmats_environment_worst(out);
Existing trajectory files and the frozen model are reused. For a fresh experiment, use a NEW output directory; do not delete prior records.
To open the target controller: tmats_environment_controller_setup; open_system('GasTurbine_Dyn_EnvironmentGPR');
Source setup locates this study through tmp/environment_directory.txt. Preserve that pointer when moving files.
Build PDF: run build_tmats_environment_report.py, then pdflatex twice in tmp/pdfs/environment_controller_tutorial.
