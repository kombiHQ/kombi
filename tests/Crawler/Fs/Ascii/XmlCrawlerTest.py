import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler.Fs import FsPathCrawler
from kombi.Crawler.Fs.Ascii import XmlCrawler

class XmlCrawlerTest(BaseTestCase):
    """Test Xml crawler."""

    __xmlFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.xml")

    def testXmlCrawler(self):
        """
        Test that the Xml crawler test works properly.
        """
        crawler = FsPathCrawler.createFromPath(self.__xmlFile)
        self.assertIsInstance(crawler, XmlCrawler)

    def testXmlVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = FsPathCrawler.createFromPath(self.__xmlFile)
        self.assertEqual(crawler.var("type"), "xml")
        self.assertEqual(crawler.var("category"), "ascii")

    def testXmlContents(self):
        """
        Test that txt files are parsed properly.
        """
        crawler = FsPathCrawler.createFromPath(self.__xmlFile)
        self.assertEqual(crawler.queryTag('testC')[0], "testing child C")
        self.assertEqual(crawler.queryTag('testD1')[0], "1 2 3")
        self.assertEqual(crawler.queryTag('{TestNamespace}testD1', ignoreNameSpace=False)[0], "1 2 3")
        self.assertEqual(crawler.queryTag('testB')[1]['id'], "123")


if __name__ == "__main__":
    unittest.main()
