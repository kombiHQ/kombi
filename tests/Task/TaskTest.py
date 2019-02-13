import os
import unittest
from ..BaseTestCase import BaseTestCase
from chilopoda.Crawler.Fs import FsPath
from chilopoda.TaskHolderLoader import TaskHolderLoader
from chilopoda.TaskWrapper import TaskWrapper
from chilopoda.Template import Template
from chilopoda.Task import Task
from chilopoda.Task.Task import TaskInvalidOptionError
from chilopoda.Task.Task import TaskTypeNotFoundError
from chilopoda.TaskHolder import TaskHolder, TaskHolderInvalidVarNameError
from chilopoda.Crawler.Fs.Image import Jpg, Exr
from chilopoda.Crawler import Crawler

class TaskTest(BaseTestCase):
    """Test for tasks."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'test.json')

    def testTaskRegistration(self):
        """
        Test that you can register a new Task.
        """
        class DummyTask(Task):
            pass
        Task.register("dummy", DummyTask)
        self.assertIn("dummy", Task.registeredNames())
        self.assertRaises(TaskTypeNotFoundError, Task.create, 'badTask')

    def testFilterTemplateCrawlers(self):
        """
        Test that filter template in task holder.
        """
        crawlers = [FsPath.createFromPath(self.__jsonConfig)]

        for filterOption in ['0', 'false', 'False']:
            dummyTask = Task.create('checksum')
            taskHolder = TaskHolder(dummyTask, Template(), Template(filterOption))
            result = taskHolder.run(crawlers)
            self.assertEqual(len(result), 0)

    def testFilterTemplateNotApplied(self):
        """
        Test that filter template should not be applied.
        """
        crawlers = [FsPath.createFromPath(self.__jsonConfig)]

        for filterOption in ['randomStr', '']:
            dummyTask = Task.create('checksum')

            taskHolder = TaskHolder(dummyTask, Template("{filePath}"), Template('randomStr'))
            result = taskHolder.run(crawlers)
            self.assertEqual(len(result), len(crawlers))

    def testExecuteStatus(self):
        """
        Test execute status in the task holder.
        """
        dummyTask = Task.create('checksum')
        crawlers = [FsPath.createFromPath(self.__jsonConfig)]

        taskHolder = TaskHolder(dummyTask, Template("{filePath}"))
        dummyTask2 = Task.create('checksum')
        taskHolder2 = TaskHolder(dummyTask2, Template("{filePath}"))
        taskHolder2.setStatus("execute")
        taskHolder.addSubTaskHolder(taskHolder2)
        self.assertEqual(len(taskHolder.run(crawlers)), len(crawlers) * 2)

    def testBypassStatus(self):
        """
        Test bypass status in the task holder.
        """
        dummyTask = Task.create('checksum')
        crawlers = [FsPath.createFromPath(self.__jsonConfig)]

        taskHolder = TaskHolder(dummyTask, Template("{filePath}"))
        dummyTask2 = Task.create('checksum')
        taskHolder2 = TaskHolder(dummyTask2, Template("{filePath}"))
        taskHolder.addSubTaskHolder(taskHolder2)
        self.assertEqual(len(taskHolder.run(crawlers)), len(crawlers) * 2)

        taskHolder.setStatus("bypass")
        self.assertEqual(len(taskHolder.run(crawlers)), len(crawlers))

    def testIgnoreStatus(self):
        """
        Test ignore status in the task holder.
        """
        dummyTask = Task.create('checksum')
        crawlers = [FsPath.createFromPath(self.__jsonConfig)]

        taskHolder = TaskHolder(dummyTask, Template("{filePath}"))
        taskHolder.setStatus("ignore")

        dummyTask2 = Task.create('checksum')
        taskHolder2 = TaskHolder(dummyTask2, Template("{filePath}"))
        taskHolder2.setStatus("execute")
        taskHolder.addSubTaskHolder(taskHolder2)
        self.assertEqual(len(taskHolder.run(crawlers)), 0)

        taskHolder.setStatus("execute")
        taskHolder2.setStatus("ignore")
        self.assertEqual(len(taskHolder.run(crawlers)), len(crawlers))

    def testTaskClone(self):
        """
        Test that cloning tasks works properly.
        """
        dummyTask = Task.create('sequenceThumbnail')
        crawlers = FsPath.createFromPath(BaseTestCase.dataTestsDirectory()).glob(['exr'])
        for crawler in crawlers:
            target = '{}_target'.format(crawler.var('name'))
            dummyTask.add(crawler, target)
        clone = dummyTask.clone()
        self.assertCountEqual(dummyTask.optionNames(), clone.optionNames())
        self.assertCountEqual(dummyTask.metadataNames(), clone.metadataNames())
        self.assertCountEqual(
            map(dummyTask.target, dummyTask.crawlers()),
            map(clone.target, clone.crawlers())
        )
        self.assertCountEqual(
            map(lambda x: x.var('filePath'), dummyTask.crawlers()),
            map(lambda x: x.var('filePath'), clone.crawlers())
        )

    def testTaskOptions(self):
        """
        Test that task options are working properly.
        """
        dummyTask = Task.create('copy')
        dummyTask.setOption('boolOption', True)
        self.assertEqual(dummyTask.option('boolOption'), True)
        dummyTask.setOption('floatOption', 1.0)
        self.assertEqual(dummyTask.option('floatOption'), 1.0)
        dummyTask.setOption('intOption', 1)
        self.assertEqual(dummyTask.option('intOption'), 1)
        self.assertRaises(TaskInvalidOptionError, dummyTask.option, 'badOption')

    def testTaskTemplateOption(self):
        """
        Test that task template option are working properly.
        """
        class MyClawler(Crawler):
            pass

        taskHolderLoader = TaskHolderLoader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        dummyCrawler = MyClawler('dummy')
        dummyCrawler.setVar('testCustomVar', 'testValue')

        taskHolders = taskHolderLoader.taskHolders()
        self.assertEqual(len(taskHolders), 1)

        # copy task holder
        extraVars = {'testCustomVar': taskHolders[0].var('testCustomVar')}
        copyTask = taskHolders[0].task()
        self.assertEqual(copyTask.type(), 'copy')

        self.assertEqual(copyTask.templateOption('testOption', crawler=dummyCrawler), 'testValue')
        self.assertEqual(copyTask.templateOption('testOption', extraVars=extraVars), 'randomValue')
        self.assertEqual(copyTask.templateOption('testExpr'), '2')

        # sequence thumbnail task holder
        self.assertEqual(len(taskHolders[0].subTaskHolders()), 1)
        sequenceThumbnailTask = taskHolders[0].subTaskHolders()[0].task()
        sequenceThumbnailTask.setOption('height', "{height}")
        dummyCrawler.setVar('height', 2000)
        self.assertEqual(sequenceThumbnailTask.type(), 'sequenceThumbnail')
        self.assertEqual(sequenceThumbnailTask.option('width'), 640)
        self.assertEqual(sequenceThumbnailTask.templateOption('height', crawler=dummyCrawler), '2000')

    def testTaskOutput(self):
        """
        Test that task output is returned properly.
        """
        class DummyTask(Task):
            pass
        Task.register("dummy", DummyTask)

        dummyTask = Task.create('dummy')
        crawlers = FsPath.createFromPath(BaseTestCase.dataTestsDirectory()).glob(['mov'])
        targetPaths = []
        for crawler in crawlers:
            target = '{}_target.mov'.format(crawler.var('name'))
            targetPath = os.path.join(BaseTestCase.dataTestsDirectory(), target)
            targetPaths.append(targetPath)
            crawler.setVar('contextVarTest', 1, True)
            dummyTask.add(crawler, targetPath)
        result = dummyTask.output()
        self.assertEqual(len(result), len(crawlers))
        self.assertCountEqual(
            map(lambda x: x.var('filePath'), result),
            targetPaths
        )
        self.assertEqual(
            list(map(lambda x: x.var('contextVarTest'), result)),
            [1]*len(crawlers)
        )
        for crawler in result:
            self.assertIn('contextVarTest', crawler.contextVarNames())

    def testTaskJson(self):
        """
        Test that you can convert a Task to json and back.
        """
        class DummyTask(Task):
            pass
        Task.register("dummy", DummyTask)

        dummyTask = Task.create('dummy')
        crawlers = FsPath.createFromPath(BaseTestCase.dataTestsDirectory()).glob(['mov'])
        targetPaths = []
        for crawler in crawlers:
            target = '{}_target.mov'.format(crawler.var('name'))
            targetPath = os.path.join(BaseTestCase.dataTestsDirectory(), target)
            targetPaths.append(targetPath)
            dummyTask.add(crawler, targetPath)
        jsonResult = dummyTask.toJson()
        resultTask = Task.createFromJson(jsonResult)
        self.assertCountEqual(dummyTask.optionNames(), resultTask.optionNames())
        self.assertCountEqual(dummyTask.metadataNames(), resultTask.metadataNames())
        self.assertCountEqual(
            map(lambda x: x.var('filePath'), dummyTask.crawlers()),
            map(lambda x: x.var('filePath'), resultTask.crawlers())
        )
        self.assertCountEqual(
            map(dummyTask.target, dummyTask.crawlers()),
            map(resultTask.target, resultTask.crawlers())
        )

    def testConfig(self):
        """
        Test that you can run tasks through a config file properly.
        """
        taskHolderLoader = TaskHolderLoader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        crawlers = FsPath.createFromPath(BaseTestCase.dataTestsDirectory()).glob()

        createdCrawlers = []
        for taskHolder in taskHolderLoader.taskHolders():
            self.assertIn('testCustomVar', taskHolder.varNames())
            self.assertEqual(taskHolder.var('testCustomVar'), 'randomValue')
            self.assertRaises(TaskHolderInvalidVarNameError, taskHolder.var, 'badVar')
            createdCrawlers += taskHolder.run(crawlers)

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
