import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Render import TurntableCrawler

class TurntableCrawlerTest(BaseTestCase):
    """Test turntable crawler."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "RND_ass_lookdev_default_beauty_tt.1001.exr")

    def testTurntableCrawler(self):
        """
        Test that the turntable crawler test works properly.
        """
        crawler = Crawler.create(PathHolder(self.__exrFile))
        self.assertIsInstance(crawler, TurntableCrawler)

    def testTurntableCrawlerVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__exrFile))
        self.assertEqual(crawler.var("type"), "turntable")
        self.assertEqual(crawler.var("category"), "render")
        self.assertEqual(crawler.var("renderType"), "tt")
        self.assertEqual(crawler.var("assetName"), "ass")
        self.assertEqual(crawler.var("step"), "lookdev")
        self.assertEqual(crawler.var("pass"), "beauty")
        self.assertEqual(crawler.var("renderName"), "ass-default-beauty")


if __name__ == "__main__":
    unittest.main()
