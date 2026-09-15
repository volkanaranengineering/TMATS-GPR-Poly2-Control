"""Typeset the verified Markdown study as native LaTeX with vector diagrams."""
from pathlib import Path
import re, shutil

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'results/virtual_fuel_20260913_182229_028'
WORK = ROOT / 'tmp/pdfs/virtual_fuel_latex'
OUT = ROOT / 'output/pdf'
WORK.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

def inline(s):
    saved = []
    def protect(value):
        saved.append(value)
        return f'ZZPLACEHOLDER{len(saved)-1}ZZ'
    s = re.sub(r'\\\(.*?\\\)', lambda m: protect(m.group()), s)
    s = re.sub(r'`([^`]+)`', lambda m: protect(r'\path{' + m[1] + '}'), s)
    s = s.replace('–', '-').replace('—', ' - ').replace('−', '-').replace('“','"').replace('”','"').replace('’',"'").replace('²',r'ZZSQUAREDZZ').replace('·',r'ZZDOTZZ')
    s = s.replace('\\',r'\textbackslash{}')
    for c, v in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]: s=s.replace(c,v)
    s = s.replace('ZZSQUAREDZZ',r'\textsuperscript{2}').replace('ZZDOTZZ',r'\textperiodcentered{}')
    s = re.sub(r'\*\*(.*?)\*\*', lambda m: r'\textbf{'+m[1]+'}', s)
    s = re.sub(r'\*([^*]+)\*', lambda m: r'\emph{'+m[1]+'}', s)
    for i,v in enumerate(saved): s=s.replace(f'ZZPLACEHOLDER{i}ZZ',v)
    return s

