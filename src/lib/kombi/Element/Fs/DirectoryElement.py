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
    def test(cls, path, parentElement):
        """
        Test if the path contains a directory.
        """
        if not super(DirectoryElement, cls).test(path, parentElement):
            return False
        return path.is_dir()

    def _computeChildren(self):
        """
        Return the directory contents.
        """
        result = []
        currentPath = str(self.path())
        for childFile in os.listdir(currentPath):
            childPath = pathlib.Path(os.path.join(currentPath, childFile))
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
