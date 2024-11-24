import os
import unittest
from ..BaseTestCase import BaseTestCase
from kombi.InfoCrate.Fs import FsInfoCrate
from kombi.TaskHolder.Loader import Loader
from kombi.TaskWrapper import TaskWrapper
from kombi.Template import Template
from kombi.Task import Task
from kombi.Task.Task import TaskInvalidOptionError
from kombi.Task.Task import TaskTypeNotFoundError
from kombi.TaskHolder import TaskHolder, TaskHolderInvalidVarNameError
from kombi.InfoCrate.Fs.Image import JpgInfoCrate, ExrInfoCrate
from kombi.InfoCrate import InfoCrate

class TaskTest(BaseTestCase):
    """Test for tasks."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'test.json')

    def testTaskRegistration(self):
        """
        Test that you can register a new Task.
        """
        class DummyTask(Task):
            pass
        Task.register('dummy', DummyTask)
        self.assertIn('dummy', Task.registeredNames())
        self.assertRaises(TaskTypeNotFoundError, Task.create, 'badTask')

    def testFilterTemplateInfoCrates(self):
        """
        Test that filter template in task holder.
        """
        infoCrates = [FsInfoCrate.createFromPath(self.__jsonConfig)]

        for filterOption in ['0', 'false', 'False']:
            dummyTask = Task.create('checksum')
            taskHolder = TaskHolder(dummyTask, Template(), Template(filterOption))
            result = taskHolder.run(infoCrates)
            self.assertEqual(len(result), 0)

    def testFilterTemplateNotApplied(self):
        """
        Test that filter template should not be applied.
        """
        infoCrates = [FsInfoCrate.createFromPath(self.__jsonConfig)]

        for filterOption in ['randomStr', '']:
            dummyTask = Task.create('checksum')

            taskHolder = TaskHolder(dummyTask, Template("{filePath}"), Template('randomStr'))
            result = taskHolder.run(infoCrates)
            self.assertEqual(len(result), len(infoCrates))

    def testExecuteStatus(self):
        """
        Test execute status in the task holder.
        """
        dummyTask = Task.create('checksum')
        infoCrates = [FsInfoCrate.createFromPath(self.__jsonConfig)]

        taskHolder = TaskHolder(dummyTask, Template("{filePath}"))
        dummyTask2 = Task.create('checksum')
        taskHolder2 = TaskHolder(dummyTask2, Template("{filePath}"))
        taskHolder2.setStatus('execute')
        taskHolder.addSubTaskHolder(taskHolder2)
        self.assertEqual(len(taskHolder.run(infoCrates)), len(infoCrates) * 2)

    def testBypassStatus(self):
        """
        Test bypass status in the task holder.
        """

        class DummyMultiplyTask(Task):
            def _perform(self):
                """
                Perform the task.
                """
                result = []
                result.extend(self.infoCrates())
                result.extend(self.infoCrates())
                return result
        Task.register('dummyMultiply', DummyMultiplyTask)

        dummyTask = Task.create('dummyMultiply')
        infoCrates = [FsInfoCrate.createFromPath(self.__jsonConfig)]

        taskHolder = TaskHolder(dummyTask, Template("{filePath}"))
        dummyTask2 = Task.create('dummyMultiply')
        taskHolder2 = TaskHolder(dummyTask2, Template("{filePath}"))
        taskHolder.addSubTaskHolder(taskHolder2)

        self.assertEqual(len(taskHolder.run(infoCrates)), len(infoCrates) * 4)

        taskHolder.setStatus('bypass')
        self.assertEqual(len(taskHolder.run(infoCrates)), len(infoCrates) * 3)

    def testIgnoreStatus(self):
        """
        Test ignore status in the task holder.
        """
        dummyTask = Task.create('checksum')
        infoCrates = [FsInfoCrate.createFromPath(self.__jsonConfig)]

        taskHolder = TaskHolder(dummyTask, Template("{filePath}"))
        taskHolder.setStatus('ignore')

        dummyTask2 = Task.create('checksum')
        taskHolder2 = TaskHolder(dummyTask2, Template("{filePath}"))
        taskHolder2.setStatus('execute')
        taskHolder.addSubTaskHolder(taskHolder2)
        self.assertEqual(len(taskHolder.run(infoCrates)), 0)

        taskHolder.setStatus('execute')
        taskHolder2.setStatus('ignore')
        self.assertEqual(len(taskHolder.run(infoCrates)), len(infoCrates))

    def testTaskClone(self):
        """
        Test that cloning tasks works properly.
        """
        dummyTask = Task.create('sequenceThumbnail')
        infoCrates = FsInfoCrate.createFromPath(BaseTestCase.dataTestsDirectory()).glob(['exr'])
        for infoCrate in infoCrates:
            target = '{}_target'.format(infoCrate.var('name'))
            dummyTask.add(infoCrate, target)
        clone = dummyTask.clone()
        self.assertCountEqual(dummyTask.optionNames(), clone.optionNames())
        self.assertCountEqual(dummyTask.metadataNames(), clone.metadataNames())
        self.assertCountEqual(
            map(dummyTask.target, dummyTask.infoCrates()),
            map(clone.target, clone.infoCrates())
        )
        self.assertCountEqual(
            map(lambda x: x.var('filePath'), dummyTask.infoCrates()),
            map(lambda x: x.var('filePath'), clone.infoCrates())
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
        class MyClawler(InfoCrate):
            pass

        taskHolderLoader = Loader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        dummyInfoCrate = MyClawler('dummy')
        dummyInfoCrate.setVar('testCustomVar', 'testValue')

        taskHolders = taskHolderLoader.taskHolders()
        self.assertEqual(len(taskHolders), 1)

        # copy task holder
        extraVars = {'testCustomVar': taskHolders[0].var('testCustomVar')}
        copyTask = taskHolders[0].task()
        self.assertEqual(copyTask.type(), 'copy')

        self.assertEqual(copyTask.templateOption('testOption', infoCrate=dummyInfoCrate), 'testValue')
        self.assertEqual(copyTask.templateOption('testOption', extraVars=extraVars), 'randomValue')
        self.assertEqual(copyTask.templateOption('testExpr'), '2')

        # sequence thumbnail task holder
        self.assertEqual(len(taskHolders[0].subTaskHolders()), 1)
        sequenceThumbnailTask = taskHolders[0].subTaskHolders()[0].task()
        sequenceThumbnailTask.setOption('height', "{height}")
        dummyInfoCrate.setVar('height', 2000)
        self.assertEqual(sequenceThumbnailTask.type(), 'sequenceThumbnail')
        self.assertEqual(sequenceThumbnailTask.option('width'), 640)
        self.assertEqual(sequenceThumbnailTask.templateOption('height', infoCrate=dummyInfoCrate), '2000')

    def testTaskOutput(self):
        """
        Test that task output is returned properly.
        """
        class DummyTask(Task):
            pass
        Task.register("dummy", DummyTask)

        dummyTask = Task.create('dummy')
        infoCrates = FsInfoCrate.createFromPath(BaseTestCase.dataTestsDirectory()).glob(['mov'])
        targetPaths = []
        for infoCrate in infoCrates:
            target = '{}_target.mov'.format(infoCrate.var('name'))
            targetPath = os.path.join(BaseTestCase.dataTestsDirectory(), target)
            targetPaths.append(targetPath)
            infoCrate.setVar('contextVarTest', 1, True)
            dummyTask.add(infoCrate, targetPath)
        result = dummyTask.output()
        self.assertEqual(len(result), len(infoCrates))
        self.assertCountEqual(
            map(lambda x: x.var('filePath'), result),
            targetPaths
        )
        self.assertEqual(
            list(map(lambda x: x.var('contextVarTest'), result)),
            [1] * len(infoCrates)
        )
        for infoCrate in result:
            self.assertIn('contextVarTest', infoCrate.contextVarNames())

    def testTaskJson(self):
        """
        Test that you can convert a Task to json and back.
        """
        class DummyTask(Task):
            pass
        Task.register('dummy', DummyTask)

        dummyTask = Task.create('dummy')
        infoCrates = FsInfoCrate.createFromPath(BaseTestCase.dataTestsDirectory()).glob(['mov'])
        targetPaths = []
        for infoCrate in infoCrates:
            target = '{}_target.mov'.format(infoCrate.var('name'))
            targetPath = os.path.join(BaseTestCase.dataTestsDirectory(), target)
            targetPaths.append(targetPath)
            dummyTask.add(infoCrate, targetPath)
        jsonResult = dummyTask.toJson()
        resultTask = Task.createFromJson(jsonResult)
        self.assertCountEqual(dummyTask.optionNames(), resultTask.optionNames())
        self.assertCountEqual(dummyTask.metadataNames(), resultTask.metadataNames())
        self.assertCountEqual(
            map(lambda x: x.var('filePath'), dummyTask.infoCrates()),
            map(lambda x: x.var('filePath'), resultTask.infoCrates())
        )
        self.assertCountEqual(
            map(dummyTask.target, dummyTask.infoCrates()),
            map(resultTask.target, resultTask.infoCrates())
        )

    def testConfig(self):
        """
        Test that you can run tasks through a config file properly.
        """
        taskHolderLoader = Loader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        infoCrates = FsInfoCrate.createFromPath(BaseTestCase.dataTestsDirectory()).glob()

        createdInfoCrates = []
        for taskHolder in taskHolderLoader.taskHolders():
            self.assertIn('testCustomVar', taskHolder.varNames())
            self.assertEqual(taskHolder.var('testCustomVar'), 'randomValue')
            self.assertRaises(TaskHolderInvalidVarNameError, taskHolder.var, 'badVar')
            createdInfoCrates += taskHolder.run(infoCrates)

        exrInfoCrates = list(filter(lambda x: isinstance(x, ExrInfoCrate), createdInfoCrates))
        self.assertEqual(len(exrInfoCrates), 19)

        jpgInfoCrates = list(filter(lambda x: isinstance(x, JpgInfoCrate), createdInfoCrates))
        self.assertEqual(len(jpgInfoCrates), 1)

        self.cleanup(exrInfoCrates + jpgInfoCrates)

    def cleanup(self, infoCrates):
        """
        Remove the data that was copied.
        """
        removeTask = Task.create('remove')
        for infoCrate in infoCrates:
            removeTask.add(infoCrate, infoCrate.var("filePath"))
        wrapper = TaskWrapper.create('python')
        wrapper.setOption('user', '')
        wrapper.run(removeTask)


if __name__ == "__main__":
    unittest.main()
