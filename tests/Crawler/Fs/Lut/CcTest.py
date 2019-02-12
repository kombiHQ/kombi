import os
import unittest
from ....BaseTestCase import BaseTestCase
from chilopoda.Crawler.Fs import FsPath
from chilopoda.PathHolder import PathHolder
from chilopoda.Crawler.Fs.Lut import Ccc

class CcTest(BaseTestCase):
    """Test Cc crawler."""

    __ccFile = os.path.join(BaseTestCase.dataDirectory(), "test.cc")

    def testCcCrawler(self):
        """
        Test that the Cc crawler test works properly.
        """
        crawler = FsPath.create(PathHolder(self.__ccFile))
        self.assertIsInstance(crawler, Ccc)

    def testCcVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = FsPath.create(PathHolder(self.__ccFile))
        self.assertEqual(crawler.var("type"), "cc")
        self.assertEqual(crawler.var("category"), "lut")
        self.assertEqual(crawler.var("slope"), [1.1, 1.2, 1.3])
        self.assertEqual(crawler.var("offset"), [0.1, 0.2, 0.3])
        self.assertEqual(crawler.var("power"), [1.4, 1.5, 1.6])
        self.assertEqual(crawler.var("saturation"), 1.0)


if __name__ == "__main__":
    unittest.main()
