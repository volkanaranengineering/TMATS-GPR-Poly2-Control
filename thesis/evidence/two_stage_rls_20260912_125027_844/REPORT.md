# Offline two-stage RLS results

Stage 1 used reorthogonalized forward selection over 20 candidates (output/fuel delays 1–10), with relative residual-energy threshold 1e-06. Stage 2 used RLS with lambda 0.9990 and P0 10000. The smallest stable candidate within 0.010 normalized MSE of the best selection score was chosen. No final-validation outputs entered support selection.

Selected **8 terms**: output delays **[1 2 4 6]**, fuel delays **[1 2 5 10]** (samples; multiply by 15 ms). Candidate path contains 9 admissible models.

| Evaluation | Selected fit | Previous ten-term fit |
|---|---:|---:|
| Chirp one-step | 99.8720% | 99.8729% |
| Chirp frozen free-run | 87.3880% | 88.3707% |
| Ramp final validation free-run | 65.2666% | 62.6191% |

Selected training one-step RMSE: 0.710104 rpm/s; training free-run RMSE: 69.956083 rpm/s. Final validation RMSE: 28.349800 rpm/s versus previous 30.510694 rpm/s. Selection-ramp fit: 66.8846%.

Selected design-matrix condition number 15571.7 versus previous 1.01674e+06. Final maximum pole magnitude 0.97774209. Stage-2 covariance has 64 entries versus 100; this is theoretical storage/work reduction, not a measured whole-system speedup. The 20-candidate selection stage and longer lag buffer add overhead during learning.

Validation fit changes by +2.6475 percentage points, with 7.08% lower validation RMSE. Covariance storage decreases by 36% and conditioning improves by a factor of 65.29. Training free-run fit changes by -0.9827 percentage points. The result is a modest generalization improvement with a smaller, better-conditioned model, not a uniformly more accurate model.

The selected sample delays correspond to output delays `[15 30 60 90]` ms and fuel delays `[15 30 75 150]` ms. Stage 1 stopped before ten terms because remaining candidates failed the declared redundancy test. Candidate-path CSV retains rejected unstable candidates; the plot shows stable candidates only.

## Reproduction and verification

Run `results = analyze_two_stage_rls;` in this project, or pass this folder's `offline_inputs.mat` as an argument. The function does not exit MATLAB or launch Simulink. Raw data are reused offline. Offline saved chirp and separate selection/validation ramps; selection Ndot reconstructed by verified shaft power law.

Selection acceleration uses Ndot = 60/(2*pi*30) * 5252.113 * (compressor_power/N + turbine_power/N), using signed power in hp, N in rpm and zero external load. This was checked against both chirp and validation direct Ndot logs; maximum difference 5.59e-10 rpm/s.

Weighted augmented QR and RLS coefficients agree to relative error 1.58e-11; MATLAB recursiveLS agreement 1.57e-11. Covariance minimum eigenvalue 0.000147. The repeated baseline prior predictions match previous logs within 2.55e-08 rpm/s.

## Interpretation and limits

Only the valid chirp prefix 0–17.790 s (1187 samples) was used. Reference failure begins at 17.805 s; no failed samples enter the dictionary. Because the support is chosen using the full prefix, its replay one-step fit is an offline training measure, not a fully causal online structure-selection result. Weights still predict before each current-sample update.

The final coefficients were frozen for the 60 s validation ramp, using zero normalized filter states after equilibrium preparation. Greedy forward selection is not an exhaustive search. The predetermined redundancy threshold can exclude useful correlated dynamic terms; this run does not tune it against final validation. Sparse linear structure cannot by itself guarantee correct equilibrium or nonlinear behavior.

A(z^-1), including zero coefficients at skipped lags: `[1 -1.8943373173 0.84354606889 0 0.0730433076284 0 -0.0213582767346 0 0 0 0]`.

B normalized: `[0 0.361940693762 -0.497137697864 0 0 0.147924362846 0 0 0 0 -0.0127326672965]`.

Fuel offset 0.9810869146824126 lbm/s; acceleration scale 1000 rpm/s. Coefficient ordering follows selected dictionary indices `[11 1 2 4 12 15 20 6]`.

The polynomial convention is `A(z^-1)*y = B(z^-1)*u + e`, where `y=Ndot/1000` and `u=Wf-Wf0` in the stated units. Missing lags have exactly zero coefficients. The final lag set is frozen for this offline experiment; online support switching was not simulated.

Files include the candidate path, full input data, weight/covariance evolution, comparison tables, coefficients, MAT results and plot. For the mathematical proposal and literature see `TWO_STAGE_RLS_PROPOSAL.md` in the project.
