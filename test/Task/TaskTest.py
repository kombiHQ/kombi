import os
import unittest
from ..BaseTestCase import BaseTestCase
from kombi.Element.Fs import FsElement
from kombi.TaskHolder.Loader import Loader
from kombi.TaskWrapper import TaskWrapper
from kombi.Template import Template
from kombi.Task import Task
from kombi.Task.Task import TaskInvalidOptionError
from kombi.Task.Task import TaskTypeNotFoundError
from kombi.TaskHolder import TaskHolder, TaskHolderInvalidVarNameError
from kombi.Element.Fs.Image import JpgElement, ExrElement
from kombi.Element import Element

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

            taskHolder = TaskHolder(dummyTask, Template("{filePath}"), Template('randomStr'))
            result = taskHolder.run(elements)
            self.assertEqual(len(result), len(elements))

    def testExecuteStatus(self):
        """
        Test execute status in the task holder.
        """
        dummyTask = Task.create('checksum')
        elements = [FsElement.createFromPath(self.__jsonConfig)]

        taskHolder = TaskHolder(dummyTask, Template("{filePath}"))
        dummyTask2 = Task.create('checksum')
        taskHolder2 = TaskHolder(dummyTask2, Template("{filePath}"))
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

        taskHolder = TaskHolder(dummyTask, Template("{filePath}"))
        dummyTask2 = Task.create('dummyMultiply')
        taskHolder2 = TaskHolder(dummyTask2, Template("{filePath}"))
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

        taskHolder = TaskHolder(dummyTask, Template("{filePath}"))
        taskHolder.setStatus('ignore')

        dummyTask2 = Task.create('checksum')
        taskHolder2 = TaskHolder(dummyTask2, Template("{filePath}"))
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

        self.assertEqual(copyTask.templateOption('testOption', element=dummyElement), 'testValue')
        self.assertEqual(copyTask.templateOption('testOption', extraVars=extraVars), 'randomValue')
        self.assertEqual(copyTask.templateOption('testExpr'), '2')

        # sequence thumbnail task holder
        self.assertEqual(len(taskHolders[0].subTaskHolders()), 1)
        sequenceThumbnailTask = taskHolders[0].subTaskHolders()[0].task()
        sequenceThumbnailTask.setOption('height', "{height}")
        dummyElement.setVar('height', 2000)
        self.assertEqual(sequenceThumbnailTask.type(), 'sequenceThumbnail')
        self.assertEqual(sequenceThumbnailTask.option('width'), 640)
        self.assertEqual(sequenceThumbnailTask.templateOption('height', element=dummyElement), '2000')

    def testTaskOutput(self):
        """
        Test that task output is returned properly.
        """
        class DummyTask(Task):
            pass
        Task.register("dummy", DummyTask)

        dummyTask = Task.create('dummy')
        elements = FsElement.createFromPath(BaseTestCase.dataTestsDirectory()).glob(['mov'])
        targetPaths = []
        for element in elements:
            target = '{}_target.mov'.format(element.var('name'))
            targetPath = os.path.join(BaseTestCase.dataTestsDirectory(), target)
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

    def testConfig(self):
        """
        Test that you can run tasks through a config file properly.
        """
        taskHolderLoader = Loader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        elements = FsElement.createFromPath(BaseTestCase.dataTestsDirectory()).glob()

        createdElements = []
        for taskHolder in taskHolderLoader.taskHolders():
            self.assertIn('testCustomVar', taskHolder.varNames())
            self.assertEqual(taskHolder.var('testCustomVar'), 'randomValue')
            self.assertRaises(TaskHolderInvalidVarNameError, taskHolder.var, 'badVar')
            createdElements += taskHolder.run(elements)

        exrElements = list(filter(lambda x: isinstance(x, ExrElement), createdElements))
        self.assertEqual(len(exrElements), 19)

        jpgElements = list(filter(lambda x: isinstance(x, JpgElement), createdElements))
        self.assertEqual(len(jpgElements), 1)

        self.cleanup(exrElements + jpgElements)

    def cleanup(self, elements):
        """
        Remove the data that was copied.
        """
        removeTask = Task.create('remove')
        for element in elements:
            removeTask.add(element, element.var("filePath"))
        wrapper = TaskWrapper.create('python')
        wrapper.setOption('user', '')
        wrapper.run(removeTask)


if __name__ == "__main__":
    unittest.main()
