# Referee T: experienced control theory academic

AI-assisted role review, 15 September 2026. This reuses the previous referee role and its emphasis on derivation, assumptions, inverse conditioning, and stability; it is not independent human peer review. Reviewed the manuscript LaTeX, diagram source, and implemented GP, virtual-fuel, uncertainty-scheduled, remedy, and Poly2 controller sources. No new simulation was performed.

## Overall assessment

Revision is warranted for algorithm precision and hybrid-controller interpretation. The core ideal local equivalent PID, characteristic polynomials, nominal-load response, analytic GP derivative, polynomial derivative, constant-feedforward equivalence, and positive affine invariance of normalized coordinates are mathematically consistent under the manuscript's stated assumptions. The manuscript already correctly avoids presenting these ideal formulas as nonlinear sampled-loop stability certificates. I found no basis to change the numerical rankings from this theory review.

## T1 — The anti-windup gate must use the error actually integrated

**Severity:** Major specification defect, correctable in text; not a demonstrated simulation defect.

**Locations:** `control_evolution_paper.tex:236–239` (Chapter 4 conditional integration), `:423` (R2), `:437` (R3); `tmats_gpr_remedy_sfun.m:25–38,48–52`; identical logic in `tmats_r3_poly2_sfun.m`.

**Evidence:** The only definition of gamma uses the sign of dynamic virtual-fuel error e_v. Later R2 and R3 equations reuse gamma but integrate e_0 and e_N^g, respectively. Their signs need not equal the sign of e_v because e_v includes acceleration fuel. The source correctly gates on `ei`, the actual integrated error. Taken literally, the paper's R2/R3 algorithm can therefore permit or suppress a saturation-time integral increment differently from the implementation.

**Required correction:** Define a generic gate gamma(u*, e_i) using the sign of e_i (or of K_i e_i if permitting negative gains), and explicitly map e_i=e_v for original virtual PI/R1/schedules, e_i=e_0 for R2, and e_i=the selected normalized or fallback speed error for R3/Poly2. All implemented K_i are positive, so the e_i-sign formulation is sufficient. Carry that notation into the R3 diagram. State that the unsaturated command includes all enabled FF and feedback terms. This is a manuscript correction; do not alter archived controller results.

## T2 — State the actual fallback transition law and its limits

**Severity:** Moderate omission in the hybrid algorithm definition.

**Locations:** `control_evolution_paper.tex:451–462`, Chapter 8 guards/fallback; `tmats_gpr_remedy_sfun.m:30–40,48–54`; corresponding Poly2 S-function.

**Evidence:** Fallback is a memoryless threshold decision evaluated at each sample. It substitutes the two coordinates without a hysteresis state, blending, dwell time, or compensating reset of the integral. The integral is only tracked before startup and otherwise conditionally integrated. This differs materially from the expressly bumpless proportional-gain transfer in the uncertainty-scheduled controller. In the broad cycle, fallback occurs extensively, so the switching behavior belongs in the main algorithm definition.

**Required correction:** State explicitly that fallback preserves the current integral and static FF, uses no hysteresis or bumpless transfer, and can change the unsaturated feedback command when the selected coordinates change. At fixed signals and integral, the hypothetical normalized-to-raw switch has jump Delta u*=K_p[(r-N_s)-e_N^g]-K_d[ahat-a^g]. The formula is explanatory where both normalized coordinates are finite; it is not an extra computation used at a singular denominator. Do not claim that observed ringing was caused by switching without a separate event-level analysis. Chattering, transition smoothness, and stability of the switched implementation remain open validation questions.

## T3 — Make the baseline feedforward signal dependence visible in its block diagram

**Severity:** Moderate diagram omission with attribution consequences.

**Locations:** `control_evolution_diagrams.tex:2–17`, baseline figure in Chapter 3; corresponding equations `control_evolution_paper.tex:205–216`.

**Evidence:** The optional inverse FF block has only an outgoing line to the command sum and no input lines. The equations establish that this early correction uses clipped sensed speed, requested acceleration, a nominal equilibrium subtraction, an enable factor, and a correction clamp. The dependence on sensed speed is exactly why this early branch is not equivalent to the later pure setpoint static-FF branch in a fixed-reference test.

**Required correction:** Add labeled incoming dependencies (at minimum N_s, a_r, and nominal reference g(N_0,0), with enable/clamp indicated inside or adjacent to the block). Preserve the distinction between this early state-dependent correction and R3's direct g(r,0,T,P). A compact explicitly labeled functional diagram is sufficient; no new simulation is needed.

## Open experiments, not conditions to fabricate closure

A sampled-loop robustness analysis with sensor/acceleration filters, scheduled and switched stability, and a conventional PID retuned under the same objective and search budget would strengthen the study. These are already acknowledged limitations or future work and are not results obtained by this review. Corrections T1–T3 should enter the main manuscript, not only a response appendix. None requires claiming hardware qualification, new stability theorems, or changed performance metrics.
