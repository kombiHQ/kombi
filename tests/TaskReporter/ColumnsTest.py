import os
import io
import unittest
from fnmatch import fnmatch
from ..BaseTestCase import BaseTestCase
from chilopoda.Crawler.Fs import FsPath
from chilopoda.TaskHolderLoader import JsonLoader
from chilopoda.Dispatcher import Dispatcher
from chilopoda.Resource import Resource

class ColumnsTest(BaseTestCase):
    """Test for column task reporter."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'reporterTest.json')
    __taskPath = os.path.join(BaseTestCase.dataTestsDirectory(), 'tasks', 'EchoTask.py')
    __output = """
        echoTask\t\tnukeRender\t\t*/RND-TST-SHT_comp_compName_output_v010_tk.1001.exr
        echoTask\t\tshotRender\t\t*/RND-TST-SHT_lighting_beauty_sr.1001.exr
        echoTask\t\tturntable\t\t*/RND_ass_lookdev_default_beauty_tt.1001.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0001.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0002.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0003.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0004.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0005.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0006.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0007.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0008.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0009.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0010.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0011.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0012.exr
        echoTask\t\ttestCrawler\t\t*/test_0001.exr
        echoTask\t\tjpg\t\t\t*/testSeq.jpg
    """

    def testReport(self):
        """
        Test the output produced by the reporter.
        """
        resource = Resource.get()
        resource.load(self.__taskPath)

        taskHolderLoader = JsonLoader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        crawlers = FsPath.createFromPath(BaseTestCase.dataTestsDirectory()).glob()

        dispacher = Dispatcher.create('local')
        dispacher.setOption('defaultReporter', 'columns')
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
