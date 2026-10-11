"""Assemble existing evidence only. Never runs a model, fit, or optimization."""
from pathlib import Path
import re,json,shutil,hashlib,textwrap,csv
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/pdf/tmats_complete_thesis_source'
OUT.mkdir(parents=True,exist_ok=True)
V2=ROOT/'tmp/pdfs/control_evolution_v2'
evidence={}
def record(p):
    p=Path(p)
    if p.is_file(): evidence[str(p.relative_to(ROOT)).replace('\\','/')]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def esc(s):
    s=str(s)
    replacements={'–':'--','—':'---','−':'-','±':r'$\pm$','×':r'$\times$','≤':r'$\le$','≥':r'$\ge$','α':r'$\alpha$','λ':r'$\lambda$','θ':r'$\theta$','φ':r'$\phi$','Σ':r'$\Sigma$','₀':'0','₁':'1','₂':'2','Δ':r'$\Delta$','ω':r'$\omega$','π':r'$\pi$','→':r'$\rightarrow$','≈':r'$\simeq$','²':r'$^2$','³':r'$^3$','‘':"'",'’':"'",'“':'``','”':"''",'…':'...','‑':'-','‖':'|','∈':r'$\in$','·':r'$\cdot$'}
    s=''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in s)
    for a,b in replacements.items():s=s.replace(a,b)
    return s.replace(r'\_',r'\_\allowbreak ')
def inline(s):
    parts=re.split(r'(`[^`]+`|https?://[^\s]+)',s)
    out=''
    for x in parts:
        if x.startswith('`'):
            value=x[1:-1].replace(str(ROOT)+'\\','').replace('\\','/').replace('|','/')
            if re.fullmatch('[A-Fa-f0-9]{64}',value):out+=r'\par{\footnotesize\ttfamily '+value+r'}\par '
            elif ' ' in value:
                formatted=' '.join(r'\texttt{'+esc(v)+'}' for v in value.split())
                out+=(r'\par\begingroup\small\raggedright '+formatted+r'\par\endgroup ' if len(value)>75 else formatted)
            else:out+=r'\path|'+value+'|'
        elif x.startswith('http'):out+=r'\url{'+x+'}'
        else:out+=re.sub(r'\*\*(.*?)\*\*',lambda m:r'\textbf{'+m[1]+'}',esc(x))
    return out
def md_chapter(path,title):
    path=ROOT/path;record(path)
    raw=path.read_text(encoding='utf-8-sig'); lines=raw.splitlines(); out=[r'\chapter{'+title+'}',r'\textit{Evidence basis: }\path|'+str(path.relative_to(ROOT)).replace('\\','/')+'|. The following detailed account is adapted from the archived study; references to simulation and verification describe historical work.\par']
    i=0;inlist=False;section='Study results';tableindex=0
    while i<len(lines):
        s=lines[i].strip()
        if s.startswith('# '):i+=1;continue
        if s.startswith('!['):
            m=re.search(r'!\[(.*?)\]\((.*?)\)',s)
            p=path.parent/m[2]
            if p.exists():
                dest='early_'+path.parent.name+'_'+p.name;shutil.copy2(p,OUT/dest);record(p)
                out.append(r'\begin{figure}[H]\centering\includegraphics[width=.95\linewidth,height=.6\textheight,keepaspectratio]{'+dest+'}'+r'\caption{'+esc(m[1])+r'. Archived study figure.}\end{figure}')
            i+=1;continue
        if s.startswith('```') or lines[i].startswith('    '):
            block=[]
            if s.startswith('```'):
                i+=1
                while i<len(lines) and not lines[i].strip().startswith('```'):block.append(lines[i]);i+=1
                i+=1
            else:
                while i<len(lines) and (lines[i].startswith('    ') or not lines[i].strip()):block.append(lines[i][4:]);i+=1
            # Verbatim formula/code is kept as an implementation record, with prose equations in primers.
            ascii_block='\n'.join(block).translate(str.maketrans({'θ':'theta','φ':'phi','λ':'lambda','−':'-','–':'-','±':'+/-','≤':'<=','≥':'>=','×':'*','Σ':'Sigma'}))
            ascii_block=ascii_block.encode('ascii','replace').decode()
            wrapped='\n'.join('\n'.join(textwrap.wrap(x,94,replace_whitespace=False,drop_whitespace=False)) if len(x)>94 else x for x in ascii_block.splitlines())
            out.append('\\begin{quote}\\footnotesize\n\\begin{verbatim}\n'+wrapped+'\n\\end{verbatim}\n\\end{quote}')
            continue
        if s.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+',c) for c in cells):rows.append(cells)
                i+=1
            n=len(rows[0]); tableindex+=1
            # Fixed-width paragraphs keep lengthy headings readable; longtable allows page breaks.
            widths=([18]+[(160-3*n-18)/(n-1)]*(n-1)) if n>10 else [(160-3*n)/n]*n
            fmt=''.join(r'>{\raggedright\arraybackslash}p{'+f'{w:.2f}mm'+'}' for w in widths)
            out.append(r'{\scriptsize\setlength{\tabcolsep}{1.5mm}\begin{longtable}{'+fmt+'}'+r'\caption{'+esc(title+': '+section)+r'. Archived values.}\\\toprule')
            header=' & '.join(inline(c) for c in rows[0])+r'\\\midrule'
            out.extend([header,r'\endfirsthead',header,r'\endhead'])
            for row in rows[1:]:out.append(' & '.join(inline(c) for c in row)+r'\\')
            out.append(r'\bottomrule\end{longtable}}');continue
        if s.startswith('##'):
            section=s.lstrip('# ')
            out.append(('\\subsection{' if s.startswith('###') else '\\section{')+esc(s.lstrip('# '))+'}');i+=1;continue
        if s.startswith('- '):
            out.append(r'\par\noindent\textbullet\ '+inline(s[2:]));i+=1;continue
        s=s.replace('fuel/temperature/compressor-margin','fuel, temperature, and compressor-margin').replace('fuel/temperature/compressor-','fuel, temperature, and compressor-')
        s=s.replace('dN/dt = 60/(2*pi*30)*5252.113*(Pc+Pt)/N','the shaft power-balance equation derived in the foundations')
        out.append(inline(s));i+=1
    return '\n'.join(out)+'\n'

