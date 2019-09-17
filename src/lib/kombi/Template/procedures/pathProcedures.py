"""
Basic path functions.
"""

import os
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

def rfindpath(fileName, startPath, finalPath=None):
    """
    Find and return a specific file.

    Starts from the "startPath" and it goes backwards until it finds the specified file or reaches the "finalPath".
    If a file is not found, raises an IOError exception.

    :param fileName: The file name to find.
    :type fileName: str
    :param startPath: The path to start.
    :type startPath: str
    :param finalPath: It stops to search when reaching this path.
    :type: finalPath: str
    """
    resultPath = os.path.join(startPath, fileName)
    if os.path.exists(resultPath):
        return resultPath

    if startPath == finalPath or startPath == '/':
        raise IOError('File was not found')

    previousPath = os.path.dirname(startPath)
    return rfindpath(fileName, previousPath, finalPath)

def findpath(fileName, startPath):
    """
    Find and return a specific file.

    Starts from the "startPath" and it goes forwards until it finds the specified file. If a file is not found,
    return an empty string.

    :param fileName: The file name to find.
    :type fileName: str
    :param startPath: The path to start.
    :type startPath: str
    """
    result = ''
    resultPath = os.path.join(startPath, fileName)
    if os.path.exists(resultPath):
        return resultPath

    # When it can not access the next directory (e.g. permissions errors), It raises a StopIteration Error.
    try:
        dirList = next(os.walk(startPath))[1]
    except StopIteration:
        dirList = []

    for dirName in dirList:
        nextPath = os.path.join(startPath, dirName)
        result = findpath(fileName, nextPath)
        if result:
            return result

    return result


# registering template procedures
Template.registerProcedure(
    'dirname',
    dirname
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
    'rfindpath',
    rfindpath
)

Template.registerProcedure(
    'findpath',
    findpath
)
