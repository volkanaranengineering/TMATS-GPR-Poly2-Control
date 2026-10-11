
# PI Disturbance-Rejection Augmentations for a Dynamic Gas-Turbine Model

<b>A tutorial comparison of DOB, LESO, UDE and GPIO at 9000 and 9500 rpm</b>

Comprehensive technical paper | 13 September 2026 | T-MATS project


## Abstract

This tutorial explains how to augment an existing proportional-integral (PI) gas-turbine speed controller with disturbance estimation, and compares four implementations using saved nonlinear T-MATS simulations. The methods are an identified-model disturbance observer (DOB), linear extended-state observer (LESO), uncertainty and disturbance estimator (UDE), and generalized proportional-integral observer (GPIO). A common fuel-compensation interface preserves the PI gains and actuator limits. The paper develops the continuous equations, traces every numerical parameter to its source, and gives the discrete matrices and causal sample sequence used in Simulink.

The validation scenario regulates speed at 9000 or 9500 rpm under 10% gross-turbine-power extraction with 0.30, 1.50 and 3.00 s load ramps. All ten trajectories pass numerical checks. GPIO produces the smallest RMSE at both speeds, while UDE produces the smallest peak speed error. At 9500 rpm, the existing DOB has the fastest or joint-fastest recovery in all six events. The result is a requirement-dependent choice rather than a universal ranking. Five SWOT assessments and a staged validation plan translate these findings into practical design guidance.


## What the reader will learn

Question | Where it is answered
How is the shaft-load experiment defined? | Sections 2-3
How are the observers derived and discretized? | Sections 4-7
Which method performs best, and by which measure? | Sections 8-12
How should the method be selected and reproduced? | Sections 13-16

<b>Keywords:</b> gas turbine; PI control; disturbance rejection; DOB; LESO; UDE; GPIO; discrete implementation.

This document consolidates the two project reports into a single account. It reuses their verified data, corrects the preparation-command interpretation, and reassesses method selection across both speeds. No new plant simulations or tuning are claimed.


# 1. The control problem and tutorial roadmap

A speed PI controller changes fuel flow when measured speed departs from demand. A shaft load first removes mechanical power, causing a speed deviation before feedback can respond. An observer uses measured speed and known applied fuel to estimate the combined effect of this disturbance and model mismatch. Subtracting a bounded equivalent-fuel estimate from the PI output can improve rejection without replacing the PI controller.


## 1.1 Three quantities that should not be confused

Quantity | Interpretation
Shaft extraction PL | The actual external mechanical load, expressed in hp or MW.
Equivalent disturbance d | A residual in fuel units that includes shaft loading, plant dynamics and model mismatch. It is not a calibrated shaft-power measurement.
Compensation c | The limited correction subtracted from PI output. A negative correction increases fuel.


## 1.2 Why these methods?

LESO offers a two-state estimate with bandwidth-style tuning [1,2]. UDE estimates a filtered residual with a one-state realization [3]. GPIO adds a disturbance-slope state and is relevant to time-varying loads [4]. The existing DOB retains the project’s fuller identified plant model. LESO and GPIO are closely related members of the same observer family; this is a practical shortlist, not three unrelated theories.


## 1.3 What is shared and what differs?

The plant, sensor, PI gains, fuel limits, compensation gain and ramp durations are shared. The observer pole-frequency parameter is also fixed, but equal parameter values do not equalize estimator bandwidth. The new observers use one approximate input gain from the earlier ARX fit, whereas the existing DOB uses the identified dynamic model. This is therefore a comparison of concrete fixed-setting implementations, not an isolated test of observer structure.

The tutorial proceeds from parameter provenance to a worked load calculation, then derives each observer, gives exact discrete matrices, and explains trim removal and sample order. Only after that does it compare complete responses, recovery times and implementation tradeoffs. The final sections provide five SWOT tables and an evidence-based development choice.


# 2. Define the parameters before tuning

The numerical settings below define this experiment. They are not claimed to be optimal or prescribed by a paper. Measured operating-point quantities are separated from inherited project settings and design choices. No retuning occurred between speeds.

