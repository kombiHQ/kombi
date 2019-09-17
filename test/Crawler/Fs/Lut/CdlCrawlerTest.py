import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler.Fs import FsCrawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Lut import CdlCrawler

class CdlCrawlerTest(BaseTestCase):
    """Test Cdl crawler."""

    __cdlFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.cdl")

    def testCdlCrawler(self):
        """
        Test that the Cdl crawler test works properly.
        """
        crawler = FsCrawler.create(PathHolder(self.__cdlFile))
        self.assertIsInstance(crawler, CdlCrawler)

    def testCdlVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = FsCrawler.create(PathHolder(self.__cdlFile))
        self.assertEqual(crawler.var("type"), "cdl")
        self.assertEqual(crawler.var("category"), "lut")
        self.assertEqual(crawler.var("slope"), [1.014, 1.0104, 0.62])
        self.assertEqual(crawler.var("offset"), [-0.00315, -0.00124, 0.3103])
        self.assertEqual(crawler.var("power"), [1.0, 0.9983, 1.0])
        self.assertEqual(crawler.var("saturation"), 1.09)


if __name__ == "__main__":
    unittest.main()
