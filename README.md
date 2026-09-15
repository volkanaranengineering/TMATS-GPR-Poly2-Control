# T-MATS inverse GPR and Poly2 fuel-control research

A complete simulation research record of fuel control evolving from inverse Gaussian-process PI to derivative-normalized R3 and retuned quadratic-polynomial PID. Research direction: **Volkan Aran**; code, analysis, and writing developed with **OpenAI Codex under human direction**.

This is a separate companion to the earlier [DOB and observer studies](https://github.com/volkanaranengineering/Research). It preserves the learned models, full saved trajectories, gain searches, successful and rejected cases, reports, and three AI referee-role reviews through **15 September 2026**.

## Start here

- **[Revised comprehensive paper V2, 68 pages](study/output/pdf/TMATS_GPR_to_Poly2_Comprehensive_Paper_V2.pdf)**: research problem, derivations, block diagrams, time-domain zooms, 21 numerical tables, limitations, and five takeaways.
- **[Response to the three referees, 5 pages](study/output/pdf/TMATS_GPR_to_Poly2_Response_to_Referees_V2.pdf)**: ten findings, corrections, and back-checks.
- [Standalone LaTeX source and evidence package](study/output/pdf/TMATS_GPR_to_Poly2_Paper_V2_LaTeX_Evidence.zip), also expanded under [paper/](paper/).
- [Canonical studies and dataset guide](docs/STUDIES.md), [complete data catalog](docs/DATA_CATALOG.csv), and [reproduction instructions](docs/REPRODUCIBILITY.md).
- [Latest 9250 rpm tuning report](study/output/pdf/TMATS_Poly2_9250_Tuning.pdf) and [configured model](study/GasTurbine_Poly2_9250_Tuned.mdl).

## Controller development

1. Exact two-input inverse GPR: speed and acceleration to nominal fuel, with 600 training and 100 held-out observations.
2. Dual inverse-query virtual-fuel PI, direct GPR feedforward, and separate gain retuning.
3. Decreasing and increasing posterior-SD gain schedules; fixed lower gains to reduce fuel ringing.
4. Four-way fixed-controller comparisons: base PI, base PI + GPR FF, inverse PI, and inverse PI + GPR FF.
5. Four-input inverse including inlet temperature and pressure: 1400 training observations over 35 altitude/ISA combinations, with 200 held-out observations covering 33 conditions.
6. Remedies R1, R2, R3; derivative normalization, separate acceleration feedback, guarded fallback, and matched-PID diagnosis.
7. Repeated acceleration/deceleration cycles under changing ambient conditions, followed by box/hull coverage restriction and static-FF ablation.
8. Full quadratic (15-term) inverse using the same data and R3 gains, then a separate local PID retune at 9250 rpm, sea level, ISA 0.

## Selected results and their limits

The latest frozen-model gain change is `(Kp, Ki, Kd): (0.025, 0.1, 0.002) -> (0.025, 0.14, 0.00125)`.

At **9250 rpm / sea level / ISA 0 / 10% shaft-load pulses**:

| Metric | Base PI | Original Poly2 | Retuned Poly2 |
|---|---:|---:|---:|
| Actual-speed RMSE (rpm) | 2.420904 | 1.665802 | 1.546141 |
| Peak speed error (rpm) | 21.40623 | 14.11331 | 15.82465 |
| Six-window fuel excess variation (lbm/s) | 2.070228 | 1.696797 | 1.299043 |
| Worst recovery to 0.1 rpm (s) | 2.475 | 1.365 | 0.930 |
| Worst recovery to 1% speed (s) | 0 | 0 | 0 |
| Peak edge-window fuel slew (lbm/s²) | 4.817496 | 8.718722 | 7.273621 |

Source: [full tuning scores](study/results/poly2_tune9250_20260915/tuning_scores.csv), candidates 0, 1, and 34. A separate [5% amplitude test](study/results/poly2_tune9250_20260915/validation_summary.csv) uses frozen gains.

- Retuning improves RMSE/ringing relative to original Poly2 by approximately **7.2% / 23.4%**, while increasing peak speed error by **12.1%**.
- Relative to base PI, retuned Poly2 reduces RMSE/ringing by **36.1% / 37.3%**, but increases peak edge-window fuel slew by **51.0%**. Fewer fuel reversals do not imply lower peak actuator-rate demand.
- Ringing ordering survives 0.5/1/2/3 s window checks. At 10% load, the recovery ranking reverses at the **1 rpm** band: original Poly2 0.630 s, retuned 0.675 s. All methods remain inside the broad 1% band, explaining zero recovery there.
- The 9250 rpm point is **14.23 rpm below** the original training-speed minimum. These local gains have not been revalidated across the earlier environmental grid or covered cycle.
- Earlier R3 improves paired RMSE/ringing on all 35 load-grid conditions, but only 25 pairs are map-clean, and a matched PID nearly reproduces its target result. On the covered moving-reference cycle, base PI still has lower overall RMSE.

Do not pool load-edge excess variation with cycle-segment reversal: their windows differ. Numerical acceptance, map range, GP support, and closed-loop robustness are separate questions. Consult the paper for exact signal timing, anti-windup gates, and fallback semantics.

## Layout

```text
study/                  Original relative workspace layout
  *.m, *.mdl, *.py       Controller, setup, runner, and report sources
  results/              Full saved experiment data, fitted models, searches and figures
  output/pdf/           Study reports, V1/V2 papers and packaged snapshots
  reviews/              Three referee-role reports, back-checks and sensitivity evidence
  tmp/                  Reproduction pointers, reference caches and vector figure sources
paper/                  Self-contained V2 LaTeX typesetting bundle
docs/                   Study index, data catalog, reproduction and AI disclosure
tools/                  Standard-library integrity/metric check and relocation helper
manifest.json           Sizes and SHA-256 hashes of the published files
third_party/            Preserved NASA T-MATS license
```

Earlier shared MATLAB scripts/models are retained where they support the setup and comparator lineage. Full earlier observer analysis is in the companion repository. Superseded broad/coverage/FF diagnostics are preserved and labeled in the study guide. Runtime caches, installed dependencies, private authentication material, and downloaded literature are not part of this archive.

## Verify or reproduce

From this repository root, with Python 3.10 or newer:

```sh
python tools/verify_archive.py
```

This checks file hashes and independently recomputes latest base/original/retuned RMSE and ringing from CSV. It does not execute MATLAB. For typesetting, run `pdflatex control_evolution_paper.tex` twice in `paper/`; the response source is `response_to_referees.tex`. For simulations, use a separate working copy placed at `T-MATS/Trunk/TMATSGPT` and follow [the reproduction guide](docs/REPRODUCIBILITY.md). MATLAB R2018b, Simulink, relevant toolboxes and the local T-MATS v1.3.3 installation are external dependencies.

## Attribution and research status

NASA T-MATS is the underlying simulation toolbox; NASA has not endorsed this work. The three referee roles are AI-assisted technical reviews, **not independent human peer review**. No hardware, embedded timing, physical actuator, or robustness certification is claimed. See [AI disclosure](docs/AI_DISCLOSURE.md) and [third-party notices](THIRD_PARTY_NOTICES.md). No new blanket license is assigned to the mixed research material.
