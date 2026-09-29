"""Fingerprint extraction: class, container, Tag, type name, placement origin, world bounding box."""
import multiprocessing
import numpy as np
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as ue
import ifcopenshell.util.placement as up
import ifcopenshell.util.unit as uu


def extract_features(f):
    """f: an opened ifcopenshell file. Returns a list of dicts, all lengths in metres."""
    scale = uu.calculate_unit_scale(f)          # file length unit -> metres (placements)
    D = f.by_type("IfcDistributionElement")
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)             # geometry is returned in metres
    geo = {}
    it = ifcopenshell.geom.iterator(s, f, multiprocessing.cpu_count(), include=D)
    if it.initialize():
        while True:
            sh = it.get()
            v = np.array(sh.geometry.verts).reshape(-1, 3)
            if len(v):
                geo[sh.id] = (v.min(0), v.max(0))
            if not it.next():
                break
    out = []
    for e in D:
        if e.id() not in geo:
            continue
        lo, hi = geo[e.id()]
        c = ue.get_container(e)
        name = e.Name or ""
        pl = up.get_local_placement(e.ObjectPlacement)[:3, 3] * scale if e.ObjectPlacement else (lo + hi) / 2
        out.append(dict(
            g=e.GlobalId, cls=e.is_a(), cont=c.GlobalId if c else "", tag=e.Tag or "",
            typ=name.rsplit(":", 1)[0] if ":" in name else name,
            cen=((lo + hi) / 2).tolist(), dim=sorted((hi - lo).tolist()), pl=[float(x) for x in pl],
        ))
    return out


def load_features(records):
    """Convert list-valued fields to numpy arrays (in place) and return the list."""
    for x in records:
        x["cen"] = np.asarray(x["cen"], float)
        x["dim"] = np.asarray(x["dim"], float)
        x["pl"] = np.asarray(x["pl"], float)
    return records
