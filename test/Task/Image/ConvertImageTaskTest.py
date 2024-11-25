import os
import unittest
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Element.Fs import FsElement

class ConvertImageTaskTest(BaseTestCase):
    """
    Test ConvertImage task.

    Note that the convert image task will add time metadata on EXR and TIF files so they wouldn't pass the
    checksum test here.
    """

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "test.exr")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.jpg")

    def testConvertImage(self):
        """
        Test that the ConvertImage task works properly.
        """
        element = FsElement.createFromPath(self.__sourcePath)
        convertTask = Task.create('convertImage')
        convertTask.add(element, self.__targetPath)
        result = convertTask.output()
        self.assertEqual(len(result), 1)
        self.assertTrue(os.path.exists(result[0].var('filePath')))

    @classmethod
    def tearDownClass(cls):
        """
        Remove the file that was copied.
        """
        os.remove(cls.__targetPath)


if __name__ == "__main__":
    unittest.main()
