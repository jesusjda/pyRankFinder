import os
import sys
import getopt
import argparse

_version = "0.0.0.1"
_name = "pyRankFinder"


def setArgumentParser():
    algorithms = ["prlrf", "bgllrf", "adfglrf", "nlrf", "bmsnlrf"]
    scc_strategies = ["global", "local", "incremental"]
    desc = _name+": a Ranking Function finder on python."
    argParser = argparse.ArgumentParser(description=desc)
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 4),
                           help="increase output verbosity", default=0)
    argParser.add_argument("--dotProgram", required=False,
                           help="Outfile to show the program as dot graph.")
    argParser.add_argument("-dt", "--different_template", action='store_true',
                           help="Use different templates on each node")
    argParser.add_argument("-sccs", "--scc_strategy", required=False,
                           default=scc_strategies[0], choices=scc_strategies,
                           help="Strategy based on SCC to go through the CFG.")
    argParser.add_argument("-ver", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("-f", "--file", required=True,
                           help="File to be analysed.")
    argParser.add_argument("-a", "--algorithm", choices=algorithms,
                           required=True, help="Algorithm to be apply.")
    return argParser


def Main(argv):
    argParser = setArgumentParser()
    args = argParser.parse_args(argv)
    config = vars(args)
    if args.version:
        print _name+" version: "+_version
        exit(0)
    prs = pyParser.GenericParser()
    try:
        if args.dotProgram:
            cfg = prs.parse(args.file, dot=args.dotProgram)
            os.system("xdot " + args.dotProgram + " &")
        else:
            cfg = prs.parse(args.file)
    except Exception as e:
        print(e)
        exit(-2)
    Configuration = Config.the()
    Configuration.set_properties(config)
    config["cfg"] = cfg
    internal_config = set_config(config)
    Configuration.echo(3, config)
    Configuration.echo(3, internal_config)
    result = Termination.run(internal_config)
    print(result)
    exit(0)


def set_config(data):
    config = {}
    if data["algorithm"] == "adfglrf":
        config = {
            "algorithm": "lex",
            "different_template": data["different_template"],
            "scc_strategy": data["scc_strategy"],
            "cfg": data["cfg"],
            "inner_alg": {
                "algorithm": "adfglrf",
                "different_template": data["different_template"],
                "scc_strategy": data["scc_strategy"]
            }
        }
    elif data["algorithm"] == "bgllrf":
        config = {
            "algorithm": "lex",
            "different_template": data["different_template"],
            "scc_strategy": data["scc_strategy"],
            "cfg": data["cfg"],
            "inner_alg": {
                "algorithm": "bgllrf",
                "different_template": data["different_template"],
                "scc_strategy": data["scc_strategy"]
            }
        }
    else:
        config = {
            "algorithm": data["algorithm"],
            "different_template": data["different_template"],
            "scc_strategy": data["scc_strategy"],
            "cfg": data["cfg"]
        }
    return config


class Config:

    props = {}

    def __init__(self):
        if hasattr(self.__class__, 'instance'):
            raise Exception()
        self.__class__.instance = self
        self.props = {}

    @staticmethod
    def the():
        if hasattr(Config, 'instance'):
            return Config.instance
        return Config()

    def set_properties(self, properties):
        self.props.update(properties)

    def set_property(self, key, value):
        self.props[key] = value

    def get(self, key):
        return self.props[key]

    def echo(self, verbosity, msg):
        if self.get("verbosity") >= verbosity:
            print(msg)


if __name__ == "__main__":
    projectPath = os.path.join(os.path.dirname(__file__), "..")
    sys.path.append(os.path.join(projectPath, "lib/pyParser/pyParser"))
    sys.path.append(os.path.join(projectPath, "lib/pyLPi/pyLPi"))
    globals()["pyParser"] = __import__("GenericParser")
    globals()["Termination"] = __import__("Termination")
    Main(sys.argv[1:])
