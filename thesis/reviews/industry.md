# Industry-engineer referee review

Reviewer identity: AI-assisted industry-engineer role, reusing the practical, actuator, startup and real-time remit of the earlier three-role review. This is not independent human peer review. Scope: current `control_evolution_paper.tex`, selected tables and controller source. No simulations or manuscript edits were made.

Overall recommendation: revise the three concrete points below. The manuscript already handles many earlier concerns well: startup and evaluation are separated, hardware and real-time qualification are explicitly absent, the baseline tuning confound is stated, rejected runs are retained, 9250 rpm extrapolation is disclosed, and the broad 1% recovery metric is not misinterpreted. I found no arithmetic error in the final tuning comparison.

## E1 — Reduced ringing does not imply reduced peak actuator-rate demand

- Severity: moderate; result-interpretation correction.
- Location: Chapter 12, selected-gain discussion (`control_evolution_paper.tex:627–629`); Chapter 14 final takeaway; `tmp/pdfs/control_evolution/table_tune.tex`.
- Evidence: `results/poly2_tune9250_20260915/tuning_scores.csv`, candidate 0 (base PI) versus candidate 34 (selected): peak slew increases from 4.81749568885 to 7.27362117868 lbm/s², approximately **51.0%**, although ringing decreases by 37.3%. The selected setting does reduce slew versus original Poly2 (8.71872208099 lbm/s²), so comparator identity matters. The numerical table contains these values, but the headline interpretation discusses only peak speed error as the cost of the chosen gains.
- Concrete correction: add the paired peak-slew comparison to Chapter 12 and the concluding tradeoff, explicitly distinguishing fewer reversals from lower instantaneous fuel-rate demand. At this operating point the command stays away from the magnitude limit (`fuel_limit_percent=0`), which does not test a physical valve rate limit. No new simulation is needed to correct the claim; a rate-limited actuator evaluation is an open experiment, not a completed finding.

## E2 — “Deployable study model” overstates the artifact status

- Severity: minor but material qualification correction.
- Location: `control_evolution_paper.tex:645`: “The deployable study model is ...”.
- Evidence: Chapter 11 line 600 correctly states that implementations remain desktop Simulink S-functions; Chapter 13 line 659 correctly states there is no hardware test, actuator-lag campaign, or execution-time qualification. The model file is a usable simulator artifact, not evidence of deployable engine control.
- Concrete correction: replace with “The configured desktop Simulink study model is ...” or equivalent. Preserve the existing candid deployment limitations. This is a text correction; no hardware-validation result should be invented or marked closed.

## E3 — State the operational meaning and limits of fallback switching

- Severity: moderate; incomplete implementation definition.
- Location: Chapter 8, “Guards, fallback, and local interpretation” (`control_evolution_paper.tex:452–458`).
- Evidence: `tmats_gpr_remedy_sfun.m:31–43,48–54` and matching `tmats_r3_poly2_sfun.m` recompute the fallback decision every sample, immediately substitute raw speed error and filtered acceleration, and retain the existing integral state. The DWork states are only previous speed, acceleration and integral. There is no fallback hysteresis, dwell time, blending, or integral correction at a mode transition. The training-box `outside` value is calculated after the control command and only logged; it is not a fallback trigger. Convex-hull coverage is an offline audit, not an online protection branch. The broad-cycle fallback occupancy of 78.69% makes this distinction useful for interpreting the actual tested controller.
- Concrete correction: add a short explicit paragraph after the guard equations identifying the instantaneous memoryless switch, retained integral, lack of bumpless mode-transition logic, and logged/offline status of box/hull checks. The reader should not infer that the architecture guarantees domain containment or smooth switching. Whether chattering or a transition bump occurs in a given trace requires a dedicated transition audit; neither is asserted to have occurred here. Hysteresis or blending would be a future controller change requiring fresh simulations, not a paper-only fix.

## Open work, not manuscript defects

Physical actuator dynamics and rate constraints, noisy/bias-shifted sensing, condition-based startup/restart, measured execution-time qualification, and equal-budget baseline retuning remain appropriate future experiments. The present manuscript already labels these limitations, so they should not be counted as newly fixed empirical evidence. No requirement for extra engine simulations is imposed by this review.
