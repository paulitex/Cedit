'''
Command Line Interface for editing .hgrc / Mercurial.ini configuration files
'''

from mercurial.i18n import _
from mercurial import commands, hg, util
from iniparse import SafeConfigParser
from ConfigParser import NoOptionError, NoSectionError
import os, StringIO

_options = ['&add', '&remove', '&view', 're&load', '&write', '&quit', '&help']
_options = map(lambda opt: _(opt), _options)
_help =_( """
Mercurial configuration editor extension.
Commands:
a       add to or modify your configuration
r       remove a section or property from your configuration
v       view current configuration, including changes
w       write to file and exit
q       quit, discarding changes
l       load a new configuration from disk (discarding changes)
h       view this help screen
""")


def hgrccli(ui, repo, **opts):
    """Edit mercurial configuration"""
    hgconfig(ui, repo)


class hgconfig(object):
    _ui = None
    _conf = None
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
            index = self._ui.promptchoice(_("(a, r, v, l, w, q, h)>>>"),
            _options, len(_options) - 1) # default to 'help'
            [lambda: self.modsection(),
            lambda: self.delsection(),
            lambda: self.viewconf(),
            lambda: self.reloadconf(),
            lambda: self.writeconf(),
            lambda: exit(0),
            lambda: self.printhelp()][index]()

    def modsection(self):
        """Adds or modifies sections and properties to current configuration"""
        sec = self._ui.prompt(_("Enter section name: "), "")
        if sec not in self._conf.sections():
            self._conf.add_section(sec)
        prop = self._ui.prompt(_("Enter property name: "), "")
        try:
            old_val = _(" (currently '%d'): ") % self._conf.get(sec, prop)
        except NoOptionError:
            old_val = ": "
        val = self._ui.prompt(_("Enter property value %s") % old_val)
        self._conf.set(sec, prop, val)
        
    def delsection(self):
        self._ui.status(_("Delete an entire (s)ection or a single (p)roperty?\n"))
        index = self._ui.promptchoice("(s, p)>>>", 
        [_('&section'), _('&property')])
        if index:
            sec = self._ui.prompt(_("Enter section name: "), "")
            prop = self._ui.prompt(_("Enter property name: "), "")
            try:
                if prop not in self._conf.options(sec):
                    self._ui.warn(_("Property '%s' not found\n") % prop)
                    return
                removed = self._conf.remove_option(sec, prop)
                if removed:
                    self._ui.status(_("Property removed\n"))
                else:
                    self._ui.warn(_("Unable to remove property '%s'\n") % prop)
            except NoSectionError:
                self._ui.warn(_("Section not found.\n"))
        else:
            sec = self._ui.prompt(_("Enter section name: "), "")
            if sec not in self._conf.sections():
                self._ui.warn(_("Section '%s' not found\n") % sec)
                return
            removed = self._conf.remove_section(sec)
            if removed:
                self._ui.status(_("Section removed\n"))
            else:
                self._ui.warn(_("Unable to remove section '%s'\n") % sec)

    def viewconf(self):
        sb = StringIO.StringIO()
        self._conf.write(sb)
        self._ui.status("%s\n" % sb.getvalue())

    def reloadconf(self):
        self._conf = SafeConfigParser()
        if len(self._paths) > 1:
            self._ui.status(_("\nSelect configuration to edit:\n"))
            for i in range(len(self._paths)):
                print " " + str(i) + ".  " + self._paths[i]
            index = self._ui.promptchoice(">",
            map(lambda num: "&" + str(num), range(len(self._paths))),
            len(self._paths) - 1)
            self._path = self._paths[index]
        elif len(self._paths) == 1:
            self._path = self._paths[0]
        else:
            # This is a little silly, since without a valid config file
            # how could this extension be loaded? But for completeness...
            self._path = default = util.user_rcpath()[0]
            msg = _("Unable to find configuration file."
                    " Would you like to make one at %s?") % default
            index = self._ui.promptchoice(msg, [_('&yes'), _('&no')], _('y'))
            if index == 1:
                self._ui.status(_("No configuration to edit"))
                exit(0)
            open(default, "ab")
        self._conf.read((self._path))
        self._ui.status(_("Configuration loaded.\n"))

    def writeconf(self):
        with open(self._path, 'wb') as cfg:
            self._conf.write(cfg)
        self._ui.status(_("Configuration written to %s\n") % self._path)
        exit(0)

    def printhelp(self):
        self._ui.status(_help)

cmdtable = {
    "hgrc": (hgrccli,
                     [],
                     "hg hgrc")}