# Keep the audited September tables, diagrams, and vector illustrations.
for p in V2.iterdir():
    if p.suffix=='.tex' or (p.suffix=='.pdf' and p.name not in ('control_evolution_paper.pdf','response_to_referees.pdf')):
        shutil.copy2(p,OUT/p.name);record(p)
for name in ['thesis_foundations.tex','thesis_observer_bridges.tex','thesis_gp_primer.tex','thesis_final_synthesis.tex','thesis_latest_details.tex']:
    shutil.copy2(ROOT/name,OUT/name);record(ROOT/name)
for folder in ['data','review_traces','reviews']:
    if (V2/folder).exists():shutil.copytree(V2/folder,OUT/folder,dirs_exist_ok=True)
dobrows=list(csv.DictReader((ROOT/'results/dob98_pi_20261010/tuning.csv').open()))
dt=[r'\begin{table}[htbp]\centering\small\begin{tabular}{rrrrrrr}\toprule Case & $K_p$ & $K_i$ & Full RMSE & Ramp RMSE & $R_{\rm seg}$ & Objective\\\midrule']
for row in dobrows:
    dt.append(' & '.join([row['case_index'],f"{float(row['Kp']):.3f}",f"{float(row['Ki']):.3f}"]+[f"{float(row[x]):.4f}" for x in ['rmse_rpm','ramp_rmse_rpm','fuel_excess_TV','objective']])+r'\\')
dt.append(r'\bottomrule\end{tabular}\caption{All archived DOB98 PI candidates. RMSE is rpm; $R_{\rm seg}$ is lbm/s. Candidate 11 is selected by the stated objective.}\end{table}')
(OUT/'table_dob98_search.tex').write_text('\n'.join(dt))

