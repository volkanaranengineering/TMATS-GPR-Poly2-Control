> Updated with GPR_FF: the historical five-method analysis below is retained. The current six-method table is in the GPR_FF extension at the end.

# Five-controller comparison at 9000 and 9500 rpm

The verified 9000 rpm runs are reused; five new 9500 rpm runs repeat the same 10% ramped shaft-load scenario. The load is recalculated at each speed: 0.879124 MW at 9000 rpm and 1.428820 MW at 9500 rpm. The latter is 62.528% larger in absolute power. Controller gains, observer poles, model coefficients, limits and ramp timings are unchanged. This is an operating-point and relative-load comparison, not a same-absolute-power test.

| Speed | Method | Valid | RMSE rpm | Peak error rpm | IAE rpm s |
|---:|---|---|---:|---:|---:|
| 9000 | PI | True | 1.193 | 10.677 | 36.774 |
| 9000 | DOB | True | 1.038 | 10.351 | 28.341 |
| 9000 | LESO | True | 1.039 | 10.349 | 28.694 |
| 9000 | UDE | True | 0.969 | 9.377 | 27.587 |
| 9000 | GPIO | True | 0.951 | 9.866 | 27.577 |
| 9500 | PI | True | 2.125 | 18.642 | 65.863 |
| 9500 | DOB | True | 1.850 | 18.147 | 50.799 |
| 9500 | LESO | True | 1.853 | 18.155 | 51.429 |
| 9500 | UDE | True | 1.730 | 16.574 | 49.411 |
| 9500 | GPIO | True | 1.698 | 17.393 | 49.392 |

## Recovery after ramp completion

| Ramp s | Method | Apply 9000 | Apply 9500 | Remove 9000 | Remove 9500 |
|---:|---|---:|---:|---:|---:|
| 0.30 | PI | 1.050 | 1.350 | 1.080 | 1.365 |
| 0.30 | DOB | 0.705 | 0.855 | 0.735 | 0.870 |
| 0.30 | LESO | 0.720 | 0.885 | 0.750 | 0.900 |
| 0.30 | UDE | 0.780 | 0.990 | 0.795 | 1.005 |
| 0.30 | GPIO | 0.615 | 0.990 | 0.630 | 0.870 |
| 1.50 | PI | 0.630 | 0.945 | 0.645 | 0.930 |
| 1.50 | DOB | 0.345 | 0.540 | 0.360 | 0.525 |
| 1.50 | LESO | 0.345 | 0.555 | 0.375 | 0.540 |
| 1.50 | UDE | 0.420 | 0.630 | 0.420 | 0.615 |
| 1.50 | GPIO | 0.285 | 0.645 | 0.300 | 0.570 |
| 3.00 | PI | 0.315 | 0.645 | 0.315 | 0.600 |
| 3.00 | DOB | 0.165 | 0.330 | 0.150 | 0.285 |
| 3.00 | LESO | 0.165 | 0.330 | 0.150 | 0.285 |
| 3.00 | UDE | 0.165 | 0.390 | 0.150 | 0.360 |
| 3.00 | GPIO | 0.150 | 0.330 | 0.150 | 0.315 |

## Recovery from ramp start

| Ramp s | Method | Apply 9000 | Apply 9500 | Remove 9000 | Remove 9500 |
|---:|---|---:|---:|---:|---:|
| 0.30 | PI | 1.350 | 1.650 | 1.380 | 1.665 |
| 0.30 | DOB | 1.005 | 1.155 | 1.035 | 1.170 |
| 0.30 | LESO | 1.020 | 1.185 | 1.050 | 1.200 |
| 0.30 | UDE | 1.080 | 1.290 | 1.095 | 1.305 |
| 0.30 | GPIO | 0.915 | 1.290 | 0.930 | 1.170 |
| 1.50 | PI | 2.130 | 2.445 | 2.145 | 2.430 |
| 1.50 | DOB | 1.845 | 2.040 | 1.860 | 2.025 |
| 1.50 | LESO | 1.845 | 2.055 | 1.875 | 2.040 |
| 1.50 | UDE | 1.920 | 2.130 | 1.920 | 2.115 |
| 1.50 | GPIO | 1.785 | 2.145 | 1.800 | 2.070 |
| 3.00 | PI | 3.315 | 3.645 | 3.315 | 3.600 |
| 3.00 | DOB | 3.165 | 3.330 | 3.150 | 3.285 |
| 3.00 | LESO | 3.165 | 3.330 | 3.150 | 3.285 |
| 3.00 | UDE | 3.165 | 3.390 | 3.150 | 3.360 |
| 3.00 | GPIO | 3.150 | 3.330 | 3.150 | 3.315 |

