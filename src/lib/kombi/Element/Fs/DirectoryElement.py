import os
import re
from .FsElement import FsElement
from .. import Element, PathHolder

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

        # setting icon
        self.setTag('icon', 'icons/elements/children.png')

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

    @classmethod
    def test(cls, pathHolder, parentElement):
        """
        Test if the path holder contains a directory.
        """
        if not super(DirectoryElement, cls).test(pathHolder, parentElement):
            return False
        return pathHolder.isDirectory()

    def _computeChildren(self):
        """
        Return the directory contents.
        """
        result = []
        currentPath = self.pathHolder().path()
        for childFile in os.listdir(currentPath):
            childPathHolder = PathHolder(os.path.join(currentPath, childFile))
            childElement = Element.create(childPathHolder, self)
            result.append(childElement)

        def __sortElement(x):
            name = x.var('name').lower() if 'group' not in x.tagNames() else x.tag('group').lower()
            # in case of a version folder v#### we want to sort the recent versions on top
            if not x.isLeaf() and name.lower().startswith('v') and name[1:].isdigit():
                totalDigits = len(name[1:])
                name = name[:1] + str(int('9' * totalDigits) - int(name[1:])).zfill(totalDigits)

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