early=[
('wiener_ramps_20260908_214558_458','Wiener identification: a nonlinear output map after linear dynamics'),
('rls_acceleration_20260908_225810_094','Online acceleration identification with ten-term RLS'),
('rls_blocks_acceleration_20260909_063846_871','Realizing the estimator with ordinary Simulink blocks'),
('two_stage_rls_20260912_125027_844','Two-stage sparse RLS: conditioning and held-out prediction'),
('dob_refined_20260912_175532_449','The first filtered-inverse DOB and governed-reference tests'),
('dob_pto_20260912_182940_001','External shaft-load rejection at 10000 rpm'),
('PTO_20_30_comparison','The rejected 20 and 30 percent tests at 10000 rpm'),
('PTO_9500rpm_comparison','Moving the shaft-load experiment to 9500 rpm'),
('PTO_9000rpm_ramp_comparison','The 9000-rpm ramped-load envelope'),
('literature_observers_9000rpm_10pct_20260912_211600_355','LESO, UDE, and GPIO implementation and first comparison'),
('Observer_9000_9500_GPR_FF_Comparison','Observer transfer and the direct GPR feedforward challenger')]
early_inputs=[]
for j,(folder,title) in enumerate(early):
    fn=f'early_{j:02d}.tex';(OUT/fn).write_text(md_chapter(Path('results')/folder/'REPORT.md',title),encoding='utf8')
    if j==4:early_inputs.append(r'\input{thesis_observer_bridges}')
    if j!=10:early_inputs.append(r'\input{'+fn+'}')
gp=[]
for j,(folder,title) in enumerate([('exact_gpr_20260913_145742_458','Forward exact GP: speed and fuel to acceleration'),('inverse_gpr_20260913_150824_698','Inverse exact GP: desired motion to nominal fuel')]):
    fn=f'gp_{j}.tex';(OUT/fn).write_text(md_chapter(Path('results')/folder/'REPORT.md',title),encoding='utf8');gp.append(r'\input{'+fn+'}')

v2=(V2/'control_evolution_paper.tex').read_text(encoding='utf8')
body=v2[v2.index(r'\chapter{Research problem'):v2.index(r'\appendix')]
chapters=re.split(r'(?=\\chapter\{)',body)
chapters=[x for x in chapters if x.strip()]
# Retain the coherent audited body; its opening stage-specific framing is explicitly dated.
body='\n'.join(chapters[:12])
body=body.replace(r'\chapter{Research problem and experimental logic}',r'\chapter{The inverse-model control programme: questions and protocol}'+'\n'+r'The narrative now follows the September inverse-control programme through its final 9250-rpm polynomial retune. This portion retains the corrected V2 definitions and detailed ablations. Its phase-specific conclusions are followed by the October policy-learning and transfer studies, then a synthesis of the whole project.'+'\n')
body=body.replace(r'\chapter{Plant, signals, and evaluation protocol}',r'\chapter{Protocol for the inverse-model controller comparisons}')
body=body.replace(r'\chapter{Inverse identification and the baseline controllers}',r'\chapter{From inverse identification to feedback architecture}')
body=body.replace('the complete development','the GPR-to-Poly2 development')
(OUT/'gpr_poly2_narrative.tex').write_text(body,encoding='utf8')
(OUT/'gpr_poly2_assessment.tex').write_text('\n'.join(chapters[12:]).replace('Critical assessment of the complete development','Assessment of the September GPR-to-Poly2 phase').replace('Concise synthesis and five takeaways','Lessons established before the October transfer tests'),encoding='utf8')
appendix=v2[v2.index(r'\appendix')+len(r'\appendix'):v2.index(r'\input{control_evolution_references}')]
appendix=appendix.replace('stated in Chapter 11','stated in the full-quadratic-inverse chapter')
(OUT/'historical_appendices.tex').write_text(appendix,encoding='utf8')

