"""Assemble a jury-addressed second edition from archived evidence; no simulation."""
from pathlib import Path
import re, shutil, json, hashlib

ROOT = Path(__file__).resolve().parent
OLD = ROOT / 'output/pdf/tmats_complete_thesis_source'
OUT = ROOT / 'output/pdf/tmats_masters_thesis_v2_source'
NEW = ROOT / 'thesis_v2_revision'
OUT.mkdir(parents=True, exist_ok=True)
for p in OLD.rglob('*'):
    rel = p.relative_to(OLD)
    if p.is_dir():
        continue
    if p.suffix.lower() in {'.aux','.log','.toc','.lof','.lot','.out'} or p.name.startswith(('compile-', 'TMATS_Complete_Thesis.pdf','release_checks')):
        continue
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, target)

def read(name):
    return (OLD / name).read_text(encoding='utf-8')

def demote(s):
    # Substitute once so nested levels are not demoted repeatedly.
    mapping = {'chapter':'section','section':'subsection','subsection':'subsubsection','subsubsection':'paragraph'}
    return re.sub(r'\\(chapter|section|subsection|subsubsection)(\*?)(?=\{)', lambda m:'\\'+mapping[m[1]]+m[2], s)

def chapters(s):
    return [m.group(0) for m in re.finditer(r'\\chapter\{.*?(?=\\chapter\{|\Z)', s, re.S)]

def write(name, s):
    (OUT / name).write_text(s, encoding='utf-8')

def group(name, title, label, intro, texts, closing=''):
    write(name, '\\chapter{'+title+'}\n\\label{'+label+'}\n'+intro+'\n\n'+'\n\n'.join(demote(t) for t in texts)+'\n'+closing+'\n')

found = chapters(read('thesis_foundations.tex'))
group('v2_plant.tex','Plant, sensing, metrics, and numerical acceptance','ch:plant',
      r'This chapter specifies the physical and numerical experiment. Numerical acceptance precedes controller ranking: a failed flow solution is not a valid response to score. Historical experiments are described retrospectively; no test was rerun for Version 2.', found[1:])

group('v2_identification.tex','Identification quality and the limits of prediction','ch:identification',
      r'The first subsidiary question asks what can be inferred from a high prediction score. The following studies distinguish a fitted output map, online one-step prediction, frozen free-running prediction, and an implementable estimator. These are different achievements. Orthogonal term selection is an application of established identification ideas~\cite{ols}; the contribution here is the recorded comparison and implementation.',
      [read(f'early_{i:02d}.tex') for i in range(4)],
      r'\section{Answer supported by this evidence} Strong one-step prediction does not establish equally strong free-running transfer. Sparse selection improves the recorded conditioning and held-out acceleration result, while block replay verifies the realization. Neither result establishes robustness under untested noise or plant changes. The selected lag support was determined offline; the later coefficient recursion does not make support selection an online discovery procedure.')

group('v2_observers.tex','Disturbance estimation and the accepted load envelope','ch:observers',
      r'This chapter addresses whether an identified model can be inverted usefully. It separates the residual-estimation idea from the particular filter, model correction, and accepted plant envelope. DOB, LESO, UDE, and GPIO are established method families, not inventions of this study~\cite{doboverview,gao,ude}. Equal nominal pole settings do not imply equal closed-loop bandwidth.',
      [read('thesis_observer_bridges.tex')]+[read(f'early_{i:02d}.tex') for i in range(4,10)],
      r'\section{Interpretation of the observer comparison} The accepted runs provide local evidence that these configured observers can reduce the recorded disturbance error. The rejected high-load cases restrict the scope of that evidence. Since load percentages are defined relative to operating-point turbine power, identical percentages at 9000 and 9500 rpm are not identical physical extraction powers. The tables compare controllers within a scenario; they do not estimate a universal observer ranking.')

group('v2_gp.tex','Gaussian-process prediction and its control interpretation','ch:gp',
      r'The predictor is introduced before its use in feedback. A GP posterior describes uncertainty conditional on the kernel, likelihood, and training distribution~\cite{gpml}. It is not automatically a bound on unknown external load or a certificate for feedback stability. The two-input nominal tests below therefore answer a regression question before the later chapters answer a control question.',
      [read('thesis_gp_primer.tex'),read('gp_0.tex'),read('gp_1.tex'),read('early_10.tex')])

