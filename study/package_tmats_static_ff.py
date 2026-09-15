from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,hashlib,json
root=Path(__file__).resolve().parent;run=root/'results/r3_static_ff_20260915';work=root/'tmp/pdfs/r3_static_ff';out=root/'output/pdf'
shutil.copy2(work/'R3_Static_FF.pdf',out/'TMATS_R3_Static_FF.pdf')
with ZipFile(out/'TMATS_R3_Static_FF_LaTeX.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(work.iterdir()):
  if p.suffix in ['.tex','.pdf','.csv']:z.write(p,p.name)
files=set()
for pattern in ['*static_ff*.m','*static_ff*.py','tmats_r3_feedback_only_sfun.m','tmats_gpr_remedy_sfun.m','tmats_gp_mean_gradient.m','run_tmats_r3_cycle.m','report_tmats_r3_cycle.m','tmats_r3_cycle_setup.m','tmats_r3_covered_cycle_setup.m','audit_tmats_cycle_coverage.m','GasTurbine_FFCompare_*.mdl','TMATS_R3_STATIC_FF_USAGE.md']:
 files.update(root.glob(pattern))
files.update(run.glob('*.csv'));files.update(run.glob('*.mat'))
with ZipFile(out/'TMATS_R3_Static_FF_Models_Results.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,p.relative_to(root))
 z.writestr('SHA256_manifest.json',json.dumps({str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},indent=2))
print('Packaged',len(files),'files; original workspace dependencies required.')
