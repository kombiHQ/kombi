import os
import shutil
import unittest
from ..BaseTestCase import BaseTestCase
from kombi.Element.Fs import FsElement
from kombi.TaskHolder.Loader import Loader
from kombi.Template import Template
from kombi.Task import Task
from kombi.Task.Task import TaskInvalidOptionError
from kombi.Task.Task import TaskTypeNotFoundError
from kombi.TaskHolder import TaskHolder
from kombi.Element import Element

class TaskTest(BaseTestCase):
    """Test for tasks."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'test.json')
    __targetPath = BaseTestCase.tempDirectory()

    def testTaskRegistration(self):
        """
        Test that you can register a new Task.
        """
        class DummyTask(Task):
            pass
        Task.register('dummy', DummyTask)
        self.assertIn('dummy', Task.registeredNames())
        self.assertRaises(TaskTypeNotFoundError, Task.create, 'badTask')

    def testFilterTemplateElements(self):
        """
        Test that filter template in task holder.
        """
        elements = [FsElement.createFromPath(self.__jsonConfig)]

        for filterOption in ['0', 'false', 'False']:
            dummyTask = Task.create('checksum')
            taskHolder = TaskHolder(dummyTask, Template(), Template(filterOption))
            result = taskHolder.run(elements)
            self.assertEqual(len(result), 0)

    def testFilterTemplateNotApplied(self):
        """
        Test that filter template should not be applied.
        """
        elements = [FsElement.createFromPath(self.__jsonConfig)]

        for filterOption in ['randomStr', '']:
            dummyTask = Task.create('checksum')

            taskHolder = TaskHolder(dummyTask, Template("!kt {filePath}"), Template('!kt randomStr'))
            result = taskHolder.run(elements)
            self.assertEqual(len(result), len(elements))

    def testExecuteStatus(self):
        """
        Test execute status in the task holder.
        """
        dummyTask = Task.create('checksum')
        elements = [FsElement.createFromPath(self.__jsonConfig)]

        taskHolder = TaskHolder(dummyTask, Template("!kt {filePath}"))
        dummyTask2 = Task.create('checksum')
        taskHolder2 = TaskHolder(dummyTask2, Template("!kt {filePath}"))
        taskHolder2.setStatus('execute')
        taskHolder.addSubTaskHolder(taskHolder2)
        self.assertEqual(len(taskHolder.run(elements)), len(elements) * 2)

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
                result.extend(self.elements())
                result.extend(self.elements())
                return result
        Task.register('dummyMultiply', DummyMultiplyTask)

        dummyTask = Task.create('dummyMultiply')
        elements = [FsElement.createFromPath(self.__jsonConfig)]

        taskHolder = TaskHolder(dummyTask, Template("!kt {filePath}"))
        dummyTask2 = Task.create('dummyMultiply')
        taskHolder2 = TaskHolder(dummyTask2, Template("!kt {filePath}"))
        taskHolder.addSubTaskHolder(taskHolder2)

        self.assertEqual(len(taskHolder.run(elements)), len(elements) * 4)

        taskHolder.setStatus('bypass')
        self.assertEqual(len(taskHolder.run(elements)), len(elements) * 3)

    def testIgnoreStatus(self):
        """
        Test ignore status in the task holder.
        """
        dummyTask = Task.create('checksum')
        elements = [FsElement.createFromPath(self.__jsonConfig)]

        taskHolder = TaskHolder(dummyTask, Template("!kt {filePath}"))
        taskHolder.setStatus('ignore')

        dummyTask2 = Task.create('checksum')
        taskHolder2 = TaskHolder(dummyTask2, Template("!kt {filePath}"))
        taskHolder2.setStatus('execute')
        taskHolder.addSubTaskHolder(taskHolder2)
        self.assertEqual(len(taskHolder.run(elements)), 0)

        taskHolder.setStatus('execute')
        taskHolder2.setStatus('ignore')
        self.assertEqual(len(taskHolder.run(elements)), len(elements))

    def testTaskClone(self):
        """
        Test that cloning tasks works properly.
        """
        dummyTask = Task.create('sequenceThumbnail')
        elements = FsElement.createFromPath(BaseTestCase.dataTestsDirectory()).glob(['exr'])
        for element in elements:
            target = '{}_target'.format(element.var('name'))
            dummyTask.add(element, target)
        clone = dummyTask.clone()
        self.assertCountEqual(dummyTask.optionNames(), clone.optionNames())
        self.assertCountEqual(dummyTask.metadataNames(), clone.metadataNames())
        self.assertCountEqual(
            map(dummyTask.target, dummyTask.elements()),
            map(clone.target, clone.elements())
        )
        self.assertCountEqual(
            map(lambda x: x.var('filePath'), dummyTask.elements()),
            map(lambda x: x.var('filePath'), clone.elements())
        )

    def testTaskSetMetadata(self):
        """
        Test setting metadata to the task.
        """
        dummyTask = Task.create('copy')
        dummyTask.setMetadata('a.b.c', 'valueA')

        self.assertIn('a', dummyTask.metadataNames())
        self.assertTrue(dummyTask.hasMetadata('a.b.c'))
        self.assertEqual(dummyTask.metadata('a.b.c'), 'valueA')

    def testTaskUnsetMetadata(self):
        """
        Test removing metadata to the task.
        """
        dummyTask = Task.create('copy')
        dummyTask.setMetadata('a.b.c', 'valueA')

        dummyTask.unsetMetadata('a.b.c')
        self.assertFalse(dummyTask.hasMetadata('a.b.c'))

        dummyTask.setMetadata('a.b.c', 'valueA')
        dummyTask.unsetMetadata('a')

        self.assertNotIn('a', dummyTask.metadataNames())

    def testTaskSetOption(self):
        """
        Test setting a task option.
        """
        dummyTask = Task.create('copy')

        # boolean option
        self.assertFalse(dummyTask.hasOption('boolOption'))
        dummyTask.setOption('boolOption', True)
        self.assertTrue(dummyTask.hasOption('boolOption'))
        self.assertEqual(dummyTask.option('boolOption'), True)

        # float option
        self.assertFalse(dummyTask.hasOption('floatOption'))
        dummyTask.setOption('floatOption', 1.0)
        self.assertTrue(dummyTask.hasOption('floatOption'))
        self.assertEqual(dummyTask.option('floatOption'), 1.0)

        # int option
        self.assertFalse(dummyTask.hasOption('intOption'))
        dummyTask.setOption('intOption', 1)
        self.assertEqual(dummyTask.option('intOption'), 1)
        self.assertTrue(dummyTask.hasOption('intOption'))
        self.assertRaises(TaskInvalidOptionError, dummyTask.option, 'badOption')

    def testTaskSetMultipleOption(self):
        """
        Test setting multiple task options.
        """
        dummyTask = Task.create('copy')

        # boolean option
        dummyTask.setOption('boolOption', True)

        # float, int option
        dummyTask.setOptions(floatOption=1.0, intOption=1)

        # checking results
        self.assertTrue(dummyTask.hasOption('boolOption'))
        self.assertEqual(dummyTask.option('boolOption'), True)

        self.assertTrue(dummyTask.hasOption('floatOption'))
        self.assertEqual(dummyTask.option('floatOption'), 1.0)

        self.assertEqual(dummyTask.option('intOption'), 1)
        self.assertTrue(dummyTask.hasOption('intOption'))
        self.assertRaises(TaskInvalidOptionError, dummyTask.option, 'badOption')

    def testTaskUnsetOption(self):
        """
        Test removing a task option.
        """
        dummyTask = Task.create('copy')

        dummyTask.setOption('boolOption', True)
        dummyTask.setOption('floatOption', 1.0)
        dummyTask.setOption('intOption', 1)

        # removing option
        dummyTask.unsetOption('floatOption')

        self.assertTrue(dummyTask.hasOption('boolOption'))
        self.assertFalse(dummyTask.hasOption('floatOption'))
        self.assertTrue(dummyTask.hasOption('intOption'))

    def testTaskOptionNames(self):
        """
        Test retrieving all option names.
        """
        dummyTask = Task.create('copy')

        dummyTask.setOption('boolOption', True)
        dummyTask.setOption('floatOption', 1.0)
        dummyTask.setOption('intOption', 1)

        self.assertIn('boolOption', dummyTask.optionNames())
        self.assertIn('floatOption', dummyTask.optionNames())
        self.assertIn('intOption', dummyTask.optionNames())

    def testTaskTemplateOption(self):
        """
        Test that task template option are working properly.
        """
        class MyClawler(Element):
            pass

        taskHolderLoader = Loader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        dummyElement = MyClawler('dummy')
        dummyElement.setVar('testCustomVar', 'testValue')

        taskHolders = taskHolderLoader.taskHolders()
        self.assertEqual(len(taskHolders), 1)

        # copy task holder
        extraVars = {'testCustomVar': taskHolders[0].var('testCustomVar')}
        copyTask = taskHolders[0].task()
        self.assertEqual(copyTask.type(), 'copy')

        self.assertEqual(copyTask.option('testOption', element=dummyElement), 'testValue')
        self.assertEqual(copyTask.option('testOption', extraVars=extraVars), '!kt {testCustomVar}')
        self.assertEqual(copyTask.option('testExpr'), '!kt (min 2 6)')

        # sequence thumbnail task holder
        self.assertEqual(len(taskHolders[0].subTaskHolders()), 1)
        sequenceThumbnailTask = taskHolders[0].subTaskHolders()[0].task()
        sequenceThumbnailTask.setOption('height', "!kt {height}")
        dummyElement.setVar('height', 2000)
        self.assertEqual(sequenceThumbnailTask.type(), 'sequenceThumbnail')
        self.assertEqual(sequenceThumbnailTask.option('width'), 640)
        self.assertEqual(sequenceThumbnailTask.option('height', element=dummyElement), '2000')

    def testTaskOutput(self):
        """
        Test that task output is returned properly.
        """
        class DummyTask(Task):
            def _perform(self):
                for element in self.elements():
                    shutil.copy(element.var('filePath'), self.target(element))
                return super()._perform()
        Task.register("dummy", DummyTask)

        dummyTask = Task.create('dummy')
        elements = FsElement.createFromPath(BaseTestCase.dataTestsDirectory()).glob(['mov'])
        targetPaths = []
        for element in elements:
            target = '{}_target.mov'.format(element.var('name'))
            targetPath = os.path.join(self.__targetPath, target)
            targetPaths.append(targetPath)
            element.setVar('contextVarTest', 1, True)
            dummyTask.add(element, targetPath)
        result = dummyTask.output()
        self.assertEqual(len(result), len(elements))
        self.assertCountEqual(
            map(lambda x: x.var('filePath'), result),
            targetPaths
        )
        self.assertEqual(
            list(map(lambda x: x.var('contextVarTest'), result)),
            [1] * len(elements)
        )
        for element in result:
            self.assertIn('contextVarTest', element.contextVarNames())

    def testTaskJson(self):
        """
        Test that you can convert a Task to json and back.
        """
        class DummyTask(Task):
            pass
        Task.register('dummy', DummyTask)

        dummyTask = Task.create('dummy')
        elements = FsElement.createFromPath(BaseTestCase.dataTestsDirectory()).glob(['mov'])
        targetPaths = []
        for element in elements:
            target = '{}_target.mov'.format(element.var('name'))
            targetPath = os.path.join(BaseTestCase.dataTestsDirectory(), target)
            targetPaths.append(targetPath)
            dummyTask.add(element, targetPath)
        jsonResult = dummyTask.toJson()
        resultTask = Task.createFromJson(jsonResult)
        self.assertCountEqual(dummyTask.optionNames(), resultTask.optionNames())
        self.assertCountEqual(dummyTask.metadataNames(), resultTask.metadataNames())
        self.assertCountEqual(
            map(lambda x: x.var('filePath'), dummyTask.elements()),
            map(lambda x: x.var('filePath'), resultTask.elements())
        )
        self.assertCountEqual(
            map(dummyTask.target, dummyTask.elements()),
            map(resultTask.target, resultTask.elements())
        )


if __name__ == "__main__":
    unittest.main()