latest=[('pilco_quadratic_pi_source','PILCO_Quadratic_FF_PI.tex','PILCO-style policy learning: full derivation and first results'),('pilco_smooth_source','PILCO_Smooth_Ringing_Penalty.tex','Learning smoother control with an expected ringing penalty'),('ramp90_equal_sensor_source','Ramp90_Comparison.tex','Five-second no-load acceleration and the common-sensor audit'),('combined_cycle_source','Combined_Cycle.tex','Combined acceleration and a five-second load pulse'),('dob98_pi_source','DOB98_PI_Comparison.tex','A new inverse model at 9800 rpm and PI tuning after DOB engagement')]
latest_inputs=[]
for j,(folder,tex,title) in enumerate(latest):
    p=ROOT/'output/pdf'/folder/tex;record(p);s=p.read_text(encoding='utf8');s=s.split(r'\begin{document}',1)[1].split(r'\end{document}')[0]
    s=re.sub(r'\\maketitle','',s)
    s=s.split(r'\begin{thebibliography}')[0]
    s=s.replace(r'\begin{abstract}',r'\section*{Chapter overview}').replace(r'\end{abstract}','')
    for fig in p.parent.glob('*.pdf'):
        if fig.stem in ['PILCO_Quadratic_FF_PI','PILCO_Smooth_Ringing_Penalty','Ramp90_Comparison','Combined_Cycle','DOB98_PI_Comparison']:continue
        name=f'late{j}_{fig.name}';shutil.copy2(fig,OUT/name);record(fig);s=s.replace('{'+fig.name+'}','{'+name+'}')
    s=s.replace(r'\clearpage\section',r'\section')
    # Correct ambiguous feedback notation in the short ramp report.
    if j==2:s=s.replace('r_k-N_k','r_k-N_{s,k}')
    s=s.replace('preceding derivation paper','preceding policy-learning chapter')
    # Embedded figures are limited to a page-safe height without changing their data.
    s=s.replace('[width=\\linewidth]','[width=\\linewidth,height=.68\\textheight,keepaspectratio]').replace('[width=\\textwidth]','[width=\\textwidth,height=.68\\textheight,keepaspectratio]')
    fn=f'latest_{j}.tex';(OUT/fn).write_text(r'\chapter{'+title+'}\n'+r'\textit{Archived October study. All simulations, searches, and checks described below predate this report.}\par'+'\n'+s,encoding='utf8');latest_inputs.append(r'\input{'+fn+'}')

# Entire directory inventory, including empty and superseded records.
inventory=json.loads((ROOT/'tmp/thesis_evidence/inventory.json').read_text())
reg=[r'\chapter{Complete study-directory register}',r'The register covers every direct directory under the project results folder at assembly time. Counts are file counts, not independent simulations. Aggregate reports and repeated attempts are retained for provenance. A timestamp alone does not establish acceptance. The detailed reports and validity columns control interpretation.']
for item in inventory:
    d=item['directory'];files=list((ROOT/'results'/d).glob('*'))
    if item['file_count']==0:status='Empty pilot directory; no empirical result.'
    elif d.startswith(('Turkce','Comprehensive','Observer_','PTO_')):status='Derived comparison, tutorial, or presentation collection; not an independent set of plant trials.'
    elif d in ['r3_dynamic_ff_20260915','r3_covered_cycle_20260915']:status='Intermediate or superseded interpretation/scenario; use the final covered-cycle and static-feedforward studies for conclusions.'
    elif d.startswith(('chirp','prbs')):status='Excitation request or diagnostic record. Full-amplitude runs fail; only explicitly accepted prefixes are usable.'
    elif d.startswith(('baseline','step','ramp_selection','ramp_validation')):status='Plant preparation, numerical acceptance, or identification input record. See the early experiment narrative for accepted and rejected variants.'
    else:status='Study evidence; acceptance and tuning/validation roles are defined in the corresponding narrative and saved metrics.'
    reg += [r'\subsection*{\path|'+d+'|}',esc(status)+f' Archived file count: {item["file_count"]}.']
    evid=item.get('evidence',[])
    for q in evid:
        p=ROOT/q if isinstance(q,str) else None
        if p and p.exists():record(p)
    examples=[p.name for p in files if p.suffix.lower() in ['.md','.json','.csv']][:5]
    if examples:reg.append('Entry files: '+', '.join(r'\path|'+x+'|' for x in examples)+'.')
(OUT/'study_register.tex').write_text('\n'.join(reg),encoding='utf8')

