from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parent
dest=ROOT/'output/DOB98_PI_Study.zip'
names=['TMATS_DOB98_PI_USAGE.md','GasTurbine_DOB98_PI.mdl','GasTurbine_DOB98_Identification.mdl','identify_tmats_dob98.m','dob98_identify_batch.m','fit_dob98_model.py','tmats_dob98_setup.m','run_tmats_dob98_tune.m','dob98_tune_batch.m','validate_dob98.py','build_dob98_deliverables.py','package_dob98.py','output/pdf/DOB98_PI_Comparison.pdf','output/video/DOB98_PI_Combined_Cycle_Comparison.mp4']
files=[ROOT/n for n in names]
files+=list((ROOT/'results/dob98_pi_20261010').glob('*.csv'))+list((ROOT/'results/dob98_pi_20261010').glob('*.json'))+list((ROOT/'results/dob98_pi_20261010').glob('*.mat'))
files+=list((ROOT/'output/pdf/dob98_pi_source').glob('*.tex'))+list((ROOT/'output/pdf/dob98_pi_source').glob('*.pdf'))
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
    for p in sorted(set(files)):z.write(p,p.relative_to(ROOT))
with ZipFile(dest) as z:assert z.testzip() is None
print(dest,round(dest.stat().st_size/1e6,2),'MB')
