import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Render import NukeRender

class NukeRenderTest(BaseTestCase):
    """Test NukeRender crawler."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "RND-TST-SHT_comp_compName_output_v010_tk.1001.exr")

    def testNukeRenderCrawler(self):
        """
        Test that the NukeRender crawler test works properly.
        """
        crawler = Crawler.create(PathHolder(self.__exrFile))
        self.assertIsInstance(crawler, NukeRender)

    def testNukeRenderVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__exrFile))
        self.assertEqual(crawler.var("type"), "nukeRender")
        self.assertEqual(crawler.var("category"), "render")
        self.assertEqual(crawler.var("renderType"), "tk")
        self.assertEqual(crawler.var("seq"), "TST")
        self.assertEqual(crawler.var("shot"), "RND-TST-SHT")
        self.assertEqual(crawler.var("step"), "comp")
        self.assertEqual(crawler.var("renderName"), "compName")
        self.assertEqual(crawler.var("output"), "output")
        self.assertEqual(crawler.var("versionName"), "v010")
        self.assertEqual(crawler.var("version"), 10)


if __name__ == "__main__":
    unittest.main()
