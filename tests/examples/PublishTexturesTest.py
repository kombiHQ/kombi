import os
import shutil
import unittest
from ..BaseTestCase import BaseTestCase
from chilopoda.TaskHolderLoader import TaskHolderLoader
from chilopoda.Crawler import Crawler
from chilopoda.Crawler.Fs.FsPath import FsPath

class PublishTexturesTest(BaseTestCase):
    """Test for example publish textures."""

    __exampleDirectory = os.path.join(BaseTestCase.dataDirectory(), 'examples', 'publishTextures')
    __exampleTargetPrefixDirectory = os.path.join(BaseTestCase.tempDirectory(), 'publishTextures')
    __generatedData = """
        publishTextures/test/publish/texture/default/v001/data.json
        publishTextures/test/publish/texture/default/v001/env.json
        publishTextures/test/publish/texture/default/v001/info.json
        publishTextures/test/publish/texture/default/v001/data
        publishTextures/test/publish/texture/default/v001/data/exr
        publishTextures/test/publish/texture/default/v001/data/exr/DIFF_1001.exr
        publishTextures/test/publish/texture/default/v001/data/tif
        publishTextures/test/publish/texture/default/v001/data/tif/BUMP_1002.tif
        publishTextures/test/publish/texture/default/v001/data/tx
        publishTextures/test/publish/texture/default/v001/data/tx/BUMP_1002.tx
        publishTextures/test/publish/texture/default/v001/data/tx/DIFF_1001.tx
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

    @unittest.skipIf(not BaseTestCase.hasBin(os.environ.get('CHILOPODA_MAKETX_EXECUTABLE', 'maketx')), 'maketx not found in the search path')
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
                os.path.join(self.__exampleDirectory, 'textures')
            ).globFromParent()
        )

        resultCrawlers = []
        for group in crawlerGroups:
            if isinstance(group[0], Crawler.registeredType('texture')):
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
