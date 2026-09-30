# Contributing to IT2

The repository contains a preserved paper snapshot and an inspectable research implementation. Changes should be small, explicit and reproducible.

## Report a problem

Include the command, full traceback, operating system and versions of Python, IfcOpenShell, NumPy, SciPy, Matplotlib and Streamlit. If relevant, attach the protected runner's report and identify the model and experiment settings. Do not upload private IFC files without permission.

## Propose a change

1. Explain the concrete problem and the expected behavior.
2. Keep `results/` and `figures/` unchanged unless an explicitly documented paper correction requires a new version.
3. Use `python scripts/reproduce_study.py --mode saved-features` to compare downstream calculations in a separate folder.
4. For extraction/topology/file-level changes, also validate the affected raw-IFC stages and describe the scope of that validation.
5. Record changed assumptions, parameters or dependency requirements. Do not attribute numerical changes to randomness without checking the source.

Comments should explain intent, units, assumptions and non-obvious choices. Avoid narrating obvious syntax or making stronger claims than the experiment supports.

## Review conventions

Use descriptive commits. Include the validation performed and any numerical differences in pull requests. Keep model files under the existing `data/ifc/` exclusion. Future-work diagrams should stay clearly distinguished from implemented features.
