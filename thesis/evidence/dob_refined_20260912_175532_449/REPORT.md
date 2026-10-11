# Disturbance-observer augmentation of the T-MATS PI speed controller

## Scope and source

This study adapts Volkan Aran, *Flexible and Robust Control of Heavy Duty Diesel
Engine Airpath Using Data Driven Disturbance Observers and GPR Models*, PhD
thesis, Sabanci University, 2019, Chapter 4, particularly equations (4.11)-(4.16)
and Chapter 6.1. Public source:
https://research.sabanciuniv.edu/39260/2/10279446_VolkanAran.pdf

The thesis distinguishes nominal linear dynamics from lumped model error,
nonlinearity, and disturbances. It estimates a control-equivalent residual and
filters it before subtractive compensation. Here the outer controller remains
the sample plant's PI (Kp=0.025, Ki=0.05), rather than the thesis's sliding-mode
controller. This is an adaptation and nonlinear simulation study, not a
reproduction of the diesel-engine experiment or a stability proof.

The eight-term frozen ARX from `analyze_two_stage_rls.m` is the starting model.
The standard GPT model is not edited. `GasTurbine_Dyn_Template_GPT_DOB.mdl`
contains ordinary Simulink blocks in its DOB subsystem; the original T-MATS
plant still uses its component S-functions. Online coefficient adaptation is
disabled so that observer/controller interactions can be evaluated first.

## Derivation and the direct-residual comparator

Let q denote a one-sample delay, Ts=0.015 s, u=Wf-u0 in lbm/s,
a=dN/dt in rpm/s, and u0=0.9810869146824126 lbm/s. The identified physical model is

    A(q) a_k = B(q) u_k + epsilon_k,
    A(q) = 1 - 1.8943373173 q + 0.8435460689 q^2
             + 0.0730433076 q^4 - 0.0213582767 q^6,
    B(q) = 361.9406938 q - 497.1376979 q^2
             + 147.9243628 q^5 - 12.7326673 q^10.

The thesis equation (4.13) can be adapted to delayed ARX regressors without
introducing a noncausal inverse. Isolating b1 u_(k-1) gives the equivalent input
residual

    dres_k = [A(q) a_k - B(q) u_k] / b1,
    dhat_res = Qres(q) dres,
    ucmd = sat(uPI - gamma dhat_res).

This is a delayed residual-based comparator, not an exact copy of the thesis's
current-state approximation (4.15). Acceleration is obtained causally from sensed
speed by backward difference in this branch. With autoregressive output terms,
the residual is an equation disturbance. It is not generally the physical fuel
disturbance: for an additive fuel disturbance d, it is B(q)d/b1. In particular,
B(1)/b1 is approximately -1.47e-5, so near-perfect one-step prediction does not
make this residual a useful constant-fuel-disturbance estimate.

## Equilibrium-consistent nominal model and filtered inverse

The raw B polynomial has a zero at 1.00026356, outside the unit circle. Its direct
inverse would be unstable. In addition, B(1)=-0.00530855346 produces the small
spurious nonzero acceleration DC gain identified in the preceding report.

The following is an explicit project-specific modeling constraint, not a formula
claimed from the thesis. Keep A and all other B coefficients fixed and set

    Beq_10 = B_10 - B(1),   hence Beq(1)=0.

This changes the last physical numerator coefficient by +0.00530855346, about
0.0417% of its magnitude. Writing Beq(q)=(1-q) C(q), a backward-integration
approximation gives the nominal speed model

    PN(q) = Ts C(q) / A(q).

Its DC gain is about 335.425 rpm/(lbm/s). This equilibrium constraint removes an
inversion defect but does not establish that the resulting DC gain accurately
matches the nonlinear engine throughout the speed range. Its largest remaining
zero magnitude is approximately 0.952616.

The observer uses the same sensed speed available to the PI. Approximate the
existing 0.05 s sensor with H(q)=(1-p)q/(1-pq), p=exp(-Ts/0.05), and define
Pn=PN H. Use a second-order low-pass with two delays:

    Q(q) = (1-r)^2 q^2 / (1-rq)^2,  r=exp(-2 pi fc Ts),
    dhat = [Q/Pn](Nsensed-9000) - Q(ucmd-u0),
    dtrim = last dhat sample before engagement,
    dc = dhat - dtrim,
    h(t) = clip((t-30)/2, 0, 1),
    ucmd = sat_[0.2,4](uPI - h(t) sat_[-0.15,0.15](gamma dc)).

Final settings are gamma=0.25 and fc=0.5 Hz. The pre-engagement trim is latched
using a Switch and Unit Delay. It removes the initial operating-point bias;
it does not remove model mismatch that changes with operating point.

