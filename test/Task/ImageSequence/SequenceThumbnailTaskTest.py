import unittest
import os
import glob
from ...BaseTestCase import BaseTestCase
from kombi.Task import Task
from kombi.Element.Fs import FsElement

class SequenceThumbnailTaskTest(BaseTestCase):
    """Test SequenceThumbnail task."""

    __sourcePath = os.path.join(BaseTestCase.dataTestsDirectory(), "testSeq.*.exr")
    __targetPath = os.path.join(BaseTestCase.tempDirectory(), "testToDelete.jpg")

    def testSequenceThumbnail(self):
        """
        Test that the SequenceThumbnail task works properly.
        """
        thumbnailTask = Task.create('sequenceThumbnail')
        sourceFiles = sorted(glob.glob(self.__sourcePath))
        for i in map(FsElement.createFromPath, sourceFiles):
            thumbnailTask.add(i, self.__targetPath)
        result = thumbnailTask.output()
        self.assertEqual(len(result), 1)
        element = result[0]
        self.assertEqual(element.var("width"), 640)
        self.assertEqual(element.var("height"), 360)

    @classmethod
    def tearDownClass(cls):
        """
        Remove the file that was copied.
        """
        os.remove(cls.__targetPath)


if __name__ == "__main__":
    unittest.main()