gpr = chapters(read('gpr_poly2_narrative.tex'))
group('v2_inverse.tex','Inverse-coordinate feedback, feedforward, and gain selection','ch:inverse',
      r'The central attribution question is whether improvement belongs to the inverse model, the feedback coordinates, or gain selection. This chapter retains the exact algorithm distinctions and the fixed-reference feedforward equivalence. Its conclusions concern the September controller family; the later PILCO-style chapter uses a separate dynamics GP.', gpr[1:6])
group('v2_environment.tex','Environmental transfer, matched PID, and coverage','ch:environment',
      r'The most informative comparator is not always the inherited PI. A matched filtered PID asks whether the GP representation contributes beyond equivalent local feedback action. Coverage diagnostics ask a separate question: whether a query lies within a stated training envelope. Neither substitutes for the other.', gpr[6:10])
group('v2_poly.tex','Polynomial replacement and local tuning tradeoffs','ch:poly',
      r'A simpler inverse is an explicit challenger to the assumption that lower regression error yields better control. First the representation changes with gains retained; only afterwards are gains retuned locally. The distinction makes the initial replacement a more informative model comparison than the final tuned-versus-inherited comparison.', gpr[10:])
group('v2_policy.tex','PILCO-style offline PI tuning and expected fuel reversal','ch:policy',
      r'This chapter studies a restricted adaptation of probabilistic policy evaluation, not a new PILCO algorithm. A frozen quadratic supplies feedforward, an offline GP predicts dynamics, and two PI gains are optimized numerically. The first experiment and the later ringing penalty are retained together so that the repair of an aggressive policy is not mistaken for a demonstrated advantage over conventional PI. The relationship to original PILCO and CAPS is evaluated in Chapter~\ref{ch:literature}.',
      [read('latest_0.tex'),read('latest_1.tex')])
group('v2_transfer.tex','Frozen-controller acceleration and the combined cycle','ch:transfer',
      r'These tests change the operating task after the earlier local controller development. The no-load ramp and common-sensor audit distinguish actual mechanical speed from the feedback measurement. The first combined cycle is a transfer test for the earlier frozen controllers; the same cycle later becomes a selection case for DOB98. Its evidential role therefore depends on the controller being discussed.',
      [read('latest_2.tex'),read('latest_3.tex')])
group('v2_dob98.tex','Local DOB98 design, PI retuning, and attribution','ch:dob98',
      r'The observer is identified around a physical speed of 9800 rpm; the number 98 does not describe model-fit accuracy. The independent multisine assesses the local predictor. The combined ramp/load cycle selects PI gains with the observer enabled and must be reported as selection evidence. The original-gain observer result is retained as a partial attribution check.',
      [read('latest_4.tex'),read('thesis_latest_details.tex')])

for p in NEW.glob('*.tex'):
    shutil.copy2(p, OUT / p.name)

# Avoid an orphaned closing filename, retaining the complete replay evidence.
p = OUT / 'v2_poly.tex'
s = p.read_text(encoding='utf-8')
s = s.replace(r'The configured desktop Simulink study model is \path{GasTurbine_Poly2_9250_Tuned.mdl}; the earlier defaults remain preserved.', r'The configured model and earlier defaults remain archived.')
p.write_text(s, encoding='utf-8')

hist = read('historical_appendices.tex')
hist = hist.replace(r'\section{V2 review evidence}',r'\section{September-paper V2 review evidence}')
hist = hist.replace(r'\section{Reproducing the paper}',r'\section{Reproducing the historical September paper}'+'\n'+r'This subsection describes the September manuscript, not the present master\textquotesingle s revision. To typeset this report, compile \path{TMATS_Masters_Thesis_V2.tex} three times from the supplied V2 source directory. The older filenames below are preserved for historical reproducibility.'+'\n')
write('historical_appendices.tex',hist)

