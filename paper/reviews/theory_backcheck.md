# Theory referee back-check of V2

15 September 2026. AI role review; source-level back-check only, with no new simulation and no independent human peer-review claim.

Reviewed `control_evolution_paper_v2.tex` and `control_evolution_diagrams_v2.tex` against the implementation evidence recorded in `theory.md`.

| Finding | Disposition | Verification |
|---|---|---|
| T1: integrated-error anti-windup gate | Closed as a manuscript correction | Chapter 4 now defines gamma(u*,e_i), states that every enabled command contribution enters u*, identifies all positive integral gains, maps each architecture to its actual integrated error, and defines later gamma shorthand. This matches the `ei` gate in the remedy and Poly2 S-functions. The R3 diagram now includes gamma in its recurrence. |
| T2: fallback transition semantics | Closed as an algorithm-description correction; robustness validation remains open | Chapter 8 explicitly states per-sample decisions, no hysteresis/dwell/blending, retained integral and FF, and no compensating integral reset. The jump formula has the correct signs for normalized-to-raw substitution. Its fixed-signal, fixed-integral, finite-coordinate assumptions are explicit. It is correctly separated from a singular-denominator calculation and from any claim that switching caused the measured ringing. |
| T3: early FF block dependencies | Closed as a diagram correction | The baseline diagram now labels clipped sensed speed, clipped reference increment, fixed equilibrium inverse value, enable factor, and correction clamp. Its note identifies sensed-speed dependence, preserving the distinction from later R3 reference-only static FF. |

No further theory correction is required for these three findings. This closure concerns accurate exposition of the implemented simulations. It does not close the explicitly open switched-loop robustness, actuator, noise, or equally retuned conventional-PID experiments. The author should complete the final rendered-PDF layout check separately.
