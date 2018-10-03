import os
import sys
import argparse
import genericparser
from partialevaluation import partialevaluate
from termination import Output_Manager as OM
from invariants import compute_invariants

_version = "1.0"
_name = "CFRefinement"

def setArgumentParser():
    desc = _name+": Control Flow refinement."
    argParser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.RawTextHelpFormatter)
    # Program Parameters
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 5),
                           help="increase output verbosity", default=0)
    argParser.add_argument("-V", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("-pe", "--pe_modes", type=int, required=False, nargs='+',
                           choices=range(0,5), default=[4],
                           help="List of levels of Partial evaluation in the order that you want to apply them.")
    argParser.add_argument("-pt", "--pe_times", type=int, choices=range(0, 5),
                           help="# times to apply pe", default=1)
    argParser.add_argument("--ei-out", required=False, action='store_true',
                           help="Shows the output supporting ei")
    argParser.add_argument("-i", "--invariants", required=False,
                           default="none", help="invariants")
    argParser.add_argument("-of", "--output_formats", required=False, nargs='+',
                           choices=["fc", "dot", "koat", "pl", "svg"], default=["fc", "dot", "svg"],
                           help="Formats to print the graphs.")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-d", "--dir", required=True, default=None,
                           help="Temporary directory.")
    return argParser

def extractname(filename):
    f = os.path.split(filename)
    b = os.path.split(f[0])
    c = os.path.splitext(f[1])
    return os.path.join(b[1], c[0])

def buildname(directory, name, num):
    if num == 0:
        f = name
    else:
        f = name + "_pe" + str(num)
    f = os.path.join(directory, f)
    return f

def toSvg(dotfile, destination):
    from subprocess import check_call
    check_call(['dot', '-Tsvg', dotfile, '-o', destination])
    check_call(['sed', '-i','-e', ':a', '-re', '/<!.*?>/d;/<\?.*?>/d;/<!/N;//ba', destination])

def file2string(filepath):
    with open(filepath, 'r') as f:
        data=f.read()
    return data

def launch(config):
    for f in config["files"]:
        launch_file(config, f)
        OM.show_output()

def printfile(config, name, destname, cfg, invariant_type):
    if "fc" in config["output_formats"]:
        cfg.toFc(path=destname+".fc")
        #OM.writefile(0, name+".fc", file2string(destname+".fc"))
    if "dot" in config["output_formats"]:
        cfg.toDot(destname+".dot")
        if "svg" in config["output_formats"]:
            toSvg(destname+".dot", destname+".svg")
            OM.printif(0, "Graph {}".format(name))
            #OM.printif(0, file2string(destname+".svg"), format="svg")
    if "koat" in config["output_formats"]:
        cfg.toKoat(path=destname+".koat",goal_complexity=True, invariant_type=invariant_type)
        #OM.writefile(0, name+".koat", file2string(destname+".koat"))

def launch_file(config, f):
    try:
        name = extractname(f)
        OM.restart(cdest="file:"+str(name))
        destname = buildname(config["dir"], name, 0)
        print(destname)
        os.makedirs(os.path.dirname(destname), exist_ok=True)
        cfg = []
        cfg.append(genericparser.parse(f))
        cfg[0].build_polyhedrons()
        invariant_type=config["invariants"]
        compute_invariants(cfg[0], invariant_type=invariant_type)
        cfg[0].simplify_constraints()
        printfile(config, name, destname, cfg[0], invariant_type)
        for i in range(1,config["pe_times"]+1):
            destname = buildname(config["dir"], name, i)
            cfg[i-1].build_polyhedrons()
            cfg.append(partialevaluate(cfg[i-1], invariant_type=invariant_type))
            compute_invariants(cfg[i], invariant_type=invariant_type)
            cfg[i].simplify_constraints()
            printfile(config, name+"_pe"+str(i), destname, cfg[i], invariant_type)
    except Exception as e:
        OM.printf("Exception  -> "+str(e))
        raise Exception() from e

if __name__ == "__main__":
    try:
        argv = sys.argv[1:]
        argParser = setArgumentParser()
        args = argParser.parse_args(argv)
        OM.restart(verbosity=args.verbosity, ei=args.ei_out)
        if args.version:
            print(_name + " version: " + _version)
            exit(0)
        config = vars(args)
        launch(config)
    except Exception as e:
        OM.show_output()
        raise Exception() from e