Times are in seconds. Recovery is the first sample after the last excursion outside +/-1 rpm, confirmed by at least 0.5 s dwell until the next ramp. After-ramp recovery subtracts ramp duration and is bounded below by zero. Sampling resolution is 15 ms.

## Findings

At 9000 rpm, GPIO has the lowest RMSE (0.9509 rpm; 20.30% below PI), while UDE has the smallest peak error (9.3768 rpm).
At 9500 rpm, GPIO has the lowest RMSE (1.6979 rpm; 20.10% below PI), while UDE has the smallest peak error (16.5737 rpm).

The recovery ranking changes at 9500 rpm. For the 0.30 s application ramp, DOB recovers in 0.855 s after completion versus 0.990 s for GPIO; at 9000 rpm GPIO was faster (0.615 versus 0.705 s). DOB has the fastest or joint-fastest recovery in all six 9500 rpm events. GPIO still has the lowest full-test RMSE, illustrating that average error and threshold recovery are different objectives. At 9500 rpm GPIO compensation clips for 2.133% of the evaluation; other methods do not clip. No fuel limit is reached. This clipping may contribute to the recovery change, but its causal effect has not been isolated.

Equal pole-frequency parameters do not imply equal estimator bandwidth. The alternatives use a one-step input-gain approximation; the existing DOB retains its fuller nominal model. The fixed offsets remain 9000 rpm and 0.981086915 lbm/s internally, with the same pre-engagement trim latch handling the 9500 rpm equilibrium offset. No coefficients are refitted at 9500 rpm.

These deterministic results do not establish noise robustness or an embedded safety envelope. Differences of one sample in recovery should not be treated as decisive. A larger absolute load and operating-point change prevent attributing speed-to-speed differences solely to observer quality.

## Figures

### 9000 rpm

![General responses](overview_9000.png)

![Rejection zooms](zooms_9000.png)

### 9500 rpm

![General responses](overview_9500.png)

![Rejection zooms](zooms_9500.png)

## Reproduction and validity

Run `run_tmats_literature_comparison(9500)` for new 9500 rpm results, then `compare_observers_two_speeds.py`. The 9000 rpm source is frozen from the prior comparison. Setup accepts `tmats_literature_setup(method,0.5,9500)` after loading the model. The runner checks unloaded trim speed and turbine power against the speed-specific cached reference. Every trajectory contains 10001 samples through 150 s. Identical mechanical profiles, torque balance, and independent low-order observer replay are verified. Validity requires finite signals, positive fuel and compressor margin, flow residual <=1e-9 and fewer than 200 solver iterations. Plots stop at the first invalid solve and complete-run metrics are withheld if any solve is invalid.




7. Parameter provenance: what was fixed and why



The numerical settings below define this experiment. They are not claimed to be optimal or prescribed by a paper. Measured operating-point quantities are separated from inherited project settings and design choices. No retuning occurred between speeds.

Preparation requests move from 10000 rpm to target during seconds 5-10. At 9000 rpm the requested slope is -200 rpm/s, so the 150 rpm/s governor extends the applied acceleration command transition; at 9500 rpm the requested slope is -100 rpm/s. Both cases settle well before evaluation starts at 60 s. The settled-state assertions, rather than nominal request timing alone, establish the initial condition.

The prior report phrase "ramps to nominal by 10 s" describes the source request. It must not be interpreted as the governed 9000 rpm request reaching target at exactly 10 s. This distinction does not alter the saved disturbance-rejection trajectories.



8. Step 1: operating point, shaft load and PI



