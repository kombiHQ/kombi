import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler.Fs import FsCrawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Lut import CccCrawler

class CcCrawlerTest(BaseTestCase):
    """Test Cc crawler."""

    __ccFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.cc")

    def testCcCrawler(self):
        """
        Test that the Cc crawler test works properly.
        """
        crawler = FsCrawler.create(PathHolder(self.__ccFile))
        self.assertIsInstance(crawler, CccCrawler)

    def testCcVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = FsCrawler.create(PathHolder(self.__ccFile))
        self.assertEqual(crawler.var("type"), "cc")
        self.assertEqual(crawler.var("category"), "lut")
        self.assertEqual(crawler.var("slope"), [1.1, 1.2, 1.3])
        self.assertEqual(crawler.var("offset"), [0.1, 0.2, 0.3])
        self.assertEqual(crawler.var("power"), [1.4, 1.5, 1.6])
        self.assertEqual(crawler.var("saturation"), 1.0)


if __name__ == "__main__":
    unittest.main()
