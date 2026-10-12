"""Publish the reviewed V2 artifact and navigation locally; no simulation or git push."""
from pathlib import Path
import hashlib,json,re,shutil,zipfile
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'output/pdf/tmats_masters_thesis_v2_source'
REPO=ROOT/'TMATS-GPR-Poly2-Control'
checks=json.loads((SRC/'release_checks.json').read_text())
assert checks['visual_review']=='passed'
pages=checks['pages']
pdf=ROOT/'output/pdf/TMATS_Masters_Thesis_V2.pdf'
assert hashlib.sha256(pdf.read_bytes()).hexdigest()==checks['pdf_sha256']

# Retain the dependency closure for compilation, rather than unused V1 manuscripts.
needed=set()
def visit(name):
    name=name if name.endswith('.tex') else name+'.tex'
    if name in needed:return
    p=SRC/name
    assert p.is_file(),name
    needed.add(name)
    for dep in re.findall(r'\\input\{([^}]+)\}',p.read_text(encoding='utf-8')):visit(dep)
visit('TMATS_Masters_Thesis_V2.tex')
readme=f'''# T-MATS master's revision V2

This is the standalone editable source for the {pages}-page revised report. It contains 15 thematic chapters, six appendices, 48 numbered figures and 53 numbered tables, plus unnumbered synthesis and examination-response tables.

Compile from this directory three times:

```sh
pdflatex -no-shell-escape TMATS_Masters_Thesis_V2.tex
```

No MATLAB, new simulations, fitting, tuning or online downloads are needed when the LaTeX packages are installed. The supplied PDF has navigation bookmarks added during release checking; typesetting alone reproduces the content but does not add those postprocessed bookmarks.

The report addresses the Version 1 jury-style assessment through a focused question, literature comparison, evidence-role ledger, attribution analysis and point-by-point response in Appendix A. Missing equal-budget comparisons, robustness tests and a human oral defence are not claimed to have been completed. This is not an institutional acceptance decision.

`evidence_manifest.json` preserves the original workspace evidence provenance. `v2_revision_manifest.json` records this package's file hashes. `release_checks.json` records the final PDF checks. The evidence, data and review directories are supporting historical material; references there to an earlier V2 concern the September paper, not this master's revision. The complete simulation installation and all raw workspace data are not included in this document bundle.

The workspace assembly, release and packaging scripts are archived separately under `study/`; they expect the original workspace layout and are not needed to compile this source package. Version 1 is preserved in `thesis/` and as a separate PDF.
'''
(SRC/'README.md').write_text(readme,encoding='utf-8')

selected=[]
for p in sorted(SRC.rglob('*')):
    if not p.is_file():continue
    rel=p.relative_to(SRC)
    if rel.parts[0] in {'evidence','data','reviews','review_traces'}:
        selected.append(p);continue
    if len(rel.parts)>1:continue
    if p.name in needed or p.suffix.lower() in {'.png','.jpg','.jpeg'} or p.suffix.lower()=='.pdf' and not p.name.startswith('TMATS_'):
        selected.append(p)
    elif p.name in {'README.md','release_checks.json','evidence_manifest.json','study_inventory.json'}:
        selected.append(p)

rev={'edition':'Masters revision V2','source_baseline_commit':'1dc32c7','jury_record_commit':'b16e59e','original_pdf_sha256':hashlib.sha256((ROOT/'output/pdf/TMATS_Complete_Thesis.pdf').read_bytes()).hexdigest(),'pdf_sha256':checks['pdf_sha256'],'new_simulations':0,'new_fits':0,'new_tuning_runs':0,'files':{p.relative_to(SRC).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in selected}}
(SRC/'v2_revision_manifest.json').write_text(json.dumps(rev,indent=2),encoding='utf-8')
selected.append(SRC/'v2_revision_manifest.json')
archive=ROOT/'output/pdf/TMATS_Masters_Thesis_V2_LaTeX_Evidence.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in selected:z.write(p,Path('tmats_masters_thesis_v2_source')/p.relative_to(SRC))
target=REPO/'thesis_v2'
target.mkdir(exist_ok=True)
for p in selected:
    dest=target/p.relative_to(SRC);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
