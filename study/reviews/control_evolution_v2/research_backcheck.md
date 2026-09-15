# Research-assistant referee: V2 back-check

Reviewed `control_evolution_paper_v2.tex`, V2 assembly, sensitivity script/tables, and source trajectory `results/poly2_tune9250_20260915/candidate_34.csv`.

- **A1: closed.** Substantive definition corrected in Chapter 2: fixed-load slew is limited to six post-edge windows, while cycle slew spans the scored cycle. The final assembled tuning table now reads “Edge-window peak slew,” and `revise_control_evolution_paper.py:105` preserves this label when rebuilt. Both locations were verified. No numerical change was needed.
- **A2: closed.** The main text now specifies the one-sample inlet T/P delay, 288.15 K/99.298 kPa initialization, physical conversion, and contemporaneous offline identification values. V2 assembly includes the inlet patch and coverage-audit code.
- **A3: closed.** The manuscript now separates actual-speed/current-temperature logged map coordinates from sensed-speed/delayed-temperature guard coordinates. It preserves the common limits without treating the signals as identical.
- **A4: closed.** The main results and critical discussion now describe the 1-rpm recovery ranking reversal, retain the original declared metrics, and identify sensitivity results as reanalysis of existing traces.

## Independent numerical check

I did not execute or reuse the sensitivity script. Using Python standard-library CSV reading and scalar loops, I independently reconstructed all four excess-TV window totals and all four worst persistent recovery values for the retuned 10% trajectory. Each matched `metric_sensitivity.csv` within 1e-10:

| Quantity | Recomputed value |
|---|---:|
| Ringing, 0.5 s windows | 1.0555721975189405 |
| Ringing, 1 s windows | 1.2946330215323796 |
| Ringing, 2 s windows | 1.2990426121848597 |
| Ringing, 3 s windows | 1.2990674213812592 |
| Recovery, 0.1 rpm | 0.9300000000000068 s |
| Recovery, 0.5 rpm | 0.8100000000000023 s |
| Recovery, 1 rpm | 0.6750000000000114 s |
| Recovery, 1% speed (92.5 rpm) | 0 s |

The original event starts, end-exclusive persistence intervals, and inclusive post-edge ringing windows were preserved. No new simulation or gain selection was performed. Remaining external-validation experiments are appropriately left open.
