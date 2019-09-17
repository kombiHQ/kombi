import os
import re
from .FsCrawler import FsCrawler
from .. import Crawler, PathHolder

class DirectoryCrawler(FsCrawler):
    """
    Directory crawler.
    """

    # checking for digits as prefix separated by x or X and finishing with digits as suffix
    __resolutionRegex = r'^[0-9]+[x|X][0-9]+$'
    __ignoreWidth = 320
    __ignoreHeight = 240

    def __init__(self, *args, **kwargs):
        """
        Create a directory crawler.
        """
        super(DirectoryCrawler, self).__init__(*args, **kwargs)

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
        Return a boolean telling if the crawler is leaf.
        """
        return False

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a directory.
        """
        if not super(DirectoryCrawler, cls).test(pathHolder, parentCrawler):
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
            childCrawler = Crawler.create(childPathHolder, self)
            result.append(childCrawler)

        return result


# registration
Crawler.register(
    'directory',
    DirectoryCrawler
)
