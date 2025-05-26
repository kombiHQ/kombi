"""
Basic system functions.
"""

import tempfile
import getpass
import uuid
import os
from ..Template import Template

def resolvePath(prefixPath, suffixPath):
    """
    Return a resolved path.

    It works by trying to find the suffix path path under the prefix
    path otherwise it tries to find the suffix path under prefix path
    parent levels (in case it does not find the suffix path an empty
    string is returned instead).
    """
    result = ""

    currentLevel = prefixPath
    while currentLevel:
        findPath = os.path.join(currentLevel, suffixPath)
        if os.path.exists(findPath):
            result = findPath
            break

        parentLevel = os.path.dirname(currentLevel)
        if parentLevel == currentLevel:
            break

        currentLevel = parentLevel
    return result.replace('\\', '/')

def user():
    """
    Return the kombi user.
    """
    return os.environ.get('KOMBI_USER', getpass.getuser())

def random():
    """
    Return a random unique string.
    """
    return str(uuid.uuid4())

def tmp():
    """
    Return the location of the temporary directory.
    """
    return os.environ.get('KOMBI_TEMP_REMOTE_DIR', tempfile.gettempdir())

def tmpdir(baseDirectory=''):
    """
    Return a new temporary directory path (under the OS temp location).
    """
    path = os.path.join(
        tmp() if not baseDirectory else baseDirectory,
        random()
    )

    return path

def env(name, defaultValue=''):
    """
    Return the value of an environment variable.
    """
    return os.environ.get(name, defaultValue)


# registering template procedures
Template.registerProcedure(
    'resolvepath',
    resolvePath
)

Template.registerProcedure(
    'user',
    user
)

Template.registerProcedure(
    'rand',
    random
)

Template.registerProcedure(
    'tmp',
    tmp
)

Template.registerProcedure(
    'tmpdir',
    tmpdir
)

Template.registerProcedure(
    'env',
    env
)
