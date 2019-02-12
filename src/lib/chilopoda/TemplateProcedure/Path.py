import os
from ..Template import Template

class _Path(object):
    """
    Basic path functions.
    """

    @staticmethod
    def dirname(string):
        """
        Return the dir name from a full path file.
        """
        return os.path.dirname(string)

    @staticmethod
    def parentdirname(string):
        """
        Return the dir name of the parent folder from the full path file.
        """
        return _Path.dirname(_Path.dirname(string))

    @staticmethod
    def basename(string):
        """
        Return the base name from a full path file.
        """
        return os.path.basename(string)

    @staticmethod
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
        return _Path.rfindpath(fileName, previousPath, finalPath)

    @staticmethod
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
            result = _Path.findpath(fileName, nextPath)
            if result:
                return result

        return result


# registering template procedures
Template.registerProcedure(
    'dirname',
    _Path.dirname
)

Template.registerProcedure(
    'parentdirname',
    _Path.parentdirname
)

Template.registerProcedure(
    'basename',
    _Path.basename
)

Template.registerProcedure(
    'rfindpath',
    _Path.rfindpath
)

Template.registerProcedure(
    'findpath',
    _Path.findpath
)
