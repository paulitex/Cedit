#!/usr/bin/env python
#
# start.py - Bootstrapping script for cedit. Gets config.py as an extension
# in the user's default hgrc. This means that new users never have to
# edit a configuration file by hand, if they so choose.
#
# Copyright 2010 Paul Lambert <paul@matygo.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

"""
This script exists to boostrap the cedit Mercurial configuration editor.

It creates a user configuration file, if one is not already present,
and adds this extension's current path to the configuration. If there is
already a configuration file entry for a 'config' extension, it will be overwritten.
"""

from __future__ import with_statement
import os

try:
    from mercurial import util
    from mercurial.i18n import _
except:
    raise SystemExit(_(
        "Couldn't import mercurial libraries"))
from iniparse import SafeConfigParser
import config

section = "extensions"


def getrcpath():
    if 'HGRCPATH' in os.environ:
        path = os.environ['HGRCPATH'].split(os.pathsep)[0]
    else:
        path = util.user_rcpath()[0]
    if not os.path.exists(path):
        with open(path, "wb") as _empty:
            pass # create empty file
    return path


def getconfig(path):
    conf = SafeConfigParser()
    conf.read(path)
    if section not in conf.sections():
        conf.add_section(section)
    return conf


def writeconfig(conf, path):
    # find out where we are...
    thispath = os.path.abspath(os.path.dirname(__file__))
    conf.set(section, "config", thispath)
    config.savepretty(conf, path)

# Start script...
rcpath = getrcpath()
conf = getconfig(rcpath)
writeconfig(conf, rcpath)
print _("cedit succesfully added to %s") % rcpath
print _("If you just installed Mercurial, run \"hg setuser\"" +
"to set up your personal info.")
print _("Run \"hg cedit\" to further customize your configuration.")
