"""Publishable sibling archive for the inverse-model control study."""
from pathlib import Path
from zipfile import ZipFile
import shutil,json,hashlib,csv,re

ROOT=Path(__file__).resolve().parent
REPO=ROOT/'TMATS-GPR-Poly2-Control'
STUDY=REPO/'study'
REPO.mkdir(exist_ok=True);STUDY.mkdir(exist_ok=True)
prefixes=('environment_gpr','exact_gpr','ff_lowgain','four_fixed','gpr_','inverse_gpr','virtual_fuel','r3_','poly2_','Observer_9000_9500_GPR')
support=['chirp_9000_10000_01_1Hz_60s_20260907_203056_686','ramp_selection_stretch1_20260908_214642_454','ramp_validation_stretch1_20260908_214653_124','rls_blocks_acceleration_20260909_063846_871','two_stage_rls_20260912_125027_844']
selected=[p for p in (ROOT/'results').iterdir() if p.is_dir() and (p.name.startswith(prefixes) or p.name in support)]
files=[]
for p in ROOT.iterdir():
    if p.is_file() and (p.suffix in {'.m','.mdl','.slx'} or (p.suffix in {'.py','.md','.tex'} and re.search('gpr|virtual|control_evolution|poly|covered|r3|static_ff|remed|controller_tutorial|response_to_referees',p.name,re.I))):files.append(p)
for p in selected:files.extend(f for f in p.rglob('*') if f.is_file() and 'slprj' not in f.parts and f.suffix.lower() not in {'.slxc','.pyc'})
files.extend(p for p in (ROOT/'output/pdf').iterdir() if p.is_file() and re.search('GPR|Poly|Virtual|Fixed|Environment|R3|Remed|Fuel',p.name))
files.extend(p for p in (ROOT/'reviews/control_evolution_v2').rglob('*') if p.is_file())
for p in (ROOT/'tmp').iterdir():
    if p.is_file() and p.suffix in {'.txt','.json','.mat'}:files.append(p)
for p in (ROOT/'tmp/dob').rglob('*'):
    if p.is_file() and p.suffix in {'.txt','.json','.mat'}:files.append(p)
figure_dirs=['control_evolution','fixed_controller_tutorial','environment_controller_tutorial','gpr_remedies','r3_cycle','r3_covered','r3_static_ff','r3_poly2','poly9250']
for name in figure_dirs:
    p=ROOT/'tmp/pdfs'/name
    files.extend(f for f in p.iterdir() if f.is_file() and f.suffix in {'.pdf','.tex','.json','.md'})
for p in sorted(set(files)):
    dest=STUDY/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
