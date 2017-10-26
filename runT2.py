import os
from subprocess import Popen
from subprocess import PIPE
import sys
import getopt
import argparse
from genericparser import Parser_smt2

def positive(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("Minimum value is 0")
    return ivalue


def setArgumentParser():
    algorithms = ["pr", "bg", "adfg", "lex_bg", "lex_adfg",
                  "bms_lrf", "bms_nlrf", "nlrf"]
    desc = ""
    argParser = argparse.ArgumentParser(description=desc)
    # Program Parameters
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 4),
                           help="increase output verbosity", default=0)
    argParser.add_argument("-ver", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("--dotDestination", required=False,
                           help="Folder to save dot graphs.")
    argParser.add_argument("--ei-out", required=False, action='store_true',
                           help="Shows the output supporting ei")
    # Algorithm Parameters
    argParser.add_argument("-dt", "--different_template", action='store_true',
                           help="Use different templates on each node")
    argParser.add_argument("-sccd", "--scc_depth", type=positive, default=0,
                           help="Strategy based on SCC to go through the CFG.")
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-a", "--algorithms", choices=algorithms, nargs='+',
                           required=True, help="Algorithms to be apply.")
    argParser.add_argument("-t2", "--t2home", default="/opt/tools/t2",
                           help="T2_HOME")
    argParser.add_argument("-td", "--tmpdir", default="/tmp/t2stuff",
                           help="Tmp dir")
    
    return argParser


def Main(argv):
    argParser = setArgumentParser()
    args = argParser.parse_args(argv)
    if args.version:
        print("version: 1.0")
        return
    config = vars(args)
    files = args.files

    for f in files:
        aux_p = f.split('/')
        aux_c = len(aux_p) - 1
        while aux_c > 0:
            if aux_p[aux_c] == "examples":
                break
            if aux_p[aux_c] == "User_Projects":
                break
            aux_c -= 1
        r = '/'.join(aux_p[aux_c:])

        # smt2 to T2
        ps = Parser_smt2.Parser_smt2()
        t2program,err = ps.toT2(f)
        if err is not None and err != "":
            raise Exception(err)
        print("###############################")
        print(f)
        print("###############################")
        print(t2program)
        tmpfile = os.path.join(config["tmpdir"], aux_p[-1])
        with open(tmpfile, "w") as tf:
            tf.write(t2program)
        # run T2 
        t2path = os.path.join(config["t2home"], 'src/bin/Release/T2.exe')
        pipe = Popen([t2path, '-input_t2', tmpfile,
                      '-termination', '-print_proof'],
                     stdout=PIPE, stderr=PIPE)
        output, err = pipe.communicate()
        if err is not None and err != "":
            raise Exception(err)
        print("###############################")
        print(output)
    return


if __name__ == "__main__":
    Main(sys.argv[1:])
