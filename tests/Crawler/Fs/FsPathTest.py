import os
import unittest
from ...BaseTestCase import BaseTestCase
from kombi.Crawler import Crawler
from kombi.Crawler.Fs import FsPath
from kombi.Crawler.Fs import File
from kombi.Crawler.PathHolder import PathHolder
from kombi.Crawler.Fs.Render import ExrRender
from kombi.Crawler.Fs.Image import Exr
from kombi.Crawler.Crawler import CrawlerInvalidVarError
from kombi.Crawler.Crawler import CrawlerInvalidTagError

class FsPathTest(BaseTestCase):
    """Test Directory crawler."""

    __dir = os.path.join(BaseTestCase.dataTestsDirectory(), "glob")
    __turntableFile = os.path.join(__dir, "images", "RND_ass_lookdev_default_beauty_tt.1001.exr")
    __shotRenderFile = os.path.join(__dir, "images", "RND-TST-SHT_lighting_beauty_sr.1001.exr")

    def testFsCrawler(self):
        """
        Test that the fs crawler test works.
        """
        pathHolder = PathHolder(self.__dir)
        self.assertTrue(FsPath.test(pathHolder, None))

        notAPathHolder = {}
        self.assertFalse(FsPath.test(notAPathHolder, None))

    def testFsPathGlob(self):
        """
        Test the glob functionality.
        """
        crawler = Crawler.create(PathHolder(self.__dir))
        crawlers = crawler.glob()
        result = self.collectFiles(self.__dir)
        result = list(map(lambda x: x.rstrip("/"), result))
        crawlerPaths = list(map(lambda x: x.var("filePath"), crawlers))
        self.assertCountEqual(result, crawlerPaths)

        crawlers = crawler.glob(filterTypes=["turntable", "shotRender"])
        crawlerPaths = list(map(lambda x: x.var("filePath"), crawlers))
        self.assertCountEqual(crawlerPaths, [self.__turntableFile, self.__shotRenderFile])

        crawlers = crawler.glob(filterTypes=[ExrRender])
        crawlerPaths = list(map(lambda x: x.var("filePath"), crawlers))
        result = self.collectFiles(self.__dir, "RND*.exr")
        result = list(map(lambda x: x.rstrip("/"), result))
        self.assertCountEqual(result, crawlerPaths)

        crawlers = crawler.glob(filterTypes=['exr'])
        crawlerPaths = list(map(lambda x: x.var("filePath"), crawlers))
        result = self.collectFiles(self.__dir, "*.exr")
        result = list(map(lambda x: x.rstrip("/"), result))
        self.assertCountEqual(result, crawlerPaths)

        crawler = Crawler.create(PathHolder(self.__turntableFile))
        otherCrawlers = crawler.globFromParent(filterTypes=[ExrRender])
        crawlerPaths = list(map(lambda x: x.var("filePath"), crawlers))
        otherCrawlerPaths = list(map(lambda x: x.var("filePath"), otherCrawlers))
        self.assertCountEqual(crawlerPaths, otherCrawlerPaths)

    def testPathVariables(self):
        """
        Test that the crawler variables are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__turntableFile))
        name, ext = os.path.splitext(self.__turntableFile)
        self.assertEqual(crawler.var('filePath'), self.__turntableFile)
        self.assertEqual(crawler.var('ext'), ext.lstrip("."))
        self.assertEqual(crawler.var('baseName'), os.path.basename(self.__turntableFile))
        self.assertEqual(crawler.var('name'), os.path.basename(name).split(".")[0])
        self.assertEqual(crawler.var('sourceDirectory'), os.path.dirname(name))
        self.assertRaises(CrawlerInvalidVarError, crawler.var, "dummyVar")

    def testCrawlerTags(self):
        """
        Test that the Crawler tags are set properly.
        """
        crawler = Crawler.create(PathHolder(self.__turntableFile))
        self.assertRaises(CrawlerInvalidTagError, crawler.tag, "dummyTag")

    def testCrawlerRegistration(self):
        """
        Test that you can register a new crawler.
        """
        class DummyCrawler(File):
            @classmethod
            def test(cls, pathHolder, parentCrawler):
                return False

        Crawler.register("dummy", DummyCrawler)
        self.assertIn("dummy", Crawler.registeredNames())
        self.assertIn(DummyCrawler, Crawler.registeredSubclasses("file"))
        self.assertIn(DummyCrawler, Crawler.registeredSubclasses(FsPath))

    def testCrawlerClone(self):
        """
        Test that cloning crawlers works.
        """
        crawler = Crawler.create(PathHolder(self.__turntableFile))
        clone = crawler.clone()
        self.assertCountEqual(crawler.varNames(), clone.varNames())
        self.assertCountEqual(crawler.contextVarNames(), clone.contextVarNames())
        self.assertCountEqual(crawler.tagNames(), clone.tagNames())

    def testCrawlerJson(self):
        """
        Test that you can convert a crawler to json and back.
        """
        crawler = Crawler.create(PathHolder(self.__turntableFile))
        jsonResult = crawler.toJson()
        crawlerResult = Crawler.createFromJson(jsonResult)
        self.assertCountEqual(crawler.varNames(), crawlerResult.varNames())
        self.assertCountEqual(crawler.contextVarNames(), crawlerResult.contextVarNames())
        self.assertCountEqual(crawler.tagNames(), crawlerResult.tagNames())

    def testCrawlerCreate(self):
        """
        Test that you can create a crawler with a specific type.
        """
        crawler = FsPath.createFromPath(self.__turntableFile, "exr")
        self.assertIsInstance(crawler, Exr)

    def testPathHolder(self):
        """
        Test PathHolder functions.
        """
        pathHolder = PathHolder(self.__turntableFile)
        self.assertEqual(pathHolder.size(), 5430903)
        self.assertEqual(pathHolder.name(), "RND_ass_lookdev_default_beauty_tt.1001")
        self.assertTrue(pathHolder.exists())
        pathHolder = PathHolder("/")
        self.assertEqual(pathHolder.baseName(), os.sep)


if __name__ == "__main__":
    unittest.main()
