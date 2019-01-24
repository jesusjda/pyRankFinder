def threshold_options():
    return ["none", "user", "project_head", "all_in"]


def compute_thresholds(cfg, modes=[]):
    thresholds = {n: [] for n in cfg.get_nodes()}
    if len(modes) == 0 or "none" in modes:
        return thresholds
    if "user" in modes:
        thr = user_thresholds(cfg)
        for n in thr:
            thresholds[n] += thr[n]
    if "project_head" in modes:
        thr = project_head_thresholds(cfg)
        for n in thr:
            thresholds[n] += thr[n]
    if "all_in" in modes:
        th = [t for n in thresholds for t in thresholds[n]]
        thresholds = {n: th for n in thresholds}
    print(thresholds)
    return thresholds


def user_thresholds(cfg):
    return {n: [c for c in v if c.is_linear()] for n, v in cfg.nodes.data("threshold", default=[])}


def project_head_thresholds(cfg):
    from nodeproperties.cfrprops import project_props
    for t in cfg.get_edges():
        t["cfr_polyhedron"] = t["polyhedron"].copy()
    props = project_props(cfg, do_head_props=True)
    return {n: [c for a1 in props[n] for c in a1] for n in props}
