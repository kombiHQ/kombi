"""
Basic version template procedures.

The versions path is usually specified using <parent> token.

You can use the environment variable KOMBI_VERSION_PATTERN to define a
custom default pattern for the versions. The pattern can be define in three
parts where the only required part is the padding which is represented
as a sequence of # for each digit. For instance:
    01   ->  ##
    001  ->  ###
    0001 ->  ####

You can also define a prefix and suffix for the version pattern.
For instance:
    v01   -> v##
    v001  -> v###
    v0001 -> v####

    (including suffix)
    v01b   -> v##b
    v001b  -> v###b
    v0001b -> v####b

Additionally, a custom version pattern can be provided directly through
'labelver', 'newver', 'latestver', (etc) expressions. For instance:
    (labelver 1 v###)
    (new <parent> v#####)
    (latest <parent> v##)
"""

import os
import re
from ..Template import Template

DEFAULT_VERSION_PATTERN = "v###"

def verPrefix(version, versionPattern=''):
    """
    Return the version prefix.
    """
    if not versionPattern:
        versionPattern = os.environ.get('KOMBI_VERSION_PATTERN', DEFAULT_VERSION_PATTERN)

    patternParts = __splitVersionPattern(versionPattern)
    return str(version)[:len(patternParts['prefix'])]

def verNumber(version, versionPattern=''):
    """
    Return the version number.
    """
    if not versionPattern:
        versionPattern = os.environ.get('KOMBI_VERSION_PATTERN', DEFAULT_VERSION_PATTERN)

    patternParts = __splitVersionPattern(versionPattern)
    return str(version)[len(patternParts['prefix']): len(patternParts['prefix']) + len(patternParts['padding'])]

def verSuffix(version, versionPattern=''):
    """
    Return the version suffix.
    """
    if not versionPattern:
        versionPattern = os.environ.get('KOMBI_VERSION_PATTERN', DEFAULT_VERSION_PATTERN)

    patternParts = __splitVersionPattern(versionPattern)
    return str(version)[len(patternParts['prefix']) + len(patternParts['padding']):]

def label(versionNumber, versionPattern=''):
    """
    Return a version using the pattern.
    """
    if not versionPattern:
        versionPattern = os.environ.get('KOMBI_VERSION_PATTERN', DEFAULT_VERSION_PATTERN)

    return __buildVersion(
        int(versionNumber),
        versionPattern
    )

def new(versionsPath, versionPattern=''):
    """
    Return a new version.
    """
    if not versionPattern:
        versionPattern = os.environ.get('KOMBI_VERSION_PATTERN', DEFAULT_VERSION_PATTERN)

    version = __queryLatest(versionsPath, versionPattern)
    return label(
        version + 1,
        versionPattern
    )

def latest(versionsPath, versionPattern=''):
    """
    Return a new version, in case none version is found it version 0, for instance v000.
    """
    if not versionPattern:
        versionPattern = os.environ.get('KOMBI_VERSION_PATTERN', DEFAULT_VERSION_PATTERN)

    version = __queryLatest(versionsPath, versionPattern)
    return label(
        version,
        versionPattern
    )

def __buildVersion(version, versionPattern):
    """
    Return a resolved version string using the version pattern.
    """
    patternParts = __splitVersionPattern(versionPattern)
    return patternParts['prefix'] + str(version).zfill(len(patternParts['padding'])) + patternParts['suffix']

def __splitVersionPattern(versionPattern):
    """
    Split the version pattern in parts.
    """
    prefix = ''
    padding = ''
    suffix = ''
    for char in versionPattern:
        if char != '#' and not padding:
            prefix += char
        elif char != '#' and padding:
            suffix += char
        else:
            padding += char

    assert len(padding), 'Padding pattern representation (#) not found in version pattern: {}'.format(versionPattern)
    return {
        'prefix': prefix,
        'padding': padding,
        'suffix': suffix
    }

def __queryLatest(versionsPath, versionPattern):
    """
    Return the latest version found under the versions path.

    In case none version is found, it returns 0 by default.
    """
    version = 0
    patternParts = __splitVersionPattern(versionPattern)
    versionRegEx = "^" + patternParts['prefix'] + "[0-9]{" + str(len(patternParts['padding'])) + ",}" + patternParts['suffix'] + "$"

    # finding the latest version
    if os.path.exists(versionsPath):
        for directory in os.listdir(versionsPath):
            if re.match(versionRegEx, directory):
                version = max(
                    int(verNumber(directory, versionPattern)),
                    version
                )
    return version


# version prefix procedure
Template.registerProcedure(
    'verprefix',
    verPrefix
)

# version number procedure
Template.registerProcedure(
    'vernumber',
    verNumber
)

# version suffix procedure
Template.registerProcedure(
    'versuffix',
    verSuffix
)

# version label procedure
Template.registerProcedure(
    'labelver',
    label
)

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
