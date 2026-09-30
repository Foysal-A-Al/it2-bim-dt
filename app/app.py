"""IT2 checker: a desktop app for identity and topology integrity of IFC models.

Run from the repository root:   streamlit run app/app.py
"""
import json, pathlib, sys, tempfile, time
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import ifcopenshell
from it2.topology import topology_metrics, topology_details
from it2.features import extract_features, load_features
from it2.matching import reconcile, perturb, score, DEFAULT_LAMBDA, DEFAULT_TAU

BLUE, GOLD, DARK, RED, GREEN = "#2E75B6", "#BF9000", "#1F2A36", "#B22222", "#3B7A2A"
st.set_page_config(page_title="IT2 checker", page_icon="🔗", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=Source+Serif+4:wght@600&display=swap');
html, body, [class*="css"], .stMarkdown, .stText, p, li, label { font-family: 'IBM Plex Sans', Arial, sans-serif; }
h1, h2, h3 { font-family: 'Source Serif 4', Georgia, serif !important; color: #1F2A36; }
.verdict { border-radius: 10px; padding: 18px 22px; margin: 6px 0 14px 0; font-size: 1.05rem; }
.pass { background: #E7F2E3; border-left: 6px solid #3B7A2A; }
.fail { background: #F8E6E4; border-left: 6px solid #B22222; }
.note { color: #55606B; font-size: 0.92rem; }
</style>""", unsafe_allow_html=True)

IFC_DIR = ROOT / "data" / "ifc"


def save_upload(upload):
    """Streamlit uploads live in memory; IfcOpenShell needs a path."""
    tmp = pathlib.Path(tempfile.gettempdir()) / f"it2_{upload.file_id}_{upload.name}"
    if not tmp.exists():
        tmp.write_bytes(upload.getbuffer())
    return str(tmp)


def pick_model(label, key):
    """Either upload an IFC file or choose one of the study models if they were downloaded."""
    # Users can inspect their own IFC or a downloaded study model with the same audit code.
    local = sorted(p.name for p in IFC_DIR.glob("*.ifc")) if IFC_DIR.exists() else []
    choice = st.radio(label, ["Upload a file"] + (["Use a study model"] if local else []), horizontal=True, key=key + "_mode")
    if choice == "Use a study model":
        name = st.selectbox("Study model", local, key=key + "_sel")
        return str(IFC_DIR / name), name
    up = st.file_uploader("IFC file (.ifc)", type=["ifc"], key=key + "_up")
    return (save_upload(up), up.name) if up else (None, None)


@st.cache_data(show_spinner=False)
# Cache results by path. Clear the Streamlit cache if a file is replaced at the same path.
def cached_topology(path, _mtime):
    return topology_metrics(path), topology_details(path)


@st.cache_data(show_spinner=False)
def cached_features(path, _mtime):
    return extract_features(ifcopenshell.open(path))


def verdict(ok, text):
    st.markdown(f'<div class="verdict {"pass" if ok else "fail"}"><b>{"Passes" if ok else "Does not pass"} the gate.</b> {text}</div>',
                unsafe_allow_html=True)


st.title("IT2 checker")
st.markdown('<p class="note">Checks whether a BIM model is ready to carry a digital twin: are its distribution systems really connected, '
            'and do elements keep their identity from one version to the next?</p>', unsafe_allow_html=True)

tab_topo, tab_id, tab_study = st.tabs(["Topology check", "Identity check", "Study results"])

# ---------------------------------------------------------------- topology
with tab_topo:
    st.subheader("Is the network connected?")
    path, name = pick_model("Model", "topo")
    c1, c2 = st.columns(2)
    pc_min = c1.slider("Minimum port coverage (PC)", 0.0, 1.0, 0.95, 0.01)
    lc_min = c2.slider("Minimum share in largest component (LC)", 0.0, 1.0, 0.90, 0.01)
    if path:
        t0 = time.time()
        with st.spinner(f"Reading {name} ..."):
            try:
                m, rows = cached_topology(path, pathlib.Path(path).stat().st_mtime)
            except Exception as ex:
                st.error(f"Could not read this file as IFC: {ex}")
                st.stop()
        df = pd.DataFrame(rows)
        # These are user-selected operational thresholds, not universal engineering criteria.
        ok = m["PC"] >= pc_min and m["LC"] >= lc_min
        verdict(ok, f"PC = {m['PC']:.2f} (needs {pc_min:.2f}), LC = {m['LC']:.2f} (needs {lc_min:.2f}).")
        k = st.columns(6)
        k[0].metric("Distribution elements", f"{m['D']:,}")
        k[1].metric("Port coverage PC", f"{m['PC']:.2f}")
        k[2].metric("Connection coverage CC", f"{m['CC']:.2f}")
        k[3].metric("Components", f"{m['components']:,}")
        k[4].metric("Largest component LC", f"{m['LC']:.2f}")
        k[5].metric("System membership SM", f"{m['SM']:.2f}")
        if m["SM"] >= 0.5 and m["PC"] < 0.5:
            st.warning("Every element sits in a system, but the elements are not connected. A check that only counts "
                       "system membership would pass this model; network-level fault diagnosis would not work on it.")
        if m["PC"] >= 0.5 and m["SM"] < 0.5:
            st.info("The network is modelled, but no IfcSystem groups it. Systems can be rebuilt from the connected components.")
        st.caption(f"Schema {m['schema']} · exporter: {m['exporter'] or 'not stated'} · read in {time.time()-t0:.1f} s")

        left, right = st.columns([1, 1])
        with left:
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.axvline(0.5, color="0.6", lw=0.6); ax.axhline(0.5, color="0.6", lw=0.6)
            ref = ROOT / "results" / "topology.json"
            if ref.exists():
                for t in json.load(open(ref)):
                    ax.scatter(t["SM"], t["PC"], s=30, marker="D", fc="white", ec="0.55", lw=0.8)
            ax.scatter(m["SM"], m["PC"], s=140, marker="D", fc=BLUE, ec=DARK, zorder=3, label=name)
            for x, y, t in [(0.03, 1.02, "Topology without systems"), (0.53, 1.02, "Target: both"),
                            (0.03, 0.47, "Neither"), (0.53, 0.47, "Systems without topology")]:
                ax.text(x, y, t, fontsize=8, va="top", fontweight="bold", color=DARK)
            ax.set_xlim(-0.05, 1.05); ax.set_ylim(-0.05, 1.05)
            ax.set_xlabel("System membership, SM"); ax.set_ylabel("Port coverage, PC")
            ax.legend(loc="center right", fontsize=8, frameon=False)
            st.pyplot(fig, clear_figure=True)
            st.caption("Grey diamonds: the seven models of the study, for comparison.")
        with right:
            comp = df.groupby("component").size().sort_values(ascending=False)
            st.markdown("**Network pieces, largest first**")
            st.bar_chart(comp.head(30).reset_index(drop=True), height=260, color=BLUE)
            isolated = df[df.component_size == 1]
            st.markdown(f"**{len(isolated):,} elements are not connected to anything**")
            st.dataframe(isolated[["GlobalId", "ifc_class", "name", "ports"]].head(500), height=220, width="stretch")
        st.download_button("Download element report (CSV)", df.to_csv(index=False).encode(), file_name=f"{name}_topology.csv")
    else:
        st.info("Upload an IFC model to see whether its distribution network is connected.")

# ---------------------------------------------------------------- identity
with tab_id:
    st.subheader("Do elements keep their identity between versions?")
    mode = st.radio("What do you want to compare?", ["Two versions of a model", "One model against a simulated revision"], horizontal=True, key="id_mode")
    c1, c2 = st.columns(2)
    lam = c1.slider("Name weight λ", 0.0, 1.0, DEFAULT_LAMBDA, 0.05, help="How much a different type name counts against a match.")
    tau = c2.slider("Rejection gate τ (m)", 0.1, 2.0, DEFAULT_TAU, 0.05, help="Pairs costing more than this go to manual review instead of being matched.")
    old = new = truth = None
    if mode == "Two versions of a model":
        a, b = st.columns(2)
        with a:
            p_old, n_old = pick_model("Earlier version", "old")
        with b:
            p_new, n_new = pick_model("Later version", "new")
        if p_old and p_new:
            with st.spinner("Reading geometry of both versions (large models take a few minutes) ..."):
                old = load_features([dict(x) for x in cached_features(p_old, pathlib.Path(p_old).stat().st_mtime)])
                new = load_features([dict(x) for x in cached_features(p_new, pathlib.Path(p_new).stat().st_mtime)])
    else:
        p_old, n_old = pick_model("Model", "sim")
        s = st.columns(4)
        r = s[0].slider("Share redrawn (new ID and Tag)", 0.0, 1.0, 0.3, 0.05)
        mv = s[1].slider("Share moved", 0.0, 1.0, 0.1, 0.05)
        sg = s[2].slider("Move size σ (m)", 0.0, 1.0, 0.15, 0.05)
        seed = s[3].number_input("Seed", 0, 10_000, 0)
        if p_old:
            with st.spinner("Reading geometry (large models take a few minutes) ..."):
                old = load_features([dict(x) for x in cached_features(p_old, pathlib.Path(p_old).stat().st_mtime)])
            new, truth = perturb(old, np.random.default_rng(int(seed)), r, move=mv, sigma=sg)
            for x in new:                      # a revision regenerates GlobalIds
                x["g"] = "new-" + str(id(x))
    if old is not None and new is not None:
        # Record how each correspondence was recovered so users can inspect the mapping.
        pairs, stage = reconcile(old, new, lam, tau)
        n_g = sum(v == "globalid" for v in stage.values()); n_t = sum(v == "tag" for v in stage.values())
        n_geo = sum(v == "geometry" for v in stage.values())
        un_old = len(old) - len(pairs); un_new = len(new) - len(pairs)
        ic = n_g / len(pairs) if pairs else 0.0
        k = st.columns(5)
        k[0].metric("Same GlobalId", f"{n_g:,}")
        k[1].metric("Recovered by Tag", f"{n_t:,}")
        k[2].metric("Recovered by geometry", f"{n_geo:,}")
        k[3].metric("Old elements unmatched", f"{un_old:,}")
        k[4].metric("New elements unmatched", f"{un_new:,}")
        verdict(ic >= 0.98, f"Identity continuity IC ≈ {ic:.3f}: the share of matched elements that kept their GlobalId. "
                            f"{n_t + n_geo:,} elements changed ID and were re-linked; {un_old + un_new:,} go to manual review.")
        if truth is not None:
            P, R, F = score(pairs, truth)
            st.success(f"Against the known truth of the simulation: precision {P:.3f}, recall {R:.3f}, F1 {F:.3f}.")
        rows = [dict(stage=stage[(i, j)], ifc_class=old[i]["cls"], old_GlobalId=old[i]["g"], new_GlobalId=new[j]["g"],
                     old_tag=old[i]["tag"], new_tag=new[j]["tag"], type=old[i]["typ"],
                     moved_m=round(float(np.linalg.norm(old[i]["cen"] - new[j]["cen"])), 3)) for i, j in pairs]
        mp = pd.DataFrame(rows)
        st.markdown("**Element mapping**")
        show = st.multiselect("Show stages", ["globalid", "tag", "geometry"], default=["tag", "geometry"])
        st.dataframe(mp[mp.stage.isin(show)].head(2000), height=320, width="stretch")
        ui = {i for i, _ in pairs}; uj = {j for _, j in pairs}
        review = pd.DataFrame([dict(version="earlier", GlobalId=o["g"], ifc_class=o["cls"], type=o["typ"]) for i, o in enumerate(old) if i not in ui] +
                              [dict(version="later", GlobalId=x["g"], ifc_class=x["cls"], type=x["typ"]) for j, x in enumerate(new) if j not in uj])
        st.markdown(f"**Manual review queue ({len(review):,})**: deleted, added, or moved further than τ")
        st.dataframe(review.head(2000), height=220, width="stretch")
        d1, d2 = st.columns(2)
        d1.download_button("Download mapping (CSV)", mp.to_csv(index=False).encode(), file_name="it2_mapping.csv")
        d2.download_button("Download review queue (CSV)", review.to_csv(index=False).encode(), file_name="it2_review.csv")
    else:
        st.info("Choose two versions of the same model, or one model to test against a simulated revision.")

# ---------------------------------------------------------------- study
with tab_study:
    st.subheader("Results of the controlled study")
    # This tab presents the saved paper snapshot; selecting a model does not rerun the study.
    res = ROOT / "results"; figs = ROOT / "figures"
    if (res / "topology.json").exists():
        t = pd.DataFrame(json.load(open(res / "topology.json")))[["file", "exporter", "D", "PC", "components", "LC", "SM"]]
        st.markdown("**Topology audit of the seven models**")
        st.dataframe(t.round(2), width="stretch", hide_index=True)
    rows = []
    for p in sorted(res.glob("identity_*.json")):
        d = json.load(open(p)); m = p.stem.replace("identity_", "")
        for r in ["0.3", "0.5"]:
            rows.append(dict(model=m, recreated=r, tag_R=d[r]["tag"]["R"][0], placement_R=d[r]["placement"]["R"][0],
                             hybrid_P=d[r]["hybrid"]["P"][0], hybrid_R=d[r]["hybrid"]["R"][0]))
    if rows:
        st.markdown("**Identity recovery, 20 seeds per setting**")
        st.dataframe(pd.DataFrame(rows).round(3), width="stretch", hide_index=True)
    names = {"f4_quadrant.png": "System membership against port coverage", "f5_recall.png": "Recall against share of recreated elements",
             "f6_sensitivity.png": "Sensitivity to λ and τ", "f3_protocol.png": "The IT2 protocol"}
    cols = st.columns(2)
    for n, (f, cap) in enumerate(names.items()):
        if (figs / f).exists():
            cols[n % 2].image(str(figs / f), caption=cap, width="stretch")
