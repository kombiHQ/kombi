import os
import unittest
from ....BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Ascii import JsonCrawler

class JsonCrawlerTest(BaseTestCase):
    """Test Json crawler."""

    __jsonFile = os.path.join(BaseTestCase.dataTestsDirectory(), "test.json")

    def testJsonCrawler(self):
        """
        Test that the Json crawler test works properly.
        """
        crawler = Crawler.create(PathHolder(self.__jsonFile))
        self.assertIsInstance(crawler, JsonCrawler)

    def testJsonVariables(self):
        """
        Test that variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__jsonFile))
        self.assertEqual(crawler.var("type"), "json")
        self.assertEqual(crawler.var("category"), "ascii")

    def testJsonContents(self):
        """
        Test that json files are parsed properly.
        """
        crawler = Crawler.create(PathHolder(self.__jsonFile))
        testData = {
            "testList": [1, 1.2, "value"],
            "testDict": {"key": "value", "number": 1},
            "testString": "blah"
        }
        self.assertEqual(crawler.contents(), testData)


if __name__ == "__main__":
    unittest.main()