refs = read('references.tex').replace('\\end{thebibliography}', r'''
\bibitem{ols} S. Chen, S. A. Billings, and W. Luo. Orthogonal least squares methods and their application to non-linear system identification. International Journal of Control, 50(5), 1873--1896, 1989. doi:10.1080/00207178908953472. \url{https://www.southampton.ac.uk/~sqc/listP/IJC1989-50-5.pdf}.
\bibitem{doboverview} W.-H. Chen, J. Yang, L. Guo, and S. Li. Disturbance-Observer-Based Control and Related Methods---An Overview. IEEE Transactions on Industrial Electronics, 63(2), 1083--1095, 2016. doi:10.1109/TIE.2015.2478397.
\bibitem{caps} S. Mysore, B. Mabsout, R. Mancuso, and K. Saenko. Regularizing Action Policies for Smooth Control with Reinforcement Learning. IEEE International Conference on Robotics and Automation, 2021. Authors' project and paper: \url{https://ai.bu.edu/caps/}.
\bibitem{nasaengine} NASA Technical Reports Server. Model-Based Control of a Nonlinear Aircraft Engine Simulation using an Optimal Tuner Kalman Filter Approach. Record 20140009131. \url{https://ntrs.nasa.gov/citations/20140009131}.
\bibitem{jury} OpenAI Codex, at the project owner's request. Thesis jury-style examination and literature assessment. 11 October 2026. AI-generated written review, not independent human peer review. \url{https://github.com/volkanaranengineering/TMATS-GPR-Poly2-Control/blob/b16e59e/docs/THESIS_JURY_EXAMINATION.md}.
\end{thebibliography}
''')
write('references.tex', refs)

oldmain = read('TMATS_Complete_Thesis.tex')
preamble = oldmain.split('\\begin{document}')[0]
preamble = preamble.replace('T-MATS System Identification and Control: Complete Research Narrative','T-MATS Comparative Control Study - Masters Revision V2')
preamble = preamble.replace('T-MATS: complete research narrative','T-MATS: comparative control study').replace('Retrospective thesis report',"Master's revision / V2")
preamble += '\n% PDF navigation is added after compilation by the release checker.\n\\clubpenalty=10000\\widowpenalty=10000\n'
notation = oldmain.split('\\chapter*{Notation and units}')[1].split('\\tableofcontents')[0]
main = preamble + '\n\\begin{document}\n\\input{v2_frontmatter}\n\\chapter*{Notation and units}' + notation
main += r'''
\tableofcontents\clearpage\listoffigures\clearpage\listoftables
\clearpage\pagenumbering{arabic}
\input{v2_question}
\input{v2_literature}
\input{v2_protocol}
\input{v2_plant}
\input{v2_identification}
\input{v2_observers}
\input{v2_gp}
\input{v2_inverse}
\input{v2_environment}
\input{v2_poly}
\input{v2_policy}
\input{v2_transfer}
\input{v2_dob98}
\input{v2_synthesis}
\input{v2_conclusions}
\appendix
\input{v2_jury_response}
\input{historical_appendices}
\input{study_register}
\input{references}
\end{document}
'''
write('TMATS_Masters_Thesis_V2.tex', main)

# Keep algorithm and evidence wording consistent with the retrospective scope.
for p in OUT.glob('v2_*.tex'):
    s=p.read_text(encoding='utf-8')
    s=re.sub(r'Run \\path\|run_tmats_pto_9500_batch\|[^\n]+', lambda m:r'Batch reproduction uses \path{run_tmats_pto_9500_batch}. For one load level, call \path{run_tmats_pto_study(0.2,9500)} and then \path{analyze_tmats_pto(out)}, assigning the returned result to \path{out}; use 0.3 for the larger load. For an already loaded model, \path{tmats_pto_setup([],0.2,9500)} loads the measured speed-specific power reference. The no-argument setup retains the original 10000 rpm, 10\% case.', s)
    s=re.sub(r'Original PILCO(?!-style)', 'Original PILCO-style PI', s)
    s=s.replace('The present controllers do not perform that form of long-horizon probabilistic planning.', 'The September inverse controllers do not perform that form of probabilistic planning; the later offline policy study is a separate adaptation.')
    p.write_text(s,encoding='utf-8')

manifest={
    'edition':'Masters revision V2',
    'original_pdf_sha256':hashlib.sha256((ROOT/'output/pdf/TMATS_Complete_Thesis.pdf').read_bytes()).hexdigest(),
    'new_simulations':0,'new_identification_fits':0,'new_tuning_runs':0,
    'source_evidence_manifest':'evidence_manifest.json',
    'editorial_changes':['Focused research question and contribution boundaries','Targeted literature and novelty matrix','Explicit model-fitting, selection and evaluation ledger','Thematic consolidation of technical studies','Cross-study attribution and metric interpretation','Point-by-point jury response and unresolved requirements'],
    'files':{str(p.relative_to(OUT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file() and p.suffix not in {'.log','.aux','.toc','.lof','.lot','.out'}}
}
write('v2_revision_manifest.json',json.dumps(manifest,indent=2))
print('Assembled:',OUT)
