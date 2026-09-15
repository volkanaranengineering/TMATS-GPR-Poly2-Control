# Research assistant referee: reproducibility and metric audit

This is an AI role review using the previous newly graduated PhD research-assistant lens, not independent human peer review. I reviewed the manuscript, table/packaging generators, archived summaries, fixed-load and cycle metric implementations, inlet-signal patch, and coverage-audit code. The main numerical comparisons inspected agree with the archived evidence. The following four bounded findings warrant revision; no new controller simulation is requested.

## A1 — Define the observation window for the reported peak fuel slew

**Severity: medium; verified reporting ambiguity.**

**Location:** `build_control_evolution_paper.py`, `labs` entry `Peak slew (lbm/s^2)` used in the 9250-rpm table; manuscript Chapter 2 metrics and Chapter 12 tuning results.

**Evidence:** `tmats_fixed_comparison_metrics.m:20` computes slew only inside each of the six two-second post-edge windows and takes their maximum. By contrast, `run_tmats_r3_cycle.m:55` computes slew over all evaluation samples. Both summary columns use the same name, `max_fuel_slew_lbm_s2`. The manuscript carefully distinguishes the two fuel-reversal metrics but does not make this parallel distinction for slew. An unqualified peak label can be read as the full-run maximum, which is not the fixed-load statistic implemented.

**Required correction:** Label the fixed-load table row “Peak edge-window slew,” define `max_j max_{k in W_j} |u[k]-u[k-1]|/Ts`, and state that the cycle statistic instead covers the complete evaluation interval. Do not change archived values or imply that startup/entire-run slew was evaluated. If the full-evaluation statistic is added, identify it as a new reanalysis.

## A2 — Include the one-sample delay of inlet conditions in the algorithm specification

**Severity: medium; verified implementation detail omitted from reproduction instructions.**

**Location:** `control_evolution_paper.tex:120-137` (notation/timing), Chapter 7 input definition, and Chapter 9 coverage audit; `tmats_environment_vf_patch.m:6-13`.

**Evidence:** The model patch converts inlet temperature and pressure, then passes each through a Unit Delay with `SampleTime=VF.Ts`, initialized to 288.15 K and 99.298 kPa. `audit_tmats_cycle_coverage.m:26` reconstructs controller queries using the prior sample explicitly: `temp=[288.15;d.inlet_temperature_K(1:end-1)]` and the analogous pressure vector. The current manuscript says actual inlet T/P are used and gives contemporaneous notation without specifying that controller values lag logged inlet signals by one sample. This matters in the changing-ambient experiment and in reproducing the coverage checks.

**Required correction:** Introduce controller-query conditions `T_q[k]=T_in[k-1]`, `P_q[k]=P_in[k-1]`, initialization and 0.015-s delay. State that T/P in inverse controller equations denote these delayed converted measurements, whereas identification targets and logged physical inlet signals are contemporaneous. Add the patch and coverage-audit scripts to the reproducibility code register/package if they are currently omitted. The displayed block diagram can carry a compact z^-1 annotation on the inlet path or refer directly to the timing paragraph.

## A3 — Separate the monitored compressor-map coordinate from the controller guard coordinate

**Severity: medium; verified signal-definition mismatch.**

**Location:** `control_evolution_paper.tex:175`, Chapter 2 “Acceptance is not coverage,” and the guard definition in Chapter 8.

**Evidence:** The manuscript calls the monitored coordinate `N_s/(10000 sqrt(T/288.15))`. However, `tmats_environment_data.m:13-14` records `compressor_NcMap=d.Nmech./sqrt(d.inlet_temperature_K/288.15)/10000`, using actual speed and current logged inlet temperature. `tmats_gpr_remedy_sfun.m:29-30` uses sensed speed and the delayed inlet-temperature input for the fallback guard. These signals can differ during transients. The archived map-overrun percentages therefore describe the first coordinate, while fallback can be triggered by the second.

**Required correction:** Define `N_c,plant=N/(10000 sqrt(T_in/288.15))` for monitored percentages and `N_c,guard=N_s/(10000 sqrt(T_q/288.15))` for the online trigger. Preserve the common [0.5,1.05] limits and state explicitly that matching limits do not make the signals identical. This corrects the prose/notation without changing numerical evidence.

## A4 — Expose settling-band sensitivity in the main conclusion

**Severity: medium; additional analysis strengthening claim boundaries, not a false original 0.1-rpm value.**

**Location:** Chapter 12 recovery discussion, Chapter 13 metric validity, and the response-to-referees record.

**Evidence:** The primary agent's new archived-trace reanalysis in `reviews/control_evolution_v2/metric_sensitivity.csv` retains original timing and shows a ranking reversal at the 10% load: original/retuned Poly2 recover in 0.630/0.675 s to 1 rpm, although the existing 0.1-rpm result favors the retune (1.365/0.930 s). At the 0.5-rpm band the retune still wins (1.080/0.810 s). Both remain at zero for the broad 1% band. The excess-TV ranking retuned < original < base is stable at 0.5, 1, 2, and 3 seconds for both load amplitudes.

**Requested correction:** Include the compact sensitivity table or figure and state that the retune shortens the fine tail but is not faster for every recovery band. Keep the original declared 2-s ringing and 0.1-rpm fine-recovery definitions as the primary results; report the added calculations as a read-only sensitivity analysis, not a new simulation or retuning result. This closes the earlier referee's metric-sensitivity concern more convincingly than a generic limitation paragraph.

## Disposition recommendation

Revise the manuscript and table labels for A1–A3; integrate A4 into the main text. The training/test limitations, missing two held-out environments, coverage-versus-density distinction, matched-PID attribution limit, 9250-rpm extrapolation, and peak-error penalty are already stated clearly and should be retained. Further noise, actuator, independent-engine, and fair-budget comparator studies remain future experiments, not conditions that can be marked completed by editing prose.
