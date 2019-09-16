import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler.Fs import FsCrawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Lut import CccCrawler

class CccCrawlerTest(BaseTestCase):
    """Test Ccc crawler."""

    __cccFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.ccc")

    def testCccCrawler(self):
        """
        Test that the Ccc crawler test works properly.
        """
        crawler = FsCrawler.create(PathHolder(self.__cccFile))
        self.assertIsInstance(crawler, CccCrawler)

    def testCccVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = FsCrawler.create(PathHolder(self.__cccFile))
        self.assertEqual(crawler.var("type"), "cc")
        self.assertEqual(crawler.var("category"), "lut")
        self.assertEqual(crawler.var("slope"), [1.1, 1.2, 1.3])
        self.assertEqual(crawler.var("offset"), [0.1, 0.2, 0.3])
        self.assertEqual(crawler.var("power"), [1.4, 1.5, 1.6])
        self.assertEqual(crawler.var("saturation"), 1.0)


if __name__ == "__main__":
    unittest.main()
