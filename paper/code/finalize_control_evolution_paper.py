"""Add PDF navigation, audit the release, and package reproducible source."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import re, json, shutil, hashlib
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
from pypdf.annotations import Link
import pdfplumber

root=Path(__file__).resolve().parent
work=root/'tmp/pdfs/control_evolution'
out=root/'output/pdf'
source=work/'control_evolution_paper.pdf'
reader=PdfReader(source)
texts=[p.extract_text() or '' for p in reader.pages]
offset=next(i for i,t in enumerate(texts) if t.splitlines()[0]=='Chapter 1')
assert len(reader.pages)>=50
assert not any('??' in t for t in texts)
log=(work/'control_evolution_paper.log').read_text(errors='replace')
assert not re.search(r'Overfull|undefined|! LaTeX Error',log)
writer=PdfWriter();writer.clone_document_from_reader(reader)
writer.add_metadata({'/Title':'From Inverse Gaussian-Process Fuel Coordinates to Retuned Polynomial Control','/Author':'T-MATS Controller Development Study','/Subject':'Controller algorithms, comparative simulation evidence, limitations and five takeaways','/Keywords':'T-MATS, GPR, inverse control, PI, PID, polynomial regression, fuel control'})
writer.set_page_label(0,0,prefix='Cover')
writer.set_page_label(1,offset-1,style='/r',start=1)
writer.set_page_label(offset,len(reader.pages)-1,style='/D',start=1)
writer.add_outline_item('Title and research problem',0)
for heading in ['Contents','List of Figures','List of Tables']:
    n=next(i for i,t in enumerate(texts) if t.startswith(heading))
    writer.add_outline_item(heading,n)

def groups(line):
    result=[];depth=0;start=None
    for i,c in enumerate(line):
        if c=='{':
            if depth==0:start=i+1
            depth+=1
        elif c=='}':
            depth-=1
            if depth==0:result.append(line[start:i])
    return result

parent=None;outline_count=0
for line in (work/'control_evolution_paper.toc').read_text().splitlines():
    a=groups(line)
    if len(a)<3:continue
    kind,title,num=a[:3]
    title=re.sub(r'\\numberline\s*\{([^}]+)\}',r'\1 ',title).replace('\\%','%')
    n=1 if num=='i' else offset+int(num)-1
    if kind=='chapter':parent=writer.add_outline_item(title,n)
    elif kind=='section':writer.add_outline_item(title,n,parent=parent)
    outline_count+=1

urls=[
'https://gaussianprocess.org/gpml/chapters/RW2.pdf',
'https://ntrs.nasa.gov/citations/20150002325',
'https://github.com/nasa/T-MATS',
'https://research.sabanciuniv.edu/35801/',
'https://people.sabanciuniv.edu/munel/',
'https://portal.research.lu.se/en/publications/integrator-windup-and-how-to-avoid-it/',
'https://experts.illinois.edu/en/publications/research-on-gain-scheduling/',
'https://arxiv.org/abs/1502.02860',
'https://www.statlearning.com/']
clip=[];links=0
with pdfplumber.open(source) as pdf:
    for i,p in enumerate(pdf.pages):
        # Only extract detailed geometry on prose/table pages and reference/navigation pages.
        # Imported plot PDFs have internal labels beyond the prose margin by design.
        if i<offset or texts[i].startswith('References'):
            words=p.extract_words()
            if texts[i].startswith('References'):
                for w in words:
                    m=re.fullmatch(r'\[(\d)\]',w['text'])
                    if m:
                        writer.add_uri(i,urls[int(m[1])-1],RectangleObject([w['x0']-2,p.height-w['bottom']-2,w['x1']+3,p.height-w['top']+2]),border=[0,0,0]);links+=1
            elif i>=2:
                for w in words:
                    if w['x0']>515 and (w['text'].isdigit() or w['text']=='i'):
                        n=1 if w['text']=='i' else offset+int(w['text'])-1
                        if 0<=n<len(pdf.pages):
                            writer.add_annotation(i,Link(rect=(65,p.height-w['bottom']-1,535,p.height-w['top']+1),target_page_index=n))
        # Media bounds are checked independently of paragraph margins.
        for c in p.chars:
            if c.get('text','').strip() and (c['x0'] < -1 or c['x1']>p.width+1 or c['top'] < -1 or c['bottom'] > p.height+1):clip.append([i+1,c['text']])
assert not clip,clip[:10]
dest=out/'TMATS_GPR_to_Poly2_Comprehensive_Paper.pdf'
with dest.open('wb') as f:writer.write(f)
check=PdfReader(dest)
assert len(check.pages)==len(reader.pages) and links==9
qa={'pages':len(check.pages),'body_starts_at_pdf_page':offset+1,'words_in_extracted_pdf':sum(len(t.split()) for t in texts),'chapters':14,'appendices':4,'numbered_figures':len(re.findall(r'\\contentsline', (work/'control_evolution_paper.lof').read_text())),'numbered_tables':len(re.findall(r'\\contentsline',(work/'control_evolution_paper.lot').read_text())),'references':9,'outline_entries':outline_count+4,'reference_links':links,'overfull_boxes':0,'unresolved_references':0,'characters_outside_media_box':0,'pdf_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
(work/'release_checks.json').write_text(json.dumps(qa,indent=2))
(work/'README.md').write_text('''# Comprehensive GPR-to-Poly2 controller paper

Compile `control_evolution_paper.tex` with pdflatex twice (no shell escape).
The main source, six TikZ block diagrams, bibliography, all 19 generated
numerical tables and all vector figures are included. The report has a
research problem, 14 chapters, four appendices, a concise synthesis and
five takeaways. PDF bookmarks and clickable reference numbers are added
by finalize_control_evolution_paper.py; they are optional for typesetting.

`data/` contains the 22 registered empirical evidence files. The manifest
records original workspace paths and SHA-256 hashes. `code/` preserves the
relevant controller and audit implementations and figure/table generators.
These are an overlay for the existing T-MATS workspace, not a standalone
engine installation. The original native simulation traces remain in the
study result directories listed in the paper.

Rebuilding tables from original results requires the existing workspace and
Python with pandas/numpy. Rebuilding the three early vector figures requires
MATLAB; all final figure PDFs are already included, so LaTeX compilation
does not require MATLAB. No new fitting, simulation tuning or controller
selection was performed for this paper.

The release PDF includes navigable chapter/section bookmarks and page labels.
Click a bracketed reference number on the reference page to open its source.
The complete final PDF was rendered for visual review; release_checks.json
records structural checks and its SHA-256 hash.
''',encoding='utf-8')
shutil.copy2(root/'finalize_control_evolution_paper.py',work/'code'/'finalize_control_evolution_paper.py')
with ZipFile(out/'TMATS_GPR_to_Poly2_Paper_LaTeX_Evidence.zip','w',ZIP_DEFLATED) as z:
    for p in sorted(work.rglob('*')):
        if not p.is_file():continue
        if p.suffix in ['.tex','.pdf','.csv','.json','.md','.m','.py'] and p.name!='control_evolution_paper.pdf':z.write(p,p.relative_to(work))
print(json.dumps(qa,indent=2))