print('Copied',len(set(files)),'study files',flush=True)
with ZipFile(ROOT/'output/pdf/TMATS_GPR_to_Poly2_Paper_V2_LaTeX_Evidence.zip') as z:z.extractall(REPO/'paper')
for name in ['docs','tools','third_party']:(REPO/name).mkdir(exist_ok=True)
shutil.copy2(ROOT/'Research/third_party/TMATS-LICENSE.txt',REPO/'third_party/TMATS-LICENSE.txt')
shutil.copy2(ROOT/'Research/THIRD_PARTY_NOTICES.md',REPO/'THIRD_PARTY_NOTICES.md')
shutil.copy2(ROOT/'Research/tools/prepare_working_copy.py',REPO/'tools/prepare_working_copy.py')
p=REPO/'tools/prepare_working_copy.py';p.write_text(p.read_text().replace("/'tmats-gas-turbine'","/'study'"))
(REPO/'.gitignore').write_text('__pycache__/\n*.pyc\n*.slxc\nslprj/\n*.aux\n*.log\n*.toc\n*.lof\n*.lot\n*.synctex.gz\n.DS_Store\n',encoding='utf-8')
(REPO/'.gitattributes').write_text('* -text\n*.pdf binary\n*.mat binary\n*.zip binary\n*.png binary\n',encoding='utf-8')
(REPO/'requirements.txt').write_text('# Only needed for analysis and report generation; integrity checks use stdlib.\nnumpy\npandas\npypdf\npdfplumber\nPillow\n',encoding='utf-8')
(REPO/'README.md').write_text('''# T-MATS inverse GPR and Poly2 fuel-control research

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
''',encoding='utf-8')
(REPO/'docs/AI_DISCLOSURE.md').write_text('''# AI contribution and review provenance

Volkan Aran directed the research questions, controller variants, experiments and requested revisions. OpenAI Codex contributed code, simulations, numerical analysis, derivations, report text, figures and repository assembly. Three separate AI reviewer roles reused the previous industry-engineer, experienced control-theory academic and newly graduated PhD research-assistant perspectives. Their ten findings were checked and addressed in V2; they are not independent human peer review or journal acceptance.

The archive preserves deterministic simulator evidence and failed/superseded experiments. The V2 paper corrections changed exposition and added saved-trace metric sensitivity; no controller or original simulation result was changed during review. Attribution and limitations remain part of the research record.
''',encoding='utf-8')
(REPO/'docs/REPRODUCIBILITY.md').write_text('''# Reproduction levels

## 1. Integrity and saved-trace metrics

Run `python tools/verify_archive.py` from the repository root. Only Python's standard library is needed. The manifest preserves original file bytes; Git text conversion is disabled to keep hashes identical across platforms. Full-data clones are intentionally substantial because CSV and MAT trajectories are retained, including candidate searches and rejected runs.

## 2. Typeset the reviewed paper

The `paper/` directory contains the V2 source, vector figures, generated tables, evidence, and reviewer records. With a LaTeX installation providing the packages listed in its preamble:

```sh
cd paper
pdflatex -no-shell-escape control_evolution_paper.tex
pdflatex -no-shell-escape control_evolution_paper.tex
pdflatex -no-shell-escape response_to_referees.tex
```

The published PDF additionally has bookmarks/page labels/reference links added with pypdf. Those annotations are optional for reproducing the typeset content. Python analysis/report generators require the packages in requirements.txt. Do not run workspace assembly scripts directly inside `paper/code`: they expect the original study workspace layout. Existing source PDFs/tables make MATLAB unnecessary for LaTeX compilation.

## 3. Re-run controller simulations

Use MATLAB R2018b, Simulink, NASA T-MATS (the original local installation was labeled v1.3.3), and Statistics and Machine Learning Toolbox for exact GPR fitting. Shared historical identification scripts may also require System Identification Toolbox. No MATLAB, toolbox binaries, or complete upstream engine installation is redistributed here. The exact upstream commit was not recorded.

Create a separate T-MATS installation and a NEW working directory at `T-MATS/Trunk/TMATSGPT`, adjacent to `TMATS_Library` and `TMATS_Examples`. The archived helper can copy study files and relocate historical absolute text paths:

```sh
python tools/prepare_working_copy.py /path/to/T-MATS/Trunk/TMATSGPT
```

The target must not already exist; the helper never overwrites the archived study. Binary MAT/ZIP provenance paths remain historical. Read the relevant TMATS_*_USAGE.md before executing a runner. Verify tmp/*directory.txt points to the intended result set. Several runners resume prior results or write to fixed result names: create separate output locations before a genuinely fresh experiment. Do not mistake a resume for a new plant evaluation.

Entry points include `run_tmats_inverse_gpr`, `run_tmats_virtual_fuel_study`, `run_tmats_virtual_fuel_ff_study`, the UQ/UQUp runners, `run_tmats_four_fixed_comparison`, `run_tmats_environment_data`, `fit_tmats_environment_gpr`, `run_tmats_gpr_remedies`, `run_tmats_r3_cycle`, and `run_tmats_poly9250`. Setup functions load the frozen model and condition-specific power references. The latest configured model is `GasTurbine_Poly2_9250_Tuned.mdl`.

These are reconstruction instructions, not a claim that every archived historical runner was rerun during publication. The saved data were checked without retuning or executing the engine for this upload.
''',encoding='utf-8')
guide=['# Study and data guide','', 'Use the revised paper for final definitions. Do not select a dataset by timestamp alone.','', '| Directory | Role |','|---|---|']
def role(name):
    if name=='r3_covered_cycle_20260915':return 'Superseded 9400–9600 rpm attempt; box passes but hull fails.'
    if name.startswith('r3_dynamic'):return 'Superseded acceleration-input FF diagnostic; excluded from final static-FF comparison.'
    if name.startswith('r3_ambient'):return 'Broad 9025–9975 rpm cycle; large extrapolation/fallback, not in-domain validation.'
    if name.startswith('r3_covered_cycle'):return 'Final 9450–9550 rpm covered cycle; old R3 already includes static FF.'
    if name.startswith('r3_static'):return 'Explicit feedback-only versus static setpoint FF ablation.'
    if name.startswith('r3_poly2'):return 'Final covered four-way cycle with unchanged-gain Poly2 challenger.'
    if name.startswith('poly2_tune'):return 'Latest local 9250 rpm gain search, 10% target, frozen 5% amplitude check.'
    if name.startswith('poly2_inverse'):return 'Full quadratic model, coefficients and held-out fit metrics.'
    if name.startswith('gpr_remedies'):return 'R1/R2/R3 candidate search, target, 35-condition transfer and matched-PID diagnostic.'
    if name.startswith('environment_gpr'):return 'Four-input GP data, exact model, 200 held-out rows and original controller transfer.'
    if name in support:return 'Shared identification/setup dependency; earlier study provenance retained.'
    return 'Archived stage data; consult local report, acceptance columns, and main-paper chronology.'
with (REPO/'docs/DATA_CATALOG.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['directory','file_count','bytes','role'])
    for p in sorted(selected):
        fs=[q for q in (STUDY/'results'/p.name).rglob('*') if q.is_file()]
        w.writerow(['study/results/'+p.name,len(fs),sum(q.stat().st_size for q in fs),role(p.name)])
        guide.append(f'| [{p.name}](../study/results/{p.name}/) | {role(p.name)} |')
(REPO/'docs/STUDIES.md').write_text('\n'.join(guide)+'\n',encoding='utf-8')
print('Repository content assembled; verifier and manifest are finalized separately.',flush=True)
