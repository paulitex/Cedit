#!/usr/bin/env python

'''
hgrc_cli

Command Line Interface for editing .hgrc / Mercurial.ini configuration files
'''

from iniparse import INIConfig
from mercurial import commands, hg, util
import os, sys

#  Sections Reference: http://www.selenic.com/mercurial/hgrc.5.html
#  Written by Bryan O'Sullivan <bos@serpentine.com>.
_sections = {
"alias": "Defines command aliases. Aliases allow you to define your own"+
" commands in terms of other commands (or aliases)," +
" optionally including arguments.",
"auth": "Authentication credentials for HTTP authentication."+
" Each line has the following format:" +
" <name>.<argument> = <value> where <name> is used to group arguments"+
" into authentication entries.",
"decode": "Filters for transforming files on checkout. This would"+
" typically be used for " +
"newline processing or other localization/canonicalization of files.",
"encode": "Filters for transforming files on checkin. This would"+
" typically be used for " +
"newline processing or other localization/canonicalization of files.",
"diff": "Settings used when displaying diffs. They are all Boolean "+
"and defaults to False.",
"email": "Settings for extensions that send email messages.",
"extensions": "Mercurial has an extension mechanism for adding new " +
"features. To enable an extension, create an entry for it in this section.",
"format": "Settings related to repository format",
"merge-patterns": "This section specifies merge tools to "+
"associate with particular file"+
" patterns. Tools matched here will take precedence over the default "+
"merge tool. Patterns are globs by default, rooted at the repository root.",
"merge-tools": "This section configures external merge tools"+
" to use for file-level merges.",
"hooks": "Commands or Python functions that get automatically"+
" executed by various actions "+
"such as starting or finishing a commit. Multiple hooks can be"+
" run for the same action by "+
"appending a suffix to the action. Overriding a site-wide hook"+
" can be done by changing its "+
"value or setting it to an empty string.",
"http_proxy": "Used to access web-based Mercurial"+
" repositories through a HTTP proxy.",
"smtp": "Configuration for extensions that need to send email messages.",
"patch": "Settings used when applying patches, for instance through "+
"the 'import' command or with Mercurial Queues extension.",
"paths": "Assigns symbolic names to repositories. "+
"The left side is the symbolic name, and the"+
" right gives the directory or URL that is the location of the repository.",
"profiling": "Specifies profiling format and file output.",
"server": "Controls generic server settings.",
"trusted": "For security reasons, Mercurial will not use the settings in"+
" the .hg/hgrc file from a repository if it doesn't belong to a trusted user"+
" or to a trusted group. This section specifies what users and groups are"+
" trusted. The current user is always trusted. To trust everybody,"+
" list a user or a group with name *.",
"ui": "User interface controls.",
"web": "Web interface configuration."}
_options = ['&modify', '&view', '&reload', '&write', '&quit', '&help']

_help = """
Mercurial configuration editor extension.
Commands:
m       modify your configuration
v       view current configuration, including changes
w       write file and exit
q       quit, discarding changes
r       reload configuration from disk (discard changes)
h       view this help screen
"""

#       main function of extension. Should be smart enough to figure out
#       what platform we're on and read in the correct config file but isn't
#       currently.
#       Should also give option to read user default (~/.hgrc) or
#       project default ("./.hg/hgrc") config (and maybe also system-wide
#       default?).

def hgrc_cli(ui, **opts):
    """Edit mercurial configuration"""
    ui.status("Reading current configuration...\n")
    conf = reload_conf(ui)
    print_help(conf, ui)
    for path in util.rcpath():
        print path
    while True:
        index = ui.promptchoice("(m, v, r, w, q, h)>>>",
        _options, len(_options) - 1) # default to 'help'
        conf = [lambda c: mod_section(c, ui),
                lambda c: view_conf(c, ui),
                lambda c: reload_conf(ui),
                lambda c: write_conf(c, ui),
                lambda c: exit(0),
                lambda c: print_help(c, ui)][index](conf)


def mod_section(conf, ui):
    """Adds or modifies sections and properties to current configuration"""
    # following adapted from mercurial.ui._readline()
    # and from http://stackoverflow.com/questions/2046050
    if sys.stdin.isatty(): 
        try:               
            # magically add command line editing support, where
            # available
            import readline
            def complete(text, state):
                for cmd in _sections.keys():
                    if cmd.startswith(text):
                        if not state:
                            return cmd
                        else:
                            state -= 1
            
            readline.parse_and_bind("tab: complete")
            readline.set_completer(complete)
            # windows sometimes raises something other than ImportError
        except Exception:
            pass
    sec = ui.prompt("Enter section name: ", "")
    if sec not in conf._sections.keys():
        conf._new_namespace(sec)  
    try:
        readline.set_completer() # reset tab-completes
    except Exception:
        pass
    prop = ui.prompt("Enter property name: ", "")
    try:
        old_val = " (currently '" + conf[sec][prop] + "'): "
    except KeyError:
        old_val = ": "
    val = ui.prompt("Enter property value" + old_val, "")
    conf[sec][prop] = val
    return conf

def view_conf(conf, ui):
    ui.status("\n" + str(conf) + "\n")
    return conf


def reload_conf(ui):
    home = os.environ.get("HOME")
    file = home + "/.hgrc"
    conf = INIConfig(open(file))
    ui.status("Configuration reloaded.\n")
    return conf


def write_conf(conf, ui):
    home = os.environ.get("HOME")
    file = home + "/.hgrc"
    f = open(file, 'w')
    print >>f, conf
    f.close()
    ui.status("Configuration written to " + file + "\n")
    exit(0)


def print_help(conf, ui):
    ui.status(_help)
    return conf

commands.norepo += " hgrc"
cmdtable = {
    "hgrc": (hgrc_cli,
                     [],
                     "hg hgrc")}
