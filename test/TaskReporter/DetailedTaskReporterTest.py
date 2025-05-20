import os
import io
import unittest
from fnmatch import fnmatch
from ..BaseTestCase import BaseTestCase
from kombi.Element.Fs import FsElement
from kombi.TaskHolder.Loader import JsonLoader
from kombi.Dispatcher import Dispatcher

class DetailedTaskReporterTest(BaseTestCase):
    """Test for detailed task reporter."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'reporterTest.json')
    __output = """
        convertImage output (execution * seconds):
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
        convertImage output (execution * seconds):
          - jpg(*/testSeq.0001.jpg)
          - jpg(*/testSeq.0002.jpg)
          - jpg(*/testSeq.0003.jpg)
          - jpg(*/testSeq.0004.jpg)
          - jpg(*/testSeq.0005.jpg)
          - jpg(*/testSeq.0006.jpg)
          - jpg(*/testSeq.0007.jpg)
          - jpg(*/testSeq.0008.jpg)
          - jpg(*/testSeq.0009.jpg)
          - jpg(*/testSeq.0010.jpg)
          - jpg(*/testSeq.0011.jpg)
          - jpg(*/testSeq.0012.jpg)
        done
    """

    def testReport(self):
        """
        Test the output produced by the reporter.
        """
        taskHolderLoader = JsonLoader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        elements = FsElement.createFromPath(BaseTestCase.dataTestsDirectory()).children()

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
