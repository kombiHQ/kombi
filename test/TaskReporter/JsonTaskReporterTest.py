import os
import io
import unittest
from fnmatch import fnmatch
from ..BaseTestCase import BaseTestCase
from kombi.Element.Fs import FsElement
from kombi.TaskHolder.Loader import JsonLoader
from kombi.Dispatcher import Dispatcher
from kombi.ResourceLoader import ResourceLoader

class JsonTaskReporterTest(BaseTestCase):
    """Test for json task reporter."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'reporterTest.json')
    __taskPath = os.path.join(BaseTestCase.dataTestsDirectory(), 'tasks', 'EchoTask.py')
    __output = """
        {
            "elements": [
                {
                    "elementType": "nukeRender",
                    "fullPath": "*/RND-TST-SHT_comp_compName_output_v010_tk.1001.exr"
                },
                {
                    "elementType": "shotRender",
                    "fullPath": "*/RND-TST-SHT_lighting_beauty_sr.1001.exr"
                },
                {
                    "elementType": "turntable",
                    "fullPath": "*/RND_ass_lookdev_default_beauty_tt.1001.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0001.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0002.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0003.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0004.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0005.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0006.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0007.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0008.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0009.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0010.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0011.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/testSeq.0012.exr"
                },
                {
                    "elementType": "testElement",
                    "fullPath": "*/test_0001.exr"
                }
            ],
            "execution": *,
            "task": "echoTask"
        }
        {
            "elements": [
                {
                    "elementType": "jpg",
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
        resource = ResourceLoader.get()
        resource.load(self.__taskPath)

        taskHolderLoader = JsonLoader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        elements = FsElement.createFromPath(BaseTestCase.dataTestsDirectory()).glob()

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
            dispacher.dispatch(taskHolder, elements)

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
