

class AbstractDomain:

    def lub(self, s1, s2):
        return s1.lub(s2)

    def widening(self, s1, s2):
        return s1.widening(s2)

    def apply_tr(self, s, t):
        return s.apply_tr(t)

    def lte(self, s1, s2):
        return s1 <= s2