DIAGRAMS = [r'''
\begin{tikzpicture}[x=1cm,y=1cm]
\node[block, text width=2.15cm] (ref) at (1.2,0) {Motion setpoint\\$r,\ a_r$};
\node[gp, text width=2.2cm] (gr) at (4.25,0) {Inverse GP\\$g(r,a_r)$};
\node[sum] (err) at (7,0) {$\Sigma$};
\node[block,text width=2.3cm] (pi) at (10,0) {Fuel-domain PI\\$K_p=4$\\$K_i=40\ \mathrm{s}^{-1}$};
\node[block,text width=1.65cm] (lim) at (13.4,0) {Fuel limits\\$[0.2,4]$\\lbm/s};
\node[plant,text width=2.3cm] (engine) at (13.4,-2.1) {T-MATS\\gas turbine};
\node[block,text width=2.3cm] (sensor) at (9.5,-2.1) {Speed sensor\\$\tau_s=0.05$ s};
\node[gp,text width=2.4cm] (gy) at (4.25,-4.25) {Inverse GP\\$g(N_s,\hat a_s)$};
\node[block,text width=2.3cm] (diff) at (9.5,-4.25) {Filtered difference\\$D_a(z)$};
\draw[arr] (ref)--(gr);
\draw[arr] (gr)--node[above,lab]{$v_r$}node[pos=.86,below,lab]{$+$}(err);
\draw[arr] (err)--node[above,lab]{$e_v$}(pi);
\draw[arr] (pi)--node[above,lab]{$u^\star$}(lim);
\draw[arr] (lim)--node[right,lab]{$u$}(engine);
\draw[arr] (engine)--node[above,lab]{$N$}(sensor);
\draw[arr] (sensor.west)--node[above,lab]{$N_s$}(6.3,-2.1)--(6.3,-3.3)--(4.25,-3.3)--(gy.north);
\draw[arr] (sensor)--(diff);
\draw[arr] (diff)--node[above,lab]{$\hat a_s$}(gy);
\draw[arr] (gy.west)--(2.3,-4.25)--(2.3,-1.2)--(7,-1.2)--node[right,lab]{$v_y$}node[pos=.85,left,lab]{$-$}(err.south);
\node[lab,anchor=east,text=amber] (load) at (15.1,-3.55) {Shaft load $P_L$};
\draw[arr,draw=amber] (load.north)--(14.25,-2.65)--(engine.south east);
\node[note,anchor=west,text width=11cm] at (0,-5.45) {Same frozen GP in both branches. The load is applied to the plant only.\\$a_r=0$ during constant-speed disturbance evaluation.};
\end{tikzpicture}
''',r'''
\begin{tikzpicture}[x=1cm,y=1cm]
\node[block,text width=2.5cm] (data) at (1.4,0) {600 training samples\\$N,\ a,\ w$};
\node[block,text width=2.5cm] (fit) at (5.4,0) {Standardization\\and exact GP fit};
\node[gp,text width=3.3cm] (model) at (10.3,0) {Frozen model\\$\mu_x,s_x,\mu_w,s_w,\ell,\alpha$};
\draw[arr](data)--(fit);\draw[arr](fit)--(model);
\node[block,text width=2.5cm] (query) at (1.4,-2.1) {Online query\\$x=[N\ a]^{\mathsf T}$};
\node[gp,text width=3.5cm] (pred) at (6.9,-2.1) {Posterior mean\\$g(x)=\mu_w+s_w\mathbf{k}_x^{\mathsf T}\alpha$};
\node[block,text width=2cm] (out) at (12.5,-2.1) {Virtual fuel\\lbm/s};
\draw[arr](query)--(pred);\draw[arr](pred)--(out);
\draw[arr,dashed](model.south)--(10.3,-1.15)-|(pred.north);
\node[note,anchor=west] at (0,-3.35) {Offline: fit and factorize.\qquad Online: two GP-mean queries per control sample.};
\end{tikzpicture}
''',r'''
\begin{tikzpicture}[x=1cm,y=1cm]
\node[lab] (e) at (0,0) {$e_v$};
\node[block,text width=1.4cm] (kp) at (3.1,0) {$K_p$};
\node[block,text width=1.4cm] (ki) at (3.1,-2) {$T_sK_i$};
\node[block,text width=2.4cm] (gate) at (6.3,-2) {Conditional update\\$\gamma[k]$};
\node[gp,text width=2.4cm] (state) at (10,-2) {Integral state\\$I[k+1]=I[k]+\Delta I$};
\node[sum] (add) at (10,0) {$+$};
\node[block,text width=1.7cm] (sat) at (13,0) {Saturation};
\draw[arr](e)--(kp);\draw[arr](1,0)|-(ki);
\draw[arr](kp)--(add);\draw[arr](ki)--(gate);\draw[arr](gate)--(state);
\draw[arr](state)--node[right,lab]{$I[k]$}(add);
\draw[arr](add)--node[above,lab]{$u^\star$}(sat);\draw[arr](sat)--(14.7,0)node[right,lab]{$u$};
\draw[arr,dashed](11.4,0)--(11.4,1.15)--(6.3,1.15)--(gate.north);
\draw[arr,dashed](1,-2)--(1,-3.3)-|(gate.south);
\node[note,anchor=west,text width=14cm] at (0,-4.1) {The gate suppresses only integration that pushes further into saturation. Output uses $I[k]$; the state update follows.};
\end{tikzpicture}
''',r'''
\begin{tikzpicture}[x=1cm,y=1cm]
\node[block,text width=2.65cm] (old) at (1.5,0) {Original speed PI\\$u_{\rm PI}$};
\node[gp,text width=2.65cm] (new) at (1.5,-2.2) {Virtual-fuel PI\\$u^\star$};
\node[block,text width=2.6cm] (sw) at (6.6,-1.1) {Startup selector\\handover at 30 s};
\node[block,text width=1.9cm] (lim) at (10.2,-1.1) {Shared\\fuel limits};
\node[plant,text width=1.6cm] (plant) at (13.4,-1.1) {Plant};
\draw[arr](old.east)--(4,0)--(4,-.75)--(sw.west |- 4,-.75);
\draw[arr](new.east)--(4,-2.2)--(4,-1.45)--(sw.west |- 4,-1.45);
\draw[arr](sw)--(lim);\draw[arr](lim)--(plant);
\node[note,text width=7cm,align=center] (track) at (6.8,-3.25) {Before handover:\\$I[k+1]=u_{\rm PI}[k]-K_pe_v[k]$};
\draw[arr,dashed](old.north)--(1.5,.9)--(15,.9)--(15,-3.25)--(track.east);
\draw[arr,dashed](track.west)-|(new.south);
\end{tikzpicture}
''',r'''
\begin{tikzpicture}[x=1cm,y=1cm]
\node[lab] (e) at (0,0) {$e_N$};
\node[gp,text width=3cm] (g) at (4,0) {Local GP operator\\$c_N+c_as$};
\node[block,text width=2.7cm] (pi) at (9,0) {Fuel-domain PI\\$K_p+K_i/s$};
\node[lab] (u) at (14.1,0) {$\delta u$};
\draw[arr](e)--(g);\draw[arr](g)--node[above,lab]{$e_v$}(pi);\draw[arr](pi)--(u);
\node[block,text width=10.5cm,minimum height=1.2cm] (equiv) at (7,-2) {Ideal local PID equivalent\\$K_{d,N}=K_pc_a\quad K_{p,N}=K_pc_N+K_ic_a\quad K_{i,N}=K_ic_N$};
\draw[arr,dashed](.8,0)|-(equiv.west);\draw[arr,dashed](equiv.east)-|(13.3,0);
\node[note,anchor=west,text width=14.6cm] at (0,-3.35) {Analytical equivalence only: ideal derivatives, local linearization, zero-state transfer functions. The implemented filter and sample timing are retained in Eq. (27).};
\end{tikzpicture}
''']

