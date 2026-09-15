"""Package the native LaTeX PDF with correctly oriented figure pages."""
from pathlib import Path
from io import BytesIO
import shutil, re
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT=Path(__file__).resolve().parent
WORK=ROOT/'tmp/pdfs/virtual_fuel_latex'
SOURCE=ROOT/'results/virtual_fuel_20260913_182229_028'
OUT=ROOT/'output/pdf'
spec={
6:('comparison_9000rpm.png','9000 rpm / ramp-load comparison','5%, 10%, 20% and 30% turbine-power extraction. Grey: original PI; blue: virtual-fuel PI. The new controller reduces RMSE by 37.6-37.9% across these cases.'),
7:('comparison_9500rpm.png','9500 rpm / ramp-load comparison','The gains remain fixed at Kp = 4 and Ki = 40 per second. The original PI trace at 30% load ends at its first validity failure; the new controller completes the run with a minimum surge margin of 0.356%.'),
8:('virtual_fuel_signals.png','Virtual fuel / internal controller signals','9000 rpm, 30% ramp load. Virtual feedback returns to the constant virtual setpoint, while the integral state retains the additional actual fuel required to balance the shaft load.'),
9:('step_tradeoff.png','9500 rpm / abrupt-load tradeoff','20% step load. RMSE improves from 6.430 to 3.095 rpm, but peak fuel rises from 3.333 to 3.758 lbm/s and minimum surge margin falls from 4.864% to 0.673%. The fuel response is more oscillatory.')}

reader=PdfReader(WORK/'Virtual_Fuel_Controller_Report.pdf')
writer=PdfWriter()
for i,page in enumerate(reader.pages):
    text=page.extract_text()
    match=re.search(r'Figure ([6-9]):',text)
    if match and len(text)<600:
        num=int(match[1]);name,title,caption=spec[num]
        size=landscape(A4) if num in (6,7) else A4
        w,h=size;buf=BytesIO();c=canvas.Canvas(buf,pagesize=size)
        navy=HexColor('#16324F');teal=HexColor('#007F86')
        c.setFillColor(navy);c.setFont('Helvetica',8.5)
        c.drawString(42,h-28,'INVERSE-GPR VIRTUAL-FUEL PI')
        c.drawRightString(w-42,h-28,'T-MATS control study')
        c.setStrokeColor(navy);c.setLineWidth(.4);c.line(42,h-36,w-42,h-36)
        c.setFont('Helvetica-Bold',15);c.drawString(42,h-62,title)
        image=ImageReader(str(SOURCE/name));iw,ih=image.getSize()
        maxw=w-84;maxh=h-167 if num in (6,7) else h-260
        scale=min(maxw/iw,maxh/ih);dw,dh=iw*scale,ih*scale
        y=h-82-dh;c.drawImage(image,(w-dw)/2,y,width=dw,height=dh)
        style=ParagraphStyle('caption',fontName='Helvetica',fontSize=10,leading=14,textColor=navy)
        p=Paragraph(f'<b>Figure {num}.</b> '+caption,style)
        pw,ph=p.wrap(w-84,120);p.drawOn(c,42,y-ph-16)
        c.setFont('Helvetica',8);c.drawString(42,25,'9000 rpm tuning / 9500 rpm transfer evaluation')
        c.drawRightString(w-42,25,str(i))
        c.showPage();c.save();buf.seek(0);writer.add_page(PdfReader(buf).pages[0])
    else:writer.add_page(page)
writer.add_metadata({'/Title':'Inverse-GPR Virtual-Fuel PI Controller','/Author':'T-MATS Controller Development Study','/Subject':'Mathematical formulation, vector block diagrams and disturbance performance'})
OUT.mkdir(parents=True,exist_ok=True)
target=OUT/'Virtual_Fuel_Controller_Report.pdf'
with target.open('wb') as f:writer.write(f)
sourceout=OUT/'virtual_fuel_latex_source';sourceout.mkdir(exist_ok=True)
shutil.copy2(WORK/'Virtual_Fuel_Controller_Report.tex',sourceout)
for name,_,_ in spec.values():shutil.copy2(SOURCE/name,sourceout/name)
final=PdfReader(target);full='\n'.join(p.extract_text() for p in final.pages)
assert len(final.pages)==len(reader.pages)
assert all(f'({i})' in full for i in range(1,35)), 'Missing equation number'
assert all(f'Figure {i}:' in full or f'Figure {i}.' in full for i in range(1,10)), 'Missing figure'
assert not any(c in full for c in ['\ufffd','\u25a0'])
print(f'PDF_READY {target} / {len(final.pages)} pages / all 34 equations and 9 figures verified')
