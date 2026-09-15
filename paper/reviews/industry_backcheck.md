# Industry referee: V2 back-check

AI-assisted industry-engineer role; source review completed against `control_evolution_paper_v2.tex` and the relevant R3 diagram in `control_evolution_diagrams_v2.tex`. This is not human peer review or hardware approval.

| Finding | Disposition | Verified revision |
|---|---|---|
| E1: ringing versus actuator-rate demand | Closed as a manuscript interpretation correction | Line 656 states the 8.71872 → 7.27362 lbm/s² reduction versus original Poly2 and the 51.0% increase versus base PI, alongside the 37.3% reversal reduction. The text correctly identifies the two-second edge-window domain and inactive magnitude limits; it does not claim a physical valve-rate test. The final takeaway at line 735 retains this tradeoff. |
| E2: deployable model wording | Closed as a wording correction | Line 680 now calls the artifact a “configured desktop Simulink study model.” The computational discussion at line 625 retains the absence of measured execution-time qualification. |
| E3: operational fallback definition | Closed as an algorithm-description correction | Lines 477–481 specify per-sample switching, no hysteresis/dwell/blending, retained integral and FF, the possible finite-coordinate command jump, and the logged/offline status of box/hull coverage. The equation has the correct sign for normalized-to-raw switching with unchanged integral. The R3 diagram identifies guarded coordinates without implying coverage containment. |

No false empirical closure identified. The manuscript explicitly leaves transition smoothness, chattering, switched-loop robustness and physical actuator qualification as untested matters. No additional controller or plant simulation is represented as having been performed. These findings are closed at the document level only; the V2 remains a qualified simulation study.

Recommendation: acceptable with respect to E1–E3, subject to the root author's final PDF layout and build checks.
