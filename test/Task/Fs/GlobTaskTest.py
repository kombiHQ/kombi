import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Template import Template
from kombi.Crawler.Fs import FsCrawler, DirectoryCrawler
from kombi.Crawler.Fs.Image import ExrCrawler
from kombi.Crawler.Fs.Ascii import JsonCrawler, TxtCrawler

class GlobTaskTest(BaseTestCase):
    """Test Glob task."""

    __globFiles = {
        'exr': [
            'RND-TST-SHT_comp_compName_output_v010_tk.1001.exr',
            'RND_ass_lookdev_default_beauty_tt.1001.exr',
            'RND-TST-SHT_lighting_beauty_sr.1001.exr'
        ],
        'json': [
            'test.json'
        ],
        'txt': [
            'test.txt'
        ],
        'directory': [
            'images'
        ]
    }

    def testGlobSpecficFiles(self):
        """
        Test that the glob task looking for specific exr files.
        """
        crawler = FsCrawler.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        globTask = Task.create('glob')
        globTask.add(
            crawler,
            Template("(dirname {filePath})/**/*.exr").valueFromCrawler(crawler)
        )
        result = globTask.output()
        self.assertEqual(len(result), len(self.__globFiles['exr']))

        for resultCrawler in result:
            self.assertIsInstance(resultCrawler, ExrCrawler)
            self.assertIn(resultCrawler.var('baseName'), self.__globFiles['exr'])

    def testGlobAll(self):
        """
        Test that the glob task find all files & directories.
        """
        crawler = FsCrawler.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        globTask = Task.create('glob')
        globTask.add(
            crawler,
            Template("(dirname {filePath})/**/*").valueFromCrawler(crawler)
        )
        result = globTask.output()
        self.assertEqual(
            len(result),
            len(self.__globFiles['exr']) + len(self.__globFiles['json']) + len(self.__globFiles['txt']) + len(self.__globFiles['directory'])
        )

        for resultCrawler in result:
            baseType = 'directory' if 'ext' not in resultCrawler.varNames() else resultCrawler.var('ext')
            if baseType == 'exr':
                CrawlerType = ExrCrawler
            elif baseType == 'json':
                CrawlerType = JsonCrawler
            elif baseType == 'txt':
                CrawlerType = TxtCrawler
            else:
                baseType = 'directory'
                CrawlerType = DirectoryCrawler

            self.assertIsInstance(resultCrawler, CrawlerType)
            self.assertIn(resultCrawler.var('baseName'), self.__globFiles[baseType])

    def testGlobSkipDuplicated(self):
        """
        Test that the glob task with the option skip duplicated enabled (default).
        """
        crawler1 = FsCrawler.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        crawler2 = FsCrawler.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "text.txt")
        )

        globTask = Task.create('glob')
        globTask.add(
            crawler1,
            Template("(dirname {filePath})/**/*.exr").valueFromCrawler(crawler1)
        )
        globTask.add(
            crawler2,
            Template("(dirname {filePath})/images/*.exr").valueFromCrawler(crawler2)
        )
        result = globTask.output()
        self.assertEqual(len(result), len(self.__globFiles['exr']))

        for resultCrawler in result:
            self.assertIsInstance(resultCrawler, ExrCrawler)
            self.assertIn(resultCrawler.var('baseName'), self.__globFiles['exr'])

    def testGlobDontSkipDuplicated(self):
        """
        Test that the glob task with he option skip duplicated disabled.
        """
        crawler1 = FsCrawler.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "test.json")
        )

        crawler2 = FsCrawler.createFromPath(
            os.path.join(BaseTestCase.dataTestsDirectory(), "glob", "text.txt")
        )

        globTask = Task.create('glob')
        globTask.setOption('skipDuplicated', False)

        globTask.add(
            crawler1,
            Template("(dirname {filePath})/**/*.exr").valueFromCrawler(crawler1)
        )
        globTask.add(
            crawler2,
            Template("(dirname {filePath})/images/*.exr").valueFromCrawler(crawler2)
        )

        result = globTask.output()
        self.assertEqual(len(result), len(self.__globFiles['exr']) * 2)

        for resultCrawler in result:
            self.assertIsInstance(resultCrawler, ExrCrawler)
            self.assertIn(resultCrawler.var('baseName'), self.__globFiles['exr'])


if __name__ == "__main__":
    unittest.main()