1. Initialize the standard plant at 10000 rpm. With zero external shaft extraction, hold the target request until settled. Average turbine power over absolute seconds 55-60. This yields P0 = 11789.245211 hp at 9000 rpm and 19160.793887 hp at 9500 rpm. The loaded-run preparations are checked against those cached references.

2. Set PL,max = 0.10 P0. The conversion is 1 hp = 0.7456998715822702 kW: load amplitudes are 1178.924521 hp (0.879123864 MW) and 1916.079389 hp (1.428820154 MW). Only the cached turbine_power_hp field is used; a cached extraction value from an older 20% or 30% study is not reused.

3. For each pulse j, let S(x) = min(1,max(0,x)). Construct PL(t) = 0.10 P0 sum_j [S((t-aj)/Tj) - S((t-bj)/Tj)]. Application times aj are [10.005,30,60] s and removal starts bj are [15,40.005,75] s after preparation. Tj = [0.30,1.50,3.00] s. Slopes are amplitude divided by Tj.

4. The shaft balance used for verification is Ndot = [60/(2 pi J)] [(5252.113(Pt+Pc)-5252.11 PL)/N], with J = 30 in the standard model inertia convention, signed compressor power Pc, hp powers and rpm speed. The slight difference between conversion constants follows the existing model. Extraction produces negative acceleration until extra fuel supplies the load.

5. Define controller error e = Nrequest - Ns. The inherited continuous PI is uPI = 0.025 e + I, with Idot = 0.05 e and initial integral output I(0) = 3. The plant sensor has time constant 0.05 s. Performance is scored using actual shaft speed; feedback uses sensed speed.

6. Compute c = rho(t) sat[-0.15,0.15]{0.25(dhat-dtrim)} and u = sat[0.2,4](uPI-c). The final limited command enters both plant and observer. Baseline PI uses gain zero. The command bound is common to all methods; no new PI anti-windup was added.



9. Step 2: derive the existing ARX-based DOB



Let q denote a one-sample delay. The identified acceleration equation is A(q) a = B(q) v, where v = u-u0 and a is acceleration in rpm/s. Eight selected regressors occupy output lags [1,2,4,6] and fuel lags [1,2,5,10]. The coefficients are frozen from the prior valid chirp-data identification.

A(q) = 1 - 1.894337317304 q + 0.843546068890 q^2
       + 0.073043307628 q^4 - 0.021358276735 q^6
B(q) = 361.940693761732 q - 497.137697864232 q^2
       + 147.924362845582 q^5 - 12.732667296544 q^10

1. Enforce zero steady acceleration by replacing only the last fuel coefficient: Beq[10] = B[10] - sum(B). The original sum is -0.005308553463; the corrected last coefficient is -12.727358743081. This is a project equilibrium correction, not a coefficient estimated anew from the 9500 rpm run.

2. Integrate acceleration to speed. Since Beq(1) = 0, the (1-q) factor cancels. The coefficient form is Bspeed = Ts cumsum(Beq[0:9]); hence nominal speed/fuel transfer is Bspeed(q)/A(q). Bspeed starts with one zero coefficient, so write Bspeed(q) = q C(q).

Bspeed coefficients (q^0 to q^9):
0.000000000, 5.429110406, -2.027955062, -2.027955062, -2.027955062
0.190910381, 0.190910381, 0.190910381, 0.190910381, 0.190910381

3. Approximate the sensor by H(q) = q(1-p)/(1-pq), with p = exp(-Ts/0.05) = 0.740818220682. Thus the sensed nominal plant is Pn(q) = q^2 (1-p) C(q) / [A(q)(1-pq)]. The continuous sensor is retained in the nonlinear simulation; H is its observer design approximation.

4. Choose r = exp(-2 pi fc Ts) = 0.953969203212. Set Q(q) = q^2(1-r)^2/(1-2rq+r^2 q^2). The two delays render the inverse causal. Q numerator is [0,0,0.002118834253] and denominator is [1,-1.907938406423,0.910057240676].

5. Cancel the two advances analytically: Q/Pn = (1-r)^2 A(q)(1-pq) / [(1-p) C(q)(1-2rq+r^2 q^2)]. The implementation forms numerator/denominator by convolution. Estimate dhat = (Q/Pn)(Ns-N0) - Q(u-u0), then apply the trim and compensation law. Mode 2 selects this inverse-filter path; the alternative residual path is not the tested DOB.



