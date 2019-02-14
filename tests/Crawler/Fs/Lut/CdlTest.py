import os
import unittest
from ....BaseTestCase import BaseTestCase
from chilopoda.Crawler.Fs import FsPath
from chilopoda.PathHolder import PathHolder
from chilopoda.Crawler.Fs.Lut import Cdl

class CdlTest(BaseTestCase):
    """Test Cdl crawler."""

    __cdlFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.cdl")

    def testCdlCrawler(self):
        """
        Test that the Cdl crawler test works properly.
        """
        crawler = FsPath.create(PathHolder(self.__cdlFile))
        self.assertIsInstance(crawler, Cdl)

    def testCdlVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = FsPath.create(PathHolder(self.__cdlFile))
        self.assertEqual(crawler.var("type"), "cdl")
        self.assertEqual(crawler.var("category"), "lut")
        self.assertEqual(crawler.var("slope"), [1.014, 1.0104, 0.62])
        self.assertEqual(crawler.var("offset"), [-0.00315, -0.00124, 0.3103])
        self.assertEqual(crawler.var("power"), [1.0, 0.9983, 1.0])
        self.assertEqual(crawler.var("saturation"), 1.09)


if __name__ == "__main__":
    unittest.main()
