# Thesis jury-style examination and literature assessment

**Date:** 11 October 2026
**Assessor:** OpenAI Codex, at the project owner's request
**Submission assessed:** [Complete T-MATS thesis-style report](../study/output/pdf/TMATS_Complete_Thesis.pdf), with its documented experiments and a targeted comparison with relevant literature.
**Assessment baseline:** Repository commit `1dc32c7`.

This document preserves the assessment delivered in the project conversation. It is an AI-generated jury-style written assessment, not an institutional examination, independent human peer review, or degree decision. No oral defence was conducted. University regulations could affect a formal outcome. No new simulations were performed for this assessment. The literature comparison is targeted, not an exhaustive proof of novelty or absence of novelty.

## Recommendation

**Master's thesis: major revision and resubmission. PhD thesis: reject in its current form.**

The project contains substantial engineering work and useful findings, but it has not yet established a sufficiently clear, original research contribution for a doctorate.

The distinction between a comprehensive report and a successful thesis matters here. The report documents the project extensively. A thesis must additionally organize that evidence around a research question, identify what existing literature does not answer, and demonstrate a defensible contribution.

For context, the QAA doctoral benchmark requires an original contribution to knowledge, which can include an original application of existing knowledge. A new mathematical theorem is therefore not mandatory, but the originality must be demonstrated. This is a reference benchmark, not an assertion about the regulations of a particular university. [QAA doctoral characteristics](https://www.qaa.ac.uk/the-quality-code/characteristics-statements/characteristics-statement-doctoral-degrees).

| Assessment dimension | Jury finding |
|---|---|
| Engineering implementation | Substantial and technically credible |
| Reproducibility and preservation | A major strength |
| Reporting failed and unfavourable results | A major strength |
| Identification of a focused research gap | Insufficient |
| Fair attribution of controller improvements | Incomplete |
| Methodological originality | Limited; one promising candidate |
| Generalization and robustness evidence | Too narrow for broad claims |
| Master's-level potential | Strong after substantial revision |
| Doctoral contribution demonstrated | No |

## Comparison with relevant literature

Most controller components are established methods.

| Thesis component | Relevant prior work | Novelty assessment |
|---|---|---|
| Sparse identification and orthogonal term selection | Chen, Billings and Luo established orthogonal least-squares identification methods in 1989. [Original paper](https://www.southampton.ac.uk/~sqc/listP/IJC1989-50-5.pdf) | The particular turbine implementation and selected structure are application results; the identification principle is not new. |
| Identified inverse model, filtered DOB and PI | Inverse-model disturbance estimation and its relationship to other disturbance-rejection methods are extensively documented. [Chen et al., overview](https://doi.org/10.1109/TIE.2015.2478397) | Identifying at 9800 rpm, selecting the filter and retuning PI constitute engineering design, not a new DOB theory. |
| Gaussian-process feedforward | GP feedforward has already been applied to engine airpath control. [Aran and Ünel, 2018](https://research.sabanciuniv.edu/35801/) | Applying it to this turbine can provide application-specific evidence, but “GP feedforward for engine control” is not a defensible novelty claim. |
| PILCO-style policy optimization | GP dynamics, uncertain-state propagation and policy optimization are central to original PILCO. [Deisenroth and Rasmussen, 2011](https://icml.cc/2011/papers/323_icmlpaper.pdf) | The study adapts an established framework to a restricted controller family. |
| Penalties for smoother learned control | Temporal and spatial action regularization already appear in CAPS. [Mysore et al., 2021](https://ai.bu.edu/caps/) | Penalizing control oscillation is not itself novel. The particular expected excess-variation construction deserves closer examination. |
| Advanced control of simulated turbine engines | NASA studies already investigate model-based control, estimation and deterioration-sensitive engine control. [NASA engine-control study](https://ntrs.nasa.gov/citations/20140009131) | Using a turbine simulation platform does not establish novelty; the contribution must lie in the method or the knowledge extracted from the experiments. |

These sources do not establish that someone has already published the exact implementation. They establish that its major building blocks are prior art. Combining known methods can be original, but a new combination needs a demonstrated advantage or new understanding beyond successful implementation.

## Most plausible methodological contribution: expected ringing penalty

The construction evaluates excess fuel variation over an event window:

$$
R=\sum_{k=1}^{m}|u_k-u_{k-1}|-|u_m-u_0|.
$$

It distinguishes repeated reversals from a necessary monotonic change. Under the Gaussian approximation, the expected absolute increments can be evaluated analytically while retaining the previous command and event-start command in the augmented state.

That is a more specific contribution than “adding a smoothness penalty to PILCO.” However:

- Absolute Gaussian moments and state augmentation are established mathematical tools.
- Existing action-smoothness methods already address the broader problem.
- The thesis does not establish whether this exact construction is new.
- It does not demonstrate an advantage over simpler penalties such as squared command increments, ordinary total variation, or direct gain optimization under the same objective.

There is also a conceptual limitation worth explaining: **zero excess variation does not imply a gentle command.** A large, abrupt, monotonic fuel change can have zero excess variation. The metric measures reversals, not maximum slew, actuator wear, or fuel consumption.

The classification is therefore **a plausible incremental methodological contribution requiring further literature comparison and validation**, not an established doctoral innovation.

## Strongest demonstrated contribution: comparative evidence

Several findings undermine an “advanced methods are superior” thesis.

| Existing result | What it establishes |
|---|---|
| R3 target-case RMSE is approximately **1.752 rpm**, while matched filtered PID gives **1.749 rpm** | That operating-point improvement cannot convincingly be attributed to the GP representation. |
| Smooth PILCO reduces the original policy's ringing by about **86%**, but its 10% pulse ringing remains approximately **2.084**, versus **2.070** for base PI | The penalty repairs an aggressive policy; it does not establish superiority over conventional PI. |
| DOB plus original PI reduces combined-cycle RMSE from **5.408 to 4.546 rpm**; retuning further reduces it to **3.142 rpm** | There is evidence of observer benefit and additional tuning benefit. |
| The final DOB controller's load ringing increases from approximately **0.945 to 2.184** | Its tracking improvement comes with substantially greater actuator activity. |
| The quadratic inverse performs competitively despite worse regression accuracy | Prediction accuracy alone is an inadequate basis for selecting a control model. |
| Controller rankings change when scoring actual versus sensed ramp speed | Measurement dynamics and the definition of tracking error materially affect the conclusion. |

The numerical values above are rounded from the existing project record. Ringing values denote the corresponding study's fuel excess-variation metric, in lbm/s, not fuel consumed. Different study windows must not be treated as interchangeable. Consult the [complete report](../study/output/pdf/TMATS_Complete_Thesis.pdf), [study map](COMPLETE_STUDY_MAP.md), and [DOB98 saved comparison](../study/results/dob98_pi_20261010/comparison.csv) for context.

These are valuable findings. A carefully framed thesis about **the conditions under which model complexity improves closed-loop performance** would be stronger than a thesis presenting a sequence of increasingly advanced controllers.

## Main examination objections

### 1. Baseline comparison and attribution

The baseline comparison is not consistently balanced. The inherited PI is often compared with controllers selected using additional tuning and a particular evaluation scenario. This supports a comparison of those saved configurations; it does not isolate the benefit of their architectures.

The latest DOB experiment partly addresses this by preserving DOB with the original PI gains. That is good experimental design. Nevertheless, an equally retuned PI-only comparator is missing from the same search protocol.

### 2. Selection results versus generalization

Some headline results are also selection results. Selecting gains on a scenario and reporting their best performance on that scenario is legitimate optimization, but it is weaker evidence of generalization. The held-out amplitude checks help, although they do not establish performance across a broad independent operating distribution.

### 3. Local identification versus the control envelope

Excellent local identification is sometimes much narrower than the later control task. The 9800-rpm model was identified over approximately **9796.7–9803.1 rpm**. Its excellent validation fit does not establish accuracy throughout a **9000–10000 rpm** acceleration or under a substantial load disturbance. Successful operation there is useful empirical evidence, but the local fit percentage cannot explain or guarantee that success.

### 4. Implementation verification versus physical validation

Recurrence replay, filtered-inverse identities and Monte Carlo agreement with GP moment calculations verify important calculations. They do not demonstrate robustness to plant deterioration, sensor bias, actuator dynamics or unmodelled disturbances.

### 5. PILCO terminology

The implemented method uses offline historical data, a fixed quadratic feedforward component and optimization of two PI gains with numerical gradients. Original PILCO emphasizes analytical policy gradients and iterative data-efficient learning. “PILCO-style GP-based offline PI tuning” is a defensible description; implying reproduction of the original learning framework would be misleading. [Original PILCO paper](https://icml.cc/2011/papers/323_icmlpaper.pdf).

### 6. Thesis focus

The manuscript has the breadth of a research archive more than the focus of a thesis argument. Preserving every study is valuable, but the central contribution becomes difficult to identify. More pages, videos and controller variants do not resolve that problem.

## Master's recommendation and required revisions

For a master's degree, the recommendation is major revisions rather than rejection of the project outright. The existing work has enough technical substance for a credible master's thesis. Acceptance would require:

1. A focused research question and an explicit contribution statement.
2. A literature comparison that separates established methods, adaptations and potentially original elements.
3. Clear labels distinguishing model training, controller selection and held-out evaluation.
4. Conclusions limited to the tested configurations and operating conditions.
5. A central discussion of the matched-PID, feedforward-ablation, sensor and DOB-retuning evidence.
6. A defence demonstrating independent understanding of inversion, uncertainty propagation, saturation and performance metrics.

**Most of these revisions can be completed from the existing archive without new simulations.** If the thesis retains claims of architectural superiority or broad robustness, additional experiments would be necessary. Alternatively, those claims can be narrowed. These are recommendations for future work, not experiments performed as part of this assessment.

A suitable framing would be:

*Identification, Disturbance Rejection and Learning-Based Control of a Simulated Gas Turbine: A Comparative Study of Tracking and Actuator Activity.*

## PhD recommendation

For a PhD, the recommendation is rejection of the current submission because the original contribution has not been established.

The problem is not simply the absence of hardware. A simulation-based doctorate can be valid. Nor does every control doctorate require a global stability theorem. The problem is that the current evidence does not yet support a sufficiently distinct methodological or generalizable scientific advance.

A viable doctoral direction might develop the expected excess-variation objective into a rigorously characterized method, or develop control-oriented model-selection criteria explaining when inverse-model accuracy fails to predict closed-loop performance. Either direction would require a focused literature gap, discriminating comparisons and evidence beyond the present sequence of tuning studies.

## Questions for an oral defence

- Why does the matched PID reproduce the GP controller's target-case performance?
- What does the GP uncertainty represent, and which plant uncertainties does it omit?
- How much of the DOB improvement remains after equally retuning PI alone?
- Can the ringing penalty miss a damaging fuel command?
- What precise contribution remains after removing the established identification, GP, PILCO and DOB machinery?

## Written jury-style decision

> The submission demonstrates substantial engineering competence and a valuable reproducible comparative study. It is suitable for revision into a master's thesis. It does not presently demonstrate the clearly established original contribution required for a PhD.

This assessment does not modify the archived results or certify completion of the recommended revisions. See also the repository's [AI disclosure](AI_DISCLOSURE.md).
