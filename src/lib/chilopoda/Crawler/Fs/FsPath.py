import os
from ..Crawler import Crawler
from ...PathHolder import PathHolder

# compatibility with python 2/3
try:
    basestring
except NameError:
    basestring = str

class FsPath(Crawler):
    """
    Abstracted file system Path.
    """

    def __init__(self, filePathOrPathHolder, parentCrawler=None):
        """
        Create a crawler (use the factory function Path.create instead).
        """
        if isinstance(filePathOrPathHolder, basestring):
            pathHolder = PathHolder(filePathOrPathHolder)
        else:
            pathHolder = filePathOrPathHolder

        super(FsPath, self).__init__(pathHolder.baseName(), parentCrawler)

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
        Return the path holder object used to create the crawler.
        """
        return self.__pathHolder

    def globFromParent(self, filterTypes=[], useCache=True):
        """
        Return a list of all crawlers found recursively under the parent directory of the given path.

        Filter result list by exact crawler type (str) or class type (includes derived classes).
        """
        parentPath = os.path.dirname(self.var("filePath"))
        return FsPath.createFromPath(parentPath).glob(filterTypes, useCache)

    @classmethod
    def test(cls, data=None, parentCrawler=None):
        """
        Tests if the data is a path holder.
        """
        return isinstance(data, PathHolder)

    @staticmethod
    def createFromPath(fullPath, crawlerType=None, parentCrawler=None):
        """
        Create a crawler directly from a path string.
        """
        if crawlerType:
            crawlerClass = FsPath.registeredType(crawlerType)
            assert crawlerClass, "Invalid crawler type {} for {}".format(crawlerType, fullPath)

            result = crawlerClass(PathHolder(fullPath), parentCrawler)
            result.setVar('type', crawlerType)

            return result
        else:
            return FsPath.create(PathHolder(fullPath), parentCrawler)

    def __setPathHolder(self, pathHolder):
        """
        Set the path holder to the crawler.
        """
        assert isinstance(pathHolder, PathHolder), \
            "Invalid PathHolder type"

        self.__pathHolder = pathHolder
