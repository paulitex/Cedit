'''
Command Line interactive editor for Mercurial configuration files.

This extension adds two commands to Mercurial:
1. hg confedit - command line and interactive editor for
Mercurial configuration files
2. hg setuser - covenience command line and interactive editor for
setting username and password in the default user configuration file.
'''

from iniparse import SafeConfigParser
from mercurial.i18n import _
from mercurial import commands, hg, util
from ConfigParser import NoOptionError, NoSectionError
import os
import sys
import re

_options = ['&add', '&delete', '&view', 're&load', '&write', '&quit', '&help']
_help =_("""
Mercurial configuration editor extension.

A '*' before the prompt denotes unsaved changes. See 
http://www.selenic.com/mercurial/hgrc.5.html or 'man 5 hgrc' 
for more information on configuration files.

Commands:
a       add to or modify your configuration
d       delete/remove a section or property from your configuration
v       view current configuration, including changes
w       write/save to file
q       quit
l       load a configuration from disk
h       view this help screen
""")


def hgrccli(ui, **opts):
    """
    Edit mercurial configuration.
    For more information on configuration files,
    see http://www.selenic.com/mercurial/hgrc.5.html or 'man 5 hgrc'.
    Passing options will override the interactive editor.
    """
    if len(sys.argv) > 2:
        paths = []
        if opts['user']:
            paths.extend(util.user_rcpath())
        if opts['global']:
            paths.extend(util.system_rcpath())
        if opts['local']:
            paths.append(repopath())
        if opts['file']:
            paths.append(opts['file'])
        if not paths:
            ui.warn(_('No configuration selected (nothing written).\n'))
            exit(0)
        if opts['add']:
            setoption(ui, paths, opts['add'])
        if opts['delete']:
            deleteoption(ui, paths, opts['delete'])
    else:
        hgconfig(ui)


def setuser(ui, **opts):
    """
    Sets ui.username field in user's default Mercurial configuration.
    Username saved in format: First Last <email@address.com>.
    If a -u option is passed, it overrides and
    username will be set to given string.
    """
    path = util.user_rcpath()[0]
    conf = SafeConfigParser()
    conf.read(path)

    if opts['username']:
        username = opts['username']
    else:
        if opts['name']:
            name = opts['name']
        else:
            name = ui.prompt(_("Full Name: "), "")
        if opts['email']:
            email = opts['email']
        else:
            email = ui.prompt(_("Email: "), "")
        email = " <%s>" % email if email else ""
        username = "%s%s" % (name, email)
    if 'ui' not in conf.sections():
        conf.add_section('ui')
    conf.set('ui', 'username', username)
    with open(path, 'wb') as cfg:
        conf.write(cfg)
    ui.status(_("Username saved in %s\n") % path)


def setoption(ui, paths, optstring):
    """
    Sets option given in optionstring in every path given in paths.
    Creates files, sections, and properties as needed.
    """
    match = re.search("^([\w\-<>]+)\.([\w\-<>]+)\s+=\s+([^\s].*)", optstring)
    if not match:
        ui.warn(_("Invalid set property syntax. See 'hg help confedit'.\n"))
    else:
        sec = match.group(1)
        prop = match.group(2)
        val = match.group(3)
        for path in paths:
            conf = SafeConfigParser()
            conf.read(path)
            if sec not in conf.sections():
                conf.add_section(sec)
            conf.set(sec, prop, val)
            with open(path, 'wb') as cfg:
                conf.write(cfg)
            ui.status(_("Property set in %s\n") % path)


def deleteoption(ui, paths, delstring):
    """
    Deletes property or section in delstring.
    To delete an section, the delstring should simply be the section name.
    To delete a property, the delstring should be qualified with the section,
    e.g. ui.username
    """
    secmatch = re.search("^\s*([\w\-<>]+)\s*$", delstring)
    propmatch = re.search("^\s*([\w\-<>]+)\.([\w\-<>]+)\s*$", delstring)
    if secmatch:
        sec = secmatch.group(1)
        for path in paths:
            conf = SafeConfigParser()
            conf.read(path)
            if sec not in conf.sections():
                ui.warn(_("No section '%s' in %s\n") % (sec, path))
            else:
                conf.remove_section(sec)
                with open(path, 'wb') as cfg:
                    conf.write(cfg)
                ui.status(_("Section removed from %s\n") % path)
    elif propmatch:
        sec = propmatch.group(1)
        prop = propmatch.group(2)
        for path in paths:
            conf = SafeConfigParser()
            conf.read(path)
            if sec not in conf.sections():
                ui.warn(_("No %s section in %s") % (sec, path))
            else:
                removed = conf.remove_option(sec, prop)
                if removed:
                    with open(path, 'wb') as cfg:
                        conf.write(cfg)
                    ui.status(_("%s removed from %s\n") % (delstring, path))
                else:
                    ui.warn(_("Unable to remove %s from %s\n") %
                    (delstring, path))
    else:
        ui.warn(_("Invalid delete syntax. See 'hg help confedit'.\n"))


def repopath():
    cwd = os.getcwd()
    return os.path.join(cwd, ".hg", "hgrc")


class hgconfig(object):
    _dirty = False
    _ui = None
    _conf = None
    _path = ""
    _paths = []

    def __init__(self, ui):
        self._ui = ui
        self.setpaths()
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

    def setpaths(self):
        userpath = util.user_rcpath()[0]
        rpath =  repopath()
        util.rcpath().append(rpath)
        self._paths = [f for f in util.rcpath() if os.path.isfile(f)]
        self.checkpath(userpath, "user")
        if os.path.exists(os.path.join(os.getcwd(), ".hg")):
            # is there a local repository?
            self.checkpath(rpath, "repository")

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
        self._conf.data.clean_format()
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
        if self.warnflush('load a new configuration'):
            return
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
        self._conf.data.clean_format()
        self._dirty = False
        self._ui.status(_("Configuration loaded.\n"))

    def writeconf(self):
        with open(self._path, 'wb') as cfg:
            self._conf.write(cfg)
        self._ui.status(_("Configuration written to %s\n") % self._path)
        self._dirty = False

    def exitext(self):
        if self.warnflush('quit'):
            return
        exit(0)

    def warnflush(self, action):
        return self._dirty and self._ui.promptchoice("You have unsaved "
             "changes.\nReally %s before saving [y n]?" % action,
             ['&yes', '&no'], 1)

    def printhelp(self):
        self._ui.status(_help)

    def getPrompt(self):
        return "*>" if self._dirty else ">"

commands.norepo += " setuser confedit"
cmdtable = {
    "confedit": (hgrccli,
                [('a', 'add', '', _("Add/Set configuration property. Takes " +
                 "a string with format: '<section>.<property> = <value>'")),
                  ('d', 'delete', '', _("Delete from configuration. Pass" +
                  " section's name to remove entire section or " +
                  "'<section>.<prop>' to remove a single property")),
                 ('u', 'user', False, _('target user configuration')),
                 ('g', 'global', False, _("target global/system-wide " +
                 "configuration")),
                   ('l', 'local', False, _("target current repository's "+
                   "configuration")),
                   ('f', 'file', '', _("target configuration file at "+
                   "given path. "))],
                     "hg confedit [OPTIONS]"),
    "setuser": (setuser,
                [('n', 'name', '', _('full name')),
                  ('e', 'email', '', _('email address')),
                  ('u', 'username', '',
                   _('username (overrides other options)'))],
                     "hg setuser [OPTIONS]"),
                     }
