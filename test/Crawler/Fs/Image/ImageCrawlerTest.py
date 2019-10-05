import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.Fs.Image import ImageCrawler
from kombi.Crawler.PathHolder import PathHolder

class ImageCrawlerTest(BaseTestCase):
    """Test Image crawler."""

    __singleFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.dpx")
    __sequenceFile = os.path.join(BaseTestCase.dataTestsDirectory(), "testSeq.0001.exr")

    def testSingleImage(self):
        """
        Test that the crawler created for a single image is based on the image crawler.
        """
        crawler = Crawler.create(PathHolder(self.__singleFile))
        self.assertIsInstance(crawler, ImageCrawler)

    def testSequenceImage(self):
        """
        Test that the crawler created for a sequence image is based on the image crawler.
        """
        crawler = Crawler.create(PathHolder(self.__sequenceFile))
        self.assertIsInstance(crawler, ImageCrawler)

    def testGroupTagSequence(self):
        """
        Test that the tag group has been assigned to the image sequence crawler.
        """
        crawler = Crawler.create(PathHolder(self.__sequenceFile))

        self.assertIn('group', crawler.tagNames())
        self.assertEqual(crawler.tag('group'), "testSeq.####.exr")

    def testGroupSprintfTagSequence(self):
        """
        Test that the tag groupSprintf has been assigned to the image sequence crawler.
        """
        crawler = Crawler.create(PathHolder(self.__sequenceFile))
        self.assertIn('groupSprintf', crawler.tagNames())
        self.assertEqual(crawler.tag('groupSprintf'), "testSeq.%04d.exr")

    def testGroupTagSingle(self):
        """
        Test that the tag group has not been assigned to a single image crawler.
        """
        crawler = Crawler.create(PathHolder(self.__singleFile))
        self.assertNotIn('group', crawler.tagNames())

    def testGroupSprintfTagSingle(self):
        """
        Test that the tag groupSprintf has not been assigned to a single image crawler.
        """
        crawler = Crawler.create(PathHolder(self.__singleFile))
        self.assertNotIn('groupSprintf', crawler.tagNames())

    def testIsSequence(self):
        """
        Test if a crawler is a sequence.
        """
        singleCrawler = Crawler.create(PathHolder(self.__singleFile))
        sequenceCrawler = Crawler.create(PathHolder(self.__sequenceFile))

        self.assertEqual(singleCrawler.isSequence(), False)
        self.assertEqual(singleCrawler.var("imageType"), "single")
        self.assertEqual(sequenceCrawler.isSequence(), True)
        self.assertEqual(sequenceCrawler.var("imageType"), "sequence")


if __name__ == "__main__":
    unittest.main()
