import os
import unittest
import tempfile
from ...BaseTestCase import BaseTestCase
from chilopoda.Crawler.Fs import FsPath
from chilopoda.TaskHolderLoader import JsonLoader
from chilopoda.TaskWrapper import TaskWrapper
from chilopoda.Task import Task
from chilopoda.Crawler.Fs.Image import Jpg, Exr
from chilopoda.Dispatcher import Dispatcher

class LocalTest(BaseTestCase):
    """Test for the local dispatcher."""

    __jsonConfig = os.path.join(BaseTestCase.dataDirectory(), 'config', 'dispatcherTest.json')

    def testConfig(self):
        """
        Test that you can run tasks through a config file properly.
        """
        taskHolderLoader = JsonLoader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        crawlers = FsPath.createFromPath(BaseTestCase.dataDirectory()).glob()
        temporaryDir = tempfile.mkdtemp()

        dispacher = Dispatcher.create("local")
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
