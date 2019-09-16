import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Ascii import TxtCrawler

class TxtCrawlerTest(BaseTestCase):
    """Test Txt crawler."""

    __txtFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.txt")

    def testTxtCrawler(self):
        """
        Test that the Txt crawler test works properly.
        """
        crawler = Crawler.create(PathHolder(self.__txtFile))
        self.assertIsInstance(crawler, TxtCrawler)

    def testTxtVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__txtFile))
        self.assertEqual(crawler.var("type"), "txt")
        self.assertEqual(crawler.var("category"), "ascii")

    def testTxtContents(self):
        """
        Test that txt files are parsed properly.
        """
        crawler = Crawler.create(PathHolder(self.__txtFile))
        testData = "testing txt file\nwith random data\n\n1 2 3\n"
        self.assertEqual(crawler.contents(), testData)


if __name__ == "__main__":
    unittest.main()
