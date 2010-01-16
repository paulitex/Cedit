'''
Command Line interactive editor for Mercurial configuration files.

This extension adds two commands to Mercurial:
1. hg config - interactive editor for Mercurial configuration files
2. hg setuser - sets a username and password in the default user configuration file.
'''

try:
    from iniparse import SafeConfigParser
    _noiniparse = False
except Exception:
    _noiniparse = True
from mercurial.i18n import _
from mercurial import commands, hg, util
from ConfigParser import NoOptionError, NoSectionError
import os

_options = ['&add', '&remove', '&view', 're&load', '&write', '&quit', '&help']
_help =_("""
Mercurial configuration editor extension.

A '*' before the prompt denotes the file has been modified since last saving.
Type 'sections'

Commands:
a       add to or modify your configuration
r       remove a section or property from your configuration
v       view current configuration, including changes
w       write/save to file 
q       quit
l       load a configuration from disk
h       view this help screen
""")


def hgrccli(ui, repo, **opts):
    """Edit mercurial configuration"""
    if _noiniparse:
        print("To use the hgrc editor extension you must have iniparse" +
        " installed.\nIt can be found at http://code.google.com/p/iniparse/")
        exit(0)
    hgconfig(ui, repo)

def setuser(ui, **opts):
    path = util.user_rcpath()[0]
    conf = SafeConfigParser()
    conf.read(path)
    name = ui.prompt(_("Full Name: "), "Alex Doe")
    email = ui.prompt(_("Email: "), "")
    email = " <%s>" % email if email else ""
    conf.set('ui', 'username', "%s%s" % (name, email))
    with open(path, 'wb') as cfg:
        conf.write(cfg)
    ui.status(_("User set in configuration at %s\n") % path)


class hgconfig(object):
    _dirty = False
    _ui = None
    _conf = None
    _path = ""
    _paths = []

    def __init__(self, ui, repo):
        self._ui = ui
        self.setpaths(repo)
        self.reloadconf()
        self.printhelp()
        while True:
            index = self._ui.promptchoice(self.getPrompt(),
            _options, len(_options) - 1) # default to 'help'
            [self.modsection,
            self.delsection,
            self.viewconf,
            self.reloadconf,
            self.writeconf,
            self.exitext,
            self.printhelp][index]()

    def setpaths(self, repo):
        userpath = util.user_rcpath()[0]
        repopath = repo.join('hgrc')
        util.rcpath().append(repopath)
        self._paths = [f for f in util.rcpath() if os.path.isfile(f)]
        self.checkpath(userpath, "user")
        self.checkpath(repopath, "repository")

    def checkpath(self, path, pathtype):
        if path not in self._paths and self._ui.promptchoice(_("No %(a)s "+
        "configuration found at %(b)s.\nWould you like to create one [y n]?") %
            {'a': pathtype, 'b': path}, ['&no', '&yes'], 1):
                with open(path, "wb") as _empty:
                    pass # Create an empty file for later editing
                self._paths.append(path)

    def modsection(self):
        """Adds or modifies sections and properties to current configuration"""
        sec = self._ui.prompt(_("Enter section name: "), "")
        if sec not in self._conf.sections():
            self._conf.add_section(sec)
        prop = self._ui.prompt(_("Enter property name: "), "")
        try:
            old_val = _(" (currently '%s'): ") % self._conf.get(sec, prop)
        except NoOptionError:
            old_val = ": "
        val = self._ui.prompt(_("Enter property value %s") % old_val, "")
        self._conf.set(sec, prop, val)
        self._ui.status(_("Value set\n"))
        self._dirty = True

    def delsection(self):
        self._ui.status(_("Delete an entire (s)ection or a single (p)roperty"+
        " [(m) return to main menu]? \n"))
        index = self._ui.promptchoice(self.getPrompt(),
        ['&section', '&property', '&main'], 2)
        if index == 2:
            return
        elif index:
            sec = self._ui.prompt(_("Enter section name: "), "")
            prop = self._ui.prompt(_("Enter property name: "), "")
            try:
                if prop not in self._conf.options(sec):
                    self._ui.warn(_("Property '%s' not found\n") % prop)
                    return
                removed = self._conf.remove_option(sec, prop)
                if removed:
                    self._ui.status(_("Property removed\n"))
                    self._dirty = True
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
                self._dirty = True
            else:
                self._ui.warn(_("Unable to remove section '%s'\n") % sec)

    def viewconf(self):
        confstr = str(self._conf.data)
        if not confstr:
            self._ui.status(_("(Empty configuration)"))
        self._ui.status("%s\n" % confstr)

    def reloadconf(self):
        if self.warndirty('load a new configuration'): return
        self._conf = SafeConfigParser()
        if len(self._paths) > 1:
            self._ui.status(_("\nSelect configuration to edit:\n"))
            for i in range(len(self._paths)):
                print " " + str(i) + ".  " + self._paths[i]
            index = self._ui.promptchoice(self.getPrompt(),
            ["&" + str(num) for num in range(len(self._paths))],
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
        self._dirty = False
        self._ui.status(_("Configuration loaded.\n"))

    def writeconf(self):
        with open(self._path, 'wb') as cfg:
            self._conf.write(cfg)
        self._ui.status(_("Configuration written to %s\n") % self._path)
        self._dirty = False

    def exitext(self):
        if self.warndirty('quit'): return
        exit(0)
        
    def warndirty(self, action):
        return self._dirty and self._ui.promptchoice("You have unsaved changes.\n"
             "Really %s before saving [y n]?" % action, ['&yes', '&no'], 1)
        
        
    def printhelp(self):
        self._ui.status(_help)
        
    def getPrompt(self):
        return "*>" if self._dirty else ">"

commands.norepo += " setuser"
cmdtable = {
    "config": (hgrccli,
                     [],
                     "hg hgrc"),
    "setuser": (setuser,
                     [],
                     "hg setuser"),
                     }
