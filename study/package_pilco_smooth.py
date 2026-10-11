"""Bundle the smoothing study as an overlay for the existing T-MATS workspace."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/pilco_smooth_20261010'
names=['pilco_smooth.py','refine_pilco_smooth.py','select_pilco_smooth.py',
       'check_pilco_smooth_mc.py','run_tmats_pilco_smooth.m','tmats_pilco_smooth_setup.m',
       'pilco_smooth_tune_batch.m','pilco_smooth_validate_batch.m',
       'GasTurbine_PILCO_Smooth_PI.mdl','pilco_smooth_report_template.tex',
       'build_pilco_smooth_report.py','build_pilco_smooth_video.py','package_pilco_smooth.py',
       'TMATS_PILCO_SMOOTH_USAGE.md','pilco_tmats.py','tmats_pilco_pi_sfun.m',
       'tmats_pilco_setup.m','GasTurbine_PILCO_Quadratic_PI.mdl',
       'build_pilco_deliverables.py','build_pilco_video_v2.py']
files=[ROOT/n for n in names]
files += [f for f in OUT.iterdir() if f.is_file() and f.suffix in ['.csv','.mat','.json']]
prior=ROOT/'results/pilco_quadratic_pi_20261010';old=ROOT/'results/poly2_tune9250_20260915'
files += [prior/n for n in ['dynamics_gp.npz','policy.json','pilco_10pct.csv','pilco_5pct.csv']]
files += [old/f'candidate_{i:02d}.csv' for i in [0,1,34]]+[old/f'validation_{n}.csv' for n in ['base','original','tuned']]
files += [ROOT/'output/pdf/PILCO_Smooth_Ringing_Penalty.pdf',ROOT/'output/pdf/PILCO_Quadratic_FF_PI_Comparison.pdf',ROOT/'output/video/PILCO_Smooth_Four_Window_Load_Comparison.mp4']
paper=ROOT/'output/pdf/pilco_smooth_source';files+=list(paper.glob('*.tex'))+list(paper.glob('*.pdf'))
assert all(f.exists() for f in files)
manifest=OUT/'SHA256_manifest.txt';manifest.write_text('\n'.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.relative_to(ROOT).as_posix() for f in files));files.append(manifest)
target=ROOT/'output/PILCO_Smooth_Ringing_Study.zip'
with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=6) as z:
    for f in files:z.write(f,f.relative_to(ROOT))
with ZipFile(target) as z:assert z.testzip() is None
print(target,target.stat().st_size)
