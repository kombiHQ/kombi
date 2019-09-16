import os
import unittest
import glob
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Image import ExrCrawler

class ExrCrawlerTest(BaseTestCase):
    """Test Exr crawler."""

    __exrFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __exrSeq = os.path.join(BaseTestCase.dataTestsDirectory(), "testSeq.0001.exr")
    __exrAmbiguousSeq = os.path.join(BaseTestCase.dataTestsDirectory(), "test_0001.exr")

    def testExrCrawler(self):
        """
        Test that the Exr crawler test works properly.
        """
        crawler = Crawler.create(PathHolder(self.__exrFile))
        self.assertIsInstance(crawler, ExrCrawler)
        crawler = Crawler.create(PathHolder(BaseTestCase.dataTestsDirectory()))
        self.assertNotIsInstance(crawler, ExrCrawler)

    def testExrVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__exrFile))
        self.assertEqual(crawler.var("type"), "exr")
        self.assertEqual(crawler.var("category"), "image")
        self.assertEqual(crawler.var("imageType"), "single")

    def testExrWidthHeight(self):
        """
        Test that width and height variables are processed properly.
        """
        crawler = Crawler.create(PathHolder(self.__exrFile))
        self.assertNotIn("width", crawler.varNames())
        self.assertNotIn("height", crawler.varNames())
        self.assertEqual(crawler.var("width"), 1920)
        self.assertEqual(crawler.var("height"), 1080)

    def testImageSequence(self):
        """
        Test that detection of an image sequence works properly.
        """
        crawler = Crawler.create(PathHolder(self.__exrFile))
        self.assertFalse(crawler.isSequence())
        crawler = Crawler.create(PathHolder(self.__exrSeq))
        self.assertTrue(crawler.isSequence())
        crawler = Crawler.create(PathHolder(self.__exrAmbiguousSeq))
        self.assertTrue(crawler.isSequence())

    def testImageSequenceVariables(self):
        """
        Test that the image sequence related variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__exrSeq))
        self.assertEqual(crawler.var("imageType"), "sequence")
        self.assertEqual(crawler.var("name"), "testSeq")
        self.assertEqual(crawler.var("frame"), 1)
        self.assertEqual(crawler.var("padding"), 4)
        crawler = Crawler.create(PathHolder(self.__exrAmbiguousSeq))
        self.assertEqual(crawler.var("imageType"), "sequence")
        self.assertEqual(crawler.var("name"), "test")
        self.assertEqual(crawler.var("frame"), 1)
        self.assertEqual(crawler.var("padding"), 4)

    def testImageSequenceGroup(self):
        """
        Test that an image sequence is grouped properly.
        """
        paths = glob.glob("{}/testSeq.*.exr".format(self.dataTestsDirectory()))
        crawlers = list(map(lambda x: Crawler.create(PathHolder(x)), paths))
        crawlers.append(Crawler.create(PathHolder(self.__exrFile)))
        grouped = ExrCrawler.group(crawlers)
        self.assertEqual(len(grouped), 2)
        self.assertEqual(len(grouped[0]), len(paths))
        self.assertEqual(len(grouped[1]), 1)
        groupedPaths = list(map(lambda x: x.var("filePath"), grouped[0]))
        self.assertEqual(groupedPaths, sorted(paths))
        self.assertEqual(grouped[1][0].var("filePath"), self.__exrFile)
        reversedGrouped = ExrCrawler.sortGroup(grouped, lambda x: x.var('filePath'), True)
        reversedPaths = list(map(lambda x: x.var("filePath"), reversedGrouped[0]))
        self.assertEqual(reversedPaths, sorted(paths, reverse=True))


if __name__ == "__main__":
    unittest.main()
