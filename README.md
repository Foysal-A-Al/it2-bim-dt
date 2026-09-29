# IT2: identity and topology integrity for BIM-based digital twins

Code, data pointers, results and figures for the paper
**"Identity and Topology Integrity as a Precondition for BIM-Based Digital Twins: A Controlled Study on Real MEP Models."**

A digital twin built on BIM assumes two things that are rarely checked. Elements keep their identity when the model is revised, and the ducts, pipes and equipment in the model are actually connected. This repository measures both on open IFC models and tests a two-stage matcher that recovers element identity after GlobalIds are lost.

## The IT2 checker app

A desktop app (runs in your browser, on your machine) built on the same code as the paper.

- **Topology check:** load one IFC model and see whether its distribution network is connected, with a pass or fail gate, the network pieces, and a list of disconnected elements.
- **Identity check:** load two versions of a model and see which elements kept their GlobalId, which were re-linked by Tag or by geometry, and which go to manual review. Or test one model against a simulated revision, with precision and recall against the known truth.
- **Study results:** the tables and figures of the paper.

### Windows with Anaconda

Open the **Anaconda Prompt**, go to the unzipped folder, and run:

```bat
cd path\to\it2-bim-dt
setup_windows.bat        :: once: creates the conda environment "it2" and downloads the study models
run_app_windows.bat      :: every time: opens the app in your browser
```

The environment `it2` then also appears in Anaconda Navigator, where you can open Jupyter or Spyder on the project.

### Mac or Linux

```bash
conda env create -f environment.yml
./run_app.sh
```

### Put it on GitHub

