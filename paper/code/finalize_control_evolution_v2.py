"""Use the verified V1 navigation pipeline with explicit V2 destinations."""
from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'finalize_control_evolution_paper.py').read_text()
source=source.replace("work=root/'tmp/pdfs/control_evolution'","work=root/'tmp/pdfs/control_evolution_v2'")
source=source.replace('TMATS_GPR_to_Poly2_Comprehensive_Paper.pdf','TMATS_GPR_to_Poly2_Comprehensive_Paper_V2.pdf')
source=source.replace('TMATS_GPR_to_Poly2_Paper_LaTeX_Evidence.zip','TMATS_GPR_to_Poly2_Paper_V2_LaTeX_Evidence.zip')
source=source.replace("'/Title':'From Inverse Gaussian-Process Fuel Coordinates to Retuned Polynomial Control'","'/Title':'From Inverse Gaussian-Process Fuel Coordinates to Retuned Polynomial Control - Revised V2'")
source=source.replace('all 19 generated','all 21 generated')
source=source.replace('# Comprehensive GPR-to-Poly2 controller paper','# Revised V2 GPR-to-Poly2 controller paper')
source=source.replace('The original native simulation traces remain in the','Six archived traces supporting the V2 sensitivity checks are included in review_traces/. Other native simulation traces remain in the')
source=source.replace('study result directories listed in the paper.','study result directories listed in the paper.\n\nV2 includes the three AI referee-role reports, their back-checks, point-by-point author responses, corrected signal and algorithm definitions, and supplementary metric-sensitivity tables. No controller simulation or tuning was changed. The companion review response is compiled from response_to_referees.tex.\n\nFor workspace reconstruction, run review_control_evolution_metrics.py and revise_control_evolution_paper.py; compile the assembled manuscript twice, then run finalize_control_evolution_v2.py. The source package itself can be typeset without running these workspace-dependent assembly scripts.')
exec(compile(source,str(root/'finalize_control_evolution_paper.py'),'exec'),{'__file__':str(root/'finalize_control_evolution_paper.py'),'__name__':'__main__'})
