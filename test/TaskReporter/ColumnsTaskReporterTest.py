import os
import io
import unittest
from fnmatch import fnmatch
from ..BaseTestCase import BaseTestCase
from kombi.Element.Fs import FsElement
from kombi.TaskHolder.Loader import JsonLoader
from kombi.Dispatcher import Dispatcher

class ColumnsTaskReporterTest(BaseTestCase):
    """Test for column task reporter."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'reporterTest.json')
    __output = """
        convertImage\t\tnukeRender\t\t*/RND-TST-SHT_comp_compName_output_v010_tk.1001.exr
        convertImage\t\tshotRender\t\t*/RND-TST-SHT_lighting_beauty_sr.1001.exr
        convertImage\t\tturntable\t\t*/RND_ass_lookdev_default_beauty_tt.1001.exr
        convertImage\t\ttestElement\t\t*/testSeq.0001.exr
        convertImage\t\ttestElement\t\t*/testSeq.0002.exr
        convertImage\t\ttestElement\t\t*/testSeq.0003.exr
        convertImage\t\ttestElement\t\t*/testSeq.0004.exr
        convertImage\t\ttestElement\t\t*/testSeq.0005.exr
        convertImage\t\ttestElement\t\t*/testSeq.0006.exr
        convertImage\t\ttestElement\t\t*/testSeq.0007.exr
        convertImage\t\ttestElement\t\t*/testSeq.0008.exr
        convertImage\t\ttestElement\t\t*/testSeq.0009.exr
        convertImage\t\ttestElement\t\t*/testSeq.0010.exr
        convertImage\t\ttestElement\t\t*/testSeq.0011.exr
        convertImage\t\ttestElement\t\t*/testSeq.0012.exr
        convertImage\t\ttestElement\t\t*/test_0001.exr
        convertImage\t\tjpg\t\t\t*/testSeq.0001.jpg
        convertImage\t\tjpg\t\t\t*/testSeq.0002.jpg
        convertImage\t\tjpg\t\t\t*/testSeq.0003.jpg
        convertImage\t\tjpg\t\t\t*/testSeq.0004.jpg
        convertImage\t\tjpg\t\t\t*/testSeq.0005.jpg
        convertImage\t\tjpg\t\t\t*/testSeq.0006.jpg
        convertImage\t\tjpg\t\t\t*/testSeq.0007.jpg
        convertImage\t\tjpg\t\t\t*/testSeq.0008.jpg
        convertImage\t\tjpg\t\t\t*/testSeq.0009.jpg
        convertImage\t\tjpg\t\t\t*/testSeq.0010.jpg
        convertImage\t\tjpg\t\t\t*/testSeq.0011.jpg
        convertImage\t\tjpg\t\t\t*/testSeq.0012.jpg
    """

    def testReport(self):
        """
        Test the output produced by the reporter.
        """
        taskHolderLoader = JsonLoader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)
        elements = FsElement.createFromPath(BaseTestCase.dataTestsDirectory()).children()

        dispacher = Dispatcher.create('local')
        dispacher.setOption('defaultReporter', 'columns')
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
