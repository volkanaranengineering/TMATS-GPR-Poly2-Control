# T-MATS gas-turbine identification and control research

A simulation research record following identification, disturbance observers, inverse Gaussian-process control, polynomial control, and PILCO-style policy learning. Research direction: **Volkan Aran**; implementation, analysis, and writing developed with **OpenAI Codex under human direction**.

**Updated 11 October 2026.** The complete retrospective report explains the full project for an undergraduate reader. It preserves failed experiments and distinguishes prediction accuracy, controller performance, tuning, transfer, and limitations. No new simulations were added to produce the thesis or this repository update.

## Start here

- **[Complete thesis-style report — 191 pages](study/output/pdf/TMATS_Complete_Thesis.pdf)**: 41 chapters, five appendices, 48 figures, 53 tables, and a register of all 69 workspace result directories.
- **[Standalone editable LaTeX and evidence ZIP](study/output/pdf/TMATS_Complete_Thesis_LaTeX_Evidence.zip)**, also expanded in [thesis/](thesis/). Compile [TMATS_Complete_Thesis.tex](thesis/TMATS_Complete_Thesis.tex) without MATLAB.
- **[Latest DOB98 + tuned PI report](study/output/pdf/DOB98_PI_Comparison.pdf)**, [configured model](study/GasTurbine_DOB98_PI.mdl), and [usage guide](study/TMATS_DOB98_PI_USAGE.md).
- **[Latest four-window comparison video](study/output/video/DOB98_PI_Combined_Cycle_Comparison.mp4)**: common ramp and load pulse, distinct controller windows, and visible load.
- [Complete study map](docs/COMPLETE_STUDY_MAP.md), [dataset catalog](docs/DATA_CATALOG.csv), [reproduction instructions](docs/REPRODUCIBILITY.md), and [October study guide](docs/OCTOBER_STUDIES.md).

## Research progression

1. Establish numerical acceptance of the nonlinear plant. Large steps, the full chirp, and full-amplitude PRBS expose solver limits; valid prefixes and independent ramps support later identification.
2. Fit Wiener and recursive ARX acceleration models; implement RLS with ordinary blocks; use sparse lag selection to improve conditioning.
3. Correct equilibrium behavior before filtered inversion; compare DOB, LESO, UDE, and GPIO under shaft-power extraction, retaining rejected high-load runs.
4. Fit forward and inverse exact GPs. Test direct feedforward, virtual-fuel PI, decreasing/increasing uncertainty schedules, and lower fixed gains.
5. Expand the inverse to inlet temperature and pressure. Diagnose derivative problems and develop R1–R3 remedies, matched-PID checks, coverage restrictions, and static-feedforward ablations.
6. Replace the GP inverse with a full quadratic; retune PID locally at 9250 rpm and validate at a second load amplitude.
7. Learn PI gains with a frozen quadratic feedforward and a probabilistic dynamics model. Add an expected fuel-reversal penalty after aggressive gains produce excessive ringing.
8. Test frozen controllers on a five-second 9000–10000 rpm ramp. Enforce identical sensor settings and confirm exact reproduction of prior traces.
9. Combine the ramp with a 10% shaft-load pulse at seconds 10–15. Replace original PILCO in the latest comparison with a DOB identified at **9800 rpm**, then tune PI with the DOB enabled.

## Latest combined-cycle result

The reference ramps from 9000 to 10000 rpm over seconds 0–5. A common **2789.650 hp** shaft extraction is applied at seconds 10–15; recovery runs through 25.005 s. Every controller uses the same 0.05 s sensor dynamics and 0.015 s sample interval.

| Controller | Ramp RMSE (rpm) | Load/recovery RMSE (rpm) | Full RMSE (rpm) |
|---|---:|---:|---:|
| Base PI | 2.160858 | 6.815075 | 5.407708 |
| Retuned Poly2 + PID | 10.948833 | 4.415537 | 6.214481 |
| DOB98 + tuned PI | 2.458988 | 3.709882 | 3.142353 |
| Smooth PILCO | 10.251905 | 6.912781 | 7.207197 |

Source: [saved comparison CSV](study/results/dob98_pi_20261010/comparison.csv). DOB98 uses a local model identified around 9800 rpm and `(Kp, Ki) = (0.048, 0.05)`. Its original-gain ablation has full RMSE 4.546279 rpm; PI retuning reduces that to 3.142353 rpm, while worsening ramp RMSE from 1.441616 to 2.458988 rpm. [All 13 candidates](study/results/dob98_pi_20261010/tuning.csv) are preserved.

