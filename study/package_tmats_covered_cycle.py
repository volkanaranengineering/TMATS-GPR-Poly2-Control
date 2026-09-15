from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,hashlib,json
root=Path(__file__).resolve().parent;run=root/'results/r3_covered_cycle_20260915_final';work=root/'tmp/pdfs/r3_covered';out=root/'output/pdf'
shutil.copy2(work/'R3_Covered_Cycle.pdf',out/'TMATS_R3_Covered_Cycle.pdf')
with ZipFile(out/'TMATS_R3_Covered_Cycle_LaTeX.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(work.iterdir()):
  if p.suffix in ['.tex','.pdf','.csv']:z.write(p,p.name)
files=set()
for pattern in ['*covered_cycle*.m','*covered_cycle*.py','*r3_cycle*.m','verify_tmats_r3_cycle.py','audit_tmats_cycle_coverage.m','GasTurbine_Covered_*.mdl','TMATS_R3_COVERED_CYCLE_USAGE.md']:
 files.update(root.glob(pattern))
files.update(run.glob('*.csv'));files.update(run.glob('*.mat'))
with ZipFile(out/'TMATS_R3_Covered_Cycle_Models_Results.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,p.relative_to(root))
 z.writestr('SHA256_manifest.json',json.dumps({str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},indent=2))
print('Packaged',len(files),'files; original workspace dependencies required.')
