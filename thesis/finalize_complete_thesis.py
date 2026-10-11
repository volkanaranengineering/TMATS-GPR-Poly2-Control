"""PDF navigation, static checks, and Poppler render; no simulation."""
from pathlib import Path
import re,json,hashlib,subprocess
import fitz
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parent
WORK=ROOT/'output/pdf/tmats_complete_thesis_source'
QA=ROOT/'tmp/pdfs/complete_thesis_qa';QA.mkdir(parents=True,exist_ok=True)
log=(WORK/'TMATS_Complete_Thesis.log').read_text(errors='replace')
assert not re.search(r'Overfull|undefined|! LaTeX Error',log),'Resolve typesetting errors first'
doc=fitz.open(WORK/'TMATS_Complete_Thesis.pdf');texts=[p.get_text() for p in doc]
assert not any('??' in t for t in texts)
offset=next(i for i,t in enumerate(texts) if re.search(r'Chapter 1\s+Purpose',t))
def groups(line):
    out=[];depth=0;start=0
    for i,c in enumerate(line):
        if c=='{':
            if depth==0:start=i+1
            depth+=1
        elif c=='}':
            depth-=1
            if depth==0:out.append(line[start:i])
    return out
def roman(s):
    vals={'i':1,'v':5,'x':10,'l':50,'c':100};a=[vals[x] for x in s.lower()];return sum(-v if k+1<len(a) and v<a[k+1] else v for k,v in enumerate(a))
toc=[[1,'Title',1]]
for line in (WORK/'TMATS_Complete_Thesis.toc').read_text().splitlines():
    a=groups(line)
    if len(a)<3:continue
    kind,title,page=a[:3]
    title=re.sub(r'\\numberline\s*\{([^}]+)\}',r'\1 ',title).replace(r'\%','%')
    page=offset+int(page) if page.isdigit() else 1+roman(page)
    toc.append([1 if kind=='chapter' else 2,title,page])
doc.set_toc(toc)
doc.set_metadata({'title':'T-MATS System Identification and Control: Complete Research Narrative','author':'Volkan Aran research project; AI-assisted report','subject':'Evidence-only retrospective thesis; September–October 2026','keywords':'T-MATS, identification, RLS, DOB, GPR, PI, PID, PILCO, fuel ringing'})
outside=[]
for i,p in enumerate(doc):
    for b in p.get_text('dict')['blocks']:
        for line in b.get('lines',[]):
            for s in line['spans']:
                x0,y0,x1,y1=s['bbox']
                if x0 < -1 or y0 < -1 or x1>p.rect.width+1 or y1>p.rect.height+1:outside.append([i+1,s['text']])
assert not outside,outside[:5]
dest=ROOT/'output/pdf/TMATS_Complete_Thesis.pdf';doc.save(dest,garbage=4,deflate=True)
report={'pages':len(doc),'main_chapters':41,'appendices':5,'study_directories':69,'words_extracted':sum(len(t.split()) for t in texts),'figures':(WORK/'TMATS_Complete_Thesis.lof').read_text().count('contentsline'),'tables':(WORK/'TMATS_Complete_Thesis.lot').read_text().count('contentsline'),'bookmarks':len(toc),'undefined_references':0,'overfull_boxes':0,'text_outside_page':len(outside),'new_simulations':0,'pdf_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
(WORK/'release_checks.json').write_text(json.dumps(report,indent=2));(QA/'page_text.txt').write_text('\n\n'.join(f'PDF PAGE {i+1}\n{t}' for i,t in enumerate(texts)),encoding='utf8')
print(json.dumps(report,indent=2),flush=True)
poppler=Path(r'C:\Users\volka\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
subprocess.run([str(poppler),'-r','65','-png',str(dest),str(QA/'page')],check=True)
pages=sorted(QA.glob('page-*.png'))
for start in range(0,len(pages),12):
    sheet=Image.new('RGB',(1200,4*448),'#bcc5ce');draw=ImageDraw.Draw(sheet)
    for j,p in enumerate(pages[start:start+12]):
        im=Image.open(p).convert('RGB');im.thumbnail((384,416));x=(j%3)*400+8;y=(j//3)*448+24
        sheet.paste(im,(x,y));draw.text((x,y-18),f'PDF page {start+j+1}',fill='black')
    sheet.save(QA/f'contact-{start//12+1:02d}.png')
print('Rendered all pages and contact sheets:',QA,flush=True)
