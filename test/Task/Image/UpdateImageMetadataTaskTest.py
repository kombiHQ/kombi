import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Element.Fs import FsElement

class UpdateImageMetadataTaskTest(BaseTestCase):
    """Test UpdateImageMetadata task."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.exr")

    def testUpdateImageMetadata(self):
        """
        Test that the UpdateImageMetadata task works properly.
        """
        element = FsElement.createFromPath(self.__sourcePath)
        updateTask = Task.create('updateImageMetadata')
        updateTask.setOption('data', {"testInt": 0, "testStr": "True"})
        updateTask.add(element, self.__targetPath)
        result = updateTask.output()
        self.assertEqual(len(result), 1)
        element = result[0]

        import OpenImageIO as oiio
        inputSpec = oiio.ImageInput.open(self.__targetPath).spec()
        self.assertEqual(inputSpec.get_int_attribute("testInt"), 0)
        self.assertEqual(inputSpec.get_string_attribute("testStr"), "True")


if __name__ == "__main__":
    unittest.main()
