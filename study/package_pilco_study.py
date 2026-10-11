"""Package new artifacts as an overlay for the supplied T-MATS workspace."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,importlib.metadata
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/pilco_quadratic_pi_20261010'
sources=['pilco_tmats.py','tmats_pilco_pi_sfun.m','tmats_pilco_setup.m',
         'run_tmats_pilco.m','pilco_matlab_batch.m','GasTurbine_PILCO_Quadratic_PI.mdl',
         'pilco_paper_template.tex','build_pilco_deliverables.py',
         'package_pilco_study.py','TMATS_PILCO_QUADRATIC_PI_USAGE.md']
versions={m:importlib.metadata.version(m) for m in ['numpy','pandas','scipy','matplotlib','imageio','imageio-ffmpeg','pymupdf']}
(OUT/'python_versions.json').write_text(json.dumps(versions,indent=2))
files=[ROOT/s for s in sources]
files+=list(OUT.glob('*.csv'))+list(OUT.glob('*.mat'))+list(OUT.glob('*.json'))+list(OUT.glob('*.npz'))
files+=[ROOT/'output/pdf/PILCO_Quadratic_FF_PI_Comparison.pdf',ROOT/'output/video/PILCO_Quadratic_FF_PI_Comparison.mp4']
files+=list((ROOT/'output/pdf/pilco_quadratic_pi_source').glob('*.tex'))
files+=list((ROOT/'output/pdf/pilco_quadratic_pi_source').glob('*.pdf'))
old=ROOT/'results/poly2_tune9250_20260915'
files+=[old/f'candidate_{i:02d}.csv' for i in [0,1,34]]+[old/f'validation_{s}.csv' for s in ['base','original','tuned']]
files+=[ROOT/'results/poly2_inverse_20260915/poly2_model.json']
assert all(f.exists() for f in files)
manifest=OUT/'SHA256_manifest.txt'
manifest.write_text('\n'.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.relative_to(ROOT).as_posix() for f in files))
files.append(manifest)
target=ROOT/'output/PILCO_Quadratic_FF_PI_Study.zip'
with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=6) as z:
    for f in files:z.write(f,f.relative_to(ROOT))
with ZipFile(target) as z:assert z.testzip() is None
print(target,target.stat().st_size)
