
def user_thresholds(cfg, use_threshold=False):
    if not use_threshold:
        return {n:None for n in cfg.get_nodes()}
    from ppl import Constraint_System
    node_data = {n:v for n,v in cfg.nodes.data("threshold", default=[])}
    threshold = {}
    gvars = cfg.get_info("global_vars")
    for node, data in node_data:
        threshold[node] = Constraint_System([c.transform(gvars, lib="ppl") 
                                             for c in data["threshold"]
                                             if c.is_linear()])
    cfg.set_nodes_info(threshold, "cs_threshold")
    return threshold

def compute_thresholds(cfg, use_threshold=False):
    raise NotImplementedError("Compute Automatic Thresholds is not implemented yet.")