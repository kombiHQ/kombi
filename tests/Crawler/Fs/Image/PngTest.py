import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.PathHolder import PathHolder
from kombi.Crawler.Fs.Image import Png

class PngTest(BaseTestCase):
    """Test Exr crawler."""

    __pngFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.png")

    def testPngCrawler(self):
        """
        Test that the Png crawler test works properly.
        """
        crawler = Crawler.create(PathHolder(self.__pngFile))
        self.assertIsInstance(crawler, Png)

    def testPngVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__pngFile))
        self.assertEqual(crawler.var("type"), "png")
        self.assertEqual(crawler.var("category"), "image")
        self.assertEqual(crawler.var("imageType"), "single")
        # Current version of Oiio doesn't work with png.
        # Skipping this test for now.
        # self.assertEqual(crawler.var("width"), 640)
        # self.assertEqual(crawler.var("height"), 480)


if __name__ == "__main__":
    unittest.main()
