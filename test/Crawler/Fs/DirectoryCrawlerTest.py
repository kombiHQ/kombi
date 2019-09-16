import os
import unittest
from ...BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs import DirectoryCrawler

class DirectoryCrawlerTest(BaseTestCase):
    """Test Directory crawler."""

    __dir = os.path.join(BaseTestCase.dataTestsDirectory(), "640x480")

    def testDirectoryCrawler(self):
        """
        Test that the Directory crawler test works properly.
        """
        crawler = Crawler.create(PathHolder(self.__dir))
        self.assertIsInstance(crawler, DirectoryCrawler)

    def testDirectoryVariables(self):
        """
        Test that the variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__dir))
        self.assertEqual(crawler.var("width"), 640)
        self.assertEqual(crawler.var("height"), 480)

    def testIsLeaf(self):
        """
        Test to show directory crawler is not a leaf.
        """
        crawler = Crawler.create(PathHolder(self.__dir))
        self.assertFalse(crawler.isLeaf())

    def testBadFile(self):
        """
        Test to show that file names with illegal characters are skipped.
        """
        crawler = Crawler.create(PathHolder(self.dataTestsDirectory()))
        crawlerPaths = map(lambda x: x.var("filePath"), crawler.children())
        self.assertNotIn(os.path.join(self.__dir, "bad file.txt"), crawlerPaths)


if __name__ == "__main__":
    unittest.main()