refs=(OUT/'control_evolution_references.tex').read_text()
extra=r'''
\bibitem{tmatsguide} J. W. Chapman, T. M. Lavelle, R. D. May, J. S. Litt, and T.-H. Guo. Toolbox for the Modeling and Analysis of Thermodynamic Systems (T-MATS) User's Guide. NASA/TM-2014-216638, 2014. \url{https://ntrs.nasa.gov/citations/20140012486}.
\bibitem{pilco} M. P. Deisenroth and C. E. Rasmussen. PILCO: A Model-Based and Data-Efficient Approach to Policy Search. ICML, pp. 465--472, 2011. \url{https://icml.cc/2011/papers/323_icmlpaper.pdf}.
\bibitem{gao} Z. Gao. Scaling and bandwidth-parameterization based controller tuning. American Control Conference, 2003. \url{https://engagedscholarship.csuohio.edu/enece_facpub/528/}.
\bibitem{ude} Q.-C. Zhong and D. Rees. Control of uncertain LTI systems based on an uncertainty and disturbance estimator. Journal of Dynamic Systems, Measurement, and Control, 126, 2004. \url{https://doi.org/10.1115/1.1850529}.
\bibitem{project} T-MATS project computational archive, September--October 2026. Primary evidence: saved trajectories, identified coefficients, controller source, numerical checks, and the study register in this report. Project direction: Volkan Aran; AI-assisted implementation and documentation. SHA-256 index supplied as evidence\_manifest.json.
'''
refs=refs.replace(r'\end{thebibliography}',extra+r'\end{thebibliography}')
(OUT/'references.tex').write_text(refs,encoding='utf8')
preamble=v2.split(r'\begin{document}')[0]
preamble=preamble.replace('Inverse-model fuel control','T-MATS: complete research narrative').replace('T-MATS research synthesis','Retrospective thesis report')
preamble=preamble.replace('From Inverse GPR to Retuned Polynomial Fuel Control','T-MATS System Identification and Control: Complete Research Narrative')
preamble+=r'\newcommand{\E}{\mathbb{E}}\newcommand{\Cov}{\operatorname{Cov}}\newcommand{\Var}{\operatorname{Var}}'+'\n'
front=r'''
\begin{document}
\begin{titlepage}\sffamily\color{navy}
{\large T-MATS RESEARCH / COMPLETE RETROSPECTIVE}\par\vspace{16mm}
{\fontsize{29}{35}\selectfont\bfseries System Identification and Control of a Nonlinear Gas-Turbine Model\par}
\vspace{10mm}{\Large From numerical validation and recursive identification to inverse learning, ringing-aware policy search, and disturbance-observer control\par}
\vspace{10mm}\textcolor{teal}{\rule{\linewidth}{1.2pt}}\vspace{8mm}
\normalfont\color{black}
An undergraduate-accessible, thesis-style account of the complete archived project. Detailed mathematical derivations, implementation explanations, comparison tables, failed experiments, and limits of inference.
\vspace{10mm}
\begin{tabular}{@{}ll@{}}
Research direction & Volkan Aran\\[5pt]
Development and writing & AI-assisted under human direction\\[5pt]
Plant framework & T-MATS v1.3.3; MATLAB/Simulink R2018b archive\\[5pt]
Study record & September--October 2026\\[5pt]
Report date & 11 October 2026\\[5pt]
Latest controller & DOB identified at 9800 rpm + retuned PI
\end{tabular}
\vfill\textbf{Evidence-only edition.} No new simulations, fits, or tuning runs were added in preparing this document. Historical experimental claims are distinguished from mathematical explanation and proposed future work.
\end{titlepage}
\pagenumbering{roman}
\chapter*{Abstract}\addcontentsline{toc}{chapter}{Abstract}
This report follows a nonlinear gas-turbine control project from its initial numerical acceptance tests through identified-model observers, Gaussian-process inverse control, polynomial approximation, probabilistic PI policy learning, and a final disturbance observer identified at 9800 rpm. The unifying question is how much predictive models improve control once signal timing, numerical validity, actuator demand, tuning objectives, and operating coverage are treated explicitly.

Large abrupt speed excitations first expose limits of the numerical experiment. Accepted chirp prefixes and independent ramps then support Wiener and recursive ARX identification. Strong one-step prediction is distinguished from weaker free-running transfer. A physically constrained acceleration model enables causal filtered inversion, while PTO studies reveal both observer benefits and rejected high-load cases. Alternative LESO, UDE, and GPIO structures demonstrate metric-dependent tradeoffs.

Forward and inverse Gaussian processes achieve high local prediction accuracy, but direct feedforward and virtual-fuel control do not improve every closed-loop metric. Uncertainty schedules, lower fixed gains, environmental expansion, derivative-normalized feedback, and explicit coverage tests progressively clarify why. A quadratic inverse remains competitive despite poorer regression accuracy; local PID retuning improves load regulation and command ringing while increasing some actuator demands.

PILCO-style offline policy learning further reduces load-test RMSE but initially increases fuel reversals substantially. An expected excess-variation penalty restores smoother commands with slower correction. Frozen-policy acceleration tests favor base PI, and an explicit sensor audit confirms equal sensing rather than attributing the ranking to different sensor dynamics. The combined ramp/load cycle motivates a new local filtered-inverse DOB, followed by PI retuning: its full-cycle RMSE is 3.142 rpm versus 5.408 rpm for the inherited PI. This improvement remains a nominal scenario result rather than a global robustness guarantee.

The thesis explains the mathematics at undergraduate level, preserves unsuccessful results, supplies complete study provenance, and argues that model accuracy, controller structure, tuning, and validation must be evaluated separately. All empirical results are retrospective; no new plant experiment was added for this report.
\chapter*{Notation and units}\addcontentsline{toc}{chapter}{Notation and units}
\begin{longtable}{p{28mm}p{126mm}}\toprule Symbol & Meaning\\\midrule
$N,N_s,r$ & Actual shaft speed, sensed speed, and governed target; rpm.\\
$u,W_f,I$ & Fuel command/flow and controller integral contribution; lbm/s.\\
$\dot N,\hat a$ & Actual acceleration and causal estimated acceleration; rpm/s.\\
$T_s,q$ & Sample period 0.015 s; one-sample delay $q=z^{-1}$.\\
$T,P$ & Inlet absolute temperature and pressure; K and kPa for inverse models.\\
$P_t,P_c,P_L$ & Turbine, signed compressor, and external extraction power; model hp.\\
$K_p,K_i,K_d$ & Controller gains; units depend on speed or virtual-fuel error definition.\\
$P_n,H,Q$ & Nominal plant, sensor approximation, and observer low-pass filter.\\
$g,p_2$ & Learned inverse GP mean and full quadratic inverse.\\
$\mu,\Sigma$ & Gaussian mean vector and covariance matrix.\\
$R,\mathrm{TV}$ & Excess fuel variation and total variation; lbm/s, not consumed mass.\\
SM, PTO & Available compressor surge margin; external shaft power takeoff.\\
NR & No confirmed recovery within the stated record/band, where used in tables.\\\bottomrule
\end{longtable}
Symbols are reused locally in some historical derivations. Each chapter defines its state and normalization before use. In particular, the GP training matrix and controller gain must not be confused merely because both sometimes use the letter $K$.
\tableofcontents\clearpage\listoffigures\clearpage\listoftables
\clearpage\pagenumbering{arabic}
'''
main=preamble+front+r'\input{thesis_foundations}'+'\n'+'\n'.join(early_inputs)+'\n'+r'\input{thesis_gp_primer}'+'\n'+'\n'.join(gp)+'\n'+r'\input{early_10.tex}\input{gpr_poly2_narrative}'+'\n'+r'\input{gpr_poly2_assessment}'+'\n'+'\n'.join(latest_inputs)+'\n'+r'\input{thesis_latest_details}\input{thesis_final_synthesis}'+'\n'+r'\appendix\input{historical_appendices}\input{study_register}\input{references}\end{document}'
(OUT/'TMATS_Complete_Thesis.tex').write_text(main,encoding='utf8')
# Preserve all compact numerical evidence and narrative reports, including rejected cases.
for folder in (ROOT/'results').iterdir():
    if not folder.is_dir():continue
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in ('.csv','.json','.md') and p.stat().st_size<350000:
            record(p); dest=OUT/'evidence'/folder.name/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
