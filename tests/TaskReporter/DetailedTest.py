import os
import io
import unittest
from fnmatch import fnmatch
from ..BaseTestCase import BaseTestCase
from chilopoda.Crawler.Fs import FsPath
from chilopoda.TaskHolderLoader import JsonLoader
from chilopoda.Dispatcher import Dispatcher
from chilopoda.Resource import Resource

class DetailedTest(BaseTestCase):
    """Test for detailed task reporter."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'reporterTest.json')
    __taskPath = os.path.join(BaseTestCase.dataTestsDirectory(), 'tasks', 'EchoTask.py')
    __output = """
        echoTask output (execution * seconds):
          - nukeRender(*/RND-TST-SHT_comp_compName_output_v010_tk.1001.exr)
          - shotRender(*/RND-TST-SHT_lighting_beauty_sr.1001.exr)
          - turntable(*/RND_ass_lookdev_default_beauty_tt.1001.exr)
          - testCrawler(*/testSeq.0001.exr)
          - testCrawler(*/testSeq.0002.exr)
          - testCrawler(*/testSeq.0003.exr)
          - testCrawler(*/testSeq.0004.exr)
          - testCrawler(*/testSeq.0005.exr)
          - testCrawler(*/testSeq.0006.exr)
          - testCrawler(*/testSeq.0007.exr)
          - testCrawler(*/testSeq.0008.exr)
          - testCrawler(*/testSeq.0009.exr)
          - testCrawler(*/testSeq.0010.exr)
          - testCrawler(*/testSeq.0011.exr)
          - testCrawler(*/testSeq.0012.exr)
          - testCrawler(*/test_0001.exr)
        done
        echoTask output (execution * seconds):
          - jpg(*/testSeq.jpg)
        done
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
        dispacher.setOption('defaultReporter', 'detailed')
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
