
class AbstractDomain:

    def lub(s1, s2):
        return s1.lub(s2)

    def widening(s1, s2):
        return s1.widening(s2)

    def apply(s, t):
        return s.apply(t)

    def lte(s1, s2):
        return s1.lte(s2)
