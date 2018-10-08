import argparse
from multiprocessing import Manager
from multiprocessing import Process
import os
import sys
import termination.algorithm
import rankfinder
from termination.result import TerminationResult
from pprint import pprint
import datetime

def setArgumentParser():
    desc = "Generator"
    argParser = argparse.ArgumentParser(description=desc)
    # SANDBOX Parameters
    argParser.add_argument("-mo", "--memoryout", type=int, default=None,
                           help="")
    argParser.add_argument("-to", "--timeout", type=int, default=None,
                           help="")
    # Program Parameters
    argParser.add_argument("-v", "--verbosity", type=int, choices=range(0, 5),
                           help="increase output verbosity", default=0)
    argParser.add_argument("--dotDestination", required=False,
                           help="Folder to save dot graphs.")
    # Algorithm Parameters
    argParser.add_argument("-sccd", "--scc_depth", type=int,
                           choices=range(0, 10), default=5,
                           help="Strategy based on SCC to go through the CFG.")# CFR Parameters
    argParser.add_argument("-cfr-it-max", "--cfr-iterations-max", type=int, choices=range(0, 5),
                           help="# times to apply cfr", default=0)
    argParser.add_argument("-cfr-it-min", "--cfr-iterations-min", type=int, choices=range(0, 5),
                           help="# times to apply cfr", default=2)
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-c", "--cache", required=True,
                           help="Folder cache.")
    argParser.add_argument("-p", "--prefix", required=True, default="",
                           help="Prefix of the files path")
    return argParser


def sandbox(task, args=(), kwargs={}, time_segs=60, memory_mb=None):
    manager = Manager()
    r_dict = manager.dict()

    def worker(task, r_dict, *args, **kwargs):
        try:
            r_dict["output"] = task(*args, **kwargs)
            r_dict["status"] = "ok"
        except MemoryError as e:
            r_dict["status"] = TerminationResult.MEMORYLIMIT
            r_dict["output"] = "ML"
        except Exception as e:
            r_dict["status"] = TerminationResult.ERROR
            r_dict["output"] = "Error " + type(e).__name__
            raise Exception() from e

    def returnHandler(exitcode, r_dict, usage=None, usage_old=[0, 0, 0]):
        ret ={}
        try:
            if exitcode == -24:
                ret["status"] = TerminationResult.TIMELIMIT
                ret["output"] = "TL"
            elif exitcode < 0:
                ret["status"] = TerminationResult.ERROR
                ret["output"] = "ERR"
            elif not("status" in r_dict):
                ret["status"] = TerminationResult.TIMELIMIT
            elif r_dict["status"] == "ok":
                ret["status"] = r_dict["output"].get_status()
                ret["output"] = r_dict["output"]
            else:
                ret["status"] = r_dict["status"]
                ret["output"] = r_dict["output"]
        except Exception as e:
            ret["status"] = TerminationResult.ERROR
            ret["output"] = "ERROR while processing output " + type(e).__name__
        finally:
            if usage:
                ret["cputime"] = usage[0] + usage[1] - usage_old[0] - usage_old[1]
                ret["memory"] = usage[2] - usage_old[2]
            return ret

    import resource
    if memory_mb:
        bML = 1024 * 1024 * memory_mb
    else:
        bML = resource.RLIM_INFINITY
    if time_segs:
        sTL = time_segs
    else:
        sTL = resource.RLIM_INFINITY
    softM, hardM = resource.getrlimit(resource.RLIMIT_DATA)
    softT, hardT = resource.getrlimit(resource.RLIMIT_CPU)
    usage_old = resource.getrusage(resource.RUSAGE_CHILDREN)
    arguments=(task,r_dict)+args
    p = Process(target=worker, args=arguments, kwargs=kwargs)
    try:
        from resource import prlimit
        p.start()
        prlimit(p.pid, resource.RLIMIT_CPU, (sTL, hardT))
        prlimit(p.pid, resource.RLIMIT_DATA, (bML, hardM))
    except ImportError:
        resource.setrlimit(resource.RLIMIT_CPU, (sTL, hardT))
        resource.setrlimit(resource.RLIMIT_DATA, (bML, hardM))
        p.start()
    finally:
        p.join()
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        resource.setrlimit(resource.RLIMIT_CPU, (softT, hardT))
        resource.setrlimit(resource.RLIMIT_DATA, (softM, hardM))
        return returnHandler(p.exitcode, r_dict, usage, usage_old)

def config2Tag(config):
    tag = ""
    tag += str(config["termination"][0])
    tag += "_sccd:"+str(config["scc_depth"])
    tag += "_invariant:"+str(config["invariants"])
    tag += "_dt:"+str(config["different_template"])
    tag += "_sc:"+str(config["simplify_constraints"])
    tag += "_CFR-it:"+str(config["cfr_iterations"])
    tag += "_CFR-au:"+str(config["cfr_automatic_properties"])
    tag += "_CFR-inv:"+str(config["cfr_invariants"])
    tag += "_CFR-sc:"+str(config["cfr_simplify_constraints"])
    return tag

