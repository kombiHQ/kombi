import os
import shutil
from datetime import datetime
import unittest
from ..BaseTestCase import BaseTestCase
from kombi.TaskHolder.Loader import Loader
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.Fs.FsInfoCrate import FsInfoCrate

class VendorXPlatesTest(BaseTestCase):
    """Test for the example vendor 'x' plates."""

    __exampleDirectory = os.path.join(BaseTestCase.dataDirectory(), 'examples', 'vendorXPlates')
    __exampleIngestionPrefixDirectory = os.path.join(BaseTestCase.tempDirectory(), 'vendorXPlatesIngestion')
    __exampleDeliveryPrefixDirectory = os.path.join(BaseTestCase.tempDirectory(), 'vendorXPlatesDelivery')
    __ingestedGeneratedData = """
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
    __deliveryGeneratedData = """
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0001.png
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0002.png
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0003.png
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0004.png
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0005.png
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0006.png
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0007.png
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0008.png
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0009.png
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0010.png
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0011.png
        jobs/foo/seq/abc/shot/def/delivery/<date>/foo_abc_def_v001/1920x1080_exr/foo_def_abc_bla_001.0012.png
    """

    def testConfigurations(self):
        """
        Test if the task holder loader can find the configurations under the directory.
        """
        loader = Loader()
        loader.loadFromDirectory(self.__exampleDirectory)
        self.assertListEqual(
            list(sorted(map(lambda x: os.path.basename(x.var('contextConfig')), loader.taskHolders()))),
            list(sorted(['ingestConfig.yaml', 'deliveryConfig.json']))
        )

    def test01Ingestion(self):
        """
        Test the ingestion configuration.
        """
        loader = Loader()
        loader.loadFromDirectory(self.__exampleDirectory)

        taskHolder = list(filter(lambda x: os.path.basename(x.var('contextConfig')) == 'ingestConfig.yaml', loader.taskHolders()))
        self.assertEqual(len(taskHolder), 1)
        taskHolder = taskHolder[0]

        taskHolder.addVar(
            "prefix",
            self.__exampleIngestionPrefixDirectory,
            True
        )

        # loading input data for the ingestion
        infoCrateGroups = InfoCrate.group(
            FsInfoCrate.createFromPath(
                os.path.join(self.__exampleDirectory, 'plates')
            ).globFromParent()
        )

        resultInfoCrates = []
        for group in infoCrateGroups:
            if isinstance(group[0], InfoCrate.registeredType('png')):
                resultInfoCrates += taskHolder.run(group)

        targetFilePaths = list(sorted(filter(lambda x: len(x), map(lambda x: x.strip(), self.__ingestedGeneratedData.split('\n')))))
        createdFilePaths = list(sorted(map(lambda x: x.var('fullPath')[len(self.__exampleIngestionPrefixDirectory) + 1:].replace('\\', '/'), resultInfoCrates)))

        self.assertListEqual(targetFilePaths, createdFilePaths)

    def test02Delivery(self):
        """
        Test the delivery configuration.
        """
        loader = Loader()
        loader.loadFromDirectory(self.__exampleDirectory)

        taskHolder = list(filter(lambda x: os.path.basename(x.var('contextConfig')) == 'deliveryConfig.json', loader.taskHolders()))
        self.assertEqual(len(taskHolder), 1)
        taskHolder = taskHolder[0]

        taskHolder.addVar(
            "prefix",
            self.__exampleDeliveryPrefixDirectory,
            True
        )

        # loading input data for the ingestion
        infoCrateGroups = InfoCrate.group(
            FsInfoCrate.createFromPath(
                os.path.normpath(os.path.join(self.__exampleIngestionPrefixDirectory, 'jobs/foo/seq/abc/shot/def/plates/bla/v001/1920x1080_exr'))
            ).glob()
        )

        resultInfoCrates = []
        for group in infoCrateGroups:
            if isinstance(group[0], InfoCrate.registeredType('plateExr')):
                resultInfoCrates += taskHolder.run(group)

        targetFilePaths = list(sorted(filter(lambda x: len(x), map(lambda x: x.strip(), self.__deliveryGeneratedData.replace('<date>', datetime.today().strftime('%Y%m%d')).split('\n')))))
        createdFilePaths = list(sorted(map(lambda x: x.var('fullPath')[len(self.__exampleDeliveryPrefixDirectory) + 1:].replace('\\', '/'), resultInfoCrates)))

        self.assertListEqual(targetFilePaths, createdFilePaths)

    @classmethod
    def tearDownClass(cls):
        """
        Remove temporary files.
        """
        shutil.rmtree(cls.__exampleIngestionPrefixDirectory, ignore_errors=True)
        shutil.rmtree(cls.__exampleDeliveryPrefixDirectory, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
