import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.PathHolder import PathHolder
from kombi.Crawler.Fs.Scene import MayaScene
from kombi.Crawler.Fs.Scene import Scene


class MayaSceneTest(BaseTestCase):
    """Test Maya Scene crawler."""

    __maFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.ma")
    __mbFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.mb")

    def testMayaSceneCrawler(self):
        """
        Test that the Maya Scene crawler test works properly.
        """
        crawler = Crawler.create(PathHolder(self.__maFile))
        self.assertIsInstance(crawler, MayaScene)
        crawler = Crawler.create(PathHolder(self.__mbFile))
        self.assertIsInstance(crawler, MayaScene)

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
        self.assertCountEqual(MayaScene.extensions(), ["ma", "mb"])
        self.assertRaises(NotImplementedError, Scene.extensions)


if __name__ == "__main__":
    unittest.main()