Install [Git](https://git-scm.com) and the [GitHub CLI](https://cli.github.com), then from the Anaconda Prompt in this folder run `publish_to_github.bat`. It logs you in if needed, creates the public repository `it2-bim-dt` under your account and pushes everything. The IFC models are gitignored and are not uploaded.

## What is in here

```
app/app.py               the IT2 checker app (Streamlit)
it2/                     the library
  topology.py            PC, CC, TF, LC, SM metrics from IFC port relations (IFC2x3 and IFC4)
  features.py            fingerprints: class, container, Tag, type name, placement, world bounding box
  matching.py            Tag key, placement baseline, IT2 hybrid matcher, revision simulator, scoring
scripts/                 one script per section of the paper
  01_topology.py         Section 5.2  topology audit of seven models
  02_extract_features.py fingerprints for the three identity models
  03_identity.py         Section 5.3  simulated revisions, 20 seeds, bootstrap CIs, Wilcoxon tests
  04_sensitivity_bv.py   Sections 5.5 and 5.6  lambda x tau grid, simulated binding validity
  05_roundtrip.py        Section 5.4  writes a perturbed IFC, re-opens and re-fingerprints it
  06_eval_roundtrip.py   compares file-level and feature-level results
  07_figures.py          all seven figures
data/download.py         fetches the IFC models from the buildingSMART repositories
data/features/           precomputed fingerprints (so steps 03 onwards run without the IFC files)
results/                 every JSON result used in the paper
figures/                 every figure used in the paper
```

## Quick start

```bash
git clone https://github.com/TODO/it2-bim-dt.git
cd it2-bim-dt
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

or, with Anaconda: `conda env create -f environment.yml` and `conda activate it2`.

Regenerate the identity results and figures from the included fingerprints, in a few minutes and with no downloads:

```bash
cd scripts
python 03_identity.py
python 04_sensitivity_bv.py
python 06_eval_roundtrip.py
python 07_figures.py
```

Reproduce everything from the raw IFC files (about 20 to 30 minutes, roughly 130 MB of downloads):

```bash
./run_all.sh
```

Tested with Python 3.12.3, IfcOpenShell 0.8.5, NumPy 2.4.4, SciPy 1.17.1 and Matplotlib 3.10.8. All random seeds are fixed, so the numbers come out identical.

## Data

| Model | Source repository | Exporter (from file header) | Used for |
| --- | --- | --- | --- |
| Simple-Scene Building-Hvac (IFC4.3) | buildingSMART/Sample-Test-Files | SketchUp IFC manager | topology |
| Simple-Scene Infra-Plumbing (IFC4.3) | buildingSMART/Sample-Test-Files | SketchUp IFC manager | topology |
| Duplex_MEP_20110907 | buildingsmart-community/Community-Sample-Test-Files | Autodesk Revit MEP 2011 | topology, identity |
| Duplex_Electrical_20121207 | buildingsmart-community/Community-Sample-Test-Files | Autodesk Revit 2013 | topology |
| Duplex_Plumbing_20121113 | buildingsmart-community/Community-Sample-Test-Files | Autodesk Revit 2013 | topology, identity, round trip |
| Clinic_HVAC | buildingsmart-community/Community-Sample-Test-Files | Autodesk Revit MEP 2013 | topology, identity |
| Clinic_Plumbing | buildingsmart-community/Community-Sample-Test-Files | Autodesk Revit 2013 | topology |

The IFC files are not redistributed here. `data/download.py` fetches them from the original repositories; please check the licence terms there before reusing the models. The community files are stored with Git LFS, so the script downloads them through `media.githubusercontent.com`.

## Main results

Topology (Section 5.2): system membership and connectivity are unrelated. The samples have systems but no ports, the 2012 Revit exports have near-complete port networks and no IfcSystem, and two exports have neither.

| Model | Distribution elements | PC | Components | LC | SM |
| --- | --- | --- | --- | --- | --- |
| Simple-Scene HVAC | 3 | 0.00 | 3 | 0.33 | 1.00 |
| Simple-Scene Plumbing | 26 | 0.00 | 26 | 0.04 | 1.00 |
| Duplex MEP (2011) | 926 | 0.00 | 926 | 0.00 | 0.00 |
| Duplex Electrical | 99 | 0.00 | 99 | 0.01 | 0.00 |
| Duplex Plumbing | 498 | 0.98 | 20 | 0.47 | 0.00 |
| Clinic HVAC | 3,704 | 1.00 | 13 | 0.94 | 0.00 |
| Clinic Plumbing | 6,587 | 0.97 | 176 | 0.95 | 0.00 |

Identity (Section 5.3), recall with 30 percent of elements recreated, 20 seeds:

| Model | Tag key | Placement only | IT2 hybrid |
| --- | --- | --- | --- |
| Clinic HVAC | 0.699 | 0.584 | 0.999 |
| Duplex MEP | 0.699 | 0.982 | 0.999 |
| Duplex Plumbing | 0.700 | 0.576 | 0.999 |

Placement-only matching fails on the 2012 exports because nearly every flow segment shares its placement origin with another segment (1,547 of 1,548 in Clinic HVAC). The file-level round trip reproduces the simulated results within 0.03.

## Using the library on your own models

```python
import ifcopenshell
from it2.topology import topology_metrics
from it2.features import extract_features, load_features
from it2.matching import match_hybrid

print(topology_metrics("my_model.ifc"))

old = load_features(extract_features(ifcopenshell.open("model_v1.ifc")))
new = load_features(extract_features(ifcopenshell.open("model_v2.ifc")))
pairs = match_hybrid(old, new, lam=0.3, tau=0.5)       # list of (index in old, index in new)
mapping = {old[i]["g"]: new[j]["g"] for i, j in pairs}  # old GlobalId -> new GlobalId
unmatched = len(new) - len(pairs)                        # candidates for manual review
```

`tau` is the rejection gate in metres. Lower values favour precision, higher values favour recall (see Figure 6). Unmatched elements are meant to go to a person, not to be guessed.

## Scope

Clinic Plumbing (6,587 elements) is used for the topology audit only; its geometry extraction is slow, so the identity experiments use Clinic HVAC, Duplex MEP and Duplex Plumbing. You can add it with `python 02_extract_features.py Clinic_Plumbing` and `python 03_identity.py Clinic_Plumbing`.

This is a controlled study. Revisions are simulated on real models so that ground truth is known; the file-level round trip checks that the simulation is fair, but it does not replace consecutive exports from an authoring tool. Binding validity is simulated because none of the models ships with a BMS point list. See Section 7 of the paper.

## Citation

See `CITATION.cff`. Please also cite the buildingSMART repositories if you use the models.

## Licence

Code: MIT. The IFC models belong to their respective owners and are not part of this repository.
