"""Package the finished report and update the existing research checkout."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,shutil,re,csv,hashlib
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'output/pdf/tmats_complete_thesis_source'
REPO=ROOT/'TMATS-GPR-Poly2-Control'
qa=json.loads((SRC/'release_checks.json').read_text())
qa['visual_review']='All 191 pages rendered with Poppler and inspected in 16 contact sheets; detailed equation page inspected at 130 dpi. Figure-heading placement and Markdown emphasis corrected before final render.'
(SRC/'release_checks.json').write_text(json.dumps(qa,indent=2))
shutil.copy2(ROOT/'build_complete_thesis.py',SRC/'build_complete_thesis.py')
shutil.copy2(ROOT/'finalize_complete_thesis.py',SRC/'finalize_complete_thesis.py')
# Exclude compiler intermediates and historical unused standalone main files.
excluded={'control_evolution_paper.tex','response_to_referees.tex','control_evolution_references.tex'}
def include(p):
    return p.is_file() and p.suffix not in {'.aux','.log','.toc','.lof','.lot'} and not p.name.startswith('compile-') and p.name not in excluded and p.name!='TMATS_Complete_Thesis.pdf'
archive=ROOT/'output/pdf/TMATS_Complete_Thesis_LaTeX_Evidence.zip'
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
    for p in SRC.rglob('*'):
        if include(p):z.write(p,p.relative_to(SRC).as_posix())
with ZipFile(archive) as z:assert z.testzip() is None
def copy(p,d):
    d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
for p in SRC.rglob('*'):
    if include(p):copy(p,REPO/'thesis'/p.relative_to(SRC))
for p in [ROOT/'output/pdf/TMATS_Complete_Thesis.pdf',archive]:copy(p,REPO/'study/output/pdf'/p.name)
for p in ROOT.iterdir():
    if p.is_file() and p.suffix.lower() in {'.py','.m','.mdl','.tex','.md'} and re.search('pilco|ramp90|combined|equalsensor|dob98|thesis',p.name,re.I):copy(p,REPO/'study'/p.name)
for folder in (ROOT/'results').iterdir():
    if folder.is_dir() and re.search('pilco|dob98',folder.name):shutil.copytree(folder,REPO/'study/results'/folder.name,dirs_exist_ok=True)
for p in (ROOT/'output/pdf').iterdir():
    if p.is_file() and p.suffix=='.pdf' and re.search('PILCO|DOB98',p.name):copy(p,REPO/'study/output/pdf'/p.name)
    elif p.is_dir() and re.search('pilco|ramp90|combined|dob98',p.name):
        for f in p.iterdir():
            if f.suffix in {'.tex','.pdf'}:copy(f,REPO/'study/output/pdf'/p.name/f.name)
for p in (ROOT/'output/video').glob('*.mp4'):copy(p,REPO/'study/output/video'/p.name)
oldreadme=REPO/'docs/README_2026-09-15.md'
if not oldreadme.exists():copy(REPO/'README.md',oldreadme)
readme='''# T-MATS gas-turbine identification and control research

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
'''
(REPO/'README.md').write_text(readme,encoding='utf8')
(REPO/'requirements.txt').write_text('# Analysis and document/video generation only; integrity checks use stdlib.\nnumpy\nscipy\npandas\nmatplotlib\npypdf\npdfplumber\nPyMuPDF\nPillow\nimageio\nimageio-ffmpeg\n',encoding='utf8')
rep=REPO/'docs/REPRODUCIBILITY.md';s=rep.read_text(encoding='utf8')
s=s.replace('The latest configured model is `GasTurbine_Poly2_9250_Tuned.mdl`.','The September configured model is `GasTurbine_Poly2_9250_Tuned.mdl`; the latest October model is `GasTurbine_DOB98_PI.mdl`.')
s+='''
## 4. Complete retrospective thesis (October edition)

The complete editable source is in `thesis/`. Run `pdflatex -no-shell-escape TMATS_Complete_Thesis.tex` three times from that directory. Figures and tables are already included; no MATLAB, fitting, optimization, or simulation is needed. The supplied PDF additionally has navigation bookmarks. `thesis/release_checks.json` records the final PDF checks and `thesis/evidence_manifest.json` records workspace-relative source hashes.

The assembly scripts preserve the original workspace paths and expect the full project, including the September generated assets and earlier reports. They are provenance tools, not prerequisites for standalone typesetting. Full raw earlier observer datasets are in the companion Research repository; consult COMPLETE_STUDY_MAP.md.

## 5. October studies

Read OCTOBER_STUDIES.md and the respective usage guide. The archived chronology includes learning or fitting scripts, plant runners, and artifact builders. Do not execute the entire chronology merely to view saved results. PILCO-style policy optimization is offline and local; its mathematical planning model differs from the nonlinear plant validation. DOB98 identification is around 9800 rpm, not a statement of 98% fit. The 13-case PI search uses the combined cycle; its independent check changes the ramp duration and pulse amplitude.

This repository update does not rerun any of those experiments. It copies their existing data and verifies the published archive.
'''
rep.write_text(s,encoding='utf8')
octguide='''# October studies: chronology and evidence

All results below predate the complete-thesis publication. No new plant simulation was added for the report or repository update.

| Directory | Purpose and interpretation |
|---|---|
| pilco_quadratic_pi_20261010 | Offline GP moment-matching policy search with a frozen quadratic FF; improves RMSE while increasing ringing. |
| pilco_smooth_20261010 | Expected excess-TV penalty, ten weights including refinements, 10% selection and frozen 5% check. |
| pilco_ramp90_100_5s_20261010 | Frozen-controller no-load 9000–10000 rpm, five-second ramp. |
| pilco_ramp90_equal_sensor_20261010 | Explicit common-sensor settings and wiring audit; reruns reproduce prior traces exactly. |
| pilco_combined_cycle_20261010 | Five-second ramp plus 10% common-power load at seconds 10–15; original four controllers. |
| dob98_pi_20261010 | Separate 9800-rpm local identification, causal filtered inverse, 13-case PI tuning, revised comparison, and held-out scenario. |

Each folder is under `study/results/`. JSON records define the protocol and selected policy; CSV files preserve metrics and time histories, and MAT files retain native data. Consult the full thesis for equations and limitations.

The October video builders use the existing recorded trajectories. Their imports may execute analysis or artifact creation; they are not needed to read the PDF or play a saved MP4. Learning scripts and MATLAB batch runners can overwrite fixed study output names, so reproduce in a separate working copy.
'''
(REPO/'docs/OCTOBER_STUDIES.md').write_text(octguide,encoding='utf8')
inventory=json.loads((SRC/'study_inventory.json').read_text())
mapping=['# Complete project study map','', 'All 69 direct workspace result directories are listed, including empty pilots and derived reports. Local links point to this repository; earlier raw studies link to the companion Research archive. Compact report evidence is also preserved in `thesis/evidence/`.','', '| Workspace directory | Files | Archive location |','|---|---:|---|']
for item in inventory:
    d=item['directory'];local=REPO/'study/results'/d
    if local.exists():link=f'[This repository](../study/results/{d}/)'
    elif (ROOT/'Research/tmats-gas-turbine/results'/d).exists():link=f'[Research archive](https://github.com/volkanaranengineering/Research/tree/main/tmats-gas-turbine/results/{d})'
    elif item['file_count']==0:link='Empty local pilot; no empirical files'
    else:link='Workspace-only historical record; compact evidence is indexed in the thesis package'
    mapping.append(f'| `{d}` | {item["file_count"]} | {link} |')
(REPO/'docs/COMPLETE_STUDY_MAP.md').write_text('\n'.join(mapping)+'\n',encoding='utf8')
catalog=[]
for p in sorted((REPO/'study/results').iterdir()):
    if p.is_dir():
        files=[f for f in p.rglob('*') if f.is_file()]
        catalog.append({'directory':p.relative_to(REPO).as_posix(),'file_count':len(files),'bytes':sum(f.stat().st_size for f in files),'role':'October study; see OCTOBER_STUDIES.md' if re.search('pilco|dob98',p.name) else 'Historical study; see STUDIES.md and complete thesis'})
with (REPO/'docs/DATA_CATALOG.csv').open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=['directory','file_count','bytes','role']);w.writeheader();w.writerows(catalog)
studyguide=REPO/'docs/STUDIES.md'
g=studyguide.read_text(encoding='utf8');g=g.replace('Use the revised paper for final definitions.','Use the complete thesis and the revised September paper for phase-specific definitions.')
if 'October extension' not in g:g+='\n## October extension\n\nSee [October studies](OCTOBER_STUDIES.md) for PILCO, ringing penalties, common-sensor ramps, combined cycles, and DOB98. [Complete study map](COMPLETE_STUDY_MAP.md) covers all 69 workspace directories across both repositories.\n'
studyguide.write_text(g,encoding='utf8')
(REPO/'docs/CHANGELOG_2026-10-11.md').write_text('''# 11 October 2026 archive update

- Added the 191-page retrospective thesis, standalone LaTeX, compact evidence, and PDF release checks.
- Added the six October study directories, their MATLAB/Python sources and configured model copies.
- Added seven existing comparison videos and the six focused October PDFs.
- Rewrote the main README around the complete project and latest DOB98 result; preserved the September README.
- Updated requirements, reproduction guidance, dataset catalog, and complete cross-repository study map.
- Preserved existing September evidence and AI review records.
- No new simulation, model fitting, or controller tuning was performed for this update.
''',encoding='utf8')
# Check relative links in newly edited navigation documents.
for md in [REPO/'README.md',REPO/'docs/COMPLETE_STUDY_MAP.md',REPO/'docs/STUDIES.md']:
    for target in re.findall(r'\]\(([^)]+)\)',md.read_text(encoding='utf8')):
        if not target.startswith(('http','#')):assert (md.parent/target.split('#')[0]).exists(),(md,target)
manifest=[]
for p in sorted(REPO.rglob('*')):
    if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts or p.name=='manifest.json' and p.parent==REPO:continue
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    manifest.append({'path':p.relative_to(REPO).as_posix(),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
(REPO/'manifest.json').write_text(json.dumps({'format':1,'description':'Published-file byte hashes; excludes this manifest, Git internals, and Python caches. Existing simulation evidence preserved; October archive update adds no new simulations.','files':manifest},indent=2),encoding='utf8')
print(json.dumps({'source_zip':str(archive),'zip_bytes':archive.stat().st_size,'repository_files':len(manifest),'catalog_directories':len(catalog),'largest_file_bytes':max(x['bytes'] for x in manifest)},indent=2))
