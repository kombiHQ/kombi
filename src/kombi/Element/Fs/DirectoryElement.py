import os
import re
import pathlib
from .FsElement import FsElement
from ...Template import Template
from .. import Element

class DirectoryElement(FsElement):
    """
    Directory element.
    """

    # checking for digits as prefix separated by x or X and finishing with digits as suffix
    __resolutionRegex = r'^[0-9]+[x|X][0-9]+$'
    __ignoreWidth = 320
    __ignoreHeight = 240

    def __init__(self, *args, **kwargs):
        """
        Create a directory element.
        """
        super(DirectoryElement, self).__init__(*args, **kwargs)

        # in case the directory has a name "<width>x<height>" lets extract
        # this information and assign that to variables
        if re.match(self.__resolutionRegex, self.var('name')):
            width, height = map(int, self.var('name').lower().split('x'))

            # making sure it contains at least a QVGA resolution, otherwise
            # ignore it
            if width >= self.__ignoreWidth and height >= self.__ignoreHeight:
                self.setVar('width', width)
                self.setVar('height', height)

    def isLeaf(self):
        """
        Return a boolean telling if the element is leaf.
        """
        return False

    def join(self, *levelNames):
        """
        Return a child element based on the input level path names (if not found return None instead).
        """
        current = self
        for levelName in levelNames:
            found = False
            for child in current.children():
                if child.var('name') == levelName:
                    current = child
                    found = True
                    break
            if not found:
                return None

        return current

    @classmethod
    def test(cls, path, parentElement):
        """
        Test if the path contains a directory.
        """
        if not super(DirectoryElement, cls).test(path, parentElement):
            return False
        return cls.cachedPathQuery(path, 'is_dir')
    
    @classmethod
    def createFromPath(cls, fullPath, elementType=None, parentElement=None):
        """
        Create a directory element based on the full directory system path string.

        This method bypasses querying the file system by pre-caching the expected path properties,
        which significantly improves performance when constructing elements.
        """
        directoryPath = pathlib.Path(fullPath)
        cls.setCachedPathQuery(directoryPath, 'exists', True)
        cls.setCachedPathQuery(directoryPath, 'is_file', False)
        cls.setCachedPathQuery(directoryPath, 'is_dir', True)

        return super().createFromPath(fullPath, elementType, parentElement)

    def _computeChildren(self):
        """
        Return the directory contents.
        """
        result = []
        currentPath = str(self.path())

        # Using os.scandir for performance improvements, as it provides both the entry name
        # and type (file or directory) in a single call
        for childEntry in os.scandir(currentPath):
            childPath = pathlib.Path(os.path.join(currentPath, childEntry.name))
            self.setCachedPathQuery(childPath, 'exists', True)
            self.setCachedPathQuery(childPath, 'is_file', childEntry.is_file())
            self.setCachedPathQuery(childPath, 'is_dir', childEntry.is_dir())

            childElement = Element.create(childPath, self)
            result.append(childElement)

        def __sortElement(x):
            name = x.var('name').lower() if 'group' not in x.tagNames() else x.tag('group').lower()
            # in case of a version folder v#### we want to sort the recent versions on top
            if not x.isLeaf() and int(Template.runProcedure('isver', name)):
                version = int(Template.runProcedure('vernumber', name))
                name = Template.runProcedure('verprefix', name) + str(9999999999 - version).zfill(10) + Template.runProcedure('versuffix', name)

            return (int(x.isLeaf()), name)

        # sorting result by name
        result.sort(
            key=__sortElement
        )

        return result


# registration
Element.register(
    'directory',
    DirectoryElement
)