for p in [pdf,archive]:shutil.copy2(p,REPO/'study/output/pdf'/p.name)
for name in ['build_masters_thesis_v2.py','finalize_masters_thesis_v2.py','package_masters_thesis_v2.py']:
    shutil.copy2(ROOT/name,REPO/'study'/name)
shutil.copytree(ROOT/'thesis_v2_revision',REPO/'study/thesis_v2_revision',dirs_exist_ok=True)

md=REPO/'README.md'
s=md.read_text(encoding='utf-8')
s=s.replace('The complete retrospective report explains the full project for an undergraduate reader.', 'The original retrospective report preserves the complete chronology; the new master\'s revision V2 reorganizes the evidence around a focused research question and addresses the jury-style assessment.')
insert=f'''- **[Master's thesis-style report V2 — {pages} pages](study/output/pdf/TMATS_Masters_Thesis_V2.pdf)**: revised research question, literature position, evidence-role ledger, central ablation analysis, and point-by-point jury response. No new simulations.
- **[V2 standalone LaTeX and evidence ZIP](study/output/pdf/TMATS_Masters_Thesis_V2_LaTeX_Evidence.zip)**, also expanded in [thesis_v2/](thesis_v2/). See [revision response](docs/MASTERS_V2_REVISION_RESPONSE.md).
'''
s=s.replace('## Start here\n\n','## Start here\n\n'+insert,1)
s=s.replace('The [11 October 2026 jury-style examination]', 'The Version 1 [11 October 2026 jury-style examination]',1)
needle='## Research progression'
addition='''## What changed in the master’s revision

Version 2 consolidates the chronological material into **15 thematic chapters and six appendices**. It defines a comparative engineering contribution without claiming a new GP, DOB, or PILCO theory. The added evidence ledger distinguishes model fitting, gain selection, frozen transfer and implementation checks; the synthesis makes the matched-PID, feedforward, polynomial-substitution, sensor and original-gain DOB evidence central.

Appendix A answers each examination concern. Equal-budget PI tuning and broader robustness experiments remain unperformed, so claims are narrowed to the tested configurations. An independent oral defence remains a human examination requirement. **V2 is a revised report, not a new acceptance verdict.** The original thesis and jury assessment remain unchanged.

'''
s=s.replace(needle,addition+needle,1)
s=s.replace('- `thesis/`: complete standalone LaTeX report, figures, tables, compact evidence, and source hashes.', '- `thesis/`: preserved Version 1 standalone LaTeX report and evidence.\n- `thesis_v2/`: standalone master\'s revision, figures, tables, evidence, revision manifest and release checks.')
s=s.replace('Typeset the thesis from `thesis/` with `pdflatex -no-shell-escape TMATS_Complete_Thesis.tex` three times.', 'Typeset the revised report from `thesis_v2/` with `pdflatex -no-shell-escape TMATS_Masters_Thesis_V2.tex` three times. Version 1 remains compilable from `thesis/` using `TMATS_Complete_Thesis.tex`.')
md.write_text(s,encoding='utf-8')

