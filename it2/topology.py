"""Topology integrity metrics (PC, CC, TF, LC, SM) for IFC distribution systems.

Works for IFC2x3 (ports via IfcRelConnectsPortToElement / HasPorts) and
IFC4 / IFC4.3 (ports via IfcRelNests / IsNestedBy).
"""
import collections
import ifcopenshell


def _ports_of(element):
    ports = []
    for rel in getattr(element, "HasPorts", None) or []:      # IFC2x3
        ports.append(rel.RelatingPort)
    for rel in getattr(element, "IsNestedBy", None) or []:    # IFC4 and later
        ports += [o for o in rel.RelatedObjects if o.is_a("IfcPort")]
    return ports


def topology_metrics(path):
    """Return a dict of topology integrity metrics for one IFC file."""
    f = ifcopenshell.open(path)
    D = f.by_type("IfcDistributionElement")
    if not D:
        raise ValueError(f"{path}: no IfcDistributionElement instances")
    ids = {e.id() for e in D}

    owner, with_ports = {}, 0
    for e in D:
        ps = _ports_of(e)
        with_ports += bool(ps)
        for p in ps:
            owner[p.id()] = e.id()

    ports = f.by_type("IfcPort")
    connected_ports = set()
    adj = collections.defaultdict(set)
    for rel in f.by_type("IfcRelConnectsPorts"):
        a, b = rel.RelatingPort.id(), rel.RelatedPort.id()
        connected_ports |= {a, b}
        oa, ob = owner.get(a), owner.get(b)
        if oa and ob and oa != ob:
            adj[oa].add(ob)
            adj[ob].add(oa)

    seen, sizes = set(), []
    for e in D:
        if e.id() in seen:
            continue
        stack, n = [e.id()], 0
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            n += 1
            stack += list(adj[x])
        sizes.append(n)

    in_system = set()
    for g in f.by_type("IfcSystem"):
        for rel in g.IsGroupedBy or []:
            in_system |= {o.id() for o in rel.RelatedObjects}

    header = f.header.file_name
    return dict(
        file=path.split("/")[-1],
        schema=f.schema,
        exporter=" | ".join(x for x in (getattr(header, "preprocessor_version", "") or "", getattr(header, "originating_system", "") or "") if x),
        D=len(D),
        PC=with_ports / len(D),
        ports=len(ports),
        CC=(len(connected_ports) / len(ports)) if ports else 0.0,
        components=len(sizes),
        isolated=sum(1 for s in sizes if s == 1),
        TF=len(sizes) / len(D),
        LC=max(sizes) / len(D),
        SM=len(in_system & ids) / len(D),
        systems=len(f.by_type("IfcSystem")),
        control_elements=len(f.by_type("IfcDistributionControlElement")),
        contained=sum(1 for e in D if e.ContainedInStructure) / len(D),
    )


def topology_details(path):
    """Per-element view for the app: component id and size, port count, system membership."""
    f = ifcopenshell.open(path)
    D = f.by_type("IfcDistributionElement")
    owner, nports = {}, {}
    for e in D:
        ps = _ports_of(e)
        nports[e.id()] = len(ps)
        for p in ps:
            owner[p.id()] = e.id()
    adj = collections.defaultdict(set)
    for rel in f.by_type("IfcRelConnectsPorts"):
        oa, ob = owner.get(rel.RelatingPort.id()), owner.get(rel.RelatedPort.id())
        if oa and ob and oa != ob:
            adj[oa].add(ob)
            adj[ob].add(oa)
    comp, sizes, cid = {}, {}, 0
    for e in D:
        if e.id() in comp:
            continue
        stack, members = [e.id()], []
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp[x] = cid
            members.append(x)
            stack += list(adj[x])
        sizes[cid] = len(members)
        cid += 1
    in_system = set()
    for g in f.by_type("IfcSystem"):
        for rel in g.IsGroupedBy or []:
            in_system |= {o.id() for o in rel.RelatedObjects}
    rows = []
    for e in D:
        rows.append(dict(GlobalId=e.GlobalId, ifc_class=e.is_a(), name=e.Name or "",
                         ports=nports[e.id()], component=comp[e.id()],
                         component_size=sizes[comp[e.id()]], in_system=e.id() in in_system))
    return rows
