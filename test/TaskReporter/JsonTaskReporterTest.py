import os
import io
import unittest
from fnmatch import fnmatch
from ..BaseTestCase import BaseTestCase
from kombi.Crawler.Fs import FsCrawler
from kombi.TaskHolder.Loader import JsonLoader
from kombi.TaskHolder.Dispatcher import Dispatcher
from kombi.Resource import Resource

class JsonTaskReporterTest(BaseTestCase):
    """Test for json task reporter."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'reporterTest.json')
    __taskPath = os.path.join(BaseTestCase.dataTestsDirectory(), 'tasks', 'EchoTask.py')
    __output = """
        {
            "crawlers": [
                {
                    "crawlerType": "nukeRender",
                    "fullPath": "*/RND-TST-SHT_comp_compName_output_v010_tk.1001.exr"
                },
                {
                    "crawlerType": "shotRender",
                    "fullPath": "*/RND-TST-SHT_lighting_beauty_sr.1001.exr"
                },
                {
                    "crawlerType": "turntable",
                    "fullPath": "*/RND_ass_lookdev_default_beauty_tt.1001.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0001.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0002.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0003.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0004.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0005.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0006.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0007.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0008.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0009.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0010.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0011.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/testSeq.0012.exr"
                },
                {
                    "crawlerType": "testCrawler",
                    "fullPath": "*/test_0001.exr"
                }
            ],
            "execution": *,
            "task": "echoTask"
        }
        {
            "crawlers": [
                {
                    "crawlerType": "jpg",
                    "fullPath": "*/testSeq.jpg"
                }
            ],
            "execution": *,
            "task": "echoTask"
        }
    """

    def testReport(self):
        """
        Test the output produced by the reporter.
        """
        resource = Resource.get()
        resource.load(self.__taskPath)

        taskHolderLoader = JsonLoader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        crawlers = FsCrawler.createFromPath(BaseTestCase.dataTestsDirectory()).glob()

        dispacher = Dispatcher.create('local')
        dispacher.setOption('defaultReporter', 'json')
        outputStream = io.StringIO()
        dispacher.setStdout(outputStream)
        dispacher.setOption(
            'enableVerboseOutput',
            False
        )

        dispacher.setOption(
            'awaitExecution',
            True
        )

        for taskHolder in taskHolderLoader.taskHolders():
            dispacher.dispatch(taskHolder, crawlers)

        output = outputStream.getvalue().replace('\r\n', '\n').split('\n')
        prefixSize = None
        for index, line in enumerate(self.__output.split('\n')[1:-1]):
            if prefixSize is None:
                prefixSize = len(line) - len(line.lstrip())

            line = line[prefixSize:]
            outputLine = output[index].replace('\\', '/')
            if not fnmatch(outputLine, line):
                self.assertEqual(outputLine, line)


if __name__ == "__main__":
    unittest.main()
