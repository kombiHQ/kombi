import os
import io
import unittest
import tempfile
from fnmatch import fnmatch
from ...BaseTestCase import BaseTestCase
from chilopoda.Crawler.Fs import FsPath
from chilopoda.TaskHolderLoader import JsonLoader
from chilopoda.TaskWrapper import TaskWrapper
from chilopoda.Task import Task
from chilopoda.Crawler.Fs.Image import Jpg, Exr
from chilopoda.Dispatcher import Dispatcher

class LocalTest(BaseTestCase):
    """Test for the local dispatcher."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'dispatcherTest.json')
    __output = """
        copy output (execution * seconds):
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
        sequenceThumbnail output (execution * seconds):
          - jpg(*/testSeq.jpg)
        done
    """

    def testConfig(self):
        """
        Test that you can run tasks through a config file properly.
        """
        taskHolderLoader = JsonLoader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        crawlers = FsPath.createFromPath(BaseTestCase.dataTestsDirectory()).glob()
        temporaryDir = tempfile.mkdtemp()

        dispacher = Dispatcher.create("local")
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
            taskHolder.addVar(
                'temporaryDir',
                temporaryDir,
                True
            )
            dispacher.dispatch(taskHolder, crawlers)

        createdCrawlers = FsPath.createFromPath(temporaryDir).glob()
        exrCrawlers = list(filter(lambda x: isinstance(x, Exr), createdCrawlers))
        self.assertEqual(len(exrCrawlers), 16)

        jpgCrawlers = list(filter(lambda x: isinstance(x, Jpg), createdCrawlers))
        self.assertEqual(len(jpgCrawlers), 1)

        output = outputStream.getvalue().replace('\r\n', '\n').split('\n')
        prefixSize = None
        for index, line in enumerate(self.__output.split('\n')[1:-1]):
            if prefixSize is None:
                prefixSize = len(line) - len(line.lstrip())

            line = line[prefixSize:]
            outputLine = output[index].replace('\\', '/')
            if not fnmatch(outputLine, line):
                self.assertEqual(outputLine, line)

        self.cleanup(exrCrawlers + jpgCrawlers)

    def cleanup(self, crawlers):
        """
        Remove the data that was copied.
        """
        removeTask = Task.create('remove')
        for crawler in crawlers:
            removeTask.add(crawler, crawler.var("filePath"))
        wrapper = TaskWrapper.create('python')
        wrapper.setOption('user', '')
        wrapper.run(removeTask)


if __name__ == "__main__":
    unittest.main()
