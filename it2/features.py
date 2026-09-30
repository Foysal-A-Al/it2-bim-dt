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
    # Placements use the IFC length unit; convert them before comparing with metre geometry.
    scale = uu.calculate_unit_scale(f)          # file length unit -> metres (placements)
    D = f.by_type("IfcDistributionElement")
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)             # geometry is returned in metres
    geo = {}
    # Extract all available distribution-element geometry in parallel.
    it = ifcopenshell.geom.iterator(s, f, multiprocessing.cpu_count(), include=D)
    if it.initialize():
        while True:
            sh = it.get()
            v = np.array(sh.geometry.verts).reshape(-1, 3)
            # World-coordinate extrema define an axis-aligned box for the matching fingerprint.
            if len(v):
                geo[sh.id] = (v.min(0), v.max(0))
            if not it.next():
                break
    out = []
    for e in D:
        # Skip elements without returned geometry; they cannot enter geometry-based matching.
        if e.id() not in geo:
            continue
        lo, hi = geo[e.id()]
        c = ue.get_container(e)
        name = e.Name or ""
        # Resolve nested placements, then convert units. A missing placement uses the box centre.
        pl = up.get_local_placement(e.ObjectPlacement)[:3, 3] * scale if e.ObjectPlacement else (lo + hi) / 2
        # Store identifier/key fields alongside the centre, sorted dimensions and placement.
        # Revit instance suffixes are removed from the Name to obtain the type-name cue.
        out.append(dict(
            g=e.GlobalId, cls=e.is_a(), cont=c.GlobalId if c else "", tag=e.Tag or "",
            typ=name.rsplit(":", 1)[0] if ":" in name else name,
            cen=((lo + hi) / 2).tolist(), dim=sorted((hi - lo).tolist()), pl=[float(x) for x in pl],
        ))
    return out


def load_features(records):
    """Convert list-valued fields to numpy arrays (in place) and return the list."""
    # JSON stores vectors as lists; numerical matchers need NumPy arrays for arithmetic.
    for x in records:
        x["cen"] = np.asarray(x["cen"], float)
        x["dim"] = np.asarray(x["dim"], float)
        x["pl"] = np.asarray(x["pl"], float)
    return records
