import os
from pathlib import Path
from .. import Element

class FsElement(Element):
    """
    Abstracted file system Path.
    """

    def __init__(self, pathStrOrPath, parentElement=None):
        """
        Create a element (use the factory function Path.create instead).
        """
        if isinstance(pathStrOrPath, str):
            path = Path(pathStrOrPath)
        else:
            path = pathStrOrPath

        super(FsElement, self).__init__(path.name, parentElement)

        self.__setPath(path)
        self.setVar('filePath', str(path))
        self.setVar('fullPath', self.var('filePath'))
        self.setVar('ext', path.suffix[1:])
        self.setVar('baseName', path.name)
        self.setVar('name', self.var('baseName'))
        if 'sourceDirectory' not in self.varNames():
            if not path.is_dir():
                self.setVar('sourceDirectory', str(path.parent))

    def path(self):
        """
        Return the path object used to create the element.
        """
        return self.__path

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
        Tests if the data is a Path from pathlib.
        """
        return isinstance(data, Path)

    @staticmethod
    def createFromPath(fullPath, elementType=None, parentElement=None):
        """
        Create a element directly from a path string.
        """
        if elementType:
            elementClass = FsElement.registeredType(elementType)
            assert elementClass, "Invalid element type {} for {}".format(elementType, fullPath)

            result = elementClass(Path(fullPath), parentElement)
            result.setVar('type', elementType)

            return result
        else:
            return FsElement.create(Path(fullPath), parentElement)

    def __setPath(self, path):
        """
        Set the path to the element.
        """
        assert isinstance(path, Path), \
            "Invalid Path type"

        self.__path = path