for p in ROOT.glob('*.md'):record(p)
(OUT/'evidence_manifest.json').write_text(json.dumps(evidence,indent=2),encoding='utf8')
(OUT/'study_inventory.json').write_text(json.dumps(inventory,indent=2))
(OUT/'README.md').write_text('''# Complete T-MATS thesis source

Compile TMATS_Complete_Thesis.tex with pdflatex three times, without shell escape.
All figures and tables required for typesetting are included. No MATLAB or plant simulation is needed.

This is a retrospective synthesis. The assembly script reads archived material only.
The evidence folder preserves compact CSV/JSON/Markdown records. Full time histories remain in the project results folders and repository study archive. evidence_manifest.json records workspace-relative paths and SHA-256 hashes of source evidence. Historical reproduction commands in the text describe prior experiments; they are not prerequisites for compiling this report.

The September GPR-to-Poly2 V2 narrative is integrated with new undergraduate foundations, the early identification/observer reports, the October policy-learning/sensor/combined-cycle/DOB studies, and a complete study-directory register. Historical provenance and limitations remain explicit.
''',encoding='utf8')
print(json.dumps({'source':str(OUT),'study_directories':len(inventory),'evidence_files':len(evidence),'tex_words':sum(len(p.read_text(encoding='utf8').split()) for p in OUT.glob('*.tex'))},indent=2))
