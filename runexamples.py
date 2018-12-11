import argparse
from multiprocessing import Manager
from multiprocessing import Process
import os
import sys
import termination.algorithm
import irankfinder
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
    # IMPORTANT PARAMETERS
    argParser.add_argument("-f", "--files", nargs='+', required=True,
                           help="File to be analysed.")
    argParser.add_argument("-c", "--cache", required=True,
                           help="Folder cache.")
    argParser.add_argument("-p", "--prefix", required=True, default="",
                           help="Prefix of the files path")
    argParser.add_argument("-oe", "--only-errors", required=False, action='store_true',
                           help="Analyse only the results with errors.")
    argParser.add_argument("-sit", "--stop-if-terminate", required=False, action='store_true',
                           help="Analyse with each configuration until one terminates.")
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
    tag += "_CFR-st-bf:"+str(config["cfr_strategy_before"])
    tag += "_CFR-st-scc:"+str(config["cfr_strategy_scc"])
    tag += "_CFR-st-af:"+str(config["cfr_strategy_after"])
    return tag

def file2ID(file, prefix=""):
    a = file.replace(prefix,"")
    if a[0] == "/":
        a = a[1:]
    return a.replace("/","_")

def get_info(cache, file, prefix):
    name = file2ID(file, prefix)
    o = os.path.join(cache, name+".json")
    print("->",os.path.isfile(o),o)
    info = None
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
    print("saving")
    with open(o, "w") as f:
        json.dump(tojson, f, indent=4, sort_keys=True)

def extractname(filename):
    f = os.path.split(filename)
    b = os.path.split(f[0])
    c = os.path.splitext(f[1])
    return os.path.join(b[1], c[0])

def is_error(config, info):
    inf = get_i(config, info)
    if inf is None:
        return True
    return str(inf["status"]) == "Error"

def get_i(config, info):
    aas = info["analysis"]
    valids = []
    for a in aas:
        c = a["config"]
        good = True
        for k in config:
            if k == "termination":
                for t1, t2 in zip(c[k], config[k]):
                    if t1 == str(t2):
                        continue
                    else:
                        good = False
                        break
                if not good:
                    break
                continue
            if k != "invariants" and k not in c:
                continue
            try:
                if c[k] == config[k]:
                    continue
            except:
                if k == "invariants":
                    if c["nodeproperties"] == config[k]:
                        continue
            good = False
            break
        if good:
            valids.append(a)
    if len(valids) == 0:
        return None
    valids.sort(key=lambda a: a["date"], reverse=True)
    return valids[0]


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
    cfr_au = [4]
    cfr_ite= [1]
    lib = ["z3"]
    inv = ["polyhedra"]
    cfr_invs = ["polyhedra"]
    # ["scc", "after"] is not allowed
    cfr_strat = ["none", ["before"], ["scc"], ["after"], ["before", "after"], ["before", "scc"]] 
    cfr_configs = []
    conf = {"cfr_iterations": 1, "cfr_automatic_properties":4, "cfr_user_properties":False,
            "cfr_invariants":"none", "cfr_invariants_threshold": False, "cfr_simplify_constraints": True,
            "cfr_strategy_before":False,"cfr_strategy_scc":False,"cfr_strategy_after":False, "cfr_max_tries":1}
    if 0 in cfr_ite or "none" in cfr_strat or 0 in cfr_au:
        cfr_configs.append(dict(conf))
    for it in cfr_ite:
        if it ==0:
            continue
        conf["cfr_iterations"] = it
        for au in cfr_au:
            if au == 0:
                continue
            conf["cfr_automatic_properties"] = au
            for strat in cfr_strat:
                if strat == "none":
                    continue
                conf["cfr_strategy_before"] = "before" in strat
                conf["cfr_strategy_scc"] = "scc" in strat
                conf["cfr_strategy_after"] = "after" in strat
                for i in cfr_invs:
                    conf["cfr_invariants"] = i
                    cfr_configs.append(dict(conf))
    rniv = True
    dt = ["iffail"]
    if "timeout" in ar and ar["timeout"]:
        tout = int(ar["timeout"])
    else:
        tout = None
    if "memoryout" in ar and ar["memoryout"]:
        mout = int(ar["memoryout"])
    else:
        mout = None
    algs = [] #[[termination.algorithm.qnlrf.QNLRF({"max_depth": 2, "min_depth": 1,"version": 1})]]
    #algs.append([termination.algorithm.qlrf.QLRF_ADFG({"nonoptimal":True})])
    algs.append([termination.algorithm.lrf.PR()])
    for i in range(1, 3):
        algs.append([termination.algorithm.qnlrf.QNLRF({"max_depth": i, "min_depth": i,
                                                        "version": 1})])

    numm = len(files)
    info = {}
    ite = 0
    for f in files:
        ite += 1
        print("({}/{}) {}".format(ite,numm,f))
        status = False
        info = get_info(cachedir, f, ar["prefix"])
        todel = []
        for a in info["analysis"]:
            todel.append(a)
        #for a in todel:
        #    info["analysis"].remove(a)
        for cfr_conf in cfr_configs:
            for i in inv:
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
                            nname = extractname(f)
                            config = {
                                "scc_depth": sccd,
                                "verbosity": 3,
                                "ei_out": False,
                                "termination": a,
                                "invariants": i,
                                "different_template": d,
                                "simplify_constraints": True,
                                "cfr_automatic_properties": cfr_conf["cfr_automatic_properties"],
                                "cfr_iterations": cfr_conf["cfr_iterations"],
                                "cfr_invariants": cfr_conf["cfr_invariants"],
                                "cfr_simplify_constraints": cfr_conf["cfr_simplify_constraints"],
                                "cfr_user_properties": cfr_conf["cfr_user_properties"],
                                "cfr_invariants_threshold": cfr_conf["cfr_invariants_threshold"],
                                "cfr_strategy_before" : cfr_conf["cfr_strategy_before"],
                                "cfr_strategy_after" : cfr_conf["cfr_strategy_after"],
                                "cfr_strategy_scc" : cfr_conf["cfr_strategy_scc"],
                                "cfr_max_tries" : cfr_conf["cfr_max_tries"],
                                "invariants_threshold": False,
                                "files": [f],
                                "lib": l,
                                "tmpdir": None,
                                "name": extractname(f),
                                "output_destination": None,
                                "output_formats": [],
                                "remove_no_important_variables": rniv,
                                "user_reachability": False,
                                "reachability": "none",
                                "stop_if_fail": False,
                                "conditional_termination": False,
                                "show_with_invariants": False,
                                "print_graphs": False
                                #"recurrent_set": "/tmp/rec/"+nname[2:]+".pl"
                            }
                            skip = False
                            if ar["only_errors"]:
                                skip = True
                                if is_error(config,info):
                                    skip = False
                            if skip:
                                print("skip with : " + config2Tag(config))
                                continue
                            print("Trying with : " + config2Tag(config))
                            response = sandbox(irankfinder.launch_file, args=(config, f, None),
                                                time_segs=tout, memory_mb=mout)
                            response["date"] = datetime.datetime.today()
                            response["config"] = config
                            info["analysis"].append(response)
                            if response["status"].is_terminate():
                                status = ar["stop_if_terminate"]
        save_info(info, cachedir, f, ar["prefix"])