Parameter | Exact value / source | Role
Kp, Ki | 0.05/2 = 0.025; 0.1/2 = 0.05 | Inherited PI mask values
PI initial integral output | 3 lbm/s (PI_IC_M) | Inherited startup setting; not equilibrium fuel
Ts | 0.015 s | Prior data and plant solve interval
Sensor | Gain 1; time constant 0.05 s; limits 0-20000 rpm | Inherited model; noise disabled
Internal offsets | N0 = 9000 rpm; u0 = 0.9810869146824126 lbm/s | Identification offsets; fixed at both speeds
b0 | 361.94069376173167 | First nonzero ARX fuel coefficient; approximate input gain
Observer fc | 0.5 Hz; omega = pi rad/s | Fixed design pole-frequency parameter
Compensation gain g | 0.25 | Partial compensation design choice
Compensation bound | +/-0.15 lbm/s | Shared authority bound
Fuel limits | 0.2 to 4 lbm/s | Shared project actuator bounds
Trim / enable | Latch at 30 s; enable over 2 s | Bumpless engagement design
Demand rate limit | +/-150 rpm/s | Existing governor
Ramp / hold scenario | 0.30, 1.50, 3.00 s ramps; 10% load | User-requested amplitude; declared ramp choices

Preparation requests move from 10000 rpm to target during seconds 5-10. At 9000 rpm the requested slope is -200 rpm/s, so the 150 rpm/s governor extends the applied acceleration command transition; at 9500 rpm the requested slope is -100 rpm/s. Both cases settle well before evaluation starts at 60 s. The settled-state assertions, rather than nominal request timing alone, establish the initial condition.


# 3. Build the experiment and the PI interface

1. Initialize the standard plant at 10000 rpm. With zero external shaft extraction, hold the target request until settled. Average turbine power over absolute seconds 55-60. This yields P0 = 11789.245211 hp at 9000 rpm and 19160.793887 hp at 9500 rpm. The loaded-run preparations are checked against those cached references.

2. Set PL,max = 0.10 P0. The conversion is 1 hp = 0.7456998715822702 kW: load amplitudes are 1178.924521 hp (0.879123864 MW) and 1916.079389 hp (1.428820154 MW). Only the cached turbine_power_hp field is used; a cached extraction value from an older 20% or 30% study is not reused.

3. For each pulse j, let S(x) = min(1,max(0,x)). Construct PL(t) = 0.10 P0 sum_j [S((t-aj)/Tj) - S((t-bj)/Tj)]. Application times aj are [10.005,30,60] s and removal starts bj are [15,40.005,75] s after preparation. Tj = [0.30,1.50,3.00] s. Slopes are amplitude divided by Tj.

Ramp time | 9000 rpm slope (MW/s) | 9500 rpm slope (MW/s)
0.30 s | 2.930413 | 4.762734
1.50 s | 0.586083 | 0.952547
3.00 s | 0.293041 | 0.476273

4. The shaft balance used for verification is Ndot = [60/(2 pi J)] [(5252.113(Pt+Pc)-5252.11 PL)/N], with J = 30 in the standard model inertia convention, signed compressor power Pc, hp powers and rpm speed. The slight difference between conversion constants follows the existing model. Extraction produces negative acceleration until extra fuel supplies the load.

5. Define controller error e = Nrequest - Ns. The inherited continuous PI is uPI = 0.025 e + I, with Idot = 0.05 e and initial integral output I(0) = 3. The plant sensor has time constant 0.05 s. Performance is scored using actual shaft speed; feedback uses sensed speed.

6. Compute c = rho(t) sat[-0.15,0.15]{0.25(dhat-dtrim)} and u = sat[0.2,4](uPI-c). The final limited command enters both plant and observer. Baseline PI uses gain zero. The command bound is common to all methods; no new PI anti-windup was added.


# 4. Derive the identified-model DOB

Let q denote a one-sample delay. The identified acceleration equation is A(q) a = B(q) v, where v = u-u0 and a is acceleration in rpm/s. Eight selected regressors occupy output lags [1,2,4,6] and fuel lags [1,2,5,10]. The coefficients are frozen from the prior valid chirp-data identification.

