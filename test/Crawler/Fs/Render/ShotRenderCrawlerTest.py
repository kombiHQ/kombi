import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Render import ShotRenderCrawler

class ShotRenderCrawlerTest(BaseTestCase):
    """Test ShotRenderCrawler crawler."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "RND-TST-SHT_lighting_beauty_sr.1001.exr")

    def testShotRenderCrawler(self):
        """
        Test that the ShotRenderCrawler crawler test works properly.
        """
        crawler = Crawler.create(PathHolder(self.__exrFile))
        self.assertIsInstance(crawler, ShotRenderCrawler)

    def testShotRenderCrawlerVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__exrFile))
        self.assertEqual(crawler.var("type"), "shotRender")
        self.assertEqual(crawler.var("category"), "render")
        self.assertEqual(crawler.var("renderType"), "sr")
        self.assertEqual(crawler.var("seq"), "TST")
        self.assertEqual(crawler.var("shot"), "RND-TST-SHT")
        self.assertEqual(crawler.var("step"), "lighting")
        self.assertEqual(crawler.var("pass"), "beauty")
        self.assertEqual(crawler.var("renderName"), "lighting-beauty")


if __name__ == "__main__":
    unittest.main()
