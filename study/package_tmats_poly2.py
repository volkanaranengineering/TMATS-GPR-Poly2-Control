from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,hashlib,json
root=Path(__file__).resolve().parent;run=root/'results/r3_poly2_challenger_20260915';fit=root/'results/poly2_inverse_20260915';work=root/'tmp/pdfs/r3_poly2';out=root/'output/pdf'
shutil.copy2(work/'R3_Poly2_Challenger.pdf',out/'TMATS_R3_Poly2_Challenger.pdf')
with ZipFile(out/'TMATS_R3_Poly2_LaTeX.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(work.iterdir()):
  if p.suffix in ['.tex','.pdf','.csv','.json']:z.write(p,p.name)
files=set()
for pattern in ['*poly2*.m','*poly2*.py','run_tmats_r3_cycle.m','tmats_r3_cycle_setup.m','tmats_r3_covered_cycle_setup.m','report_tmats_r3_cycle.m','report_tmats_static_ff.m','verify_tmats_static_ff.py','audit_tmats_cycle_coverage.m','tmats_gpr_remedy_sfun.m','tmats_r3_feedback_only_sfun.m','tmats_gp_mean_gradient.m','GasTurbine_PolyCompare_*.mdl','TMATS_R3_POLY2_USAGE.md']:
 files.update(root.glob(pattern))
files.update(run.glob('*.csv'));files.update(run.glob('*.mat'));files.update(fit.glob('*.csv'));files.update(fit.glob('*.json'))
with ZipFile(out/'TMATS_R3_Poly2_Models_Results.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,p.relative_to(root))
 z.writestr('SHA256_manifest.json',json.dumps({str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},indent=2))
print('Packaged',len(files),'files; existing workspace dependencies required.')
