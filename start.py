#!/usr/bin/env python

"""
This script exists to boostrap the configuration editor. 

It creates a user configuration file, if one is not already present,
and adds this extension's current path to the configuration. If there is 
already a configuration file with a 'config' extension, it will be overwritten.
"""
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
    
def writeconfig(path):
    # find out where we are...
    thispath = os.path.abspath(os.path.dirname(__file__))
    conf.set(section, "config", thispath)
    config.savepretty(conf, path)

# Start script...
rcpath = getrcpath()
conf = getconfig(rcpath)
writeconfig(rcpath)
print _("Confedit succesfully added to %s") % rcpath
print _("If you just installed Mercurial, run \"hg setuser\"" +
"to set up your personal info.")
print _("Run \"hg confedit\" to further customize your configuration.")