1. Enforce zero steady acceleration by replacing only the last fuel coefficient: Beq[10] = B[10] - sum(B). The original sum is -0.005308553463; the corrected last coefficient is -12.727358743081. This is a project equilibrium correction, not a coefficient estimated anew from the 9500 rpm run.

2. Integrate acceleration to speed. Since Beq(1) = 0, the (1-q) factor cancels. The coefficient form is Bspeed = Ts cumsum(Beq[0:9]); hence nominal speed/fuel transfer is Bspeed(q)/A(q). Bspeed starts with one zero coefficient, so write Bspeed(q) = q C(q).

3. Approximate the sensor by H(q) = q(1-p)/(1-pq), with p = exp(-Ts/0.05) = 0.740818220682. Thus the sensed nominal plant is Pn(q) = q^2 (1-p) C(q) / [A(q)(1-pq)]. The continuous sensor is retained in the nonlinear simulation; H is its observer design approximation.

4. Choose r = exp(-2 pi fc Ts) = 0.953969203212. Set Q(q) = q^2(1-r)^2/(1-2rq+r^2 q^2). The two delays render the inverse causal. Q numerator is [0,0,0.002118834253] and denominator is [1,-1.907938406423,0.910057240676].

5. Cancel the two advances analytically: Q/Pn = (1-r)^2 A(q)(1-pq) / [(1-p) C(q)(1-2rq+r^2 q^2)]. The implementation forms numerator/denominator by convolution. Estimate dhat = (Q/Pn)(Ns-N0) - Q(u-u0), then apply the trim and compensation law. Mode 2 selects this inverse-filter path; the alternative residual path is not the tested DOB.


# 5. Derive the three low-order alternatives

Use y = Ns-N0, v = u-u0 and the approximation ydot = b0 v + f. Set r = y/b0 and d = f/b0 so rdot = v+d. Here b0 = B[1] = 361.940693761732 rpm/s per lbm/s. This one-step ARX coefficient is treated as an approximate continuous input gain; it is not a fresh local plant identification. Remaining dynamics, sensor lag and gain error enter f.

LESO: augment the model with locally constant d, so the state is [r,d]. With error eo = r-rhat, choose rhat_dot = v+dhat+l1 eo and dhat_dot = l2 eo. The error polynomial is s^2+l1 s+l2. Matching (s+omega)^2 gives l1 = 2 omega and l2 = omega^2. This produces the two-state observer without differentiating measured speed. This is the observer augmentation used here, rather than a complete replacement of PI by ADRC [1,2].

UDE: from d = rdot-v, filter the residual with Gf(s) = omega/(s+omega). Thus dhat = Gf(s)[sR-V]. Realize this without a raw derivative by dhat = z+omega r and zdot = -omega z-omega^2 r-omega v. Differentiating dhat verifies dhat_dot = -omega dhat + omega(rdot-v). The state is z; only speed has direct feedthrough. This realizes the filtered-residual principle in [3] with the shared PI interface.

GPIO: model disturbance slope h by d_dot = h and h_dot = 0. Use states [r,d,h] and equations rhat_dot = v+dhat+l1 eo, dhat_dot = hhat+l2 eo, hhat_dot = l3 eo. The error polynomial is s^3+l1 s^2+l2 s+l3. Matching (s+omega)^3 gives [l1,l2,l3] = [3 omega,3 omega^2,omega^3]. The added slope state is a first-degree polynomial disturbance model [4].

Value | Numerical substitution | Meaning
omega | pi = 3.141592653590 rad/s | Chosen fc = 0.5 Hz
LESO l1, l2 | 6.283185307180; 9.869604401089 | Repeated second-order observer poles
UDE omega, omega^2 | 3.141592653590; 9.869604401089 | One-state residual filter
GPIO l1, l2, l3 | 9.424777960769; 29.608813203268; 31.006276680300 | Repeated third-order observer poles
Time constant 1/omega | 0.318309886184 s | Single pole time constant, not settling time
Discrete pole | 0.953969203212 | exp(-omega Ts)

