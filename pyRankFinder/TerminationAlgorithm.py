from functools import reduce
from ppl import Variable


class TerminationAlgorithm:

    def description(self):
        raise Exception("Not implemented yet!")

    def ranking(self, data):
        raise Exception("Not implemented yet!")

    def print_result(self, result):
        raise Exception("Not implemented yet!")

    def _print_function(self, name, Vars, coeffs, inh):
        try:
            sr = name + " ( x ) = "
            for i in range(len(coeffs)):
                sr += "" + str(coeffs[i]) + " * " + str(Vars[i]) + " + "
            sr += "" + str(inh)
            print(sr)
        except Exception as e:
            print(e)
