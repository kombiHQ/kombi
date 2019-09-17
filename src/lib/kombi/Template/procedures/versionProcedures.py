"""
Basic version template procedures.

The versions path is usually specified using <parent> token.
"""

import os
import re
from ..Template import Template

def new(versionsPath):
    """
    Return a new version.
    """
    version = __queryLatest(versionsPath)

    return 'v' + str(version + 1).zfill(3)

def latest(versionsPath):
    """
    Return a new version, in case none version is found it returns v000.
    """
    version = __queryLatest(versionsPath)

    return 'v' + str(version).zfill(3)

def __queryLatest(versionsPath):
    """
    Return the latest version found under the versions path.

    In case none version is found, it returns 0 by default.
    """
    version = 0
    versionRegEx = "^v[0-9]{3}$"

    # finding the latest version
    if os.path.exists(versionsPath):
        for directory in os.listdir(versionsPath):
            if re.match(versionRegEx, directory):
                version = max(int(directory[1:]), version)

    return version


# new version procedure
Template.registerProcedure(
    'newver',
    new
)

# latest version procedure
Template.registerProcedure(
    'latestver',
    latest
)
