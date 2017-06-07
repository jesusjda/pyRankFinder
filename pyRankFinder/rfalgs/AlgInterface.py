
class AlgInterface:

    _sccs = ""
    _dt = ""

    def __init__(self, sccs="global", dif_tem=False):
        self._sccs = sccs
        self._dt = dif_tem

    def ranking(self, cfg):
        pass

    def print_result(self):
        pass
