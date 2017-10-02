from . import algorithm

__all__ = ['algorithm', 'result', 'run']


def run(data):
    print("Running: "+data["algorithm"])
    config = data.copy()
    alg = config["algorithm"]
    if alg == "lex":
        return algorithm.LexicographicRF(config)
    elif alg == "bms":
        return algorithm.BMSRF(config)
    elif alg == "pr":
        return algorithm.LinearRF(config)
    elif alg == "adfg":
        return algorithm.compute_adfg_QLRF(config)
    elif alg == "bg":
        return algorithm.compute_bg_QLRF(config)
    elif alg == "lrf":
        return algorithm.compute_bms_LRF(config)
    elif alg == "nlrf":
        return algorithm.compute_bms_NLRF(config)
    else:
        raise Exception("ERROR: Algorithm (" + alg + ") not found.")