LESO assumes locally constant equivalent disturbance and GPIO assumes locally linear evolution. The actual equivalent disturbance can differ from the imposed shaft-power ramp. Poles are observer design choices retained from the original comparison; they do not imply equal bandwidth across methods or an optimized tuning result.


# 6. Convert the observers to discrete blocks

Write xdot = Ao x + Bo [r,v]^T and dhat = Co x + Do [r,v]^T. For Ts = 0.015 s, compute exp(Ts [Ao Bo; 0 0]) = [Ad Bd; 0 I]. Each sample outputs dhat_k = Co x_k + Do [r_k,v_k]^T, then updates x_(k+1) = Ad x_k + Bd [r_k,v_k]^T. All states initialize to zero.

<b>LESO</b>

<b>UDE</b>

<b>GPIO</b>

Numbers displayed here are rounded; parameter_derivation.json in the companion tutorial files retains full computed precision, including DOB filter polynomials. Unit Delay stores x, matrix Gain blocks implement Ad/Bd/Co, and the direct path uses Do[0] times speed only. The fuel direct coefficient is zero and has no wired feedthrough, preventing an artificial algebraic loop.


# 7. Remove trim bias and execute causally

At 9000 rpm the unloaded fuel approximately equals u0. At 9500 rpm unloaded fuel is 1.849471360248 lbm/s, while u0 remains 0.981086914682 lbm/s. Consequently v_trim = 0.868384445565 lbm/s. Because r is constant at trim, rdot = 0 implies d_trim = -v_trim = -0.868384445565 lbm/s for the low-order approximation. A nonzero steady residual is therefore expected; it is not automatically a shaft disturbance.

The trim memory tracks the selected raw estimate before absolute 30 s, then holds the last pre-engagement value. The correction uses dhat-dtrim. This removes the fixed operating-point bias. It does not refit b0, change the nominal model, or guarantee equal dynamics at 9500 rpm. The inverse DOB also receives the same trim-removal logic.

Sample operation | Exact role
1. Read signals | Take sensed speed Ns and observer state x_k.
2. Estimate | Use r_k = (Ns-9000)/b0; form Co x_k + Do[0] r_k. No instantaneous fuel term.
3. Trim and compensate | Subtract the stored pre-engagement residual; multiply by 0.25, bound to +/-0.15 lbm/s, and apply enable factor.
4. Limit fuel | Subtract compensation from PI output; limit result to 0.2-4 lbm/s.
5. Update observer | Set v_k = limited fuel - u0. Compute x_(k+1) with Ad and Bd and store it in Unit Delay.
6. Advance and verify | Plant advances; log actual speed, shaft powers, convergence and observer signals.

A successful estimate implementation is not the same as a physically accurate disturbance estimate. The following results test the resulting closed-loop speed response. The numerical recurrence checks establish that the blocks implement the stated equations; they do not identify the true external load separately from model mismatch.


# 8. Experimental results at both speeds

The 10% load is 0.879124 MW at 9000 rpm and 1.428820 MW at 9500 rpm, a 62.528% increase in absolute power. The 9000 rpm records are reused from the first study; the 9500 rpm study repeats the same controller and ramp settings. Evaluation spans 90 s after 60 s preparation. Each total run has 10001 samples at 15 ms.

Speed | Method | RMSE<br/>(rpm) | Peak error<br/>(rpm) | RMSE reduction<br/>vs PI
9000 | PI | 1.193 | 10.677 | 0.00%
9000 | DOB | 1.038 | 10.351 | 13.02%
9000 | LESO | 1.039 | 10.349 | 12.90%
9000 | UDE | 0.969 | 9.377 | 18.75%
9000 | GPIO | 0.951 | 9.866 | 20.30%
9500 | PI | 2.125 | 18.642 | 0.00%
9500 | DOB | 1.850 | 18.147 | 12.94%
9500 | LESO | 1.853 | 18.155 | 12.82%
9500 | UDE | 1.730 | 16.574 | 18.59%
9500 | GPIO | 1.698 | 17.393 | 20.10%

