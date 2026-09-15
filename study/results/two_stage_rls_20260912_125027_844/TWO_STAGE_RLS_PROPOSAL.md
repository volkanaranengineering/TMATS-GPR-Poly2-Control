# Two-stage lag selection and recursive weight estimation

Prepared 12 September 2026 for the T-MATS fuel-flow to shaft-acceleration problem. This is a literature-grounded design proposal and mathematical derivation, not a newly fitted or simulated model. Example selected lags below are illustrative.

The recommended architecture is a slow structure selector followed by a fast reduced-dimension RLS estimator. Stage 1 chooses which input/output delays exist and how many coefficients to retain. Stage 2 estimates only those coefficients. Structure selection necessarily uses provisional parameter estimates or residual projections; it cannot generally be performed independently of coefficient fitting.

## Related literature

| Work | Relationship to this proposal |
|---|---|
| Chen, Billings and Luo, *Orthogonal least squares methods and their application to non-linear system identification*, International Journal of Control 50(5), 1873–1896, 1989. [DOI](https://doi.org/10.1080/00207178908953472); [author research-report version, 1988](https://eprints.whiterose.ac.uk/id/eprint/78100/) | Orthogonal least-squares methods combine selection of model terms with parameter estimation. This is the foundation for choosing individual delayed regressors rather than merely consecutive orders. |
| Luo and Billings, *Adaptive model selection and estimation for nonlinear systems using a sliding data window*, Signal Processing 46(2), 179–202, 1995. [Publisher](https://www.sciencedirect.com/science/article/pii/016516849500081N) | Online model-structure and parameter adaptation using a sliding rectangular data window and Givens rotations. A close precedent for adaptive selection plus estimation. |
| Luo, Billings and Tsang, *On-line Structure Detection and Parameter Estimation with Exponential Windowing for Nonlinear Systems*, European Journal of Control 2(4), 291–304, 1996. [Publisher](https://www.sciencedirect.com/science/article/pii/S0947358096700547) | Recursive orthogonal estimation with exponential windowing and online structure changes. Particularly close to the proposed streaming selector. |
| Babadi, Kalouptsidis and Tarokh, *SPARLS: The Sparse RLS Algorithm*, IEEE Transactions on Signal Processing 58(8), 4013–4025, 2010. [Author publication record](https://scholars.duke.edu/individual/pub1289734); [2009 preprint](https://arxiv.org/abs/0901.0734) | Related alternative: recursive L1-regularized estimation of sparse tap weights. Sparsity and weight estimation are coupled, whereas this proposal exposes the selected support explicitly and then uses ordinary RLS on it. |

This focused literature check establishes that the general concept has clear precedents; it is not a novelty claim. The particular scheduling, acceptance criteria and turbine-specific choices below are proposed engineering decisions, not a verbatim implementation of one paper. The source descriptions above are supported by accessible abstracts/author records; no claims of reproducing inaccessible full-text algorithms are made.

## 1. Project variables and candidate dictionary

Retain the existing physical definitions:

\[
T_s=0.015\ {m s},\qquad
u_k=\frac{W_{f,k}-W_{f,0}}{1\ {m lbm/s}},\qquad
y_k=\frac{\dot N_k}{1000\ {m rpm/s}},
\]

where the previous preparation gave \(W_{f,0}=0.9810869146824126\) lbm/s. Freeze normalization during identification; changing it without transforming the coefficient/covariance states changes the model.

The previous model always used output lags 1–5 and fuel lags 1–5. Instead start with maximum candidate delay \(L=10\):

\[
\psi_k=[-y_{k-1},\ldots,-y_{k-10},u_{k-1},\ldots,u_{k-10}]^T\in\mathbb R^{20}.
\]

No current output appears in the dictionary. Fuel lag zero is excluded to retain the previous causal delay convention. It could be tested separately if the sampled plant's direct feedthrough warrants it. No intercept or quadratic terms are added in this linear ARX proposal.

For a support set \(S\subset\{1,\ldots,20\}\), let \(E_S\) extract its entries:

\[
\phi_k=E_S\psi_k\in\mathbb R^m,\qquad m=|S|\le10,
\qquad \hat y_{k|k-1}=\phi_k^T\hat\theta_{k-1}.
\]

Stage 1 returns \(S\), not just \(m\). Decode it into separate delay lists:

\[
D_y=S\cap\{1,\ldots,10\},\qquad
D_u=\{j-10:j\in S,\ j>10\}.
\]

Require at least one fuel regressor for a fuel-to-acceleration model. An output-only predictor might obtain a high one-step score but would not identify the requested input-response relation. Allow the data to determine the number of output lags; a pure FIR candidate is possible.

Here \(L=10\) covers only 0.150 s. It is a candidate search horizon, not a claim that the turbine has only 0.150 s of physical memory. Longer or logarithmically spaced candidate delays may be needed. Also, coefficient count and polynomial order are different: six coefficients with a largest output lag of ten can define a tenth-order denominator.

## 2. Stage 1: compact information storage

At accepted samples, maintain

\[
G_k=\lambda_sG_{k-1}+\psi_k\psi_k^T,\quad
g_k=\lambda_sg_{k-1}+\psi_ky_k,\quad
q_k=\lambda_sq_{k-1}+y_k^2,
\]

initialized to zero. For a fixed dictionary these are the sufficient statistics for the exponentially weighted quadratic prediction-error objective. Thus

\[
J_S(\theta)=q-2\theta^Tg_S+\theta^TG_{SS}\theta.
\]

When \(G_{SS}\) is nonsingular,

\[
\theta_S^{LS}=G_{SS}^{-1}g_S,\qquad
\operatorname{SSE}(S)=q-g_S^TG_{SS}^{-1}g_S.
\]

Do not explicitly invert matrices in implementation; solve factored systems. These equations explain the selection criterion. With this project's ill-conditioned lag dictionary, recursive QR/Givens factors of the augmented rows \([\psi_k^T,y_k]\) are preferred to forming normal equations, which square the design-matrix condition number. Update the factor by appending the new row beneath \(\sqrt{\lambda_s}\) times the old factor. The factor preserves the same weighted quadratic information with memory bounded independently of record length.

Use \(\lambda_s=1\) for the first stationary, finite training experiment. For later drifting operation, a proposed starting value is 0.9995, approximately 30 s of exponential memory. This is not a tested optimum. Invalid samples must not enter the statistics. Retain the existing latched reference-failure gate, and do not bridge invalid gaps with delayed regressors.

Sufficient statistics preserve training least-squares information, not time ordering. A bounded time-ordered buffer or separate record is still needed for free-run validation and residual checks. A ring buffer also retains the last \(L\) values of both raw input and output.

## 3. Selecting individual delays

For a currently selected set \(S\) and an unused candidate \(j\), define

\[
d_j=G_{jj}-G_{jS}G_{SS}^{-1}G_{Sj},\qquad
r_j=g_j-G_{jS}G_{SS}^{-1}g_S.
\]

The quantity \(d_j\) is the candidate's energy after projection onto the already selected regressors; \(r_j\) is its correlation with the remaining output residual. Adding a coefficient \(\alpha\) to this residualized candidate gives

\[
J_{S+j}=\operatorname{SSE}(S)-2\alpha r_j+\alpha^2d_j.
\]

Therefore

\[
\alpha^*=r_j/d_j,\qquad
\boxed{\Delta_j=\operatorname{SSE}(S)-\operatorname{SSE}(S\cup\{j\})=r_j^2/d_j}.
\]

This is the useful selection rule: choose the lag giving the largest additional residual reduction after accounting for the other lags. It is invariant to nonzero rescaling of an individual candidate. It is not the same as selecting the largest current RLS coefficient or largest raw input/output correlation.

Reject candidates with zero energy or \(d_j/G_{jj}\le\epsilon_{col}\), for example \(\epsilon_{col}=10^{-6}\) as an initial numerical screening threshold. Use QR residual norms to evaluate this robustly; do not subtract nearly equal Gram-matrix terms in production. Threshold sensitivity must be checked, since related but useful dynamic regressors can also be highly correlated.

One concrete greedy search is:

1. Start with the single fuel lag having the largest \(g_j^2/G_{jj}\), provided its energy is adequate.
2. Add the remaining candidate with the largest admissible \(\Delta_j\).
3. Refit all selected coefficients and retain the resulting support as a candidate.
4. Continue until ten coefficients or no numerically independent candidate remains.

This produces a path \(S_1,S_2,\ldots,S_{m_{max}}\). A backward deletion or one-for-one swap pass can improve it. It is a greedy approximation, not a proof of the globally best subset. Provisional coefficients are essential to assess structure; Stage 2 supplies the final online tracking estimates.

## 4. Selecting the total number of terms

Training SSE always decreases when valid regressors are added. It cannot by itself select model size. Use a separate selection record, preserving the final validation record for one final report.

For each candidate support, first obtain its chirp-fitted coefficients using the intended Stage-2 RLS forgetting factor and prior, then freeze them and compute fuel-only free-run acceleration on the selection record. The Stage-1 least-squares coefficients used to rank terms are provisional; using the Stage-2 fit here makes the selection score representative of the estimator that will actually run:

\[
V(S)=\frac{\sum_{k\in\mathcal V}(y_k-\tilde y_k(S))^2}
{\sum_{k\in\mathcal V}(y_k-\bar y_{\mathcal V})^2}.
\]

In this recursion, substitute past predicted acceleration for the output-history regressors. Define the initial state from the same preceding equilibrium for every candidate. Reject unstable or nonfinite simulations. For sparse ARX denominators, insert zeros at unselected lags before checking polynomial roots.

Let \(V_{best}\) be the smallest admissible score on the candidate path. Choose

\[
S^*=\arg\min_{S\in\{S_1,\ldots,S_{m_{max}}\}} |S|
\quad\text{subject to}\quad V(S)\le V_{best}+\delta_V.
\]

For example, start with an absolute normalized-MSE tolerance \(\delta_V=0.01\), then assess sensitivity on selection data. This is a declared engineering tolerance, not a statistical confidence rule or a guarantee that the smallest possible model was found. Among equal-size acceptable candidates, prefer better conditioning and then lower validation error. If none meets the application error requirements, report insufficient model adequacy rather than accepting a small but poor model.

The earlier project has separate ramp-selection and ramp-validation experiments. Use the former here for selection; reserve the latter for the final frozen-model result. Existing published validation scores are historical baselines, not new two-stage scores. Because both records are already known in this exploratory project, a newly generated untouched test record would be stronger evidence for any final tuned design.

## 5. Stage 2: RLS on the chosen support

For fixed \(S^*\), use only \(\phi_k=E_{S^*}\psi_k\). At each valid sample:

\[
\hat y_{k|k-1}=\phi_k^T\hat\theta_{k-1},\qquad
e_k=y_k-\hat y_{k|k-1},
\]

\[
P_k^-=P_{k-1}/\lambda_w,\quad
v_k=P_k^-\phi_k,\quad s_k=1+\phi_k^Tv_k,\quad K_k=v_k/s_k,
\]

\[
\boxed{\hat\theta_k=\hat\theta_{k-1}+K_ke_k},\qquad
\boxed{P_k=P_k^--v_kv_k^T/s_k}.
\]

These are ordinary RLS equations with \(m\) parameters. Initial comparison settings are \(\lambda_w=0.999\), \(\hat\theta_0=0\), \(P_0=10^4I_m\), as in the previous study. Multiply normalized predictions by 1000 rpm/s. Symmetrization and positive-definiteness monitoring remain useful; square-root RLS is preferable if numerical problems occur.

The rank-one covariance form above costs O(m²). It is algebraically equivalent to the earlier Joseph form in exact arithmetic with unit innovation-noise scale. Implementing Joseph form literally as multiple dense matrix multiplications can cost O(m³); a smaller covariance alone does not make every implementation quadratically efficient.

Publish the prediction before assimilating the current output. The measured output is used for the coefficient correction and stored for subsequent regressors. Keep free-run simulation separate from this measured-history one-step predictor.

## 6. Illustrative sparse turbine model

Suppose Stage 1 selected

\[
D_y=\{1,3,10\},\qquad D_u=\{1,4,10\},\qquad m=6.
\]

Then

\[
\phi_k=[-y_{k-1},-y_{k-3},-y_{k-10},u_{k-1},u_{k-4},u_{k-10}]^T,
\]

\[
\theta=[a_1,a_3,a_{10},b_1,b_4,b_{10}]^T,
\]

\[
y_k=-a_1y_{k-1}-a_3y_{k-3}-a_{10}y_{k-10}
+b_1u_{k-1}+b_4u_{k-4}+b_{10}u_{k-10}+e_k.
\]

The physical output delays are 15, 45 and 150 ms; fuel delays are 15, 60 and 150 ms. The transfer polynomials are

\[
A(z^{-1})=1+a_1z^{-1}+a_3z^{-3}+a_{10}z^{-10},\quad
B(z^{-1})=b_1z^{-1}+b_4z^{-4}+b_{10}z^{-10}.
\]

In physical units,

\[
\widehat{\dot N}_k=-\sum_{i\in D_y}a_i\dot N_{k-i}
+1000\sum_{j\in D_u}b_j(W_{f,k-j}-W_{f,0}),
\]

when numerical fuel values are expressed in lbm/s. Stage 2 uses a 6-by-6 covariance and six gains. The illustrated support has not been selected from the data, and no new fit value is claimed for it.

## 7. Structure changes and data reuse

For the first prototype, identify the support during a dedicated learning phase and then freeze it. That delivers the clearest compute benefit and avoids changes of regressor meaning during RLS tracking.

For continuous operation, inspect structure less frequently, for example every 100 samples (1.5 s), and require persistent improvement before a switch. A proposed policy is the same acceptable candidate at three consecutive checks, a minimum dwell time of 3 s and a free-run selection-score improvement exceeding a declared threshold. These are starting settings, not validated values. Structure updates require sufficient excitation and valid reference data; deteriorating error alone does not prove a changed structure.

Use a consistent transfer of estimator state when support changes. Do not relabel old coefficient slots or take an arbitrary principal submatrix of the old covariance: in general, a submatrix of an inverse information matrix is not the inverse of the selected information submatrix.

For an accepted new support, rebuild from a bounded historical buffer \(\mathcal B\), using the Stage-2 forgetting factor:

\[
H=\lambda_w^n\delta I+
\sum_{r=1}^{n}\lambda_w^{n-r}\phi_r\phi_r^T,\qquad
h=\sum_{r=1}^{n}\lambda_w^{n-r}\phi_ry_r,
\]

\[
P=H^{-1},\qquad \theta=H^{-1}h,\qquad \delta=10^{-4}.
\]

This is a zero-mean prior with P0=10000*I aged across n consecutive accepted buffer samples. Solve with QR/Cholesky rather than explicit inversion. Resume online updates at the next sample after the buffer endpoint. Replaying those same samples again would double-count them. If a reduced buffer replaces a longer history, document that intentional reset of information.

Rebuilding from Stage-1 information with a different forgetting factor is possible, but then the initialization represents Stage-1 weighting, not the same full-history Stage-2 objective. The bounded-buffer rule avoids this ambiguity.

## 8. Simulink structure and computational tradeoffs

```text
Actual fuel, direct Ndot, solver validity
                  |
       Sample / normalize / delay buffers
                  |
           Candidate dictionary
             /             \
     Slow selector       Active lag selector <--- support S
     QR information             |
     Forward selection    Reduced-size RLS
     Size/validity tests   (weights and covariance)
             |                  |
      Support supervisor   Prior prediction / error
             ^                  |
             +--- monitoring ---+
```

The fast path maps naturally to the existing basic-block observer: Unit Delay histories, Selector blocks, matrix-vector/outer-product arithmetic, state delays and validity switches. The slow combinatorial supervisor is separate. A script-based offline first stage is the simplest first prototype; a fully basic-block online selector would require additional controlled iterations and matrix-factorization logic.

Merely zeroing unused entries in a 20-by-20 RLS block does not reduce its dimension or necessarily its arithmetic. For fixed-size generated Simulink code, specialize the active estimator after selection, or use an enabled bank of supported dimensions. A fixed ten-slot implementation remains bounded but may not realize savings when m is six.

| Quantity | Earlier fixed model | Example selected model |
|---|---:|---:|
| Active coefficients | 10 | 6 |
| Dense Stage-2 covariance entries | 100 | 36 |
| Approximate rank-one RLS quadratic work ratio | 1 | 0.36 |
| Maximum stored delay per signal | 5 samples | 10 samples |

The 64% reduction refers to Stage-2 covariance entries and the quadratic kernel's scaling, not measured whole-model speedup. While active, a full 20-candidate selector has its own O(20²) information storage/update work, plus periodic search costs and validation storage. The always-running two-stage system can cost more than the previous ten-regressor RLS. The efficient initial architecture is learn structure, freeze it, suspend the selector, and reactivate only when needed. Delay history storage follows the largest retained lag, not the number of coefficients.

## 9. Evaluation plan using this project

The previous valid chirp prefix ends at 17.790 s (1187 samples), with reference failure at 17.805 s. Its one-step fit was 99.8729%, frozen chirp free-run fit 88.3707%, and frozen ramp validation fit 62.6192%. The ten-column regressor condition number was approximately 1.0167e6. These observations motivate a parsimonious and better-conditioned model but do not guarantee sparse selection improves free-run behavior.

1. Retain only valid contiguous data and preserve the same normalization, demand and input/output definitions.
2. Form candidate lags from the chirp training data. Generate sparse supports using QR-based forward selection, capped at ten terms.
3. Choose support size with the separate ramp-selection record, considering free-run error, stability and conditioning.
4. Freeze that support and estimate its weights with RLS on training data. If support was selected using the complete chirp, replaying that chirp is an offline training experiment; it is not a fully causal online-selection demonstration.
5. Freeze the final coefficients and report held-out ramp free-run results, alongside one-step prediction, actual selected delays, parameter count, conditioning, covariance behavior and measured execution cost.
6. Test online support changes separately on a longer valid stream. The current short prefix is inadequate evidence for repeated support convergence across the requested 0.1–1 Hz sweep.

```text
LEARN:
    gather valid contiguous chirp information with a fixed dictionary
    construct a QR forward-selection path, with at least one fuel term
    choose the smallest acceptable stable support on selection data
    freeze support and initialize/replay the reduced RLS exactly once

TRACK, at each new valid sample:
    extract only the selected historical input/output values
    publish the prior prediction
    update selected weights and covariance
    advance history and monitoring statistics

IF STRUCTURE RELEARNING IS ENABLED:
    maintain bounded selection data/information
    assess new support periodically, with hysteresis
    rebuild state consistently before accepting a support change

ON REFERENCE FAILURE:
    freeze learning and flag prediction invalid, as in the prior model
```

No structural selection can manufacture missing excitation or repair a failed reference simulation. The proposed two-stage system primarily targets unnecessary coefficients and redundant delays; nonlinear operating-point effects and equilibrium mismatch may still need a different model class.
