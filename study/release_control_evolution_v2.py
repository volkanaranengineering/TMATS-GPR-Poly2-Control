"""Finalize the referee-response PDF and refresh V2 provenance/package."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,re,shutil
from pypdf import PdfReader,PdfWriter
import pdfplumber

ROOT=Path(__file__).resolve().parent;WORK=ROOT/'tmp/pdfs/control_evolution_v2';OUT=ROOT/'output/pdf'
log=(WORK/'response_to_referees.log').read_text(errors='replace')
assert not re.search(r'Overfull|undefined|! LaTeX Error',log)
src=WORK/'response_to_referees.pdf';r=PdfReader(src);w=PdfWriter();w.clone_document_from_reader(r)
w.add_metadata({'/Title':'Response to Three AI Referee Roles - GPR-to-Poly2 Study V2','/Author':'T-MATS Controller Development Study','/Subject':'Ten findings, main-text corrections, archived-trace sensitivity and back-checks'})
for i,p in enumerate(r.pages):
    t=p.extract_text() or '';assert '??' not in t
    for title in ['Review scope and provenance','Industry-engineer referee','Control-theory academic referee','Research-assistant referee','A4: Test sensitivity']:
        if title in t:w.add_outline_item(title,i)
with pdfplumber.open(src) as pdf:
    for i,p in enumerate(pdf.pages):
        for c in p.chars:
            if c.get('text','').strip():assert -1<=c['x0']<=c['x1']<=p.width+1 and -1<=c['top']<=c['bottom']<=p.height+1,(i,c)
dest=OUT/'TMATS_GPR_to_Poly2_Response_to_Referees_V2.pdf'
with dest.open('wb') as f:w.write(f)
for p in (ROOT/'reviews/control_evolution_v2').glob('*'):
    if p.is_file():shutil.copy2(p,WORK/'reviews'/p.name)
for name in ['finalize_control_evolution_v2.py','release_control_evolution_v2.py','revise_control_evolution_paper.py','review_control_evolution_metrics.py']:
    shutil.copy2(ROOT/name,WORK/'code'/name)
manifest=json.loads((WORK/'evidence_manifest.json').read_text())
for p in [WORK/'response_to_referees.tex',*sorted((WORK/'reviews').glob('*')),*sorted((WORK/'code').glob('*'))]:
    if p.is_file():manifest['V2_'+p.relative_to(WORK).as_posix()]={'path':p.relative_to(WORK).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(WORK/'evidence_manifest.json').write_text(json.dumps(manifest,indent=2))
qa=json.loads((WORK/'release_checks.json').read_text());qa['response_pdf_pages']=len(r.pages);qa['response_pdf_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();qa['referee_findings']=10;qa['backchecked_findings']=10
(WORK/'release_checks.json').write_text(json.dumps(qa,indent=2))
with ZipFile(OUT/'TMATS_GPR_to_Poly2_Paper_V2_LaTeX_Evidence.zip','w',ZIP_DEFLATED) as z:
    for p in sorted(WORK.rglob('*')):
        if p.is_file() and p.suffix in ['.tex','.pdf','.csv','.json','.md','.m','.py'] and p.name!='control_evolution_paper.pdf':z.write(p,p.relative_to(WORK))
v1=OUT/'TMATS_GPR_to_Poly2_Comprehensive_Paper.pdf'
assert hashlib.sha256(v1.read_bytes()).hexdigest()=='bd93a8cdcb987a74d6f6b80ba8f83beb144a7470dc3695430dec1cb4137158c5'
print(json.dumps(qa,indent=2))
