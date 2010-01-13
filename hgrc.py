'''
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


def hgrccli(ui, repo, **opts):
    """Edit mercurial configuration"""
    hgconfig(ui, repo)


class hgconfig(object):
    _ui = None
    _conf = ""
    _path = ""
    _paths = []

    def __init__(self, ui, repo):
        self._ui = ui
        util.rcpath().append(repo.join('hgrc'))
        self._paths = filter(lambda f: os.path.isfile(f), util.rcpath())
        self.reloadconf()
        self.printhelp()
        while True:
            # self._conf.sections()
            # self._conf.add_section("peter piper")
            index = self._ui.promptchoice("(m, v, r, w, q, h)>>>",
            _options, len(_options) - 1) # default to 'help'
            [lambda: self.modsection(),
            lambda: self.viewconf(),
            lambda: self.reloadconf(),
            lambda: self.writeconf(),
            lambda: exit(0),
            lambda: self.printhelp()][index]()

    def modsection(self):
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

    def viewconf(self):
        self._ui.status("\n%s\n" % str(self._conf))

    def reloadconf(self):
        if len(self._paths) > 1:
            self._ui.status("\nSelect configuration to edit:\n")
            for i in range(len(self._paths)):
                print " " + str(i) + ".  " + self._paths[i]
            index = self._ui.promptchoice(">",
            map(lambda num: "&" + str(num), range(len(self._paths))),
            len(self._paths) - 1)
            self._path = self._paths[index]
            self._conf = INIConfig(open(self._path))
        elif len(self._paths) == 1:
            self._path = self._paths[0]
            self._conf = INIConfig(open(self._path))
        else:
            # This is a little silly, since without a valid config file
            # how could this extension be loaded? But for completeness...
            self._path = default = util.user_rcpath()[0]
            index = self._ui.promptchoice("Unable to find configuration file."+
            " Would you like to make one at %s?" % default,
            ['&yes', '&no'], 'y')
            if index == 1:
                self._ui.status("No configuration to edit")
                exit(0)
            self._conf = INIConfig(open(default, "a+"))
        self._ui.status("Configuration loaded.\n")

    def writeconf(self):
        f = open(self._path, 'wb')
        f.write(str(self._conf))
        f.close()
        self._ui.status("Configuration written to %s\n" % self._path)
        exit(0)

    def printhelp(self):
        self._ui.status(_help)

cmdtable = {
    "hgrc": (hgrccli,
                     [],
                     "hg hgrc")}
