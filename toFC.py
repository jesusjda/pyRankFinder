import argparse
from partialevaluation import partialevaluate


def setArgumentParser():
    desc = "Generator"
    pe_options = ["none", "simple", "complete", "full"]
    argParser = argparse.ArgumentParser(description=desc)
    # Program Parameters
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 5),
                           help="increase output verbosity", default=0)
    # Algorithm Parameters
    argParser.add_argument("-mo", "--memoryout", type=int, default=None,
                           help="")
    argParser.add_argument("-to", "--timeout", type=int, default=None,
                           help="")
    argParser.add_argument("-pe", "--partial_evaluate", required=False, nargs='*',
                           default=[pe_options[0]], choices=pe_options, help="Partial Evaluate")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-g", "--goals", nargs='+', required=False, choices=["COMPLEXITY", "TERMINATION"],
                           help="Goals.", default=["COMPLEXITY"])
    argParser.add_argument("-c", "--cache", required=True,
                           help="Folder cache.")
    return argParser


def toKoat(ar, cachedir):
    files = ar["files"]
    verb = ar["verbosity"]
    pe_modes = ar["partial_evaluate"]
    for f in files:
        print("Launching: "+f)
        for g in goals:
            print("  > "+str(g))
            for pe in pe_modes:
                try:
                    print("  >  > pe = "+str(pe))
                    name = os.path.basename(f)
                    o = name + "."+g[0:6]+"_"+pe+".fc"
                    o = os.path.join(cachedir, o)
                    if os.path.isfile(o):
                        os.remove(o)
                    from genericparser import GenericParser
                    precfg = GenericParser().parse(f)

                    partialevaluate(precfg, level=pe, fcpath=o)
                except Exception as e:
                    print(e)
                    raise Exception() from e


if __name__ == '__main__':
    import os
    import sys
    argParser = setArgumentParser()
    args = argParser.parse_args(sys.argv[1:])
    ar = vars(args)
    cachedir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), ar["cache"])
    toKoat(ar, cachedir)
