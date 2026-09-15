from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,hashlib,json
root=Path(__file__).resolve().parent;run=root/'results/r3_ambient_cycle_20260915';work=root/'tmp/pdfs/r3_cycle';out=root/'output/pdf'
shutil.copy2(work/'R3_Ambient_Cycle.pdf',out/'TMATS_R3_Ambient_Cycle.pdf')
with ZipFile(out/'TMATS_R3_Ambient_Cycle_LaTeX.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(work.iterdir()):
  if p.suffix in ['.tex','.pdf','.csv']:z.write(p,p.name)
files=set()
for pattern in ['*r3_cycle*.m','*r3_cycle*.py','GasTurbine_Cycle_*.mdl','TMATS_R3_CYCLE_USAGE.md']:
 files.update(root.glob(pattern))
for name in ['BasePI.mat','R3.mat','BasePI.csv','R3.csv','BasePI_segments.csv','R3_segments.csv','summary.csv','verification.csv','sensor_diagnostics.csv']:
 files.add(run/name)
with ZipFile(out/'TMATS_R3_Ambient_Cycle_Models_Results.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,p.relative_to(root))
 z.writestr('SHA256_manifest.json',json.dumps({str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},indent=2))
print('Packaged',len(files),'files; original workspace dependencies required.')
