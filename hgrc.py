#!/usr/bin/env python

'''
hgrc_cli

Command Line Interface for editing .hgrc / Mercurial.ini configuration files
'''

from iniparse import INIConfig
from mercurial import commands, hg
import os

# 	Standard sections could be mapped to one-line help 
#	strings explaining their purpose.
# 	E.g. "help alias" => "Defines command aliases. 
#	Aliases allow you to define your own commands in terms of 
#	other commands (or aliases), optionally including arguments."
#
#  Reference: http://www.selenic.com/mercurial/hgrc.5.html

_options = [ '&modify', '&view', '&reload', '&write', '&quit', '&help']

_help = """
Mercurial configuration editor extension.
Commands:
m	modify your configuration
v	view current configuration, including changes
w	write file and exit
q	quit, discarding changes
r	reload configuration from disk (discard changes)
h	view this help screen
"""

# 	main function of extension. Should be smart enough to figure out
#	what platform we're on and read in the correct config file but isn't
#	currently.
#	Should also give option to read user default (~/.hgrc) or
#	project default ("./.hg/hgrc") config (and maybe also system-wide
#	default?).	
def hgrc_cli(ui, **opts):
	"""Edit mercurial configuration"""
	ui.status("Reading current configuration...\n")
	conf = reload_conf(ui)
	print_help(conf, ui)
	while True:
		index = ui.promptchoice("(m, v, r, w, q, h)>>>", _options, len(_options) - 1) # default to 'help'
		conf = [	lambda c: mod_section(c, ui), 
					lambda c: view_conf(c, ui),
					lambda c: reload_conf(ui),
					lambda c: write_conf(c, ui),
					lambda c: exit(0),
					lambda c: print_help(c, ui)
				][index](conf)


def mod_section(conf, ui):
	"""Adds or modifies sections and properties to current working configuration"""
	sec = ui.prompt("Enter section name: ", "")
	prop = ui.prompt("Enter property name: ", "")
	val = ui.prompt("Enter new property value: ", "")
	# 	Below is how the properties are actually set using the iniparse api.
	#	This is the only example setter api given at http://code.google.com/p/iniparse/wiki/UsageExamples
	#	but it's bad for a number of reasons: Can't use multi-word sections, properties, or values
	#	and also executes arbitrary user input which isn't the safest thing to do.
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
                     "hg hgrc")
}