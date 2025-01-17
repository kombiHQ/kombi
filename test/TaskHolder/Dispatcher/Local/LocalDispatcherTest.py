import os
import io
import unittest
import tempfile
from fnmatch import fnmatch
from ....BaseTestCase import BaseTestCase
from kombi.Element.Fs import FsElement
from kombi.TaskHolder.Loader import JsonLoader
from kombi.TaskWrapper import TaskWrapper
from kombi.Task import Task
from kombi.Element.Fs.Image import JpgElement, ExrElement
from kombi.Dispatcher import Dispatcher

class LocalDispatcherTest(BaseTestCase):
    """Test for the local dispatcher."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'dispatcherTest.json')
    __output = """
        copy output (execution * seconds):
          - nukeRender(*/RND-TST-SHT_comp_compName_output_v010_tk.1001.exr)
          - shotRender(*/RND-TST-SHT_lighting_beauty_sr.1001.exr)
          - turntable(*/RND_ass_lookdev_default_beauty_tt.1001.exr)
          - testElement(*/testSeq.0001.exr)
          - testElement(*/testSeq.0002.exr)
          - testElement(*/testSeq.0003.exr)
          - testElement(*/testSeq.0004.exr)
          - testElement(*/testSeq.0005.exr)
          - testElement(*/testSeq.0006.exr)
          - testElement(*/testSeq.0007.exr)
          - testElement(*/testSeq.0008.exr)
          - testElement(*/testSeq.0009.exr)
          - testElement(*/testSeq.0010.exr)
          - testElement(*/testSeq.0011.exr)
          - testElement(*/testSeq.0012.exr)
          - testElement(*/test_0001.exr)
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
        elements = FsElement.createFromPath(BaseTestCase.dataTestsDirectory()).glob()
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
            dispacher.dispatch(taskHolder, elements)

        createdElements = FsElement.createFromPath(temporaryDir).glob()
        exrElements = list(filter(lambda x: isinstance(x, ExrElement), createdElements))
        self.assertEqual(len(exrElements), 16)

        jpgElements = list(filter(lambda x: isinstance(x, JpgElement), createdElements))
        self.assertEqual(len(jpgElements), 1)

        output = outputStream.getvalue().replace('\r\n', '\n').split('\n')
        prefixSize = None
        for index, line in enumerate(self.__output.split('\n')[1:-1]):
            if prefixSize is None:
                prefixSize = len(line) - len(line.lstrip())

            line = line[prefixSize:]
            outputLine = output[index].replace('\\', '/')
            if not fnmatch(outputLine, line):
                self.assertEqual(outputLine, line)

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