def file2ID(file, prefix=""):
    a = file.replace(prefix,"")
    if a[0] == "/":
        a = a[1:]
    return a.replace("/","_")

def get_info(cache, file, prefix):
    name = file2ID(file, prefix)
    o = os.path.join(cache, name+".json")
    info = None
    print("->",os.path.isfile(o),o)
    if os.path.isfile(o):
        import json
        with open(o) as f:
            info = json.load(f)
    else:
        info = {"id":name,"file":file}
    if not "analysis" in info:
        info["analysis"] = []
    for a in info["analysis"]:
        ter = []
        for alg in a["config"]["termination"]:
            ter.append(alg)
        a["config"]["termination"] = ter
        a["status"] = str(TerminationResult(a["status"]))
        a["date"] = datetime.datetime.strptime(a["date"], "%Y-%m-%dT%H:%M:%S.%f")

    pprint(info)
    return info

def save_info(info, cache, file, prefix):
    name = file2ID(file, prefix)
    o = os.path.join(cache, name+".json")
    print(o)
    if os.path.isfile(o):
        os.remove(o)
    import json
    tojson = info
    if "file" in tojson:
        tojson["file"] = tojson["file"].replace(prefix,"")
    if "analysis" in tojson:
        for a in tojson["analysis"]:
            ter = []
            if "files" in a["config"]:
                del a["config"]["files"]
            for alg in a["config"]["termination"]:
                if isinstance(alg, (str)):
                    ter.append(alg)
                else:
                    ter.append(alg.get_name())
            a["config"]["termination"] = ter
            a["status"] = str(a["status"])
            a["date"] = str(a["date"].isoformat())
            a["output"] = str(a["output"])
    pprint(tojson)
    with open(o, "w") as f:
        json.dump(tojson, f, indent=4, sort_keys=True)
def extractname(filename):
    f = os.path.split(filename)
    b = os.path.split(f[0])
    c = os.path.splitext(f[1])
    return os.path.join(b[1], c[0])
if __name__ == "__main__":
    argParser = setArgumentParser()
    args = argParser.parse_args(sys.argv[1:])
    ar = vars(args)
    cachedir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), ar["cache"])
    files = ar["files"]
    sccd = ar["scc_depth"]
    dotF = ar["dotDestination"]
    verb = ar["verbosity"]
    cfr_au = 4
    cfr_ite= (ar["cfr_iterations_min"],ar["cfr_iterations_max"])
    lib = ["ppl"]
    inv = ["none", "polyhedra", "interval"]
    cfr_invs = ["none", "polyhedra", "interval"]
    dt = ["never", "iffail", "always"]
    if "timeout" in ar and ar["timeout"]:
        tout = int(ar["timeout"])
    else:
        tout = None
    if "memoryout" in ar and ar["memoryout"]:
        mout = int(ar["memoryout"])
    else:
        mout = None
    algs = []
    algs.append([termination.algorithm.lrf.PR()])
    for i in range(1, 3):
        algs.append([termination.algorithm.qnlrf.QNLRF({"max_depth": i, "min_depth": i,
                                                        "version": 1})])
    # algs.append([{"name": "qlrf_bg"}])
    numm = len(files)
    info = {}
    ite = 0
    for f in files:
        ite += 1
        print("({}/{}) {}".format(ite,numm,f))
        status = False
        info = get_info(cachedir, f, ar["prefix"])
        for cfr_it in range(cfr_ite[0], cfr_ite[1]+1):
            for i in inv:
                if status:
                    continue
                for cfr_inv in cfr_invs:
                    if status:
                        continue
                    for l in lib:
                        if status:
                            continue
                        for a in algs:
                            if status:
                                continue
                            a[0].set_prop("lib", l)
                            for d in dt:
                                if status:
                                    continue
                                name = os.path.basename(f)  # .replace("/","_")
                                config = {
                                    "scc_depth": sccd,
                                    "verbosity": verb,
                                    "ei_out": False,
                                    "termination": a,
                                    "invariants": i,
                                    "different_template": d,
                                    "simplify_constraints": True,
                                    "cfr_automatic_properties": [cfr_au],
                                    "cfr_iterations": cfr_it,
                                    "cfr_invariants": cfr_inv,
                                    "cfr_simplify_constraints": True,
                                    "cfr_user_properties":False,
                                    "cfr_invariants_threshold":False,
                                    "invariants_threshold":False,
                                    "files": [f],
                                    "lib": l,
                                    "tmpdir":None,
                                    "name": extractname(f),
                                    "output_destination":None,
                                    "output_formats":[]
                                }
                                print("Trying with : " + config2Tag(config))
                                response = sandbox(rankfinder.launch_file, args=(config, f, None),
                                                    time_segs=tout, memory_mb=mout)
                                response["date"] = datetime.datetime.today()
                                response["config"] = config
                                info["analysis"].append(response)
                                if response["status"].is_terminate():
                                    status = True
        save_info(info, cachedir, f, ar["prefix"])

