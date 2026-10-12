# T-MATS master's revision V2

This is the standalone editable source for the 182-page revised report. It contains 15 thematic chapters, six appendices, 48 numbered figures and 53 numbered tables, plus unnumbered synthesis and examination-response tables.

Compile from this directory three times:

```sh
pdflatex -no-shell-escape TMATS_Masters_Thesis_V2.tex
```

No MATLAB, new simulations, fitting, tuning or online downloads are needed when the LaTeX packages are installed. The supplied PDF has navigation bookmarks added during release checking; typesetting alone reproduces the content but does not add those postprocessed bookmarks.

The report addresses the Version 1 jury-style assessment through a focused question, literature comparison, evidence-role ledger, attribution analysis and point-by-point response in Appendix A. Missing equal-budget comparisons, robustness tests and a human oral defence are not claimed to have been completed. This is not an institutional acceptance decision.

`evidence_manifest.json` preserves the original workspace evidence provenance. `v2_revision_manifest.json` records this package's file hashes. `release_checks.json` records the final PDF checks. The evidence, data and review directories are supporting historical material; references there to an earlier V2 concern the September paper, not this master's revision. The complete simulation installation and all raw workspace data are not included in this document bundle.

The workspace assembly, release and packaging scripts are archived separately under `study/`; they expect the original workspace layout and are not needed to compile this source package. Version 1 is preserved in `thesis/` and as a separate PDF.
