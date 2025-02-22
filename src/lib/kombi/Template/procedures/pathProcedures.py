"""
Basic path functions.
"""

import os
from glob import glob
from ..Template import Template

def dirname(string):
    """
    Return the dir name from a full path file.
    """
    return os.path.dirname(string)

def parentdirname(string):
    """
    Return the dir name of the parent folder from the full path file.
    """
    return dirname(dirname(string))

def basename(string):
    """
    Return the base name from a full path file.
    """
    return os.path.basename(string)

def basenamewithoutext(string):
    """
    Return the base name from a full path without the extension.
    """
    return os.path.splitext(basename(string))[0]

def exists(string):
    """
    Return if the input path exists.
    \todo: needs test
    """
    return int(os.path.exists(string))

def globpath(path):
    """
    Return the first result found by the glob or an empty string in case of no result.
    """
    result = glob(path)
    return result[0] if result else ""


# registering template procedures
Template.registerProcedure(
    'glob',
    globpath
)

Template.registerProcedure(
    'dirname',
    dirname
)

Template.registerProcedure(
    'exists',
    exists
)

Template.registerProcedure(
    'parentdirname',
    parentdirname
)

Template.registerProcedure(
    'basename',
    basename
)

Template.registerProcedure(
    'basenamewithoutext',
    basenamewithoutext
)

Template.registerProcedure(
    'noext',
    basenamewithoutext
)
