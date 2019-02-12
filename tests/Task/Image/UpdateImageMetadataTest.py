import unittest
import os
from ...BaseTestCase import BaseTestCase
from chilopoda.Task import Task
from chilopoda.Crawler.Fs import FsPath
from chilopoda.Task.Fs.Checksum import ChecksumMatchError
from chilopoda.Task.Image import UpdateImageMetadata

class UpdateImageMetadataTest(BaseTestCase):
    """Test UpdateImageMetadata task."""

    __sourcePath = os.path.join(BaseTestCase.dataDirectory(), "test.exr")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.exr")

    def testUpdateImageMetadata(self):
        """
        Test that the UpdateImageMetadata task works properly.
        """
        crawler = FsPath.createFromPath(self.__sourcePath)
        updateTask = Task.create('updateImageMetadata')
        updateTask.add(crawler, self.__targetPath)
        result = updateTask.output()
        self.assertEqual(len(result), 1)
        crawler = result[0]

        import OpenImageIO as oiio
        inputSpec = oiio.ImageInput.open(self.__targetPath).spec()
        self.assertEqual(inputSpec.get_string_attribute("chilopoda:sourceFile"), self.__sourcePath)
        checkTask = Task.create('checksum')
        checkTask.add(crawler, self.__sourcePath)
        self.assertRaises(ChecksumMatchError, checkTask.output)

        customMetadata = {"testInt": 0, "testStr": "True"}
        UpdateImageMetadata.updateDefaultMetadata(inputSpec, crawler, customMetadata)
        self.assertEqual(inputSpec.get_int_attribute("chilopoda:testInt"), 0)
        self.assertEqual(inputSpec.get_string_attribute("chilopoda:testStr"), "True")

    @classmethod
    def tearDownClass(cls):
        """
        Remove the file that was created.
        """
        os.remove(cls.__targetPath)


if __name__ == "__main__":
    unittest.main()
