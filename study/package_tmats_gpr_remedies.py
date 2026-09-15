"""Package the verified report source and controller overlay, preserving source paths."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,shutil
root=Path(__file__).resolve().parent
run=Path((root/'tmp/remedies_directory.txt').read_text().strip())
env=Path((root/'tmp/environment_directory.txt').read_text().strip())
out=root/'output/pdf';out.mkdir(parents=True,exist_ok=True)
work=root/'tmp/pdfs/gpr_remedies'
shutil.copy2(work/'GPR_Three_Remedies.pdf',out/'TMATS_GPR_Three_Remedies.pdf')
with ZipFile(out/'TMATS_GPR_Three_Remedies_LaTeX.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(work.iterdir()):
  if p.suffix in ['.tex','.pdf','.csv']:z.write(p,p.name)
files=set()
for pattern in ['*remed*.m','*remed*.py','tmats_remedy_report_template.tex','tmats_gp_mean_gradient.m','GasTurbine_Remedy*.mdl','TMATS_GPR_REMEDIES_USAGE.md',
 'tmats_environment*.m','tmats_virtual_fuel_ff_setup.m','tmats_pto_setup.m','tmats_fixed_comparison_metrics.m','predict_tmats_environment_gpr.m','diagnose_tmats_inverse_feedback.m','build_virtual_fuel_pdf.py']:
 files.update(root.glob(pattern))
files.update([root/'tmp/remedies_directory.txt',root/'tmp/environment_directory.txt',run/'selected_remedies.mat',env/'environment_inverse_gpr_model.mat',root/'results/inverse_gpr_20260913_150824_698/inverse_gpr_model.mat'])
files.update(env.glob('trim_*.mat'))
for pattern in ['*summary*.csv','*checks.csv','*diagnosis.csv','remedy_comparison.csv','report_summary.json','ablation_worker_01.csv']:
 files.update(run.glob(pattern))
manifest={str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
with ZipFile(out/'TMATS_GPR_Three_Remedies_Controllers.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,p.relative_to(root))
 z.writestr('SHA256_manifest.json',json.dumps(manifest,indent=2))
print('Packaged',len(files),'controller/source/parameter files')
