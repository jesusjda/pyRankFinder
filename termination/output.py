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
        if dest is None:
            self._ei_commands = eiol.eicommands()
            self._ei_actions = eiol.eiactions()
        else:
            self._ei_commands = eiol.eicommands(dest=dest)
            self._ei_actions = eiol.eiactions(dest=dest)

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

    def writefile(self, path, content):
        if self.ei:
            aux_p = path.split('/')
            aux_c = len(aux_p) - 1
            while aux_c > 0:
                if aux_p[aux_c] == "examples":
                    break
                if aux_p[aux_c] == "User_Projects":
                    break
                aux_c -= 1
            aux_t = ["translations"] + aux_p[aux_c+1:]
            r = '/'.join(aux_t)
            c = eiol.command_writefile(overwrite="true",
                                       text=content,
                                       filename=str(r))
            self._ei_commands.append(c)

    def show_output(self):
        if self.ei:
            # root = eiol.create_output(eicommands=self._ei_commands)
            print(ET.tostring(self._ei_commands,
                              encoding='utf8', method='xml'))
        return

Output_Manager = Output()
