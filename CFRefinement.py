import os
import sys
import argparse
from genericparser import GenericParser
from partialevaluation import partialevaluate
from termination import Output_Manager as OM

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

def buildname(dir, name, num):
    if num == 0:
        f = name
    else:
        f = name + "pe" + str(num)
    f = os.path.join(dir, f)
    return (f+".fc",f+".dot",f+".svg")

def toSvg(dotfile, destination):
    from subprocess import check_call
    check_call(['dot', '-Tsvg', dotfile, '-o', destination])
    check_call(['sed', '-i','-e', ':a', '-re', 's/<!.*?>//g;/<\?.*?>/d;/<!/N;//ba', destination])

def file2string(filepath):
    with open(filepath, 'r') as f:
        data=f.read()
    return data

def launch(config):
    for f in config["files"]:
        launch_file(config, f)
        OM.show_output()

def launch_file(config, f):
    try:
        name = extractname(f)
        OM.restart(cdest="file:"+str(name))
        fcfile, dotfile, svgfile = buildname(config["dir"], name, 0) 
        os.makedirs(os.path.dirname(fcfile), exist_ok=True)
        cfg = []
        cfg.append(GenericParser().parse(f))
        cfg[0].toFc(path=fcfile)
        cfg[0].toDot(dotfile)
        toSvg(dotfile, svgfile)
        OM.printif(0, file2string(svgfile), format="svg")
        OM.writefile(0, name+".fc", file2string(fcfile))
        for i in range(1,config["pe_times"]+1):
            fcfile, dotfile, svgfile = buildname(config["dir"], name, i) 
            cfg.append(partialevaluate(cfg[i-1]))
            cfg[i].toFc(path=fcfile)
            cfg[i].toDot(dotfile)
            toSvg(dotfile, svgfile)
            OM.printif(0, file2string(svgfile), format="svg")
            OM.writefile(0, name+"_pe"+str(i)+".fc", file2string(fcfile))
    except Exception as e:
        OM.printf("Exception  -> "+str(e))

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
    finally:
        OM.show_output()
        