The combined cycle is a **tuning case for DOB+PI** and a transfer case for the frozen comparators. It is not an equal-budget optimization contest. The selected DOB controller also produces more load-phase fuel reversal than base PI and spends 1.139% of full-cycle samples at a fuel limit. A [frozen-gain four-second ramp / 5% pulse check](study/results/dob98_pi_20261010/heldout_validation.csv) supports limited transfer, not global robustness.

## Why the baseline sometimes wins

Base PI is strongest on actual-speed error in the no-load ramp, but it does not win all load tests. Retuned Poly2 improves tracking and ringing at 9250 rpm; original PILCO improves tracking further with much greater ringing; smooth PILCO restores smoothness at a tracking cost. Equal sensors reproduce the earlier ramp results exactly. Different responses to the same sensor lag, local training, objective mismatch, and the distinction between actual and sensed speed explain why regression accuracy alone cannot predict controller ranking.

## Videos and focused papers

| Study | Report | Video |
|---|---|---|
| Original PILCO-style FF + PI | [PDF](study/output/pdf/PILCO_Quadratic_FF_PI_Comparison.pdf) | [Four windows](study/output/video/PILCO_Four_Window_Load_Comparison.mp4) |
| Ringing-aware PILCO | [PDF](study/output/pdf/PILCO_Smooth_Ringing_Penalty.pdf) | [Four windows](study/output/video/PILCO_Smooth_Four_Window_Load_Comparison.mp4) |
| Equal-sensor no-load ramp | [PDF](study/output/pdf/PILCO_Equal_Sensors_Ramp_Comparison.pdf) | [Video](study/output/video/PILCO_90_to_100_Equal_Sensors_5s_Ramp.mp4) |
| Combined ramp and pulse | [PDF](study/output/pdf/PILCO_Combined_Ramp_Load_Cycle.pdf) | [Video](study/output/video/PILCO_Combined_Ramp_Load_Cycle.mp4) |
| DOB98 + retuned PI | [PDF](study/output/pdf/DOB98_PI_Comparison.pdf) | [Video](study/output/video/DOB98_PI_Combined_Cycle_Comparison.mp4) |

Videos animate recorded signals. Rotor rotation is visually scaled; it is not a blade-resolved simulation. Removing original PILCO from the latest lineup does not remove its historical evidence.

## Archive layout and earlier work

- `study/`: models, controller and analysis source, saved trajectories, results, reports, and videos for this repository's studies.
- `thesis/`: complete standalone LaTeX report, figures, tables, compact evidence, and source hashes.
- `paper/`: preserved September GPR-to-Poly2 V2 manuscript and AI referee-role response.
- `docs/`: study guides, catalogs, disclosure, and reproduction instructions.
- `tools/verify_archive.py`: file-integrity checks and replay of selected saved Poly2 metrics; no simulation.

The earlier identification and observer raw archive remains in the companion [Research repository](https://github.com/volkanaranengineering/Research/tree/main/tmats-gas-turbine). The complete study map identifies which archive contains each directory. The thesis covers both archives; 69 directories are **not** claimed to be 69 independent experiments or all duplicated here.

The [68-page September V2 paper](study/output/pdf/TMATS_GPR_to_Poly2_Comprehensive_Paper_V2.pdf), [referee-role response](study/output/pdf/TMATS_GPR_to_Poly2_Response_to_Referees_V2.pdf), and [previous README](docs/README_2026-09-15.md) remain available. AI referee-role review is not independent human peer review.

## Reproduction and limits

Run `python tools/verify_archive.py` for integrity and saved-data checks. Typeset the thesis from `thesis/` with `pdflatex -no-shell-escape TMATS_Complete_Thesis.tex` three times. Simulation requires a separate compatible MATLAB/Simulink/T-MATS installation; consult the reproduction guide before running historical scripts. Some write to fixed output folders.

No hardware qualification, robust-stability guarantee, noise robustness, or measured fuel-economy benefit is claimed. Fuel excess variation measures command reversal, not fuel consumed. Numerical convergence, compressor-map coverage, learned-model coverage, and control performance are separate checks. See [AI disclosure](docs/AI_DISCLOSURE.md) and [third-party notices](THIRD_PARTY_NOTICES.md).
