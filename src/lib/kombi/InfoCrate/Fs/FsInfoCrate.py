import os
from .. import InfoCrate, PathHolder

class FsInfoCrate(InfoCrate):
    """
    Abstracted file system Path.
    """

    def __init__(self, filePathOrPathHolder, parentInfoCrate=None):
        """
        Create a infoCrate (use the factory function Path.create instead).
        """
        if isinstance(filePathOrPathHolder, str):
            pathHolder = PathHolder(filePathOrPathHolder)
        else:
            pathHolder = filePathOrPathHolder

        super(FsInfoCrate, self).__init__(pathHolder.baseName(), parentInfoCrate)

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
        Return the path holder object used to create the infoCrate.
        """
        return self.__pathHolder

    def globFromParent(self, filterTypes=[], useCache=True):
        """
        Return a list of all infoCrates found recursively under the parent directory of the given path.

        Filter result list by exact infoCrate type (str) or class type (includes derived classes).
        """
        parentPath = os.path.dirname(self.var("filePath"))
        return FsInfoCrate.createFromPath(parentPath).glob(filterTypes, useCache)

    @classmethod
    def test(cls, data=None, parentInfoCrate=None):
        """
        Tests if the data is a path holder.
        """
        return isinstance(data, PathHolder)

    @staticmethod
    def createFromPath(fullPath, infoCrateType=None, parentInfoCrate=None):
        """
        Create a infoCrate directly from a path string.
        """
        if infoCrateType:
            infoCrateClass = FsInfoCrate.registeredType(infoCrateType)
            assert infoCrateClass, "Invalid infoCrate type {} for {}".format(infoCrateType, fullPath)

            result = infoCrateClass(PathHolder(fullPath), parentInfoCrate)
            result.setVar('type', infoCrateType)

            return result
        else:
            return FsInfoCrate.create(PathHolder(fullPath), parentInfoCrate)

    def __setPathHolder(self, pathHolder):
        """
        Set the path holder to the infoCrate.
        """
        assert isinstance(pathHolder, PathHolder), \
            "Invalid PathHolder type"

        self.__pathHolder = pathHolder
