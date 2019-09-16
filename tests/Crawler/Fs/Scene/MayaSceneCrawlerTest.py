import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Scene import MayaSceneCrawler
from kombi.Crawler.Fs.Scene import SceneCrawler


class MayaSceneCrawlerTest(BaseTestCase):
    """Test Maya Scene crawler."""

    __maFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.ma")
    __mbFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.mb")

    def testMayaSceneCrawler(self):
        """
        Test that the Maya Scene crawler test works properly.
        """
        crawler = Crawler.create(PathHolder(self.__maFile))
        self.assertIsInstance(crawler, MayaSceneCrawler)
        crawler = Crawler.create(PathHolder(self.__mbFile))
        self.assertIsInstance(crawler, MayaSceneCrawler)

    def testMayaSceneVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__maFile))
        self.assertEqual(crawler.var("type"), "mayaScene")
        self.assertEqual(crawler.var("category"), "scene")

    def testMayaSceneExtensions(self):
        """
        Test that the list of extensions matching maya scenes is correct.
        """
        self.assertCountEqual(MayaSceneCrawler.extensions(), ["ma", "mb"])
        self.assertRaises(NotImplementedError, SceneCrawler.extensions)


if __name__ == "__main__":
    unittest.main()