RMSE = sqrt(mean(e²)) summarizes average regulation error; peak error = max|e| measures the largest excursion. IAE = Ts sum|e| measures cumulative absolute error. These calculations use actual shaft speed relative to the nominal demand, whereas the controller uses the sensed speed.


## 8.1 Reading the ranking correctly

<b>GPIO has the lowest RMSE at both speeds.</b> Its advantage relative to PI is about 20%. <b>UDE has the lowest peak error at both speeds.</b> LESO closely follows the existing DOB. These statements concern different objectives and are not interchangeable with recovery-time ranking.

All ten trajectories pass the numerical-validity checks and none reaches the fuel limits. At 9500 rpm, GPIO compensation reaches its bound for 2.133% of the evaluation. The other configurations do not reach the compensation bound. The minimum reported compressor margins remain positive; this alone does not establish a validated physical operating envelope.


# 9. General responses: 9000 rpm

![Figure 1. Actual speed, speed error, limited fuel and shaft extraction at 9000 rpm. Time is measured after preparation. All five controllers receive the same load profile.](C:/Users/volka/OneDrive/Belgeler/MATLAB/T-MATS_v1_3_3/T-MATS-master/Trunk/TMATSGPT/results/Observer_9000_9500_Comparison/overview_9000.png)


# 9. General responses: 9500 rpm

![Figure 2. Actual speed, speed error, limited fuel and shaft extraction at 9500 rpm. Time is measured after preparation. All five controllers receive the same load profile.](C:/Users/volka/OneDrive/Belgeler/MATLAB/T-MATS_v1_3_3/T-MATS-master/Trunk/TMATSGPT/results/Observer_9000_9500_Comparison/overview_9500.png)


# 10. Rejection zooms: 9000 rpm

![Figure 3. Six ramp edges at 9000 rpm. Gray shading marks the ramp duration; green shading marks the +/-1 rpm recovery band. Each panel uses local time from ramp start.](C:/Users/volka/OneDrive/Belgeler/MATLAB/T-MATS_v1_3_3/T-MATS-master/Trunk/TMATSGPT/results/Observer_9000_9500_Comparison/zooms_9000.png)

GPIO recovers fastest on the rapid and intermediate events at 9000 rpm, while UDE suppresses the initial rapid-ramp peak most strongly. For the 3.00 s ramps, recovery differences among augmentations are at most one sample. Those small differences should not determine implementation choice alone.


# 10. Rejection zooms: 9500 rpm

![Figure 4. Six ramp edges at 9500 rpm. Gray shading marks the ramp duration; green shading marks the +/-1 rpm recovery band. Each panel uses local time from ramp start.](C:/Users/volka/OneDrive/Belgeler/MATLAB/T-MATS_v1_3_3/T-MATS-master/Trunk/TMATSGPT/results/Observer_9000_9500_Comparison/zooms_9500.png)

At 9500 rpm, GPIO still minimizes full-test RMSE but does not retain its recovery lead. Existing DOB is fastest or joint-fastest in all six events. UDE retains the smallest peak. Thus the larger operating-point/load case changes the recovery ranking even though the RMSE ordering is preserved.


# 11. Recovery after ramp completion

Recovery is the first sample after the last excursion outside +/-1 rpm, confirmed by at least 0.5 s dwell until the next ramp. Post-ramp recovery subtracts the ramp duration and is bounded below by zero. All entries are seconds; sampling resolution is 15 ms. These are absolute-band regulation times, not percentage settling times.


## 0.30 s application and removal ramps

Method | Apply<br/>9000 rpm | Apply<br/>9500 rpm | Remove<br/>9000 rpm | Remove<br/>9500 rpm
PI | 1.050 | 1.350 | 1.080 | 1.365
DOB | 0.705 | 0.855 | 0.735 | 0.870
LESO | 0.720 | 0.885 | 0.750 | 0.900
UDE | 0.780 | 0.990 | 0.795 | 1.005
GPIO | 0.615 | 0.990 | 0.630 | 0.870