PREAMBLE = r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=22mm,headheight=16pt,footskip=12mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern,amsmath,amssymb,graphicx,xcolor,booktabs,longtable,array,tabularx}
\usepackage{tikz,float,caption,fancyhdr,titlesec,url,lscape}
\usetikzlibrary{arrows.meta,positioning,calc}
\definecolor{navy}{HTML}{16324F}
\definecolor{teal}{HTML}{007F86}
\definecolor{pale}{HTML}{EAF5F5}
\definecolor{ink}{HTML}{243646}
\definecolor{amber}{HTML}{A45C13}
\pdfinfo{/Title (Inverse-GPR Virtual-Fuel PI Controller) /Author (T-MATS Controller Development Study)}
\urlstyle{tt}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt plus 1pt minus 1pt}
\setlength{\emergencystretch}{2em}
\widowpenalty=10000\clubpenalty=10000
\linespread{1.05}
\titleformat{\section}{\Large\sffamily\bfseries\color{navy}}{\thesection}{.7em}{}
\titleformat{\subsection}{\large\sffamily\bfseries\color{teal}}{\thesubsection}{.7em}{}
\titlespacing*{\section}{0pt}{19pt}{8pt}
\titlespacing*{\subsection}{0pt}{13pt}{5pt}
\captionsetup{font=small,labelfont={bf,color=navy},skip=8pt}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small\sffamily\color{navy}INVERSE-GPR VIRTUAL-FUEL PI}
\fancyhead[R]{\small\sffamily T-MATS control study}
\fancyfoot[L]{\scriptsize\color{ink}9000 rpm tuning / 9500 rpm transfer evaluation}
\fancyfoot[R]{\small\thepage}
\renewcommand{\headrulewidth}{.3pt}
\tikzset{block/.style={draw=navy!55,fill=navy!3,rounded corners=3pt,minimum height=.92cm,align=center,font=\sffamily\small,inner sep=5pt},
gp/.style={block,draw=teal,fill=pale},plant/.style={block,draw=navy,fill=navy!12},
sum/.style={circle,draw=navy,minimum size=.68cm,fill=white,font=\large},
arr/.style={-{Latex[length=2.2mm]},draw=navy,line width=.65pt},
lab/.style={font=\small,fill=white,inner sep=2pt},
note/.style={font=\small\sffamily,text=ink,align=left}}
\begin{document}
\begin{titlepage}
\color{navy}\sffamily
{\small T-MATS / CONTROLLER DEVELOPMENT}\par
\vspace{22mm}
{\fontsize{32}{38}\selectfont\bfseries Inverse-GPR\\Virtual-Fuel\\PI Controller\par}
\vspace{7mm}
{\Large Concept, mathematical formulation\\and disturbance performance\par}
\vspace{12mm}\color{teal}\rule{\linewidth}{1.3pt}\color{navy}
\vspace{6mm}
{\large Two motion-to-fuel projections.\\One feedback controller in fuel coordinates.\par}
\vspace{12mm}
\begin{tabular}{@{}ll}
\textbf{Selected gains}& $K_p=4,\quad K_i=40\ \mathrm{s}^{-1}$\\[6pt]
\textbf{Tuning point}&9000 rpm\\[6pt]
\textbf{Transfer evaluation}&9500 rpm, unchanged gains\\[6pt]
\textbf{Study date}&13 September 2026
\end{tabular}
\vfill
\color{ink}\normalfont
\textbf{Measured outcome.} Mean ramp-case RMSE at 9000 rpm fell by 37.74\%. The new controller completed 9 of 10 test cases; the original PI completed 8.
\par\vspace{3mm}
\textbf{Engineering qualification.} Demanding 9500-rpm tests leave very small surge margins, and abrupt loading produces stronger damped oscillations. Performance gains do not establish a robust operating reserve.
\end{titlepage}
\tableofcontents
\clearpage
\section*{Study overview}\addcontentsline{toc}{section}{Study overview}
'''

def table(lines):
    rows=[[x.strip() for x in line.strip().strip('|').split('|')] for line in lines]
    headers=rows[0]; rows=rows[2:]; n=len(headers)
    if headers[0]=='Symbol': ratios=[.16,.67,.17]
    elif n==2: ratios=[.38,.62]
    elif n==3: ratios=[.22,.56,.22]
    elif n==4: ratios=[.13,.27,.33,.27]
    elif n==6:
        ratios=[.10,.18,.18,.18,.18,.18]
        headers=['rpm',r'\(c_N\)',r'\(c_a\)',r'\(K_{p,N}\)',r'\(K_{i,N}\)',r'\(K_{d,N}\)']
    elif n==8:
        ratios=[.08,.065,.09,.15,.15,.165,.15,.15]
        headers=['rpm','Load','Shape','PI RMSE','VF RMSE','Reduction','PI peak','VF peak']
    elif n==7 and 'controller' in headers:
        ratios=[.085,.07,.085,.17,.23,.18,.18]
        headers=['rpm','Load','Shape','Controller','First invalid [s]','Flow residual','Iterations']
    elif n==7:
        ratios=[.08,.07,.10,.185,.185,.19,.19]
        headers=['rpm','Load','Shape','PI peak fuel','VF peak fuel','PI min. margin','VF min. margin']
    else: ratios=[1/n]*n
    ratios=[x/sum(ratios) for x in ratios]
    widths=[(16.6-(n-1)*.211)*x for x in ratios]
    spec='@{}'+''.join(r'>{\raggedright\arraybackslash}p{%.3fcm}'%w for w in widths)+'@{}'
    head=' & '.join(r'\textbf{'+inline(x)+'}' for x in headers)+r'\\'
    out=[r'{\small\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.2}']
    if n==2:
        out += [r'\begin{minipage}{\linewidth}',r'\begin{tabular}{'+spec+'}',r'\toprule',head,r'\midrule']
    else:
        out += [r'\begin{longtable}{'+spec+'}',r'\toprule',head,r'\midrule\endfirsthead',r'\toprule',head,r'\midrule\endhead',r'\bottomrule\endfoot']
    for row in rows:
        vals=[]
        for value in row:
            if value in ['NaN','NaN%']: value='--'
            if value=='VirtualFuel': value='Virtual-fuel'
            vals.append(inline(value))
        out.append(' & '.join(vals)+r'\\')
    if n==2: out += [r'\bottomrule\end{tabular}\end{minipage}}\par\vspace{9pt}']
    else: out += [r'\end{longtable}}']
    return '\n'.join(out)

text=(SOURCE/'REPORT.md').read_text(encoding='utf-8')
lines=text.splitlines(); body=[]; i=1; diagram=0
while i<len(lines):
    line=lines[i].strip()
    if not line: i+=1;continue
    if line=='```mermaid':
        i+=1
        while lines[i].strip()!='```': i+=1
        i+=1
        while not lines[i].strip(): i+=1
        cap=lines[i].strip()
        cap=re.sub(r'^\*\*Figure \d+\. ', '**',cap)
        body += [r'\begin{figure}[H]\centering',r'\resizebox{\linewidth}{!}{'+DIAGRAMS[diagram]+'}',r'\caption{'+inline(cap)+'}',r'\end{figure}']
        diagram+=1;i+=1;continue
    if line==r'\[':
        eq=[];i+=1
        while lines[i].strip()!=r'\]': eq.append(lines[i]);i+=1
        body.append('\\begin{equation}\n'+'\n'.join(eq)+'\n\\end{equation}')
        i+=1;continue
    if line.startswith('|'):
        t=[]
        while i<len(lines) and lines[i].strip().startswith('|'): t.append(lines[i]);i+=1
        body.append(table(t));continue
    if line.startswith('### '): body.append(r'\subsection{'+inline(line[4:])+'}');i+=1;continue
    if line.startswith('## '):
        title=line[3:]
        body.append(r'\section{'+inline(title)+'}');i+=1;continue
    if line.startswith('!['):
        match=re.match(r'!\[(.*?)\]\((.*?)\)',line);caption,name=match.groups()
        landscape=name in ['comparison_9000rpm.png','comparison_9500rpm.png']
        body.append(r'\clearpage')
        if landscape: body.append(r'\begin{landscape}')
        shutil.copy2(SOURCE/name,WORK/name)
        dims='width=23.8cm,height=15.3cm' if landscape else r'width=\linewidth,height=.79\textheight'
        body += [r'\begin{figure}[H]\centering',r'\includegraphics['+dims+',keepaspectratio]{'+name+'}',r'\caption{'+inline(caption)+r'. Saved simulation results; invalid traces are truncated at the first failed validity check.}',r'\end{figure}']
        if landscape: body.append(r'\end{landscape}')
        i+=1;continue
    p=[line];i+=1
    while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','```','\\[','![')):
        p.append(lines[i].strip());i+=1
    paragraph=' '.join(p).replace('NaN entries denote invalid full runs, not zero error.', 'Dashes in the tables denote unavailable full-run scores, not zero error; the source CSV files retain NaN values.')
    if paragraph.startswith('Linearizing the GP gives e_virtual approximately'):
        paragraph=r'The local gains below follow Eq. (25): \(K_{d,N}=K_pc_a\), \(K_{p,N}=K_pc_N+K_ic_a\), and \(K_{i,N}=K_ic_N\). They describe the ideal continuous-time interpretation; the implemented derivative filter and sampling modify that approximation. This explains how the new PI changes both transient damping and integral action.'
    body.append(inline(paragraph)+'\n')

assert diagram==5
tex=PREAMBLE+'\n'.join(body)+r'\end{document}'
(WORK/'Virtual_Fuel_Controller_Report.tex').write_text(tex,encoding='utf-8')
print(WORK/'Virtual_Fuel_Controller_Report.tex')
