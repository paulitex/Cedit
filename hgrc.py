#!/usr/bin/env python

'''
hgrc_cli

Command Line Interface for editing .hgrc / Mercurial.ini configuration files
'''

from iniparse import INIConfig
from mercurial import commands, hg, util
import os

_options = ['&modify', '&view', '&reload', '&write', '&quit', '&help']
_help = """
Mercurial configuration editor extension.
Commands:
m       modify your configuration
v       view current configuration, including changes
w       write file and exit
q       quit, discarding changes
r       (re)load a new configuration from disk (discarding changes)
h       view this help screen
"""

def hgrc_cli(ui, **opts):
    """Edit mercurial configuration"""
    hgconfig(ui)


class hgconfig(object):
    _ui = None
    _conf = ""
    _path = ""
    def __init__(self, ui):
        self._ui = ui
        self._conf = self.reload_conf()
        self.print_help()
        while True:
            print "CONF! " + _conf
            print "PATH!" + _path
            index = self._ui.promptchoice("(m, v, r, w, q, h)>>>",
            _options, len(_options) - 1) # default to 'help'
            [lambda: self.mod_section(),
            lambda: self.view_conf(),
            lambda: self.reload_conf(),
            lambda: self.write_conf(),
            lambda: exit(0),
            lambda: self.print_help()][index]()


    def mod_section(self):
        """Adds or modifies sections and properties to current configuration"""
        sec = self._ui.prompt("Enter section name: ", "")
        if sec not in self._conf._sections.keys():
            self._conf._new_namespace(sec)
        prop = self._ui.prompt("Enter property name: ", "")
        try:
            old_val = " (currently '" + self._conf[sec][prop] + "'): "
        except KeyError:
            old_val = ": "
        val = self._ui.prompt("Enter property value" + old_val, "")
        self._conf[sec][prop] = val

    def view_conf(self):
        self._ui.status("\n" + str(self._conf) + "\n")

    def reload_conf(self):
        paths = filter(lambda f: os.path.isfile(f), util.rcpath())
        if len(paths) > 1:
            self._ui.status("Available configurations:\n")
            for i in range(len(paths)):
                print "[" + str(i) + "]\t" + paths[i]
            index = self._ui.promptchoice("Which would you like to edit? ",
            map(lambda num: "&" + str(num), range(len(paths))), len(paths) - 1)
            self._path = paths[index]
            self._conf = INIConfig(open(self._path))
        elif len(paths) == 1:
            self._path = paths[0]
            self._conf = INIConfig(open(self._path))
        else:
            # This is a little silly, since without a valid config file
            # how could this extension be loaded? But for completeness...
            self._path = default = util.user_rcpath()[0]
            index = self._ui.promptchoice("Unable to find configuration file. "+
            "Would you like to make one at " + default + "?",
            ['&yes', '&no'], 'y')
            if index == 1:
                self._ui.status("No configuration to edit")
                exit(0)
            self._conf = INIConfig(open(default, "a+"))
        self._ui.status("Configuration loaded.\n")

    def write_conf(self):
        print "PATH: " + self._path
        f = open(self._path, 'w')
        print >>f, conf
        f.close()
        self._ui.status("Configuration written to " + _path + "\n")
        exit(0)

    def print_help(self):
        self._ui.status(_help)

commands.norepo += " hgrc"
cmdtable = {
    "hgrc": (hgrc_cli,
                     [],
                     "hg hgrc")}
