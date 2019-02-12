import os
import unittest
from ....BaseTestCase import BaseTestCase
from chilopoda.Crawler.Fs import FsPath
from chilopoda.Crawler.Fs.Ascii import Xml

class XmlTest(BaseTestCase):
    """Test Xml crawler."""

    __xmlFile = os.path.join(BaseTestCase.dataDirectory(), "test.xml")

    def testXmlCrawler(self):
        """
        Test that the Xml crawler test works properly.
        """
        crawler = FsPath.createFromPath(self.__xmlFile)
        self.assertIsInstance(crawler, Xml)

    def testXmlVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = FsPath.createFromPath(self.__xmlFile)
        self.assertEqual(crawler.var("type"), "xml")
        self.assertEqual(crawler.var("category"), "ascii")

    def testXmlContents(self):
        """
        Test that txt files are parsed properly.
        """
        crawler = FsPath.createFromPath(self.__xmlFile)
        self.assertEqual(crawler.queryTag('testC')[0], "testing child C")
        self.assertEqual(crawler.queryTag('testD1')[0], "1 2 3")
        self.assertEqual(crawler.queryTag('{TestNamespace}testD1', ignoreNameSpace=False)[0], "1 2 3")
        self.assertEqual(crawler.queryTag('testB')[1]['id'], "123")


if __name__ == "__main__":
    unittest.main()