The two advances in Pn^-1 cancel analytically against the two Q delays. The
resulting Q/Pn is causal and stable. Its implementation uses discrete transfer
function blocks with coefficient lengths padded so they represent polynomials
in q correctly. fc names the pole-frequency parameter, not the cascade's exact
-3 dB frequency. The sensor discretization and acceleration integration are
approximations; nonlinear simulation remains the relevant comparison.

The observer sees saturated commanded fuel before an unknown test disturbance
is added. It does not see the injected disturbance or direct plant acceleration.
Compensation ramps in over two seconds after 30 s preparation. Both controllers use identical
fuel limits and demand conditioning. Saturation activity must be reported;
anti-windup is not added to the unchanged PI in this experiment.

## Experiment and acceptance

The previous unconditioned 9000/10000 rpm PRBS at 0.51 s/bit failed at its first
edge. Therefore this comparison distinguishes raw binary demand from applied
speed demand. A 150 rpm/s governor makes the full-range case a rate-limited PRBS,
not a strict binary plant input. The 60 s evaluation uses a truncated maximal
length sequence, 10.005 s/bit, after 30 s preparation. A separate 9495/9505 rpm
PRBS at 0.51 s/bit tests strict binary demand with the governor effectively
bypassed. The 127-bit recurrence is b(k+7)=xor(b(k),b(k+3)).

Matched positive/negative fuel offsets and a sinusoidal fuel disturbance are
injected after the command limit. Nominal and disturbed runs use paired command
sequences. Tracking RMSE, IAE, peak error and fuel variation are evaluated only
after preparation; numerical validity is checked over the entire simulation.
Every accepted sample requires positive fuel, finite speed/fuel, flow residual
at most 1e-9, fewer than 200 solver iterations, and positive compressor margin.
Results from failed trajectories cannot substantiate control improvement.

## Reproduction

    build_tmats_dob_model;
    outputDirectory = run_tmats_dob_study('refined');
    [MWS,DOB] = tmats_dob_setup;
    open_system('GasTurbine_Dyn_Template_GPT_DOB');

`run_tmats_dob_batch.m` is the isolated batch entry point. Each experiment saves
native MAT data, CSV signals and numerical metrics under `results/dob_*`.
The saved model's default setup reproduces the accepted disturbed full-range
comparison, with the rate-limited demand. `analyze_tmats_dob(outputDirectory)`
regenerates plots and checks; `verify_tmats_dob_saved` rebuilds the model and
checks default replay against the latest case 2. Call
`tmats_dob_setup(struct('gain',0.25,'fc',0.5))` to recompute filter coefficients
when changing settings. Set `DOB.gain=0` after loading for the baseline, or set
`DOB.disturbance(:,2)=0` for the nominal case. A changed fc requires recomputing
the coefficients, not merely editing the scalar field after setup.

## Results: accepted final configuration

The final results are in `results/dob_refined_20260912_175532_449`.
All first seven cases passed the numerical acceptance checks for the entire
90 s simulation, including preparation. Maximum inner iterations were 20;
all residuals stayed below 1e-9. Fuel remained positive and all operating
comparisons stayed clear of the shared fuel limits. The minimum compressor
margin was 14.9054% in the full-range pair. No solver tolerances were relaxed.

| Experiment / measure | Existing PI | PI + DOB | Improvement |
| --- | ---: | ---: | ---: |
| Rate-limited 9000-10000 rpm, disturbed: tracking RMSE (rpm) | 1.42705 | 1.20710 | 15.41% |
| Same test: IAE (rpm s) | 54.0001 | 43.4278 | 19.58% |
| Same test: peak tracking error (rpm) | 8.12493 | 7.21189 | 11.24% |
| Rate-limited nominal: tracking RMSE (rpm) | 1.32431 | 1.08438 | 18.12% |
| Strict 9495/9505 rpm PRBS, disturbed: RMSE (rpm) | 2.29021 | 2.26952 | 0.90% |
| Paired disturbance-induced speed RMS (rpm) | 0.63657 | 0.60068 | 5.64% |
| Paired disturbance-induced peak (rpm) | 4.20270 | 4.17338 | 0.70% |

The paired rejection measure uses

    deltaN_PI  = N_PI,disturbed  - N_PI,nominal,
    deltaN_DOB = N_DOB,disturbed - N_DOB,nominal,

on identical 60 s demand histories. This removes nominal tracking behavior
from the comparison, though nonlinear interactions still remain. The 15.41%
tracking improvement must not be described as a 15.41% disturbance-rejection
improvement: the latter is only 5.64% by this paired RMS measure.

The full-range disturbance sequence is +0.08 lbm/s over 7.5-15 s, -0.08 lbm/s
over 20-27.5 s, and a 0.06 lbm/s, 0.2 Hz sine over 35-50 s. The clock here
starts after preparation. Injection is downstream of the known command.
These tests cover matched additive actuator/fuel disturbances, not independent
shaft-load, thermal, ambient, or sensor disturbances.

