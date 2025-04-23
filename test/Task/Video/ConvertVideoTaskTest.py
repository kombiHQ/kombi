import unittest
import os
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Element.Fs import FsElement

class ConvertVideoTaskTest(BaseTestCase):
    """Test ConvertVideo task."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "videoNoTimeCode.mov")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.mov")

    def testConvertVideo(self):
        """
        Test that the Convert Video task works properly.
        """
        element = FsElement.createFromPath(self.__sourcePath)
        convertTask = Task.create('convertVideo')
        convertTask.add(element, self.__targetPath)
        result = convertTask.output()
        self.assertEqual(len(result), 1)

        # the check is currently done through an approximation
        # from the expected size rather than a hash due metadata
        # that can vary the file size
        convertedSize = os.path.getsize(result[0].var('filePath'))
        self.assertGreaterEqual(convertedSize, 1450000)
        self.assertLessEqual(convertedSize, 1600000)


if __name__ == "__main__":
    unittest.main()
