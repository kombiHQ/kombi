from .FsPathCrawler import FsPathCrawler
from ..Crawler import Crawler

class FileCrawler(FsPathCrawler):
    """
    File crawler.
    """

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a file.
        """
        if not super(FileCrawler, cls).test(pathHolder, parentCrawler):
            return False
        return pathHolder.isFile()


Crawler.register(
    'file',
    FileCrawler
)
