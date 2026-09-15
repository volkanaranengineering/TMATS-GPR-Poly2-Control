# Reproduction levels

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
