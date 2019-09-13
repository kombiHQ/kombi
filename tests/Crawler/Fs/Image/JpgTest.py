import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Image import Jpg

class JpgTest(BaseTestCase):
    """Test Jpg crawler."""

    __jpgFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.jpg")

    def testJpgCrawler(self):
        """
        Test that the Jpg crawler test works properly.
        """
        crawler = Crawler.create(PathHolder(self.__jpgFile))
        self.assertIsInstance(crawler, Jpg)

    def testJpgVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__jpgFile))
        self.assertEqual(crawler.var("type"), "jpg")
        self.assertEqual(crawler.var("category"), "image")
        self.assertEqual(crawler.var("imageType"), "single")
        self.assertEqual(crawler.var("width"), 512)
        self.assertEqual(crawler.var("height"), 512)


if __name__ == "__main__":
    unittest.main()
