import os
import io
import unittest
from fnmatch import fnmatch
from .BaseTestCase import BaseTestCase
from chilopoda.Cli import Cli
from chilopoda.TaskHolderLoader import JsonLoader
from chilopoda.Resource import Resource

class CliTest(BaseTestCase):
    """Test for cli app."""

    __jsonConfig = os.path.join(BaseTestCase.dataTestsDirectory(), 'config', 'reporterTest.json')
    __taskPath = os.path.join(BaseTestCase.dataTestsDirectory(), 'tasks', 'EchoTask.py')
    __output = """
        echoTask\t\ttestCrawler\t\t*/testSeq.0001.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0002.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0003.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0004.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0005.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0006.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0007.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0008.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0009.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0010.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0011.exr
        echoTask\t\ttestCrawler\t\t*/testSeq.0012.exr
        echoTask\t\tjpg\t\t\t*/testSeq.jpg
        echoTask\t\tturntable\t\t*/RND_ass_lookdev_default_beauty_tt.1001.exr
        echoTask\t\tnukeRender\t\t*/RND-TST-SHT_comp_compName_output_v010_tk.1001.exr
        echoTask\t\tshotRender\t\t*/RND-TST-SHT_lighting_beauty_sr.1001.exr
        echoTask\t\ttestCrawler\t\t*/test_0001.exr
    """

    def testOutput(self):
        """
        Test the output produced by the cli app.
        """
        resource = Resource.get()
        resource.load(self.__taskPath)

        taskHolderLoader = JsonLoader()
        taskHolderLoader.loadFromFile(self.__jsonConfig)

        cli = Cli()
        outputStream = io.StringIO()
        cli.run(
            (
                self.__jsonConfig,
                BaseTestCase.dataTestsDirectory()
            ),
            outStream=outputStream
        )

        output = outputStream.getvalue().split("\n")
        prefixSize = None
        for index, line in enumerate(self.__output.split("\n")[1:-1]):
            if prefixSize is None:
                prefixSize = len(line) - len(line.lstrip())

            line = line[prefixSize:]
            if not fnmatch(output[index].replace('\\', '/'), line):
                self.assertEqual(output[index], line)


if __name__ == "__main__":
    unittest.main()
