# Basic-block RLS gas-turbine model

`GasTurbine_Dyn_Template_GPT_RLS_Blocks.mdl` implements the fuel-flow to shaft-acceleration ARX(5,5,1) observer with ordinary Simulink blocks. The observer contains no S-function, MATLAB Function, MATLAB System, or interpreted-expression Fcn block. The reference T-MATS engine still uses its original component S-functions.

From the existing TMATSGPT working directory:

```matlab
tmats_rls_setup;
open_system('GasTurbine_Dyn_Template_GPT_RLS_Blocks');
```

Press Run and open `Acceleration Reference vs RLS`. Double-click the green `RLS Acceleration Observer` subsystem to inspect the implementation. `tmats_rls_setup.m` is initialization code only; the estimator executes entirely as a Simulink block diagram.

The three areas of the observer are:

- **History and states:** Zero-Order Hold samples plant signals at 0.015 s. Ten scalar Unit Delay blocks store five past normalized accelerations and five past fuel deviations. Additional Unit Delays store the ten coefficients, 10-by-10 covariance, fuel offset, update count and fault latch.
- **RLS matrix arithmetic:** Product blocks perform matrix multiplication. Math Function blocks transpose matrices; Gain, Sum and Product blocks calculate the pre-update prediction, RLS gain, coefficient correction, Joseph covariance update and symmetrization. This subsystem contains no embedded code.
- **Validity and update gate:** comparison and logic blocks check finite signals, inner solver residuals/iterations, fuel, stability margin, preparation time and regressor energy. Switches accept or reject state updates. A reference failure freezes all estimator states and masks predictions with NaN until the next simulation reset.

The model uses five output-history and five input-history coefficients, one-sample input delay, lambda=0.999, P0=10000*I and zero initial coefficients. Acceleration is divided by 1000; fuel is centered on its measured preparation equilibrium. Unit Delays ensure the published prediction uses coefficients from the preceding update.

The default experiment is unchanged: 30 s preparation followed by a 60 s 9000–10000 rpm demand chirp sweeping 0.1–1 Hz. Actual controller fuel flow is the identification input and direct plant Ndot is the reference output. The prior study's plant validity limitation still applies unless a new run establishes otherwise.

For complete command-line reproduction, `build_tmats_rls_blocks_batch` builds and runs the chirp plus independent ramp/hold validation. `analyze_tmats_rls_blocks_batch` performs numerical checks, compares against the earlier S-function implementation, exports block inventory/diagrams, and reports one-step and free-run fits. Both batch scripts exit MATLAB on completion. To rerun without rebuilding, use `run_tmats_rls_blocks_batch`.

The builder uses the previous `GasTurbine_Dyn_Template_GPT_RLS.mdl` as a template, replaces its entire observer, and restores the top-level wiring. Existing block-model files are backed up before rebuilding. The original GPT and earlier RLS model are preserved. A completed block model does not need `tmats_rls_arx_sfun.m` or `tmats_rls_step.m` to simulate; the latter is used only by the independent analysis checks.

These files expect the existing adjacent T-MATS library/standard-example installation. Batch analysis also uses the earlier chirp results and ramp-profile pointer for comparison. Results are stored under `results/rls_blocks_acceleration_<timestamp>`; `tmp/rls_blocks_directory.txt` points to the latest run.