## 1.50 s application and removal ramps

Method | Apply<br/>9000 rpm | Apply<br/>9500 rpm | Remove<br/>9000 rpm | Remove<br/>9500 rpm
PI | 0.630 | 0.945 | 0.645 | 0.930
DOB | 0.345 | 0.540 | 0.360 | 0.525
LESO | 0.345 | 0.555 | 0.375 | 0.540
UDE | 0.420 | 0.630 | 0.420 | 0.615
GPIO | 0.285 | 0.645 | 0.300 | 0.570


## 3.00 s application and removal ramps

Method | Apply<br/>9000 rpm | Apply<br/>9500 rpm | Remove<br/>9000 rpm | Remove<br/>9500 rpm
PI | 0.315 | 0.645 | 0.315 | 0.600
DOB | 0.165 | 0.330 | 0.150 | 0.285
LESO | 0.165 | 0.330 | 0.150 | 0.285
UDE | 0.165 | 0.390 | 0.150 | 0.360
GPIO | 0.150 | 0.330 | 0.150 | 0.315


# 12. Recovery from ramp start

Recovery is the first sample after the last excursion outside +/-1 rpm, confirmed by at least 0.5 s dwell until the next ramp. Post-ramp recovery subtracts the ramp duration and is bounded below by zero. All entries are seconds; sampling resolution is 15 ms. These are absolute-band regulation times, not percentage settling times.


## 0.30 s application and removal ramps

Method | Apply<br/>9000 rpm | Apply<br/>9500 rpm | Remove<br/>9000 rpm | Remove<br/>9500 rpm
PI | 1.350 | 1.650 | 1.380 | 1.665
DOB | 1.005 | 1.155 | 1.035 | 1.170
LESO | 1.020 | 1.185 | 1.050 | 1.200
UDE | 1.080 | 1.290 | 1.095 | 1.305
GPIO | 0.915 | 1.290 | 0.930 | 1.170


## 1.50 s application and removal ramps

Method | Apply<br/>9000 rpm | Apply<br/>9500 rpm | Remove<br/>9000 rpm | Remove<br/>9500 rpm
PI | 2.130 | 2.445 | 2.145 | 2.430
DOB | 1.845 | 2.040 | 1.860 | 2.025
LESO | 1.845 | 2.055 | 1.875 | 2.040
UDE | 1.920 | 2.130 | 1.920 | 2.115
GPIO | 1.785 | 2.145 | 1.800 | 2.070


## 3.00 s application and removal ramps

Method | Apply<br/>9000 rpm | Apply<br/>9500 rpm | Remove<br/>9000 rpm | Remove<br/>9500 rpm
PI | 3.315 | 3.645 | 3.315 | 3.600
DOB | 3.165 | 3.330 | 3.150 | 3.285
LESO | 3.165 | 3.330 | 3.150 | 3.285
UDE | 3.165 | 3.390 | 3.150 | 3.360
GPIO | 3.150 | 3.330 | 3.150 | 3.315


# 13. SWOT assessment: PI and existing DOB

Strengths and weaknesses combine measured evidence with known implementation requirements. Opportunities and threats are engineering assessments for future use, not additional simulation results.


## 13.1 Baseline PI

Dimension | Assessment
Strengths | Simple, transparent feedback law; all cases valid. Serves as a reproducible baseline and potential fallback.
Weaknesses | Largest RMSE and peak excursions at both speeds. No explicit disturbance estimate and no added anti-windup.
Opportunities | Retain as fallback; add anti-windup and constraint handling before increasing loop complexity.
Threats | Gain changes, larger extraction and fuel saturation can degrade rejection. Windup was not exercised in these unsaturated runs.


## 13.2 PI + identified-model DOB

Dimension | Assessment
Strengths | Uses the fuller sparse ARX model and sensor-aware causal inverse. Fastest or joint-fastest recovery in all six 9500 rpm events.
Weaknesses | Requires nominal-model preparation, equilibrium correction and inverse-filter realization. RMSE is higher than UDE and GPIO.
Opportunities | Prioritize when the tested 9500 rpm recovery objective dominates. Validate scheduled models and independently tune Q.
Threats | Inverse-model mismatch, uncertain delay and excessive bandwidth can erode robustness. Stable nominal filter poles are insufficient for nonlinear closed-loop guarantees.


