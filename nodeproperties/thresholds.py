def threshold_options():
    return ["none", "user", "project_head", "project_head_var",
            "project_call", "project_call_var", "all_in"]


def compute_thresholds(cfg, modes=[]):
    thresholds = {n: [] for n in cfg.get_nodes()}
    if len(modes) == 0 or "none" in modes:
        return thresholds
    do_user = "user" in modes
    do_project_head = "project_head" in modes
    do_project_head_var = "project_head_var" in modes
    do_project_call = "project_call" in modes
    do_project_call_var = "project_call_var" in modes
    do_all_in = "all_in" in modes
    if do_user:
        thr = user_thresholds(cfg)
        for n in thr:
            thresholds[n] += thr[n]
    if do_project_head or do_project_head_var or do_project_call or do_project_call_var:
        thr = project_thresholds(cfg, do_project_head, do_project_head_var, do_project_call, do_project_call_var)
        for n in thr:
            thresholds[n] += thr[n]
    if do_all_in:
        th = [t for n in thresholds for t in thresholds[n]]
        thresholds = {n: th for n in thresholds}
    return thresholds


def user_thresholds(cfg):
    return {n: [c for c in v if c.is_linear()] for n, v in cfg.nodes.data("threshold", default=[])}


def project_thresholds(cfg, do_project_head, do_project_head_var, do_project_call, do_project_call_var):
    from nodeproperties.cfrprops import project_props
    for t in cfg.get_edges():
        t["cfr_polyhedron"] = t["polyhedron"].copy()
    props = project_props(cfg, do_head_props=do_project_head, do_head_var_props=do_project_head_var,
                          do_call_props=do_project_call, do_call_var_props=do_project_call_var)
    return {n: [c for a1 in props[n] for c in a1] for n in props}
