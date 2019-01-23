def user_thresholds(cfg, use_threshold=False):
    if not use_threshold:
        return {n: None for n in cfg.get_nodes()}
    node_data = {n: v for n, v in cfg.nodes.data("threshold", default=[])}
    threshold = {}
    for node in node_data:
        threshold[node] = [c for c in node_data[node] if c.is_linear()]
    cfg.set_nodes_info(threshold, "cs_threshold")
    return threshold


def compute_thresholds(cfg, use_threshold=False):
    raise NotImplementedError("Compute Automatic Thresholds is not implemented yet.")