# 14. SWOT assessment: LESO and UDE


## 14.1 PI + LESO

Dimension | Assessment
Strengths | Two-state core with a simple pole-based design; avoids a complete plant inverse. Closely matches DOB performance at both speeds.
Weaknesses | Does not improve full-test RMSE over the existing DOB. Relies on approximate b0 and locally constant equivalent-disturbance modeling.
Opportunities | Use as a simpler-model alternative. Identify local input gain independently and tune with explicit noise and delay limits.
Threats | High observer gain, gain-sign errors, sensor lag and neglected fast dynamics may cause peaking or degraded robustness.


## 14.2 PI + UDE

Dimension | Assessment
Strengths | One-state core and no raw differentiator. Smallest peak error at both speeds, with about 19% lower RMSE than PI.
Weaknesses | Recovery is slower than DOB on the tested rapid 9500 rpm ramps. The direct speed term retains finite high-frequency noise gain.
Opportunities | Strong compact-implementation candidate when peak error and state count dominate. Validate speed-noise filtering before deployment.
Threats | Quantization, noisy speed, delay and filter/plant bandwidth mismatch may reduce its deterministic advantage.

The UDE recommendation is conditional: a low state count and a low measured peak do not imply the fastest recovery or the greatest noise robustness.


# 15. SWOT assessment: GPIO and design choice


## 15.1 PI + ramp GPIO

Dimension | Assessment
Strengths | Lowest RMSE at both speeds; explicit disturbance-slope state. Best rapid/intermediate recovery at 9000 rpm.
Weaknesses | Three core states; rapid-ramp peak exceeds UDE. Recovery lead is lost at 9500 rpm, where compensation clips for 2.133% of evaluation.
Opportunities | Candidate when average speed error is the primary objective. Test independently tuned, ramp-heavy scenarios under actuator and noise constraints.
Threats | Slope estimation, ramp corners and nonlinear equivalent-disturbance dynamics challenge the assumed local ramp model. More gain may increase noise sensitivity.


## 15.2 A requirement-dependent recommendation

Primary requirement | Candidate supported by this evidence
Small implementation and minimum peak error | UDE, followed by noise and delay validation.
Minimum average error in the tested scenarios | GPIO, with explicit attention to compensation clipping.
Fast recovery at the tested 9500 rpm condition | Existing DOB; fastest or joint-fastest in every event.
Simple nominal model with DOB-like response | LESO; little RMSE advantage over the existing DOB.

On the 0.30 s application ramp, post-ramp recovery changes from 0.615 s (GPIO) versus 0.705 s (DOB) at 9000 rpm to 0.990 s versus 0.855 s at 9500 rpm. Clipping may contribute to that change, but causality was not isolated. Do not select a controller from RMSE alone.


# 16. Verification, reproducibility and next steps

Every trajectory passes finite-signal, positive-fuel and positive-margin checks, flow residual no greater than 10^-9, and fewer than 200 solver iterations. Matched shaft-load timing and unloaded power references are checked. Torque-balance reconstruction differs from logged acceleration by less than 2.0 × 10^-11 rpm/s. Independent observer replay differs by less than 6.2 × 10^-14 lbm/s. These checks verify the simulation and equation implementation; they do not validate the disturbance estimate as a separate physical measurement.

Important limitations are a single deterministic scenario per speed, no sensor noise, no parameter sweep, no measured target execution time, and no confidence intervals. Equal pole-frequency settings do not equalize bandwidth. The absolute disturbance is 62.528% larger at 9500 rpm. Different ramp durations also have different preceding histories and hold times. The ranking therefore applies to these frozen implementations and experiments.

