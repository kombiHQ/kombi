import os
from .. import Element, PathHolder

class FsElement(Element):
    """
    Abstracted file system Path.
    """

    def __init__(self, filePathOrPathHolder, parentElement=None):
        """
        Create a element (use the factory function Path.create instead).
        """
        if isinstance(filePathOrPathHolder, str):
            pathHolder = PathHolder(filePathOrPathHolder)
        else:
            pathHolder = filePathOrPathHolder

        super(FsElement, self).__init__(pathHolder.baseName(), parentElement)

        self.__setPathHolder(pathHolder)
        self.setVar('filePath', pathHolder.path())
        self.setVar('fullPath', pathHolder.path())
        self.setVar('ext', pathHolder.ext())
        self.setVar('baseName', pathHolder.baseName())
        self.setVar('name', os.path.splitext(pathHolder.baseName())[0])
        if 'sourceDirectory' not in self.varNames():
            path = pathHolder.path()
            if not pathHolder.isDirectory():
                path = os.path.dirname(path)
            self.setVar('sourceDirectory', path)

    def pathHolder(self):
        """
        Return the path holder object used to create the element.
        """
        return self.__pathHolder

    def globFromParent(self, filterTypes=[], useCache=True):
        """
        Return a list of all elements found recursively under the parent directory of the given path.

        Filter result list by exact element type (str) or class type (includes derived classes).
        """
        parentPath = os.path.dirname(self.var("filePath"))
        return FsElement.createFromPath(parentPath).glob(filterTypes, useCache)

    @classmethod
    def test(cls, data=None, parentElement=None):
        """
        Tests if the data is a path holder.
        """
        return isinstance(data, PathHolder)

    @staticmethod
    def createFromPath(fullPath, elementType=None, parentElement=None):
        """
        Create a element directly from a path string.
        """
        if elementType:
            elementClass = FsElement.registeredType(elementType)
            assert elementClass, "Invalid element type {} for {}".format(elementType, fullPath)

            result = elementClass(PathHolder(fullPath), parentElement)
            result.setVar('type', elementType)

            return result
        else:
            return FsElement.create(PathHolder(fullPath), parentElement)

    def __setPathHolder(self, pathHolder):
        """
        Set the path holder to the element.
        """
        assert isinstance(pathHolder, PathHolder), \
            "Invalid PathHolder type"

        self.__pathHolder = pathHolder
