"""Create a separate V2 manuscript; preserve V1 and all simulation evidence."""
from pathlib import Path
import shutil, json, hashlib
ROOT=Path(__file__).resolve().parent
WORK=ROOT/'tmp/pdfs/control_evolution_v2'
WORK.mkdir(parents=True,exist_ok=True)
old=ROOT/'tmp/pdfs/control_evolution'
for p in old.iterdir():
    if p.is_file() and p.suffix in ['.tex','.pdf','.json'] and p.name!='control_evolution_paper.pdf':
        shutil.copy2(p,WORK/p.name)
for name in ['data','code']:
    shutil.copytree(old/name,WORK/name,dirs_exist_ok=True)
s=(ROOT/'control_evolution_paper.tex').read_text(encoding='utf-8')
def replace(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:100])
    s=s.replace(a,b)
replace('T-MATS CONTROLLER DEVELOPMENT / LONG-FORM RESEARCH SYNTHESIS','T-MATS CONTROLLER DEVELOPMENT / REVISED EDITION V2')
replace(r'Document status & Simulation research synthesis; not hardware validation',r'Document status & V2: revised after three AI referee-role reviews')
replace(r'\textbf{Keywords:}',r'''\textbf{Revision provenance.} Three separate AI-assisted reviewers reused the previous industry-engineer, control-theory academic, and newly graduated PhD researcher roles. Their findings were checked against implementation and archived evidence. V2 corrects algorithm and signal-timing definitions, clarifies fallback and actuator-demand limits, and adds sensitivity reanalysis of existing trajectories. It does not claim independent human peer review. No model, gains, or plant simulation was changed. The companion response records each finding and disposition.

\textbf{Keywords:}''')
replace(r'$T,P$ & Actual inlet temperature and pressure at the model query & K, kPa\\',r'$T,P$ & Sample-delayed inlet values used by the online inverse & K, kPa\\')
replace('At each sample, define $p=',r'''For four-input online controllers, the inlet measurements pass through one-sample Unit Delay blocks after conversion to K and kPa. Writing current plant inlet values as $T_{\rm in},P_{\rm in}$, the query notation used throughout the controller equations is
\begin{equation}
T[k]=T_{\rm in}[k-1],\qquad P[k]=P_{\rm in}[k-1],
\end{equation}
with initialized values 288.15 K and 99.298 kPa. Offline identification rows use their contemporaneous recorded inlet values. Thus replay of online queries must shift logged inlet signals by one sample; the archived cycle coverage audit does so. At changing ambient conditions this timing distinction is part of the implemented algorithm, even though it is small at the 15 ms sample interval.

At each sample, define $p=''')
replace('Window length and sample interval are part of its definition.',r'''Window length and sample interval are part of its definition. The fixed-load ``peak fuel slew'' is likewise evaluated only within those same six two-second windows:
\begin{equation}
S_L=\max_j\max_{k,k-1\in W_j}\frac{|u[k]-u[k-1]|}{T_s}.
\end{equation}
It is not the maximum across the complete evaluation trace. Cycle peak slew, in contrast, uses the entire scored cycle. These different domains must be retained when comparing tables.''')
replace('The monitored corrected-speed coordinate is $N_c=N_s/(10000\\sqrt{T/288.15})$, with a working map range $[0.5,1.05]$.',r'''The logged plant-map audit uses actual speed and current inlet temperature,
$N_{c,\rm log}=N/(10000\sqrt{T_{\rm in}/288.15})$, with a working range $[0.5,1.05]$.
The online fallback guard instead uses sensed speed and sample-delayed temperature,
$N_{c,\rm guard}=N_s/(10000\sqrt{T/288.15})$.
They are distinct signals, so zero logged map overrun and zero fallback need not coincide.''')
replace(r'''\gamma[k]=\mathbf1\!\left[(u^\star<u_{\max}\ \lor\ e_v<0)
\land(u^\star>u_{\min}\ \lor\ e_v>0)\right].''',r'''\gamma(u^\star,e_i)=\mathbf1\!\left[(u^\star<u_{\max}\ \lor\ e_i<0)
\land(u^\star>u_{\min}\ \lor\ e_i>0)\right].''')
replace('Then $I[k+1]=I[k]+\\gamma[k]T_sK_i e_v[k]$.',r'''Here $e_i$ is the error actually integrated and $u^\star$ contains every enabled FF and feedback contribution. All implemented integral gains are positive. The general update is
$I[k+1]=I[k]+\gamma(u^\star[k],e_i[k])T_sK_i e_i[k]$.
Use $e_i=e_v$ for the original virtual PI, R1, and both SD schedules; use $e_i=e_0$ for R2; and use the selected normalized or fallback speed error for R3 and Poly2. For the original controller this reduces to $I[k+1]=I[k]+\gamma(u^\star[k],e_v[k])T_sK_i e_v[k]$.
The later shorthand $\gamma$ always denotes this architecture-specific gate.''')
replace('if the corrected compressor speed leaves $[0.5,1.05]$',r'if the controller coordinate $N_{c,\rm guard}$ leaves $[0.5,1.05]$')
replace('Near a well-behaved operating point,',r'''The decision is recomputed at every sample, with no hysteresis, dwell time, or blending. The current integral and static FF are retained; there is no integral reset to compensate for a change of feedback coordinates. This differs from the proportional-gain compensation used in the SD schedules. At fixed signals and integral, switching from finite normalized coordinates to raw coordinates would change the unsaturated command by
\begin{equation}
\Delta u^\star=K_p[(r-N_s)-e_N^g]-K_d[\hat a-a^g].
\end{equation}
This identity explains a possible transition discontinuity; it is not a calculation performed at a singular denominator, nor evidence that switching caused the measured ringing. Transition smoothness, chattering, and switched-loop robustness require separate validation. The training-box flag is logged only, and joint-hull coverage is audited offline; neither is an online fallback trigger or domain-containment mechanism.

Near a well-behaved operating point,''')
replace('The measured tradeoff, rather than a generic damping intuition, justifies the conclusion.',r'''The measured tradeoff, rather than a generic damping intuition, justifies the conclusion.

The fuel-demand tradeoff also depends on the comparator. The selected setting reduces two-second-window peak fuel slew from 8.71872 to 7.27362 lbm/s$^2$ relative to original Poly2, but its slew remains 51.0\% above base PI's 4.81750 lbm/s$^2$, despite the 37.3\% reduction in fuel reversal. Fewer reversals therefore do not imply lower instantaneous actuator-rate demand. Fuel magnitude limits are inactive in these three evaluation traces; this does not test a physical valve rate constraint. Peak speed errors are 0.2314\%, 0.1526\%, and 0.1711\% of 9250 rpm for base PI, original Poly2, and retuned Poly2, respectively. These effect sizes describe simulation behavior, not compliance with a supplied product requirement.''')
replace(r'\section{Coverage and implementation qualification}',r'''\section{Sensitivity to ringing windows and recovery bands}
\label{sec:sensitivity}
The referee revision reanalyzes the saved base, original-Poly2, and retuned-Poly2 trajectories at both load amplitudes. Models, gains, event timing, and the original objective are unchanged. Only the reporting window or recovery band changes; the results do not enter candidate selection.
\input{table_sensitivity_ring}
Retuned Poly2 has less summed excess variation than original Poly2 and base PI for each tested window of 0.5, 1, 2, and 3 s at both amplitudes. Thus the local reversal ranking is not peculiar to the original two-second choice over this tested range. This is a window-sensitivity check on deterministic traces, not evidence about different sampling rates, noisy measurements, or physical actuator motion.
\input{table_sensitivity_recovery}
The recovery ordering is less universal. At 10\% load and a 0.1 rpm band, retuned Poly2 recovers in 0.930 s versus 1.365 s for original Poly2. At 0.5 rpm it remains faster (0.810 versus 1.080 s), but at 1 rpm it is slightly slower (0.675 versus 0.630 s). At 5\% load it is faster at all three fine bands tested. Every method remains inside the 1\% speed band in both tests, hence the zero entries. The larger initial peak and shorter final tail can therefore reverse a settling-time ranking when the acceptance band changes. Recovery claims must name that band explicitly.

\section{Coverage and implementation qualification}''')
replace('The deployable study model is','The configured desktop Simulink study model is')
replace('A future actuator-oriented evaluation could add spectral energy, cycle counting, or bandwidth-weighted command variation, but these were not measured here.',r'''The saved-trace sensitivity analysis in Section~\ref{sec:sensitivity} retains the final ringing ranking across four window lengths, but reverses the original-versus-retuned fine-recovery ordering at the 1 rpm band for 10\% load. Neither a lower reversal score nor a faster 0.1 rpm recovery entails better performance under every metric definition. A future actuator-oriented evaluation could add spectral energy, cycle counting, or bandwidth-weighted command variation, but these were not measured here.''')
replace('but raise peak error and have not yet transferred across the earlier grid.',r'''but raise peak error relative to original Poly2 and retain 51\% higher edge-window peak fuel slew than base PI. Recovery ordering depends on the specified band, and the new gains have not yet transferred across the earlier grid.''')
replace(r'\section{Reproducing the paper}',r'''\section{V2 review evidence}
The companion response records three separate AI role reviews and the author dispositions. The review files are preserved under \path{reviews/} in the source package. The supplementary \path{metric_sensitivity.csv} and its trace-hash manifest document the calculations in Section~\ref{sec:sensitivity}. The six supporting archived traces are included as \path{review_traces/}; they are unchanged simulator outputs, not additional experiments. The revision changes exposition and derived reporting only. The original paper and original numerical source tables remain preserved.

\section{Reproducing the paper}''')
replace('Tables are generated from the archived CSV files by \\path{build_control_evolution_paper.py}.',r'''The original tables are generated from archived CSV files by \path{build_control_evolution_paper.py}; V2 assembly is performed by \path{revise_control_evolution_paper.py}. The supplementary sensitivity tables are generated by \path{review_control_evolution_metrics.py}.''')
(ROOT/'control_evolution_paper_v2.tex').write_text(s,encoding='utf-8')
(WORK/'control_evolution_paper.tex').write_text(s,encoding='utf-8')
d=(ROOT/'control_evolution_diagrams.tex').read_text()
start=d.index(r'\newcommand{\diagramBaseline}')
end=d.index(r'\newcommand{\diagramVirtual}')
d=d[:start]+r'''\newcommand{\diagramBaseline}{%
\begin{tikzpicture}[x=1cm,y=1cm]
\node[sum] (e) at (0,0) {$\Sigma$};
\node[block] (pi) at (2.5,0) {Speed PI\\$K_{pN}+K_{iN}/s$};
\node[sum] (add) at (5,0) {$+$};
\node[block] (lim) at (7.4,0) {Fuel limits};
\node[plant] (plant) at (10.7,0) {T-MATS engine};
\node[block] (sensor) at (5,-2.1) {Speed sensor};
\node[gp,text width=45mm] (ff) at (5,2.4) {Early inverse correction\\$g(N_q,a_r)-g(N_0,0)$\\enable $\eta$; clamp $\pm0.15$};
\node[font=\small,align=center] (inputs) at (0,2.4) {$N_q=\mathrm{clip}(N_s)$\\$a_r=\mathrm{clip}(\Delta r/T_s)$\\fixed $g(N_0,0)$};
\draw[arr](inputs)--(ff);\draw[arr](ff)--(add);
\draw[arr](-1.1,0)--node[above]{$r$}(e);\draw[arr](e)--(pi);\draw[arr](pi)--(add);\draw[arr](add)--(lim);\draw[arr](lim)--node[above]{$u$}(plant);
\draw[arr](plant.south)|-(sensor.east);\draw[arr](sensor.west)-|node[pos=.92,left]{$-$}(e.south);
\draw[arr](10.7,1.3)--node[right]{$P_L$}(plant.north);
\node[font=\small,align=center] at (6,-3.2) {The early correction depends on sensed speed.\\Unknown load acts on the plant only.};
\end{tikzpicture}}

'''+d[end:]
d=d.replace(r'$I^+=I+T_s K_i e_N^g$',r'$I^+=I+\gamma T_s K_i e_N^g$')
(ROOT/'control_evolution_diagrams_v2.tex').write_text(d)
(WORK/'control_evolution_diagrams.tex').write_text(d)
review=ROOT/'reviews/control_evolution_v2'
for p in review.glob('table_*.tex'):shutil.copy2(p,WORK/p.name)
table=WORK/'table_tune.tex'
table.write_text(table.read_text().replace('Peak slew (','Edge-window peak slew ('))
shutil.copytree(review,WORK/'reviews',dirs_exist_ok=True)
(WORK/'review_traces').mkdir(exist_ok=True)
for name,info in json.loads((review/'metric_sensitivity_manifest.json').read_text()).items():
    shutil.copy2(ROOT/info['path'],WORK/'review_traces'/name)
for name in ['review_control_evolution_metrics.py','revise_control_evolution_paper.py','tmats_environment_vf_patch.m','tmats_environment_data.m','audit_tmats_cycle_coverage.m']:
    shutil.copy2(ROOT/name,WORK/'code'/name)
manifest=json.loads((WORK/'evidence_manifest.json').read_text())
manifest['manuscript']={'path':'control_evolution_paper_v2.tex','sha256':hashlib.sha256((WORK/'control_evolution_paper.tex').read_bytes()).hexdigest()}
for p in [WORK/'control_evolution_diagrams.tex',*sorted((WORK/'reviews').glob('*')),*sorted((WORK/'review_traces').glob('*')),*sorted((WORK/'code').glob('*'))]:
    if p.is_file():manifest['V2_'+p.relative_to(WORK).as_posix()]={'path':p.relative_to(WORK).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(WORK/'evidence_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Created V2 manuscript and assembly:',WORK)