Next stage | Purpose
Independent tuning and held-out validation | Tune on separate profiles, then compare peak, RMSE, recovery and fuel activity on unseen scenarios.
Robustness and constraints | Add noise, quantization, sensor delay and gain mismatch; assess fuel, temperature and compressor-margin limits.
Implementation testing | Add appropriate anti-windup/fallback logic and measure precision, execution time and memory on the intended target.


## Reproduction

Use MATLAB R2018b, Simulink and the adjacent T-MATS library/example setup. Run <b>run_tmats_literature_comparison(9500)</b> and then <b>compare_observers_two_speeds.py</b>. The 9000 rpm data remain frozen from the first comparison. Run <b>build_comprehensive_observer_tutorial.py</b> to rebuild this paper. The model is <b>GasTurbine_Dyn_Template_GPT_DOB_PTO_ALT.mdl</b>.

Load the model before calling tmats_literature_setup(method,0.5,nominalRpm), since its PreLoadFcn initializes LESO by default. Methods 2, 3 and 4 select LESO, UDE and GPIO. The source archive retains MAT/CSV trajectories, global/event metrics, recovery tables and verification outputs. The companion tutorial directory holds full-precision parameter matrices and a source integrity manifest.

<b>Conclusion.</b> The observer additions improve the PI baseline in these tests, but no method dominates every requirement. UDE is the compact peak-rejection candidate, GPIO is the average-error candidate, and the existing DOB is the tested 9500 rpm recovery candidate. Further validation should follow that distinction.


# References and evidence record

<b>[1]</b> Z. Gao, "Scaling and bandwidth-parameterization based controller tuning," American Control Conference, vol. 6, pp. 4989-4996, 2003. DOI: 10.1109/ACC.2003.1242516. <link href="https://engagedscholarship.csuohio.edu/enece_facpub/528/" color="#007f86">Source</link>

<b>[2]</b> G. Herbst, "A simulative study on active disturbance rejection control (ADRC) as a control tool for practitioners," Electronics, 2(3), pp. 246-279, 2013. DOI: 10.3390/electronics2030246. <link href="https://arxiv.org/html/1908.04596" color="#007f86">Source</link>

<b>[3]</b> Q.-C. Zhong and D. Rees, "Control of uncertain LTI systems based on an uncertainty and disturbance estimator," Journal of Dynamic Systems, Measurement, and Control, 126(4), pp. 905-910, 2004. DOI: 10.1115/1.1850529. <link href="https://doi.org/10.1115/1.1850529" color="#007f86">Source</link>

<b>[4]</b> H. Sira-Ramirez, "Robust linear output feedback control of a synchronous generator," American Control Conference, pp. 3728-3733, 2011. <link href="https://skoge.folk.ntnu.no/prost/proceedings/acc11/data/papers/0048.pdf" color="#007f86">Source</link>


## Project evidence

Numerical results come from the saved project experiments, not from the cited papers. The literature supports the estimation principles. This work preserves the existing PI and introduces project-specific partial compensation, limits and trim removal; it does not claim to reproduce the complete reference-paper controllers or transfer their stability guarantees.

The source documents are <i>Comparison of PI Disturbance-Rejection Augmentations for a Dynamic Gas-Turbine Model</i> (12 pages, 12 September 2026) and <i>PI disturbance-rejection augmentations at 9000 and 9500 rpm</i> (15 pages, augmented 13 September 2026). This paper replaces their repeated exposition with one tutorial sequence and updates the SWOT and recommendations using both operating points.

The earlier description of preparation reaching nominal by 10 s applies to the source demand. The 150 rpm/s governor extends the applied 9000 rpm demand transition. Both tests are verified settled before the evaluation, so this clarification does not change the data or metrics.

Frozen datasets:<br/>9000 rpm: literature_observers_9000rpm_10pct_20260912_211600_355<br/>9500 rpm: literature_observers_9500rpm_10pct_20260912_213607_364<br/>Combined tables and plots: results/Observer_9000_9500_Comparison

Document status: scholarly-style project tutorial and technical record; not a peer-reviewed publication. Prior PDFs and raw results are preserved. The tutorial source manifest records the new PDF, builder, input metrics, and both source PDFs by SHA-256.
