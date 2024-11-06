import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Texture import TextureCrawler

class TextureCrawlerTest(BaseTestCase):
    """Test Texture crawler."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test_DIFF_u1_v1.exr")
    __tifFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test_bump_1002.tif")
    __badExrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test_0001.exr")

    def testTextureCrawler(self):
        """
        Test that the Texture crawler test works properly.
        """
        crawler = Crawler.registeredType('texture')(PathHolder(self.__exrFile))
        self.assertIsInstance(crawler, TextureCrawler)
        crawler = Crawler.registeredType('texture')(PathHolder(self.__tifFile))
        self.assertIsInstance(crawler, TextureCrawler)
        self.assertFalse(Crawler.registeredType('texture').test(PathHolder(self.__badExrFile), None, enable=True))

    def testTextureVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = Crawler.registeredType('texture')(PathHolder(self.__exrFile))
        self.assertTrue(crawler.test(crawler.pathHolder(), None, enable=True))
        self.assertEqual(crawler.var("category"), "texture")
        self.assertEqual(crawler.var("assetName"), "test")
        self.assertEqual(crawler.var("mapType"), "DIFF")
        self.assertEqual(crawler.var("udim"), 1001)
        self.assertEqual(crawler.var("variant"), "default")

        crawler = Crawler.registeredType('texture')(PathHolder(self.__tifFile))
        self.assertTrue(crawler.test(crawler.pathHolder(), None, enable=True))
        self.assertEqual(crawler.var("assetName"), "test")
        self.assertEqual(crawler.var("mapType"), "BUMP")
        self.assertEqual(crawler.var("udim"), 1002)
        self.assertEqual(crawler.var("variant"), "default")

    def testTextureTags(self):
        """
        Test that the tags are set properly.
        """
        crawler = Crawler.registeredType('texture')(PathHolder(self.__exrFile))
        self.assertEqual(crawler.tag("group"), "test-default")


if __name__ == "__main__":
    unittest.main()
