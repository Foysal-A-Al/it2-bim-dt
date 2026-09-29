import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
IFC = ROOT / "data" / "ifc"
FEAT = ROOT / "data" / "features"
RES = ROOT / "results"
FIG = ROOT / "figures"
for p in (FEAT, RES, FIG):
    p.mkdir(parents=True, exist_ok=True)
# models used in the identity experiments (real exports with rich geometry)
IDENTITY_MODELS = ["Clinic_HVAC", "Duplex_MEP_20110907", "Duplex_Plumbing_20121113"]
def dump(obj, path):
    json.dump(obj, open(path, "w"), indent=1, default=float)