The original ARX equation-residual comparator gives 1.42594 rpm RMSE versus
1.42705 rpm for PI: only about 0.077% improvement. This confirms that simply
feeding back the small ARX prediction innovation does not yield a strong input
disturbance observer for this model.

### What the result establishes and what it does not

1. **Useful bounded augmentation.** The existing PI gains were preserved. All
   accepted final comparisons improved tracking, although the strict small PRBS
   improvement is modest. Known-command total variation changed from 12.2658
   to 12.2716 lbm/s in the disturbed full-range test, about +0.047%; this is a
   sampled variation measure, not an actuator wear or fuel-economy measurement.
2. **Model mismatch dominates the broad-range estimate.** The raw lumped estimate
   approaches roughly 1 lbm/s during high-speed operation, far larger than the
   injected 0.08 lbm/s offset. The correction reaches its 0.15 lbm/s limit for
   about 50.44% of the full-range disturbed evaluation. It must not be interpreted
   as a calibrated estimate of physical fuel error. Around the fixed 9500 rpm
   operating point, the trim-removed estimate follows the injected offset much
   more closely, and compensation does not reach its limit.
3. **A governor is essential in the full-range example.** Raw PRBS tracking RMSE
   is 383.611 rpm for PI and 383.789 rpm for PI+DOB, because the applied demand
   is intentionally limited to 150 rpm/s. The small applied-demand error does
   not mean that instantaneous 1000 rpm steps are tracked. In new unconditioned
   0.51 s/bit tests, both controllers first fail flow convergence at 0.525 s,
   one sample after the first edge. Those three-second records are diagnostic
   only. Their complete-trajectory error scores in the machine-readable table
   must not be used to rank controllers.
4. **Bounded correction matters.** The initial gamma=0.5 design improved the
   disturbed full-range case more, but its nominal pair failed at 40.755 s and
   the strict small case worsened before trim compensation was added. Those
   settings were rejected. The final gamma=0.25 setting passed the intended
   tests. Refinement used these evaluation cases; they are comparative design
   experiments, not an untouched statistical validation set.
5. **No general robustness or deployment claim.** The tests are deterministic,
   noise-free sample-engine simulations. They do not establish closed-loop
   robustness over an operating envelope, sensor-noise tolerance, load rejection,
   fixed-point suitability, or worst-case embedded execution time. The model
   computes both observer branches for comparison; a deployed implementation
   should retain only the chosen branch after validation.

## Numerical and implementation verification

The analytical Q/Pn and block coefficients agree to 1.22e-14 over 1001 points
from DC to Nyquist. Maximum inverse pole magnitude is 0.953969. This checks
the filter realization, not stability of the uncertain nonlinear closed loop.
The DOB contains 32 ordinary blocks, zero S-functions and zero MATLAB Function
blocks. The new top-level speed scope displays applied demand and sensed speed.
Default-model replay after layout changes agrees with accepted case 2 to
4.92e-11 rpm and 5.11e-15 lbm/s.

The reference GPT model SHA-256 remains
`99D95A3F42A12DD42EE5C4353B8D3AE6DB2A54F7AC15A106FC72D0EEBBB31376`.

### Result files

| File in final result directory | Contents |
| --- | --- |
| `case_01` / `case_02` MAT and CSV | Disturbed full-range, PI / PI+DOB |
| `case_03` / `case_04` | Nominal full-range, PI / PI+DOB |
| `case_05` / `case_06` | Strict small PRBS, PI / PI+DOB |
| `case_07` | Delayed thesis-style ARX residual comparator |
| `case_08` / `case_09` | Failed strict full-range diagnostic trajectories |
| `metrics.csv`, `metrics.json` | Tracking, limits, fuel and validity measures |
| `verification.json`, `default_replay.json` | Mathematical/block checks and replay |
| `comparison_1.png` to `comparison_3.png` | Speed, error, fuel and observer histories |
| `disturbance_rejection.png` | Paired disturbance-induced speed comparison |
| `dob_blocks.png` | Actual basic-block observer implementation |

## Recommended next development

First fit equilibrium-consistent local fuel-to-speed models, with measured
operating-point gains, rather than relying on a small post-fit coefficient
adjustment in an acceleration ARX model. Preserve a new untouched PRBS/load
record for assessment. Then test causal sensing with noise, shaft-load and
ambient disturbances, filter/compensation bandwidth sensitivity, and observer
disable/fallback behavior. Add PI anti-windup before broadening the operating
range into fuel saturation. Only after these checks should fixed-point or
single-precision code generation and target timing be assessed. Online RLS
updates should remain disabled until pole/zero acceptance, bumpless transfer,
and closed-loop robustness checks are in place.
