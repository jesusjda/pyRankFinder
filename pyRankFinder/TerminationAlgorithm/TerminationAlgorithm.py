from ppl import Variable


class TerminationAlgorithm:

    def description(self):
        raise Exception("Not implemented yet!")

    def ranking(self, data):
        raise Exception("Not implemented yet!")

    def print_result(self, result):
        raise Exception("Not implemented yet!")

    def _f(self, shift, size, coeffs):
        f = coeffs[0]
        for i in range(1, size):
            f += Variable(i)*coeffs[i]
        return f
