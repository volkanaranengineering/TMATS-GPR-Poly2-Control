# Comprehensive GPR-to-Poly2 controller paper

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