10. Step 3: derive LESO, UDE and ramp GPIO



Use y = Ns-N0, v = u-u0 and the approximation ydot = b0 v + f. Set r = y/b0 and d = f/b0 so rdot = v+d. Here b0 = B[1] = 361.940693761732 rpm/s per lbm/s. This one-step ARX coefficient is treated as an approximate continuous input gain; it is not a fresh local plant identification. Remaining dynamics, sensor lag and gain error enter f.

LESO: augment the model with locally constant d, so the state is [r,d]. With error eo = r-rhat, choose rhat_dot = v+dhat+l1 eo and dhat_dot = l2 eo. The error polynomial is s^2+l1 s+l2. Matching (s+omega)^2 gives l1 = 2 omega and l2 = omega^2. This produces the two-state observer without differentiating measured speed.

UDE: from d = rdot-v, filter the residual with Gf(s) = omega/(s+omega). Thus dhat = Gf(s)[sR-V]. Realize this without a raw derivative by dhat = z+omega r and zdot = -omega z-omega^2 r-omega v. Differentiating dhat verifies dhat_dot = -omega dhat + omega(rdot-v). The state is z; only speed has direct feedthrough.

GPIO: model disturbance slope h by d_dot = h and h_dot = 0. Use states [r,d,h] and equations rhat_dot = v+dhat+l1 eo, dhat_dot = hhat+l2 eo, hhat_dot = l3 eo. The error polynomial is s^3+l1 s^2+l2 s+l3. Matching (s+omega)^3 gives [l1,l2,l3] = [3 omega,3 omega^2,omega^3].

LESO assumes locally constant equivalent disturbance and GPIO assumes locally linear evolution. The actual equivalent disturbance can differ from the imposed shaft-power ramp. Poles are observer design choices retained from the original comparison; they do not imply equal bandwidth across methods or an optimized tuning result.



11. Step 4: exact discrete matrices for this example



Write xdot = Ao x + Bo [r,v]^T and dhat = Co x + Do [r,v]^T. For Ts = 0.015 s, compute exp(Ts [Ao Bo; 0 0]) = [Ad Bd; 0 I]. Each sample outputs dhat_k = Co x_k + Do [r_k,v_k]^T, then updates x_(k+1) = Ad x_k + Bd [r_k,v_k]^T. All states initialize to zero.

<b>LESO</b>

Ad =
  [ 0.9090144636   0.0143095380]
  [-0.1412294797   0.9989239428]
Bd =
  [ 0.0909855364   0.0143095380]
  [ 0.1412294797  -0.0010760572]
Co = [0, 1]; Do = [0, 0]

<b>UDE</b>

Ad =
  [ 0.9539692032]
Bd =
  [-0.1446100130  -0.0460307968]
Co = [1]; Do = [3.1415926536, 0]

<b>GPIO</b>

Ad =
  [ 0.8651189451   0.0139723775   0.0001073215]
  [-0.4170331567   0.9968055006   0.0149838591]
  [-0.4332314027  -0.0033276412   0.9999831639]
Bd =
  [ 0.1348810549   0.0139723775]
  [ 0.4170331567  -0.0031944994]
  [ 0.4332314027  -0.0033276412]
Co = [0, 1, 0]; Do = [0, 0]

Numbers displayed here are rounded; parameter_derivation.json retains full computed precision, including DOB filter polynomials. Unit Delay stores x, matrix Gain blocks implement Ad/Bd/Co, and the direct path uses Do[0] times speed only. The fuel direct coefficient is zero and has no wired feedthrough, preventing an artificial algebraic loop.



12. Step 5: trim, sample order and final assessment



At 9000 rpm the unloaded fuel approximately equals u0. At 9500 rpm unloaded fuel is 1.849471360248 lbm/s, while u0 remains 0.981086914682 lbm/s. Consequently v_trim = 0.868384445565 lbm/s. Because r is constant at trim, rdot = 0 implies d_trim = -v_trim = -0.868384445565 lbm/s for the low-order approximation. A nonzero steady residual is therefore expected; it is not automatically a shaft disturbance.

