import os
import imp
import inspect
import traceback
import importlib

import modules

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".reload"

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):
        self.reloadmodules()
        return

    # Reloads all modules, loads any new modules as well
    # TODO: Should be importlib.reload(), but that's not implemented on 3.2
    # Fall back to imp instead until 3.2+ is considered stable enough
    def reloadmodules(self):

        # Reload the modules folder, find any new modules
        imp.reload(modules)
        current_modules = self.share.get_modulelist()
        old_module_names = [os.path.basename(inspect.getfile(m))[:-3] for m in current_modules]
        all_module_names = modules.__all__
        new_module_names = [m for m in all_module_names if m not in old_module_names]
        new_modules = []
        remove_modules = []

        # Load new modules
        for mod in new_module_names:
            try:
                new_mod = importlib.import_module("." + mod, package="modules")
                new_modules.append(new_mod)
                self.sendmsg("LOAD NEW MODULE {}".format(mod))
            except:
                self.sendmsg("LOAD NEW MODULE {} FAILED".format(mod))

        # Reloads all known modules
        for mod in current_modules:
            moduleClass = getattr(mod, "Module")
            try:
                mod = imp.reload(mod)
            except:
                self.sendmsg("RELOAD MODULE {} FAILED".format(moduleClass))
                remove_modules.append(mod)

        # Removes unloadable modules from known modules and adds new modules
        self.write_modulelist([m for m in current_modules if m not in remove_modules] + new_modules)
        self.sendmsg("RELOADED MODULES FOLDER")