response=f'''# Master's revision V2: response and remaining limits

The [{pages}-page revised report](../study/output/pdf/TMATS_Masters_Thesis_V2.pdf) addresses the [Version 1 jury-style examination](THESIS_JURY_EXAMINATION.md). Appendix A contains the complete point-by-point response and defence questions.

| Examination requirement | Change | Status |
|---|---|---|
| Focused research question | One primary question, four subsidiary questions and bounded contributions C1–C4 | Addressed in Chapters 1 and 14–15 |
| Literature and novelty | Primary-source comparison; established methods separated from application evidence | Addressed in Chapter 2; penalty originality remains unestablished |
| Training/selection/validation separation | Study-by-study evidence-role ledger | Addressed in Chapter 3 |
| Fairness and attribution | Existing ablations made central; unequal tuning explicitly acknowledged | Claims narrowed; equal-budget PI-only search not performed |
| Local model versus broad control task | DOB98 identification range stated alongside the wider ramp | Claims narrowed; no global error bound |
| Verification versus robustness | Algebra and GP moment checks distinguished from physical validation | Claims narrowed; new robustness tests not performed |
| PILCO and ringing claims | Offline two-gain adaptation named explicitly; ringing repair distinguished from baseline dominance | Addressed in Chapters 2, 11 and 14 |
| Independent mastery | Disclosure and defence questions | Requires human examination; not certified by the document |

The report preserves detailed derivations and all stages of the project narrative in a thematic structure. No new plant simulation, identification fit, controller search or Monte Carlo run was added. The original PDF, source and jury examination remain unchanged. Version 2 does not claim an institutional acceptance decision.

## Deliverables and checks

- [PDF](../study/output/pdf/TMATS_Masters_Thesis_V2.pdf)
- [Editable source](../thesis_v2/README.md)
- [Portable source/evidence ZIP](../study/output/pdf/TMATS_Masters_Thesis_V2_LaTeX_Evidence.zip)
- [PDF release checks](../thesis_v2/release_checks.json)
- [Revision manifest](../thesis_v2/v2_revision_manifest.json)

The PDF has 15 main chapters, six appendices, 48 numbered figures, 53 numbered tables and {checks['bookmarks']} navigation bookmarks. All pages were rendered and visually reviewed; the final LaTeX log has no overfull boxes or undefined references, and the extracted text has no out-of-page spans. The hashes preserve artifact identity, not physical validation of the simulations.
'''
(REPO/'docs/MASTERS_V2_REVISION_RESPONSE.md').write_text(response,encoding='utf-8')
repro=REPO/'docs/REPRODUCIBILITY.md'
r=repro.read_text(encoding='utf-8')
r+='''\n## 6. Master's revision V2\n\nCompile `TMATS_Masters_Thesis_V2.tex` three times from `thesis_v2/` with `pdflatex -no-shell-escape`. All figures and tables are included. The PDF release checker adds bookmarks after typesetting. See `thesis_v2/README.md`, `release_checks.json`, and `v2_revision_manifest.json`. The source/evidence ZIP is a portable document bundle, not a complete simulation installation. The older September paper also has a V2; its filenames and reproduction instructions remain historical and distinct. No simulation or tuning is needed to reproduce this report.\n'''
repro.write_text(r,encoding='utf-8')
change=REPO/'docs/CHANGELOG_2026-10-11.md'
c=change.read_text(encoding='utf-8')
c+='''\n## Jury-addressed master's revision V2\n\n- Preserved the original thesis and jury-style examination.\n- Added a revised thematic thesis, standalone LaTeX/evidence package and point-by-point response.\n- Clarified research scope, literature position, data roles, controller attribution and remaining examination requirements.\n- Updated README and reproduction instructions; refreshed the archive manifest, including the jury document and README changes.\n- No new simulations, identification fits, controller tuning or Monte Carlo experiments.\n'''
change.write_text(c,encoding='utf-8')

for md in [REPO/'README.md',REPO/'docs/MASTERS_V2_REVISION_RESPONSE.md',REPO/'docs/THESIS_JURY_EXAMINATION.md']:
    for link in re.findall(r'\]\(([^)]+)\)',md.read_text(encoding='utf-8')):
        if not link.startswith(('http','#')):assert (md.parent/link.split('#')[0]).exists(),(md,link)
records=[]
for p in sorted(REPO.rglob('*')):
    if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts or p==REPO/'manifest.json':continue
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    records.append({'path':p.relative_to(REPO).as_posix(),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
(REPO/'manifest.json').write_text(json.dumps({'format':1,'description':'Published-file byte hashes; excludes this manifest, Git internals and Python caches. Includes masters revision V2 and jury assessment; no new simulations.','files':records},indent=2),encoding='utf-8')
print(json.dumps({'pdf_pages':pages,'zip_bytes':archive.stat().st_size,'source_files':len(selected),'archive_files':len(records)},indent=2))
