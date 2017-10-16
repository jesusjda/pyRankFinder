import xml.etree.ElementTree as ET
import eiol


class Output:

    ei = False
    verbosity = 0
    _ei_commands = None
    _ei_actions = None

    def __init__(self):
        self.ei = False
        self.verbosity = 0
        self._ei_commands = eiol.eicommands()
        self._ei_actions = eiol.eiactions()

    def restart(self, dest=None):
        self.printf(">"+dest)
        if dest is None:
            _ei_commands = eiol.eicommands()
            _ei_actions = eiol.eiactions()
        else:
            _ei_commands = eiol.eicommands(dest=dest)
            _ei_actions = eiol.eiactions(dest=dest)

    def printf(self, *kwargs):
        self.printif(0, *kwargs)

    def printif(self, verbosity, *kwargs):
        msg = ""
        for m in kwargs:
            msg += str(m)
        if self.verbosity >= verbosity:
            if self.ei:
                c = eiol.content(format="text", text=msg)
                self._ei_commands.append(eiol.command_print(content=c))
            else:
                print(kwargs)

    def print_rf_tr(self, cfg, tr_name, rfs):
        msg = "HI"  # rfs_tostring(rfs)
        if self.ei:
            c = eiol.content(format="text", text=msg)
            numl = str(cfg.get_edge(tr_name)["line"])
            d = {"from": numl}
            l = eiol.line(**d)
            ls = eiol.lines(line=l)
            self._ei_commands.append(eiol.command_addinlinemarker(lines=ls,
                                                                  content=c))
        else:
            print(tr_name + ":\n\t" + msg)

    def show_output(self):
        if self.ei:
            # root = eiol.create_output(eicommands=self._ei_commands)
            print(ET.tostring(self._ei_commands, encoding='utf8', method='xml'))
        return

Output_Manager = Output()
