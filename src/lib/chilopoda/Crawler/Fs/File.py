from .FsPath import FsPath
from ..Crawler import Crawler

class File(FsPath):
    """
    File crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a file.
        """
        if not super(File, cls).test(pathHolder, parentCrawler):
            return False
        return pathHolder.isFile()


Crawler.register(
    'file',
    File
)