The trim memory tracks the selected raw estimate before absolute 30 s, then holds the last pre-engagement value. The correction uses dhat-dtrim. This removes the fixed operating-point bias. It does not refit b0, change the nominal model, or guarantee equal dynamics at 9500 rpm. The inverse DOB also receives the same trim-removal logic.

Final assessment: UDE retains the smallest peak excursion at both speeds and requires one observer state. GPIO retains the lowest RMSE, but loses its fast recovery lead at 9500 rpm. Existing DOB is fastest or joint-fastest in all six 9500 rpm recovery events. LESO closely follows DOB with a simpler nominal model. PI remains a transparent baseline and fallback candidate.

GPIO hits the compensation bound for 2.133% of the 9500 rpm evaluation, while no fuel saturation occurs. Clipping may contribute to its altered recovery, but this comparison does not isolate causality. Prefer DOB when the tested 9500 rpm recovery time dominates the requirement; prefer UDE for a low-complexity peak-rejection candidate; retain GPIO when average error dominates and additional validation is planned.

All settings and claims above refer to the frozen experiments. A defensible next step is separately tuned, held-out validation including noise, delay and operating-point uncertainty, with independent limits for peak speed, recovery, fuel activity and compressor margin. The 62.528% larger absolute load at 9500 rpm prevents interpreting the two-speed difference as a speed-only effect.

<!-- GPR_FF_EXTENSION -->

## Inverse GPR feedforward extension

At 9000 rpm, GPR_FF RMSE is 1.207770 rpm versus PI 1.193143 rpm (+1.23% change; positive is worse). Peak error is 11.057788 rpm. Speed guard active: 34.04% of evaluation samples.

GPR_FF +/-1 rpm recovery at 9000 rpm is faster than PI in 3/6 events, equal in 3/6, and slower in 0/6. Thus the larger peaks and RMSE coexist with faster threshold recovery; these metrics must not be collapsed into a single blanket ranking.

At 9500 rpm, GPR_FF RMSE is 2.191826 rpm versus PI 2.125136 rpm (+3.14% change; positive is worse). Peak error is 19.937677 rpm. Speed guard active: 0.00% of evaluation samples.

GPR_FF +/-1 rpm recovery at 9500 rpm is faster than PI in 6/6 events, equal in 0/6, and slower in 0/6. Thus the larger peaks and RMSE coexist with faster threshold recovery; these metrics must not be collapsed into a single blanket ranking.

| Speed | Load | Shape | Method | Valid | RMSE rpm | Peak rpm | IAE rpm s | Failure s |
|---:|---:|---|---|---|---:|---:|---:|---:|
| 9000 | 10% | ramps | PI | True | 1.193 | 10.677 | 36.774 | N/A |
| 9000 | 10% | ramps | DOB | True | 1.038 | 10.351 | 28.341 | N/A |
| 9000 | 10% | ramps | LESO | True | 1.039 | 10.349 | 28.694 | N/A |
| 9000 | 10% | ramps | UDE | True | 0.969 | 9.377 | 27.587 | N/A |
| 9000 | 10% | ramps | GPIO | True | 0.951 | 9.866 | 27.577 | N/A |
| 9000 | 10% | ramps | GPR_FF | True | 1.208 | 11.058 | 36.774 | N/A |
| 9500 | 10% | ramps | PI | True | 2.125 | 18.642 | 65.863 | N/A |
| 9500 | 10% | ramps | DOB | True | 1.850 | 18.147 | 50.799 | N/A |
| 9500 | 10% | ramps | LESO | True | 1.853 | 18.155 | 51.429 | N/A |
| 9500 | 10% | ramps | UDE | True | 1.730 | 16.574 | 49.411 | N/A |
| 9500 | 10% | ramps | GPIO | True | 1.698 | 17.393 | 49.392 | N/A |
| 9500 | 10% | ramps | GPR_FF | True | 2.192 | 19.938 | 65.864 | N/A |

Full extended report: [Six-controller GPR FF comparison](../Observer_9000_9500_GPR_FF_Comparison/REPORT.md).
