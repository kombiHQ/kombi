import os
import unittest
from ..BaseTestCase import BaseTestCase
from chilopoda.TaskHolderLoader import TaskHolderLoader
from chilopoda.Crawler import Crawler
from chilopoda.Crawler.Fs.FsPath import FsPath

class VendorXPlatesTest(BaseTestCase):
    """Test for the example vendor 'x' plates."""

    __exampleDirectory = os.path.join(BaseTestCase.dataDirectory(), 'examples', 'vendorXPlates')
    __examplePrefixDirectory = os.path.join(BaseTestCase.tempDirectory(), 'examples', 'vendorXPlates')
    __ingestedData = """
        jobs/ant/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/ant_abc_def_v001.000001.exr
        jobs/ant/seq/abc/shot/def/plates/bla/v001/960x540_exr/ant_abc_def_v001.000001.exr
        jobs/ant/seq/abc/shot/def/plates/bla/v001/960x540_jpg/ant_abc_def_v001.000001.jpg
        jobs/ant/seq/abc/shot/def/plates/bla/v001/plate.mov
        jobs/ant/seq/abc/shot/def/plates/bla/v001/thumbnail.png
        jobs/ant/seq/abc/shot/def/plates/bla/v001/vendor.json
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000001.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000002.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000003.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000004.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000005.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000006.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000007.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000008.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000009.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000010.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000011.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr/foo_abc_def_v001.000012.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000001.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000002.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000003.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000004.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000005.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000006.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000007.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000008.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000009.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000010.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000011.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_exr/foo_abc_def_v001.000012.exr
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000001.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000002.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000003.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000004.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000005.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000006.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000007.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000008.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000009.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000010.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000011.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/960x540_jpg/foo_abc_def_v001.000012.jpg
        jobs/foo/seq/abc/shot/def/plates/bla/v001/plate.mov
        jobs/foo/seq/abc/shot/def/plates/bla/v001/thumbnail.png
        jobs/foo/seq/abc/shot/def/plates/bla/v001/vendor.json
    """

    def testConfigurations(self):
        """
        Test if the task holder loader can find the configurations under the directory.
        """
        loader = TaskHolderLoader()
        loader.loadFromDirectory(self.__exampleDirectory)
        self.assertListEqual(
            list(sorted(map(lambda x: os.path.basename(x.var('contextConfig')), loader.taskHolders()))),
            list(sorted(['ingestConfig.yaml', 'deliveryConfig.json']))
        )

    def testIngestion(self):
        """
        Test the ingestion configuration.
        """
        loader = TaskHolderLoader()
        loader.loadFromDirectory(self.__exampleDirectory)

        taskHolder = list(filter(lambda x: os.path.basename(x.var('contextConfig')) == 'ingestConfig.yaml', loader.taskHolders()))
        self.assertEqual(len(taskHolder), 1)
        taskHolder = taskHolder[0]

        taskHolder.addVar(
            "prefix",
            self.__examplePrefixDirectory,
            True
        )

        # loading input data for the ingestion
        crawlerGroups = Crawler.group(
            FsPath.createFromPath(
                os.path.join(self.__exampleDirectory, 'vendorPlate')
            ).globFromParent()
        )

        crawlers = []
        for group in crawlerGroups:
            if isinstance(group[0], Crawler.registeredType('png')):
                crawlers += taskHolder.run(group)

        targetFilePaths = list(sorted(filter(lambda x: len(x), map(lambda x: x.strip(), self.__ingestedData.split('\n')))))
        createdFilePaths = list(sorted(map(lambda x: x.var('fullPath')[len(self.__examplePrefixDirectory) + 1:].replace('\\', '/'), crawlers)))

        self.assertListEqual(targetFilePaths, createdFilePaths)

    def testDelivery(self):
        """
        Test that filter template in task holder.
        """
        pass


if __name__ == "__main__":
    unittest.main()
