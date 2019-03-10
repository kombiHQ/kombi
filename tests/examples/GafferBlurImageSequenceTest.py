import os
import shutil
import unittest
from ..BaseTestCase import BaseTestCase
from kombi.TaskHolderLoader import TaskHolderLoader
from kombi.Crawler import Crawler
from kombi.Crawler.Fs.FsPath import FsPath

class GafferBlurImageSequenceTest(BaseTestCase):
    """Test for example gaffer blur image sequence."""

    __exampleDirectory = os.path.join(BaseTestCase.dataDirectory(), 'examples', 'gafferBlurImageSequence')
    __exampleTargetPrefixDirectory = os.path.join(BaseTestCase.tempDirectory(), 'gafferBlurImageSequence')
    __generatedData = """
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000001.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000002.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000003.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000004.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000005.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000006.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000007.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000008.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000009.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000010.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000011.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.000012.exr
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001.mov
        gafferBlurImageSequence/v001/foo_def_abc_bla_001_v001_copy.mov
    """

    def testLoadConfiguration(self):
        """
        Test if the task holder loader can find the configurations under the directory.
        """
        loader = TaskHolderLoader()
        loader.loadFromDirectory(self.__exampleDirectory)

        self.assertEqual(len(loader.taskHolders()), 1)

        self.assertEqual(
            os.path.basename(loader.taskHolders()[0].var('contextConfig')),
            'config.json'
        )

    @unittest.skipIf(not BaseTestCase.hasBin(os.environ.get('KOMBI_GAFFER_EXECUTABLE', 'gaffer')), 'gaffer not found in the search path')
    def testRunConfiguration(self):
        """
        Test execution of the configuration.
        """
        loader = TaskHolderLoader()
        loader.loadFromDirectory(self.__exampleDirectory)

        self.assertEqual(len(loader.taskHolders()), 1)

        taskHolder = loader.taskHolders()[0]

        taskHolder.addVar(
            "prefix",
            self.__exampleTargetPrefixDirectory,
            True
        )

        # loading input data for the execution
        crawlerGroups = Crawler.group(
            FsPath.createFromPath(
                os.path.join(self.__exampleDirectory, 'imageSequence')
            ).globFromParent()
        )

        resultCrawlers = []
        for group in crawlerGroups:
            if isinstance(group[0], Crawler.registeredType('png')):
                resultCrawlers += taskHolder.run(group)

        targetFilePaths = list(sorted(filter(lambda x: len(x), map(lambda x: x.strip(), self.__generatedData.split('\n')))))
        createdFilePaths = list(sorted(map(lambda x: x.var('fullPath')[len(self.__exampleTargetPrefixDirectory) + 1:].replace('\\', '/'), resultCrawlers)))

        self.assertListEqual(targetFilePaths, createdFilePaths)

    @classmethod
    def tearDownClass(cls):
        """
        Remove temporary files.
        """
        shutil.rmtree(cls.__exampleTargetPrefixDirectory, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
